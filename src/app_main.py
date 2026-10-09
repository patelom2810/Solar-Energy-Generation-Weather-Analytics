from flask import Flask, request, jsonify, render_template
import os
import joblib
import pandas as pd
import logging
import threading
from datetime import datetime
from .appsql import log_prediction, get_prediction_history, get_prediction_stats, init_db, init_connection_pool
from .api_docs import API_DOCS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app    = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)

# Load model with validation
try:
    model  = joblib.load('models/solar_generation_model.pkl')
    FEATS  = joblib.load('models/feature_names.pkl')
    logger.info("✓ Model and features loaded successfully")
except FileNotFoundError as e:
    logger.error(f"✗ Model file not found: {e}", exc_info=True)
    model = None
    FEATS = None
except Exception as e:
    logger.error(f"✗ Error loading model: {e}", exc_info=True)
    model = None
    FEATS = None

# Input validation bounds for prediction features
FEATURE_BOUNDS = {
    'shortwave_radiation_sum': (0, 500),      # W/m²
    'sunshine_duration': (0, 86400),           # seconds per day
    'cloud_cover_mean': (0, 100),              # percentage
    'temperature_2m_mean': (-50, 60),          # celsius
    'wind_speed_10m_mean': (0, 50),            # m/s
    'rain_sum': (0, 500),                      # mm
    'day_of_year': (1, 366),                   # calendar day of year
}

# Flag to track if startup was called
_startup_done = False

def _startup():
    """Initialize database and connection pool"""
    global _startup_done
    if _startup_done:
        return
    try:
        init_connection_pool()
        init_db()
        print("✓ App startup: Database and connection pool initialized")
        _startup_done = True
    except Exception as e:
        print(f"⚠ Startup warning: {e}")
        _startup_done = True

# Initialize on first request
@app.before_request
def before_request():
    """Execute startup on first request"""
    global _startup_done
    if not _startup_done:
        _startup()

from .features import compute_engineered_features, FEATURE_NAMES
from .models import compute_model_scores

# ── Cache model scores so we only compute once ──────────────────────────
_model_score_cache = None

def _compute_model_scores():
    global _model_score_cache
    if _model_score_cache is not None:
        return _model_score_cache
    try:
        solar = pd.read_csv('data/fact_solar_daily.csv')
        weather = pd.read_csv('data/fact_weather_daily.csv')
        feats_to_use = FEATS if FEATS is not None else FEATURE_NAMES
        _model_score_cache = compute_model_scores(model, feats_to_use, solar, weather)
    except Exception as e:
        _model_score_cache = {'error': str(e)}
    return _model_score_cache

# Data cache for CSV files with thread safety
csv_cache = {}
csv_cache_time = {}
csv_cache_lock = threading.Lock()  # Thread-safe lock for cache operations
CACHE_DURATION = 300  # 5 minutes

