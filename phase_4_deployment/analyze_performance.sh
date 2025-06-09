#!/bin/bash
# Analyze performance test results for Synergy7 Trading System

# Check if results file is provided
if [ $# -lt 1 ]; then
  echo "Usage: $0 RESULTS_FILE [--output OUTPUT_DIR] [--charts]"
  echo "Example: $0 output/load_tests/load_test_results_20230101_120000.json"
  exit 1
fi

RESULTS_FILE="$1"
shift

# Parse additional arguments
OUTPUT_DIR="output/performance_analysis"
CHARTS=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --charts)
      CHARTS=true
      shift
      ;;
    --help)
      echo "Usage: $0 RESULTS_FILE [options]"
      echo "Options:"
      echo "  --output DIR      Directory to store analysis results (default: output/performance_analysis)"
      echo "  --charts          Generate performance charts"
      echo "  --help            Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Make sure the script is executable
chmod +x phase_4_deployment/scripts/analyze_performance.py

# Run the analysis script
echo "Analyzing performance results: $RESULTS_FILE"
if [ "$CHARTS" = true ]; then
  python phase_4_deployment/scripts/analyze_performance.py "$RESULTS_FILE" --output "$OUTPUT_DIR" --charts
else
  python phase_4_deployment/scripts/analyze_performance.py "$RESULTS_FILE" --output "$OUTPUT_DIR"
fi

# Check exit code
if [ $? -eq 0 ]; then
  echo "Performance analysis completed successfully"
  exit 0
else
  echo "Performance analysis failed"
  exit 1
fi
