from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import DriverProfile, CustomerProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
  """
  Signal to create a DriverProfile or CustomerProfile 
  automatically when a User is created.
  """
  if created:
    if instance.is_driver:
      DriverProfile.objects.create(user=instance)
    # Note: A user can be both, or default to customer
    if instance.is_customer:
      CustomerProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
  """
  Signal to save the profile whenever the user object is saved.
  """
  if instance.is_driver and hasattr(instance, 'driver_profile'):
    instance.driver_profile.save()
  if instance.is_customer and hasattr(instance, 'customer_profile'):
    instance.customer_profile.save()