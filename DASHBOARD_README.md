# Solar Energy Analytics Dashboard

## Overview
A modern, responsive web-based dashboard for visualizing solar energy generation, consumption, and machine learning predictions. Built with Flask, Chart.js, and modern HTML5/CSS3.

## Features Implemented

### 1. **Dashboard Routes**
- `GET /` - Home page (index.html)
- `GET /dashboard` - Modern analytics dashboard
- `GET /api/dashboard-data` - API endpoint returning all dashboard data
- `POST /predict` - ML prediction endpoint
- `GET /history` - Prediction history
- `GET /stats` - Prediction statistics

### 2. **KPI Cards (Section 1)**
- ✅ Total Solar Generation (kWh)
- ✅ Total Consumption (kWh)
- ✅ Self Sufficiency %
- ✅ Average Temperature (°C)
- ✅ Total Predictions Made
- ✅ Change indicators with trend arrows

### 3. **Historical CSV Analytics (Section 2)**

#### Data Sources
- `fact_solar_daily.csv` - Daily generation, consumption, grid data
- `fact_weather_daily.csv` - Daily weather metrics and codes
- `fact_solar_hourly.csv` - Hourly generation and consumption

#### Charts Created
1. **Daily Generation vs Consumption** (Line Chart)
   - Last 30 days of data
   - Dual axis for generation and consumption
   
2. **Monthly Generation vs Consumption** (Bar Chart)
   - Last 12 months aggregated
   - Side-by-side bar comparison

3. **Radiation vs Generation** (Scatter Chart)
   - Correlation between radiation and generation
   - Helps identify relationship patterns

4. **Weather Distribution** (Doughnut Chart)
   - Distribution by weather codes
   - Color-coded segments

5. **Hourly Generation Pattern** (Area/Line Chart)
   - Average hourly pattern over time
   - Shows daily generation cycle

### 4. **Live Prediction Analytics (Section 3)**
- ✅ Latest predicted kWh value
- ✅ Prediction timestamp
- ✅ Weather inputs used (cloud cover, temperature)
- ✅ Prediction status (Normal/Low/High)
- ✅ Auto-refresh every 5 seconds
- ✅ Prediction logs table (last 10 predictions)
- ✅ Recent predictions trend chart

