from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomerProfile, DriverProfile, CustomerVehicle
from .utils import get_distance_and_duration
from decimal import Decimal

class PricingConfiguration(models.Model):
  """
  Stores pricing rules. 
  Only one record should be 'active' at a time.
  """
  name = models.CharField(max_length=50, help_text="e.g., 'Standard 2025' or 'Rainy Season Surge'")
  
  # Fare Calculation Factors
  base_fare = models.DecimalField(max_digits=6, decimal_places=2, help_text="Starting fee for the ride")
  price_per_km = models.DecimalField(max_digits=6, decimal_places=2, help_text="Cost per kilometer")
  price_per_minute = models.DecimalField(max_digits=6, decimal_places=2, help_text="Cost per minute (traffic/waiting)")
  
  # Business Logic
  platform_commission_rate = models.DecimalField(
    max_digits=4, 
    decimal_places=2, 
    help_text="Decimal percentage (e.g., 0.20 for 20%)"
  )
  
  is_active = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)

  def save(self, *args, **kwargs):
    # Logic: If we set this one to Active, deactivate all others
    if self.is_active:
      PricingConfiguration.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
    super().save(*args, **kwargs)

  def __str__(self):
    return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
  

class Ride(models.Model):
  class RideStatus(models.TextChoices):
    REQUESTED = 'REQUESTED', 'Requested'
    DRIVER_ASSIGNED = 'ASSIGNED', 'Driver Assigned'
    DRIVER_ARRIVED = 'ARRIVED', 'Driver Arrived'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

  # --- RELATIONS ---
  customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='rides')
  driver = models.ForeignKey(DriverProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='rides')
  vehicle = models.ForeignKey(CustomerVehicle, on_delete=models.SET_NULL, null=True, related_name='rides')
  
  # --- LOCATION DATA ---
  pickup_address = models.CharField(max_length=255)
  pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6)
  pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6)
  
  dropoff_address = models.CharField(max_length=255)
  dropoff_latitude = models.DecimalField(max_digits=9, decimal_places=6)
  dropoff_longitude = models.DecimalField(max_digits=9, decimal_places=6)
  
  # --- TRIP METRICS (Populated via Maps API) ---
  distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
  estimated_duration_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
  
  # --- STATUS & TIMESTAMPS ---
  status = models.CharField(max_length=20, choices=RideStatus.choices, default=RideStatus.REQUESTED)
  created_at = models.DateTimeField(auto_now_add=True)
  accepted_at = models.DateTimeField(null=True, blank=True)
  started_at = models.DateTimeField(null=True, blank=True)
  completed_at = models.DateTimeField(null=True, blank=True)
  
  # --- FINANCIAL SNAPSHOT (Anti-Data Loss) ---
  estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
  final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
  platform_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
  driver_earnings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
  
  # Store the pricing rules used for this specific ride (Audit trail)
  applied_base_fare = models.DecimalField(max_digits=6, decimal_places=2, null=True)
  applied_rate_per_km = models.DecimalField(max_digits=6, decimal_places=2, null=True)
  applied_rate_per_min = models.DecimalField(max_digits=6, decimal_places=2, null=True)

  def estimate_fare(self):
    """
    Calls Google Maps to get distance/time, then calculates price based on Active Config.
    """
    # 1. Get Distance & Duration from Utility
    # Note: Ensure self.pickup_latitude etc are converted to strings/floats if needed by the utility, 
    # though Decimal usually works fine or can be cast inside the utility.
    metrics = get_distance_and_duration(
      self.pickup_latitude, 
      self.pickup_longitude, 
      self.dropoff_latitude, 
      self.dropoff_longitude
    )
    
    if metrics:
      self.distance_km = metrics['distance_km']
      self.estimated_duration_min = metrics['duration_min']
      
      # 2. Get Active Pricing
      try:
        # Use .first() in case multiple are accidentally active
        config = PricingConfiguration.objects.filter(is_active=True).first()
        if config:
          # 3. Calculate Price
          # Formula: Base + (Km * Price/Km) + (Min * Price/Min)
          cost = config.base_fare + \
                  (self.distance_km * config.price_per_km) + \
                  (self.estimated_duration_min * config.price_per_minute)
          
          self.estimated_price = round(cost, 2)
          
          # Snapshot the rates used so we know how we got this price
          self.applied_base_fare = config.base_fare
          self.applied_rate_per_km = config.price_per_km
          self.applied_rate_per_min = config.price_per_minute
          
          self.save()
          return self.estimated_price
      except PricingConfiguration.DoesNotExist:
        return None
    return None

  def __str__(self):
    return f"Ride #{self.id} - {self.status}"

class Transaction(models.Model):
  class PaymentMethod(models.TextChoices):
    CASH = 'CASH', 'Cash'
    MOMO = 'MOMO', 'Mobile Money'
    CARD = 'CARD', 'Credit/Debit Card'

  class TransactionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'

  ride = models.OneToOneField('Ride', on_delete=models.CASCADE, related_name='transaction')
  amount = models.DecimalField(max_digits=10, decimal_places=2)
  payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
  
  # External References (for Momo/Stripe)
  external_transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID from Stripe/Momo")
  
  status = models.CharField(max_length=10, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f"Txn #{self.id} - {self.amount} RWF ({self.status})"

class Review(models.Model):
  class ReviewerType(models.TextChoices):
    DRIVER = 'DRIVER', 'Driver'
    CUSTOMER = 'CUSTOMER', 'Customer'

  ride = models.ForeignKey('Ride', on_delete=models.CASCADE, related_name='reviews')
  reviewer = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='reviews_given')
  
  rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="1 to 5 stars")
  comment = models.TextField(blank=True, null=True)
  
  reviewer_type = models.CharField(max_length=10, choices=ReviewerType.choices)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.rating}★ by {self.reviewer.username}"