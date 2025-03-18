from django.shortcuts import render
from django.db.models import Count, Avg, Q
from dashboard.models import TransportData
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def congestion(request):
    return render(request, 'congestion/congestion.html')


def analysis(request):
    return render(request, 'congestion/analysis.html')

def congestion_map(request):
    return render(request, 'congestion/congestion_map.html')

def index(request):
    # Get filters
    road_type = request.GET.get('road_type', '')
    congestion_level = request.GET.get('congestion', '')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)

    # Base queryset
    congestion_data = TransportData.objects.values(
        'road_name',
        'road_type',
        'congestion_level',
        'average_speed',
        'peak_hours',
        'traffic_lights_count',
        'alternative_routes'
    ).distinct()

    # Apply filters
    if road_type:
        congestion_data = congestion_data.filter(road_type=road_type)
    if congestion_level:
        congestion_data = congestion_data.filter(congestion_level=congestion_level)
    if search_query:
        congestion_data = congestion_data.filter(
            Q(road_name__icontains=search_query) |
            Q(alternative_routes__icontains=search_query)
        )

    # Calculate statistics
    stats = TransportData.objects.aggregate(
        avg_speed=Avg('average_speed'),
        total_traffic_lights=Count('traffic_lights_count'),
    )

    # Get congestion level distribution
    congestion_distribution = TransportData.objects.values(
        'congestion_level'
    ).annotate(
        count=Count('id')
    ).order_by('congestion_level')

    # Get road types with their average congestion
    road_type_stats = TransportData.objects.values(
        'road_type'
    ).annotate(
        avg_speed=Avg('average_speed'),
        count=Count('id')
    ).order_by('road_type')

    # Pagination
    paginator = Paginator(list(congestion_data), 8)  # Show 8 roads per page
    try:
        roads = paginator.page(page)
    except PageNotAnInteger:
        roads = paginator.page(1)
    except EmptyPage:
        roads = paginator.page(paginator.num_pages)

    context = {
        'roads': roads,
        'stats': stats,
        'congestion_distribution': congestion_distribution,
        'road_type_stats': road_type_stats,
        'road_types': TransportData.objects.values_list('road_type', flat=True).distinct(),
        'congestion_levels': TransportData.objects.values_list('congestion_level', flat=True).distinct(),
        'selected_road_type': road_type,
        'selected_congestion': congestion_level,
        'search_query': search_query,
    }

    return render(request, 'congestion/index.html', context)


@csrf_exempt
def get_ml_prediction(request):
    if request.method == 'POST':
        # Get input features from request
        features = {
            'road_distance': float(request.POST.get('road_distance', 0)),
            'average_speed': float(request.POST.get('average_speed', 0)),
            'travel_time': float(request.POST.get('travel_time', 0)),
            'traffic_lights_count': int(request.POST.get('traffic_lights_count', 0)),
            'passenger_capacity': int(request.POST.get('passenger_capacity', 0))
        }

        # Get training data from model
        transport_data = TransportData.objects.all()
        X_train = [[
            data.road_distance,
            data.average_speed,
            data.travel_time,
            data.traffic_lights_count,
            data.passenger_capacity
        ] for data in transport_data]
        y_train = [data.congestion_level for data in transport_data]

        # Prepare input data
        X_input = [[
            features['road_distance'],
            features['average_speed'],
            features['travel_time'],
            features['traffic_lights_count'],
            features['passenger_capacity']
        ]]

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_input_scaled = scaler.transform(X_input)

        # Train MLP
        mlp = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            activation='relu',
            solver='adam',
            max_iter=1000,
            random_state=42
        )
        mlp.fit(X_train_scaled, y_train)

        # Get prediction and probabilities
        prediction = mlp.predict(X_input_scaled)[0]
        raw_probabilities = mlp.predict_proba(X_input_scaled)[0]
        
        # Apply softmax to ensure proper probability distribution
        def softmax(x):
            exp_x = np.exp(x - np.max(x))  # Subtract max for numerical stability
            return exp_x / exp_x.sum()
        
        # Normalize probabilities and ensure they sum to 1
        normalized_probabilities = softmax(raw_probabilities)
        
        # Calculate confidence as the highest probability
        confidence = round(float(max(normalized_probabilities) * 100), 1)
        
        # Create confidence scores dictionary with proper normalization
        confidence_scores = {}
        total_prob = sum(normalized_probabilities)
        
        for label, prob in zip(mlp.classes_, normalized_probabilities):
            # Normalize to ensure all probabilities sum to 100%
            score = round(float(prob / total_prob * 100), 1)
            confidence_scores[label] = score

        return JsonResponse({
            'prediction': prediction,
            'confidence': confidence,
            'confidence_scores': confidence_scores
        })

    return JsonResponse({'error': 'Invalid request method'}, status=400)