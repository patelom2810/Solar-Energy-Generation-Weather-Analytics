# ☀️ Solar Energy Analytics Dashboard

> **A modern, responsive solar energy analytics platform combining historical CSV data visualization with real-time ML prediction storage and real-time database retrieval.**

## 🌟 Features

### 📊 Real-Time Dashboard
- **5 Key Performance Indicator (KPI) Cards** - Track generation, consumption, efficiency, temperature, and predictions
- **5 Interactive Charts** - Visualize daily trends, monthly patterns, radiation correlation, weather distribution, and hourly generation patterns
- **Auto-Refresh Mechanism** - Data updates every 5 seconds for real-time insights
- **Responsive Design** - Works seamlessly on desktop (1200px+), tablet (768px), and mobile (640px)
- **PowerBI-Style Theme** - Professional white and baby blue color scheme with intuitive UI

### 🤖 ML-Powered Predictions
- **Solar Generation Forecasting** - Predict hourly energy generation based on weather parameters
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
- **Database Statistics** - Real-time prediction stats and historical tracking

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | Flask | 3.0.0 |
| **Runtime** | Python | 3.12 |
| **Database** | MySQL | 8.0+ |
| **Data Processing** | Pandas | 2.2.0 |
| **Numerical Computation** | NumPy | 1.26.4 |
| **ML Model** | Scikit-learn | 1.4.0 |
| **Model Persistence** | Joblib | 1.3.2 |
| **Charting** | Chart.js | 3.9.1 |
| **Frontend** | HTML5/CSS3/ES6+ | - |
| **Icons** | Font Awesome | 6.4.0 |

## 📦 Installation

### Prerequisites
- Python 3.12+
- MySQL 8.0+
- pip package manager

### 1️⃣ Clone Repository
```bash
git clone https://github.com/patelom2810/Solar-Energy-Generation-Weather-Analytics.git
cd solar_analytics
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
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=solar_analytics
DB_PORT=3306
FLASK_ENV=development
```

### 5️⃣ Initialize Database
```bash
# MySQL must be running
python3 -c "from appsql import init_db; init_db()"
```

### 6️⃣ Start Flask Server
```bash
python3 app.py
```
Server runs on `http://127.0.0.1:8000`

## 🚀 Usage

### Access Dashboard
1. Open browser: **http://127.0.0.1:8000/dashboard**
2. View real-time KPIs, charts, and prediction analytics
3. Data auto-refreshes every 5 seconds

### Make Predictions
1. Navigate to: **http://127.0.0.1:8000** (Predictor Form)
2. Fill in weather parameters:
   - ☀️ Shortwave Radiation (W/m²)
   - 🌤️ Sunshine Duration (seconds)
   - ☁️ Cloud Cover (0-100%)
   - 🌡️ Temperature 2m (°C)
   - 💨 Wind Speed 10m (m/s)
   - 💧 Rain Sum (mm)
   - 📍 Season (Dry/Wet)
   - 📅 Weekend (Yes/No)
3. Click **Predict** to generate forecast and store in database

### API Endpoints

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

#### 📈 Get Prediction History
```bash
GET /api/history?limit=100
```

#### 📊 Get Statistics
```bash
GET /api/stats
```

## 📊 Data Sources

### Historical Data (CSV)
- **fact_solar_daily.csv** - Daily solar generation and consumption data
- **fact_weather_daily.csv** - Daily weather conditions and parameters
- **fact_solar_hourly.csv** - Hourly generation patterns (24-hour cycles)
- **dim_date.csv** - Date dimension with season information
- **dim_weather_codes.csv** - Weather code reference data
- **fact_weather_hourly.csv** - Hourly weather data

### Database Schema
**prediction_logs table:**
```sql
CREATE TABLE prediction_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  prediction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  shortwave_radiation FLOAT,
  sunshine_duration FLOAT,
  cloud_cover FLOAT,
  temperature_2m FLOAT,
  wind_speed_10m FLOAT,
  rain FLOAT,
  is_weekend TINYINT(1),
  season VARCHAR(20),
  predicted_kwh FLOAT,
  actual_kwh FLOAT
)
```

## 🧠 ML Model

### Model Architecture
- **Algorithm**: Random Forest Regressor (Scikit-learn)
- **Training Data**: Historical solar generation with weather features
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

### Model Performance
```
✅ Test Results Across Various Scenarios:

Scenario              Prediction    Cloud    Temperature
────────────────────────────────────────────────────────
☀️ Perfect Sunny     38.13 kWh      5%       28.0°C
🌤️ Partly Cloudy    31.29 kWh     40%       26.0°C
☁️ Cloudy Day        26.75 kWh     70%       24.0°C
⛈️ Rainy Day         19.86 kWh     95%       22.0°C
🌅 Early Morning     22.02 kWh     20%       18.0°C
🏖️ Optimal (Weekend) 43.64 kWh     10%       27.5°C

Average: 30.28 kWh | Range: 19.86 - 43.64 kWh | StdDev: 9.28 kWh
```

### Key Insights
- ✓ **Cloud Impact**: Clear skies average **42.02 kWh** vs cloudy **25.41 kWh**
- ✓ **Seasonal Pattern**: Dry season averages **37.02 kWh** vs wet **25.41 kWh**
- ✓ **Temperature Correlation**: Warm days (25-30°C) generate more consistently
- ✓ **Weather Sensitivity**: Model accurately responds to all weather parameters

