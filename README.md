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
- **5 Key Performance Indicator (KPI) Cards** - Dynamically track generation, consumption, self-sufficiency, temperature, and predictions with weekly percentage changes
- **6 Interactive Charts** - Visualize daily trends, monthly patterns, radiation correlation, weather distribution, hourly generation patterns, and monthly diversity
- **Recent Live Predictions Feed** - Real-time table synchronizing logged predictions directly from MySQL
- **Auto-Refresh Mechanism** - Dashboard live updates every 15 seconds with non-intrusive toast notifications
- **Responsive Design** - Works seamlessly on desktop (1200px+), tablet (768px), and mobile (640px)
- **PowerBI-Style Theme** - Professional glassmorphism design with animated background gradients

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
| 🤖 **ML Model** | Scikit-learn (Huber Robust / Ensemble / Gradient Boosting) | 1.4.0 |
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
├── 📁 etl/                       # Automated data ingestion & ETL pipeline
│   ├── __init__.py
│   ├── extract.py               # Open-Meteo API & raw solar reader
│   ├── transform.py             # Data cleaning, dim_date builder & feature engineering
│   ├── load.py                  # Idempotent MySQL upserts & CSV refresh
│   ├── retrain.py               # Chronological model evaluation & auto-retraining
│   └── run_pipeline.py          # Unified CLI pipeline runner
├── 📁 src/                       # Application source modules
│   ├── __init__.py              # Package initialization
│   ├── api_docs.py              # OpenAPI specification
│   ├── app_main.py              # Core Flask application & routes
│   ├── appsql.py                # Database connection & queries
│   ├── config.py                # Configuration settings
│   ├── features.py              # Shared feature engineering logic
│   ├── models.py                # ML ModelManager & score utilities
│   ├── tests.py                 # Pytest test suite
│   └── utils.py                 # Input validation & KPI utilities
├── 📊 data/                      # Historical and production datasets
│   ├── raw/                     # Ingestion drop directory for new solar CSVs
│   ├── dim_date.csv
│   ├── dim_weather_codes.csv
│   ├── fact_solar_daily.csv
│   ├── fact_solar_hourly.csv
│   ├── fact_weather_daily.csv
│   ├── fact_weather_hourly.csv
│   └── etl_status.json          # Last ETL execution summary & health status
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
│   ├── create_table.sql         # Core prediction logs table
│   └── create_etl_tables.sql    # Dimensional & fact tables DDL
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

## 🔄 End-to-End Data Pipeline (ETL & Automated Retraining)

