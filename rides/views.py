import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator # Added for pagination
from users.models import CustomerVehicle, CustomerProfile, PreferredDestination, DriverProfile
from .models import PricingConfiguration, Ride
from .utils import get_distance_and_duration
from django.utils import timezone
from django.db import transaction
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Review

@login_required
def book_ride_view(request):
    """
    GET: Renders the booking page.
    POST: Creates the ride request.
    """
    if request.method == 'POST':
        # --- HANDLE BOOKING CREATION ---
        try:
            # 1. Extract Data
            pickup_lat = request.POST.get('pickup_latitude')
            pickup_lng = request.POST.get('pickup_longitude')
            dropoff_lat = request.POST.get('dropoff_latitude')
            dropoff_lng = request.POST.get('dropoff_longitude')
            vehicle_id = request.POST.get('vehicle')
            # Use 'pickup' and 'dropoff' from form names, fallback to empty string
            pickup_addr = request.POST.get('pickup', '') 
            dropoff_addr = request.POST.get('dropoff', '')
            
            # Booking Options
            schedule_time = request.POST.get('schedule_time') # Can be empty
            driver_selection_mode = request.POST.get('driver_selection_mode') # 'auto' or driver_id
            
            # Basic Validation
            if not all([pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, vehicle_id]):
                messages.error(request, "Please fill in all location and vehicle details.")
                return redirect('book_ride')

            # Ensure user has profile
            if not hasattr(request.user, 'customer_profile'):
                 messages.error(request, "Customer profile not found.")
                 return redirect('profile') # Redirect to profile creation if needed

            customer_profile = request.user.customer_profile
            vehicle = get_object_or_404(CustomerVehicle, id=vehicle_id, customer=customer_profile)

            # 2. Create Ride Object
            ride = Ride(
                customer=customer_profile,
                vehicle=vehicle,
                pickup_address=pickup_addr,
                pickup_latitude=pickup_lat,
                pickup_longitude=pickup_lng,
                dropoff_address=dropoff_addr,
                dropoff_latitude=dropoff_lat,
                dropoff_longitude=dropoff_lng,
                scheduled_for=schedule_time if schedule_time else None
            )
            
            # 3. Calculate Fare (Calls Mapbox) - This also saves the ride initially
            ride.estimate_fare() 
            
            # 4. Handle Driver Assignment
            with transaction.atomic():
                driver_to_assign = None
                if driver_selection_mode == 'auto':
                    # Auto Assign Logic
                    qualified_drivers = DriverProfile.objects.filter(
                        is_verified=True,
                        license_score__gte=vehicle.required_license_score
                    ).exclude(current_status=DriverProfile.DriverStatus.OFFLINE)

                    if vehicle.transmission_type == 'MANUAL':
                        qualified_drivers = qualified_drivers.filter(transmission_capability='BOTH')

                    best_driver_list = sorted(
                        qualified_drivers, 
                        key=lambda d: (0 if d.current_status == DriverProfile.DriverStatus.AVAILABLE else 1, -d.average_rating)
                    )
                    if best_driver_list:
                        driver_to_assign = best_driver_list[0]
                
                else:
                    # Manual Selection (driver_id passed)
                    try:
                        driver_to_assign = DriverProfile.objects.get(id=driver_selection_mode)
                    except DriverProfile.DoesNotExist:
                        pass # Handled below

                # Assign driver and update statuses
                if driver_to_assign:
                    ride.driver = driver_to_assign
                    ride.status = Ride.RideStatus.DRIVER_ASSIGNED
                    
                    if driver_to_assign.current_status == DriverProfile.DriverStatus.BUSY:
                        messages.warning(request, f"Ride booked! Driver {ride.driver.user.username} is currently busy but will come to you next.")
                    else:
                        driver_to_assign.current_status = DriverProfile.DriverStatus.BUSY
                        driver_to_assign.save()
                        messages.success(request, f"Ride booked! Driver {ride.driver.user.username} is on the way.")
                else:
                    ride.status = Ride.RideStatus.REQUESTED
                    if driver_selection_mode != 'auto':
                         messages.warning(request, "Selected driver not found. Request broadcasted to all.")
                    else:
                        messages.info(request, "Ride requested. We are searching for a driver for you.")

                ride.save()
            
            # Redirect to avoid resubmission. Ideally to a 'ride_detail' page.
            return redirect('book_ride')

        except Exception as e:
            messages.error(request, f"Error creating booking: {e}")
            return redirect('book_ride')

    # --- GET REQUEST (Render Page) ---
    user_vehicles = []
    saved_destinations = []
    
    if hasattr(request.user, 'customer_profile'):
        profile = request.user.customer_profile
        user_vehicles = CustomerVehicle.objects.filter(customer=profile)
        saved_destinations = PreferredDestination.objects.filter(customer=profile)
    
    context = {
        'user_vehicles': user_vehicles,
        'saved_destinations': saved_destinations,
        'mapbox_access_token': settings.MAPBOX_ACCESS_TOKEN,
    }
    return render(request, 'rides/book_ride.html', context)

