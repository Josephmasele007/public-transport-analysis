from django.shortcuts import render
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .models import TransportData  # Updated import
import json

def dashboard(request):
    try:
        # Get search parameters
        search_query = request.GET.get('search', '')
        selected_road_type = request.GET.get('road_type', '')
        page = request.GET.get('page', 1)

        # Base queryset
        routes = TransportData.objects.all()

        # Apply filters
        if search_query:
            routes = routes.filter(
                road_name__icontains=search_query) | routes.filter(
                route_name__icontains=search_query) | routes.filter(
                bus_station__icontains=search_query) | routes.filter(
                brt_station__icontains=search_query
            )
        if selected_road_type:
            routes = routes.filter(road_type=selected_road_type)

        # Calculate statistics
        total_routes = routes.count()
        total_stations = routes.values('bus_station').distinct().count()
        avg_fare = routes.aggregate(Avg('fare'))['fare__avg'] or 0
        avg_travel_time = routes.aggregate(Avg('travel_time'))['travel_time__avg'] or 0

        # Get unique road types for filter dropdown
        road_types = TransportData.objects.values_list('road_type', flat=True).distinct()

        # Prepare data for road type distribution chart
        road_type_stats = TransportData.objects.values('road_type').annotate(
            count=Count('id')
        ).order_by('road_type')

        road_type_data = [item['count'] for item in road_type_stats]
        road_type_labels = [item['road_type'] for item in road_type_stats]

        # Prepare data for fare vs distance chart - Enhanced version
        fare_distance_stats = (
            TransportData.objects
            .values('road_distance')
            .annotate(avg_fare=Avg('fare'))
            .order_by('road_distance')
        )

        # Prepare series data for the line chart
        fare_distance_series = [{
            'name': 'Average Fare',
            'data': [round(float(item['avg_fare']), 2) for item in fare_distance_stats]
        }]
        distance_categories = [float(item['road_distance']) for item in fare_distance_stats]

        # Pagination
        paginator = Paginator(routes, 10)  # Show 10 routes per page
        routes_page = paginator.get_page(page)

        context = {
            'routes': routes_page,
            'total_routes': total_routes,
            'total_stations': total_stations,
            'avg_fare': avg_fare,
            'avg_travel_time': avg_travel_time,
            'road_types': road_types,
            'selected_road_type': selected_road_type,
            'search_query': search_query,
            'road_type_data': json.dumps(road_type_data),
            'road_type_labels': json.dumps(road_type_labels),
            'fare_distance_series': json.dumps(fare_distance_series),
            'distance_categories': json.dumps(distance_categories),
        }
    except Exception as e:
        context = {
            'routes': [],
            'total_routes': 0,
            'total_stations': 0,
            'avg_fare': 0,
            'avg_travel_time': 0,
            'road_types': [],
            'error_message': str(e)
        }

    return render(request, 'dashboard/dashboard.html', context)

def insights(request):
    return render(request, 'dashboard/insights.html')

def congestion_analysis(request):
    return render(request, 'dashboard/congestion_analysis.html')

