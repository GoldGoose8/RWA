#!/bin/bash
# Run all tests for the Q5 System

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print header
function print_header() {
    echo -e "\n${YELLOW}======================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}======================================${NC}\n"
}

# Print success message
function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print error message
function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if running in Docker container
if [ ! -f "/.dockerenv" ]; then
    echo -e "${YELLOW}This script should be run inside the Docker container.${NC}"
    echo -e "${YELLOW}Run it with: docker exec -it q5_trading_bot /app/tests/run_all_tests.sh${NC}"
    exit 1
fi

# Make sure we're in the right directory
cd /app

# Make all test scripts executable
chmod +x /app/tests/*.py

# Create output directory if it doesn't exist
mkdir -p /app/output

print_header "Running Q5 System Tests"

# Run GUI Dashboard test
print_header "Testing GUI Dashboard"
python3 /app/tests/test_gui_dashboard.py
if [ $? -eq 0 ]; then
    print_success "GUI Dashboard test passed"
else
    print_error "GUI Dashboard test failed"
fi

# Run Birdeye API test
print_header "Testing Birdeye API"
python3 /app/tests/test_birdeye_api.py
if [ $? -eq 0 ]; then
    print_success "Birdeye API test passed"
else
    print_error "Birdeye API test failed"
fi

# Run Whale Watcher test
print_header "Testing Whale Watcher"
python3 /app/tests/test_whale_watcher.py
if [ $? -eq 0 ]; then
    print_success "Whale Watcher test passed"
else
    print_error "Whale Watcher test failed"
fi

# Run Helius integration test
print_header "Testing Helius Integration"
python3 /app/scripts/helius_dry_run.py
if [ $? -eq 0 ]; then
    print_success "Helius integration test passed"
else
    print_error "Helius integration test failed"
fi

# Run test trade
print_header "Testing Trade Execution"
python3 /app/scripts/test_trade.py
if [ $? -eq 0 ]; then
    print_success "Trade execution test passed"
else
    print_error "Trade execution test failed"
fi

# Restart the dashboard
print_header "Restarting Dashboard"
pkill -f "streamlit run" || true
nohup streamlit run /app/gui_dashboard/app.py > /app/output/streamlit.log 2>&1 &
if [ $? -eq 0 ]; then
    print_success "Dashboard restarted successfully"
    echo -e "${GREEN}Dashboard URL: http://localhost:8501${NC}"
else
    print_error "Failed to restart dashboard"
fi

print_header "Test Summary"
echo -e "${GREEN}All tests completed.${NC}"
echo -e "${YELLOW}Check the logs for detailed results.${NC}"
echo -e "${YELLOW}Dashboard URL: http://localhost:8501${NC}"
