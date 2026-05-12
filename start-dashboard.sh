#!/bin/bash
# Quick Start - Solar Energy Analytics Dashboard

echo "🚀 Starting Solar Energy Analytics Dashboard..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create it first:"
    echo "   python -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Kill any existing Flask processes
pkill -f "python app.py" 2>/dev/null
sleep 1

# Start Flask server
echo "📡 Starting Flask server on http://127.0.0.1:8000"
python app.py &

# Wait for server to start
sleep 3

# Check if server is running
if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
    echo "✅ Flask server started successfully!"
    echo ""
    echo "📊 Dashboard URLs:"
    echo "   - Home:              http://127.0.0.1:8000/"
    echo "   - Analytics:         http://127.0.0.1:8000/dashboard"
    echo ""
    echo "🔗 API Endpoints:"
    echo "   - Dashboard Data:    http://127.0.0.1:8000/api/dashboard-data"
    echo "   - Prediction History: http://127.0.0.1:8000/history"
    echo "   - Statistics:        http://127.0.0.1:8000/stats"
    echo ""
    echo "📝 Logs available at: /tmp/flask.log"
    echo ""
    echo "To stop the server: pkill -f 'python app.py'"
else
    echo "❌ Failed to start Flask server"
    echo "Check logs: tail -50 /tmp/flask.log"
    exit 1
fi
