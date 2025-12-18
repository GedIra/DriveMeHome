from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_driver = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)

    def __str__(self):
        return self.username

class DriverProfile(models.Model):
    class TransmissionType(models.TextChoices):
        AUTOMATIC_ONLY = 'AUTO', _('Automatic Only')
        MANUAL_AND_AUTOMATIC = 'BOTH', _('Manual & Automatic')

    class LicenseCategory(models.TextChoices):
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
    
    # Docs
    driving_license_file = models.FileField(upload_to='drivers/licenses/', blank=True, null=True)
    national_id_file = models.FileField(upload_to='drivers/ids/', blank=True, null=True)
    criminal_record_file = models.FileField(upload_to='drivers/criminal_records/', blank=True, null=True)
    other_documents_file = models.FileField(upload_to='drivers/others/', blank=True, null=True)

    # Capabilities
    license_category = models.CharField(
        max_length=5,
        choices=LicenseCategory.choices,
        default=LicenseCategory.CAT_B
    )
    license_score = models.IntegerField(default=10, help_text="Auto-calculated score")
    
    transmission_capability = models.CharField(
        max_length=10,
        choices=TransmissionType.choices,
        default=TransmissionType.AUTOMATIC_ONLY
    )
    
    current_status = models.CharField(
        max_length=20,
        choices=DriverStatus.choices,
        default=DriverStatus.OFFLINE
    )
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    average_rating = models.FloatField(default=5.0)

    def clean(self):
        # Validation: If verified, must have license number
        if self.is_verified and not self.license_number:
            raise ValidationError("Verified drivers must have a license number.")
        
        if self.current_latitude is not None:
            self.current_latitude = round(Decimal(str(self.current_latitude)), 6) 
        if self.current_longitude is not None:
            self.current_longitude = round(Decimal(str(self.current_longitude)), 6)

    def save(self, *args, **kwargs):
        scores = {'A': 5, 'B': 10, 'C': 20, 'D': 30, 'E': 40, 'F': 100}
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
    name = models.CharField(max_length=50)
    plate_number = models.CharField(max_length=20, blank=True, null=True)
    transmission_type = models.CharField(max_length=10, choices=TransmissionType.choices, default=TransmissionType.AUTOMATIC)
    vehicle_category = models.CharField(max_length=5, choices=VehicleCategory.choices, default=VehicleCategory.CAT_B)
    required_license_score = models.IntegerField(default=10, editable=False)

    def save(self, *args, **kwargs):
        scores = {'A': 5, 'B': 10, 'C': 20, 'D': 30, 'E': 40, 'F': 100}
        self.required_license_score = scores.get(self.vehicle_category, 10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_vehicle_category_display()})"

class EmergencyContact(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    relationship = models.CharField(max_length=50, blank=True, null=True)

    def clean(self):
        if self.phone_number:
             # Basic validation (can be enhanced with regex)
             if not self.phone_number.replace("+", "").isdigit():
                 raise ValidationError("Phone number contains invalid characters.")

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.phone_number = self.phone_number.replace(" ", "")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} for {self.customer.user.username}"

class PreferredDestination(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='preferred_destinations')
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def clean(self):
        # Round coordinates to 6 decimal places to prevent database errors
        if self.latitude is not None:
            self.latitude = round(Decimal(str(self.latitude)), 6)
        if self.longitude is not None:
            self.longitude = round(Decimal(str(self.longitude)), 6)
            
    def save(self, *args, **kwargs):
        self.clean() # Ensure clean is called on save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}: {self.address}"