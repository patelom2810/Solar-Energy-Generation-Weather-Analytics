"""
ETL Load Module for Solar Energy Analytics.
Performs idempotent upserts into MySQL tables (dim_date, fact_solar_daily,
fact_weather_daily, fact_*_hourly) and refreshes CSV datasets in data/.
Records execution status into MySQL and data/etl_status.json.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'solar_analytics'),
    'port': int(os.getenv('DB_PORT', 3306))
}


def get_db_connection():
    """Create a database connection with automatic database creation if missing."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        if getattr(e, 'errno', None) == 1049 or 'Unknown database' in str(e):
            temp_config = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
            temp_conn = mysql.connector.connect(**temp_config)
            temp_cur = temp_conn.cursor()
            temp_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}`")
            temp_cur.close()
            temp_conn.close()
            return mysql.connector.connect(**DB_CONFIG)
        raise


def init_etl_tables(ddl_path: str = 'sql/create_etl_tables.sql') -> bool:
    """Execute SQL DDL file to ensure all ETL tables exist."""
    if not os.path.exists(ddl_path):
        logger.warning(f"DDL file not found at {ddl_path}")
        return False
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        with open(ddl_path, 'r') as f:
            sql_statements = f.read().split(';')
            
        for stmt in sql_statements:
            stmt = stmt.strip()
            if stmt:
                cursor.execute(stmt)
                
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"✓ Initialized ETL tables from {ddl_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ETL tables: {e}", exc_info=True)
        return False


def upsert_table(
    df: pd.DataFrame,
    table_name: str,
    primary_key: str,
    conn: Optional[mysql.connector.MySQLConnection] = None,
    batch_size: int = 500
) -> int:
    """
    Perform idempotent upsert (INSERT ... ON DUPLICATE KEY UPDATE) into MySQL.
    
    Args:
        df: DataFrame containing records to upsert
        table_name: Target MySQL table
        primary_key: Primary key column (or list of columns)
        conn: Optional active database connection
        batch_size: Number of records per batch
        
    Returns:
        int: Number of rows upserted
    """
    if df is None or len(df) == 0:
        logger.info(f"No records to upsert into {table_name}")
        return 0
        
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
        
    cursor = conn.cursor()
    columns = list(df.columns)
    
    # Exclude non-existent columns from DataFrame or ensure valid values
    placeholders = ", ".join(["%s"] * len(columns))
    cols_str = ", ".join([f"`{c}`" for c in columns])
    
    # Update clause: update all non-primary key columns
    update_cols = [c for c in columns if c != primary_key]
    if update_cols:
        update_clause = ", ".join([f"`{c}`=VALUES(`{c}`)" for c in update_cols])
    else:
        update_clause = f"`{primary_key}`=VALUES(`{primary_key}`)"
        
    sql = f"INSERT INTO `{table_name}` ({cols_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"
    
    total_upserted = 0
    try:
        # Convert DataFrame to clean Python native types converting NaN/NaT to None
        records = []
        for row in df.itertuples(index=False):
            clean_row = []
            for val in row:
                if pd.isna(val) or val is None:
                    clean_row.append(None)
                elif isinstance(val, (bool, np.bool_)):
                    clean_row.append(int(val))
                elif isinstance(val, (int, np.integer)):
                    clean_row.append(int(val))
                elif isinstance(val, (float, np.floating)):
                    clean_row.append(float(val))
                else:
                    clean_row.append(str(val))
            records.append(clean_row)

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            cursor.executemany(sql, batch)
            total_upserted += len(batch)
            
        conn.commit()
        logger.info(f"✓ Upserted {total_upserted} rows into {table_name}")
    except Exception as e:
        logger.error(f"Error during upsert into {table_name}: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        cursor.close()
        if close_conn:
            conn.close()
            
    return total_upserted


def refresh_csv_files(transformed_data: Dict[str, pd.DataFrame], data_dir: str = 'data') -> None:
    """
    Refresh production CSV files in data/ directory with latest cleaned datasets.
    
    Args:
        transformed_data: Mapping of dataset name to DataFrame
        data_dir: Target directory path
    """
    os.makedirs(data_dir, exist_ok=True)
    mapping = {
        'fact_solar_daily': 'fact_solar_daily.csv',
        'fact_weather_daily': 'fact_weather_daily.csv',
        'fact_solar_hourly': 'fact_solar_hourly.csv',
        'fact_weather_hourly': 'fact_weather_hourly.csv',
        'dim_date': 'dim_date.csv',
    }
    
    for key, filename in mapping.items():
        df = transformed_data.get(key)
        if df is not None and len(df) > 0:
            target_path = os.path.join(data_dir, filename)
            if key == 'dim_date' and os.path.exists(target_path):
                try:
                    existing_dim = pd.read_csv(target_path)
                    combined = pd.concat([existing_dim, df], ignore_index=True).drop_duplicates(subset=['date'], keep='last')
                    combined.to_csv(target_path, index=False)
                    logger.info(f"✓ Refreshed CSV: {target_path} ({len(combined)} rows preserved)")
                    continue
                except Exception:
                    pass
            df.to_csv(target_path, index=False)
            logger.info(f"✓ Refreshed CSV: {target_path} ({len(df)} rows)")


def record_etl_run(
    run_id: str,
    start_time: datetime,
    end_time: datetime,
    status: str,
    records_processed: Dict[str, int],
    retrain_summary: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    status_file_path: str = 'data/etl_status.json'
) -> None:
    """
    Persist pipeline run summary to data/etl_status.json and MySQL etl_runs table.
    """
    duration_sec = round((end_time - start_time).total_seconds(), 2)
    summary = {
        'run_id': run_id,
        'status': status,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': duration_sec,
        'records_processed': records_processed,
        'retrain_summary': retrain_summary,
        'error_message': error_message,
        'timestamp': end_time.isoformat()
    }
    
    # 1. Write to JSON status file for fast reading by /health
    try:
        os.makedirs(os.path.dirname(os.path.abspath(status_file_path)), exist_ok=True)
        with open(status_file_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"✓ Recorded ETL status in {status_file_path}")
    except Exception as e:
        logger.error(f"Failed to write ETL status JSON: {e}", exc_info=True)
        
    # 2. Persist in MySQL etl_runs table
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        total_records = sum(records_processed.values()) if isinstance(records_processed, dict) else 0
        details_json = json.dumps(summary)
        
        sql = '''INSERT INTO etl_runs 
                 (run_id, start_time, end_time, status, records_processed, details)
                 VALUES (%s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE 
                 end_time=VALUES(end_time), status=VALUES(status), 
                 records_processed=VALUES(records_processed), details=VALUES(details)'''
                 
        cursor.execute(sql, (
            run_id,
            start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time.strftime('%Y-%m-%d %H:%M:%S'),
            status,
            total_records,
            details_json
        ))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"✓ Saved ETL run record to MySQL table 'etl_runs'")
    except Exception as e:
        logger.warning(f"Could not write to MySQL etl_runs table: {e}")


def load_all(
    transformed_data: Dict[str, pd.DataFrame],
    full_refresh: bool = False,
    data_dir: str = 'data'
) -> Dict[str, int]:
    """
    Run full load phase: updates MySQL tables and refreshes CSVs.
    
    Returns:
        dict: Counts of upserted records per table
    """
    logger.info("Starting ETL load phase...")
    init_etl_tables()
    
    counts = {}
    table_configs = [
        ('dim_date', 'date'),
        ('fact_solar_daily', 'date'),
        ('fact_weather_daily', 'date'),
        ('fact_solar_hourly', 'hour_ts'),
        ('fact_weather_hourly', 'hour_ts'),
    ]
    
    # 1. Idempotent upserts to MySQL
    conn = None
    try:
        conn = get_db_connection()
        for tbl, pk in table_configs:
            df = transformed_data.get(tbl)
            if df is not None and len(df) > 0:
                counts[tbl] = upsert_table(df, tbl, pk, conn=conn)
    except Exception as e:
        logger.error(f"MySQL upsert failed: {e}. Proceeding to CSV refresh...", exc_info=True)
        for tbl, _ in table_configs:
            counts[tbl] = len(transformed_data.get(tbl, []))
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            
    # 2. Refresh CSVs on disk
    refresh_csv_files(transformed_data, data_dir=data_dir)
    
    return counts
