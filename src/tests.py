"""
Unit and integration tests for Solar Analytics
"""
import pytest
import pandas as pd
from .utils import validate_prediction_input, prepare_prediction_row, calculate_kpis


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
            'is_weekend': False
        }
        is_valid, errors, validated = validate_prediction_input(data)
        assert is_valid, f"Validation failed: {errors}"
        assert validated['season'] == 'Dry'
        assert validated['is_weekend'] == 0
    
    def test_invalid_season(self):
        """Test invalid season parameter"""
        data = {
            'shortwave_radiation_sum': 25.0,
            'season': 'Summer'
        }
        is_valid, errors, _ = validate_prediction_input(data)
        assert not is_valid
        assert any('season' in error for error in errors)
    
    def test_invalid_numeric_bounds(self):
        """Test numeric values outside valid bounds"""
        data = {
            'shortwave_radiation_sum': 600.0,  # Max is 500
        }
        is_valid, errors, _ = validate_prediction_input(data)
        assert not is_valid
        assert any('shortwave_radiation' in error for error in errors)
    
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
    
    def test_prepare_prediction_row_dry_season(self):
        """Test row preparation for dry season"""
        data = {
            'shortwave_radiation_sum': 25.0,
            'sunshine_duration': 39000,
            'cloud_cover_mean': 30.0,
            'temperature_2m_mean': 26.0,
            'wind_speed_10m_mean': 17.5,
            'rain_sum': 0.0,
        }
        row = prepare_prediction_row(data, 'Dry', 0)
        
        assert row['season_enc'] == 0
        assert row['is_weekend_enc'] == 0
        assert row['sunshine_ratio'] == pytest.approx(39000 / (43200 + 1e-5))
        assert row['rad_clear'] == pytest.approx(25.0 * (1 - 30 / 100))
    
    def test_prepare_prediction_row_wet_season_weekend(self):
        """Test row preparation for wet season weekend"""
        data = {
            'shortwave_radiation_sum': 15.0,
            'sunshine_duration': 25000,
            'cloud_cover_mean': 70.0,
            'temperature_2m_mean': 24.0,
            'wind_speed_10m_mean': 8.0,
            'rain_sum': 5.0,
        }
        row = prepare_prediction_row(data, 'Wet', 1)
        
        assert row['season_enc'] == 1
        assert row['is_weekend_enc'] == 1
        assert row['rad_clear'] == pytest.approx(15.0 * (1 - 70 / 100))


