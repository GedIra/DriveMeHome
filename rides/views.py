import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from users.models import CustomerVehicle, CustomerProfile, PreferredDestination, DriverProfile
from .models import PricingConfiguration, Ride
from .utils import get_distance_and_duration

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
            pickup_addr = request.POST.get('pickup') # Raw text address
            dropoff_addr = request.POST.get('dropoff') # Raw text address
            
            # Booking Options
            schedule_time = request.POST.get('schedule_time') # Can be empty
            driver_selection_mode = request.POST.get('driver_selection_mode') # 'auto' or driver_id
            
            if not all([pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, vehicle_id]):
                messages.error(request, "Please fill in all location and vehicle details.")
                return redirect('book_ride')

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
            
            # 3. Calculate Fare (Calls Mapbox)
            ride.estimate_fare() # This saves the ride object
            
            # 4. Handle Driver Assignment
            if driver_selection_mode == 'auto':
                # Auto Assign Logic
                qualified_drivers = DriverProfile.objects.filter(
                    is_verified=True,
                    license_score__gte=vehicle.required_license_score
                ).exclude(current_status=DriverProfile.DriverStatus.OFFLINE)

                if vehicle.transmission_type == 'MANUAL':
                    qualified_drivers = qualified_drivers.filter(transmission_capability='BOTH')

                # Prefer AVAILABLE, then BUSY
                # Sort: 0 for AVAILABLE, 1 for BUSY
                best_driver = sorted(
                    qualified_drivers, 
                    key=lambda d: (0 if d.current_status == 'AVAILABLE' else 1, -d.average_rating)
                )

                if best_driver:
                    ride.driver = best_driver[0]
                    ride.status = Ride.RideStatus.DRIVER_ASSIGNED
                    if best_driver[0].current_status == 'BUSY':
                        messages.warning(request, f"Ride booked! Driver {ride.driver.user.username} is currently busy but will come to you next.")
                    else:
                        messages.success(request, f"Ride booked! Driver {ride.driver.user.username} is on the way.")
                else:
                    ride.status = Ride.RideStatus.REQUESTED
                    messages.info(request, "Ride requested. We are searching for a driver for you.")
            
            else:
                # Manual Selection (driver_id passed)
                try:
                    driver = DriverProfile.objects.get(id=driver_selection_mode)
                    ride.driver = driver
                    ride.status = Ride.RideStatus.DRIVER_ASSIGNED
                    messages.success(request, f"Ride booked with {driver.user.username}!")
                except DriverProfile.DoesNotExist:
                    ride.status = Ride.RideStatus.REQUESTED
                    messages.warning(request, "Selected driver not found. Request broadcasted to all.")

            ride.save()
            
            # TODO: Redirect to a "Track Ride" page. For now, reload.
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
        query = query.filter(vehicle__required_license_score__lte=driver.license_score)
        
        available_rides = query.order_by('-created_at')

    context = {
        'driver': driver,
        'active_ride': active_ride,
        'available_rides': available_rides
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