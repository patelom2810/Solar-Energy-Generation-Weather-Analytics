"""
ETL Transformation Module for Solar Energy Analytics.
Cleans, dedupes, validates value ranges, builds the dim_date calendar dimension,
merges daily solar + weather, and computes engineered features using src/features.py.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from src.features import compute_engineered_features, FEATURE_NAMES, encode_season

logger = logging.getLogger(__name__)

# Numeric validation bounds
VALIDATION_BOUNDS = {
    'shortwave_radiation_sum': (0.0, 500.0),
    'sunshine_duration': (0.0, 86400.0),
    'cloud_cover_mean': (0.0, 100.0),
    'temperature_2m_mean': (-50.0, 60.0),
    'wind_speed_10m_mean': (0.0, 50.0),
    'rain_sum': (0.0, 500.0),
    'generation_kwh': (0.0, 1000.0),
    'consumption_kwh': (0.0, 1000.0),
}


def clean_and_validate(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Clean, dedupe, and validate numeric ranges in a DataFrame.
    
    Args:
        df: DataFrame to clean
        dataset_name: Identifier for logging
        
    Returns:
        pd.DataFrame: Cleaned and validated DataFrame
    """
    if df is None or len(df) == 0:
        return df
        
    df = df.copy()
    initial_rows = len(df)
    
    # Standardize date and hour_ts string formats
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    if 'hour_ts' in df.columns:
        df['hour_ts'] = df['hour_ts'].astype(str)
        
    # Deduplication
    if 'hour_ts' in df.columns:
        df = df.drop_duplicates(subset=['hour_ts'], keep='last')
    elif 'date' in df.columns:
        df = df.drop_duplicates(subset=['date'], keep='last')
        
    deduped_rows = len(df)
    if initial_rows != deduped_rows:
        logger.info(f"[{dataset_name}] Deduped {initial_rows - deduped_rows} duplicate rows ({initial_rows} -> {deduped_rows})")
        
    # Numeric column coercion and boundary validation
    for col, (min_val, max_val) in VALIDATION_BOUNDS.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            out_of_bounds = (df[col] < min_val) | (df[col] > max_val)
            outliers_count = out_of_bounds.sum()
            if outliers_count > 0:
                logger.warning(f"[{dataset_name}] Column '{col}' had {outliers_count} values outside [{min_val}, {max_val}]. Clipping.")
                df[col] = df[col].clip(lower=min_val, upper=max_val)
                
    # Sort for deterministic ordering
    if 'hour_ts' in df.columns:
        df = df.sort_values('hour_ts').reset_index(drop=True)
    elif 'date' in df.columns:
        df = df.sort_values('date').reset_index(drop=True)
        
    return df


def build_dim_date(dates_series: pd.Series) -> pd.DataFrame:
    """
    Build the full star-schema dim_date dimension table from dates.
    
    Attributes:
    date_key, date, year, quarter, quarter_name, month_number, month_name,
    year_month, week_of_year, day_of_month, day_of_week_number, day_name,
    day_of_year, season, is_weekend
    
    Args:
        dates_series: Series or list of date strings/datetimes
        
    Returns:
        pd.DataFrame: Dimension table
    """
    unique_dates = pd.to_datetime(pd.Series(dates_series).dropna().unique())
    unique_dates = sorted(unique_dates)
    
    records = []
    for dt in unique_dates:
        # ISO calendar week calculation
        iso_calendar = dt.isocalendar()
        is_weekend = dt.dayofweek in [5, 6]
        season = 'Wet' if dt.month in [6, 7, 8, 9, 10, 11] else 'Dry'
        
        record = {
            'date_key': int(dt.strftime('%Y%m%d')),
            'date': dt.strftime('%Y-%m-%d'),
            'year': int(dt.year),
            'quarter': int((dt.month - 1) // 3 + 1),
            'quarter_name': f"Q{(dt.month - 1) // 3 + 1} {dt.year}",
            'month_number': int(dt.month),
            'month_name': dt.strftime('%B'),
            'year_month': dt.strftime('%Y-%m'),
            'week_of_year': int(iso_calendar.week),
            'day_of_month': int(dt.day),
            'day_of_week_number': int(dt.dayofweek + 1),  # 1=Monday ... 7=Sunday
            'day_name': dt.strftime('%A'),
            'day_of_year': int(dt.dayofyear),
            'season': season,
            'is_weekend': bool(is_weekend)
        }
        records.append(record)
        
    df_dim_date = pd.DataFrame(records)
    logger.info(f"Built dim_date dimension table with {len(df_dim_date)} dates")
    return df_dim_date


def transform_all(extracted_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Execute full transform pipeline.
    
    Args:
        extracted_data: Dict with raw DataFrames
        
    Returns:
        dict: Cleaned and feature-engineered datasets
    """
    logger.info("Starting ETL transformation phase...")
    
    # 1. Clean individual fact tables
    df_wd = clean_and_validate(extracted_data.get('weather_daily'), 'fact_weather_daily')
    df_wh = clean_and_validate(extracted_data.get('weather_hourly'), 'fact_weather_hourly')
    df_sd = clean_and_validate(extracted_data.get('solar_daily'), 'fact_solar_daily')
    df_sh = clean_and_validate(extracted_data.get('solar_hourly'), 'fact_solar_hourly')
    
    # 2. Collect all dates to build dim_date
    all_dates = []
    if 'date' in df_wd.columns:
        all_dates.extend(df_wd['date'].tolist())
    if 'date' in df_sd.columns:
        all_dates.extend(df_sd['date'].tolist())
    dim_date_df = build_dim_date(pd.Series(all_dates))
    
    # 3. Merge daily solar + weather + date dimension for feature engineering
    daily_merged = pd.merge(df_sd, df_wd, on='date', how='inner')
    if len(daily_merged) > 0 and len(dim_date_df) > 0:
        daily_merged = pd.merge(
            daily_merged,
            dim_date_df[['date', 'season', 'is_weekend', 'day_name', 'month_name']],
            on='date',
            how='left'
        )
        
    # 4. Compute engineered features using shared module
    daily_features = compute_engineered_features(daily_merged)
    logger.info(f"Computed {len(FEATURE_NAMES)} engineered features for {len(daily_features)} daily records")
    
    return {
        'dim_date': dim_date_df,
        'fact_solar_daily': df_sd,
        'fact_weather_daily': df_wd,
        'fact_solar_hourly': df_sh,
        'fact_weather_hourly': df_wh,
        'daily_features': daily_features
    }
