
import mysql.connector
from mysql.connector import Error
import os

# MySQL connection configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'solar_analytics'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def init_db():
    """Initialize MySQL database with prediction_logs table"""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        
        # Connect to the database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create table if not exists
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ MySQL Database initialized")
        return True
    except Error as e:
        print(f"✗ Database init error: {e}")
        return False

def log_prediction(prediction_data):
    """
    Store prediction data into MySQL database.
    
    Args:
        prediction_data (dict): Dictionary containing prediction details
        
    Returns:
        bool: True if successful, False otherwise
    """
    init_db()  # Ensure database and table exist
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
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
            int(prediction_data.get('is_weekend', False)),
            prediction_data.get('season', 'Unknown'),
            prediction_data.get('predicted_kwh', 0)
        )
        
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Prediction logged: {prediction_data.get('predicted_kwh', 0):.2f} kWh")
        return True
        
    except Error as e:
        print(f"✗ Database error: {e}")
        return False


def get_prediction_history(limit=100):
    """
    Retrieve recent prediction history from database.
    
    Args:
        limit (int): Number of records to retrieve
        
    Returns:
        list: List of prediction records
    """
    init_db()  # Ensure database and table exist
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        sql = '''SELECT * FROM prediction_logs 
                 ORDER BY timestamp DESC LIMIT %s'''
        
        cursor.execute(sql, (limit,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return records
        
    except Error as e:
        print(f"✗ Database error: {e}")
        return []


def get_prediction_stats():
    """
    Get statistics about predictions.
    
    Returns:
        dict: Statistics including count, average, min, max, and predictions made today
    """
    init_db()  # Ensure database and table exist
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        sql = '''SELECT 
                    COUNT(*) as total_predictions,
                    AVG(predicted_kwh) as avg_generation,
                    MIN(predicted_kwh) as min_generation,
                    MAX(predicted_kwh) as max_generation,
                    MAX(timestamp) as last_prediction,
                    SUM(CASE WHEN DATE(timestamp) = CURDATE() THEN 1 ELSE 0 END) as predictions_made_today
                 FROM prediction_logs'''
        
        cursor.execute(sql)
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # Ensure predictions_made_today is 0 if NULL
        if stats and stats.get('predictions_made_today') is None:
            stats['predictions_made_today'] = 0
        
        return stats if stats else {}
        
    except Error as e:
        print(f"✗ Database error: {e}")
        return {}


def delete_old_predictions(days=30):
    """
    Delete predictions older than specified days.
    
    Args:
        days (int): Delete records older than this many days
        
    Returns:
        int: Number of records deleted
    """
    init_db()  # Ensure database and table exist
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        sql = '''DELETE FROM prediction_logs 
                 WHERE timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)'''
        
        cursor.execute(sql, (days,))
        conn.commit()
        deleted_count = cursor.rowcount
        cursor.close()
        conn.close()
        
        print(f"✓ Deleted {deleted_count} old predictions")
        return deleted_count
        
    except Error as e:
        print(f"✗ Database error: {e}")
        return 0
