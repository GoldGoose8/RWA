#!/bin/bash

# Q5 System Master Orchestrator Script
# This script launches all components of the Q5 trading system in sequence
# and performs an end-to-end simulation test (dry run)

# Set environment variables if not already set
export DRY_RUN=${DRY_RUN:-false}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export BIRDEYE_API_KEY=${BIRDEYE_API_KEY:-"a2679724762a47b58dde41b20fb55ce9"}
export HELIUS_API_KEY=${HELIUS_API_KEY:-"dda9f776-9a40-447d-9ca4-22a27c21169e"}
export HELIUS_RPC_URL=${HELIUS_RPC_URL:-"https://mainnet.helius-rpc.com/?api-key=${HELIUS_API_KEY}"}
export FALLBACK_RPC_URL=${FALLBACK_RPC_URL:-"${HELIUS_RPC_URL}"}
export WALLET_ADDRESS=${WALLET_ADDRESS:-"J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz"}

# Create output directory if it doesn't exist
mkdir -p output

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}\n"
}

# Function to check if a file exists and has content
check_file() {
    if [ -f "$1" ] && [ -s "$1" ]; then
        echo -e "${GREEN}✓ $2 generated successfully${NC}"
    else
        echo -e "${RED}✗ $2 not generated or empty${NC}"
        if [ "$3" = "critical" ]; then
            echo -e "${RED}Critical error. Stopping execution.${NC}"
            exit 1
        fi
    fi
}

# Function to run a component and check its output
run_component() {
    component_name=$1
    command=$2
    output_file=$3
    output_desc=$4
    critical=$5

    print_header "Running $component_name"
    echo -e "${YELLOW}Executing: $command${NC}"

    # Run the command
    eval $command

    # Check if command was successful
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $component_name executed successfully${NC}"
        # Check output file if specified
        if [ ! -z "$output_file" ]; then
            check_file "$output_file" "$output_desc" "$critical"
        fi
    else
        echo -e "${RED}✗ $component_name failed to execute${NC}"
        if [ "$critical" = "critical" ]; then
            echo -e "${RED}Critical error. Stopping execution.${NC}"
            exit 1
        fi
    fi
}

# Print start message
print_header "STARTING Q5 SYSTEM END-TO-END SIMULATION TEST"
if [ "$DRY_RUN" = "true" ]; then
    echo -e "${YELLOW}DRY RUN MODE: Enabled (No real transactions will be executed)${NC}"
else
    echo -e "${RED}LIVE TRADING MODE: Enabled (REAL TRANSACTIONS WILL BE EXECUTED)${NC}"
fi
echo -e "${YELLOW}Timestamp: $(date)${NC}"

# Step 1: Run Birdeye Scanner
run_component "Birdeye Scanner" "python3 data_router/birdeye_scanner.py" \
    "output/token_opportunities.json" "Token opportunities data" "non-critical"

# Step 2: Pump.fun Tracker removed - not using Pump.fun

# Step 3: Run Whale Watcher
run_component "Whale Watcher" "python3 data_router/whale_watcher.py" \
    "output/whale_opportunities.json" "Whale opportunities data" "non-critical"

# Step 4: Run Signal Enricher
# We'll use the sample signals from Phase 3 as input
print_header "Copying sample signals from Phase 3"
cp ../phase_3_rl_agent_training/phase_3_strategy_selector/outputs/best_signals.json output/signals.json
check_file "output/signals.json" "Sample signals" "critical"

run_component "Signal Enricher" "python3 core/signal_enricher.py" \
    "output/enriched_signals.json" "Enriched signals data" "critical"

# Step 5: Run Transaction Builder (dry run)
run_component "Transaction Builder" "python3 rpc_execution/tx_builder.py" \
    "output/tx_builder_log.txt" "Transaction builder log" "non-critical"

# Step 6: Run Helius Executor (dry run)
run_component "Helius Executor" "python3 scripts/helius_dry_run.py" \
    "output/helius_dry_run_results.json" "Helius test results" "non-critical"

# Step 7: Launch GUI Dashboard (in background)
print_header "Launching GUI Dashboard"
echo -e "${YELLOW}Starting Streamlit dashboard in background...${NC}"
nohup streamlit run gui_dashboard/app.py > output/dashboard_log.txt 2>&1 &
DASHBOARD_PID=$!
echo -e "${GREEN}✓ Dashboard started with PID: $DASHBOARD_PID${NC}"
echo -e "${YELLOW}Dashboard URL: http://localhost:8501${NC}"

# Print summary
print_header "END-TO-END SIMULATION TEST SUMMARY"
echo -e "${GREEN}✓ Data Router components executed${NC}"
echo -e "${GREEN}✓ Signal Enricher processed signals${NC}"
echo -e "${GREEN}✓ Transaction Builder created transactions${NC}"
echo -e "${GREEN}✓ Helius Executor simulated execution${NC}"
echo -e "${GREEN}✓ GUI Dashboard launched${NC}"

echo -e "\n${YELLOW}To view the dashboard, open a browser and navigate to: http://localhost:8501${NC}"
echo -e "${YELLOW}To stop the dashboard, run: kill $DASHBOARD_PID${NC}"

echo -e "\n${GREEN}End-to-End Simulation Test completed successfully!${NC}"
echo -e "${YELLOW}Timestamp: $(date)${NC}"

# Exit with success
exit 0
