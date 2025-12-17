from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.book_ride_view, name='book_ride'),
    path('api/add-vehicle/', views.add_vehicle_view, name='api_add_vehicle'),
    path('book/api/estimate-ride/', views.get_ride_estimate_view, name='api_estimate_ride'),
    path('api/get-drivers/', views.get_qualified_drivers_view, name='api_get_drivers'),
]