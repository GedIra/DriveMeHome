from django.db import models
from django.contrib.auth.models import AbstractUser
import re
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
  email = models.EmailField(unique=True)
  phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
  is_driver = models.BooleanField(default=False)
  is_customer = models.BooleanField(default=True)
  
  def __str__(self):
    return self.username

  def clean(self):
    """Normalize and validate phone number before saving/validation.

    - Strips non-digit characters.
    - Ensures phone numbers contain between 10 and 15 digits when provided.
    """
    super().clean()
    if self.phone_number:
      cleaned = re.sub(r"\D", "", str(self.phone_number))
      if cleaned == "":
        self.phone_number = None
        return
      if len(cleaned) < 10 or len(cleaned) > 15:
        raise ValidationError({'phone_number': 'Phone number must contain between 10 and 15 digits.'})
      # store normalized digits-only value
      self.phone_number = cleaned

  def save(self, *args, **kwargs):
    # Ensure the phone number is normalized/validated on every save
    try:
      self.clean()
    except ValidationError:
      # re-raise so callers (forms/views) can handle/display errors
      raise
    super().save(*args, **kwargs)
