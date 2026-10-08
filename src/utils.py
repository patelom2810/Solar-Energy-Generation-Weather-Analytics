"""
Utility functions for Solar Analytics application
"""
import logging
import pandas as pd
from datetime import datetime

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
    
    # Feature bounds for numeric validation
    FEATURE_BOUNDS = {
        'shortwave_radiation_sum': (0, 500),
        'sunshine_duration': (0, 86400),
        'cloud_cover_mean': (0, 100),
        'temperature_2m_mean': (-50, 60),
        'wind_speed_10m_mean': (0, 50),
        'rain_sum': (0, 500),
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
    
    # Validate season parameter
    season = data.get('season', 'Dry')
    if season not in ['Dry', 'Wet']:
        errors.append(f"season must be 'Dry' or 'Wet', got '{season}'")
    
    # Validate is_weekend parameter
    is_weekend = data.get('is_weekend', False)
    if not isinstance(is_weekend, (bool, int)) or (isinstance(is_weekend, int) and is_weekend not in [0, 1]):
        errors.append(f"is_weekend must be boolean or 0/1, got {type(is_weekend).__name__}")
        valid_weekend = 0
    else:
        valid_weekend = int(is_weekend)
    
    validated_data = {
        'season': season,
        'is_weekend': valid_weekend
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


def prepare_prediction_row(data, season, is_weekend):
    """
    Prepare feature row for model prediction.
    Delegates to shared src.features.prepare_single_prediction_features.
    
    Args:
        data (dict): Input data
        season (str): Season ('Dry' or 'Wet')
        is_weekend (int): 0 or 1
        
    Returns:
        dict: Feature row for model
    """
    from .features import prepare_single_prediction_features
    return prepare_single_prediction_features(data, season=season, is_weekend=is_weekend)
