"""
Machine Learning model utilities for Solar Analytics
"""
import logging
import joblib
import numpy as np
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
            float: Predicted value (bounded >= 0) or None if model not loaded
        """
        if not self.is_loaded or self.model is None:
            logger.error("Model not loaded - cannot make prediction")
            return None
        
        try:
            raw_pred = float(self.model.predict(X)[0])
            prediction = max(0.0, raw_pred)
            logger.debug(f"Prediction generated: {prediction:.3f} kWh (raw: {raw_pred:.3f})")
            return prediction
        except Exception as e:
            logger.error(f"Error during prediction: {e}", exc_info=True)
            return None
    
    def get_feature_names(self):
        """Get feature names required by model"""
        return self.features if self.features is not None else []


def extract_model_feature_importances(model, feature_names):
    """
    Extract or approximate normalized feature importances across different model types
    (Tree models, Linear models, Pipelines, Ensembles).
    
    Args:
        model: Trained estimator or pipeline
        feature_names (list): List of feature names
        
    Returns:
        dict: Mapping of feature names to normalized importance scores (sum to 1.0)
    """
    try:
        if hasattr(model, 'feature_importances_'):
            imps = np.array(model.feature_importances_, dtype=float)
        elif hasattr(model, 'coef_'):
            imps = np.abs(np.array(model.coef_, dtype=float)).flatten()
        elif hasattr(model, 'named_steps'):
            # Pipeline: extract from final estimator
            estimator = model.named_steps.get('reg') or model.named_steps.get('model') or list(model.named_steps.values())[-1]
            if hasattr(estimator, 'coef_'):
                imps = np.abs(np.array(estimator.coef_, dtype=float)).flatten()
            elif hasattr(estimator, 'feature_importances_'):
                imps = np.array(estimator.feature_importances_, dtype=float)
            else:
                imps = np.ones(len(feature_names))
        elif hasattr(model, 'estimators_'):
            # VotingRegressor / Ensemble
            sub_imps = []
            weights = getattr(model, 'weights', None)
            if weights is None or len(weights) != len(model.estimators_):
                weights = [1.0] * len(model.estimators_)
            for est, w in zip(model.estimators_, weights):
                sub_dict = extract_model_feature_importances(est, feature_names)
                sub_arr = np.array([sub_dict.get(f, 0.0) for f in feature_names])
                sub_imps.append(sub_arr * float(w))
            imps = np.sum(sub_imps, axis=0) if sub_imps else np.ones(len(feature_names))
        else:
            imps = np.ones(len(feature_names))
            
        total = np.sum(imps)
        if total > 0:
            imps = imps / total
        else:
            imps = np.ones(len(feature_names)) / len(feature_names)
            
        fi = {f: round(float(v), 4) for f, v in zip(feature_names, imps)}
        return dict(sorted(fi.items(), key=lambda x: -x[1]))
    except Exception as e:
        logger.warning(f"Could not compute feature importances: {e}")
        uniform = round(1.0 / max(len(feature_names), 1), 4)
        return {f: uniform for f in feature_names}


def get_model_display_name(model):
    """Return descriptive human-readable model type name."""
    if hasattr(model, 'named_steps'):
        steps = [type(s).__name__ for s in model.named_steps.values()]
        return f"Pipeline ({' → '.join(steps)})"
    return type(model).__name__


def compute_model_scores(model, features, solar_daily, weather_daily):
    """
    Compute model performance metrics.
    
    Returns both:
    1. rolling_validation: Out-of-sample expanding-window 5-fold rolling validation (50 unseen days)
    2. training_fit: In-sample metrics on the 89 training days (kept separate as secondary reference)
    
    Args:
        model: Trained model
        features (list): Feature names
        solar_daily (pd.DataFrame): Daily solar data
        weather_daily (pd.DataFrame): Daily weather data
        
    Returns:
        dict: Model performance metrics
    """
    try:
        from .features import compute_engineered_features
        from .utils import filter_anomalies
        from .rolling_validation import compute_rolling_validation_metrics
        
        merged = solar_daily.merge(weather_daily, on='date', how='inner')
        merged = merged.drop_duplicates(subset=['date']).reset_index(drop=True)
        merged = filter_anomalies(merged)
        merged = compute_engineered_features(merged)
        
        X = merged[features]
        y = merged['generation_kwh']
        preds = np.clip(model.predict(X), 0.0, None)
        
        fi = extract_model_feature_importances(model, features)
        
        # In-sample metrics (training fit)
        training_fit = {
            'r2_score': round(float(r2_score(y, preds)), 4),
            'mae': round(float(mean_absolute_error(y, preds)), 4),
            'rmse': round(float(np.sqrt(mean_squared_error(y, preds))), 4),
            'mse': round(float(mean_squared_error(y, preds)), 4),
            'mape': round(float(mean_absolute_percentage_error(y, preds)) * 100, 2),
            'n_samples': int(len(y)),
            'note': 'In-sample training fit on 89 clean samples (optimistic; overstates real forecast accuracy)'
        }
        
        # Rolling-origin cross-validation metrics (out-of-sample on unseen days)
        rolling_val = compute_rolling_validation_metrics(solar_daily, weather_daily)
        
        metrics = {
            'model_type': get_model_display_name(model),
            # Primary headline metrics reported from rolling validation on unseen days
            'r2_score': rolling_val['r2'],
            'r2_raw': rolling_val['r2_raw'],
            'mae': rolling_val['mae'],
            'mae_display': rolling_val['mae_display'],
            'mae_raw': rolling_val['mae_raw'],
            'rmse': rolling_val['rmse'],
            'rmse_display': rolling_val['rmse_display'],
            'rmse_raw': rolling_val['rmse_raw'],
            'baseline_mae': rolling_val['baseline_mae'],
            'pct_error_reduction': rolling_val['pct_error_reduction'],
            'pct_error_reduction_display': rolling_val['pct_error_reduction_display'],
            'n_folds': rolling_val['n_folds'],
            'n_test_days': rolling_val['n_test_days'],
            'n_samples': training_fit['n_samples'],
            'evaluation_mode': 'rolling_validation',
            'evaluation_label': f"Rolling validation, {rolling_val['n_test_days']} unseen days ({rolling_val['n_folds']} folds × {rolling_val['test_block_size']} days)",
            'neutral_interpretation': 'About half of day-to-day variation is explained.',
            'limitations_note': rolling_val['limitations_note'],
            'selection_note': rolling_val['selection_note'],
            'model_comparison': rolling_val['model_comparison'],
            'feature_importances': fi,
            'rolling_validation': rolling_val,
            'training_fit': training_fit,
            'predictions_vs_actual': [
                {'actual': round(float(a), 3), 'predicted': round(float(p), 3)}
                for a, p in zip(y.tail(30).values, preds[-30:])
            ]
        }
        
        logger.info(f"Model metrics computed: Rolling R²={metrics['r2_score']}, MAE={metrics['mae']} kWh, In-sample R²={training_fit['r2_score']}")
        return metrics
        
    except Exception as e:
        logger.error(f"Error computing model scores: {e}", exc_info=True)
        return {'error': str(e)}
