from django.db import models

class TransportData(models.Model):
    road_name = models.CharField(max_length=255)
    road_distance = models.FloatField()
    route_name = models.CharField(max_length=255)
    bus_station = models.CharField(max_length=255)
    brt_station = models.CharField(max_length=255)
    peak_hours = models.CharField(max_length=50)
    average_speed = models.FloatField()
    travel_time = models.FloatField()
    fare = models.FloatField()
    landmark_nearby = models.CharField(max_length=255)
    road_type = models.CharField(max_length=50)
    traffic_lights_count = models.IntegerField()
    route_type = models.CharField(max_length=50)
    congestion_level = models.CharField(max_length=50)
    passenger_capacity = models.IntegerField()
    alternative_routes = models.CharField(max_length=255)
    bus_station_location = models.CharField(max_length=255)
    brt_station_location = models.CharField(max_length=255)
    geojson_data = models.TextField()

    def __str__(self):
        return self.route_name