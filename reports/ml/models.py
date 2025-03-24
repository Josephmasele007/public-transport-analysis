import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, accuracy_score
from .preprocessor import DataPreprocessor

class TransportML:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.data = None
        self.load_data()
        
    def load_data(self):
        """Load and preprocess the data"""
        self.data = self.preprocessor.load_data()
        
    def predict_fare(self, route_name, congestion_level):
        """Predict fare using Linear Regression"""
        if self.data is None or len(self.data) == 0:
            return 0.0
            
        try:
            X, y = self.preprocessor.prepare_features(self.data, 'regression')
            if X is None or y is None:
                return 0.0
                
            # Train model
            model = LinearRegression()
            model.fit(X, y)
            
            # Prepare input for prediction
            route_data = self.data[self.data['route_name'] == route_name]
            if len(route_data) == 0:
                return 0.0
                
            input_data = route_data.iloc[0]
            input_features = np.array([[
                input_data['road_distance_scaled'],
                input_data['average_speed_scaled'],
                input_data['travel_time_scaled'],
                input_data['traffic_lights_count_scaled'],
                self.preprocessor.label_encoders['congestion_level'].transform([congestion_level])[0]
            ]])
            
            return float(model.predict(input_features)[0])
        except Exception:
            return 0.0
            
    def predict_congestion(self, route_name):
        """Predict congestion level using Random Forest"""
        if self.data is None or len(self.data) == 0:
            return "Low"
            
        try:
            X, y = self.preprocessor.prepare_features(self.data, 'classification')
            if X is None or y is None:
                return "Low"
                
            # Train model
            model = RandomForestClassifier(n_estimators=100)
            model.fit(X, y)
            
            # Prepare input for prediction
            route_data = self.data[self.data['route_name'] == route_name]
            if len(route_data) == 0:
                return "Low"
                
            input_data = route_data.iloc[0]
            input_features = np.array([[
                input_data['average_speed_scaled'],
                input_data['travel_time_scaled'],
                input_data['traffic_lights_count_scaled'],
                input_data['passenger_capacity_scaled'],
                input_data['peak_hours_encoded']
            ]])
            
            predicted_encoded = model.predict(input_features)[0]
            return self.preprocessor.label_encoders['congestion_level'].inverse_transform([predicted_encoded])[0]
        except Exception:
            return "Low"
            
    def cluster_stations(self, n_clusters=3):
        """Cluster stations based on performance metrics"""
        if self.data is None or len(self.data) == 0:
            return self._empty_clusters(n_clusters)
            
        try:
            X, _ = self.preprocessor.prepare_features(self.data, 'clustering')
            if X is None:
                return self._empty_clusters(n_clusters)
                
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X)
            
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
            return self._empty_clusters(n_clusters)
            
    def predict_peak_performance(self, route_name):
        """Predict route performance during peak hours"""
        if self.data is None or len(self.data) == 0:
            return self._empty_performance()
            
        try:
            peak_data = self.data[self.data['peak_hours'].str.contains('yes', case=False)]
            if len(peak_data) == 0:
                return self._empty_performance()
            
            X, y = self.preprocessor.prepare_features(peak_data, 'regression')
            if X is None or y is None:
                return self._empty_performance()
            
            # Train model
            model = RandomForestRegressor(n_estimators=100)
            model.fit(X, y)
            
            # Prepare input for prediction
            route_data = self.data[self.data['route_name'] == route_name]
            if len(route_data) == 0:
                return self._empty_performance()
                
            input_data = route_data.iloc[0]
            input_features = np.array([[
                input_data['average_speed_scaled'],
                input_data['travel_time_scaled'],
                input_data['traffic_lights_count_scaled'],
                input_data['passenger_capacity_scaled'],
                input_data['peak_hours_encoded']
            ]])
            
            predicted_time = float(model.predict(input_features)[0])
            return {
                'predicted_travel_time': round(predicted_time, 2),
                'efficiency_score': round(100 * (1 - predicted_time / input_data['travel_time']), 2)
            }
        except Exception:
            return self._empty_performance()
            
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
            max_congestion = max(self.data['congestion_level_encoded'])
            max_speed = max(self.data['average_speed'])
            max_fare = max(self.data['fare'])
            
            recommendations = []
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
            return self._empty_patterns()
            
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
            return self._empty_patterns()
            
    def _empty_clusters(self, n_clusters):
        """Return empty cluster data"""
        return [{
            'cluster_id': i,
            'avg_speed': 0.0,
            'avg_fare': 0.0,
            'avg_congestion': 'Low',
            'station_count': 0
        } for i in range(n_clusters)]
        
    def _empty_performance(self):
        """Return empty performance data"""
        return {
            'predicted_travel_time': 0.0,
            'efficiency_score': 0.0
        }
        
    def _empty_patterns(self):
        """Return empty congestion patterns"""
        return {
            'overall_patterns': {'Low': 0, 'Medium': 0, 'High': 0},
            'peak_patterns': {'Low': 0, 'Medium': 0, 'High': 0},
            'most_congested_routes': []
        }
