import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
from .preprocessor import DataPreprocessor

class ModelEvaluator:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.data = None
        self.load_data()
        
    def load_data(self):
        """Load and preprocess the data"""
        self.data = self.preprocessor.load_data()
        
    def evaluate_regression(self, model, feature_type='regression', test_size=0.2):
        """Evaluate regression model performance"""
        if self.data is None or len(self.data) == 0:
            return {
                'rmse': 0.0,
                'mae': 0.0,
                'r2_score': 0.0,
                'cv_scores': []
            }
            
        try:
            X, y = self.preprocessor.prepare_features(self.data, feature_type)
            if X is None or y is None:
                return {
                    'rmse': 0.0,
                    'mae': 0.0,
                    'r2_score': 0.0,
                    'cv_scores': []
                }
                
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Train and evaluate
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            r2_score = model.score(X_test, y_test)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X, y, cv=5)
            
            return {
                'rmse': float(rmse),
                'mae': float(mae),
                'r2_score': float(r2_score),
                'cv_scores': cv_scores.tolist()
            }
        except Exception as e:
            print(f"Error in regression evaluation: {str(e)}")
            return {
                'rmse': 0.0,
                'mae': 0.0,
                'r2_score': 0.0,
                'cv_scores': []
            }
            
    def evaluate_classification(self, model, feature_type='classification', test_size=0.2):
        """Evaluate classification model performance"""
        if self.data is None or len(self.data) == 0:
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'confusion_matrix': [],
                'classification_report': {}
            }
            
        try:
            X, y = self.preprocessor.prepare_features(self.data, feature_type)
            if X is None or y is None:
                return {
                    'accuracy': 0.0,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1': 0.0,
                    'confusion_matrix': [],
                    'classification_report': {}
                }
                
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Train and evaluate
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            f1 = f1_score(y_test, y_pred, average='weighted')
            conf_matrix = confusion_matrix(y_test, y_pred)
            class_report = classification_report(y_test, y_pred, output_dict=True)
            
            return {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                'confusion_matrix': conf_matrix.tolist(),
                'classification_report': class_report
            }
        except Exception as e:
            print(f"Error in classification evaluation: {str(e)}")
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'confusion_matrix': [],
                'classification_report': {}
            }
            
    def evaluate_clustering(self, model, feature_type='clustering', n_clusters=3):
        """Evaluate clustering model performance"""
        if self.data is None or len(self.data) == 0:
            return {
                'silhouette_score': 0.0,
                'inertia': 0.0,
                'cluster_sizes': [],
                'cluster_means': []
            }
            
        try:
            X, _ = self.preprocessor.prepare_features(self.data, feature_type)
            if X is None:
                return {
                    'silhouette_score': 0.0,
                    'inertia': 0.0,
                    'cluster_sizes': [],
                    'cluster_means': []
                }
                
            # Fit model
            clusters = model.fit_predict(X)
            
            # Calculate metrics
            cluster_sizes = [int((clusters == i).sum()) for i in range(n_clusters)]
            cluster_means = []
            
            for i in range(n_clusters):
                cluster_data = X[clusters == i]
                if len(cluster_data) > 0:
                    cluster_means.append(cluster_data.mean().tolist())
                else:
                    cluster_means.append([0.0] * X.shape[1])
            
            return {
                'silhouette_score': float(model.inertia_),
                'inertia': float(model.inertia_),
                'cluster_sizes': cluster_sizes,
                'cluster_means': cluster_means
            }
        except Exception as e:
            print(f"Error in clustering evaluation: {str(e)}")
            return {
                'silhouette_score': 0.0,
                'inertia': 0.0,
                'cluster_sizes': [],
                'cluster_means': []
            }
            
    def get_feature_importance(self, model, feature_type):
        """Get feature importance scores"""
        if self.data is None or len(self.data) == 0:
            return {}
            
        try:
            X, _ = self.preprocessor.prepare_features(self.data, feature_type)
            if X is None:
                return {}
                
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                return {
                    col: float(imp) 
                    for col, imp in zip(X.columns, importances)
                }
            elif hasattr(model, 'coef_'):
                importances = model.coef_
                return {
                    col: float(abs(imp)) 
                    for col, imp in zip(X.columns, importances)
                }
            return {}
        except Exception:
            return {}
