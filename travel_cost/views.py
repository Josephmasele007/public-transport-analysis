from django.shortcuts import render
from dashboard.models import TransportationData
from .ml_model import TravelCostPredictor
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Count, Sum
from django.utils import timezone
from stations.models import Station, Route, RouteStation, StationTraffic
import json
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import FareCalculator, FareHistory
from admin_panel.models import TrafficRecord
from django.db import models

def travel_cost(request):
    # Your logic for the dashboard page goes here
    return render(request, 'travel_cost/travel_cost.html')

def index(request):
    try:
        # Get all stations
        stations = Station.objects.all()
        
        # Get all routes with their stations
        routes = Route.objects.all().prefetch_related('routestation_set__station')
        
        # Get active fare calculator
        calculator = FareCalculator.objects.filter(is_active=True).first()
        
        # Prepare transport data
        transport_data = {
            'routes': [],
            'calculator': None
        }
        
        if calculator:
            transport_data['calculator'] = {
                'base_fare': float(calculator.base_fare),
                'distance_rate': float(calculator.distance_rate),
                'peak_hour_surcharge': float(calculator.peak_hour_surcharge),
                'traffic_light_surcharge': float(calculator.traffic_light_surcharge),
                'distance_discount_threshold': float(calculator.distance_discount_threshold),
                'distance_discount_rate': float(calculator.distance_discount_rate)
            }
        
        # Process routes
        for route in routes:
            route_stations = route.routestation_set.all().order_by('order')
            if len(route_stations) >= 2:
                start_station = route_stations.first().station
                end_station = route_stations.last().station
                
                # Get traffic data for this route
                traffic_records = TrafficRecord.objects.filter(
                    route=route,
                    timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
                )
                
                # Calculate average traffic level
                avg_traffic = traffic_records.aggregate(avg_level=models.Avg('traffic_level'))['avg_level'] or 0
                
                transport_data['routes'].append({
                    'id': route.id,
                    'name': route.name,
                    'start_station': {
                        'id': start_station.id,
                        'name': start_station.name,
                        'latitude': start_station.latitude,
                        'longitude': start_station.longitude
                    },
                    'end_station': {
                        'id': end_station.id,
                        'name': end_station.name,
                        'latitude': end_station.latitude,
                        'longitude': end_station.longitude
                    },
                    'distance': float(route.distance),
                    'estimated_time': route.estimated_time,
                    'traffic_level': avg_traffic,
                    'coordinates': route.coordinates
                })
        
        context = {
            'stations': stations,
            'transport_data': json.dumps(transport_data)
        }
        return render(request, 'travel_cost/index.html', context)
        
    except Exception as e:
        return render(request, 'travel_cost/index.html', {
            'error_message': f"Error loading data: {str(e)}",
            'stations': [],
            'transport_data': json.dumps({'routes': [], 'calculator': None})
        })

