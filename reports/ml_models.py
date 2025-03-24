import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, accuracy_score
from django.utils import timezone
from datetime import timedelta
from dashboard.models import TransportData

class TransportAnalytics:
    def __init__(self):
        self.data = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.load_data()
        
    def load_data(self):
        """Load and preprocess data from TransportData model"""
        queryset = TransportData.objects.all().values()
        if not queryset.exists():
            self.data = pd.DataFrame()
            return
            
        self.data = pd.DataFrame(list(queryset))
        
        # Encode categorical variables
        categorical_columns = ['road_type', 'route_type', 'congestion_level', 'peak_hours']
        for col in categorical_columns:
            if col in self.data.columns:
                le = LabelEncoder()
                self.data[f'{col}_encoded'] = le.fit_transform(self.data[col])
                self.label_encoders[col] = le

    def predict_fare(self, route_name, congestion_level, route_type):
        """Predict fare using Linear Regression"""
        if self.data is None or len(self.data) == 0:
            return 0.0
            
        try:
            # Prepare features
            X = self.data[[
                'road_distance', 'average_speed', 'travel_time',
                'traffic_lights_count', 'congestion_level_encoded'
            ]]
            y = self.data['fare']
            
            # Train model
            model = LinearRegression()
            model.fit(X, y)
            
            # Prepare input for prediction
            route_data = self.data[self.data['route_name'] == route_name]
            if len(route_data) == 0:
                return 0.0
                
            input_data = route_data.iloc[0]
            input_features = np.array([[
                input_data['road_distance'],
                input_data['average_speed'],
                input_data['travel_time'],
                input_data['traffic_lights_count'],
                self.label_encoders['congestion_level'].transform([congestion_level])[0]
            ]])
            
            return float(model.predict(input_features)[0])
        except Exception:
            return 0.0

    def predict_congestion(self, route_name):
        """Predict congestion level using Random Forest"""
        if self.data is None or len(self.data) == 0:
            return "Low"
            
        try:
            # Prepare features
            X = self.data[[
                'average_speed', 'travel_time', 'traffic_lights_count',
                'passenger_capacity', 'peak_hours_encoded'
            ]]
            y = self.data['congestion_level_encoded']
            
            # Train model
            model = RandomForestClassifier(n_estimators=100)
            model.fit(X, y)
            
            # Prepare input for prediction
            route_data = self.data[self.data['route_name'] == route_name]
            if len(route_data) == 0:
                return "Low"
                
            input_data = route_data.iloc[0]
            input_features = np.array([[
                input_data['average_speed'],
                input_data['travel_time'],
                input_data['traffic_lights_count'],
                input_data['passenger_capacity'],
                input_data['peak_hours_encoded']
            ]])
            
            predicted_encoded = model.predict(input_features)[0]
            return self.label_encoders['congestion_level'].inverse_transform([predicted_encoded])[0]
        except Exception:
            return "Low"

    def cluster_stations(self, n_clusters=3):
        """Cluster stations based on performance metrics"""
        if self.data is None or len(self.data) == 0:
            return [{
                'cluster_id': i,
                'avg_speed': 0.0,
                'avg_fare': 0.0,
                'avg_congestion': 'Low',
                'station_count': 0
            } for i in range(n_clusters)]
            
        try:
            # Prepare features for clustering
            features = ['average_speed', 'travel_time', 'fare', 'traffic_lights_count']
            X = self.data[features]
            X_scaled = self.scaler.fit_transform(X)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Prepare results
            results = []
            for i in range(n_clusters):
                cluster_data = self.data[clusters == i]
                results.append({
                    'cluster_id': i,
                    'avg_speed': float(cluster_data['average_speed'].mean()),
                    'avg_fare': float(cluster_data['fare'].mean()),
                    'avg_congestion': str(cluster_data['congestion_level'].mode()[0]),
                    'station_count': int(len(cluster_data))
                })
            
            return results
        except Exception:
            return [{
                'cluster_id': i,
                'avg_speed': 0.0,
                'avg_fare': 0.0,
                'avg_congestion': 'Low',
                'station_count': 0
            } for i in range(n_clusters)]

    def predict_peak_performance(self, route_name):
        """Predict route performance during peak hours"""
        if self.data is None or len(self.data) == 0:
            return {
                'predicted_travel_time': 0.0,
                'efficiency_score': 0.0
            }
            
        try:
            peak_data = self.data[self.data['peak_hours'].str.contains('yes', case=False)]
            if len(peak_data) == 0:
                return {
                    'predicted_travel_time': 0.0,
                    'efficiency_score': 0.0
                }
            
            # Prepare features
            X = peak_data[[
                'average_speed', 'passenger_capacity',
                'traffic_lights_count', 'congestion_level_encoded'
            ]]
            y = peak_data['travel_time']
            
            # Train model
            model = RandomForestRegressor(n_estimators=100)
            model.fit(X, y)
            
            # Prepare input for prediction
            route_data = self.data[self.data['route_name'] == route_name]
            if len(route_data) == 0:
                return {
                    'predicted_travel_time': 0.0,
                    'efficiency_score': 0.0
                }
                
            input_data = route_data.iloc[0]
            input_features = np.array([[
                input_data['average_speed'],
                input_data['passenger_capacity'],
                input_data['traffic_lights_count'],
                input_data['congestion_level_encoded']
            ]])
            
            predicted_time = float(model.predict(input_features)[0])
            return {
                'predicted_travel_time': round(predicted_time, 2),
                'efficiency_score': round(100 * (1 - predicted_time / input_data['travel_time']), 2)
            }
        except Exception:
            return {
                'predicted_travel_time': 0.0,
                'efficiency_score': 0.0
            }

    def get_route_recommendations(self, origin_station, destination_station=None):
        """Get route recommendations based on current conditions"""
        if self.data is None or len(self.data) == 0:
            return []
            
        try:
            # Filter routes between stations
            routes = self.data[
                (self.data['bus_station'] == origin_station) | 
                (self.data['brt_station'] == origin_station)
            ]
            
            if len(routes) == 0:
                return []
            
            # Score each route based on multiple factors
            recommendations = []
            max_congestion = max(self.data['congestion_level_encoded'])
            max_speed = max(self.data['average_speed'])
            max_fare = max(self.data['fare'])
            
            for _, route in routes.iterrows():
                score = (
                    0.4 * (1 - route['congestion_level_encoded'] / max_congestion if max_congestion > 0 else 0) +
                    0.3 * (route['average_speed'] / max_speed if max_speed > 0 else 0) +
                    0.3 * (1 - route['fare'] / max_fare if max_fare > 0 else 0)
                )
                
                recommendations.append({
                    'route_name': str(route['route_name']),
                    'estimated_time': round(float(route['travel_time']), 2),
                    'fare': round(float(route['fare']), 2),
                    'congestion': str(route['congestion_level']),
                    'score': round(float(score * 100), 2)
                })
            
            return sorted(recommendations, key=lambda x: x['score'], reverse=True)
        except Exception:
            return []

    def analyze_congestion_patterns(self):
        """Analyze congestion patterns over time"""
        if self.data is None or len(self.data) == 0:
            return {
                'overall_patterns': {'Low': 0, 'Medium': 0, 'High': 0},
                'peak_patterns': {'Low': 0, 'Medium': 0, 'High': 0},
                'most_congested_routes': []
            }
            
        try:
            congestion_counts = self.data['congestion_level'].value_counts()
            peak_congestion = self.data[
                self.data['peak_hours'].str.contains('yes', case=False)
            ]['congestion_level'].value_counts()
            
            return {
                'overall_patterns': {
                    str(level): int(count) for level, count in congestion_counts.items()
                },
                'peak_patterns': {
                    str(level): int(count) for level, count in peak_congestion.items()
                },
                'most_congested_routes': self.data[
                    self.data['congestion_level'].isin(['High', 'Very High'])
                ]['route_name'].unique().tolist()[:5]
            }
        except Exception:
            return {
                'overall_patterns': {'Low': 0, 'Medium': 0, 'High': 0},
                'peak_patterns': {'Low': 0, 'Medium': 0, 'High': 0},
                'most_congested_routes': []
            }
