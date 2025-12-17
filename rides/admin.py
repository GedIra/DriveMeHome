from django.contrib import admin
from .models import PricingConfiguration, Ride, Transaction, Review

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

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'driver', 'status', 'final_price', 'created_at', 'scheduled_for')
    list_filter = ('status', 'created_at', 'scheduled_for')
    search_fields = ('customer__user__username', 'driver__user__username', 'pickup_address')
    
    # Show financial snapshot as read-only to prevent tampering
    readonly_fields = ('estimated_price', 'final_price', 'platform_fee', 'driver_earnings', 'distance_km', 'estimated_duration_min')

    fieldsets = (
        ('Ride Info', {
            'fields': ('customer', 'driver', 'vehicle', 'status', 'scheduled_for')
        }),
        ('Locations', {
            'fields': ('pickup_address', 'dropoff_address', 'distance_km', 'estimated_duration_min')
        }),
        ('Financials (Auto-Calculated)', {
            'fields': ('estimated_price', 'final_price', 'platform_fee', 'driver_earnings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'accepted_at', 'started_at', 'completed_at')
        })
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'ride', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('ride', 'reviewer', 'rating', 'reviewer_type', 'created_at')
    list_filter = ('rating', 'reviewer_type')