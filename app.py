from flask import Flask, request, jsonify, render_template
import joblib, numpy as np, pandas as pd
from appsql import log_prediction, get_prediction_history, get_prediction_stats
from datetime import datetime, timedelta
import os

app    = Flask(__name__)
model  = joblib.load('models/solar_generation_model.pkl')
FEATS  = joblib.load('models/feature_names.pkl')

# Data cache for CSV files
csv_cache = {}
csv_cache_time = {}
CACHE_DURATION = 300  # 5 minutes

def load_csv_data(filename):
    """Load CSV with caching to reduce I/O"""
    filepath = f'data/{filename}'
    now = datetime.now()
    
    # Check if cached data is still valid
    if filename in csv_cache and filename in csv_cache_time:
        if (now - csv_cache_time[filename]).total_seconds() < CACHE_DURATION:
            return csv_cache[filename]
    
    # Load fresh data
    df = pd.read_csv(filepath)
    csv_cache[filename] = df
    csv_cache_time[filename] = now
    return df

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
        print(f"Error in api_dashboard_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    # Build DataFrame in correct feature order
    row = {
        'shortwave_radiation_sum': data.get('shortwave_radiation_sum', 24.0),
        'sunshine_duration':       data.get('sunshine_duration', 38000),
        'cloud_cover_mean':        data.get('cloud_cover_mean', 30.0),
        'temperature_2m_mean':     data.get('temperature_2m_mean', 26.0),
        'wind_speed_10m_mean':     data.get('wind_speed_10m_mean', 18.0),
        'rain_sum':                data.get('rain_sum', 0.0),
        'season_enc':              1 if data.get('season','Dry')=='Wet' else 0,
        'is_weekend_enc':          int(data.get('is_weekend', False)),
        'sunshine_ratio':          data.get('sunshine_duration',38000) / 43200,
        'rad_clear':               data.get('shortwave_radiation_sum',24.0) *
                                   (1 - data.get('cloud_cover_mean',30)/100),
    }
    X = pd.DataFrame([row])[FEATS]
    pred = float(model.predict(X)[0])
    
    # Prepare data for database logging
    log_data = {
        'shortwave_radiation_sum': row['shortwave_radiation_sum'],
        'sunshine_duration': row['sunshine_duration'],
        'cloud_cover_mean': row['cloud_cover_mean'],
        'temperature_2m_mean': row['temperature_2m_mean'],
        'wind_speed_10m_mean': row['wind_speed_10m_mean'],
        'rain_sum': row['rain_sum'],
        'is_weekend_enc': row['is_weekend_enc'],
        'season': data.get('season','Dry'),
        'predicted_kwh': pred
    }
    
    # Log prediction to database
    log_prediction(log_data)
    
    return jsonify({'predicted_generation_kwh': round(pred, 3),
                    'status': 'Fraud' if pred < 5 else 'Normal' })

@app.route('/history', methods=['GET'])
def history():
    """Get prediction history - skip if database unavailable"""
    try:
        limit = request.args.get('limit', 100, type=int)
        records = get_prediction_history(limit)
        return jsonify({'predictions': records, 'count': len(records)})
    except Exception as e:
        print(f"Database error in history: {str(e)}")
        return jsonify({'predictions': [], 'count': 0})

@app.route('/stats', methods=['GET'])
def stats():
    """Get prediction statistics"""
    statistics = get_prediction_stats()
    return jsonify(statistics)

if __name__ == '__main__':
    app.run(debug=False, port=8000, host='0.0.0.0', threaded=True)