## 📁 Project Structure

```
solar_analytics/
├── app.py                          # Flask backend & API routes
├── appsql.py                       # MySQL database layer
├── config.py                       # Configuration management
├── solar_generation_model.pkl      # Trained ML model
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
├── README.md                       # This file
├── data/
│   ├── fact_solar_daily.csv       # Historical daily solar data
│   ├── fact_weather_daily.csv     # Historical weather data
│   ├── fact_solar_hourly.csv      # Hourly generation patterns
│   ├── dim_date.csv               # Date dimensions
│   ├── dim_weather_codes.csv      # Weather code reference
│   └── fact_weather_hourly.csv    # Hourly weather data
├── models/
│   └── (ML model training scripts)
├── notebooks/
│   ├── 01_EDA.ipynb              # Exploratory data analysis
│   └── 02_Modelling.ipynb        # Model training & validation
├── sql/
│   └── create_table.sql          # Database schema
└── templates/
    ├── dashboard.html             # Main analytics dashboard
    └── index.html                 # Predictor form
```

## 🔧 Configuration

### Environment Variables (`.env`)
```env
# MySQL Configuration
DB_HOST=localhost              # MySQL server host
DB_USER=root                   # MySQL username
DB_PASSWORD=password           # MySQL password
DB_NAME=solar_analytics        # Database name
DB_PORT=3306                   # MySQL port

# Flask Configuration
FLASK_ENV=development          # development/production
```

### Flask Settings (`app.py`)
```python
app.run(
  debug=False,                 # Debug mode disabled for stability
  port=8000,                   # Port number
  host='0.0.0.0',             # Listen on all interfaces
  threaded=True                # Enable threading for concurrent requests
)
```

## 🐛 Troubleshooting

### MySQL Connection Issues
```bash
# Check MySQL is running
brew services list | grep mysql

# Start MySQL if not running
brew services start mysql

# Verify credentials in .env file
# Test connection: mysql -h localhost -u root -p
```

### Port 8000 Already in Use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port in app.py
```

### CSV Data Not Loading
```bash
# Verify data files exist in /data directory
ls -lah data/

# Check CSV format (UTF-8 encoding recommended)
file data/*.csv
```

### Database Table Not Found
```bash
# Reinitialize database
python3 -c "from appsql import init_db; init_db()"

# Verify MySQL connection and privileges
mysql -u root -p solar_analytics
SHOW TABLES;
```

## 🚀 Deployment

### Production Deployment
```bash
# Use Gunicorn for production
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Or use with Supervisor for process management
```

### Docker Deployment
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

## 📊 Prediction Accuracy Metrics

```
Database Analysis (10+ Predictions Stored):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Predictions:     10
Average Generation:    34.70 kWh
Range:                 23.97 - 43.76 kWh
Standard Deviation:    7.62 kWh

By Season:
  Dry:   8 predictions, Avg 37.02 kWh
  Wet:   2 predictions, Avg 25.41 kWh

By Cloud Cover:
  Clear (0-20%):   5 preds, Avg 42.02 kWh
  Partly (20-40%): 1 pred,  Avg 30.61 kWh
  Mostly (40-60%): 2 preds, Avg 27.74 kWh
  Cloudy (60-80%): 2 preds, Avg 25.41 kWh
```

## 🎨 UI/UX Features

### 🎭 Design System
- **Color Palette**: White (#f8fafc), Baby Blue (#0ea5e9), Sky Blue (#06b6d4)
- **Typography**: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI)
- **Spacing**: 8px base unit for consistent rhythm
- **Shadows**: Subtle shadows for depth perception
- **Animations**: Smooth transitions and loading states

### 📱 Responsive Breakpoints
- **Desktop**: 1200px+ (Full layout with sidebar)
- **Tablet**: 768px - 1200px (Optimized 2-column grids)
- **Mobile**: < 640px (Single column, horizontal navigation)

### ♿ Accessibility
- Semantic HTML5 structure
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast text for readability
- Font Awesome icons with text labels

## 📚 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [Scikit-learn Regression](https://scikit-learn.org/stable/modules/ensemble.html#random-forests)
- [MySQL Python Connector](https://dev.mysql.com/doc/connector-python/en/)

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👤 Author

**Om Patel**
- 📧 Email: patelom2810@gmail.com
- 🔗 GitHub: [@patelom2810](https://github.com/patelom2810)

## 🙏 Acknowledgments

- ☀️ Solar energy data from [OpenMeteo API](https://open-meteo.com/)
- 📊 Chart visualization by [Chart.js](https://www.chartjs.org/)
- 🎨 Icons by [Font Awesome](https://fontawesome.com/)
- 🤖 ML framework by [Scikit-learn](https://scikit-learn.org/)

## 🚦 Status

✅ **Dashboard**: Production Ready  
✅ **API Endpoints**: Fully Functional  
✅ **ML Model**: Validated & Tested  
✅ **Database**: MySQL Connected  
✅ **Documentation**: Complete  

---

<div align="center">

### ⭐ If you find this project helpful, please consider giving it a star!

**[View Live Dashboard](http://127.0.0.1:8000/dashboard)** | **[Report Issue](https://github.com/patelom2810/Solar-Energy-Generation-Weather-Analytics/issues)** | **[Make Prediction](http://127.0.0.1:8000/)**

**Last Updated**: May 2026 | **Version**: 1.0.0 🚀

</div>
