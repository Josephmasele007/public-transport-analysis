from django.contrib import admin
from django.utils.html import format_html
from .models import Station, Route, RouteStation, StationTraffic

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'station_type', 'location', 'capacity', 'is_operational', 
                   'opening_time', 'closing_time', 'map_link')
    list_filter = ('station_type', 'is_operational')
    search_fields = ('name', 'location', 'landmark_nearby')
    ordering = ('name',)
    
    def map_link(self, obj):
        if obj.latitude and obj.longitude:
            url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html('<a href="{}" target="_blank">View on Map</a>', url)
        return "No location data"
    map_link.short_description = "Map"

class RouteStationInline(admin.TabularInline):
    model = RouteStation
    extra = 1
    ordering = ('order',)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'distance', 'estimated_time', 'fare', 'is_active', 
                   'station_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    inlines = [RouteStationInline]
    
    def station_count(self, obj):
        return obj.stations.count()
    station_count.short_description = "Number of Stations"

@admin.register(RouteStation)
class RouteStationAdmin(admin.ModelAdmin):
    list_display = ('route', 'station', 'order', 'arrival_time', 'departure_time', 
                   'stop_duration')
    list_filter = ('route', 'station')
    search_fields = ('route__name', 'station__name')
    ordering = ('route', 'order')

@admin.register(StationTraffic)
class StationTrafficAdmin(admin.ModelAdmin):
    list_display = ('station', 'date', 'hour', 'passenger_count')
    list_filter = ('station', 'date')
    search_fields = ('station__name',)
    date_hierarchy = 'date'
    ordering = ('-date', 'hour')

    class Media:
        css = {
            'all': ('admin/css/station_admin.css',)
        }
