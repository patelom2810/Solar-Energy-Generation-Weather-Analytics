import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration is defined in appsql.py
# This file can be used for other application config if needed

FLASK_CONFIG = {
    'debug': os.getenv('FLASK_ENV', 'development') == 'development',
    'port': int(os.getenv('FLASK_PORT', 8000)),
    'host': os.getenv('FLASK_HOST', '0.0.0.0'),
}
