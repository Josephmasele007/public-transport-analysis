from django.urls import path
from . import views

app_name = 'travel_cost'

urlpatterns = [
    path('', views.index, name='index'),
]
