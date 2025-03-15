from django.db import models
from stations.models import Route

# Create your models here.

class Settings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"

class TrafficRecord(models.Model):
    TRAFFIC_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('severe', 'Severe'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='traffic_records')
    traffic_level = models.CharField(max_length=10, choices=TRAFFIC_LEVELS)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Traffic Record'
        verbose_name_plural = 'Traffic Records'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.route.name} - {self.traffic_level} ({self.timestamp})"
