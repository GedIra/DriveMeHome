from django.urls import path
from . import views

urlpatterns = [
   # Client Views
    path('book/', views.book_ride_view, name='book_ride'),
    path('history/', views.ride_history_view, name='ride_history'),
    
    # APIs
    path('api/add-vehicle/', views.add_vehicle_view, name='api_add_vehicle'),
    path('api/estimate-ride/', views.get_ride_estimate_view, name='api_estimate_ride'),
    path('api/get-drivers/', views.get_qualified_drivers_view, name='api_get_drivers'),
    
    # Driver Views
    path('driver/dashboard/', views.driver_dashboard_view, name='driver_dashboard'),
    path('api/driver/status/', views.update_driver_status_api, name='api_update_driver_status'),
]