def load_csv_data(filename):
    """Load CSV with caching to reduce I/O - thread-safe"""
    filepath = f'data/{filename}'
    now = datetime.now()
    
    with csv_cache_lock:
        # Check if cached data is still valid
        if filename in csv_cache and filename in csv_cache_time:
            if (now - csv_cache_time[filename]).total_seconds() < CACHE_DURATION:
                logger.debug(f"Cache hit for {filename}")
                return csv_cache[filename]
        
        # Load fresh data
        try:
            df = pd.read_csv(filepath)
            if 'dim_date' in filename and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], format='mixed').dt.strftime('%Y-%m-%d')
                df = df.drop_duplicates(subset=['date']).reset_index(drop=True)
            csv_cache[filename] = df
            csv_cache_time[filename] = now
            logger.info(f"Loaded CSV: {filename} ({len(df)} rows)")
            return df
        except FileNotFoundError:
            logger.error(f"CSV file not found: {filepath}")
            raise
        except Exception as e:
            logger.error(f"Error loading CSV {filename}: {e}", exc_info=True)
            raise

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Render the modern analytics dashboard"""
    return render_template('dashboard.html')


@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API endpoint for dashboard data - combines CSV and prediction analytics"""
    try:
        print("Starting dashboard data load...")
        
        # Load CSV data with error handling
        try:
            solar_daily = load_csv_data('fact_solar_daily.csv')
            weather_daily = load_csv_data('fact_weather_daily.csv')
            solar_hourly = load_csv_data('fact_solar_hourly.csv')
        except Exception as csv_err:
            print(f"Error loading CSV: {str(csv_err)}")
            return jsonify({'error': f'CSV loading failed: {str(csv_err)}'}), 500
        
        # Convert date columns
        try:
            solar_daily['date'] = pd.to_datetime(solar_daily['date'])
            weather_daily['date'] = pd.to_datetime(weather_daily['date'])
            solar_hourly['date'] = pd.to_datetime(solar_hourly['date'])
        except Exception as dt_err:
            print(f"Error converting dates: {str(dt_err)}")
            return jsonify({'error': f'Date conversion failed: {str(dt_err)}'}), 500
        
        # Merge daily data
        try:
            daily_data = solar_daily.merge(weather_daily, on='date', how='left')
        except Exception as merge_err:
            print(f"Error merging data: {str(merge_err)}")
            return jsonify({'error': f'Data merge failed: {str(merge_err)}'}), 500
        
        # ===== KPI CALCULATIONS =====
        print("Calculating KPIs...")
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
        except Exception as kpi_err:
            print(f"Error calculating KPIs: {str(kpi_err)}")
            return jsonify({'error': f'KPI calculation failed: {str(kpi_err)}'}), 500
        
        # Prediction stats - handle database errors gracefully
        print("Fetching prediction stats...")
        total_predictions = 0
        predictions_made_today = 0
        try:
            prediction_stats = get_prediction_stats()
            total_predictions = int(prediction_stats.get('total_predictions', 0) or 0)
            predictions_made_today = int(prediction_stats.get('predictions_made_today', 0) or 0)
        except Exception as db_err:
            print(f"Warning: Could not fetch prediction stats: {str(db_err)}")
            total_predictions = 0
            predictions_made_today = 0
        
        # ===== CHART DATA GENERATION =====
        print("Generating chart data...")
        
        # 1. Daily Generation vs Consumption (last 30 days)
        try:
            daily_chart_data = []
            for _, row in solar_daily.tail(30).iterrows():
                daily_chart_data.append({
                    'date': row['date'].strftime('%m-%d'),
                    'generation_kwh': float(row['generation_kwh']),
                    'consumption_kwh': float(row['consumption_kwh'])
                })
        except Exception as e:
            print(f"Error creating daily chart data: {str(e)}")
            daily_chart_data = []
        
        # 2. Monthly aggregation
        try:
            solar_daily_copy = solar_daily.copy()
            solar_daily_copy['month'] = solar_daily_copy['date'].dt.to_period('M')
            monthly_data = solar_daily_copy.groupby('month').agg({
                'generation_kwh': 'sum',
                'consumption_kwh': 'sum'
            }).reset_index()
            
            monthly_chart_data = []
            for _, row in monthly_data.tail(12).iterrows():
                monthly_chart_data.append({
                    'month': str(row['month']),
                    'generation_kwh': float(row['generation_kwh']),
                    'consumption_kwh': float(row['consumption_kwh'])
                })
        except Exception as e:
            print(f"Error creating monthly chart data: {str(e)}")
            monthly_chart_data = []
        
        # 3. Radiation vs Generation (scatter)
        try:
            radiation_data = []
            for _, row in daily_data.tail(30).iterrows():
                if pd.notna(row.get('shortwave_radiation_sum')) and pd.notna(row.get('generation_kwh')):
                    radiation_data.append({
                        'radiation': float(row['shortwave_radiation_sum']),
                        'generation_kwh': float(row['generation_kwh'])
                    })
        except Exception as e:
            print(f"Error creating radiation chart data: {str(e)}")
            radiation_data = []
        
        # 4. Weather Distribution (by weather code)
        try:
            weather_code_counts = weather_daily['weather_code'].value_counts().to_dict()
            weather_distribution = {f'Code {int(k)}': int(v) for k, v in weather_code_counts.items()}
        except Exception as e:
            print(f"Error creating weather distribution: {str(e)}")
            weather_distribution = {}
        
        # 5. Hourly Generation Pattern (last 24 hours)
        try:
            hourly_data = []
            if len(solar_hourly) > 0:
                solar_hourly_copy = solar_hourly.copy()
                solar_hourly_copy['hour'] = pd.to_datetime(solar_hourly_copy['hour_ts']).dt.strftime('%H:%M')
                hourly_agg = solar_hourly_copy.groupby('hour').agg({
                    'generation_kwh': 'mean'
                }).reset_index()
                
                for _, row in hourly_agg.tail(24).iterrows():
                    hourly_data.append({
                        'hour': row['hour'],
                        'generation_kwh': float(row['generation_kwh'])
                    })
        except Exception as e:
            print(f"Error creating hourly chart data: {str(e)}")
            hourly_data = []
        
        print("Dashboard data ready!")
        
        # ===== RETURN RESPONSE =====
        return jsonify({
            # KPIs
            'total_generation': total_generation,
            'total_consumption': total_consumption,
            'generation_change': generation_change,
            'consumption_change': consumption_change,
            'self_sufficiency': self_sufficiency,
            'self_sufficiency_change': self_sufficiency_change,
            'avg_temperature': avg_temperature,
            'temperature_change': temp_change,
            'total_predictions': total_predictions,
            'predictions_made_today': predictions_made_today,
            
            # Chart data
            'daily_data': daily_chart_data,
            'monthly_data': monthly_chart_data,
            'radiation_data': radiation_data,
            'weather_distribution': weather_distribution,
            'hourly_data': hourly_data
        })
    
    except Exception as e:
        logger.error(f"Error in api_dashboard_data: {str(e)}", exc_info=True)
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/predict', methods=['POST'])
def predict():
    """Predict solar generation with comprehensive input validation"""
    
    # Check if model is loaded
    if model is None or FEATS is None:
        logger.error("Model not available for prediction")
        return jsonify({'error': 'Model not loaded or initialization failed'}), 503
    
    try:
        data = request.get_json()
        if not data:
            logger.warning("Empty JSON payload received in /predict")
            return jsonify({'error': 'Invalid JSON payload'}), 400
        
        # Validate input bounds and parameters using shared utility
        from .utils import validate_prediction_input, prepare_prediction_row
        is_valid, errors, validated = validate_prediction_input(data)
        if not is_valid:
            logger.warning(f"Validation failed for predict: {errors}")
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        season = validated['season']
        is_weekend = validated['is_weekend']
        date_param = validated.get('date')
        day_of_year = validated.get('day_of_year')
        warning_msg = validated.get('warning')
        
        # Build feature dictionary using shared feature utility
        row = prepare_prediction_row(
            data,
            season=season,
            is_weekend=is_weekend,
            date=date_param,
            day_of_year=day_of_year
        )
        X = pd.DataFrame([row])[FEATS]
        pred = max(0.0, float(model.predict(X)[0]))
        
        # Prepare data for database logging
        log_data = {
            'shortwave_radiation_sum': row['shortwave_radiation_sum'],
            'sunshine_duration': row['sunshine_duration'],
            'cloud_cover_mean': row['cloud_cover_mean'],
            'temperature_2m_mean': row['temperature_2m_mean'],
            'wind_speed_10m_mean': row['wind_speed_10m_mean'],
            'rain_sum': row['rain_sum'],
            'is_weekend_enc': row['is_weekend_enc'],
            'season': season,
            'predicted_kwh': pred
        }
        
        # Log prediction to database
        success = log_prediction(log_data)
        if not success:
            logger.warning(f"Failed to log prediction to database, but prediction was generated: {pred:.3f} kWh")
        
        row_doy = int(row['day_of_year'])
        if (row_doy < 32 or row_doy > 122) and (not warning_msg or "extrapolated" not in warning_msg):
            extrap_warn = "Date is outside historical training window (day_of_year below 32 or above 122); the day-of-year trend is extrapolated."
            warning_msg = f"{warning_msg} {extrap_warn}".strip() if warning_msg else extrap_warn

        logger.info(f"Prediction generated: {pred:.3f} kWh for day_of_year={row_doy}, season={season}")
        response_payload = {
            'predicted_generation_kwh': round(pred, 3),
            'day_of_year': row_doy,
            'status': 'Low' if pred < 5 else 'Normal',
            'warning': warning_msg if warning_msg else None
        }
        return jsonify(response_payload)
    
    except Exception as e:
        logger.error(f"Error in predict endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/history', methods=['GET'])
def history():
    """Get prediction history - gracefully handles database unavailability"""
    try:
        limit = request.args.get('limit', 100, type=int)
        if limit < 1 or limit > 1000:
            limit = 100  # Default if out of range
        
        records = get_prediction_history(limit)
        logger.info(f"Retrieved {len(records)} prediction history records (limit={limit})")
        return jsonify({'predictions': records, 'count': len(records)})
    except Exception as e:
        logger.error(f"Error in history endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e), 'predictions': [], 'count': 0}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get prediction statistics"""
    try:
        statistics = get_prediction_stats()
        logger.info("Retrieved prediction statistics")
        return jsonify(statistics if statistics else {'error': 'No statistics available'})
    except Exception as e:
        logger.error(f"Error in stats endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Check model
        if model is None:
            return jsonify({'status': 'unhealthy', 'reason': 'Model not loaded'}), 500
        
        # Check database connection
        try:
            stats = get_prediction_stats()
            db_status = 'connected'
        except:
            db_status = 'disconnected'
            
        # Check ETL status if exists
        last_etl_run = None
        etl_status_path = os.path.join(BASE_DIR, 'data', 'etl_status.json')
        if os.path.exists(etl_status_path):
            try:
                import json
                with open(etl_status_path, 'r') as f:
                    last_etl_run = json.load(f)
            except Exception as e_etl:
                last_etl_run = {'error': str(e_etl)}
        
        logger.info(f"Health check: model=loaded, database={db_status}")
        return jsonify({
            'status': 'healthy',
            'model': 'loaded',
            'database': db_status,
            'last_etl_run': last_etl_run,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}", exc_info=True)
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/docs', methods=['GET'])
def api_docs():
    """Return API documentation in OpenAPI format"""
    try:
        logger.info("API documentation requested")
        return jsonify(API_DOCS)
    except Exception as e:
        logger.error(f"Error returning API docs: {str(e)}")
        return jsonify({'error': 'Failed to load API documentation'}), 500

@app.route('/api/model-score')
def api_model_score():
    """Return model performance metrics and feature importances"""
    try:
        return jsonify(_compute_model_scores())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, port=8000, host='0.0.0.0', threaded=True)

