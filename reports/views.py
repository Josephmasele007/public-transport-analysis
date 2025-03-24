from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import models
from dashboard.models import TransportData
from .ml.models import TransportML
from .ml.utils import (
    calculate_time_based_features,
    calculate_route_metrics,
    calculate_station_metrics,
    calculate_performance_metrics
)
import json

def index(request):
    context = {
        'start_date': timezone.now().strftime('%Y-%m-%d'),
        'end_date': timezone.now().strftime('%Y-%m-%d'),
        **get_report_data()
    }
    return render(request, 'reports/index.html', context)

def get_report_data():
    # Initialize ML models
    ml = TransportML()
    
    # Get data
    transport_data = TransportData.objects.all()
    if not transport_data.exists():
        return get_empty_report()
    
    # Calculate metrics
    data_df = calculate_time_based_features(ml.data)
    route_metrics = calculate_route_metrics(data_df)
    station_metrics = calculate_station_metrics(data_df)
    performance_metrics = calculate_performance_metrics(data_df)
    
    # Get station data with ML insights
    station_data = []
    for station in station_metrics.itertuples():
        recommendations = ml.get_route_recommendations(station.station)
        station_data.append({
            'name': station.station,
            'type': 'bus' if station.station in data_df['bus_station'].unique() else 'brt',
            'current_load': round(station.avg_congestion * 33.33, 1),  # Convert 0-3 scale to percentage
            'wait_time': round(station.avg_travel_time / 2, 1),
            'status': get_status_class(station.avg_congestion * 33.33),
            'status_class': f"status-{get_status_class(station.avg_congestion * 33.33)}",
            'recommendations': recommendations[:3] if recommendations else []
        })
    
    # Get route data with ML insights
    route_data = []
    for route in route_metrics.itertuples():
        predicted_congestion = ml.predict_congestion(route.route_name)
        peak_performance = ml.predict_peak_performance(route.route_name)
        
        route_data.append({
            'route_name': route.route_name,
            'avg_speed': round(route.average_speed, 1),
            'avg_fare': round(route.fare, 2),
            'predicted_congestion': predicted_congestion,
            'peak_performance': peak_performance,
            'efficiency_score': round(route.efficiency_score * 100, 2)
        })
    
    # Get congestion patterns
    congestion_patterns = ml.analyze_congestion_patterns()
    
    # Get station clusters
    station_clusters = ml.cluster_stations()
    
    # Prepare chart data
    congestion_data = data_df['congestion_level'].value_counts()
    route_speeds = route_metrics[['route_name', 'average_speed']].sort_values('average_speed', ascending=False)[:10]
    
    # Cost trend analysis with ML predictions
    cost_labels = [(timezone.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(7)][::-1]
    cost_data = []
    
    for route in route_data[:5]:  # Get predictions for top 5 routes
        predicted_fare = ml.predict_fare(
            route['route_name'],
            route['predicted_congestion']
        )
        if predicted_fare > 0:
            cost_data.append(round(predicted_fare, 2))
    
    return {
        'total_stations': performance_metrics['total_stations'],
        'bus_stations': len(data_df['bus_station'].unique()),
        'brt_stations': len(data_df['brt_station'].unique()),
        
        'current_load': round(performance_metrics['avg_congestion'] * 33.33, 1),
        'peak_load': round(performance_metrics['peak_load'] * 33.33, 1),
        'off_peak': round(performance_metrics['off_peak_load'] * 33.33, 1),
        
        'route_performance': round(performance_metrics['avg_speed'] / performance_metrics['avg_travel_time'] * 100, 1),
        'current_fares': {
            'avg_fare': round(performance_metrics['avg_fare'], 2),
            'min_fare': round(data_df['fare'].min(), 2),
            'max_fare': round(data_df['fare'].max(), 2)
        },
        
        'station_data': station_data,
        'route_data': route_data,
        
        # ML insights
        'congestion_patterns': congestion_patterns,
        'station_clusters': station_clusters,
        
        # Chart data
        'congestion_labels': json.dumps(congestion_data.index.tolist()),
        'congestion_data': json.dumps(congestion_data.values.tolist()),
        'route_labels': json.dumps(route_speeds['route_name'].tolist()),
        'route_speeds': json.dumps(route_speeds['average_speed'].tolist()),
        'cost_labels': json.dumps(cost_labels),
        'cost_data': json.dumps(cost_data),
        'explorer_labels': json.dumps([r['route_name'] for r in route_data]),
        'explorer_data': json.dumps([r['efficiency_score'] for r in route_data]),
        
        # Last update timestamp
        'last_update': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def get_status_class(value):
    if value <= 50:
        return 'low'
    elif value <= 75:
        return 'medium'
    return 'high'

def get_empty_report():
    """Return empty report data when no records exist"""
    return {
        'total_stations': 0,
        'bus_stations': 0,
        'brt_stations': 0,
        'current_load': 0.0,
        'peak_load': 0.0,
        'off_peak': 0.0,
        'route_performance': 0.0,
        'current_fares': {
            'avg_fare': 0.0,
            'min_fare': 0.0,
            'max_fare': 0.0
        },
        'station_data': [],
        'route_data': [],
        'congestion_patterns': {
            'overall_patterns': {},
            'peak_patterns': {},
            'most_congested_routes': []
        },
        'station_clusters': [],
        'congestion_labels': '[]',
        'congestion_data': '[]',
        'route_labels': '[]',
        'route_speeds': '[]',
        'cost_labels': '[]',
        'cost_data': '[]',
        'explorer_labels': '[]',
        'explorer_data': '[]',
        'last_update': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@csrf_exempt
def update_report(request):
    """Update report data based on date range"""
    return JsonResponse(get_report_data())

@csrf_exempt
def filter_report(request):
    """Filter report data based on selected filters"""
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        # In a real application, you would filter data based on dates
        return JsonResponse(get_report_data())
    return JsonResponse({'error': 'Invalid request method'})