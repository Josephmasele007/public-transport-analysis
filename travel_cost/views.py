from django.shortcuts import render
from dashboard.models import TransportData
from .ml_model import TravelCostPredictor
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Count, Sum
from django.utils import timezone
import json
from django.views.decorators.http import require_http_methods
from .models import FareCalculator, FareHistory

def travel_cost(request):
    # Your logic for the dashboard page goes here
    return render(request, 'travel_cost/travel_cost.html')

def index(request):
    try:
        # Get transport data
        transport_data_entries = TransportData.objects.all()
        
        # Get active fare calculator
        calculator = FareCalculator.objects.filter(is_active=True).first()
        
        # Prepare transport data
        transport_data = {
            'routes': [],
            'calculator': None,
            'stations': {
                'bus': [],
                'brt': []
            }
        }
        
        # Process stations and routes
        for entry in transport_data_entries:
            # Add route
            route_data = {
                'id': entry.id,
                'name': entry.route_name,
                'road_name': entry.road_name,
                'distance': entry.road_distance,
                'travel_time': entry.travel_time,
                'fare': entry.fare,
                'traffic_lights': entry.traffic_lights_count,
                'congestion_level': entry.congestion_level,
                'route_type': entry.route_type
            }
            
            if route_data not in transport_data['routes']:
                transport_data['routes'].append(route_data)
            
            # Add bus station if not already added
            if entry.bus_station and entry.bus_station not in [s['name'] for s in transport_data['stations']['bus']]:
                transport_data['stations']['bus'].append({
                    'id': f"bus_{len(transport_data['stations']['bus'])}",
                    'name': entry.bus_station,
                    'type': 'bus',
                    'location': entry.bus_station_location,
                    'landmark': entry.landmark_nearby
                })
            
            # Add BRT station if not already added
            if entry.brt_station and entry.brt_station not in [s['name'] for s in transport_data['stations']['brt']]:
                transport_data['stations']['brt'].append({
                    'id': f"brt_{len(transport_data['stations']['brt'])}",
                    'name': entry.brt_station,
                    'type': 'brt',
                    'location': entry.brt_station_location,
                    'landmark': entry.landmark_nearby
                })
        
        if calculator:
            transport_data['calculator'] = {
                'base_fare': float(calculator.base_fare),
                'distance_rate': float(calculator.distance_rate),
                'peak_hour_surcharge': float(calculator.peak_hour_surcharge),
                'traffic_light_surcharge': float(calculator.traffic_light_surcharge),
                'distance_discount_threshold': float(calculator.distance_discount_threshold),
                'distance_discount_rate': float(calculator.distance_discount_rate)
            }
        
        # Combine all stations for the template
        all_stations = transport_data['stations']['bus'] + transport_data['stations']['brt']
        
        context = {
            'stations': all_stations,
            'routes': transport_data['routes'],  
            'transport_data': json.dumps(transport_data)
        }
        return render(request, 'travel_cost/index.html', context)
        
    except Exception as e:
        return render(request, 'travel_cost/index.html', {
            'error_message': f"Error loading data: {str(e)}",
            'stations': [],
            'routes': [],
            'transport_data': json.dumps({'routes': [], 'calculator': None})
        })

@ensure_csrf_cookie
def refresh_stations(request):
    if request.method == 'GET':
        try:
            # Get updated station data with traffic information
            transport_data_entries = TransportData.objects.all()
            
            stations_data = []
            for entry in transport_data_entries:
                station_data = {
                    'id': f"bus_{len(stations_data)}",
                    'name': entry.bus_station,
                    'station_type': 'bus',
                    'get_station_type_display': 'Bus',
                    'location': entry.bus_station_location,
                    'landmark_nearby': entry.landmark_nearby,
                    'opening_time': '06:00',
                    'closing_time': '22:00',
                    'capacity': 1000,
                    'is_operational': True,
                    'coordinates': {
                        'lat': 10.0,
                        'lng': 10.0
                    },
                    'today_traffic': 100,
                    'routes_count': 10,
                    'routes': []
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
        transport_data_entries = TransportData.objects.filter(bus_station=station_id)
        routes = []
        for entry in transport_data_entries:
            routes.append({
                'id': entry.id,
                'name': entry.route_name,
                'distance': entry.road_distance,
                'estimated_time': entry.travel_time
            })
        
        return JsonResponse({
            'id': station_id,
            'name': station_id,
            'latitude': 10.0,
            'longitude': 10.0,
            'routes': routes
        })
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
            
            transport_data_entries = TransportData.objects.filter(bus_station=from_station, brt_station=to_station)
            route = transport_data_entries.first()
            
            if route:
                return JsonResponse({
                    'success': True,
                    'route': {
                        'distance': route.road_distance,
                        'travel_time': route.travel_time,
                        'traffic_lights': route.traffic_lights_count,
                        'road_type': route.route_type,
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
        transport_data_entry = TransportData.objects.get(id=route_id)
        
        # Get active calculator
        calculator = FareCalculator.objects.filter(is_active=True).first()
        if not calculator:
            return JsonResponse({
                'error': 'No active fare calculator found'
            }, status=400)
        
        # Calculate fare
        fare_breakdown = calculator.calculate_fare(
            distance=transport_data_entry.road_distance,
            is_peak_hour=is_peak_hour,
            traffic_lights=transport_data_entry.traffic_lights_count
        )
        
        # Save to history
        FareHistory.objects.create(
            calculator=calculator,
            start_station=start_station_id,
            end_station=end_station_id,
            distance=transport_data_entry.road_distance,
            base_fare=calculator.base_fare,
            distance_fare=float(transport_data_entry.road_distance) * float(calculator.distance_rate),
            peak_hour_surcharge=fare_breakdown.get('peak_hour_surcharge', 0),
            traffic_light_surcharge=fare_breakdown.get('traffic_light_surcharge', 0),
            distance_discount=fare_breakdown.get('distance_discount', 0),
            total_fare=fare_breakdown['total_fare'],
            is_peak_hour=is_peak_hour,
            traffic_lights=transport_data_entry.traffic_lights_count
        )
        
        return JsonResponse({
            'fare': fare_breakdown['total_fare'],
            'breakdown': fare_breakdown,
            'traffic_level': 10.0,
            'traffic_lights': transport_data_entry.traffic_lights_count
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)