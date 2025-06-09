#!/bin/bash
# Script to display trade metrics in the terminal

# Default values
METRICS_DIR="output/dashboard"
REFRESH_INTERVAL=1.0
MAX_TRADES=10

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --metrics-dir)
      METRICS_DIR="$2"
      shift 2
      ;;
    --refresh-interval)
      REFRESH_INTERVAL="$2"
      shift 2
      ;;
    --max-trades)
      MAX_TRADES="$2"
      shift 2
      ;;
    --live)
      METRICS_DIR="output/live_trade_test"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --metrics-dir DIR         Directory containing metrics files (default: output/dashboard)"
      echo "  --refresh-interval SEC    Refresh interval in seconds (default: 1.0)"
      echo "  --max-trades NUM          Maximum number of trades to display (default: 10)"
      echo "  --live                    Use live trade test metrics (shortcut for --metrics-dir output/live_trade_test)"
      echo "  --help                    Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Check if required packages are installed
echo "Checking required packages..."
python -c "import rich" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "Installing rich package..."
  pip install rich
fi

# Create output directories
mkdir -p "$METRICS_DIR"
mkdir -p "output/logs"

# Display ASCII art header
echo -e "\033[1;36m"
echo "  _____                                _____  "
echo " / ____|                              |___  | "
echo "| (___  _   _ _ __   ___ _ __ __ _ _   _  / / "
echo " \___ \| | | | '_ \ / _ \ '__/ _\` | | | |/ /  "
echo " ____) | |_| | | | |  __/ | | (_| | |_| / /   "
echo "|_____/ \__, |_| |_|\___|_|  \__, |\__, /_/    "
echo "         __/ |                __/ | __/ |      "
echo "        |___/                |___/ |___/       "
echo -e "\033[0m"
echo -e "\033[1;32mTrade Metrics Display\033[0m"
echo

# Run the metrics display
echo "Starting trade metrics display with metrics_dir: $METRICS_DIR"
echo "Press Ctrl+C to exit"
echo

# Change to the HedgeFund directory
cd "$(dirname "$0")"

# Run the Python script
python phase_4_deployment/scripts/display_trade_metrics.py \
  --metrics-dir "$METRICS_DIR" \
  --refresh-interval "$REFRESH_INTERVAL" \
  --max-trades "$MAX_TRADES"
