from django.urls import path
from . import views

app_name = 'congestion'  # Add namespace

urlpatterns = [
    path('', views.congestion, name='congestion'),
    path('analysis/', views.analysis, name='analysis'),
    path('congestion_map/', views.congestion_map, name='congestion_map')]
