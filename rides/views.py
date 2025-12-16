import json
from decimal import Decimal # Ensure Decimal is imported
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from users.models import CustomerVehicle, CustomerProfile, PreferredDestination
from .models import PricingConfiguration
from .utils import get_distance_and_duration


@login_required
@never_cache
def book_ride_view(request):
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
    API to calculate distance, duration, and price.
    """
    try:
        p_lat = request.GET.get('pickup_lat')
        p_lng = request.GET.get('pickup_lng')
        d_lat = request.GET.get('dropoff_lat')
        d_lng = request.GET.get('dropoff_lng')

        if not all([p_lat, p_lng, d_lat, d_lng]):
            return JsonResponse({'success': False, 'error': 'Missing coordinates'}, status=400)

        # 1. Get Distance/Duration from Mapbox Utility (Server-Side)
        # Note: This requires MAPBOX_ACCESS_TOKEN to be set in settings.py/.env on the server
        metrics = get_distance_and_duration(p_lat, p_lng, d_lat, d_lng)
        
        if not metrics:
            print("Error: Backend failed to fetch route from Mapbox.")
            return JsonResponse({'success': False, 'error': 'Could not calculate route path from backend.'}, status=400)

        # 2. Calculate Price based on Config
        config = PricingConfiguration.objects.filter(is_active=True).first()
        
        # --- FALLBACK DEFAULTS (If no admin config exists yet) ---
        if config:
            base_fare = config.base_fare
            rate_km = config.price_per_km
            rate_min = config.price_per_minute
        else:
            print("Warning: No active PricingConfiguration found. Using defaults.")
            base_fare = Decimal('2000') # 2000 RWF start
            rate_km = Decimal('1000')   # 1000 RWF per km
            rate_min = Decimal('100')   # 100 RWF per min

        # Formula: Base + (Km * Rate) + (Min * Rate)
        cost = base_fare + \
               (metrics['distance_km'] * rate_km) + \
               (metrics['duration_min'] * rate_min)
        
        estimated_price = round(cost)
        currency = "RWF"

        return JsonResponse({
            'success': True,
            'distance_km': round(metrics['distance_km'], 1),
            'duration_min': round(metrics['duration_min']),
            'estimated_price': estimated_price,
            'currency': currency
        })

    except Exception as e:
        print(f"Estimate View Error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)