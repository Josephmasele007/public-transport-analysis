from django.contrib import admin
# Remove the TransportationData registration since it's already registered in dashboard.admin.py

# Register your models here if needed
# Note: If models are registered in dashboard.admin.py, you don't need to register them here

from .models import Settings, TrafficRecord

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key', 'value')
    readonly_fields = ('updated_at',)

@admin.register(TrafficRecord)
class TrafficRecordAdmin(admin.ModelAdmin):
    list_display = ('route', 'traffic_level', 'timestamp')
    list_filter = ('traffic_level', 'route', 'timestamp')
    search_fields = ('route__name', 'description')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    fieldsets = (
        ('Route Information', {
            'fields': ('route', 'traffic_level')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        })
    )
