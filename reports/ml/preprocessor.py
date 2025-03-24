import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from dashboard.models import TransportData

class DataPreprocessor:
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        
    def load_data(self):
        """Load and preprocess data from TransportData model"""
        queryset = TransportData.objects.all().values()
        if not queryset.exists():
            return pd.DataFrame()
            
        data = pd.DataFrame(list(queryset))
        
        # Encode categorical variables
        categorical_columns = ['road_type', 'route_type', 'congestion_level', 'peak_hours']
        for col in categorical_columns:
            if col in data.columns:
                le = LabelEncoder()
                data[f'{col}_encoded'] = le.fit_transform(data[col])
                self.label_encoders[col] = le
                
        # Scale numerical features
        numerical_columns = ['road_distance', 'average_speed', 'travel_time', 
                           'fare', 'traffic_lights_count', 'passenger_capacity']
        data_scaled = self.scaler.fit_transform(data[numerical_columns])
        
        for i, col in enumerate(numerical_columns):
            data[f'{col}_scaled'] = data_scaled[:, i]
            
        return data
        
    def prepare_features(self, data, feature_type='regression'):
        """Prepare features for different model types"""
        if len(data) == 0:
            return None, None
            
        if feature_type == 'regression':
            X = data[[
                'road_distance_scaled', 'average_speed_scaled', 
                'travel_time_scaled', 'traffic_lights_count_scaled',
                'congestion_level_encoded'
            ]]
            y = data['fare']
            
        elif feature_type == 'classification':
            X = data[[
                'average_speed_scaled', 'travel_time_scaled',
                'traffic_lights_count_scaled', 'passenger_capacity_scaled',
                'peak_hours_encoded'
            ]]
            y = data['congestion_level_encoded']
            
        elif feature_type == 'clustering':
            X = data[[
                'average_speed_scaled', 'travel_time_scaled',
                'fare_scaled', 'traffic_lights_count_scaled'
            ]]
            y = None
            
        return X, y
