import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'solar_analytics'),
    'port':     int(os.getenv('DB_PORT', 3306)),
}
