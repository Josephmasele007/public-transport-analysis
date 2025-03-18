from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import models
from dashboard.models import TransportData
import json

def index(request):
    context = {
        'start_date': timezone.now().strftime('%Y-%m-%d'),
        'end_date': timezone.now().strftime('%Y-%m-%d'),
        **get_report_data()
    }
    return render(request, 'reports/index.html', context)

def get_report_data():
    # Stations data
    stations = TransportData.objects.values('bus_station', 'brt_station').distinct()
    bus_stations = TransportData.objects.values('bus_station').distinct().count()
    brt_stations = TransportData.objects.values('brt_station').distinct().count()
    total_stations = bus_stations + brt_stations
    
    # System load calculation based on congestion level
    def get_load_value(level):
        load_mapping = {
            'Low': 30,
            'Medium': 60,
            'High': 90,
            'Very High': 100
        }
        return load_mapping.get(level, 50)
    
    transport_data = TransportData.objects.all()
    current_load = transport_data.annotate(
        load=models.Case(
            *[models.When(congestion_level=k, then=models.Value(v)) for k, v in {
                'Low': 30, 'Medium': 60, 'High': 90, 'Very High': 100
            }.items()],
            default=models.Value(50),
            output_field=models.IntegerField(),
        )
    ).aggregate(avg_load=models.Avg('load'))['avg_load'] or 0
    
    # Peak hours analysis
    peak_hours_data = transport_data.filter(peak_hours__icontains='yes')
    peak_load = peak_hours_data.annotate(
        load=models.Case(
            *[models.When(congestion_level=k, then=models.Value(v)) for k, v in {
                'Low': 30, 'Medium': 60, 'High': 90, 'Very High': 100
            }.items()],
            default=models.Value(50),
            output_field=models.IntegerField(),
        )
    ).aggregate(peak_load=models.Avg('load'))['peak_load'] or 0
    
    off_peak_data = transport_data.filter(peak_hours__icontains='no')
    off_peak = off_peak_data.annotate(
        load=models.Case(
            *[models.When(congestion_level=k, then=models.Value(v)) for k, v in {
                'Low': 30, 'Medium': 60, 'High': 90, 'Very High': 100
            }.items()],
            default=models.Value(50),
            output_field=models.IntegerField(),
        )
    ).aggregate(off_peak=models.Avg('load'))['off_peak'] or 0

    # Route performance based on average speed
    avg_speed = transport_data.aggregate(avg=models.Avg('average_speed'))['avg'] or 0
    max_speed = transport_data.aggregate(max=models.Max('average_speed'))['max'] or 1
    route_performance = (avg_speed / max_speed * 100) if max_speed > 0 else 0
    
    # Cost analysis
    current_fares = transport_data.aggregate(
        avg_fare=models.Avg('fare'),
        min_fare=models.Min('fare'),
        max_fare=models.Max('fare')
    )
    
    # Prepare data for charts
    congestion_data = transport_data.values('congestion_level').annotate(
        count=models.Count('id')
    ).order_by('congestion_level')
    
    route_data = transport_data.values('route_name').annotate(
        avg_speed=models.Avg('average_speed'),
        avg_fare=models.Avg('fare'),
        congestion_count=models.Count('congestion_level')
    ).order_by('-avg_fare')[:10]
    
    # Station data
    station_data = []
    for station in stations:
        bus_data = transport_data.filter(bus_station=station['bus_station']).first()
        if bus_data:
            station_data.append({
                'name': bus_data.bus_station,
                'type': 'bus',
                'current_load': get_load_value(bus_data.congestion_level),
                'wait_time': round(bus_data.travel_time / 2, 1),
                'status': get_status_class(get_load_value(bus_data.congestion_level))
            })
        
        brt_data = transport_data.filter(brt_station=station['brt_station']).first()
        if brt_data:
            station_data.append({
                'name': brt_data.brt_station,
                'type': 'brt',
                'current_load': get_load_value(brt_data.congestion_level),
                'wait_time': round(brt_data.travel_time / 2, 1),
                'status': get_status_class(get_load_value(brt_data.congestion_level))
            })

    # Prepare chart data
    congestion_labels = [d['congestion_level'] for d in congestion_data]
    congestion_values = [d['count'] for d in congestion_data]
    
    route_labels = [d['route_name'] for d in route_data]
    route_costs = [float(d['avg_fare']) for d in route_data]
    
    # Calculate efficiency based on speed and travel time
    efficiency_data = transport_data.values('route_name').annotate(
        efficiency=models.ExpressionWrapper(
            models.F('average_speed') / models.F('travel_time'),
            output_field=models.FloatField()
        )
    ).order_by('route_name')
    
    explorer_labels = [d['route_name'] for d in efficiency_data]
    explorer_efficiency = [float(d['efficiency']) for d in efficiency_data]
    
    # Calculate passenger flow based on capacity and congestion
    passenger_flows = []
    for route in transport_data.order_by('route_name'):
        load_percentage = get_load_value(route.congestion_level) / 100
        passenger_flow = route.passenger_capacity * load_percentage
        passenger_flows.append(passenger_flow)

    return {
        'stations_count': total_stations,
        'brt_stations': brt_stations,
        'bus_stations': bus_stations,
        'stations_utilization': 100,  # All stations are considered active
        
        'system_load': round(current_load, 1),
        'peak_load': round(peak_load, 1),
        'off_peak_load': round(off_peak, 1),
        'load_status': get_status_class(current_load),
        
        'avg_fare': round(current_fares['avg_fare'], 2),
        'min_fare': round(current_fares['min_fare'], 2),
        'max_fare': round(current_fares['max_fare'], 2),
        'fare_trend': 0,  # No historical data for trend
        'fare_trend_status': 'normal',
        
        'route_performance': round(route_performance, 1),
        'on_time_rate': round(route_performance, 1),  # Using route performance as proxy
        'delay_rate': round(100 - route_performance, 1),
        'performance_status': get_status_class(route_performance),
        
        'congestion_labels': json.dumps(congestion_labels),
        'congestion_data': json.dumps(congestion_values),
        'cost_labels': json.dumps(route_labels),
        'cost_data': json.dumps(route_costs),
        'explorer_labels': json.dumps(explorer_labels),
        'explorer_efficiency': json.dumps(explorer_efficiency),
        'explorer_flow': json.dumps(passenger_flows),
        
        'stations': station_data,
        'routes': get_route_data(transport_data),
    }

