# Q5 Trading System - Phase 4 Deployment

This directory contains the deployment components for the Q5 Trading System, designed for automated trading on Solana.

## Directory Structure

```
📦 phase_4_deployment/
├── data_router/
│   ├── birdeye_scanner.py            # Detects new tokens with volume
│   ├── pumpfun_tracker.py            # Tracks pump.fun token launches
│   └── whale_watcher.py              # Helius-based whale alert system
├── rpc_execution/
│   ├── jito_executor.py              # Sends trades using Jito RPC
│   └── tx_builder.py                 # Builds transactions from signals
├── gui_dashboard/
│   ├── app.py                        # Streamlit GUI launcher
│   ├── components/
│   │   ├── strategy_viewer.py        # Strategy analysis component
│   │   ├── live_monitor.py           # Live trading monitor component
│   │   └── pnl_graphs.py             # PnL visualization component
├── core/
│   └── signal_enricher.py            # Adds metadata to final signals
├── output/                           # Output directory for logs and data
├── launch_all.sh                     # Master orchestrator script
├── run_simulation_test.sh            # End-to-End simulation test script
├── check_dependencies.py             # Dependency checker script
└── verify_simulation.py              # Simulation verification script
```

## Prerequisites

Before running the system, make sure you have the following:

1. Python 3.8+ installed
2. Required Python packages:
   ```
   pip install httpx pandas numpy plotly pyyaml streamlit solana
   ```
3. API keys for:
   - Birdeye API
   - Helius API
   - Jito RPC (optional for dry run)

## Deployment Steps

### Step 1: End-to-End Simulation Test (Dry Run)

This step simulates the entire flow from token detection to virtual execution without making any real transactions.

1. Check dependencies first:
   ```bash
   ./check_dependencies.py
   ```
   This will verify that all required Python packages are installed and provide instructions for installing any missing packages.

2. Set your API keys in `run_simulation_test.sh`:
   ```bash
   export BIRDEYE_API_KEY="your_birdeye_api_key"
   export HELIUS_API_KEY="your_helius_api_key"
   export JITO_RPC_URL="https://jito-api.example.com"
   export FALLBACK_RPC_URL="https://api.mainnet-beta.solana.com"
   ```

3. Run the simulation test:
   ```bash
   ./run_simulation_test.sh
   ```

4. Expected outputs:
   - `output/token_opportunities.json`: Detected tokens from Birdeye
   - `output/active_launches.json`: Active token launches from Pump.fun
   - `output/whale_opportunities.json`: Whale activities from Helius
   - `output/signals.json`: Sample trading signals
   - `output/enriched_signals.json`: Enriched signals with metadata
   - `output/execution_log.txt`: Simulated execution logs
   - `output/tx_history.json`: Simulated transaction history

5. Verify the simulation results:
   ```bash
   ./verify_simulation.py
   ```
   This will check all output files and verify that they contain valid data.

6. The script will also launch a Streamlit dashboard at http://localhost:8501 for visualization.

### Step 2: Live Execution Prep (After Successful Dry Run)

1. Configure a funded wallet in `wallet_sync/`
2. Update `tx_builder.py` to use the correct keypair
3. Set `DRY_RUN=false` in `launch_all.sh`
4. Run the full system:
   ```bash
   ./launch_all.sh
   ```

### Step 3: Live Trade Test on Test Tokens

1. Monitor the dashboard for new token opportunities
2. Adjust risk parameters in `core/signal_enricher.py`
3. Let the system execute trades automatically
4. Analyze execution performance and PnL

## Monitoring and Maintenance

- Check logs in the `output/` directory
- Monitor the dashboard for real-time updates
- Use `kill <PID>` to stop the dashboard process when needed

## Troubleshooting

- If API calls fail, check your API keys and rate limits
- If the dashboard doesn't launch, ensure Streamlit is installed
- If transactions fail, check wallet balance and RPC connection

## Security Notes

- Never commit API keys or private keys to version control
- Use environment variables or secure key management
- Test with small position sizes before scaling up

## Next Steps

After successful testing, consider:
1. Containerizing with Docker
2. Setting up monitoring with Grafana/Prometheus
3. Implementing the RL agent integration
4. Deploying to a VPS for 24/7 operation
