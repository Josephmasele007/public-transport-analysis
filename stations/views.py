from django.shortcuts import render
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import ExtractHour
from .models import Station, Route, RouteStation, StationTraffic
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
import json
from dashboard.models import TransportData
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def index(request):
    # Get search query and filters
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('type', 'all')
    filter_status = request.GET.get('status', 'all')
    page = request.GET.get('page', 1)

    # Base queryset
    stations_data = []
    
    # Get all unique bus stations
    bus_stations = TransportData.objects.exclude(
        bus_station=''
    ).values(
        'bus_station',
        'bus_station_location',
        'route_name',
        'peak_hours',
        'passenger_capacity',
        'landmark_nearby'
    ).distinct()

    # Get all unique BRT stations
    brt_stations = TransportData.objects.exclude(
        brt_station=''
    ).values(
        'brt_station',
        'brt_station_location',
        'route_name',
        'peak_hours',
        'passenger_capacity',
        'landmark_nearby'
    ).distinct()

    # Process bus stations
    for station in bus_stations:
        if station['bus_station'] and station['bus_station_location']:
            lat, lng = station['bus_station_location'].split(',')
            stations_data.append({
                'name': station['bus_station'],
                'type': 'Bus Station',
                'location': f"({lat}, {lng})",
                'route': station['route_name'],
                'capacity': station['passenger_capacity'],
                'peak_hours': station['peak_hours'],
                'landmark': station['landmark_nearby'],
                'is_operational': True  # You might want to add logic for this
            })

    # Process BRT stations
    for station in brt_stations:
        if station['brt_station'] and station['brt_station_location']:
            lat, lng = station['brt_station_location'].split(',')
            stations_data.append({
                'name': station['brt_station'],
                'type': 'BRT Station',
                'location': f"({lat}, {lng})",
                'route': station['route_name'],
                'capacity': station['passenger_capacity'],
                'peak_hours': station['peak_hours'],
                'landmark': station['landmark_nearby'],
                'is_operational': True  # You might want to add logic for this
            })

    # Apply search filter
    if search_query:
        stations_data = [
            station for station in stations_data
            if search_query.lower() in station['name'].lower() or
               search_query.lower() in station['location'].lower() or
               search_query.lower() in station['landmark'].lower()
        ]

    # Apply type filter
    if filter_type != 'all':
        stations_data = [
            station for station in stations_data
            if station['type'].lower() == filter_type.lower()
        ]

    # Apply operational status filter
    if filter_status != 'all':
        is_operational = filter_status == 'operational'
        stations_data = [
            station for station in stations_data
            if station['is_operational'] == is_operational
        ]

    # Calculate statistics before pagination
    total_stations = len(stations_data)
    bus_station_count = sum(1 for s in stations_data if s['type'] == 'Bus Station')
    brt_station_count = sum(1 for s in stations_data if s['type'] == 'BRT Station')
    operational_count = sum(1 for s in stations_data if s['is_operational'])

    # Pagination
    paginator = Paginator(stations_data, 6)  # Show 6 stations per page
    try:
        stations = paginator.page(page)
    except PageNotAnInteger:
        stations = paginator.page(1)
    except EmptyPage:
        stations = paginator.page(paginator.num_pages)

    context = {
        'stations': stations,
        'total_stations': total_stations,
        'bus_station_count': bus_station_count,
        'brt_station_count': brt_station_count,
        'operational_count': operational_count,
        'search_query': search_query,
        'filter_type': filter_type,
        'filter_status': filter_status,
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
