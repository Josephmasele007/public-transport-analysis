"""
URL configuration for optimizing_transport project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:ve
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('home.urls', namespace='home')),
    path('admin/', admin.site.urls),
    path('admin_panel/', include('admin_panel.urls', namespace='admin_panel')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('explorer/', include('explorer.urls', namespace='explorer')),
    path('stations/', include('stations.urls', namespace='stations')),
    path('congestion/', include('congestion.urls', namespace='congestion')),
    path('travel_cost/', include('travel_cost.urls', namespace='travel_cost')),
    path('reports/', include('reports.urls', namespace='reports')),
]
