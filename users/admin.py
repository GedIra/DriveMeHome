from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
  CustomUser, 
  DriverProfile, 
  CustomerProfile, 
  EmergencyContact, 
  PreferredDestination,
  CustomerVehicle
)

# --- INLINES ---
# These allow you to edit related data directly inside the Parent profile page

class EmergencyContactInline(admin.TabularInline):
  model = EmergencyContact
  extra = 1  # Show one empty row by default

class PreferredDestinationInline(admin.TabularInline):
  model = PreferredDestination
  extra = 1

class CustomerVehicleInline(admin.StackedInline):
  model = CustomerVehicle
  extra = 1

# --- ADMIN DEFINITIONS ---

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
  # Add your custom fields to the list view
  list_display = ('username', 'email', 'phone_number', 'is_driver', 'is_customer', 'is_staff')
  list_filter = ('is_driver', 'is_customer', 'is_staff', 'is_active')
  
  # Add your custom fields to the edit form
  fieldsets = UserAdmin.fieldsets + (
    ('Role & Contact', {'fields': ('phone_number', 'is_driver', 'is_customer')}),
  )
  add_fieldsets = UserAdmin.add_fieldsets + (
    ('Role & Contact', {'fields': ('phone_number', 'is_driver', 'is_customer')}),
  )

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
  list_display = (
    'user', 
    'license_category', 
    'license_score', 
    'transmission_capability', 
    'current_status', 
    'is_verified', 
    'average_rating'
  )
  list_filter = ('license_category', 'transmission_capability', 'current_status', 'is_verified')
  search_fields = ('user__username', 'user__email', 'license_number')
  
  # Organize the detailed view
  fieldsets = (
    ('User Info', {
      'fields': ('user', 'profile_picture')
    }),
    ('License & Skills', {
      'fields': ('license_number', 'license_expiry_date', 'license_category', 'transmission_capability', 'license_score')
    }),
    ('Status', {
      'fields': ('is_verified', 'current_status', 'current_latitude', 'current_longitude')
    }),
    ('Metrics', {
      'fields': ('average_rating',)
    }),
  )
  readonly_fields = ('license_score',) # Auto-calculated, so read-only in admin

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
  list_display = ('user', 'vehicle_count')
  search_fields = ('user__username', 'user__email')
  
  # Add the inlines here so you can add cars/contacts while viewing the customer
  inlines = [EmergencyContactInline, PreferredDestinationInline, CustomerVehicleInline]

  def vehicle_count(self, obj):
    return obj.vehicles.count()
  vehicle_count.short_description = "Vehicles Owned"

# We register these separately too, in case you want to view them as a master list
@admin.register(CustomerVehicle)
class CustomerVehicleAdmin(admin.ModelAdmin):
  list_display = ('name', 'customer', 'vehicle_category', 'transmission_type', 'plate_number')
  list_filter = ('vehicle_category', 'transmission_type')
  search_fields = ('name', 'plate_number', 'customer__user__username')

admin.site.register(EmergencyContact)
admin.site.register(PreferredDestination)