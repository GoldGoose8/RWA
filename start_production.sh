#!/bin/bash

# Williams Capital Management - Production Trading System Launcher
# Complete production environment for live trading and dashboard

clear
echo "🏢 WILLIAMS CAPITAL MANAGEMENT"
echo "👤 Winsor Williams II - Hedge Fund Owner"
echo "🚀 Starting Complete Production Trading System"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "scripts/unified_live_trading.py" ]; then
    print_error "Please run this script from the Synergy7 project root directory"
    exit 1
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    print_info "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    print_status "Environment variables loaded from .env"
else
    print_warning ".env file not found, checking system environment..."
fi

# Check environment variables
print_info "Checking environment configuration..."
if [ -z "$WALLET_ADDRESS" ] || [ -z "$HELIUS_API_KEY" ]; then
    print_error "Required environment variables not set"
    echo "Please ensure WALLET_ADDRESS and HELIUS_API_KEY are set in your .env file"
    echo "Current WALLET_ADDRESS: ${WALLET_ADDRESS:-'Not set'}"
    echo "Current HELIUS_API_KEY: ${HELIUS_API_KEY:-'Not set'}"
    exit 1
fi
print_status "Environment variables configured"

# Check if Python dependencies are available
print_info "Checking Python dependencies..."
python3 -c "import fastapi, uvicorn, httpx" 2>/dev/null
if [ $? -ne 0 ]; then
    print_error "Missing Python dependencies. Installing..."
    pip3 install fastapi uvicorn httpx
fi
print_status "Python dependencies available"

# Check if Node.js and npm are available
print_info "Checking Node.js and npm..."
if ! command -v npm &> /dev/null; then
    print_error "npm not found. Please install Node.js and npm"
    exit 1
fi
print_status "Node.js and npm available"

# Create logs directory
mkdir -p logs
print_status "Logs directory ready"

# Kill any existing processes
print_info "Cleaning up existing processes..."
pkill -f "unified_live_trading.py" 2>/dev/null || true
pkill -f "api_server.py" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
sleep 2
print_status "Cleanup completed"

# Function to start live trading
start_live_trading() {
    print_info "Starting live trading system..."
    python3 scripts/unified_live_trading.py > logs/live_trading.log 2>&1 &
    LIVE_TRADING_PID=$!
    sleep 5
    
    if ps -p $LIVE_TRADING_PID > /dev/null; then
        print_status "Live trading system started (PID: $LIVE_TRADING_PID)"
        return 0
    else
        print_error "Failed to start live trading system"
        return 1
    fi
}

# Function to start API server
start_api_server() {
    print_info "Starting API server..."
    python3 -c "
import sys
sys.path.append('.')
from phase_4_deployment.dashboard.api_server import start_api_server
start_api_server('0.0.0.0', 8081)
" > logs/api_server.log 2>&1 &
    API_SERVER_PID=$!
    sleep 5
    
    if ps -p $API_SERVER_PID > /dev/null; then
        print_status "API server started (PID: $API_SERVER_PID)"
        return 0
    else
        print_error "Failed to start API server"
        return 1
    fi
}

# Function to start React dashboard
start_react_dashboard() {
    print_info "Preparing React dashboard..."
    
    # Check if node_modules exists
    if [ ! -d "react-dashboard/node_modules" ]; then
        print_info "Installing React dependencies..."
        cd react-dashboard
        npm install
        cd ..
        print_status "React dependencies installed"
    fi
    
    print_info "Starting React dashboard..."
    cd react-dashboard
    REACT_APP_API_URL=http://localhost:8081 PORT=3000 BROWSER=none npm start > ../logs/react_dashboard.log 2>&1 &
    REACT_PID=$!
    cd ..
    sleep 10
    
    if ps -p $REACT_PID > /dev/null; then
        print_status "React dashboard started (PID: $REACT_PID)"
        return 0
    else
        print_error "Failed to start React dashboard"
        return 1
    fi
}

# Function to check service health
check_health() {
    print_info "Checking service health..."
    
    # Check API server
    if curl -s http://localhost:8081/health > /dev/null; then
        print_status "API server is healthy"
    else
        print_warning "API server health check failed"
    fi
    
    # Check React dashboard
    if curl -s http://localhost:3000 > /dev/null; then
        print_status "React dashboard is accessible"
    else
        print_warning "React dashboard health check failed"
    fi
}

# Function to display access information
show_access_info() {
    echo ""
    echo "="*80
    echo "🎉 PRODUCTION SYSTEM STARTED SUCCESSFULLY"
    echo "="*80
    echo "🏢 Williams Capital Management"
    echo "👤 Owner: Winsor Williams II"
    echo "💰 Wallet: $WALLET_ADDRESS"
    echo ""
    echo "📊 DASHBOARD ACCESS:"
    echo "   • Main Dashboard: http://localhost:3000"
    echo "   • API Server: http://localhost:8081"
    echo "   • Health Check: http://localhost:8081/health"
    echo "   • Live Metrics: http://localhost:8081/metrics"
    echo ""
    echo "🔄 SYSTEM STATUS:"
    echo "   • Live Trading: Running"
    echo "   • API Server: Running"
    echo "   • React Dashboard: Running"
    echo "   • Real-time Updates: Every 30 seconds"
    echo ""
    echo "🛡️ SECURITY FEATURES:"
    echo "   • MEV Protection: Jito Block Engine"
    echo "   • Bundle Execution: QuickNode Bundles"
    echo "   • RPC Fallbacks: Multiple endpoints"
    echo ""
    echo "📋 LOGS:"
    echo "   • Live Trading: logs/live_trading.log"
    echo "   • API Server: logs/api_server.log"
    echo "   • React Dashboard: logs/react_dashboard.log"
    echo ""
    echo "🔧 CONTROLS:"
    echo "   • Press Ctrl+C to stop all services"
    echo "   • View logs: tail -f logs/*.log"
    echo "="*80
    echo ""
}

# Function to cleanup on exit
cleanup() {
    echo ""
    print_info "Shutting down production system..."
    
    if [ ! -z "$LIVE_TRADING_PID" ]; then
        kill $LIVE_TRADING_PID 2>/dev/null || true
        print_status "Live trading system stopped"
    fi
    
    if [ ! -z "$API_SERVER_PID" ]; then
        kill $API_SERVER_PID 2>/dev/null || true
        print_status "API server stopped"
    fi
    
    if [ ! -z "$REACT_PID" ]; then
        kill $REACT_PID 2>/dev/null || true
        print_status "React dashboard stopped"
    fi
    
    # Kill any remaining processes
    pkill -f "unified_live_trading.py" 2>/dev/null || true
    pkill -f "api_server.py" 2>/dev/null || true
    pkill -f "react-scripts" 2>/dev/null || true
    
    print_status "Production system shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
echo "🚀 Starting production services..."
echo ""

# Start services in order
if start_live_trading && start_api_server && start_react_dashboard; then
    # Wait a moment for services to stabilize
    sleep 5
    
    # Check health
    check_health
    
    # Show access information
    show_access_info
    
    # Keep running until interrupted
    print_info "Production system is running. Press Ctrl+C to stop."
    while true; do
        sleep 1
    done
else
    print_error "Failed to start production system"
    cleanup
    exit 1
fi
