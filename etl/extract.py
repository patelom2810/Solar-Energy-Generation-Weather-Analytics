"""
ETL Extraction Module for Solar Energy Analytics.
Extracts meteorological data from Open-Meteo API (with retries and timeouts)
and ingests solar generation data drops from data/raw/ CSV files.
"""
import os
import glob
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime, date, timedelta
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Default configurations from environment
DEFAULT_LATITUDE = float(os.getenv('ETL_LATITUDE', '28.6139'))
DEFAULT_LONGITUDE = float(os.getenv('ETL_LONGITUDE', '77.2090'))
DEFAULT_TIMEOUT = int(os.getenv('ETL_TIMEOUT', '20'))
MAX_RETRIES = int(os.getenv('ETL_MAX_RETRIES', '3'))


def get_requests_session(retries: int = MAX_RETRIES, backoff_factor: float = 0.5) -> requests.Session:
    """Create a requests session with automatic retries on transient errors."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_open_meteo_weather(
    start_date: str,
    end_date: str,
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    session: Optional[requests.Session] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch daily and hourly meteorological data from Open-Meteo API.
    
    Args:
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        session: Optional pre-configured requests session
        
    Returns:
        tuple: (daily_weather_df, hourly_weather_df)
    """
    logger.info(f"Extracting weather from Open-Meteo ({start_date} to {end_date}) at ({latitude}, {longitude})")
    
    daily_vars = (
        'shortwave_radiation_sum,sunshine_duration,daylight_duration,'
        'cloud_cover_mean,temperature_2m_mean,relative_humidity_2m_mean,'
        'rain_sum,wind_speed_10m_mean,weather_code'
    )
    hourly_vars = (
        'relative_humidity_2m,wind_speed_10m,is_day,'
        'sunshine_duration,temperature_2m,cloud_cover,rain,weather_code'
    )
    
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': end_date,
        'daily': daily_vars,
        'hourly': hourly_vars,
        'timezone': 'auto'
    }
    
    sess = session or get_requests_session()
    
    # Try archive API first (for past dates), fallback to forecast API (for recent/current)
    endpoints = [
        "https://archive-api.open-meteo.com/v1/archive",
        "https://api.open-meteo.com/v1/forecast"
    ]
    
    response_data = None
    last_error = None
    
    for endpoint in endpoints:
        try:
            logger.debug(f"Requesting Open-Meteo endpoint: {endpoint}")
            resp = sess.get(endpoint, params=params, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                response_data = resp.json()
                logger.info(f"✓ Open-Meteo response received from {endpoint}")
                break
            else:
                last_error = f"Status {resp.status_code}: {resp.text}"
                logger.warning(f"Endpoint {endpoint} returned status {resp.status_code}, trying fallback...")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Request failed for {endpoint}: {e}")
            
    if response_data is None:
        raise RuntimeError(f"Failed to fetch weather from Open-Meteo: {last_error}")
        
    # Parse daily records
    daily_raw = response_data.get('daily', {})
    if 'time' in daily_raw and len(daily_raw['time']) > 0:
        df_daily = pd.DataFrame(daily_raw)
        df_daily.rename(columns={'time': 'date'}, inplace=True)
    else:
        df_daily = pd.DataFrame(columns=[
            'date', 'shortwave_radiation_sum', 'sunshine_duration', 'daylight_duration',
            'cloud_cover_mean', 'temperature_2m_mean', 'relative_humidity_2m_mean',
            'rain_sum', 'wind_speed_10m_mean', 'weather_code'
        ])
        
    # Parse hourly records
    hourly_raw = response_data.get('hourly', {})
    if 'time' in hourly_raw and len(hourly_raw['time']) > 0:
        df_hourly = pd.DataFrame(hourly_raw)
        df_hourly.rename(columns={'time': 'hour_ts'}, inplace=True)
        # Add date column extracted from hour_ts
        df_hourly['date'] = pd.to_datetime(df_hourly['hour_ts']).dt.strftime('%Y-%m-%d')
    else:
        df_hourly = pd.DataFrame(columns=[
            'date', 'hour_ts', 'relative_humidity_2m', 'wind_speed_10m',
            'is_day', 'sunshine_duration', 'temperature_2m', 'cloud_cover',
            'rain', 'weather_code'
        ])
        
    logger.info(f"Extracted {len(df_daily)} daily weather records and {len(df_hourly)} hourly weather records")
    return df_daily, df_hourly


def read_solar_raw_drops(raw_dir: str = 'data/raw') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read solar generation CSV drop files from data/raw/.
    
    Supports:
    - Daily files (with 'generation_kwh' and 'date')
    - Hourly files (with 'hour_ts' and 'generation_kwh')
    
    If no files exist in raw_dir, seamlessly loads existing baseline from data/.
    
    Returns:
        tuple: (df_solar_daily, df_solar_hourly)
    """
    logger.info(f"Checking for raw solar data drops in {raw_dir}...")
    
    daily_frames = []
    hourly_frames = []
    
    if os.path.exists(raw_dir):
        csv_files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
        for fpath in csv_files:
            try:
                df = pd.read_csv(fpath)
                cols = set(df.columns)
                if 'hour_ts' in cols:
                    hourly_frames.append(df)
                    logger.info(f"Loaded raw hourly solar drop: {fpath} ({len(df)} rows)")
                elif 'date' in cols and ('generation_kwh' in cols or 'consumption_kwh' in cols):
                    daily_frames.append(df)
                    logger.info(f"Loaded raw daily solar drop: {fpath} ({len(df)} rows)")
            except Exception as e:
                logger.error(f"Error reading raw CSV {fpath}: {e}", exc_info=True)
                
    # If no raw drops loaded, fall back to existing baseline in data/
    if not daily_frames:
        fallback_daily = os.path.join('data', 'fact_solar_daily.csv')
        if os.path.exists(fallback_daily):
            logger.info(f"Using baseline daily solar dataset from {fallback_daily}")
            daily_frames.append(pd.read_csv(fallback_daily))
            
    if not hourly_frames:
        fallback_hourly = os.path.join('data', 'fact_solar_hourly.csv')
        if os.path.exists(fallback_hourly):
            logger.info(f"Using baseline hourly solar dataset from {fallback_hourly}")
            hourly_frames.append(pd.read_csv(fallback_hourly))
            
    df_solar_daily = pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame(columns=[
        'date', 'generation_kwh', 'consumption_kwh', 'grid_feed_in_kwh',
        'grid_purchase_kwh', 'charge_kwh', 'discharge_kwh'
    ])
    
    df_solar_hourly = pd.concat(hourly_frames, ignore_index=True) if hourly_frames else pd.DataFrame(columns=[
        'date', 'hour_ts', 'generation_kwh', 'consumption_kwh', 'grid_feed_in_kwh',
        'grid_purchase_kwh', 'charge_kwh', 'discharge_kwh', 'battery_soc_eoh'
    ])
    
    logger.info(f"Extracted {len(df_solar_daily)} solar daily rows and {len(df_solar_hourly)} solar hourly rows")
    return df_solar_daily, df_solar_hourly


def extract_all(
    start_date: str,
    end_date: str,
    raw_dir: str = 'data/raw',
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    session: Optional[requests.Session] = None
) -> Dict[str, pd.DataFrame]:
    """
    Run full extraction phase.
    
    Returns:
        dict: Mapping of dataset name to extracted DataFrame.
    """
    df_wd, df_wh = fetch_open_meteo_weather(
        start_date=start_date,
        end_date=end_date,
        latitude=latitude,
        longitude=longitude,
        session=session
    )
    df_sd, df_sh = read_solar_raw_drops(raw_dir=raw_dir)
    
    return {
        'weather_daily': df_wd,
        'weather_hourly': df_wh,
        'solar_daily': df_sd,
        'solar_hourly': df_sh
    }
