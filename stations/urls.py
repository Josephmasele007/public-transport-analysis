from django.urls import path
from . import views

app_name = 'stations'

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.stations, name='stations_list'),
]
