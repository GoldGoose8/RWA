#!/bin/bash

# Williams Capital Management - Complete Dashboard Launcher
# Winsor Williams II - Hedge Fund Owner Dashboard
# Professional React Dashboard with Live Trading Integration

echo "🏢 WILLIAMS CAPITAL MANAGEMENT"
echo "👤 Winsor Williams II - Hedge Fund Owner"
echo "🚀 Professional Trading Dashboard System"
echo "=" * 60

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    echo "🔄 Cleaning up port $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Clean up any existing processes
echo "🧹 Cleaning up existing processes..."
kill_port 3000  # React dashboard
kill_port 8081  # API server
kill_port 8501  # Streamlit dashboard
kill_port 8502  # Alternative Streamlit port

# Wait for cleanup
sleep 3

echo ""
echo "🚀 Starting Williams Capital Management Dashboard System..."
echo ""

# Start API Server
echo "1️⃣ Starting API Server (Port 8081)..."
cd /Users/wallc/Downloads/Synergy7-main/api-server
npm start &
API_PID=$!
sleep 3

# Check if API server started successfully
if check_port 8081; then
    echo "   ✅ API Server running on http://localhost:8081"
else
    echo "   ❌ Failed to start API Server"
    exit 1
fi

# Start React Dashboard
echo ""
echo "2️⃣ Starting React Dashboard (Port 3000)..."
cd /Users/wallc/Downloads/Synergy7-main/react-dashboard
npm start &
REACT_PID=$!
sleep 5

# Check if React dashboard started successfully
if check_port 3000; then
    echo "   ✅ React Dashboard running on http://localhost:3000"
else
    echo "   ❌ Failed to start React Dashboard"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 DASHBOARD SYSTEM FULLY OPERATIONAL!"
echo "=" * 60
echo "🏢 Williams Capital Management"
echo "👤 Owner: Winsor Williams II"
echo "💼 Type: Hedge Fund"
echo ""
echo "📊 DASHBOARD ACCESS:"
echo "   🖥️  Professional Dashboard: http://localhost:3000"
echo "   🔧 API Server: http://localhost:8081"
echo ""
echo "✨ FEATURES:"
echo "   ✅ Real-time portfolio monitoring"
echo "   ✅ Professional hedge fund interface"
echo "   ✅ Clean white design for executives"
echo "   ✅ Live trading metrics"
echo "   ✅ MEV protection status"
echo "   ✅ Risk management overview"
echo "   ✅ Performance analytics"
echo ""
echo "🛡️ SECURITY:"
echo "   ✅ MEV-protected trading"
echo "   ✅ Jito Block Engine integration"
echo "   ✅ Multi-RPC redundancy"
echo "   ✅ Real-time system monitoring"
echo ""
echo "=" * 60
echo "💡 Press Ctrl+C to stop all services"
echo "📱 Dashboard optimized for hedge fund owners"
echo "🎯 Focus on high-level metrics and performance"

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Williams Capital Management Dashboard..."
    echo "   Stopping React Dashboard..."
    kill $REACT_PID 2>/dev/null
    echo "   Stopping API Server..."
    kill $API_PID 2>/dev/null
    
    # Force kill any remaining processes
    kill_port 3000
    kill_port 8081
    
    echo "✅ All services stopped"
    echo "👋 Williams Capital Management Dashboard offline"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep script running and monitor processes
while true; do
    # Check if processes are still running
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "⚠️ API Server stopped unexpectedly"
        cleanup
    fi
    
    if ! kill -0 $REACT_PID 2>/dev/null; then
        echo "⚠️ React Dashboard stopped unexpectedly"
        cleanup
    fi
    
    sleep 10
done
