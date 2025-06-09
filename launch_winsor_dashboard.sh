#!/bin/bash

# Winsor Williams II - Hedge Fund Dashboard
# Simple one-click launcher

clear
echo "🏢 WILLIAMS CAPITAL MANAGEMENT"
echo "👤 Winsor Williams II - Hedge Fund Owner"
echo "🚀 Starting Professional Trading Dashboard..."
echo ""

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "node.*server.js" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
sleep 2

# Start API Server in background
echo "📡 Starting API Server..."
cd api-server
npm start > /dev/null 2>&1 &
sleep 3

# Start React Dashboard in background  
echo "🖥️  Starting React Dashboard..."
cd ../react-dashboard
npm start > /dev/null 2>&1 &
sleep 5

echo ""
echo "🎉 DASHBOARD SYSTEM READY!"
echo "=" * 50
echo "🏢 Williams Capital Management"
echo "👤 Winsor Williams II - Hedge Fund Owner"
echo ""
echo "📊 DASHBOARD: http://localhost:3000"
echo "🔧 API SERVER: http://localhost:8081"
echo ""
echo "✨ FEATURES:"
echo "   • Professional white interface"
echo "   • Real-time portfolio monitoring"  
echo "   • Executive-level metrics"
echo "   • MEV-protected trading"
echo "   • Mobile responsive design"
echo ""
echo "💡 Opening dashboard in browser..."
echo "=" * 50

# Open dashboard in browser
sleep 2
open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"

echo ""
echo "🎯 Dashboard is now running!"
echo "💼 Perfect for hedge fund portfolio management"
echo ""
echo "Press any key to stop all services..."
read -n 1

# Cleanup
echo ""
echo "🛑 Stopping services..."
pkill -f "node.*server.js" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
echo "✅ All services stopped"
echo "👋 Williams Capital Management Dashboard offline"
