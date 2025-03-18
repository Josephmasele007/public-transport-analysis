from django.urls import path
from . import views

app_name = 'congestion'  # Add namespace

urlpatterns = [
    path('', views.index, name='index'),
    path('details/', views.congestion, name='details'),
    path('details/predict/', views.get_ml_prediction, name='predict'),
]
