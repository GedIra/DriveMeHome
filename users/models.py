from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
  email = models.EmailField(unique=True)
  phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
  is_driver = models.BooleanField(default=False)
  is_customer = models.BooleanField(default=True)
  
  def __str__(self):
    return self.username
