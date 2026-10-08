# ☀️ Solar Energy Analytics Dashboard

> **A modern, responsive solar energy analytics platform combining historical CSV data visualization with auto-refreshing dashboard displays, ML prediction storage, and database retrieval.**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-black)
![Machine Learning](https://img.shields.io/badge/ML-ScikitLearn-orange)
![Status](https://img.shields.io/badge/Status-Prototype-yellow)

## ⭐ Features

### 📊 Auto-Refreshing Dashboard

![Auto-Refreshing Dashboard](images/1.png)
*The main dashboard provides a comprehensive view of solar generation and consumption metrics. It features auto-refreshing KPI tracking, dynamic charts for historical patterns, and weather correlation analysis for deep insights into system performance.*
- **5 Key Performance Indicator (KPI) Cards** - Track generation, consumption, efficiency, temperature, and predictions
- **5 Interactive Charts** - Visualize daily trends, monthly patterns, radiation correlation, weather distribution, and hourly generation patterns
- **Auto-Refresh Mechanism** - Data updates every 5 seconds for live insights
- **Responsive Design** - Works seamlessly on desktop (1200px+), tablet (768px), and mobile (640px)
- **PowerBI-Style Theme** - Professional white and baby blue color scheme with intuitive UI

### 🤖 ML-Powered Predictions

![ML Predictions Analytics](images/2.png)
*The ML Predictions section monitors the effectiveness of our forecasting models. It tracks the latest prediction values, daily prediction counts, and calculates accuracy scores based on historical data comparisons.*
- **Solar Generation Forecasting** - Predict daily energy generation based on weather parameters
- **Weather-Based Analysis** - Input radiation, cloud cover, temperature, wind speed, and precipitation
- **Database Storage** - All predictions logged to MySQL with weather conditions and metadata
- **Historical Analysis** - Track prediction accuracy, seasonal patterns, and weather correlations
- **Comprehensive Metrics** - Average generation, min/max ranges, seasonal breakdown, and cloud impact analysis

### 📈 Analytics & Insights
- **Daily vs Consumption Analysis** - Compare generation against consumption patterns
- **Monthly Aggregations** - Track performance trends across 12-month periods
- **Weather Distribution** - Visualize weather code frequency and patterns
- **Radiation Correlation** - Scatter plot showing radiation-to-generation relationship
- **Hourly Patterns** - Understand 24-hour generation cycles
- **Database Statistics** - Prediction stats and historical tracking

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| 🐍 **Backend** | Flask | 3.0.0 |
| 🐍 **Runtime** | Python | 3.12 |
| 🗄️ **Database** | MySQL | 8.0+ |
| 📊 **Data Processing** | Pandas | 2.2.0 |
| 🔢 **Numerical Computation** | NumPy | 1.26.4 |
| 🤖 **ML Model** | Scikit-learn (Gradient Boosting) | 1.4.0 |
| 💾 **Model Persistence** | Joblib | 1.3.2 |
| 📈 **Charting** | Chart.js | 3.9.1 |
| 🎨 **Frontend** | HTML5 / CSS3 / ES6+ | - |
| 🐳 **Containerization** | Docker | Latest |
| ⚙️ **Web Server** | Gunicorn | 21.2.0 |
| ✅ **Testing** | Pytest | 7.4.3 |
| 📦 **Deployment** | Docker Compose | 3.8 |

## 📁 Project Structure

```
Solar-Energy-Generation-Weather-Analytics/
├── 📁 src/                       # Application source modules
│   ├── __init__.py              # Package initialization
│   ├── api_docs.py              # OpenAPI specification
│   ├── app_main.py              # Core Flask application & routes
│   ├── appsql.py                # Database connection & queries
│   ├── config.py                # Configuration settings
│   ├── models.py                # ML ModelManager & score utilities
│   ├── tests.py                 # Pytest test suite
│   └── utils.py                 # Input validation & KPI utilities
├── 📊 data/                      # Historical CSV datasets
│   ├── dim_date.csv
│   ├── dim_weather_codes.csv
│   ├── fact_solar_daily.csv
│   ├── fact_solar_hourly.csv
│   ├── fact_weather_daily.csv
│   └── fact_weather_hourly.csv
├── 🖼️ images/                    # Dashboard screenshots for documentation
│   ├── 1.png
│   ├── 2.png
│   ├── 3.png
│   └── 4.png
├── 🧠 models/                    # Trained scikit-learn models & feature metadata
│   ├── feature_names.pkl
│   └── solar_generation_model.pkl
├── 📓 notebooks/                 # Jupyter exploratory analysis & training notebooks
│   ├── 01_EDA.ipynb
│   └── 02_Modelling.ipynb
├── 🗄️ sql/                        # Database schema definition
│   └── create_table.sql
├── 🎨 templates/                 # Frontend Jinja2 HTML templates
│   ├── dashboard.html
│   └── index.html
├── 🐍 app.py                     # Application entry point with runner
├── 🚀 start-dashboard.sh         # Quick-start launcher script
├── 🐳 docker-compose.yml         # Multi-container Docker configuration
├── 📦 Dockerfile                 # Container image build specification
├── 📋 requirements.txt           # Pinned Python package dependencies
├── ⚙️ .env.example               # Example environment variable template
├── 🚫 .dockerignore              # Docker build ignore patterns
├── 🚫 .gitignore                # Git version control ignore rules
├── 📄 LICENSE                    # MIT License
├── 📝 IMPROVEMENTS.md            # Improvement changelog & deployment notes
└── 📖 README.md                  # Project documentation
```

## 🚀 Recent Improvements (v1.1.0)

### 🔹 Prototype Enhancements
- ✅ **Enhanced Error Handling** - Comprehensive exception handling with detailed logging
- ✅ **Thread-Safe Caching** - Concurrent request support with threading locks
- ✅ **Database Optimization** - Added indexes for faster queries
- ✅ **Input Validation** - Strict parameter validation with helpful error messages
- ✅ **Health Monitoring** - New `/health` endpoint for system status checks
- ✅ **API Documentation** - OpenAPI/Swagger docs at `/api/docs`
- ✅ **Docker Support** - Containerized Docker and Docker Compose setup
- ✅ **Modular Code** - Refactored into `utils.py`, `models.py`, and `tests.py` in `src/` folder
- ✅ **Organized Structure** - All Python modules consolidated in `src/` directory for cleaner project layout
- ✅ **Unit Tests** - Comprehensive test suite with pytest and coverage reports
- ✅ **Structured Logging** - Replaced print statements with logging framework

### 🔹 API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check (model + database status) |
| `/api/docs` | GET | OpenAPI/Swagger documentation |
| `/api/model-score` | GET | Model performance metrics and feature importances |
| `/api/dashboard-data` | GET | All dashboard data (KPIs + charts) |
| `/predict` | POST | Solar generation prediction with validation |
| `/history` | GET | Prediction history from database |
| `/stats` | GET | Prediction statistics and aggregates |

### 🔹 Deployment Options

#### 🐳 Quick Start with Docker Compose (Recommended)
```bash
# Setup
cp .env.example .env
# Edit .env with your configuration

# Start
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

#### 🐍 Traditional Python / Gunicorn
```bash
pip install -r requirements.txt
cp .env.example .env
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

#### 🐳 Docker Single Container
```bash
docker build -t solar-analytics:latest .
docker run -p 8000:8000 --env-file .env solar-analytics:latest
```

### 🔹 Testing
```bash
# Run unit tests
pytest src/tests.py -v

# With coverage report
pytest src/tests.py --cov=src --cov-report=html

# Generate detailed coverage report with terminal output
pytest src/tests.py --cov=src --cov-report=html --cov-report=term

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/docs
```

### 🔹 Test Reports
After running pytest with coverage, a detailed HTML report is generated in the `htmlcov/` directory:
```bash
# Generate coverage report
pytest src/tests.py --cov=src --cov-report=html

# Open report in browser
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
# or
start htmlcov/index.html  # Windows
```

The coverage report shows:
- Line-by-line coverage for all modules
- Branch coverage analysis
- Overall coverage percentage
- Missing lines highlighted for quick identification

For complete details on improvements, see [IMPROVEMENTS.md](IMPROVEMENTS.md)

## 📦 Installation

### 🔹 Prerequisites
- Python 3.12+ OR Docker
- MySQL 8.0+ (or use Docker Compose)
- pip package manager (for Python installation)

### 1️⃣ Clone Repository
```bash
git clone https://github.com/patelom2810/Solar-Energy-Generation-Weather-Analytics.git
cd Solar-Energy-Generation-Weather-Analytics
```

### 2️⃣ Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment
Create `.env` file in project root:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=solar_analytics
DB_PORT=3306

# Flask Configuration
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=8000

# Application Settings
LOG_LEVEL=INFO
CSV_CACHE_DURATION=300
MAX_PREDICTIONS_HISTORY=1000
```

### 5️⃣ Initialize Database
```bash
# MySQL must be running
python3 -c "from src.appsql import init_db; init_db()"
```

### 6️⃣ Start Flask Server
```bash
python3 app.py
```
Server runs on `http://127.0.0.1:8000`

## 🚀 Usage

### 🔹 Access Dashboard
1. Open browser: **http://127.0.0.1:8000/dashboard** *(Local - requires running app)*
2. View KPIs, charts, and prediction analytics
3. Data auto-refreshes every 5 seconds

### 🔹 Make Predictions

![Solar Predictor](images/4.png)
*The Predictor Form allows users to forecast solar generation based on custom weather parameters. It supports inputs such as radiation, cloud cover, and temperature to calculate expected energy yield.*
1. Navigate to: **http://127.0.0.1:8000** *(Local - requires running app)*
2. Fill in weather parameters:
   - ☀️ Shortwave Radiation (W/m²)
   - 🌤️ Sunshine Duration (seconds)
   - ☁️ Cloud Cover (0-100%)
   - 🌡️ Temperature 2m (°C)
   - 💨 Wind Speed 10m (m/s)
   - 🌧️ Rain Sum (mm)
   - 🍂 Season (Dry/Wet)
   - 📅 Weekend (Yes/No)
3. Click **Predict** to generate forecast and store in database

### 🔹 API Endpoints

#### 🩺 System Health Check
```bash
GET /health
```
Returns:
```json
{
  "status": "healthy",
  "model": "loaded",
  "database": "connected",
  "timestamp": "2026-10-08T18:42:29.612869"
}
```

#### 📖 API Documentation
```bash
GET /api/docs
```
Returns: Complete OpenAPI 3.0 specification for all endpoints

#### 📊 Get Dashboard Data
```bash
GET /api/dashboard-data
```
Returns: KPIs, historical data, charts data, and prediction statistics

#### 🔮 Make Prediction
```bash
POST /predict
Content-Type: application/json

{
  "shortwave_radiation_sum": 25.0,
  "sunshine_duration": 39000,
  "cloud_cover_mean": 30.0,
  "temperature_2m_mean": 26.0,
  "wind_speed_10m_mean": 17.5,
  "rain_sum": 0.0,
  "season": "Dry",
  "is_weekend": false
}
```
**Validation:** Numeric fields must be within valid physical ranges; season must be 'Dry' or 'Wet'.

Response:
```json
{
  "predicted_generation_kwh": 30.24,
  "status": "Normal"
}
```

#### 📋 Get Prediction History
```bash
GET /history?limit=100
```

#### 📈 Get Statistics
```bash
GET /stats
```

#### 🧪 Get Model Score Metrics
```bash
GET /api/model-score
```
Returns: R², MAE, RMSE, MAPE, feature importances, and sample predictions

## 🗄️ Data Sources

### 🔹 Historical Data (CSV)
- **fact_solar_daily.csv** - Daily solar generation and consumption data
- **fact_weather_daily.csv** - Daily weather conditions and parameters
- **fact_solar_hourly.csv** - Hourly generation patterns (24-hour cycles)
- **dim_date.csv** - Date dimension with season information
- **dim_weather_codes.csv** - Weather code reference data
- **fact_weather_hourly.csv** - Hourly weather data

### 🔹 Database Schema
Exact contents of `sql/create_table.sql`:
```sql
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
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_season (season),
    INDEX idx_predictions_today (timestamp, is_weekend)
);
```

## 🧠 ML Model

![Model Performance Metrics](images/3.png)
*The Model Performance view shows our Gradient Boosting Regressor metrics, feature importances, and predicted versus actual comparisons.*

### 🔹 Model Architecture
- **Algorithm**: Gradient Boosting Regressor (Scikit-learn)
- **Training Data**: Historical daily solar generation with weather parameters
- **Features** (10): 
  - Shortwave Radiation Sum
  - Sunshine Duration
  - Cloud Cover Mean
  - Temperature 2m Mean
  - Wind Speed 10m Mean
  - Rain Sum
  - Season Encoding
  - Is Weekend Encoding
  - Sunshine Ratio
  - Radiation Clear Sky

### 🔹 Sample Predictions
Test predictions across diverse weather conditions generated by the model:

```
Scenario              Prediction    Cloud    Temperature
────────────────────────────────────────────────────────
☀️ Perfect Sunny     42.14 kWh      5%       28.0°C
🌤️ Partly Cloudy    31.31 kWh     40%       26.0°C
☁️ Cloudy Day        26.30 kWh     70%       24.0°C
⛈️ Rainy Day         23.53 kWh     95%       22.0°C
🌅 Early Morning     22.16 kWh     20%       18.0°C
🏖️ Optimal (Weekend) 42.78 kWh     10%       27.5°C

Average: 31.37 kWh | Range: 22.16 - 42.78 kWh | StdDev: 9.14 kWh
```

### 🔹 Key Insights
- **Cloud Impact**: Clear skies average **31.94 kWh** vs cloudy **23.99 kWh**
- **Seasonal Pattern**: Dry season averages **29.91 kWh** vs wet **23.99 kWh**
- **Temperature Correlation**: Warm days (25-30°C) generate more consistently
- **Weather Sensitivity**: Model accurately responds to all weather parameters

## ⚙️ Configuration

### 🔹 Environment Variables (`.env`)
```env
# Database Configuration
DB_HOST=localhost              # MySQL server host
DB_USER=root                   # MySQL username
DB_PASSWORD=your_password      # MySQL password
DB_NAME=solar_analytics        # Database name
DB_PORT=3306                   # MySQL port

# Flask Configuration
FLASK_ENV=development          # development/production
FLASK_HOST=0.0.0.0             # Host interface
FLASK_PORT=8000                # Port number

# Application Settings
LOG_LEVEL=INFO                 # Logging verbosity
CSV_CACHE_DURATION=300         # CSV cache duration in seconds
MAX_PREDICTIONS_HISTORY=1000   # Max records retrieved by default
```

## 🐛 Troubleshooting

### 🔹 MySQL Connection Issues
```bash
# Check MySQL is running
brew services list | grep mysql

# Start MySQL if not running
brew services start mysql

# Verify credentials in .env file
# Test connection: mysql -h localhost -u root -p
```

### 🔹 Port 8000 Already in Use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or specify a different port in .env (FLASK_PORT=8080)
```

### 🔹 CSV Data Not Loading
```bash
# Verify data files exist in data/ directory
ls -lah data/

# Check CSV format (UTF-8 encoding recommended)
file data/*.csv
```

### 🔹 Database Table Not Found
```bash
# Reinitialize database
python3 -c "from src.appsql import init_db; init_db()"

# Verify MySQL connection and privileges
mysql -u root -p solar_analytics
SHOW TABLES;
```

## 📊 Stored Prediction Statistics

```
Database Analysis (10 Representative Predictions):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Predictions:     10
Average Generation:    28.72 kWh
Range:                 23.38 - 42.45 kWh
Standard Deviation:    5.59 kWh

By Season:
  Dry:   8 predictions, Avg 29.91 kWh
  Wet:   2 predictions, Avg 23.99 kWh

By Cloud Cover:
  Clear (0-20%):     5 preds, Avg 31.94 kWh
  Partly (20-40%):   1 pred,  Avg 27.64 kWh
  Mostly (40-60%):   2 preds, Avg 25.96 kWh
  Cloudy (60-100%):  2 preds, Avg 23.99 kWh
```

## 📖 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [Scikit-learn Gradient Boosting](https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosted-trees)
- [MySQL Python Connector](https://dev.mysql.com/doc/connector-python/en/)

## ⚠️ Limitations & Future Improvements

### 🔹 Current Limitations

#### 📉 Limited Dataset Size
- **Current Data**: 89 merged daily records (~3 months of data)
- **Impact**: ML model trained on a small dataset (Holdout Test R² = 0.5141, MAE = 4.15 kWh, RMSE = 6.54 kWh)
- **Recommendation**: Collect 12+ months of historical data (365+ samples) for robust model generalization
- **Target**: Aim for 3+ years of data for seasonal pattern recognition

#### 📅 Seasonal Data Limitations
- **Gap**: Dataset covers limited seasons/weather patterns (predominantly dry season)
- **Missing**: 
  - Extreme weather events (heavy rain, storms)
  - Winter performance data
  - Temperature extremes (very hot/cold days)
  - Monsoon season variations
- **Effect**: Model may not generalize well to unseen seasonal patterns
- **Solution**: Expand dataset to cover all seasons across multiple years

#### 🎯 Model Scope Constraints
- **Current Features**: Base weather parameters + engineered interaction features
- **Missing Predictors**:
  - Cloud type classification (stratocumulus vs cirrus)
  - Atmospheric pressure and humidity
  - Solar panel surface temperature
  - Equipment efficiency degradation over time
  - Dust and soiling accumulation
  - Snow cover
- **Opportunity**: Incorporate hourly data for intra-day predictions

### 🔹 Future Enhancement Ideas

#### 🔷 Phase 1: Data & Model Improvements (High Priority)
1. **Expand Historical Dataset**
   - Collect 3+ years of daily records
   - Include multiple climate zones/seasons
   - Add extreme weather events documentation
   - Target: 1000+ samples for production-grade model

2. **Add Feature Engineering**
   - Day-of-year (captures seasonal cycles)
   - Moving averages (7-day, 30-day trends)
   - Lag features (yesterday's generation impact)
   - Weather gradients (rate of change)
   - Equipment age/degradation factor

3. **Model Upgrading**
   - Try XGBoost, LightGBM for better performance
   - Implement gradient boosting with time-series CV
   - A/B test ensemble methods (stacking, voting)
   - Hyperparameter tuning with grid/random search
   - Target: R² > 0.7 for production readiness

#### 🔷 Phase 2: Advanced Analytics (Medium Priority)
4. **Time-Series Forecasting**
   - Implement ARIMA/SARIMA for temporal patterns
   - Add Prophet for seasonal decomposition
   - Support multi-step ahead forecasting (7-14 day outlook)

5. **Anomaly Detection**
   - Identify equipment malfunctions via deviation analysis
   - Detect abnormal weather events
   - Alert system for critical underperformance

6. **Hourly-Level Predictions**
   - Migrate from daily to hourly predictions
   - Support 24-hour rolling forecasts
   - Optimize for grid demand matching

#### 🔷 Phase 3: Enterprise Features (Lower Priority)
7. **Real-Time Data Integration**
   - Connect to live weather APIs (OpenWeatherMap, WeatherAPI)
   - Stream predictions to IoT devices
   - Live generation monitoring dashboard

8. **Multi-Site Support**
   - Handle multiple solar installations
   - Location-specific model training
   - Regional performance comparison

9. **Advanced Visualizations**
   - 3D surface plots (radiation vs cloud vs generation)
   - Real-time prediction confidence intervals
   - Forecast accuracy heatmaps
   - ROI calculator for installations

10. **Deployment Optimization**
    - Model quantization for edge devices
    - API response optimization
    - Caching strategy for frequent predictions
    - Docker containerization

### 🔹 Expected Improvements by Phase

| Phase | Timeline | R² Score | MAE | Use Case |
|-------|----------|----------|-----|----------|
| Current | Now | 0.51 | 4.15 kWh | Prototype/PoC |
| Phase 1 | 3-4 months | 0.65-0.75 | 1.5-2.5 kWh | Production Ready |
| Phase 2 | 4-6 months | 0.80-0.85 | 0.8-1.2 kWh | Advanced Analytics |
| Phase 3 | 6-12 months | 0.85+ | <0.8 kWh | Enterprise Solution |

### 🔹 Recommended Priority Path
1. ✅ **Start**: Collect 12 months of clean historical data
2. ⏩ **Next**: Implement feature engineering (day-of-year, moving averages)
3. ⏩ **Then**: Retrain model with XGBoost on expanded dataset
4. ⏩ **Later**: Add time-series forecasting capabilities
5. ⏩ **Future**: Implement real-time integration and enterprise features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Om Patel**
- ✉️ Email: patelom2810@gmail.com
- 🔗 GitHub: [@patelom2810](https://github.com/patelom2810)

## 🤝 Acknowledgments

- ☀️ Solar energy data from [OpenMeteo API](https://open-meteo.com/)
- 📊 Chart visualization by [Chart.js](https://www.chartjs.org/)
- 🤖 ML framework by [Scikit-learn](https://scikit-learn.org/)

## 🚦 Status

- **Dashboard**: Prototype / Active
- **API Endpoints**: Fully Functional (with OpenAPI docs)
- **ML Model**: Validated & Tested (Gradient Boosting)
- **Database**: MySQL Connected (with indexes & connection pooling)
- **Documentation**: Complete
- **Docker Support**: Dockerfile & Docker Compose configured
- **Error Handling**: Structured logging & validation
- **Testing**: Unit tests with pytest (100% passing)

---

<div align="center">

### ⭐ If you find this project helpful, please consider giving it a star!

**[Dashboard (Local)](http://127.0.0.1:8000/dashboard)** | **[Predictor Form (Local)](http://127.0.0.1:8000/)** | **[API Docs (Local)](http://127.0.0.1:8000/api/docs)** | **[Health Check (Local)](http://127.0.0.1:8000/health)** | **[Report Issue](https://github.com/patelom2810/Solar-Energy-Generation-Weather-Analytics/issues)**

**Last Updated**: October 2026 | **Version**: 1.1.0 🚀 | **Status**: Prototype

</div>
