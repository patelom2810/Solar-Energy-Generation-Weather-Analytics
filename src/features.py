"""
Feature engineering module for Solar Energy Analytics.
Shared between ETL pipeline, training notebooks, and Flask application.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List

FEATURE_NAMES: List[str] = [
    'shortwave_radiation_sum',
    'sunshine_duration',
    'cloud_cover_mean',
    'temperature_2m_mean',
    'wind_speed_10m_mean',
    'rain_sum',
    'season_enc',
    'is_weekend_enc',
    'sunshine_ratio',
    'rad_clear',
]

TARGET_COLUMN: str = 'generation_kwh'


def encode_season(month: int) -> int:
    """Encode season based on month: Wet (June-November) = 1, Dry = 0."""
    return 1 if month in [6, 7, 8, 9, 10, 11] else 0


def compute_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute engineered features from daily solar and weather columns.
    
    Features computed:
    - season_enc: 1 for Wet season, 0 for Dry season
    - is_weekend_enc: 1 for weekend, 0 for weekday
    - sunshine_ratio: sunshine_duration / (daylight_duration or 86400)
    - rad_clear: shortwave_radiation_sum * (1 - cloud_cover_mean / 100)
    
    Args:
        df (pd.DataFrame): DataFrame containing daily solar and weather data.
        
    Returns:
        pd.DataFrame: DataFrame augmented with engineered features.
    """
    df = df.copy()

    # 1. Ensure date_dt datetime series exists
    if 'date_dt' not in df.columns:
        if 'date' in df.columns:
            df['date_dt'] = pd.to_datetime(df['date'])
        else:
            df['date_dt'] = pd.date_range(end=pd.Timestamp.now(), periods=len(df))

    # 2. Season encoding (Wet=1, Dry=0)
    if 'season' in df.columns:
        df['season_enc'] = (df['season'].astype(str).str.strip().str.lower() == 'wet').astype(int)
    else:
        df['season_enc'] = df['date_dt'].dt.month.apply(encode_season)

    # 3. Weekend encoding (Saturday=5, Sunday=6)
    if 'is_weekend' in df.columns:
        df['is_weekend_enc'] = df['is_weekend'].fillna(False).astype(int)
    else:
        df['is_weekend_enc'] = df['date_dt'].dt.dayofweek.isin([5, 6]).astype(int)

    # 4. Sunshine efficiency ratio
    # If daylight_duration is provided, use it (exact formula from 02_Modelling.ipynb)
    if 'daylight_duration' in df.columns and (df['daylight_duration'] > 0).any():
        daylight = df['daylight_duration'].replace(0, np.nan).fillna(43200.0)
        df['sunshine_ratio'] = (df['sunshine_duration'] / (daylight + 1e-5)).clip(0.0, 1.0)
    else:
        df['sunshine_ratio'] = (df['sunshine_duration'] / 43200.0).clip(0.0, 1.0)

    # 5. Clear-sky radiation interaction
    cloud = df['cloud_cover_mean'].fillna(0.0) if 'cloud_cover_mean' in df.columns else 0.0
    rad = df['shortwave_radiation_sum'].fillna(0.0) if 'shortwave_radiation_sum' in df.columns else 0.0
    df['rad_clear'] = rad * (1.0 - cloud / 100.0)

    return df


def prepare_single_prediction_features(
    data: Dict[str, Any],
    season: str = 'Dry',
    is_weekend: Any = 0,
    daylight_duration: float = None
) -> Dict[str, float]:
    """
    Prepare feature dictionary for a single model prediction.
    
    Args:
        data: Input features dictionary
        season: 'Dry' or 'Wet'
        is_weekend: boolean or int (0 or 1)
        daylight_duration: Optional daylight seconds
        
    Returns:
        dict: Features dictionary matching FEATURE_NAMES
    """
    sunshine_duration = float(data.get('sunshine_duration', 38000.0))
    shortwave_radiation = float(data.get('shortwave_radiation_sum', 24.0))
    cloud_cover = float(data.get('cloud_cover_mean', 30.0))
    temp = float(data.get('temperature_2m_mean', 26.0))
    wind = float(data.get('wind_speed_10m_mean', 18.0))
    rain = float(data.get('rain_sum', 0.0))

    season_str = str(season).strip().lower()
    season_enc = 1 if season_str == 'wet' else 0
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
        'season_enc': season_enc,
        'is_weekend_enc': weekend_enc,
        'sunshine_ratio': sunshine_ratio,
        'rad_clear': rad_clear,
    }
