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
        assert row['sunshine_ratio'] == pytest.approx(39000 / 86400)
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
