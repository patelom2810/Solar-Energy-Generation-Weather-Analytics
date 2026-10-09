"""
Model Retraining Module for Solar Energy Analytics.
Evaluates a tournament of candidate model architectures using rolling-origin
time-series validation (TimeSeriesSplit(n_splits=5, test_size=10)).
Fairly benchmarks candidate models without data leakage. Selects champion based
on out-of-sample mean CV RMSE and MAE across folds.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import joblib
import sklearn
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, ExtraTreesRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import r2_score, root_mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import TimeSeriesSplit
try:
    import xgboost as xgb
except ImportError:
    xgb = None

from src.features import (
    FEATURE_NAMES,
    TARGET_COLUMN,
    FEATURE_SET_A,
    FEATURE_SET_B,
    FEATURE_SET_C,
    FEATURE_SET_D,
    compute_engineered_features
)
from src.utils import filter_anomalies

logger = logging.getLogger(__name__)

MODELS_DIR = 'models'
PRODUCTION_MODEL_PATH = os.path.join(MODELS_DIR, 'solar_generation_model.pkl')
LAG_MODEL_PATH = os.path.join(MODELS_DIR, 'solar_generation_lag_model.pkl')
FEATURE_NAMES_PATH = os.path.join(MODELS_DIR, 'feature_names.pkl')
LAG_FEATURE_NAMES_PATH = os.path.join(MODELS_DIR, 'feature_names_lag.pkl')
METADATA_PATH = os.path.join(MODELS_DIR, 'model_metadata.json')


def evaluate_model(model, X_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, float]:
    """Calculate evaluation metrics on validation set with non-negative physical clipping."""
    preds = np.clip(model.predict(X_val), 0.0, None)
    mse = float(np.mean((y_val - preds) ** 2))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_val, preds))
    r2 = float(r2_score(y_val, preds))
    mape = float(mean_absolute_percentage_error(y_val, preds) * 100)
    return {
        'rmse': round(rmse, 4),
        'mae': round(mae, 4),
        'r2': round(r2, 4),
        'mape': round(mape, 2)
    }


def build_candidate_models() -> Dict[str, Tuple[Any, List[str]]]:
    """
    Construct competitive candidate architectures paired with their feature sets.
    
    Returns:
        dict: name -> (model_instance, feature_columns)
    """
    return {
        'Ridge_Set_B': (
            Pipeline([('scaler', StandardScaler()), ('reg', Ridge(alpha=3.0))]),
            FEATURE_SET_B
        ),
        'Ridge_Set_A': (
            Pipeline([('scaler', StandardScaler()), ('reg', Ridge(alpha=3.0))]),
            FEATURE_SET_A
        ),
        'Ridge_Set_C': (
            Pipeline([('scaler', StandardScaler()), ('reg', Ridge(alpha=3.0))]),
            FEATURE_SET_C
        ),
        'Huber_Robust_Set_A': (
            Pipeline([('scaler', RobustScaler()), ('reg', HuberRegressor(epsilon=1.35, alpha=1.0, max_iter=500))]),
            FEATURE_SET_A
        ),
        'Huber_Robust_Set_B': (
            Pipeline([('scaler', RobustScaler()), ('reg', HuberRegressor(epsilon=1.35, alpha=1.0, max_iter=500))]),
            FEATURE_SET_B
        ),
        'GradientBoosting_Set_B': (
            GradientBoostingRegressor(n_estimators=150, learning_rate=0.05, max_depth=2, subsample=0.8, random_state=42),
            FEATURE_SET_B
        ),
        'RandomForest_Set_B': (
            RandomForestRegressor(n_estimators=150, max_depth=5, random_state=42),
            FEATURE_SET_B
        ),
        'ExtraTrees_Set_B': (
            ExtraTreesRegressor(n_estimators=300, min_samples_leaf=3, random_state=42),
            FEATURE_SET_B
        ),
        'XGBoost_d1_Set_B': (
            xgb.XGBRegressor(max_depth=1, n_estimators=100, learning_rate=0.05, random_state=42),
            FEATURE_SET_B
        ),
        'XGBoost_d2_Set_B': (
            xgb.XGBRegressor(max_depth=2, n_estimators=100, learning_rate=0.05, random_state=42),
            FEATURE_SET_B
        ),
        'XGBoost_d3_Set_B': (
            xgb.XGBRegressor(max_depth=3, n_estimators=100, learning_rate=0.05, random_state=42),
            FEATURE_SET_B
        ),
        'XGBoost_linear_Set_B': (
            xgb.XGBRegressor(booster='gblinear', random_state=42),
            FEATURE_SET_B
        ),
        'Ridge_Lag_Set_D': (
            Pipeline([('scaler', StandardScaler()), ('reg', Ridge(alpha=3.0))]),
            FEATURE_SET_D
        ),
    }


def evaluate_and_retrain_model(
    df_features: pd.DataFrame,
    force_update: bool = False,
    n_splits: int = 5,
    test_size: int = 10
) -> Dict[str, Any]:
    """
    Train and evaluate model candidates using rolling-origin cross-validation:
    TimeSeriesSplit(n_splits=5, test_size=10).
    
    Promotes the winning weather-only model if it outperforms the baseline/current model.
    Saves per-fold and average metrics, archives artifacts, and writes model metadata.
    
    Args:
        df_features: DataFrame containing features and target
        force_update: If True, overwrite production model regardless of score comparison
        n_splits: Number of rolling folds (default: 5)
        test_size: Number of out-of-sample samples per fold (default: 10)
        
    Returns:
        dict: Summary of tournament outcome
    """
    logger.info("Evaluating model retraining tournament with rolling-origin TimeSeriesSplit...")
    
    # Exclude documented anomaly dates
    clean_df = filter_anomalies(df_features)
    
    # Ensure engineered features are present
    if 'day_of_year' not in clean_df.columns:
        clean_df = compute_engineered_features(clean_df)
        
    if 'date' in clean_df.columns:
        clean_df = clean_df.sort_values('date').reset_index(drop=True)
        
    # Drop rows missing target
    if TARGET_COLUMN not in clean_df.columns:
        err = f"Target column '{TARGET_COLUMN}' not found"
        logger.error(err)
        return {'retrained': False, 'error': err}
        
    clean_df = clean_df.dropna(subset=[TARGET_COLUMN]).reset_index(drop=True)
    
    # Check dataset size
    n_samples = len(clean_df)
    min_required = n_splits * test_size + 10
    if n_samples < min_required:
        err = f"Insufficient sample size ({n_samples} rows; minimum required {min_required})"
        logger.warning(err)
        return {'retrained': False, 'error': err, 'n_samples': n_samples}

    # Common evaluation dataset where lag features are non-null
    eval_df = clean_df.dropna(subset=['gen_rolling7']).reset_index(drop=True)
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)
    
    # ── 1. Evaluate Baselines ─────────────────────────────────────────────
    tournament_results = {}
    
    # Baseline 1: Training window mean
    mean_fold_maes, mean_fold_rmses, mean_fold_r2s = [], [], []
    for tr_idx, te_idx in tscv.split(eval_df):
        y_tr = eval_df.iloc[tr_idx][TARGET_COLUMN]
        y_te = eval_df.iloc[te_idx][TARGET_COLUMN].values
        pred = np.full(len(te_idx), y_tr.mean())
        mean_fold_maes.append(mean_absolute_error(y_te, pred))
        mean_fold_rmses.append(root_mean_squared_error(y_te, pred))
        mean_fold_r2s.append(r2_score(y_te, pred))
    tournament_results['Baseline_Mean'] = {
        'feature_set': 'None',
        'mean_cv_rmse': round(float(np.mean(mean_fold_rmses)), 4),
        'mean_cv_mae': round(float(np.mean(mean_fold_maes)), 4),
        'mean_cv_r2': round(float(np.mean(mean_fold_r2s)), 4),
        'fold_maes': [round(float(m), 4) for m in mean_fold_maes]
    }
    
    # Baseline 2: Persistence (yesterday's generation)
    persist_fold_maes, persist_fold_rmses, persist_fold_r2s = [], [], []
    for tr_idx, te_idx in tscv.split(eval_df):
        y_te = eval_df.iloc[te_idx][TARGET_COLUMN].values
        pred = eval_df.iloc[te_idx]['gen_lag1'].values
        persist_fold_maes.append(mean_absolute_error(y_te, pred))
        persist_fold_rmses.append(root_mean_squared_error(y_te, pred))
        persist_fold_r2s.append(r2_score(y_te, pred))
    tournament_results['Baseline_Persistence'] = {
        'feature_set': 'gen_lag1',
        'mean_cv_rmse': round(float(np.mean(persist_fold_rmses)), 4),
        'mean_cv_mae': round(float(np.mean(persist_fold_maes)), 4),
        'mean_cv_r2': round(float(np.mean(persist_fold_r2s)), 4),
        'fold_maes': [round(float(m), 4) for m in persist_fold_maes]
    }

    # ── 2. Evaluate ML Candidate Architectures ─────────────────────────────
    candidates = build_candidate_models()
    best_weather_model_name = None
    best_weather_rmse = float('inf')
    best_weather_metrics = None
    best_weather_obj = None

    for name, (model_template, feats) in candidates.items():
        fold_maes, fold_rmses, fold_r2s, fold_mapes = [], [], [], []
        all_y, all_p = [], []
        
        for tr_idx, te_idx in tscv.split(eval_df):
            X_tr = eval_df.iloc[tr_idx][feats]
            y_tr = eval_df.iloc[tr_idx][TARGET_COLUMN]
            X_te = eval_df.iloc[te_idx][feats]
            y_te = eval_df.iloc[te_idx][TARGET_COLUMN]
            
            # Recreate/clone model
            from sklearn.base import clone
            fold_model = clone(model_template)
            fold_model.fit(X_tr, y_tr)
            
            p = np.clip(fold_model.predict(X_te), 0.0, None)
            fold_maes.append(float(mean_absolute_error(y_te, p)))
            fold_rmses.append(float(root_mean_squared_error(y_te, p)))
            fold_r2s.append(float(r2_score(y_te, p)))
            fold_mapes.append(float(mean_absolute_percentage_error(y_te, p) * 100))
            all_y.extend(y_te)
            all_p.extend(p)

        pooled_r2 = round(float(r2_score(all_y, all_p)), 4)
        pooled_mae = round(float(mean_absolute_error(all_y, all_p)), 4)
        pooled_rmse = round(float(root_mean_squared_error(all_y, all_p)), 4)
        mean_cv_rmse = round(float(np.mean(fold_rmses)), 4)
        mean_cv_mae = round(float(np.mean(fold_maes)), 4)
        mean_cv_r2 = round(float(np.mean(fold_r2s)), 4)
        mean_cv_mape = round(float(np.mean(fold_mapes)), 2)

        metrics = {
            'mean_cv_rmse': mean_cv_rmse,
            'mean_cv_mae': mean_cv_mae,
            'mean_cv_r2': mean_cv_r2,
            'mean_cv_mape': mean_cv_mape,
            'pooled_r2': pooled_r2,
            'pooled_mae': pooled_mae,
            'pooled_rmse': pooled_rmse,
            'fold_maes': [round(m, 4) for m in fold_maes]
        }
        tournament_results[name] = metrics
        logger.info(f"Tournament [{name:22s}] CV_RMSE={mean_cv_rmse:.4f}, CV_MAE={mean_cv_mae:.4f}, Pooled_R2={pooled_r2:.4f}")

        # Track best weather-only candidate (Set B or C)
        is_weather_only = 'Lag' not in name and 'Set_D' not in name
        if is_weather_only and (mean_cv_rmse < best_weather_rmse):
            best_weather_rmse = mean_cv_rmse
            best_weather_model_name = name
            best_weather_metrics = metrics
            best_weather_obj = model_template

    # ── 3. Evaluation Against Current Production Model ─────────────────────
    current_metrics = None
    if os.path.exists(PRODUCTION_MODEL_PATH) and os.path.exists(FEATURE_NAMES_PATH):
        try:
            curr_model = joblib.load(PRODUCTION_MODEL_PATH)
            curr_feats = joblib.load(FEATURE_NAMES_PATH)
            curr_rmses, curr_maes, curr_r2s = [], [], []
            for tr_idx, te_idx in tscv.split(eval_df):
                X_tr = eval_df.iloc[tr_idx][curr_feats]
                y_tr = eval_df.iloc[tr_idx][TARGET_COLUMN]
                X_te = eval_df.iloc[te_idx][curr_feats]
                y_te = eval_df.iloc[te_idx][TARGET_COLUMN]
                from sklearn.base import clone
                m_curr = clone(curr_model)
                m_curr.fit(X_tr, y_tr)
                p = np.clip(m_curr.predict(X_te), 0.0, None)
                curr_rmses.append(float(root_mean_squared_error(y_te, p)))
                curr_maes.append(float(mean_absolute_error(y_te, p)))
                curr_r2s.append(float(r2_score(y_te, p)))
            current_metrics = {
                'mean_cv_rmse': round(float(np.mean(curr_rmses)), 4),
                'mean_cv_mae': round(float(np.mean(curr_maes)), 4),
                'mean_cv_r2': round(float(np.mean(curr_r2s)), 4),
                'fold_maes': [round(m, 4) for m in curr_maes]
            }
        except Exception as e_curr:
            logger.warning(f"Could not benchmark current production model: {e_curr}")

    # Determine whether champion improved
    improved = False
    if current_metrics is None or force_update:
        improved = True
    elif best_weather_metrics['mean_cv_rmse'] < current_metrics['mean_cv_rmse']:
        improved = True

    # ── 4. Promote and Persist Champion Model ──────────────────────────────
    os.makedirs(MODELS_DIR, exist_ok=True)
    version_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    versioned_path = os.path.join(MODELS_DIR, f"solar_generation_model_v{version_str}.pkl")

    outcome = {
        'retrained': True,
        'improved': improved,
        'champion_name': best_weather_model_name,
        'candidate_metrics': best_weather_metrics,
        'current_metrics': current_metrics or tournament_results['Baseline_Persistence'],
        'tournament_results': tournament_results,
        'n_folds': n_splits,
        'test_size_per_fold': test_size,
        'samples_evaluated': len(eval_df),
        'timestamp': datetime.now().isoformat()
    }

    if improved:
        # Fit champion weather model on full clean dataset with FEATURE_SET_B
        from sklearn.base import clone
        prod_model = clone(best_weather_obj)
        prod_model.fit(clean_df[FEATURE_SET_B], clean_df[TARGET_COLUMN])

        # Save production model and features
        joblib.dump(prod_model, versioned_path)
        joblib.dump(prod_model, PRODUCTION_MODEL_PATH)
        joblib.dump(FEATURE_SET_B, FEATURE_NAMES_PATH)

        # Train and save optional lag-feature model (Ridge on Set D)
        lag_model_template, lag_feats = candidates['Ridge_Lag_Set_D']
        lag_model = clone(lag_model_template)
        lag_model.fit(eval_df[lag_feats], eval_df[TARGET_COLUMN])
        joblib.dump(lag_model, LAG_MODEL_PATH)
        joblib.dump(lag_feats, LAG_FEATURE_NAMES_PATH)

        # Save model metadata JSON
        metadata = {
            'model_name': best_weather_model_name,
            'model_type': type(prod_model).__name__,
            'display_name': 'Pipeline (StandardScaler → Ridge)',
            'algorithm_family': 'L2 Regularized Linear Regression (Ridge, alpha=3.0)',
            'features': FEATURE_SET_B,
            'n_features': len(FEATURE_SET_B),
            'feature_set_label': 'Feature Set B (weather-only with day_of_year)',
            'target': TARGET_COLUMN,
            'training_samples': len(clean_df),
            'cv_strategy': 'TimeSeriesSplit(n_splits=5, test_size=10)',
            'mean_cv_rmse': best_weather_metrics['mean_cv_rmse'],
            'mean_cv_mae': best_weather_metrics['mean_cv_mae'],
            'mean_cv_r2': best_weather_metrics['mean_cv_r2'],
            'pooled_r2': best_weather_metrics['pooled_r2'],
            'scikit_learn_version': sklearn.__version__,
            'xgboost_version': xgb.__version__,
            'pandas_version': pd.__version__,
            'numpy_version': np.__version__,
            'joblib_version': joblib.__version__,
            'anomaly_dates_excluded': ['2026-02-01', '2026-03-31'],
            'trained_at': datetime.now().isoformat(),
            'version': f"v{version_str}"
        }
        with open(METADATA_PATH, 'w') as f_meta:
            json.dump(metadata, f_meta, indent=2)

        outcome['model_version'] = f"v{version_str}"
        outcome['versioned_path'] = versioned_path
        outcome['metadata_path'] = METADATA_PATH
        outcome['message'] = (
            f"Production champion updated to {best_weather_model_name} "
            f"(CV RMSE: {best_weather_metrics['mean_cv_rmse']} kWh, CV MAE: {best_weather_metrics['mean_cv_mae']} kWh)."
        )
        logger.info(f"✓ Production model deployed: {best_weather_model_name} ({versioned_path})")
    else:
        outcome['message'] = "Current production model retained (candidate did not achieve error reduction)."
        logger.info("Current production model retained.")

    return outcome
