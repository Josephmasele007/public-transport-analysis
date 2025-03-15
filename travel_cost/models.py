from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class FareCalculator(models.Model):
    name = models.CharField(max_length=100)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    distance_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    peak_hour_surcharge = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    traffic_light_surcharge = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    distance_discount_threshold = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    distance_discount_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fare Calculator'
        verbose_name_plural = 'Fare Calculators'

    def __str__(self):
        return self.name

    def calculate_fare(self, distance, is_peak_hour=False, traffic_lights=0):
        """
        Calculate fare based on distance and conditions
        """
        # Base fare
        total_fare = self.base_fare

        # Distance-based fare
        distance_fare = float(distance) * float(self.distance_rate)
        total_fare += distance_fare

        # Apply distance discount if applicable
        if float(distance) >= float(self.distance_discount_threshold):
            discount = (distance_fare * float(self.distance_discount_rate)) / 100
            total_fare -= discount

        # Peak hour surcharge
        if is_peak_hour:
            surcharge = (total_fare * float(self.peak_hour_surcharge)) / 100
            total_fare += surcharge

        # Traffic light surcharge
        if traffic_lights > 0:
            traffic_surcharge = (total_fare * float(self.traffic_light_surcharge) * traffic_lights) / 100
            total_fare += traffic_surcharge

        return round(total_fare, 2)

class FareHistory(models.Model):
    calculator = models.ForeignKey(FareCalculator, on_delete=models.CASCADE)
    start_station = models.CharField(max_length=100)
    end_station = models.CharField(max_length=100)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance_fare = models.DecimalField(max_digits=10, decimal_places=2)
    peak_hour_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    traffic_light_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    distance_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    is_peak_hour = models.BooleanField(default=False)
    traffic_lights = models.IntegerField(default=0)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fare History'
        verbose_name_plural = 'Fare Histories'
        ordering = ['-calculated_at']

    def __str__(self):
        return f"Fare from {self.start_station} to {self.end_station} - {self.total_fare}"