class TestKPICalculation:
    """Test KPI calculation functions"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        dates = pd.date_range('2025-01-01', periods=30)
        solar_daily = pd.DataFrame({
            'date': dates,
            'generation_kwh': [30 + i % 10 for i in range(30)],
            'consumption_kwh': [40 + i % 5 for i in range(30)]
        })
        weather_daily = pd.DataFrame({
            'date': dates,
            'temperature_2m_mean': [25 + i % 10 for i in range(30)]
        })
        daily_data = solar_daily.merge(weather_daily, on='date')
        
        return solar_daily, weather_daily, daily_data
    
    def test_kpi_calculation(self, sample_data):
        """Test KPI calculation"""
        solar_daily, weather_daily, daily_data = sample_data
        
        kpis = calculate_kpis(solar_daily, weather_daily, daily_data)
        
        assert 'total_generation' in kpis
        assert 'total_consumption' in kpis
        assert 'self_sufficiency' in kpis
        assert 'avg_temperature' in kpis
        assert kpis['total_generation'] > 0
        assert kpis['total_consumption'] > 0
        assert 0 <= kpis['self_sufficiency'] <= 200


class TestFeatureEngineering:
    """Test shared feature engineering functions in src/features.py"""
    
    def test_compute_engineered_features(self):
        from src.features import compute_engineered_features, FEATURE_NAMES
        
        df = pd.DataFrame({
            'date': ['2026-02-01', '2026-07-15'],
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
        
        for f in FEATURE_NAMES:
            assert f in feat_df.columns, f"Missing feature: {f}"
            
        # February = Dry (0), July = Wet (1)
        assert feat_df.iloc[0]['season_enc'] == 0
        assert feat_df.iloc[1]['season_enc'] == 1
        
        # 2026-02-01 is Sunday (weekend = 1)
        assert feat_df.iloc[0]['is_weekend_enc'] == 1
        
        # rad_clear = 25 * (1 - 20/100) = 20.0
        assert feat_df.iloc[0]['rad_clear'] == pytest.approx(20.0)
        assert feat_df.iloc[0]['sunshine_ratio'] == pytest.approx(36000.0 / (43200.0 + 1e-5))


class TestETLExtractionMocked:
    """Test ETL extraction with mocked Open-Meteo responses"""
    
    def test_fetch_open_meteo_weather_mocked(self):
        from unittest.mock import patch, MagicMock
        from etl.extract import fetch_open_meteo_weather
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'daily': {
                'time': ['2026-03-01', '2026-03-02'],
                'shortwave_radiation_sum': [22.5, 24.1],
                'sunshine_duration': [38000.0, 40000.0],
                'daylight_duration': [43200.0, 43200.0],
                'cloud_cover_mean': [15.0, 25.0],
                'temperature_2m_mean': [25.0, 26.5],
                'relative_humidity_2m_mean': [45.0, 50.0],
                'rain_sum': [0.0, 0.0],
                'wind_speed_10m_mean': [14.0, 12.0],
                'weather_code': [0, 1]
            },
            'hourly': {
                'time': ['2026-03-01T00:00', '2026-03-01T01:00'],
                'relative_humidity_2m': [60.0, 62.0],
                'wind_speed_10m': [10.0, 11.0],
                'is_day': [0, 0],
                'sunshine_duration': [0.0, 0.0],
                'temperature_2m': [18.0, 17.5],
                'cloud_cover': [10.0, 12.0],
                'rain': [0.0, 0.0],
                'weather_code': [0, 0]
            }
        }
        
        with patch('requests.Session.get', return_value=mock_response):
            daily_df, hourly_df = fetch_open_meteo_weather('2026-03-01', '2026-03-02')
            
            assert len(daily_df) == 2
            assert 'date' in daily_df.columns
            assert daily_df.iloc[0]['date'] == '2026-03-01'
            assert daily_df.iloc[0]['temperature_2m_mean'] == 25.0
            
            assert len(hourly_df) == 2
            assert 'hour_ts' in hourly_df.columns
            assert 'date' in hourly_df.columns


class TestETLTransformation:
    """Test ETL transformation logic"""
    
    def test_clean_and_validate(self):
        from etl.transform import clean_and_validate
        
        df = pd.DataFrame({
            'date': ['2026-03-01', '2026-03-01'],  # Duplicate
            'shortwave_radiation_sum': [25.0, 600.0],  # Out of bounds (>500)
            'temperature_2m_mean': [26.0, 26.0]
        })
        
        cleaned = clean_and_validate(df, 'test_dataset')
        # Deduped to 1 row
        assert len(cleaned) == 1
        # Clipped to max bound (500)
        assert cleaned.iloc[0]['shortwave_radiation_sum'] <= 500.0

    def test_build_dim_date(self):
        from etl.transform import build_dim_date
        
        dim_date = build_dim_date(['2026-02-01', '2026-08-15'])
        assert len(dim_date) == 2
        
        feb = dim_date[dim_date['date'] == '2026-02-01'].iloc[0]
        aug = dim_date[dim_date['date'] == '2026-08-15'].iloc[0]
        
        assert feb['date_key'] == 20260201
        assert feb['month_name'] == 'February'
        assert feb['season'] == 'Dry'
        assert bool(feb['is_weekend']) is True
        
        assert aug['season'] == 'Wet'


class TestETLLoadAndStatus:
    """Test ETL status reporting and CSV refresh"""
    
    def test_refresh_csv_files(self, tmp_path):
        from etl.load import refresh_csv_files
        
        dummy_data = {
            'dim_date': pd.DataFrame({'date': ['2026-01-01']}),
            'fact_solar_daily': pd.DataFrame({'date': ['2026-01-01'], 'generation_kwh': [42.0]}),
        }
        
        refresh_csv_files(dummy_data, data_dir=str(tmp_path))
        
        assert (tmp_path / 'dim_date.csv').exists()
        assert (tmp_path / 'fact_solar_daily.csv').exists()

    def test_record_etl_run(self, tmp_path):
        import json
        from datetime import datetime
        from etl.load import record_etl_run
        
        status_file = tmp_path / 'etl_status.json'
        record_etl_run(
            run_id='test_run_123',
            start_time=datetime(2026, 1, 1, 10, 0, 0),
            end_time=datetime(2026, 1, 1, 10, 0, 5),
            status='success',
            records_processed={'dim_date': 10},
            status_file_path=str(status_file)
        )
        
        assert status_file.exists()
        with open(status_file) as f:
            data = json.load(f)
            assert data['run_id'] == 'test_run_123'
            assert data['status'] == 'success'
            assert data['records_processed'] == {'dim_date': 10}


class TestHealthEndpointETL:
    """Test that /health returns last_etl_run"""
    
    def test_health_includes_last_etl_run(self):
        from src.app_main import app
        
        client = app.test_client()
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'healthy'
        assert 'last_etl_run' in data


class TestModelManager:
    """Test ModelManager and compute_model_scores in src/models.py"""
    
    def test_model_manager_loading(self):
        from src.models import ModelManager
        
        mm = ModelManager()
        assert mm.is_loaded is True
        assert len(mm.get_feature_names()) == 10

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
        assert scores['n_samples'] > 0

    def test_model_manager_non_negative_predictions(self):
        from src.models import ModelManager
        
        mm = ModelManager()
        # Test with zero/dark features
        X_zero = pd.DataFrame([{f: 0.0 for f in mm.get_feature_names()}])
        pred = mm.predict(X_zero)
        assert pred is not None
        assert pred >= 0.0


class TestFeatureImportanceExtraction:
    """Test feature importance extraction across heterogeneous model types"""

    def test_tree_model_importances(self):
        from sklearn.ensemble import GradientBoostingRegressor
        from src.models import extract_model_feature_importances
        import numpy as np
        
        feats = ['f1', 'f2', 'f3']
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [2, 3, 4]])
        y = np.array([10, 20, 30, 15])
        gbr = GradientBoostingRegressor().fit(X, y)
        
        fi = extract_model_feature_importances(gbr, feats)
        assert len(fi) == 3
        assert pytest.approx(sum(fi.values()), rel=1e-2) == 1.0

    def test_pipeline_linear_importances(self):
        from sklearn.linear_model import HuberRegressor
        from sklearn.preprocessing import RobustScaler
        from sklearn.pipeline import Pipeline
        from src.models import extract_model_feature_importances
        import numpy as np
        
        feats = ['f1', 'f2', 'f3']
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [2, 3, 4]])
        y = np.array([10, 20, 30, 15])
        pipe = Pipeline([('scaler', RobustScaler()), ('reg', HuberRegressor(max_iter=500))]).fit(X, y)
        
        fi = extract_model_feature_importances(pipe, feats)
        assert len(fi) == 3
        assert pytest.approx(sum(fi.values()), rel=1e-2) == 1.0

    def test_voting_ensemble_importances(self):
        from sklearn.ensemble import GradientBoostingRegressor, VotingRegressor
        from sklearn.linear_model import HuberRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import RobustScaler
        from src.models import extract_model_feature_importances
        import numpy as np
        
        feats = ['f1', 'f2', 'f3']
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [2, 3, 4]])
        y = np.array([10, 20, 30, 15])
        m1 = GradientBoostingRegressor().fit(X, y)
        m2 = Pipeline([('scaler', RobustScaler()), ('reg', HuberRegressor(max_iter=500))]).fit(X, y)
        vote = VotingRegressor([('m1', m1), ('m2', m2)]).fit(X, y)
        
        fi = extract_model_feature_importances(vote, feats)
        assert len(fi) == 3
        assert pytest.approx(sum(fi.values()), rel=1e-2) == 1.0


class TestModelRetrainingTournament:
    """Test model retraining tournament logic and fairness"""

    def test_candidate_models_building(self):
        from etl.retrain import build_candidate_models
        
        candidates = build_candidate_models()
        assert 'Huber_Robust' in candidates
        assert 'Ensemble_Hybrid' in candidates
        assert 'Tuned_GBR' in candidates
        assert 'Ridge_Scaled' in candidates

    def test_retraining_tournament_execution(self):
        from etl.retrain import evaluate_and_retrain_model
        from src.features import compute_engineered_features
        
        solar = pd.read_csv('data/fact_solar_daily.csv')
        weather = pd.read_csv('data/fact_weather_daily.csv')
        df_feat = compute_engineered_features(solar.merge(weather, on='date'))
        
        res = evaluate_and_retrain_model(df_feat, force_update=False)
        assert res['retrained'] is True
        assert 'candidate_metrics' in res
        assert 'current_metrics' in res
        assert 'tournament_results' in res
        assert res['candidate_metrics']['rmse'] > 0
        assert res['current_metrics']['rmse'] > 0


class TestPredictionAPIEndpoint:
    """Test Flask /predict and /api/model-score endpoints"""

    def test_predict_endpoint_success(self):
        from src.app_main import app
        
        client = app.test_client()
        payload = {
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
        assert data['status'] in ['Low', 'Normal']

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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