@login_required
@require_GET
def get_qualified_drivers_view(request):
    """
    API to fetch drivers qualified for a specific vehicle.
    """
    vehicle_id = request.GET.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({'success': False, 'error': 'Vehicle ID required'}, status=400)

    try:
        if not hasattr(request.user, 'customer_profile'):
             return JsonResponse({'success': False, 'error': 'User profile not found'}, status=403)

        vehicle = CustomerVehicle.objects.get(id=vehicle_id, customer=request.user.customer_profile)
        
        # 1. Filter by License Score
        drivers = DriverProfile.objects.filter(
            is_verified=True,
            license_score__gte=vehicle.required_license_score
        ).exclude(current_status=DriverProfile.DriverStatus.OFFLINE)

        # 2. Filter by Transmission
        if vehicle.transmission_type == 'MANUAL':
            drivers = drivers.filter(transmission_capability='BOTH')
        
        # 3. Serialize
        driver_list = []
        for d in drivers:
            driver_list.append({
                'id': d.id,
                'name': d.user.username, # Ideally use full name
                'rating': d.average_rating,
                'status': d.get_current_status_display(),
                'status_code': d.current_status, # 'AVAILABLE', 'BUSY'
                'category': d.get_license_category_display(),
                'avatar': d.profile_picture.url if d.profile_picture else None
            })
        
        # 4. Sort: AVAILABLE first, then by Rating (high to low)
        driver_list.sort(key=lambda x: (0 if x['status_code'] == 'AVAILABLE' else 1, -x['rating']))

        return JsonResponse({'success': True, 'drivers': driver_list})

    except CustomerVehicle.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Vehicle not found'}, status=404)
    
@login_required
def ride_history_view(request):
    """
    Displays a list of past rides for the user with filters and pagination.
    Differentiates logic for Drivers vs Customers.
    """
    user = request.user
    rides = Ride.objects.none()

    # 1. Determine User Role & Fetch Rides
    if user.is_driver and hasattr(user, 'driver_profile'):
        rides = Ride.objects.filter(driver=user.driver_profile)
    elif user.is_customer and hasattr(user, 'customer_profile'):
        rides = Ride.objects.filter(customer=user.customer_profile)
    
    # 2. Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        rides = rides.filter(status=status_filter)

    # 3. Search (Address)
    search_query = request.GET.get('q')
    if search_query:
        rides = rides.filter(
            Q(pickup_address__icontains=search_query) | 
            Q(dropoff_address__icontains=search_query)
        )

    # 4. Sorting (Most recent first)
    rides = rides.order_by('-created_at')

    # 5. Pagination
    paginator = Paginator(rides, 10) # 10 rides per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'rides': page_obj, # Pass page_obj as 'rides' for loop compatibility
        'page_obj': page_obj, # Pass explicitly for pagination controls
        'status_choices': Ride.RideStatus.choices,
        'selected_status': status_filter,
        'search_query': search_query
    }
    return render(request, 'rides/ride_history.html', context)

