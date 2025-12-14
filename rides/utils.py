import requests
from django.conf import settings
from decimal import Decimal

def get_distance_and_duration(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """
    Calculates the driving distance and duration between two points using Mapbox Directions API.
    
    Args:
        pickup_lat, pickup_lng: Coordinates of origin
        dropoff_lat, dropoff_lng: Coordinates of destination
        
    Returns:
        dict: {'distance_km': Decimal, 'duration_min': Decimal} or None if failed
    """
    # Ensure you have MAPBOX_ACCESS_TOKEN in your settings.py
    token = getattr(settings, 'MAPBOX_ACCESS_TOKEN', None)
    if not token:
        print("Warning: MAPBOX_ACCESS_TOKEN is not set in settings.")
        return None

    # Mapbox requires coordinates in "Longitude,Latitude" format
    # Endpoint: https://api.mapbox.com/directions/v5/mapbox/driving/{lon},{lat};{lon},{lat}
    
    # Ensure coordinates are treated as strings or floats for formatting
    origin_str = f"{pickup_lng},{pickup_lat}"
    dest_str = f"{dropoff_lng},{dropoff_lat}"
    
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{origin_str};{dest_str}"
    
    params = {
        'access_token': token,
        'geometries': 'geojson',
        'overview': 'false' # We only need distance/duration, not the path points
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200 and data.get('code') == 'Ok':
            # Directions API returns a list of routes. We take the first (best) one.
            if not data.get('routes'):
                return None
                
            route = data['routes'][0]
            
            # Mapbox returns distance in meters, duration in seconds
            distance_meters = route.get('distance')
            duration_seconds = route.get('duration')
            
            if duration_seconds is None or distance_meters is None:
                return None

            return {
                # Convert meters to km
                'distance_km': Decimal(str(distance_meters)) / Decimal(1000),
                # Convert seconds to minutes
                'duration_min': Decimal(str(duration_seconds)) / Decimal(60)
            }
        else:
            print(f"Mapbox API Error: {data.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error fetching Mapbox data: {e}")
        return None
    
    return None