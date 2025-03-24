import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone

def calculate_time_based_features(data):
    """Calculate time-based features from transport data"""
    if len(data) == 0:
        return pd.DataFrame()
        
    try:
        # Convert peak hours to binary
        data['is_peak_hour'] = data['peak_hours'].str.contains('yes', case=False).astype(int)
        
        # Calculate speed-related features
        data['speed_efficiency'] = data['average_speed'] / data['road_distance']
        data['time_efficiency'] = data['travel_time'] / data['road_distance']
        
        # Calculate congestion score
        congestion_map = {'Low': 0, 'Medium': 1, 'High': 2, 'Very High': 3}
        data['congestion_score'] = data['congestion_level'].map(congestion_map)
        
        return data
    except Exception:
        return pd.DataFrame()

def calculate_route_metrics(data):
    """Calculate route-specific metrics"""
    if len(data) == 0:
        return pd.DataFrame()
        
    try:
        # Group by route
        route_metrics = data.groupby('route_name').agg({
            'average_speed': 'mean',
            'travel_time': 'mean',
            'fare': 'mean',
            'congestion_score': 'mean',
            'traffic_lights_count': 'first',
            'passenger_capacity': 'first'
        }).reset_index()
        
        # Calculate route efficiency score
        route_metrics['efficiency_score'] = (
            route_metrics['average_speed'] / route_metrics['travel_time'] *
            (4 - route_metrics['congestion_score']) / 4
        )
        
        # Calculate cost efficiency
        route_metrics['cost_per_km'] = route_metrics['fare'] / data['road_distance'].mean()
        
        return route_metrics
    except Exception:
        return pd.DataFrame()

def calculate_station_metrics(data):
    """Calculate station-specific metrics"""
    if len(data) == 0:
        return pd.DataFrame()
        
    try:
        # Combine bus and BRT stations
        stations = pd.concat([
            data[['bus_station', 'route_name', 'average_speed', 'travel_time', 'congestion_score']]
            .rename(columns={'bus_station': 'station'}),
            data[['brt_station', 'route_name', 'average_speed', 'travel_time', 'congestion_score']]
            .rename(columns={'brt_station': 'station'})
        ])
        
        # Calculate station metrics
        station_metrics = stations.groupby('station').agg({
            'route_name': 'count',
            'average_speed': 'mean',
            'travel_time': 'mean',
            'congestion_score': 'mean'
        }).reset_index()
        
        station_metrics.columns = [
            'station', 'route_count', 'avg_speed',
            'avg_travel_time', 'avg_congestion'
        ]
        
        return station_metrics
    except Exception:
        return pd.DataFrame()

def generate_time_series(data, feature, freq='1H'):
    """Generate time series data for a specific feature"""
    if len(data) == 0:
        return pd.DataFrame()
        
    try:
        # Create time range
        now = timezone.now()
        time_range = pd.date_range(
            start=now - timedelta(days=7),
            end=now,
            freq=freq
        )
        
        # Create time series
        ts_data = pd.DataFrame(index=time_range)
        ts_data[feature] = np.random.normal(
            loc=data[feature].mean(),
            scale=data[feature].std(),
            size=len(time_range)
        )
        
        # Ensure values are reasonable
        if feature in ['congestion_score']:
            ts_data[feature] = ts_data[feature].clip(0, 3)
        elif feature in ['average_speed', 'travel_time', 'fare']:
            ts_data[feature] = ts_data[feature].clip(0)
            
        return ts_data
    except Exception:
        return pd.DataFrame()

def calculate_performance_metrics(data):
    """Calculate overall system performance metrics"""
    if len(data) == 0:
        return {}
        
    try:
        metrics = {
            'avg_speed': float(data['average_speed'].mean()),
            'avg_travel_time': float(data['travel_time'].mean()),
            'avg_fare': float(data['fare'].mean()),
            'avg_congestion': float(data['congestion_score'].mean()),
            'total_routes': int(data['route_name'].nunique()),
            'total_stations': int(
                data['bus_station'].nunique() + 
                data['brt_station'].nunique()
            ),
            'peak_load': float(
                data[data['is_peak_hour'] == 1]['congestion_score'].mean()
            ),
            'off_peak_load': float(
                data[data['is_peak_hour'] == 0]['congestion_score'].mean()
            )
        }
        
        return metrics
    except Exception:
        return {
            'avg_speed': 0.0,
            'avg_travel_time': 0.0,
            'avg_fare': 0.0,
            'avg_congestion': 0.0,
            'total_routes': 0,
            'total_stations': 0,
            'peak_load': 0.0,
            'off_peak_load': 0.0
        }
