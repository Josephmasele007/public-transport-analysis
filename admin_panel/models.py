from django.db import models

# Create your models here.

class Settings(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'

    def __str__(self):
        return self.key
