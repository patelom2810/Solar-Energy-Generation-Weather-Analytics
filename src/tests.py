"""
Unit and integration tests for Solar Analytics
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from .utils import (
    validate_prediction_input,
    prepare_prediction_row,
    calculate_kpis,
    filter_anomalies,
    align_hourly_timestamps,
)
from .config import ANOMALY_DATES, ANOMALY_REASONS
from .features import (
    FEATURE_NAMES,
    FEATURE_SET_A,
    FEATURE_SET_B,
    FEATURE_SET_C,
    FEATURE_SET_D,
    compute_engineered_features,
)


class TestInputValidation:
    """Test input validation functions"""
    
    def test_valid_prediction_input(self):
        """Test valid prediction input"""
        data = {
            'shortwave_radiation_sum': 25.0,
            'sunshine_duration': 39000,
            'cloud_cover_mean': 30.0,
            'temperature_2m_mean': 26.0,
            'wind_speed_10m_mean': 17.5,
            'rain_sum': 0.0,
            'season': 'Dry',
            'is_weekend': False,
            'date': '2026-03-15'
        }
        is_valid, errors, validated = validate_prediction_input(data)
        assert is_valid, f"Validation failed: {errors}"
        assert validated['season'] == 'Dry'
        assert validated['is_weekend'] == 0
        assert validated['day_of_year'] == 74
        assert validated['warning'] is None
    
    def test_invalid_season(self):
        """Test invalid season parameter"""
        data = {
            'shortwave_radiation_sum': 25.0,
            'season': 'Summer'
        }
        is_valid, errors, _ = validate_prediction_input(data)
        assert not is_valid
        assert any('season' in error for error in errors)
    
    def test_wet_season_warning(self):
        """Test that unseen Wet season is accepted safely but issues a clear warning"""
        data = {
            'shortwave_radiation_sum': 25.0,
            'season': 'Wet'
        }
        is_valid, errors, validated = validate_prediction_input(data)
        assert is_valid, f"Validation should succeed for Wet: {errors}"
        assert validated['season'] == 'Wet'
        assert validated['warning'] is not None
        assert 'dry-season' in validated['warning'].lower()
    
    def test_extrapolated_day_of_year_warning(self):
        """Test non-fatal warning when date/day_of_year is outside training window (< 32 or > 122)"""
        # Day 15 (Jan 15) is below 32
        data_early = {
            'date': '2026-01-15',
            'shortwave_radiation_sum': 20.0,
            'season': 'Dry'
        }
        is_valid, errors, validated = validate_prediction_input(data_early)
        assert is_valid
        assert validated['warning'] is not None
        assert 'extrapolated' in validated['warning'].lower()
        
        # Day 135 (May 15) is above 122
        data_late = {
            'date': '2026-05-15',
            'shortwave_radiation_sum': 20.0,
            'season': 'Dry'
        }
        is_valid, errors, validated = validate_prediction_input(data_late)
        assert is_valid
        assert validated['warning'] is not None
        assert 'extrapolated' in validated['warning'].lower()

        # Day 74 (Mar 15) is inside [32, 122]
        data_inside = {
            'date': '2026-03-15',
            'shortwave_radiation_sum': 20.0,
            'season': 'Dry'
        }
        is_valid, errors, validated = validate_prediction_input(data_inside)
        assert is_valid
        assert validated['warning'] is None
    
    def test_invalid_numeric_bounds(self):
        """Test numeric values outside valid bounds"""
        data = {
            'shortwave_radiation_sum': 600.0,  # Max is 500
        }
        is_valid, errors, _ = validate_prediction_input(data)
        assert not is_valid
        assert any('shortwave_radiation' in error for error in errors)
    
    def test_invalid_day_of_year_bounds(self):
        """Test day_of_year outside valid range (1 to 366)"""
        data = {
            'day_of_year': 400
        }
        is_valid, errors, _ = validate_prediction_input(data)
        assert not is_valid
        assert any('day_of_year' in error for error in errors)
    
    def test_invalid_is_weekend(self):
        """Test invalid is_weekend parameter"""
        data = {
            'is_weekend': 'yes'  # Should be bool or 0/1
        }
        is_valid, errors, _ = validate_prediction_input(data)
        assert not is_valid
        assert any('is_weekend' in error for error in errors)
    
    def test_valid_is_weekend_int(self):
        """Test is_weekend with valid int value"""
        data = {
            'is_weekend': 1
        }
        is_valid, errors, validated = validate_prediction_input(data)
        assert is_valid
        assert validated['is_weekend'] == 1


class TestPredictionRowPreparation:
    """Test prediction row preparation"""
    
    def test_prepare_prediction_row_no_season_enc(self):
        """Test that season_enc is removed and day_of_year is present in prepared row"""
        data = {
            'shortwave_radiation_sum': 25.0,
            'sunshine_duration': 39000,
            'cloud_cover_mean': 30.0,
            'temperature_2m_mean': 26.0,
            'wind_speed_10m_mean': 17.5,
            'rain_sum': 0.0,
        }
        row = prepare_prediction_row(data, season='Dry', is_weekend=0, date='2026-03-15')
        
        # season_enc must NOT be in production prediction row
        assert 'season_enc' not in row
        # day_of_year must be present
        assert 'day_of_year' in row
        assert row['day_of_year'] == 74.0
        assert row['is_weekend_enc'] == 0
        assert row['sunshine_ratio'] == pytest.approx(39000 / (43200 + 1e-5))
        assert row['rad_clear'] == pytest.approx(25.0 * (1 - 30 / 100))

    def test_prepare_prediction_row_with_explicit_day_of_year(self):
        """Test prediction row preparation with explicit day_of_year"""
        data = {
            'shortwave_radiation_sum': 20.0,
            'sunshine_duration': 30000,
            'cloud_cover_mean': 40.0,
            'temperature_2m_mean': 25.0,
            'wind_speed_10m_mean': 15.0,
            'rain_sum': 0.0,
            'day_of_year': 105
        }
        row = prepare_prediction_row(data, season='Wet', is_weekend=1)
        assert row['day_of_year'] == 105.0
        assert 'season_enc' not in row
        assert row['is_weekend_enc'] == 1


class TestFeatureEngineering:
    """Test shared feature engineering functions in src/features.py"""
    
    def test_compute_engineered_features(self):
        df = pd.DataFrame({
            'date': ['2026-02-01', '2026-04-15'],
            'shortwave_radiation_sum': [25.0, 30.0],
            'sunshine_duration': [36000.0, 45000.0],
            'daylight_duration': [43200.0, 50000.0],
            'cloud_cover_mean': [20.0, 50.0],
            'temperature_2m_mean': [22.0, 32.0],
            'wind_speed_10m_mean': [12.0, 15.0],
            'rain_sum': [0.0, 10.0],
            'generation_kwh': [40.0, 45.0],
        })
        
        feat_df = compute_engineered_features(df)
        
        # Verify FEATURE_NAMES contains day_of_year and does NOT contain season_enc
        assert 'day_of_year' in FEATURE_NAMES
        assert 'season_enc' not in FEATURE_NAMES
        
        for f in FEATURE_NAMES:
            assert f in feat_df.columns, f"Missing feature in output: {f}"
            
        # 2026-02-01 is day 32 of year
        assert feat_df.iloc[0]['day_of_year'] == 32
        # 2026-04-15 is day 105 of year
        assert feat_df.iloc[1]['day_of_year'] == 105
        
        # rad_clear = 25 * (1 - 20/100) = 20.0
        assert feat_df.iloc[0]['rad_clear'] == pytest.approx(20.0)
        assert feat_df.iloc[0]['sunshine_ratio'] == pytest.approx(36000.0 / (43200.0 + 1e-5))


class TestDeduplicationAndRowPerDate:
    """Test that dim_date is deduped and joining produces exactly one row per date"""
    
    def test_dim_date_deduplication_and_join_assertion(self):
        solar_daily = pd.read_csv('data/fact_solar_daily.csv')
        weather_daily = pd.read_csv('data/fact_weather_daily.csv')
        dim_date = pd.read_csv('data/dim_date.csv')
        
        # Standardize dates
        dim_date['date'] = pd.to_datetime(dim_date['date'], format='mixed').dt.strftime('%Y-%m-%d')
        dim_date_deduped = dim_date.drop_duplicates(subset=['date'])
        
        # Assert dim_date deduped has 1 row per unique date
        assert dim_date_deduped['date'].nunique() == len(dim_date_deduped)
        
        # Merge daily tables
        merged = solar_daily.merge(weather_daily, on='date', how='inner')
        merged = merged.merge(dim_date_deduped[['date', 'is_weekend', 'season', 'day_of_year']], on='date', how='left')
        
        # CRITICAL ASSERTION: exactly one row per date in merged daily frame
        assert merged['date'].nunique() == len(merged), (
            f"Merged daily frame must have exactly one row per date! "
            f"Got {len(merged)} rows for {merged['date'].nunique()} dates."
        )
        assert len(merged) == len(solar_daily)


class TestAnomalyFilter:
    """Test documented, configurable anomaly filtering"""
    
    def test_anomaly_filter_excludes_documented_dates(self):
        solar_daily = pd.read_csv('data/fact_solar_daily.csv')
        
        assert '2026-02-01' in solar_daily['date'].values
        assert '2026-03-31' in solar_daily['date'].values
        
        # Exclude anomalies
        filtered = filter_anomalies(solar_daily)
        
        # Assert neither anomaly date is in filtered data
        assert '2026-02-01' not in filtered['date'].values
        assert '2026-03-31' not in filtered['date'].values
        assert len(filtered) == len(solar_daily) - 2
        
        # Check reasons are documented
        for d in ANOMALY_DATES:
            assert d in ANOMALY_REASONS
            assert len(ANOMALY_REASONS[d]) > 0


class TestTimeOrderedSplits:
    """Test rolling-origin cross-validation preserves strict chronological order"""
    
    def test_time_ordered_splits_no_future_leakage(self):
        solar = pd.read_csv('data/fact_solar_daily.csv')
        weather = pd.read_csv('data/fact_weather_daily.csv')
        clean = filter_anomalies(solar.merge(weather, on='date', how='inner'))
        clean = clean.sort_values('date').reset_index(drop=True)
        
        tscv = TimeSeriesSplit(n_splits=5, test_size=10)
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(clean)):
            train_dates = clean.iloc[train_idx]['date']
            test_dates = clean.iloc[test_idx]['date']
            
            max_train_date = train_dates.max()
            min_test_date = test_dates.min()
            
            # Assert every test date is strictly later than all train dates
            assert min_test_date > max_train_date, (
                f"Fold {fold} leakage: min test date ({min_test_date}) is not strictly "
                f"after max train date ({max_train_date})"
            )
            assert len(test_idx) == 10


class TestHourlyTimestampAlignment:
    """Test verification and alignment of hourly timestamps across tables"""
    
    def test_hourly_timestamps_alignment_and_timezone(self):
        solar_h = pd.read_csv('data/fact_solar_hourly.csv')
        weather_h = pd.read_csv('data/fact_weather_hourly.csv')
        
        # fact_solar_hourly.hour_ts contains +08 timezone offset
        assert '+08' in str(solar_h.iloc[0]['hour_ts'])
        # For date 2026-02-01, solar_hourly starts at 2026-02-02 00:00:00+08
        feb1_solar = solar_h[solar_h['date'] == '2026-02-01']
        assert str(feb1_solar.iloc[0]['hour_ts']) == '2026-02-02 00:00:00+08'
        
        # When converted to UTC, 2026-02-02 00:00:00+08 matches 2026-02-01 16:00:00 UTC
        ts_utc = pd.to_datetime(feb1_solar.iloc[0]['hour_ts']).tz_convert('UTC')
        assert ts_utc.strftime('%Y-%m-%d %H:%M:%S') == '2026-02-01 16:00:00'
        
        # Test align_hourly_timestamps utility
        aligned_s, aligned_w = align_hourly_timestamps(solar_h, weather_h)
        assert 'hour_ts_utc' in aligned_s.columns
        assert 'hour_ts_utc' in aligned_w.columns
        assert str(aligned_s.iloc[0]['hour_ts_utc']).startswith('2026-02-01 16:00:00')


class TestModelManager:
    """Test ModelManager and compute_model_scores in src/models.py"""
    
    def test_model_manager_loading(self):
        from src.models import ModelManager
        mm = ModelManager()
        assert mm.is_loaded is True
        assert len(mm.get_feature_names()) == 10
        assert 'day_of_year' in mm.get_feature_names()
        assert 'season_enc' not in mm.get_feature_names()

    def test_compute_model_scores(self):
        from src.models import ModelManager, compute_model_scores
        mm = ModelManager()
        solar = pd.read_csv('data/fact_solar_daily.csv')
        weather = pd.read_csv('data/fact_weather_daily.csv')
        
        scores = compute_model_scores(mm.model, mm.features, solar, weather)
        assert 'r2_score' in scores
        assert 'rmse' in scores
        assert 'mae' in scores
        assert 'feature_importances' in scores
        assert len(scores['feature_importances']) == 10
        assert scores['n_samples'] == 89  # 91 minus 2 anomalies

    def test_model_manager_non_negative_predictions(self):
        from src.models import ModelManager
        mm = ModelManager()
        X_zero = pd.DataFrame([{f: 0.0 for f in mm.get_feature_names()}])
        pred = mm.predict(X_zero)
        assert pred is not None
        assert pred >= 0.0


class TestFeatureImportanceExtraction:
    """Test feature importance extraction across heterogeneous model types"""

    def test_pipeline_ridge_importances(self):
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        from src.models import extract_model_feature_importances
        
        feats = ['f1', 'f2', 'f3']
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [2, 3, 4]])
        y = np.array([10, 20, 30, 15])
        pipe = Pipeline([('scaler', StandardScaler()), ('reg', Ridge(alpha=1.0))]).fit(X, y)
        
        fi = extract_model_feature_importances(pipe, feats)
        assert len(fi) == 3
        assert pytest.approx(sum(fi.values()), rel=1e-2) == 1.0


class TestModelRetrainingTournament:
    """Test model retraining tournament logic and fairness"""

    def test_candidate_models_building(self):
        from etl.retrain import build_candidate_models
        candidates = build_candidate_models()
        assert 'Ridge_Set_B' in candidates
        assert 'Ridge_Set_A' in candidates
        assert 'Huber_Robust_Set_A' in candidates
        assert 'Ridge_Lag_Set_D' in candidates

    def test_retraining_tournament_execution(self):
        from etl.retrain import evaluate_and_retrain_model
        
        solar = pd.read_csv('data/fact_solar_daily.csv')
        weather = pd.read_csv('data/fact_weather_daily.csv')
        df_feat = compute_engineered_features(solar.merge(weather, on='date'))
        
        res = evaluate_and_retrain_model(df_feat, force_update=False)
        assert res['retrained'] is True
        assert 'candidate_metrics' in res
        assert 'tournament_results' in res
        assert res['candidate_metrics']['mean_cv_rmse'] > 0
        assert 'fold_maes' in res['candidate_metrics']
        assert len(res['candidate_metrics']['fold_maes']) == 5


class TestPredictionAPIEndpoint:
    """Test Flask /predict and /api/model-score endpoints"""

    def test_predict_endpoint_success_with_date(self):
        from src.app_main import app
        client = app.test_client()
        payload = {
            'date': '2026-03-20',
            'shortwave_radiation_sum': 25.0,
            'sunshine_duration': 39000,
            'cloud_cover_mean': 30.0,
            'temperature_2m_mean': 26.0,
            'wind_speed_10m_mean': 17.5,
            'rain_sum': 0.0,
            'season': 'Dry',
            'is_weekend': False
        }
        resp = client.post('/predict', json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'predicted_generation_kwh' in data
        assert data['predicted_generation_kwh'] >= 0.0
        assert data['day_of_year'] == 79
        assert data.get('warning') is None

    def test_predict_endpoint_wet_season_warning(self):
        from src.app_main import app
        client = app.test_client()
        payload = {
            'date': '2026-07-15',
            'shortwave_radiation_sum': 20.0,
            'sunshine_duration': 30000,
            'cloud_cover_mean': 50.0,
            'temperature_2m_mean': 28.0,
            'wind_speed_10m_mean': 12.0,
            'rain_sum': 5.0,
            'season': 'Wet',
            'is_weekend': False
        }
        resp = client.post('/predict', json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'predicted_generation_kwh' in data
        assert 'warning' in data
        assert 'dry-season' in data['warning'].lower()

    def test_predict_endpoint_extrapolated_day_of_year_warning(self):
        """Test /predict returns extrapolation warning when day_of_year < 32 or > 122"""
        from src.app_main import app
        client = app.test_client()
        
        # Date earlier than training window: 2026-01-10 (day 10 < 32)
        payload_early = {
            'date': '2026-01-10',
            'shortwave_radiation_sum': 22.0,
            'sunshine_duration': 32000,
            'cloud_cover_mean': 25.0,
            'temperature_2m_mean': 24.0,
            'wind_speed_10m_mean': 15.0,
            'rain_sum': 0.0,
            'season': 'Dry',
            'is_weekend': False
        }
        resp_early = client.post('/predict', json=payload_early)
        assert resp_early.status_code == 200
        data_early = resp_early.get_json()
        assert data_early['day_of_year'] == 10
        assert data_early['warning'] is not None
        assert 'extrapolated' in data_early['warning'].lower()

        # Date later than training window: 2026-06-01 (day 152 > 122) with Dry season
        payload_late = {
            'date': '2026-06-01',
            'shortwave_radiation_sum': 28.0,
            'sunshine_duration': 38000,
            'cloud_cover_mean': 20.0,
            'temperature_2m_mean': 29.0,
            'wind_speed_10m_mean': 14.0,
            'rain_sum': 0.0,
            'season': 'Dry',
            'is_weekend': False
        }
        resp_late = client.post('/predict', json=payload_late)
        assert resp_late.status_code == 200
        data_late = resp_late.get_json()
        assert data_late['day_of_year'] == 152
        assert data_late['warning'] is not None
        assert 'extrapolated' in data_late['warning'].lower()

    def test_model_score_endpoint(self):
        from src.app_main import app
        client = app.test_client()
        resp = client.get('/api/model-score')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'r2_score' in data
        assert 'rmse' in data
        assert 'mae' in data
        assert 'feature_importances' in data
        assert 'day_of_year' in data['feature_importances']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
