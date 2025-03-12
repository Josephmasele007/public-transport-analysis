from django.shortcuts import render
from django.db.models import Count, Avg, Sum
from django.db.models.functions import ExtractHour
from .models import Station, Route, RouteStation, StationTraffic
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
import json

def index(request):
    # Basic station statistics
    total_stations = Station.objects.count()
    brt_stations = Station.objects.filter(station_type='brt').count()
    bus_stations = Station.objects.filter(station_type='bus').count()
    both_stations = Station.objects.filter(station_type='both').count()

    # Get all routes
    routes = Route.objects.filter(is_active=True)
    
    # Calculate average routes per station
    total_route_stations = RouteStation.objects.count()
    avg_routes = round(total_route_stations / total_stations if total_stations > 0 else 0, 1)

    # Get today's date for traffic statistics
    today = timezone.now().date()
    
    # Get hourly passenger counts for today
    hourly_traffic = StationTraffic.objects.filter(
        date=today
    ).values('hour').annotate(
        total_passengers=Sum('passenger_count')
    ).order_by('hour')

    # Get busiest stations
    busiest_stations = StationTraffic.objects.filter(
        date=today
    ).values('station__name', 'station__station_type').annotate(
        total_passengers=Sum('passenger_count')
    ).order_by('-total_passengers')[:5]

    # Get all stations with their details
    stations = Station.objects.all().prefetch_related('routestation_set__route')
    
    station_data = []
    for station in stations:
        # Get routes for this station
        routes = Route.objects.filter(routestation__station=station).distinct()
        
        # Get today's traffic for this station
        today_traffic = StationTraffic.objects.filter(
            station=station,
            date=today
        ).aggregate(
            total_passengers=Sum('passenger_count')
        )['total_passengers'] or 0

        # Get peak hours for this station
        peak_hours = StationTraffic.objects.filter(
            station=station,
            date=today
        ).order_by('-passenger_count')[:2]

        station_data.append({
            'id': station.id,
            'name': station.name,
            'station_type': station.station_type,
            'location': station.location,
            'landmark_nearby': station.landmark_nearby,
            'is_operational': station.is_operational,
            'opening_time': station.opening_time,
            'closing_time': station.closing_time,
            'capacity': station.capacity,
            'routes': [{'name': r.name, 'fare': r.fare} for r in routes],
            'today_traffic': today_traffic,
            'peak_hours': [f"{h.hour}:00" for h in peak_hours],
            'coordinates': {
                'lat': float(station.latitude) if station.latitude else None,
                'lng': float(station.longitude) if station.longitude else None
            }
        })

    context = {
        'total_stations': total_stations,
        'brt_stations_count': brt_stations,
        'bus_stations_count': bus_stations,
        'both_stations_count': both_stations,
        'avg_routes_per_station': avg_routes,
        'hourly_traffic': list(hourly_traffic),
        'busiest_stations': list(busiest_stations),
        'stations': station_data,
        'routes': routes,
        'page_title': 'Station Management',
        'station_types': [{'value': t[0], 'label': t[1]} for t in Station.STATION_TYPES]
    }

    return render(request, 'stations/index.html', context)

def stations(request):
    try:
        stations = Station.objects.all().order_by('name')
        return render(request, 'stations/stations.html', {
            'stations': stations,
            'page_title': 'Stations List'
        })
    except Exception as e:
        messages.error(request, f"Error loading stations: {str(e)}")
        return render(request, 'stations/stations.html', {
            'error': True,
            'page_title': 'Stations List - Error'
        })

def stations_view(request):
    stations = Station.objects.all()
    return render(request, 'stations.html', {'stations': stations})

def station_list(request):
    stations = Station.objects.all()
    return render(request, 'stations/index.html', {'stations': stations})
