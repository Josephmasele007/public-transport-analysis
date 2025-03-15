import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
from datetime import datetime

class TravelCostPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = 'travel_cost/models/travel_cost_model.joblib'
        self.scaler_path = 'travel_cost/models/scaler.joblib'
        
    def prepare_data(self, transportation_data):
        """Prepare data for training"""
        # Convert data to DataFrame
        df = pd.DataFrame(transportation_data)
        
        # Select features for prediction
        features = [
            'road_distance', 'travel_time', 'traffic_lights_count',
            'average_speed', 'peak_hours'
        ]
        
        # Convert peak_hours to numeric (assuming format like "6-9,17-19")
        df['peak_hours'] = df['peak_hours'].apply(self._convert_peak_hours)
        
        # Add derived features
        df['speed_factor'] = df['average_speed'] / 40  # Normalize speed
        df['traffic_density'] = df['traffic_lights_count'] / df['road_distance']  # Traffic density
        df['time_per_km'] = df['travel_time'] / df['road_distance']  # Time efficiency
        
        # Add these to features list
        features.extend(['speed_factor', 'traffic_density', 'time_per_km'])
        
        X = df[features]
        y = df['fare']
        
        return X, y
    
    def _convert_peak_hours(self, peak_hours):
        """Convert peak hours string to numeric value"""
        try:
            # Split multiple time ranges
            ranges = peak_hours.split(',')
            total_hours = 0
            
            for range_str in ranges:
                if range_str == '0':
                    continue
                start, end = map(int, range_str.split('-'))
                total_hours += end - start
            
            return total_hours
        except:
            return 0
    
    def _is_peak_hour(self, time_str):
        """Check if given time is during peak hours"""
        try:
            current_time = datetime.strptime(time_str, '%H:%M').time()
            peak_ranges = [
                (6, 9),   # Morning peak
                (17, 19)  # Evening peak
            ]
            
            for start, end in peak_ranges:
                if start <= current_time.hour < end:
                    return True
            return False
        except:
            return False
    
    def train(self, transportation_data):
        """Train the model"""
        X, y = self.prepare_data(transportation_data)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model with more trees and deeper depth
        self.model = RandomForestRegressor(
            n_estimators=200,  # More trees for better accuracy
            max_depth=15,      # Deeper trees
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Model Performance:")
        print(f"Mean Squared Error: {mse:.2f}")
        print(f"R2 Score: {r2:.2f}")
        
        # Save model and scaler
        self._save_model()
        
        return mse, r2
    
    def predict(self, features):
        """Predict fare for given features"""
        if self.model is None:
            self._load_model()
        
        # Convert input features to DataFrame
        df = pd.DataFrame([features])
        
        # Add derived features
        df['speed_factor'] = df['average_speed'] / 40
        df['traffic_density'] = df['traffic_lights'] / df['distance']
        df['time_per_km'] = df['travel_time'] / df['distance']
        
        # Select features in the same order as training
        feature_names = [
            'distance', 'travel_time', 'traffic_lights',
            'average_speed', 'peak_hours',
            'speed_factor', 'traffic_density', 'time_per_km'
        ]
        
        X = df[feature_names]
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Make prediction
        prediction = self.model.predict(X_scaled)
        
        # Apply business rules
        base_fare = prediction[0]
        
        # Apply peak hour surcharge (20% during peak hours)
        if df['peak_hours'].iloc[0] > 0:
            base_fare *= 1.2
        
        # Apply distance-based discount for long distances
        if df['distance'].iloc[0] > 10:
            base_fare *= 0.9
        
        # Apply traffic density adjustment
        if df['traffic_density'].iloc[0] > 0.5:  # High traffic density
            base_fare *= 1.1
        
        # Apply time efficiency bonus
        if df['time_per_km'].iloc[0] < 2:  # Fast route
            base_fare *= 0.95
        
        return round(base_fare, 2)
    
    def _save_model(self):
        """Save model and scaler to disk"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
    
    def _load_model(self):
        """Load model and scaler from disk"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
        else:
            raise FileNotFoundError("Model files not found. Please train the model first.") 