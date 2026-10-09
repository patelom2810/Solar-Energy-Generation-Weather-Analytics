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

# ── Anomaly Filtering Configuration ─────────────────────────────────────────
# Documented anomalous days identified during repository audit:
# - '2026-02-01': 0.644 kWh, partial first recording day (8 hours starting 16:00 UTC).
# - '2026-03-31': 1.406 kWh, severe outage / grid loss (missing grid_purchase_kwh).
ANOMALY_DATES = [
    '2026-02-01',
    '2026-03-31',
]

ANOMALY_REASONS = {
    '2026-02-01': 'Partial first day of data collection (0.644 kWh across 8 evening UTC hours; inverter activated late).',
    '2026-03-31': 'System outage / grid disconnect (1.406 kWh, missing grid_purchase_kwh, abnormal curtailment).'
}

EXCLUDE_ANOMALIES_DEFAULT = True
