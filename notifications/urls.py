from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('api/get/', views.get_notifications_api, name='api_get_notifications'),
    path('api/read/<int:notification_id>/', views.mark_read_api, name='api_mark_read'),
    path('api/read-all/', views.mark_all_read_api, name='api_mark_all_read'),
]