from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Sum
from dashboard.models import TransportData
import json

def explorer_view(request):
    # Get search parameters
    search_query = request.GET.get('search', '')
    transport_data = TransportData.objects.all()

    if search_query:
        transport_data = transport_data.filter(
            Q(road_name__icontains=search_query) |
            Q(route_name__icontains=search_query) |
            Q(bus_station__icontains=search_query) |
            Q(brt_station__icontains=search_query) |
            Q(landmark_nearby__icontains=search_query)
        )

    # Convert transport data to GeoJSON format for the map
    features = []
    for data in transport_data:
        try:
            # If geojson_data is provided, use it directly
            if data.geojson_data:
                features.append(json.loads(data.geojson_data))
            else:
                # Create a feature for bus station
                if data.bus_station_location:
                    features.append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': data.bus_station_location.split(',')[::-1]  # Reverse for [lat, lng]
                        },
                        'properties': {
                            'name': data.bus_station,
                            'type': 'Bus Station',
                            'route_name': data.route_name,
                            'peak_hours': data.peak_hours,
                            'fare': data.fare,
                            'landmark': data.landmark_nearby,
                            'congestion': data.congestion_level
                        }
                    })
                
                # Create a feature for BRT station
                if data.brt_station_location:
                    features.append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': data.brt_station_location.split(',')[::-1]  # Reverse for [lat, lng]
                        },
                        'properties': {
                            'name': data.brt_station,
                            'type': 'BRT Station',
                            'route_name': data.route_name,
                            'peak_hours': data.peak_hours,
                            'fare': data.fare,
                            'landmark': data.landmark_nearby,
                            'congestion': data.congestion_level
                        }
                    })
        except (ValueError, IndexError):
            continue

    # Create the GeoJSON object
    geojson_data = {
        'type': 'FeatureCollection',
        'features': features
    }

    context = {
        'transport_data': json.dumps(geojson_data),
        'search_query': search_query,
        'total_routes': transport_data.count(),
        'road_types': transport_data.values_list('road_type', flat=True).distinct(),
        'congestion_levels': transport_data.values_list('congestion_level', flat=True).distinct()
    }
    
    return render(request, 'explorer/index.html', context)

def index(request):
    return explorer_view(request)

def roads(request):
    # Get filters
    road_type = request.GET.get('road_type', '')
    congestion = request.GET.get('congestion', '')
    
    # Query roads with distinct road names to avoid duplicates
    roads_query = TransportData.objects.values(
        'road_name', 
        'road_type',
        'road_distance',
        'average_speed',
        'congestion_level',
        'traffic_lights_count',
        'landmark_nearby'
    ).distinct()

    # Apply filters
    if road_type:
        roads_query = roads_query.filter(road_type=road_type)
    if congestion:
        roads_query = roads_query.filter(congestion_level=congestion)
    
    # Order by road name
    roads_query = roads_query.order_by('road_name')
    
    # Pagination
    paginator = Paginator(list(roads_query), 9)  # Convert to list since we used values()
    page = request.GET.get('page', 1)
    roads = paginator.get_page(page)
    
    # Calculate statistics
    stats = TransportData.objects.aggregate(
        total_roads=Count('road_name', distinct=True),
        avg_speed=Avg('average_speed'),
        total_distance=Sum('road_distance'),
        total_traffic_lights=Sum('traffic_lights_count')
    )
    
    context = {
        'roads': roads,
        'total_roads': stats['total_roads'],
        'avg_speed': round(stats['avg_speed'] or 0, 1),
        'total_distance': round(stats['total_distance'] or 0, 1),
        'total_traffic_lights': stats['total_traffic_lights'] or 0,
        'road_types': TransportData.objects.values_list('road_type', flat=True).distinct().order_by('road_type'),
        'congestion_levels': TransportData.objects.values_list('congestion_level', flat=True).distinct().order_by('congestion_level'),
        'selected_type': road_type,
        'selected_congestion': congestion
    }
    return render(request, 'explorer/roads.html', context)

def routes(request):
    # Get filters
    route_type = request.GET.get('route_type', '')
    fare_range = request.GET.get('fare_range', '')
    
    # Query routes with all necessary fields
    routes_query = TransportData.objects.values(
        'route_name',
        'bus_station',
        'brt_station',
        'route_type',
        'road_distance',
        'travel_time',
        'fare',
        'peak_hours',
        'congestion_level',
        'passenger_capacity'
    ).distinct()
    
    # Apply filters
    if route_type:
        routes_query = routes_query.filter(route_type=route_type)
    if fare_range:
        if fare_range == '0-1000':
            routes_query = routes_query.filter(fare__lte=1000)
        elif fare_range == '1001-2000':
            routes_query = routes_query.filter(fare__gt=1000, fare__lte=2000)
        elif fare_range == '2001+':
            routes_query = routes_query.filter(fare__gt=2000)
    
    # Order by route name
    routes_query = routes_query.order_by('route_name')
    
    # Pagination
    paginator = Paginator(list(routes_query), 6)  # Convert to list since we used values()
    page = request.GET.get('page', 1)
    routes = paginator.get_page(page)
    
    # Calculate statistics
    stats = TransportData.objects.aggregate(
        total_routes=Count('route_name', distinct=True),
        avg_fare=Avg('fare'),
        total_bus_stations=Count('bus_station', distinct=True),
        total_brt_stations=Count('brt_station', distinct=True)
    )
    
    context = {
        'routes': routes,
        'total_routes': stats['total_routes'],
        'avg_fare': round(stats['avg_fare'] or 0, 2),
        'total_bus_stations': stats['total_bus_stations'],
        'total_brt_stations': stats['total_brt_stations'],
        'route_types': TransportData.objects.values_list('route_type', flat=True).distinct().order_by('route_type'),
        'selected_type': route_type,
        'selected_fare': fare_range
    }
    return render(request, 'explorer/routes.html', context)

