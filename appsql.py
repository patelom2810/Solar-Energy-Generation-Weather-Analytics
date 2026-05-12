import mysql.connector
from mysql.connector import Error, pooling
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL connection configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'solar_analytics'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# Connection pool configuration
db_pool = None

def init_connection_pool():
    """Initialize MySQL connection pool for better performance"""
    global db_pool
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name='solar_pool',
            pool_size=5,
            pool_reset_session=True,
            **DB_CONFIG
        )
        logger.info("✓ Connection pool initialized")
        return True
    except Error as e:
        logger.error(f"✗ Connection pool error: {e}", exc_info=True)
        return False

def init_db():
    """Initialize MySQL database with prediction_logs table"""
    global db_pool
    if db_pool is None:
        init_connection_pool()
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        conn.close()
        
        # Connect to the database
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        
        # Create table if not exists with indexes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                shortwave_radiation FLOAT,
                sunshine_duration FLOAT,
                cloud_cover FLOAT,
                temperature_2m FLOAT,
                wind_speed_10m FLOAT,
                rain FLOAT,
                is_weekend INT,
                season VARCHAR(50),
                predicted_kwh FLOAT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_timestamp (timestamp),
                INDEX idx_season (season),
                INDEX idx_predictions_today (timestamp, is_weekend)
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("✓ MySQL Database initialized")
        return True
    except Error as e:
        logger.error(f"✗ Database init error: {e}", exc_info=True)
        return False

def log_prediction(prediction_data):
    """
    Store prediction data into MySQL database using connection pool.
    
    Args:
        prediction_data (dict): Dictionary containing prediction details
        
    Returns:
        bool: True if successful, False otherwise
    """
    global db_pool
    if db_pool is None:
        if not init_connection_pool():
            logger.error("Connection pool not available for log_prediction")
            return False
    
    conn = None
    cursor = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        
        sql = '''INSERT INTO prediction_logs
                 (shortwave_radiation, sunshine_duration, cloud_cover,
                  temperature_2m, wind_speed_10m, rain,
                  is_weekend, season, predicted_kwh)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        
        values = (
            prediction_data.get('shortwave_radiation_sum', 0),
            prediction_data.get('sunshine_duration', 0),
            prediction_data.get('cloud_cover_mean', 0),
            prediction_data.get('temperature_2m_mean', 0),
            prediction_data.get('wind_speed_10m_mean', 0),
            prediction_data.get('rain_sum', 0),
            int(prediction_data.get('is_weekend_enc', 0)),
            prediction_data.get('season', 'Unknown'),
            prediction_data.get('predicted_kwh', 0)
        )
        
        cursor.execute(sql, values)
        conn.commit()
        
        logger.info(f"✓ Prediction logged: {prediction_data.get('predicted_kwh', 0):.2f} kWh")
        return True
        
    except Error as e:
        logger.error(f"✗ Database error in log_prediction: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


def get_prediction_history(limit=100):
    """
    Retrieve recent prediction history from database using connection pool.
    
    Args:
        limit (int): Number of records to retrieve
        
    Returns:
        list: List of prediction records
    """
    global db_pool
    if db_pool is None:
        if not init_connection_pool():
            logger.error("Connection pool not available for get_prediction_history")
            return []
    
    conn = None
    cursor = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = '''SELECT * FROM prediction_logs 
                 ORDER BY timestamp DESC LIMIT %s'''
        
        cursor.execute(sql, (limit,))
        records = cursor.fetchall()
        logger.info(f"✓ Retrieved {len(records)} prediction records")
        return records
        
    except Error as e:
        logger.error(f"✗ Database error in get_prediction_history: {e}", exc_info=True)
        return []
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


def get_prediction_stats():
    """
    Get statistics about predictions using connection pool.
    
    Returns:
        dict: Statistics including count, average, min, max, and predictions made today
    """
    global db_pool
    if db_pool is None:
        if not init_connection_pool():
            logger.error("Connection pool not available for get_prediction_stats")
            return {}
    
    conn = None
    cursor = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = '''SELECT 
                    COUNT(*) as total_predictions,
                    AVG(predicted_kwh) as avg_generation,
                    MIN(predicted_kwh) as min_generation,
                    MAX(predicted_kwh) as max_generation,
                    MAX(timestamp) as last_prediction,
                    COALESCE(SUM(CASE WHEN DATE(timestamp) = CURDATE() THEN 1 ELSE 0 END), 0) as predictions_made_today
                 FROM prediction_logs'''
        
        cursor.execute(sql)
        stats = cursor.fetchone()
        
        logger.info("✓ Retrieved prediction statistics")
        return stats if stats else {}
        
    except Error as e:
        logger.error(f"✗ Database error in get_prediction_stats: {e}", exc_info=True)
        return {}
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


def delete_old_predictions(days=30):
    """
    Delete predictions older than specified days using connection pool.
    
    Args:
        days (int): Delete records older than this many days
        
    Returns:
        int: Number of records deleted
    """
    global db_pool
    if db_pool is None:
        init_db()  # Ensure database and connection pool exist
    
    conn = None
    cursor = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        
        sql = '''DELETE FROM prediction_logs 
                 WHERE timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)'''
        
        cursor.execute(sql, (days,))
        conn.commit()
        deleted_count = cursor.rowcount
        
        logger.info(f"✓ Deleted {deleted_count} old predictions (>{days} days)")
        return deleted_count
        
    except Error as e:
        logger.error(f"✗ Database error in delete_old_predictions: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return 0
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
