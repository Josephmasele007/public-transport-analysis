from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import TransportationData

class TransportationDataResource(resources.ModelResource):
    class Meta:
        model = TransportationData
        fields = ('id', 'road_name', 'route_name', 'bus_station', 'brt_station', 
                 'road_distance', 'peak_hours', 'average_speed', 'travel_time', 
                 'fare', 'landmark_nearby', 'road_type', 'traffic_lights_count')
        import_id_fields = ['id']

@admin.register(TransportationData)
class TransportationDataAdmin(ImportExportModelAdmin):
    resource_class = TransportationDataResource
    list_display = ('road_name', 'route_name', 'bus_station', 'brt_station', 
                   'road_distance', 'fare', 'road_type')
    list_filter = ('road_type', 'peak_hours')
    search_fields = ('road_name', 'route_name', 'bus_station')
    ordering = ('road_name', 'route_name')
    
    fieldsets = (
        ('Route Information', {
            'fields': ('road_name', 'route_name', 'road_type', 'road_distance')
        }),
        ('Station Details', {
            'fields': ('bus_station', 'brt_station', 'landmark_nearby')
        }),
        ('Time & Speed', {
            'fields': ('peak_hours', 'average_speed', 'travel_time', 'traffic_lights_count')
        }),
        ('Cost', {
            'fields': ('fare',)
        }),
    )
