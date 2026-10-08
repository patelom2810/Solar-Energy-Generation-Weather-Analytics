"""
Main application entry point - imports Flask app from src.app_main
"""
import os
from src.app_main import app

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 8000)),
        debug=False,
        threaded=True
    )
