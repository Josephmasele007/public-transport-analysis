from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('insights/', views.insights, name='insights'),
    path('congestion_analysis/', views.congestion_analysis, name='congestion_analysis'),
]
