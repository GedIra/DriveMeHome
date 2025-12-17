from django.db import models
from django.conf import settings
from rides.models import Ride # Optional: Link directly to a ride

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        RIDE_REQUEST = 'RIDE_REQ', 'New Ride Request'
        RIDE_ACCEPTED = 'RIDE_ACC', 'Ride Accepted'
        RIDE_ARRIVED = 'RIDE_ARR', 'Driver Arrived'
        RIDE_STARTED = 'RIDE_STR', 'Trip Started'
        RIDE_COMPLETED = 'RIDE_CMP', 'Trip Completed'
        PAYMENT = 'PAYMENT', 'Payment Alert'
        SYSTEM = 'SYSTEM', 'System Message'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    
    # Context
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, null=True, blank=True)
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    
    # Status
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.username}"