def get_status_class(value):
    if value <= 50:
        return 'normal'
    elif value <= 75:
        return 'warning'
    return 'critical'

def get_route_data(transport_data):
    routes = transport_data.values('route_name').annotate(
        avg_speed=models.Avg('average_speed'),
        avg_congestion=models.Count('congestion_level'),
        avg_cost=models.Avg('fare')
    )
    
    return [{
        'name': route['route_name'],
        'type': 'BRT' if 'BRT' in route['route_name'] else 'Bus',
        'avg_speed': round(route['avg_speed'], 1),
        'congestion_level': round((route['avg_congestion'] / transport_data.count()) * 100, 1),
        'congestion_status': get_status_class(route['avg_congestion']),
        'cost_per_km': round(route['avg_cost'], 2)
    } for route in routes]

@csrf_exempt
def update_report(request):
    return JsonResponse(get_report_data())

@csrf_exempt
def filter_report(request):
    data = json.loads(request.body)
    filtered_data = TransportData.objects.all()
    
    if data['stationType'] != 'all':
        if data['stationType'] == 'bus':
            filtered_data = filtered_data.exclude(bus_station='')
        else:  # brt
            filtered_data = filtered_data.exclude(brt_station='')
    
    if data['routeType'] != 'all':
        filtered_data = filtered_data.filter(route_type__icontains=data['routeType'])
    
    if data['congestionLevel'] != 'all':
        level_mapping = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High'
        }
        filtered_data = filtered_data.filter(congestion_level=level_mapping[data['congestionLevel']])
    
    return JsonResponse(get_report_data())