@ensure_csrf_cookie
def refresh_stations(request):
    if request.method == 'GET':
        try:
            # Get updated station data with traffic information
            stations = Station.objects.all().prefetch_related('routes', 'routestation_set__route')
            today = timezone.now().date()
            
            stations_data = []
            for station in stations:
                # Get today's traffic
                today_traffic = StationTraffic.objects.filter(
                    station=station,
                    date=today
                ).aggregate(
                    total_passengers=Sum('passenger_count')
                )['total_passengers'] or 0

                # Get routes with detailed information
                routes = []
                for route in station.routes.all():
                    route_station = RouteStation.objects.filter(
                        route=route,
                        station=station
                    ).first()
                    
                    if route_station:
                        routes.append({
                            'name': route.name,
                            'fare': float(route.fare),
                            'distance': float(route.distance),
                            'estimated_time': route.estimated_time,
                            'arrival_time': route_station.arrival_time.strftime('%H:%M'),
                            'departure_time': route_station.departure_time.strftime('%H:%M'),
                            'stop_duration': route_station.stop_duration
                        })

                station_data = {
                    'id': station.id,
                    'name': station.name,
                    'station_type': station.station_type,
                    'get_station_type_display': station.get_station_type_display(),
                    'location': station.location,
                    'landmark_nearby': station.landmark_nearby,
                    'opening_time': station.opening_time.strftime('%H:%M'),
                    'closing_time': station.closing_time.strftime('%H:%M'),
                    'capacity': station.capacity,
                    'is_operational': station.is_operational,
                    'coordinates': {
                        'lat': float(station.latitude) if station.latitude else None,
                        'lng': float(station.longitude) if station.longitude else None
                    },
                    'today_traffic': today_traffic,
                    'routes_count': len(routes),
                    'routes': routes
                }
                stations_data.append(station_data)
            
            return JsonResponse({
                'success': True,
                'stations': stations_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def get_station_details(request, station_id):
    try:
        station = Station.objects.get(id=station_id)
        routes = Route.objects.filter(routestation__station=station).distinct()
        
        return JsonResponse({
            'id': station.id,
            'name': station.name,
            'latitude': station.latitude,
            'longitude': station.longitude,
            'routes': [{
                'id': route.id,
                'name': route.name,
                'distance': float(route.distance),
                'estimated_time': route.estimated_time
            } for route in routes]
        })
    except Station.DoesNotExist:
        return JsonResponse({'error': 'Station not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@ensure_csrf_cookie
def predict_fare(request):
    if request.method == 'POST':
        try:
            # Get data from request
            distance = float(request.POST.get('distance'))
            travel_time = float(request.POST.get('travel_time'))
            traffic_lights = int(request.POST.get('traffic_lights'))
            average_speed = float(request.POST.get('average_speed'))
            peak_hours = request.POST.get('peak_hours')

            # Initialize predictor
            predictor = TravelCostPredictor()
            
            # Make prediction
            predicted_fare, breakdown = predictor.predict(
                distance=distance,
                travel_time=travel_time,
                traffic_lights=traffic_lights,
                average_speed=average_speed,
                peak_hours=peak_hours
            )

            return JsonResponse({
                'success': True,
                'predicted_fare': predicted_fare,
                'base_fare': breakdown.get('base_fare'),
                'peak_surcharge': breakdown.get('peak_surcharge'),
                'distance_discount': breakdown.get('distance_discount'),
                'traffic_adjustment': breakdown.get('traffic_adjustment')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_route_details(request):
    if request.method == 'GET':
        try:
            from_station = request.GET.get('from')
            to_station = request.GET.get('to')
            
            if not from_station or not to_station:
                return JsonResponse({
                    'success': False,
                    'error': 'Both from and to stations are required'
                })
            
            route = TransportationData.objects.filter(
                bus_station=from_station,
                brt_station=to_station
            ).first()
            
            if not route:
                route = TransportationData.objects.filter(
                    bus_station=to_station,
                    brt_station=from_station
                ).first()
            
            if route:
                return JsonResponse({
                    'success': True,
                    'route': {
                        'distance': route.road_distance,
                        'travel_time': route.travel_time,
                        'traffic_lights': route.traffic_lights_count,
                        'road_type': route.road_type,
                        'landmarks': route.landmark_nearby,
                        'peak_hours': route.peak_hours
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No route found between the specified stations'
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error fetching route details: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@require_http_methods(["POST"])
def calculate_fare(request):
    try:
        data = json.loads(request.body)
        start_station_id = data.get('start_station')
        end_station_id = data.get('end_station')
        route_id = data.get('route_id')
        is_peak_hour = data.get('is_peak_hour', False)
        
        # Get the route
        route = Route.objects.get(id=route_id)
        
        # Get active calculator
        calculator = FareCalculator.objects.filter(is_active=True).first()
        if not calculator:
            return JsonResponse({
                'error': 'No active fare calculator found'
            }, status=400)
        
        # Get traffic data
        traffic_records = TrafficRecord.objects.filter(
            route=route,
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        )
        
        # Calculate average traffic level and count traffic lights
        avg_traffic = traffic_records.aggregate(avg_level=models.Avg('traffic_level'))['avg_level'] or 0
        traffic_lights = traffic_records.count()
        
        # Calculate fare
        fare_breakdown = calculator.calculate_fare(
            distance=route.distance,
            is_peak_hour=is_peak_hour,
            traffic_lights=traffic_lights
        )
        
        # Save to history
        FareHistory.objects.create(
            calculator=calculator,
            start_station=route.routestation_set.first().station.name,
            end_station=route.routestation_set.last().station.name,
            distance=route.distance,
            base_fare=calculator.base_fare,
            distance_fare=float(route.distance) * float(calculator.distance_rate),
            peak_hour_surcharge=fare_breakdown.get('peak_hour_surcharge', 0),
            traffic_light_surcharge=fare_breakdown.get('traffic_light_surcharge', 0),
            distance_discount=fare_breakdown.get('distance_discount', 0),
            total_fare=fare_breakdown['total_fare'],
            is_peak_hour=is_peak_hour,
            traffic_lights=traffic_lights
        )
        
        return JsonResponse({
            'fare': fare_breakdown['total_fare'],
            'breakdown': fare_breakdown,
            'traffic_level': avg_traffic,
            'traffic_lights': traffic_lights
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)