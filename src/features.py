"""
Feature engineering module for Solar Energy Analytics.
Shared between ETL pipeline, training notebooks, and Flask application.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

FEATURE_NAMES: List[str] = [
    'shortwave_radiation_sum',
    'sunshine_duration',
    'cloud_cover_mean',
    'temperature_2m_mean',
    'wind_speed_10m_mean',
    'rain_sum',
    'is_weekend_enc',
    'sunshine_ratio',
    'rad_clear',
    'day_of_year',
]

TARGET_COLUMN: str = 'generation_kwh'

# Benchmark feature sets for model tournament
FEATURE_SET_A = [
    'shortwave_radiation_sum',
    'sunshine_duration',
    'cloud_cover_mean',
    'temperature_2m_mean',
    'wind_speed_10m_mean',
    'rain_sum',
    'is_weekend_enc',
    'sunshine_ratio',
    'rad_clear',
]
FEATURE_SET_B = FEATURE_SET_A + ['day_of_year']
FEATURE_SET_C = [
    'shortwave_radiation_sum',
    'sunshine_ratio',
    'cloud_cover_mean',
    'temperature_2m_mean',
    'relative_humidity_2m_mean',
    'wind_speed_10m_mean',
    'rain_sum',
    'rad_clear',
    'day_of_year',
]
FEATURE_SET_D = FEATURE_SET_C + ['gen_lag1', 'gen_rolling7']


def encode_season(month: int) -> int:
    """Encode season based on month: Wet (June-November) = 1, Dry = 0."""
    return 1 if month in [6, 7, 8, 9, 10, 11] else 0


def compute_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute engineered features from daily solar and weather columns.
    
    Features computed:
    - day_of_year: Calendar day of year (1-366) capturing seasonal sun trajectory
    - is_weekend_enc: 1 for weekend, 0 for weekday
    - sunshine_ratio: sunshine_duration / (daylight_duration or 43200)
    - rad_clear: shortwave_radiation_sum * (1 - cloud_cover_mean / 100)
    - gen_lag1: yesterday's generation (when generation_kwh is present)
    - gen_rolling7: 7-day rolling mean of past generation shifted by 1 day (leakage-free)
    
    Args:
        df (pd.DataFrame): DataFrame containing daily solar and weather data.
        
    Returns:
        pd.DataFrame: DataFrame augmented with engineered features.
    """
    df = df.copy()

    # 1. Ensure date_dt datetime series exists
    if 'date_dt' not in df.columns:
        if 'date' in df.columns:
            df['date_dt'] = pd.to_datetime(df['date'], format='mixed')
        else:
            df['date_dt'] = pd.date_range(end=pd.Timestamp.now(), periods=len(df))

    # 2. Day-of-year seasonal trend feature
    df['day_of_year'] = df['date_dt'].dt.dayofyear

    # 3. Weekend encoding (Saturday=5, Sunday=6)
    if 'is_weekend' in df.columns:
        df['is_weekend_enc'] = df['is_weekend'].fillna(False).astype(int)
    else:
        df['is_weekend_enc'] = df['date_dt'].dt.dayofweek.isin([5, 6]).astype(int)

    # 4. Sunshine efficiency ratio
    if 'daylight_duration' in df.columns and (df['daylight_duration'] > 0).any():
        daylight = df['daylight_duration'].replace(0, np.nan).fillna(43200.0)
        df['sunshine_ratio'] = (df['sunshine_duration'] / (daylight + 1e-5)).clip(0.0, 1.0)
    else:
        df['sunshine_ratio'] = (df['sunshine_duration'] / 43200.0).clip(0.0, 1.0)

    # 5. Clear-sky radiation interaction
    cloud = df['cloud_cover_mean'].fillna(0.0) if 'cloud_cover_mean' in df.columns else 0.0
    rad = df['shortwave_radiation_sum'].fillna(0.0) if 'shortwave_radiation_sum' in df.columns else 0.0
    df['rad_clear'] = rad * (1.0 - cloud / 100.0)

    # 6. Informational season encoding (not used in production model features)
    if 'season' in df.columns:
        df['season_enc'] = (df['season'].astype(str).str.strip().str.lower() == 'wet').astype(int)
    else:
        df['season_enc'] = df['date_dt'].dt.month.apply(encode_season)

    # 7. Lag and rolling past-generation features (strictly shifted to prevent leakage)
    if 'generation_kwh' in df.columns:
        df['gen_lag1'] = df['generation_kwh'].shift(1)
        df['gen_rolling7'] = df['generation_kwh'].shift(1).rolling(7).mean()

    return df


def prepare_single_prediction_features(
    data: Dict[str, Any],
    season: str = 'Dry',
    is_weekend: Any = 0,
    daylight_duration: float = None,
    date: Optional[str] = None,
    day_of_year: Optional[int] = None
) -> Dict[str, float]:
    """
    Prepare feature dictionary for a single model prediction.
    
    Args:
        data: Input features dictionary
        season: 'Dry' or 'Wet'
        is_weekend: boolean or int (0 or 1)
        daylight_duration: Optional daylight seconds
        date: Optional date string 'YYYY-MM-DD'
        day_of_year: Optional day of year (1-366)
        
    Returns:
        dict: Features dictionary matching FEATURE_NAMES
    """
    import logging
    logger = logging.getLogger(__name__)

    sunshine_duration = float(data.get('sunshine_duration', 38000.0))
    shortwave_radiation = float(data.get('shortwave_radiation_sum', 24.0))
    cloud_cover = float(data.get('cloud_cover_mean', 30.0))
    temp = float(data.get('temperature_2m_mean', 26.0))
    wind = float(data.get('wind_speed_10m_mean', 18.0))
    rain = float(data.get('rain_sum', 0.0))

    # Derive day_of_year
    doy = None
    if day_of_year is not None:
        try:
            doy = int(day_of_year)
        except (ValueError, TypeError):
            pass
    elif 'day_of_year' in data:
        try:
            doy = int(data['day_of_year'])
        except (ValueError, TypeError):
            pass
    elif date:
        try:
            doy = pd.to_datetime(date).dayofyear
        except Exception:
            pass
    elif 'date' in data:
        try:
            doy = pd.to_datetime(data['date']).dayofyear
        except Exception:
            pass

    if doy is None or not (1 <= doy <= 366):
        # Default to current date's day of year
        doy = pd.Timestamp.now().dayofyear

    # Warn if season is 'Wet' (dataset is entirely Dry season)
    season_str = str(season).strip().lower()
    if season_str == 'wet':
        logger.warning(
            "Prediction requested for Wet season: the model was trained exclusively on "
            "dry-season observations (Feb–May). Predictions carry higher uncertainty."
        )

    weekend_enc = int(bool(is_weekend))
    effective_daylight = daylight_duration if (daylight_duration and daylight_duration > 0) else float(data.get('daylight_duration', 43200.0))
    sunshine_ratio = min(max(sunshine_duration / (effective_daylight + 1e-5), 0.0), 1.0)
    rad_clear = shortwave_radiation * (1.0 - cloud_cover / 100.0)

    return {
        'shortwave_radiation_sum': shortwave_radiation,
        'sunshine_duration': sunshine_duration,
        'cloud_cover_mean': cloud_cover,
        'temperature_2m_mean': temp,
        'wind_speed_10m_mean': wind,
        'rain_sum': rain,
        'is_weekend_enc': weekend_enc,
        'sunshine_ratio': sunshine_ratio,
        'rad_clear': rad_clear,
        'day_of_year': float(doy),
    }

