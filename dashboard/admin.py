from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import IntegerWidget, FloatWidget
from import_export.formats import base_formats
from .models import TransportData

class TransportDataResource(resources.ModelResource):
    # Define fields with widgets for proper type conversion
    road_distance = fields.Field(attribute='road_distance', widget=FloatWidget())
    average_speed = fields.Field(attribute='average_speed', widget=FloatWidget())
    travel_time = fields.Field(attribute='travel_time', widget=FloatWidget())
    fare = fields.Field(attribute='fare', widget=FloatWidget())
    traffic_lights_count = fields.Field(attribute='traffic_lights_count', widget=IntegerWidget())
    passenger_capacity = fields.Field(attribute='passenger_capacity', widget=IntegerWidget())
    
    class Meta:
        model = TransportData
        import_id_fields = ['id']
        fields = ('id', 'road_name', 'route_name', 'bus_station', 'brt_station', 
                 'road_distance', 'peak_hours', 'average_speed', 'travel_time', 
                 'fare', 'landmark_nearby', 'road_type', 'traffic_lights_count',
                 'route_type', 'congestion_level', 'passenger_capacity',
                 'alternative_routes', 'bus_station_location', 'brt_station_location',
                 'geojson_data')
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Set default values for required fields if they're missing"""
        # Default values for required fields
        defaults = {
            'passenger_capacity': '0',
            'route_type': 'regular',
            'congestion_level': 'low',
            'traffic_lights_count': '0',
            'road_distance': '0.0',
            'average_speed': '0.0',
            'travel_time': '0.0',
            'fare': '0.0',
            'alternative_routes': '',
            'bus_station_location': '',
            'brt_station_location': '',
            'geojson_data': '',
            'landmark_nearby': '',
            'road_type': 'normal'
        }
        
        # Apply defaults for any missing fields
        for field, default in defaults.items():
            if not row.get(field):
                row[field] = default

@admin.register(TransportData)
class TransportDataAdmin(ImportExportModelAdmin):
    resource_class = TransportDataResource
    list_display = ('road_name', 'route_name', 'bus_station', 'brt_station', 
                   'road_distance', 'fare', 'road_type', 'congestion_level')
    list_filter = ('road_type', 'peak_hours', 'route_type', 'congestion_level')
    search_fields = ('road_name', 'route_name', 'bus_station', 'brt_station', 
                    'landmark_nearby', 'alternative_routes')
    ordering = ('road_name', 'route_name')
    
    fieldsets = (
        ('Route Information', {
            'fields': ('road_name', 'route_name', 'road_type', 'route_type', 'road_distance')
        }),
        ('Station Details', {
            'fields': (
                'bus_station', 'bus_station_location',
                'brt_station', 'brt_station_location',
                'landmark_nearby'
            )
        }),
        ('Time & Speed', {
            'fields': ('peak_hours', 'average_speed', 'travel_time', 'traffic_lights_count')
        }),
        ('Traffic & Capacity', {
            'fields': ('congestion_level', 'passenger_capacity', 'alternative_routes')
        }),
        ('Cost', {
            'fields': ('fare',)
        }),
        ('Geographic Data', {
            'fields': ('geojson_data',),
            'classes': ('collapse',)
        })
    )

    def get_import_formats(self):
        """Returns available import formats."""
        formats = [base_formats.CSV]  # Only use CSV format
        return [f for f in formats if f().can_import()]

    class Media:
        css = {
            'all': ('admin/css/import_export.css',)
        }

    def get_help_text(self):
        return """
        CSV Import Instructions:
        1. Required columns in your CSV file:
           - road_name: Road name
           - route_name: Route name
           - bus_station: Bus station name
           - brt_station: BRT station name
           - peak_hours: Peak hours

        2. Optional numeric columns (will default to 0 if empty):
           - road_distance: Distance in kilometers
           - average_speed: Average speed in km/h
           - travel_time: Travel time in minutes
           - fare: Fare amount
           - traffic_lights_count: Number of traffic lights
           - passenger_capacity: Passenger capacity

        3. Optional text columns (will be empty if not provided):
           - landmark_nearby: Nearby landmarks
           - road_type: Type of road (defaults to 'normal')
           - route_type: Type of route (defaults to 'regular')
           - congestion_level: Level of congestion (defaults to 'low')
           - alternative_routes: Alternative route information
           - bus_station_location: Bus station location details
           - brt_station_location: BRT station location details
           - geojson_data: Geographic data in GeoJSON format

        4. Notes:
           - All numeric fields will default to 0 if empty
           - Text fields can be empty
           - Save your file as CSV (Comma delimited)
           - Make sure to include at least the required columns
        """
