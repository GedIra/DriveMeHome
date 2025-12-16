from django.db import models
from django.contrib.auth.models import AbstractUser
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

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

class DriverProfile(models.Model):
  class TransmissionType(models.TextChoices):
    AUTOMATIC_ONLY = 'AUTO', _('Automatic Only')
    MANUAL_AND_AUTOMATIC = 'BOTH', _('Manual & Automatic')

  class LicenseCategory(models.TextChoices):
    # We assign internal codes, but the score logic handles the capability
    CAT_A = 'A', _('Category A (Motorcycles)')
    CAT_B = 'B', _('Category B (Standard Cars)')
    CAT_C = 'C', _('Category C (Trucks)')
    CAT_D = 'D', _('Category D (Buses)')
    CAT_E = 'E', _('Category E (Heavy Trailers)')
    CAT_F = 'F', _('Category F (Special Machinery)')

  class DriverStatus(models.TextChoices):
    OFFLINE = 'OFFLINE', _('Offline')
    AVAILABLE = 'AVAILABLE', _('Available')
    BUSY = 'BUSY', _('Busy on Ride')

  user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='driver_profile')
  profile_picture = models.ImageField(upload_to='drivers/avatars/', blank=True, null=True)
  
  # Verification
  license_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
  license_expiry_date = models.DateField(blank=True, null=True)
  is_verified = models.BooleanField(default=False)

  # --- VERIFICATION DOCUMENTS ---
  driving_license_file = models.FileField(upload_to='drivers/licenses/', blank=True, null=True, help_text="Upload scanned copy of driving license")
  national_id_file = models.FileField(upload_to='drivers/ids/', blank=True, null=True, help_text="Upload national ID or Passport")
  criminal_record_file = models.FileField(upload_to='drivers/criminal_records/', blank=True, null=True, help_text="Certificate of non-conviction")
  other_documents_file = models.FileField(upload_to='drivers/others/', blank=True, null=True, help_text="Any other relevant certifications")

  
  # Capabilities
  license_category = models.CharField(
    max_length=5,
    choices=LicenseCategory.choices,
    default=LicenseCategory.CAT_B,
    help_text="Highest category held by the driver"
  )
  license_score = models.IntegerField(default=10, help_text="Auto-calculated score for matching logic")
  
  transmission_capability = models.CharField(
    max_length=10,
    choices=TransmissionType.choices,
    default=TransmissionType.AUTOMATIC_ONLY
  )
  
  # Operational Status
  current_status = models.CharField(
    max_length=20,
    choices=DriverStatus.choices,
    default=DriverStatus.OFFLINE
  )
  current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
  current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
  
  average_rating = models.FloatField(default=5.0)

  def save(self, *args, **kwargs):
    # Auto-calculate score based on Hierarchy: B < C < D < E
    # A and F are distinct/special.
    scores = {
      'A': 5,   # Distinct low score
      'B': 10,  # Base car
      'C': 20,  # Truck (Implies B)
      'D': 30,  # Bus (Implies C, B)
      'E': 40,  # Trailer (Implies D, C, B)
      'F': 100  # Distinct high score
    }
    self.license_score = scores.get(self.license_category, 0)
    super().save(*args, **kwargs)

  def __str__(self):
    return f"Driver: {self.user.username} [{self.license_category}]"

  
class CustomerProfile(models.Model):
  user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='customer_profile')
  profile_picture = models.ImageField(upload_to='customers/avatars/', blank=True, null=True)

  def __str__(self):
    return f"Customer: {self.user.username}"

class CustomerVehicle(models.Model):
  """
  Stores the customer's vehicle details to easily book a driver 
  who is capable of driving this specific car.
  """
  class TransmissionType(models.TextChoices):
    AUTOMATIC = 'AUTO', _('Automatic')
    MANUAL = 'MANUAL', _('Manual')

  class VehicleCategory(models.TextChoices):
    CAT_A = 'A', _('Category A (Motorcycle)')
    CAT_B = 'B', _('Category B (Car/Jeep)')
    CAT_C = 'C', _('Category C (Truck)')
    CAT_D = 'D', _('Category D (Bus)')
    CAT_E = 'E', _('Category E (Heavy Machine/Trailer)')
    CAT_F = 'F', _('Category F (Special)')

  customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='vehicles')
  name = models.CharField(max_length=50, help_text="e.g. My Prado, Office Bus")
  
  # Vehicle Details for Matching
  plate_number = models.CharField(max_length=20, blank=True, null=True)
  transmission_type = models.CharField(max_length=10, choices=TransmissionType.choices, default=TransmissionType.AUTOMATIC)
  vehicle_category = models.CharField(max_length=5, choices=VehicleCategory.choices, default=VehicleCategory.CAT_B)
  
  # For matching logic
  required_license_score = models.IntegerField(default=10, editable=False)

  def save(self, *args, **kwargs):
    # Auto-set the score required to drive this car
    scores = {
      'A': 5,
      'B': 10,
      'C': 20,
      'D': 30,
      'E': 40,
      'F': 100
    }
    self.required_license_score = scores.get(self.vehicle_category, 10)
    super().save(*args, **kwargs)

  def __str__(self):
    return f"{self.name} ({self.get_vehicle_category_display()})"

class EmergencyContact(models.Model):
  customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='emergency_contacts')
  name = models.CharField(max_length=100)
  phone_number = models.CharField(max_length=15)
  relationship = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Spouse, Parent, Friend")

  def __str__(self):
    return f"{self.name} ({self.relationship}) for {self.customer.user.username}"
  
  def clean(self):
    super().clean()
    if self.phone_number:
      cleaned = re.sub(r"\D", "", str(self.phone_number))
      if cleaned == "":
        self.phone_number = None
        return
      if len(cleaned) < 10 or len(cleaned) > 15:
        raise ValidationError({'phone_number': 'Phone number must contain between 10 and 15 digits.'})
      self.phone_number = cleaned

  def save(self, *args, **kwargs):
    try:
      self.clean()
    except ValidationError:
      raise
    super().save(*args, **kwargs)

class PreferredDestination(models.Model):
  customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='preferred_destinations')
  name = models.CharField(max_length=50, help_text="e.g. Home, Work, Gym")
  address = models.CharField(max_length=255)
  latitude = models.DecimalField(max_digits=9, decimal_places=6)
  longitude = models.DecimalField(max_digits=9, decimal_places=6)

  def __str__(self):
    return f"{self.name}: {self.address}"