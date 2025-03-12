from django.db import models

class TransportationData(models.Model):
    road_name = models.CharField(max_length=255)
    road_distance = models.FloatField()
    route_name = models.CharField(max_length=100)
    bus_station = models.CharField(max_length=255)
    brt_station = models.CharField(max_length=255)
    peak_hours = models.CharField(max_length=50)
    average_speed = models.IntegerField()
    travel_time = models.IntegerField()
    fare = models.IntegerField()
    landmark_nearby = models.CharField(max_length=255)
    road_type = models.CharField(max_length=100)
    traffic_lights_count = models.IntegerField()

    def __str__(self):
        return f"{self.road_name} - {self.route_name}"

    class Meta:
        verbose_name_plural = "Transportation Data"
