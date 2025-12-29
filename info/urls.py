from django.urls import path
from .views import (
    support_view,
    privacy_policy_view,
    terms_of_service_view,
    driver_agreement_view,
)

app_name = 'info'

urlpatterns = [
    path('support/', support_view, name='support'),
    path('privacy-policy/', privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', terms_of_service_view, name='terms_of_service'),
    path('driver-agreement/', driver_agreement_view, name='driver_agreement'),
]
