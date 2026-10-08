"""
ETL Pipeline for Solar Energy Generation & Weather Analytics.
Extracts meteorological data from Open-Meteo API and solar logs from data/raw/,
transforms & validates features, and idempotently loads into MySQL & CSVs.
"""

from .extract import extract_all, fetch_open_meteo_weather, read_solar_raw_drops
from .transform import transform_all, build_dim_date, clean_and_validate
from .load import load_all, init_etl_tables, upsert_table
from .retrain import evaluate_and_retrain_model

__all__ = [
    'extract_all',
    'fetch_open_meteo_weather',
    'read_solar_raw_drops',
    'transform_all',
    'build_dim_date',
    'clean_and_validate',
    'load_all',
    'init_etl_tables',
    'upsert_table',
    'evaluate_and_retrain_model',
]
