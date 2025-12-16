import requests
import urllib.parse
from django.conf import settings
from decimal import Decimal

def get_distance_and_duration(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """
    Calculates driving distance and duration using Mapbox Directions API.
    Used for server-side price calculation.
    """
    token = getattr(settings, 'MAPBOX_ACCESS_TOKEN', None)
    if not token:
        print("Error: MAPBOX_ACCESS_TOKEN missing in Django settings")
        return None

    # Mapbox Directions API expects: start_long,start_lat;end_long,end_lat
    origin_str = f"{pickup_lng},{pickup_lat}"
    dest_str = f"{dropoff_lng},{dropoff_lat}"
    
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{origin_str};{dest_str}"
    
    params = {
        'access_token': token,
        'geometries': 'geojson',
        'overview': 'false' # We only need distance/duration metrics here, not the full path
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200 and data.get('code') == 'Ok':
            if not data.get('routes'):
                return None
            
            # Mapbox returns distance in meters, duration in seconds
            route = data['routes'][0]
            distance_meters = route.get('distance')
            duration_seconds = route.get('duration')

            if duration_seconds is None or distance_meters is None:
                return None

            return {
                # Convert to KM and Minutes
                'distance_km': Decimal(str(distance_meters)) / Decimal(1000),
                'duration_min': Decimal(str(duration_seconds)) / Decimal(60)
            }
        else:
            print(f"Mapbox API Error: {data.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"Error fetching Mapbox data: {e}")
        return None

def reverse_geocode(lat, lng):
    """
    Server-side reverse geocoding (optional usage).
    """
    token = getattr(settings, 'MAPBOX_ACCESS_TOKEN', None)
    if not token: return None
    
    # Mapbox Geocoding expects: long,lat
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lng},{lat}.json"
    params = {'access_token': token, 'limit': 1}
    
    try:
        r = requests.get(url, params=params, timeout=5).json()
        return r['features'][0]['place_name'] if r.get('features') else None
    except: 
        return None