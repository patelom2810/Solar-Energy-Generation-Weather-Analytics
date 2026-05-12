"""
Machine Learning model utilities for Solar Analytics
"""
import joblib
import numpy as np
import pandas as pd
import logging
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages ML model loading and predictions"""
    
    def __init__(self, model_path='models/solar_generation_model.pkl', features_path='models/feature_names.pkl'):
        """
        Initialize model manager.
        
        Args:
            model_path (str): Path to trained model
            features_path (str): Path to feature names
        """
        self.model = None
        self.features = None
        self.is_loaded = False
        self.load_model(model_path, features_path)
    
    def load_model(self, model_path, features_path):
        """
        Load model from disk.
        
        Args:
            model_path (str): Path to model file
            features_path (str): Path to features file
            
        Returns:
            bool: True if successful
        """
        try:
            self.model = joblib.load(model_path)
            self.features = joblib.load(features_path)
            self.is_loaded = True
            logger.info("✓ Model and features loaded successfully")
            return True
        except FileNotFoundError as e:
            logger.error(f"✗ Model file not found: {e}")
            self.is_loaded = False
            return False
        except Exception as e:
            logger.error(f"✗ Error loading model: {e}", exc_info=True)
            self.is_loaded = False
            return False
    
    def predict(self, X):
        """
        Make prediction with loaded model.
        
        Args:
            X (pd.DataFrame): Feature matrix
            
        Returns:
            float: Predicted value or None if model not loaded
        """
        if not self.is_loaded or self.model is None:
            logger.error("Model not loaded - cannot make prediction")
            return None
        
        try:
            prediction = float(self.model.predict(X)[0])
            logger.debug(f"Prediction generated: {prediction:.3f} kWh")
            return prediction
        except Exception as e:
            logger.error(f"Error during prediction: {e}", exc_info=True)
            return None
    
    def get_feature_names(self):
        """Get feature names required by model"""
        return self.features if self.features is not None else []


def compute_model_scores(model, features, solar_daily, weather_daily):
    """
    Compute model performance metrics.
    
    Args:
        model: Trained model
        features (list): Feature names
        solar_daily (pd.DataFrame): Daily solar data
        weather_daily (pd.DataFrame): Daily weather data
        
    Returns:
        dict: Model performance metrics
    """
    try:
        merged = solar_daily.merge(weather_daily, on='date', how='inner')
        merged['date_dt'] = pd.to_datetime(merged['date'])
        merged['is_weekend_enc'] = merged['date_dt'].dt.dayofweek.isin([5, 6]).astype(int)
        merged['season_enc'] = merged['date_dt'].dt.month.apply(lambda m: 1 if m in [6, 7, 8, 9, 10, 11] else 0)
        merged['sunshine_ratio'] = merged['sunshine_duration'] / 86400
        merged['rad_clear'] = merged['shortwave_radiation_sum'] * (1 - merged['cloud_cover_mean'] / 100)
        
        X = merged[features]
        y = merged['generation_kwh']
        preds = model.predict(X)
        
        fi = dict(zip(features, [float(x) for x in model.feature_importances_]))
        
        metrics = {
            'model_type': type(model).__name__,
            'r2_score': round(float(r2_score(y, preds)), 4),
            'mae': round(float(mean_absolute_error(y, preds)), 4),
            'rmse': round(float(np.sqrt(mean_squared_error(y, preds))), 4),
            'mse': round(float(mean_squared_error(y, preds)), 4),
            'mape': round(float(mean_absolute_percentage_error(y, preds)) * 100, 2),
            'n_samples': int(len(y)),
            'feature_importances': dict(sorted(fi.items(), key=lambda x: -x[1])),
            'predictions_vs_actual': [
                {'actual': round(float(a), 3), 'predicted': round(float(p), 3)}
                for a, p in zip(y.tail(30).values, preds[-30:])
            ]
        }
        
        logger.info(f"Model metrics computed: R²={metrics['r2_score']}, MAE={metrics['mae']}")
        return metrics
        
    except Exception as e:
        logger.error(f"Error computing model scores: {e}", exc_info=True)
        return {'error': str(e)}
