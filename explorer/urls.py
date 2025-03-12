from django.urls import path
from . import views

app_name = 'explorer'

urlpatterns = [
    path('', views.index, name='index'),
    path('roads/', views.roads, name='roads'),
    path('routes/', views.routes, name='routes'),
    ]