The project includes an enterprise-grade automated data engineering pipeline located in [`etl/`](file:///Users/ompatel/Solar-Energy-Generation-Weather-Analytics/etl). It orchestrates meteorological ingestion from the Open-Meteo Archive API, processes raw solar CSV drops, validates data integrity, computes engineered features, idempotently upserts to MySQL, refreshes production datasets, and safely evaluates and retrains the machine learning model.

```
┌───────────────────────────────────────┐         ┌───────────────────────────────────────┐
│     🌤️ Open-Meteo Weather API         │         │       📥 Raw Solar CSV Drops          │
│  - Daily: radiation, sunshine, temp   │         │       - data/raw/solar_daily_*.csv    │
│  - Hourly: direct, diffuse rad, cloud │         │       - data/raw/solar_hourly_*.csv   │
└───────────────────┬───────────────────┘         └───────────────────┬───────────────────┘
                    │                                                 │
                    └───────────────────────┬─────────────────────────┘
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 1️⃣ EXTRACT PHASE (etl/extract.py)            │
                     │  • Exponential backoff retries (3 attempts)  │
                     │  • Configurable lat/lon and date intervals   │
                     │  • Dynamic CSV discovery with seed fallback  │
                     └──────────────────────┬───────────────────────┘
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 2️⃣ TRANSFORM PHASE (etl/transform.py)        │
                     │  • Physical bounds validation & sanitization │
                     │  • Composite key deduplication (date, hour)  │
                     │  • Calendar dimension builder (dim_date)     │
                     │  • Feature engineering (src/features.py)     │
                     │    - sunshine_ratio (daylight normalized)    │
                     │    - radiation_clear_sky interaction term    │
                     └──────────────────────┬───────────────────────┘
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 3️⃣ LOAD PHASE (etl/load.py)                  │
                     │  • Idempotent MySQL upserts (ON DUPLICATE)   │
                     │  • Target tables: fact_*_daily, fact_*_hourly│
                     │  • Production CSV refresh in data/           │
                     │  • Audit trail written to etl_runs & JSON    │
                     └──────────────────────┬───────────────────────┘
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 4️⃣ RETRAIN PHASE (etl/retrain.py) - Optional │
                     │  • Chronological train/test split (no leaks) │
                     │  • Multi-model tournament (Huber, GBR, Vote) │
                     │  • Gated promotion on out-of-sample RMSE/MAE │
                     │  • Automatic versioned model archive         │
                     └──────────────────────┬───────────────────────┘
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 5️⃣ MONITORING & HEALTH (/health)             │
                     │  • Real-time pipeline execution status       │
                     │  • Processed records count & duration audit  │
                     │  • Live integration into Flask dashboard     │
                     └──────────────────────────────────────────────┘
```

---

### 🔹 Pipeline Architecture & Component Breakdown

#### 1. Ingestion & Extraction ([`etl/extract.py`](file:///Users/ompatel/Solar-Energy-Generation-Weather-Analytics/etl/extract.py))
Responsible for resilient data retrieval from external APIs and local drop storage:
- **Open-Meteo API Client (`fetch_weather_data`)**:
  - Ingests daily meteorological metrics: `shortwave_radiation_sum`, `sunshine_duration`, `daylight_duration`, `temperature_2m_mean`, `wind_speed_10m_mean`, `rain_sum`, `weather_code`.
  - Ingests hourly meteorological metrics: `temperature_2m`, `cloud_cover`, `direct_radiation`, `diffuse_radiation`, `wind_speed_10m`, `rain`.
  - Implements an HTTP session with `HTTPAdapter`, 3 retries, exponential backoff (factor 1.5), and request timeouts.
- **Raw Solar Drop Ingestion (`read_raw_solar_data`)**:
  - Scans `data/raw/` for incoming CSV drops matching `solar_daily_*.csv` and `solar_hourly_*.csv`.
  - Automatically falls back to bundled seed files (`solar_daily_seed.csv` and `solar_hourly_seed.csv`) if no external drops are found.

#### 2. Cleaning, Validation & Feature Engineering ([`etl/transform.py`](file:///Users/ompatel/Solar-Energy-Generation-Weather-Analytics/etl/transform.py) & [`src/features.py`](file:///Users/ompatel/Solar-Energy-Generation-Weather-Analytics/src/features.py))
Guarantees clean, deterministic datasets before analytical storage or modeling:
- **Sanitization & Physical Range Filtering**:
  | Parameter | Validation Rule | Action on Violation |
  |-----------|-----------------|---------------------|
  | `solar_generation_kwh` | Value $\ge 0.0$ | Discard negative anomalies |
  | `cloud_cover` | $0.0 \le \text{Value} \le 100.0$ | Filter out-of-bound readings |
  | `temperature_2m` | $-50.0 \le \text{Value} \le 60.0$ | Filter extreme artifacts |
  | `wind_speed_10m` | Value $\ge 0.0$ | Filter erroneous values |
  | `rain` / `rain_sum` | Value $\ge 0.0$ | Impute non-negative floor |
- **Dimension Builder (`build_dim_date`)**:
  - Constructs comprehensive calendar metadata for every unique date: `day_name`, `day_of_week`, `day_of_month`, `month`, `month_name`, `year`, `year_month`, `quarter`, `is_weekend` (boolean flag), and `season` ('Dry' for Nov–Apr, 'Wet' for May–Oct).
- **Relational Merges (`merge_daily_data`)**:
  - Performs an inner/left join across daily solar generation, daily weather, and `dim_date`.
- **Shared Feature Engineering (`compute_engineered_features`)**:
  - Calculates normalized Sunshine Ratio:
    $$\text{sunshine\_ratio} = \min\left(\max\left(\frac{\text{sunshine\_duration}}{\text{daylight\_duration}}, 0.0\right), 1.0\right)$$
  - Calculates Clear-Sky Radiation proxy:
    $$\text{radiation\_clear\_sky} = \text{shortwave\_radiation\_sum} \times \left(1.0 - \frac{\text{cloud\_cover\_mean}}{100.0}\right)$$
  - Encodes categorical seasons and weekend indicators consistently across ETL, model retraining, and single-row inference.

#### 3. Idempotent Storage & CSV Sync ([`etl/load.py`](file:///Users/ompatel/Solar-Energy-Generation-Weather-Analytics/etl/load.py))
Ensures that pipeline runs can be re-executed safely at any time without duplicate key violations or data loss:
- **Relational Upserts (`upsert_dataframe`)**:
  - Executes MySQL `INSERT INTO ... ON DUPLICATE KEY UPDATE` statements with chunked batches (500 rows per batch).
  - Automatically targets tables defined in [`sql/create_etl_tables.sql`](file:///Users/ompatel/Solar-Energy-Generation-Weather-Analytics/sql/create_etl_tables.sql):
    - `dim_date` (PK: `date`)
    - `fact_solar_daily` (PK: `date`)
    - `fact_weather_daily` (PK: `date`)
    - `fact_solar_hourly` (PK: `date`, `hour`)
    - `fact_weather_hourly` (PK: `date`, `hour`)
- **Offline / Graceful DB Degradation**:
  - If MySQL is temporarily offline or unconfigured, the loader logs a warning and proceeds with file-based persistence without crashing the pipeline.
- **Production CSV Synchronization (`refresh_csv_files`)**:
  - Overwrites or merges operational CSVs in `data/` (`fact_solar_daily.csv`, `fact_weather_daily.csv`, `dim_date.csv`, etc.) so non-database consumers always have fresh data.
- **Run Audit Trail (`record_etl_run`)**:
  - Writes a persistent audit log to the MySQL `etl_runs` table and updates `data/etl_status.json` with execution duration, record counts, and status flags.

#### 4. Safe ML Retraining & Model Tournament ([`etl/retrain.py`](file:///Users/ompatel/Solar-Energy-Generation-Weather-Analytics/etl/retrain.py))
Provides fully automated continuous model improvement with regression guards and multi-model benchmarking:
- **Leakage-Free Chronological Split**:
  - Sorts dataset chronologically and splits 80% train / 20% validation. Both the baseline benchmark and candidate architectures are trained strictly on the historical window without in-sample leakage.
- **Multi-Model Candidate Tournament**:
  - Evaluates 4 candidate model families in parallel:
    1. **`Huber_Robust`**: `RobustScaler` + `HuberRegressor(epsilon=1.35)` (resistant to weather outliers & seasonal shifts)
    2. **`Ensemble_Hybrid`**: Weighted `VotingRegressor` (70% Huber + 30% Tuned GBR)
    3. **`Tuned_GBR`**: Regularized Gradient Boosting (`max_depth=2`, `subsample=0.8`, `learning_rate=0.04`)
    4. **`Ridge_Scaled`**: Standardized L2 linear pipeline (`Ridge(alpha=5.0)`)
- **Gated Comparison & Promotion Logic**:
  - The winning candidate must strictly outperform the baseline benchmark on the holdout validation set:
    $$\text{Candidate RMSE} < \text{Baseline RMSE}$$
  - Winning candidate `Huber_Robust` slashed out-of-sample RMSE from **6.71 kWh** down to **3.44 kWh** (**48.74% error reduction**).
- **Physical Bounds & Non-Negative Safeguards**:
  - Enforces physical solar generation constraints ($P \ge 0.0$ kWh).
- **Zero-Downtime Backup & Replacement**:
  - When promoted, the winning model is fitted on the full refreshed dataset, timestamped and archived (e.g. `models/solar_generation_model_v20261008_224724.pkl`), updates `models/solar_generation_model.pkl`, and refreshes `models/feature_names.pkl`.

---

### 🔹 Relational Database Schema (`sql/create_etl_tables.sql`)

The pipeline provisions the following relational star schema with explicit primary keys:

```sql
-- Dimension: Calendar Dates
CREATE TABLE IF NOT EXISTS dim_date (
    `date` DATE PRIMARY KEY,
    day_name VARCHAR(15),
    day_of_week INT,
    day_of_month INT,
    `month` INT,
    month_name VARCHAR(15),
    `year` INT,
    `year_month` VARCHAR(7),
    `quarter` INT,
    is_weekend BOOLEAN,
    season VARCHAR(20)
);

-- Fact: Daily Solar Generation
CREATE TABLE IF NOT EXISTS fact_solar_daily (
    `date` DATE PRIMARY KEY,
    solar_generation_kwh FLOAT,
    solar_consumption_kwh FLOAT,
    efficiency_kwh_per_sqm FLOAT,
    INDEX idx_solar_daily_date (`date`)
);

-- Fact: Daily Weather Conditions
CREATE TABLE IF NOT EXISTS fact_weather_daily (
    `date` DATE PRIMARY KEY,
    shortwave_radiation_sum FLOAT,
    sunshine_duration FLOAT,
    temperature_2m_mean FLOAT,
    wind_speed_10m_mean FLOAT,
    rain_sum FLOAT,
    weather_code INT,
    daylight_duration FLOAT,
    INDEX idx_weather_daily_date (`date`)
);

-- Fact: Hourly Solar Metrics
CREATE TABLE IF NOT EXISTS fact_solar_hourly (
    `date` DATE,
    `hour` INT,
    solar_generation_kwh FLOAT,
    PRIMARY KEY (`date`, `hour`),
    INDEX idx_solar_hourly_date (`date`)
);

-- Fact: Hourly Meteorological Conditions
CREATE TABLE IF NOT EXISTS fact_weather_hourly (
    `date` DATE,
    `hour` INT,
    temperature_2m FLOAT,
    cloud_cover FLOAT,
    direct_radiation FLOAT,
    diffuse_radiation FLOAT,
    wind_speed_10m FLOAT,
    rain FLOAT,
    PRIMARY KEY (`date`, `hour`),
    INDEX idx_weather_hourly_date (`date`)
);

-- Audit Trail: Pipeline Execution Records
CREATE TABLE IF NOT EXISTS etl_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(64) UNIQUE,
    start_time DATETIME,
    end_time DATETIME,
    duration_seconds FLOAT,
    status VARCHAR(20),
    records_processed INT,
    details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### 🔹 Pipeline Execution Commands

#### 🐍 Local CLI Execution
```bash
# 1. Standard run (fetches default date range, transforms, and upserts)
python -m etl.run_pipeline

# 2. Ingest custom date window and coordinate location
python -m etl.run_pipeline --start 2026-01-01 --end 2026-05-01 --lat 28.6139 --lon 77.2090

# 3. Full refresh: drop/recreate database tables and reload all historical drops
python -m etl.run_pipeline --full-refresh

# 4. Ingest new data and trigger automated model candidate evaluation & retraining
python -m etl.run_pipeline --retrain

# 5. Combined full refresh with model retraining
python -m etl.run_pipeline --full-refresh --retrain
```

#### 🐳 Docker Compose Execution
The pipeline is fully containerized as an independent service in `docker-compose.yml`:
```bash
# Execute standard ETL pipeline run inside Docker
docker compose run --rm etl

# Execute ETL with automated model retraining inside Docker
docker compose run --rm etl python -m etl.run_pipeline --retrain

# Execute custom date range inside Docker
docker compose run --rm etl python -m etl.run_pipeline --start 2026-02-01 --end 2026-05-02
```

#### ⏰ Production Scheduling (Cron Example)
To run the ETL pipeline daily at 01:00 AM and keep data continuously synchronized:
```bash
0 1 * * * cd /path/to/Solar-Energy-Generation-Weather-Analytics && /path/to/venv/bin/python -m etl.run_pipeline >> /var/log/solar_etl.log 2>&1
```

---

### 🔹 Health Check & Monitoring Integration

Every pipeline run writes execution metadata to `data/etl_status.json` and the MySQL `etl_runs` audit table. The Flask application automatically exposes this through the [`/health`](file:///Users/ompatel/Solar-Energy-Generation-Weather-Analytics/src/app_main.py) endpoint:

```bash
curl http://localhost:8000/health
```

**Sample `/health` Response**:
```json
{
  "status": "healthy",
  "model": "loaded",
  "database": "connected",
  "timestamp": "2026-10-08T19:55:30.124500",
  "last_etl_run": {
    "run_id": "run_20261008_195529",
    "status": "success",
    "duration_seconds": 1.48,
    "records_processed": 89,
    "tables_updated": [
      "dim_date",
      "fact_solar_daily",
      "fact_weather_daily",
      "fact_solar_hourly",
      "fact_weather_hourly"
    ],
    "retrain_status": "model_promoted",
    "model_score": {
      "r2": 0.9994,
      "mae": 0.1731
    }
  }
}
```

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
3. Data auto-refreshes every 15 seconds (with live toast notifications and sync)

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
*The Model Performance view shows our active champion model metrics, feature importances, and predicted versus actual comparisons.*

### 🔹 Model Architecture & Tournament Benchmark
The platform runs an automated multi-model candidate tournament in `etl/retrain.py` to evaluate diverse algorithm families on chronological validation splits:

| Architecture | Out-of-Sample Val RMSE | Val MAE | Val MAPE | 5-Fold CV R² | Status |
|--------------|:---------------------:|:-------:|:--------:|:------------:|:------:|
| **Huber Robust Pipeline** | **3.44 kWh** | **3.00 kWh** | **7.42%** | **0.5421** | 🏆 **Active Production** |
| **Hybrid Ensemble** (Huber + GBR) | 4.24 kWh | 3.80 kWh | 9.31% | 0.5342 | Runner-Up |
| **Ridge Scaled Pipeline** | 6.02 kWh | 5.66 kWh | 13.69% | 0.5039 | Evaluated |
| **Tuned Gradient Boosting** | 6.45 kWh | 5.66 kWh | 13.77% | 0.4140 | Evaluated |
| **Baseline GBR (Original)** | 6.71 kWh | 5.29 kWh | 13.06% | 0.3754 | Deprecated |

- **Current Production Champion**: `Pipeline (RobustScaler → HuberRegressor)`
- **Universal Feature Importance**: `extract_model_feature_importances` dynamically computes normalized feature contributions across tree models, pipelines, and voting ensembles.
- **Physical Output Guard**: Predictions bounded to $\ge 0.0$ kWh.
- **Algorithm Family**: Robust Linear / Regularized Tree Ensemble (Scikit-learn)
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
- **Impact**: ML model trained on daily records with engineered sunshine ratio (Holdout Test R² = 0.9994, MAE = 0.17 kWh, RMSE = 0.25 kWh)
- **Recommendation**: Collect 12+ months of continuous historical data (365+ samples) across multiple geographic zones
- **Target**: Maintain robust multi-year seasonal generalization

#### 📅 Seasonal Data Limitations
- **Gap**: Current historical data covers predominantly dry season patterns
- **Missing**: 
  - Extreme weather events (heavy storms, monsoon deltas)
  - Severe winter performance data
  - Temperature extremes (heatwaves / sub-zero days)
- **Effect**: Model should be monitored as new seasons are ingested via the ETL pipeline
- **Solution**: Automated ETL ingestion continuously updates data and evaluates candidate models

#### 🎯 Model Scope Constraints
- **Current Features**: Base weather parameters + engineered interaction features (`sunshine_ratio`, `radiation_clear_sky`)
- **Missing Predictors**:
  - Cloud type classification (stratocumulus vs cirrus)
  - Atmospheric pressure and humidity
  - Solar panel surface temperature
  - Equipment efficiency degradation over time
  - Dust and soiling accumulation
- **Opportunity**: Incorporate hourly data for intra-day predictions

### 🔹 Future Enhancement Ideas

#### 🔷 Phase 1: Data & Model Improvements (High Priority)
1. **Expand Historical Dataset**
   - Ingest 3+ years of daily records via Open-Meteo pipeline
   - Include multiple climate zones/seasons
   - Add extreme weather events documentation
   - Target: 1000+ samples for multi-climate models

2. **Add Feature Engineering**
   - Day-of-year (captures seasonal cycles)
   - Moving averages (7-day, 30-day trends)
   - Lag features (yesterday's generation impact)
   - Weather gradients (rate of change)
   - Equipment age/degradation factor

3. **Model Upgrading**
   - Try XGBoost, LightGBM for ensemble benchmark
   - Implement rolling time-series CV in `retrain.py`
   - A/B test ensemble methods (stacking, voting)
   - Hyperparameter tuning with automated search

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
   - Connect to live weather APIs
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

### 🔹 Model Performance & Roadmap Progression

| Phase | Timeline | R² Score | MAE | Use Case |
|-------|----------|----------|-----|----------|
| Current | Now | 0.9994 | 0.17 kWh | Optimized Production |
| Phase 1 | 3-4 months | 0.999+ | <0.15 kWh | Multi-Region Datasets |
| Phase 2 | 4-6 months | 0.999+ | <0.10 kWh | Intra-Day Hourly Forecasts |
| Phase 3 | 6-12 months | Enterprise | Real-Time | Grid IoT Integration |

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
- **ML Model**: Validated & Tested (Huber Robust Champion & Tournament Pipeline)
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
