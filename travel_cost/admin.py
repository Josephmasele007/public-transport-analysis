from django.contrib import admin
from .models import FareCalculator, FareHistory

@admin.register(FareCalculator)
class FareCalculatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_fare', 'distance_rate', 'peak_hour_surcharge', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active')
        }),
        ('Fare Components', {
            'fields': ('base_fare', 'distance_rate')
        }),
        ('Surcharges', {
            'fields': ('peak_hour_surcharge', 'traffic_light_surcharge')
        }),
        ('Discounts', {
            'fields': ('distance_discount_threshold', 'distance_discount_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(FareHistory)
class FareHistoryAdmin(admin.ModelAdmin):
    list_display = ('start_station', 'end_station', 'distance', 'total_fare', 'is_peak_hour', 'calculated_at')
    list_filter = ('calculator', 'is_peak_hour', 'calculated_at')
    search_fields = ('start_station', 'end_station')
    readonly_fields = ('calculated_at',)
    ordering = ('-calculated_at',)
    fieldsets = (
        ('Route Information', {
            'fields': ('calculator', 'start_station', 'end_station', 'distance')
        }),
        ('Fare Breakdown', {
            'fields': ('base_fare', 'distance_fare', 'peak_hour_surcharge', 'traffic_light_surcharge', 'distance_discount', 'total_fare')
        }),
        ('Conditions', {
            'fields': ('is_peak_hour', 'traffic_lights')
        }),
        ('Timestamp', {
            'fields': ('calculated_at',),
            'classes': ('collapse',)
        })
    )
