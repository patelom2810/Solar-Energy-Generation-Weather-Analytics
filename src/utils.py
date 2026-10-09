"""
Utility functions for Solar Analytics application
"""
import logging
from typing import Tuple, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def validate_prediction_input(data):
    """
    Validate prediction input parameters.
    
    Args:
        data (dict): Input data from request
        
    Returns:
        tuple: (is_valid: bool, errors: list, validated_data: dict)
    """
    errors = []
    warning = None
    
    # Feature bounds for numeric validation
    FEATURE_BOUNDS = {
        'shortwave_radiation_sum': (0, 500),
        'sunshine_duration': (0, 86400),
        'cloud_cover_mean': (0, 100),
        'temperature_2m_mean': (-50, 60),
        'wind_speed_10m_mean': (0, 50),
        'rain_sum': (0, 500),
        'day_of_year': (1, 366),
    }
    
    # Validate numeric features
    for feature, (min_val, max_val) in FEATURE_BOUNDS.items():
        if feature in data:
            val = data.get(feature)
            try:
                val = float(val)
                if not (min_val <= val <= max_val):
                    errors.append(f"{feature} must be between {min_val} and {max_val}, got {val}")
            except (ValueError, TypeError):
                errors.append(f"{feature} must be a number, got {type(val).__name__}")
    
    # Validate date parameter if present
    parsed_date = None
    if 'date' in data and data['date']:
        try:
            parsed_date = pd.to_datetime(data['date'])
        except Exception:
            errors.append(f"Invalid date format: {data['date']}. Use YYYY-MM-DD.")

    # Validate season parameter (Dry vs Wet; Wet generates a warning because no training data exists for Wet season)
    season = data.get('season', 'Dry')
    if season not in ['Dry', 'Wet']:
        errors.append(f"season must be 'Dry' or 'Wet', got '{season}'")
    elif season == 'Wet':
        warning = "Model was trained exclusively on dry-season observations (Feb–May). Wet-season predictions carry higher uncertainty."
    
    # Validate is_weekend parameter
    is_weekend = data.get('is_weekend', False)
    if not isinstance(is_weekend, (bool, int)) or (isinstance(is_weekend, int) and is_weekend not in [0, 1]):
        errors.append(f"is_weekend must be boolean or 0/1, got {type(is_weekend).__name__}")
        valid_weekend = 0
    else:
        valid_weekend = int(is_weekend)
    
    # Derive day_of_year
    day_of_year = None
    if 'day_of_year' in data:
        try:
            day_of_year = int(data['day_of_year'])
        except (ValueError, TypeError):
            pass
    elif parsed_date is not None:
        day_of_year = int(parsed_date.dayofyear)

    validated_data = {
        'season': season,
        'is_weekend': valid_weekend,
        'date': str(data.get('date')) if 'date' in data else None,
        'day_of_year': day_of_year,
        'warning': warning,
    }
    
    return len(errors) == 0, errors, validated_data


def parse_date_column(df, col_name='date'):
    """
    Parse date column in DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame to process
        col_name (str): Name of date column
        
    Returns:
        pd.DataFrame: DataFrame with parsed dates
    """
    try:
        df[col_name] = pd.to_datetime(df[col_name])
        logger.info(f"Parsed {col_name} column successfully")
        return df
    except Exception as e:
        logger.error(f"Error parsing {col_name} column: {e}")
        raise


def calculate_kpis(solar_daily, weather_daily, daily_data):
    """
    Calculate Key Performance Indicators.
    
    Args:
        solar_daily (pd.DataFrame): Daily solar data
        weather_daily (pd.DataFrame): Daily weather data
        daily_data (pd.DataFrame): Merged daily data
        
    Returns:
        dict: KPI metrics
    """
    try:
        total_generation = float(solar_daily['generation_kwh'].sum())
        total_consumption = float(solar_daily['consumption_kwh'].sum())
        self_sufficiency = (total_generation / total_consumption * 100) if total_consumption > 0 else 0
        avg_temperature = float(weather_daily['temperature_2m_mean'].mean())
        
        # Calculate changes (comparing last 7 days with previous 7 days)
        if len(daily_data) >= 14:
            recent_7 = daily_data.tail(7)
            previous_7 = daily_data.iloc[-14:-7]
            generation_change = (recent_7['generation_kwh'].sum() - previous_7['generation_kwh'].sum()) / max(previous_7['generation_kwh'].sum(), 1)
            consumption_change = (recent_7['consumption_kwh'].sum() - previous_7['consumption_kwh'].sum()) / max(previous_7['consumption_kwh'].sum(), 1)
            self_sufficiency_change = ((recent_7['generation_kwh'].sum() / max(recent_7['consumption_kwh'].sum(), 1)) - 
                                      (previous_7['generation_kwh'].sum() / max(previous_7['consumption_kwh'].sum(), 1)))
            temp_change = recent_7['temperature_2m_mean'].mean() - previous_7['temperature_2m_mean'].mean()
        else:
            generation_change = 0
            consumption_change = 0
            self_sufficiency_change = 0
            temp_change = 0
        
        logger.info("KPIs calculated successfully")
        return {
            'total_generation': total_generation,
            'total_consumption': total_consumption,
            'generation_change': generation_change,
            'consumption_change': consumption_change,
            'self_sufficiency': self_sufficiency,
            'self_sufficiency_change': self_sufficiency_change,
            'avg_temperature': avg_temperature,
            'temperature_change': temp_change,
        }
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")
        raise


