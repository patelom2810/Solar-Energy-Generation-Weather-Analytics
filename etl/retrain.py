"""
Model Retraining Module for Solar Energy Analytics.
Retrains GradientBoostingRegressor using a time-based chronological split,
compares metrics (R² and RMSE) against the production model, and only replaces
the model if the candidate improves upon the current benchmark.
"""
import os
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from src.features import FEATURE_NAMES, TARGET_COLUMN

logger = logging.getLogger(__name__)

MODELS_DIR = 'models'
PRODUCTION_MODEL_PATH = os.path.join(MODELS_DIR, 'solar_generation_model.pkl')
FEATURE_NAMES_PATH = os.path.join(MODELS_DIR, 'feature_names.pkl')


def evaluate_model(model, X_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, float]:
    """Calculate evaluation metrics on validation set."""
    preds = model.predict(X_val)
    mse = mean_squared_error(y_val, preds)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_val, preds))
    r2 = float(r2_score(y_val, preds))
    return {
        'rmse': round(rmse, 4),
        'mae': round(mae, 4),
        'r2': round(r2, 4)
    }


def evaluate_and_retrain_model(
    df_features: pd.DataFrame,
    train_ratio: float = 0.8,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Train candidate model using chronological train/validation split,
    compare with production model, and update only if metrics improve.
    
    Args:
        df_features: DataFrame containing FEATURE_NAMES and TARGET_COLUMN
        train_ratio: Chronological train/validation ratio (default: 0.8)
        force_update: If True, replace production model regardless of comparison
        
    Returns:
        dict: Summary of retraining outcome
    """
    logger.info("Evaluating model retraining on refreshed dataset...")
    
    # Validate required columns
    missing_feats = [f for f in FEATURE_NAMES if f not in df_features.columns]
    if missing_feats:
        err_msg = f"Cannot retrain model: missing features {missing_feats}"
        logger.error(err_msg)
        return {'retrained': False, 'error': err_msg}
        
    if TARGET_COLUMN not in df_features.columns:
        err_msg = f"Cannot retrain model: target column '{TARGET_COLUMN}' not found"
        logger.error(err_msg)
        return {'retrained': False, 'error': err_msg}
        
    # Drop rows with missing features or targets
    valid_df = df_features.dropna(subset=FEATURE_NAMES + [TARGET_COLUMN]).copy()
    if 'date' in valid_df.columns:
        valid_df = valid_df.sort_values('date').reset_index(drop=True)
        
    n_samples = len(valid_df)
    if n_samples < 20:
        err_msg = f"Insufficient sample size ({n_samples} rows) to retrain robustly."
        logger.warning(err_msg)
        return {'retrained': False, 'error': err_msg, 'n_samples': n_samples}
        
    # Chronological time-based split
    split_idx = int(n_samples * train_ratio)
    train_df = valid_df.iloc[:split_idx]
    val_df = valid_df.iloc[split_idx:]
    
    X_train, y_train = train_df[FEATURE_NAMES], train_df[TARGET_COLUMN]
    X_val, y_val = val_df[FEATURE_NAMES], val_df[TARGET_COLUMN]
    
    logger.info(f"Chronological split: Train={len(train_df)} samples, Val={len(val_df)} samples")
    
    # Train candidate model with tuned hyperparameters
    candidate_model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.08,
        max_depth=3,
        min_samples_split=3,
        subsample=0.85,
        random_state=42
    )
    candidate_model.fit(X_train, y_train)
    candidate_metrics = evaluate_model(candidate_model, X_val, y_val)
    logger.info(f"Candidate Model Metrics: R²={candidate_metrics['r2']}, RMSE={candidate_metrics['rmse']}, MAE={candidate_metrics['mae']}")
    
    # Evaluate current production model if present
    current_metrics = None
    improved = False
    
    if os.path.exists(PRODUCTION_MODEL_PATH):
        try:
            prod_model = joblib.load(PRODUCTION_MODEL_PATH)
            current_metrics = evaluate_model(prod_model, X_val, y_val)
            logger.info(f"Current Model Metrics:   R²={current_metrics['r2']}, RMSE={current_metrics['rmse']}, MAE={current_metrics['mae']}")
            
            # Improvement rule: lower RMSE or lower MAE
            if (candidate_metrics['rmse'] < current_metrics['rmse'] or (candidate_metrics['mae'] < current_metrics['mae'] and candidate_metrics['rmse'] <= current_metrics['rmse'])) or force_update:
                improved = True
        except Exception as e:
            logger.warning(f"Could not evaluate current production model: {e}. Defaulting to update.")
            improved = True
    else:
        improved = True
        
    outcome = {
        'retrained': True,
        'improved': improved,
        'candidate_metrics': candidate_metrics,
        'current_metrics': current_metrics,
        'samples_evaluated': len(val_df),
        'timestamp': datetime.now().isoformat()
    }
    
    if improved:
        os.makedirs(MODELS_DIR, exist_ok=True)
        version_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        versioned_path = os.path.join(MODELS_DIR, f"solar_generation_model_v{version_str}.pkl")
        
        # Train on full dataset before final deployment
        candidate_model.fit(valid_df[FEATURE_NAMES], valid_df[TARGET_COLUMN])
        
        # Save versioned model and update production model
        joblib.dump(candidate_model, versioned_path)
        joblib.dump(candidate_model, PRODUCTION_MODEL_PATH)
        joblib.dump(FEATURE_NAMES, FEATURE_NAMES_PATH)
        
        outcome['model_version'] = f"v{version_str}"
        outcome['versioned_path'] = versioned_path
        logger.info(f"✓ Production model updated and archived as {versioned_path}")
    else:
        outcome['message'] = "Current production model outperformed candidate. Retained existing model."
        logger.info("Current production model retained (candidate did not improve validation score).")
        
    return outcome
