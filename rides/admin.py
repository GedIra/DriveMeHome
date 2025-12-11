from django.contrib import admin
from .models import PricingConfiguration

@admin.register(PricingConfiguration)
class PricingConfigurationAdmin(admin.ModelAdmin):
  list_display = (
    'name', 
    'base_fare', 
    'price_per_km', 
    'price_per_minute', 
    'platform_commission_rate', 
    'is_active', 
    'created_at'
  )
  list_filter = ('is_active', 'created_at')
  search_fields = ('name',)
  readonly_fields = ('created_at',)
  
  fieldsets = (
    ('Configuration Identity', {
      'fields': ('name', 'is_active')
    }),
    ('Fare Calculation', {
      'fields': ('base_fare', 'price_per_km', 'price_per_minute'),
      'description': "These values determine the base cost for the customer."
    }),
    ('Business Logic', {
      'fields': ('platform_commission_rate',),
      'description': "The percentage (decimal) the platform keeps from the total fare."
    }),
    ('Audit', {
      'fields': ('created_at',),
    }),
  )