def prepare_prediction_row(data, season='Dry', is_weekend=0, date=None, day_of_year=None):
    """
    Prepare feature row for model prediction.
    Delegates to shared src.features.prepare_single_prediction_features.
    
    Args:
        data (dict): Input data
        season (str): Season ('Dry' or 'Wet')
        is_weekend (int): 0 or 1
        date (str, optional): Date string 'YYYY-MM-DD'
        day_of_year (int, optional): Day of year (1-366)
        
    Returns:
        dict: Feature row for model
    """
    from .features import prepare_single_prediction_features
    return prepare_single_prediction_features(
        data,
        season=season,
        is_weekend=is_weekend,
        date=date,
        day_of_year=day_of_year
    )


def filter_anomalies(df, exclude_dates=None):
    """
    Exclude documented anomalous days from a DataFrame and log exclusions.
    
    Args:
        df (pd.DataFrame): DataFrame containing a 'date' column
        exclude_dates (list, optional): List of date strings to exclude.
            Defaults to ANOMALY_DATES from src.config.
            
    Returns:
        pd.DataFrame: Cleaned DataFrame with anomalies filtered out.
    """
    from .config import ANOMALY_DATES, ANOMALY_REASONS
    if exclude_dates is None:
        exclude_dates = ANOMALY_DATES
        
    if df is None or len(df) == 0 or 'date' not in df.columns:
        return df
        
    df = df.copy()
    initial_len = len(df)
    
    # Identify excluded rows
    excluded_mask = df['date'].astype(str).isin(exclude_dates)
    anom_rows = df[excluded_mask]
    
    for _, row in anom_rows.iterrows():
        d = str(row['date'])
        reason = ANOMALY_REASONS.get(d, 'Configured anomaly')
        gen = row.get('generation_kwh', 'N/A')
        logger.info(f"Anomaly filter: excluded date {d} (generation: {gen} kWh) -> Reason: {reason}")
        
    filtered_df = df[~excluded_mask].reset_index(drop=True)
    excluded_count = initial_len - len(filtered_df)
    if excluded_count > 0:
        logger.info(f"Anomaly filter: excluded {excluded_count} rows ({initial_len} -> {len(filtered_df)})")
        
    return filtered_df


def align_hourly_timestamps(solar_hourly: pd.DataFrame, weather_hourly: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Standardize and align timestamps between fact_solar_hourly and fact_weather_hourly.
    
    Background & Documentation:
    - fact_solar_hourly.hour_ts contains timestamps with a '+08' timezone offset
      (e.g., '2026-02-02 00:00:00+08'), while its 'date' column reflects the UTC date ('2026-02-01').
      Converting '2026-02-02 00:00:00+08' to UTC yields '2026-02-01 16:00:00+00:00'.
    - fact_weather_hourly.hour_ts contains timezone-naive ISO string timestamps
      (e.g., '2026-02-01T00:00') from Open-Meteo.
      
    This function:
    1. Converts solar_hourly['hour_ts'] to UTC datetime.
    2. Treats weather_hourly['hour_ts'] as naive or UTC timestamps.
    3. Adds standardized 'hour_ts_utc' column to both DataFrames to allow clean merging.
    
    Args:
        solar_hourly: DataFrame with solar hourly records
        weather_hourly: DataFrame with weather hourly records
        
    Returns:
        tuple: (aligned_solar_hourly, aligned_weather_hourly)
    """
    solar_df = solar_hourly.copy()
    weather_df = weather_hourly.copy()
    
    if 'hour_ts' in solar_df.columns:
        # Parse timezone-aware +08 string and convert to UTC
        solar_df['hour_ts_utc'] = pd.to_datetime(solar_df['hour_ts'], utc=True)
        solar_df['date_utc'] = solar_df['hour_ts_utc'].dt.strftime('%Y-%m-%d')
        
    if 'hour_ts' in weather_df.columns:
        # Standardize weather hour_ts to UTC
        weather_df['hour_ts_utc'] = pd.to_datetime(weather_df['hour_ts'], utc=True)
        weather_df['date_utc'] = weather_df['hour_ts_utc'].dt.strftime('%Y-%m-%d')
        
    return solar_df, weather_df


