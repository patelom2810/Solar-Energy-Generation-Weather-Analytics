"""
Model Retraining Module for Solar Energy Analytics.
Evaluates a tournament of candidate model architectures (Huber Robust Regressor,
Hybrid Voting Ensemble, Tuned Gradient Boosting, and Ridge Regression) against
the baseline benchmark using fair, leakage-free chronological validation.
Only promotes and replaces the production model if the candidate demonstrates
measurable out-of-sample error reduction.
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from src.features import FEATURE_NAMES, TARGET_COLUMN

logger = logging.getLogger(__name__)

MODELS_DIR = 'models'
PRODUCTION_MODEL_PATH = os.path.join(MODELS_DIR, 'solar_generation_model.pkl')
FEATURE_NAMES_PATH = os.path.join(MODELS_DIR, 'feature_names.pkl')


def evaluate_model(model, X_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, float]:
    """Calculate evaluation metrics on validation set with non-negative physical clipping."""
    preds = np.clip(model.predict(X_val), 0.0, None)
    mse = mean_squared_error(y_val, preds)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_val, preds))
    r2 = float(r2_score(y_val, preds))
    mape = float(np.mean(np.abs((y_val - preds) / np.maximum(np.abs(y_val), 1e-5)))) * 100
    return {
        'rmse': round(rmse, 4),
        'mae': round(mae, 4),
        'r2': round(r2, 4),
        'mape': round(mape, 2)
    }


def build_candidate_models() -> Dict[str, Any]:
    """
    Construct competitive candidate model architectures.
    
    Includes:
    1. Huber_Robust: Robust linear pipeline handling trend shifts and outliers
    2. Ensemble_Hybrid: Weighted blend of robust linear and tuned tree boosting
    3. Tuned_GBR: Regularized gradient boosting with shallow depth and subsampling
    4. Ridge_Scaled: Regularized L2 linear pipeline
    """
    return {
        'Huber_Robust': Pipeline([
            ('scaler', RobustScaler()),
            ('reg', HuberRegressor(epsilon=1.35, alpha=1.0, max_iter=500))
        ]),
        'Ensemble_Hybrid': VotingRegressor([
            ('huber', Pipeline([('scaler', RobustScaler()), ('reg', HuberRegressor(epsilon=1.35, alpha=1.0, max_iter=500))])),
            ('gbr', GradientBoostingRegressor(n_estimators=80, learning_rate=0.04, max_depth=2, min_samples_leaf=3, subsample=0.8, random_state=42))
        ], weights=[0.7, 0.3]),
        'Tuned_GBR': GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.04,
            max_depth=2,
            min_samples_split=4,
            min_samples_leaf=3,
            subsample=0.8,
            random_state=42
        ),
        'Ridge_Scaled': Pipeline([
            ('scaler', StandardScaler()),
            ('reg', Ridge(alpha=5.0))
        ])
    }


def evaluate_and_retrain_model(
    df_features: pd.DataFrame,
    train_ratio: float = 0.8,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Train candidate models using chronological train/validation split,
    fairly benchmark against baseline without data leakage, and deploy
    the winning candidate if it beats the benchmark.
    
    Args:
        df_features: DataFrame containing FEATURE_NAMES and TARGET_COLUMN
        train_ratio: Chronological train/validation ratio (default: 0.8)
        force_update: If True, replace production model regardless of comparison
        
    Returns:
        dict: Summary of retraining outcome
    """
    logger.info("Evaluating model retraining tournament on refreshed dataset...")
    
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
    
    # Train baseline benchmark on X_train to prevent data leakage
    baseline_benchmark = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.08,
        max_depth=3,
        min_samples_split=3,
        subsample=0.85,
        random_state=42
    )
    baseline_benchmark.fit(X_train, y_train)
    baseline_metrics = evaluate_model(baseline_benchmark, X_val, y_val)
    logger.info(f"Baseline Benchmark Metrics (out-of-sample): R²={baseline_metrics['r2']}, RMSE={baseline_metrics['rmse']}, MAE={baseline_metrics['mae']}")
    
    # Run tournament across candidate architectures
    candidates = build_candidate_models()
    tournament_results = {}
    best_candidate_name = None
    best_candidate_model = None
    best_candidate_metrics = None
    
    for name, candidate in candidates.items():
        candidate.fit(X_train, y_train)
        metrics = evaluate_model(candidate, X_val, y_val)
        tournament_results[name] = metrics
        logger.info(f"Candidate [{name:16s}] -> RMSE={metrics['rmse']:.4f}, MAE={metrics['mae']:.4f}, R²={metrics['r2']:.4f}, MAPE={metrics['mape']:.2f}%")
        
        # Track best candidate (lowest RMSE, tie-break on MAE)
        if (best_candidate_metrics is None or
            metrics['rmse'] < best_candidate_metrics['rmse'] or
            (metrics['rmse'] == best_candidate_metrics['rmse'] and metrics['mae'] < best_candidate_metrics['mae'])):
            best_candidate_name = name
            best_candidate_model = candidate
            best_candidate_metrics = metrics
            
    logger.info(f"🏆 Winning Candidate: {best_candidate_name} with RMSE={best_candidate_metrics['rmse']} (Baseline: {baseline_metrics['rmse']})")
    
    # Fair comparison against baseline benchmark
    improved = False
    if best_candidate_metrics['rmse'] < baseline_metrics['rmse'] or force_update:
        improved = True
        
    outcome = {
        'retrained': True,
        'improved': improved,
        'best_candidate_name': best_candidate_name,
        'candidate_metrics': best_candidate_metrics,
        'current_metrics': baseline_metrics,
        'tournament_results': tournament_results,
        'samples_evaluated': len(val_df),
        'timestamp': datetime.now().isoformat()
    }
    
    if improved:
        os.makedirs(MODELS_DIR, exist_ok=True)
        version_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        versioned_path = os.path.join(MODELS_DIR, f"solar_generation_model_v{version_str}.pkl")
        
        # Retrain winning candidate on full dataset before production deployment
        full_candidate = build_candidate_models()[best_candidate_name]
        full_candidate.fit(valid_df[FEATURE_NAMES], valid_df[TARGET_COLUMN])
        
        # Save versioned archive and update production model
        joblib.dump(full_candidate, versioned_path)
        joblib.dump(full_candidate, PRODUCTION_MODEL_PATH)
        joblib.dump(FEATURE_NAMES, FEATURE_NAMES_PATH)
        
        outcome['model_version'] = f"v{version_str}"
        outcome['versioned_path'] = versioned_path
        rmse_reduction = round((1 - best_candidate_metrics['rmse'] / baseline_metrics['rmse']) * 100, 2)
        outcome['rmse_reduction_pct'] = rmse_reduction
        outcome['message'] = f"Production model updated to {best_candidate_name} with {rmse_reduction}% RMSE reduction."
        logger.info(f"✓ Production model updated to {best_candidate_name} and archived as {versioned_path}")
    else:
        outcome['message'] = "Current baseline benchmark outperformed candidate. Retained existing model."
        logger.info("Current baseline retained (candidates did not improve validation score).")
        
    return outcome
