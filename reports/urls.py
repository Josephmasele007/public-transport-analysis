from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('update/', views.update_report, name='update_report'),
    path('filter/', views.filter_report, name='filter_report'),
]
