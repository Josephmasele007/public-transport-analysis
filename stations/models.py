from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import time

class Station(models.Model):
    STATION_TYPES = [
        ('bus', 'Bus Station'),
        ('brt', 'BRT Station'),
        ('both', 'Bus & BRT Station')
    ]

    name = models.CharField(max_length=100)
    station_type = models.CharField(max_length=4, choices=STATION_TYPES, default='bus')
    location = models.CharField(max_length=200, default='Dar es Salaam')
    landmark_nearby = models.CharField(max_length=200, blank=True)
    capacity = models.IntegerField(default=0)
    is_operational = models.BooleanField(default=True)
    opening_time = models.TimeField(default=time(6, 0))  # Default: 6:00 AM
    closing_time = models.TimeField(default=time(22, 0))  # Default: 10:00 PM
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_station_type_display()})"

class Route(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    stations = models.ManyToManyField(Station, through='RouteStation')
    distance = models.DecimalField(max_digits=8, decimal_places=2)  # in kilometers
    estimated_time = models.IntegerField()  # in minutes
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class RouteStation(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    order = models.IntegerField()
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    stop_duration = models.IntegerField()  # in minutes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['route', 'order']
        unique_together = [['route', 'order'], ['route', 'station']]

    def __str__(self):
        return f"{self.route.name} - Stop {self.order}: {self.station.name}"

class StationTraffic(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    date = models.DateField()
    hour = models.IntegerField()
    passenger_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['station', 'date', 'hour']

    def __str__(self):
        return f"{self.station.name} - {self.date} {self.hour}:00"
