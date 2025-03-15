from django.urls import path
from . import views

app_name = 'travel_cost'

urlpatterns = [
    path('', views.index, name='index'),
    path('predict-fare/', views.predict_fare, name='predict_fare'),
    path('refresh-stations/', views.refresh_stations, name='refresh_stations'),
    path('station/<int:station_id>/', views.get_station_details, name='get_station_details'),
]