@login_required
@require_POST
def add_vehicle_view(request):
    try:
        data = json.loads(request.body)
        if not hasattr(request.user, 'customer_profile'):
            return JsonResponse({'success': False, 'error': 'User profile not found.'}, status=400)
            
        profile = request.user.customer_profile
        vehicle = CustomerVehicle.objects.create(
            customer=profile,
            name=data.get('name'),
            plate_number=data.get('plate'),
            transmission_type=data.get('transmission'),
            vehicle_category=data.get('category')
        )
        
        return JsonResponse({
            'success': True,
            'vehicle': {
                'id': vehicle.id,
                'name': vehicle.name,
                'transmission': vehicle.get_transmission_type_display()
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_GET
def get_ride_estimate_view(request):
    """
    API to calculate distance, duration, and price without saving to DB.
    Expects GET params: pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
    """
    try:
        p_lat = request.GET.get('pickup_lat')
        p_lng = request.GET.get('pickup_lng')
        d_lat = request.GET.get('dropoff_lat')
        d_lng = request.GET.get('dropoff_lng')

        if not all([p_lat, p_lng, d_lat, d_lng]):
            return JsonResponse({'success': False, 'error': 'Missing coordinates'}, status=400)

        # Call the Mapbox Utility
        metrics = get_distance_and_duration(p_lat, p_lng, d_lat, d_lng)
        
        if not metrics:
            return JsonResponse({'success': False, 'error': 'Could not calculate route path'}, status=400)

        # Calculate Price
        config = PricingConfiguration.objects.filter(is_active=True).first()
        estimated_price = 0
        currency = "RWF"
        
        if config:
            cost = config.base_fare + \
                   (metrics['distance_km'] * config.price_per_km) + \
                   (metrics['duration_min'] * config.price_per_minute)
            estimated_price = round(cost)
        
        # Fallback if no config (optional, but good for MVP)
        elif not config: 
             # Basic fallback logic if needed, or just return 0
             cost = 2000 + (metrics['distance_km'] * 1000)
             estimated_price = round(cost)

        return JsonResponse({
            'success': True,
            'distance_km': round(metrics['distance_km'], 1),
            'duration_min': round(metrics['duration_min']),
            'estimated_price': estimated_price,
            'currency': currency
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# --- NEW DRIVER VIEWS ---

@login_required
def driver_dashboard_view(request):
    """
    Main dashboard for drivers.
    """
    # 1. Security Check
    if not request.user.is_driver:
        return redirect('book_ride') # Or error page
    
    # 2. Get Profile
    try:
        driver = request.user.driver_profile
    except DriverProfile.DoesNotExist:
        # Should be created by signal, but safety net:
        return redirect('profile') 

    # 3. Check for Active Ride (IN_PROGRESS or ASSIGNED)
    active_ride = Ride.objects.filter(
        driver=driver, 
        status__in=[Ride.RideStatus.DRIVER_ASSIGNED, Ride.RideStatus.DRIVER_ARRIVED, Ride.RideStatus.IN_PROGRESS]
    ).first()

    # 4. Get Available Rides (If no active ride and online)
    available_rides = []
    if not active_ride and driver.current_status == DriverProfile.DriverStatus.AVAILABLE:
        # Filter logic: 
        # - Status REQUESTED
        # - Vehicle category matches driver license score logic
        # - Transmission matches
        
        # Base query
        query = Ride.objects.filter(status=Ride.RideStatus.REQUESTED)
        
        # Transmission Filter
        if driver.transmission_capability == DriverProfile.TransmissionType.AUTOMATIC_ONLY:
            query = query.filter(vehicle__transmission_type='AUTO')
            
        # License Score Filter (Driver score >= Vehicle required score)
        # Note: We need to annotate or loop. For MVP, simple loop or DB filter if possible.
        # Since required_license_score is on Vehicle model, we can filter:
        query = query.filter(vehicle__required_license_score__lte=driver.license_score)
        
        available_rides = query.order_by('-created_at')

    context = {
        'driver': driver,
        'active_ride': active_ride,
        'available_rides': available_rides,
        'mapbox_access_token': settings.MAPBOX_ACCESS_TOKEN,
    }
    return render(request, 'rides/driver_dashboard.html', context)

@login_required
@require_POST
def update_driver_status_api(request):
    """
    API to toggle Online/Offline status.
    """
    try:
        if not hasattr(request.user, 'driver_profile'):
            return JsonResponse({'success': False, 'error': 'Not a driver'}, status=403)
            
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in ['AVAILABLE', 'OFFLINE']:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
            
        driver = request.user.driver_profile
        
        # Don't allow going offline if currently in a ride
        if new_status == 'OFFLINE' and driver.current_status == 'BUSY':
             return JsonResponse({'success': False, 'error': 'Cannot go offline while busy'}, status=400)

        driver.current_status = new_status
        driver.save()
        
        return JsonResponse({
            'success': True, 
            'new_status': new_status,
            'display_status': driver.get_current_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@login_required
@require_POST
def accept_ride_api(request, ride_id):
    """
    Driver accepts a ride.
    Enforces: Single active ride rule.
    """
    try:
        driver = request.user.driver_profile
        ride = get_object_or_404(Ride, id=ride_id)
        
        # 1. Check if Driver is already busy with an ACTIVE ride
        # Active = ASSIGNED, ARRIVED, IN_PROGRESS
        active_ride = Ride.objects.filter(
            driver=driver,
            status__in=[Ride.RideStatus.DRIVER_ASSIGNED, Ride.RideStatus.DRIVER_ARRIVED, Ride.RideStatus.IN_PROGRESS]
        ).exists()

        if active_ride:
            return JsonResponse({'success': False, 'error': 'You already have an active ride. Complete it first.'}, status=400)

        # 2. Check if Ride is still available
        if ride.status != Ride.RideStatus.REQUESTED:
            return JsonResponse({'success': False, 'error': 'This ride is no longer available.'}, status=400)

        # 3. Assign Driver
        with transaction.atomic():
            ride.driver = driver
            ride.status = Ride.RideStatus.DRIVER_ASSIGNED
            ride.accepted_at = timezone.now()
            ride.save()
            
            # Update Driver Status
            driver.current_status = DriverProfile.DriverStatus.BUSY
            driver.save()
            
            # Notify Customer (Placeholder for Notification App)
            # send_notification(ride.customer.user, "Driver Found", f"{driver.user.username} has accepted your ride.", ...)

        return JsonResponse({'success': True, 'ride_id': ride.id})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def update_driver_location_api(request):
    """
    Updates driver's current location. Called via AJAX.
    """
    try:
        driver = request.user.driver_profile
        data = json.loads(request.body)
        
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        if lat and lng:
            driver.current_latitude = lat
            driver.current_longitude = lng
            driver.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Invalid coordinates'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def get_ride_details_api(request, ride_id):
    """
    Returns details for the Modal (Route, Client Info, Price).
    """
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Calculate driver earning if not set (estimated)
    # This logic mimics the estimate_fare logic but just returns values
    earning = ride.driver_earnings
    if not earning and ride.estimated_price:
         # Simple recalculation if needed or just use estimated total for now if earning isn't saved yet
         # Ideally earning is saved on estimate_fare()
         pass

    data = {
        'id': ride.id,
        'customer_name': ride.customer.user.username,
        'customer_avatar': ride.customer.profile_picture.url if ride.customer.profile_picture else None,
        'pickup': ride.pickup_address,
        'pickup_lat': ride.pickup_latitude,
        'pickup_lng': ride.pickup_longitude,
        'dropoff': ride.dropoff_address,
        'dropoff_lat': ride.dropoff_latitude,
        'dropoff_lng': ride.dropoff_longitude,
        'distance': ride.distance_km,
        'duration': ride.estimated_duration_min,
        'est_earning': ride.driver_earnings or (ride.estimated_price * Decimal('0.8')), # Fallback 80%
        'status': ride.status,
    }
    return JsonResponse({'success': True, 'ride': data})

@login_required
@require_POST
@transaction.atomic
def update_ride_status_api(request, ride_id):
    """
    API for a driver to update the status of a ride they are assigned to.
    e.g., ARRIVED, IN_PROGRESS, COMPLETED
    """
    try:
        driver = request.user.driver_profile
        ride = get_object_or_404(Ride, id=ride_id, driver=driver)
        data = json.loads(request.body)
        new_status = data.get('status')

        if not new_status:
            return JsonResponse({'success': False, 'error': 'New status not provided'}, status=400)

        valid_statuses = [c[0] for c in Ride.RideStatus.choices]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': f'Invalid status: {new_status}'}, status=400)

        ride.status = new_status
        
        if new_status == Ride.RideStatus.IN_PROGRESS:
            ride.started_at = timezone.now()
        elif new_status == Ride.RideStatus.COMPLETED:
            ride.completed_at = timezone.now()
            # When ride is completed, driver becomes available again
            # But only if they don't have another ride queued up
            other_rides = Ride.objects.filter(
                driver=driver,
                status__in=[Ride.RideStatus.DRIVER_ASSIGNED, Ride.RideStatus.DRIVER_ARRIVED]
            ).exists()
            if not other_rides:
                driver.current_status = DriverProfile.DriverStatus.AVAILABLE
                driver.save()

        ride.save()

        return JsonResponse({'success': True, 'new_status': ride.status, 'ride_id': ride.id})

    except DriverProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Driver profile not found.'}, status=403)
    except Ride.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ride not found or you are not assigned to it.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def create_review_api(request, ride_id):
    """
    Create a review for a ride. Expects JSON: {rating: int, comment: str}
    Only participants may review and only after ride is COMPLETED.
    Prevent duplicate reviews by same reviewer.
    """
    try:
        ride = get_object_or_404(Ride, id=ride_id)

        if ride.status != Ride.RideStatus.COMPLETED:
            return JsonResponse({'success': False, 'error': 'Ride not completed yet.'}, status=400)

        user = request.user

        # Ensure user is participant
        is_driver = hasattr(user, 'driver_profile') and ride.driver and ride.driver == user.driver_profile
        is_customer = hasattr(user, 'customer_profile') and ride.customer == user.customer_profile

        if not (is_driver or is_customer):
            return JsonResponse({'success': False, 'error': 'You are not a participant of this ride.'}, status=403)

        # Prevent duplicate
        if Review.objects.filter(ride=ride, reviewer=user).exists():
            return JsonResponse({'success': False, 'error': 'You have already reviewed this ride.'}, status=400)

        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '').strip()

        if rating < 1 or rating > 5:
            return JsonResponse({'success': False, 'error': 'Rating must be between 1 and 5.'}, status=400)

        reviewer_type = Review.ReviewerType.DRIVER if is_driver else Review.ReviewerType.CUSTOMER

        review = Review.objects.create(
            ride=ride,
            reviewer=user,
            rating=rating,
            comment=comment,
            reviewer_type=reviewer_type
        )

        return JsonResponse({'success': True, 'review_id': review.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def reviews_list_view(request):
    """List reviews received by current user (drivers see customer reviews; customers see driver reviews)."""
    user = request.user
    reviews = Review.objects.none()

    if hasattr(user, 'driver_profile'):
        # Reviews where ride.driver == this driver and reviewer_type == CUSTOMER
        reviews = Review.objects.filter(ride__driver=user.driver_profile, reviewer_type=Review.ReviewerType.CUSTOMER)
    elif hasattr(user, 'customer_profile'):
        # Reviews where ride.customer == this customer and reviewer_type == DRIVER
        reviews = Review.objects.filter(ride__customer=user.customer_profile, reviewer_type=Review.ReviewerType.DRIVER)

    reviews = reviews.select_related('ride', 'reviewer').order_by('-created_at')
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'rides/reviews_list.html', {'page_obj': page_obj})