### 5. **UI/UX Design (Section 4)**
- ✅ **Dark Modern Theme** - Deep blue gradient background
- ✅ **Glassmorphism** - Frosted glass effect cards with backdrop blur
- ✅ **Responsive Layout** - Works on desktop, tablet, mobile
- ✅ **Sidebar Navigation** - Quick access to sections
- ✅ **Smooth Animations** - Hover effects, fade-ins, spin animations
- ✅ **Professional Analytics** - Business-ready appearance
- ✅ **Status Indicators** - Live/Offline status badge with pulse animation
- ✅ **Color Scheme**:
  - Primary: Cyan (#00d4ff)
  - Secondary: Lime Green (#00ff88)
  - Accent: Red (#ff6b6b), Gold (#ffd93d)
  - Background: Dark Navy (#0f172a)

## File Structure
```
/Users/ompatel/solar_analytics/
├── templates/
│   └── dashboard.html          # Modern analytics dashboard (1200+ lines)
├── app.py                       # Flask backend with API routes
├── appsql.py                    # Database interaction layer
├── config.py                    # Configuration
├── requirements.txt             # Python dependencies
├── data/
│   ├── fact_solar_daily.csv
│   ├── fact_weather_daily.csv
│   ├── fact_solar_hourly.csv
│   └── dim_date.csv
└── models/
    ├── solar_generation_model.pkl
    └── feature_names.pkl
```

## How to Use

### 1. Start the Flask Server
```bash
cd /Users/ompatel/solar_analytics
source venv/bin/activate
python app.py
```
Server will run on: `http://127.0.0.1:8000`

### 2. Access the Dashboard
```
http://127.0.0.1:8000/dashboard
```

### 3. API Endpoints

#### Get Dashboard Data
```bash
curl http://127.0.0.1:8000/api/dashboard-data
```
Returns: KPIs, daily data, monthly data, radiation data, weather distribution, hourly data

#### Get Prediction History
```bash
curl http://127.0.0.1:8000/history?limit=20
```

#### Get Prediction Statistics
```bash
curl http://127.0.0.1:8000/stats
```

#### Make a Prediction
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "shortwave_radiation_sum": 24.0,
    "sunshine_duration": 38000,
    "cloud_cover_mean": 30.0,
    "temperature_2m_mean": 26.0,
    "wind_speed_10m_mean": 18.0,
    "rain_sum": 0.0,
    "season": "Dry",
    "is_weekend": false
  }'
```

## Technical Stack

### Backend
- **Flask** - Web framework
- **Pandas** - Data processing and CSV handling
- **NumPy** - Numerical computations
- **scikit-learn** - Machine learning
- **joblib** - Model serialization
- **MySQL** - Database (for predictions logging)

### Frontend
- **HTML5** - Semantic structure
- **CSS3** - Modern styling with gradients, glassmorphism
- **JavaScript (ES6+)** - Dynamic interactions and auto-refresh
- **Chart.js** - Data visualization library
- **Fetch API** - Real-time data loading

### DevOps
- **Gunicorn** - Production WSGI server (optional)
- **python-dotenv** - Environment variable management

## Performance Features

### Caching
- CSV data cached for 5 minutes to reduce I/O
- Auto-refreshes dashboard data every 5 seconds

### Error Handling
- Graceful degradation if database unavailable
- Detailed error logging for debugging
- Timeout handling for long-running requests

### Responsive Design
- Mobile-first approach
- Breakpoints at 1200px, 768px, 640px
- Sidebar collapses on smaller screens
- Touch-friendly navigation

## Data Processing Pipeline

1. **Load CSV Files** → Pandas DataFrames
2. **Date Conversion** → Standardized datetime objects
3. **Data Merging** → Join solar and weather data on date
4. **Aggregations** → Monthly/hourly summaries
5. **Calculations** → KPIs, trends, statistics
6. **JSON Serialization** → API response

## Customization Guide

### Change Refresh Interval
In `dashboard.html`, line 1011:
```javascript
refreshInterval: 5000, // milliseconds
```

### Change Colors
In `dashboard.html`, lines 27-34:
```javascript
const colors = {
    accent1: '#00d4ff',  // Cyan
    accent2: '#00ff88',  // Green
    // ...
};
```

### Add New KPI Card
1. Add HTML card in Section 1
2. Add state variable in JavaScript
3. Update `updateKPIs()` function
4. Add calculation in API endpoint

### Add New Chart
1. Create canvas element in HTML
2. Initialize Chart.js instance
3. Add data fetching in `updateCharts()`
4. Add calculation in API endpoint

## Troubleshooting

### Port Already in Use
```bash
lsof -i :8000 | awk 'NR==2 {print $2}' | xargs kill -9
```

### Database Connection Errors
The dashboard handles this gracefully - predictions will show 0 if database is unavailable.

### Slow Data Loading
- Check CSV file sizes
- Verify system memory
- Consider using MySQL for data storage instead of CSV

### Charts Not Displaying
- Check browser console for JavaScript errors
- Verify Chart.js CDN is accessible
- Check API response format

## Future Enhancements

- [ ] Real-time data streaming via WebSocket
- [ ] User authentication and multi-user support
- [ ] Data export to Excel/PDF
- [ ] Prediction model comparison
- [ ] Advanced filtering and date range selection
- [ ] Mobile app version
- [ ] Predictive alerts and notifications
- [ ] Integration with weather APIs

## License
Proprietary - Solar Analytics Dashboard

## Support
For issues or questions, check the logs at `/tmp/flask.log`
