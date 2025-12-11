from django.db import models
from django.utils.translation import gettext_lazy as _

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
