# Synergy7 Trading System Production Deployment Guide

This guide provides instructions for deploying the Synergy7 Trading System to production with Jito Bundle execution and Orca DEX integration.

## Prerequisites

Before deploying to production, ensure you have the following:

1. **API Keys**:
   - Helius API key (for non-trading operations and whale watching)
   - Birdeye API key (for market data and whale detection)
   - Jito Bundle API access (for MEV-protected trading)
   - (Optional) Fallback API keys for redundancy

2. **Wallet**:
   - Solana wallet keypair file with Ed25519 format
   - Sufficient SOL balance for transactions (minimum 1 SOL recommended)
   - Secure storage for the keypair file with 600 permissions
   - Wallet address configured in .env file

3. **Environment**:
   - Docker and Docker Compose installed (optional)
   - Rust toolchain (for building Carbon Core and Solana TX Utils)
   - Python 3.9+ with required packages
   - Virtual environment (venv or conda) recommended

4. **Configuration**:
   - Production configuration file (config.yaml)
   - Environment variables file (.env)
   - Orca DEX configuration (config/orca_config.yaml)
   - Token registry configuration (config/token_registry.yaml)

## Deployment Steps

### 1. Prepare Configuration

1. **Set up environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   ```

2. **Edit environment variables**:
   ```bash
   nano .env
   ```

   Update the following variables:
   - `HELIUS_API_KEY`: Your Helius API key for whale watching and data collection
   - `BIRDEYE_API_KEY`: Your Birdeye API key for market data
   - `WALLET_ADDRESS`: Your wallet address (single source of truth)
   - `KEYPAIR_PATH`: Path to your wallet keypair file
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token for alerts
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID (e.g., 5135869709)
   - `JITO_BUNDLE_ENABLED`: Set to true for MEV protection
   - `ORCA_DEX_ENABLED`: Set to true for Orca DEX integration

3. **Set up wallet keypair**:
   ```bash
   # Create secure keys directory
   mkdir -p wallet
   cp /path/to/your/keypair.json wallet/trading_wallet_keypair.json
   chmod 600 wallet/trading_wallet_keypair.json

   # Verify keypair format (should be Ed25519)
   python3 scripts/generate_test_keypair.py --verify wallet/trading_wallet_keypair.json
   ```

4. **Configure trading parameters**:
   ```bash
   # Edit main configuration
   nano config.yaml
   ```

   Key settings to verify:
   - `risk.max_position_size_pct`: 0.5 (50% of wallet for production)
   - `execution.use_jito`: true (for MEV protection)
   - `execution.slippage_tolerance`: 0.02 (2% for larger trades)
   - `whale_watching.enabled`: true (for enhanced signals)
   - `market_regime.enabled`: true (for adaptive strategies)

### 2. Build System Components

Build the required Rust components for optimal performance:

```bash
# Build Carbon Core for high-performance data processing
./build_carbon_core.sh

# Build Solana TX Utils for transaction handling
cd solana_tx_utils
./build_and_install.sh
cd ..
```

If builds fail, the system will automatically fall back to Python implementations, but with reduced performance.

### 3. Verify Production Readiness

Run the comprehensive production verification to ensure all components are ready:

```bash
# Run production readiness check
python3 scripts/final_production_verification.py

# Run system status check
python3 scripts/system_status_check.py

# Verify current system integration
python3 tests/run_comprehensive_tests.py --suite deployment_validation
```

This verification checks:
- Configuration files and environment variables
- API keys and connectivity
- Wallet keypair format and permissions
- Rust component builds (Carbon Core, Solana TX Utils)
- Jito Bundle client configuration
- Orca DEX integration
- Monitoring and alerting components
- Dashboard and health endpoints

If any checks fail, address the issues before proceeding.

### 4. Run System Tests

Run comprehensive system tests to verify all components work together:

```bash
# Run simulation test with current system
python3 phase_4_deployment/run_simulation.py

# Run comprehensive system tests
python3 tests/run_comprehensive_tests.py

# Test live trading components (dry run)
python3 scripts/test_fixed_live_trading.py --dry-run

# Test dashboard functionality
python3 phase_4_deployment/dashboard/streamlit_dashboard.py --test-mode
```

This testing validates:
- Jito Bundle client functionality
- Orca DEX swap building
- Whale watching and signal generation
- Risk management and position sizing
- Telegram notification system
- Dashboard and monitoring components

### 5. Deploy Production System

Choose your deployment method:

#### Option A: Unified Runner Deployment (Recommended)

```bash
# Start the unified trading system
python3 phase_4_deployment/unified_runner.py --mode live

# Or start with specific configuration
python3 phase_4_deployment/unified_runner.py --mode live --config config.yaml
```

#### Option B: Individual Component Deployment

```bash
# Start live trading system
python3 scripts/unified_live_trading.py

# Start dashboard (in separate terminal)
streamlit run phase_4_deployment/dashboard/streamlit_dashboard.py --server.port 8501

# Start monitoring (in separate terminal)
python3 phase_4_deployment/monitoring/health_check_server.py
```

#### Option C: Docker Deployment (Optional)

```bash
cd phase_4_deployment
./deploy_production.sh
```

### 6. Monitor the Deployment

After deployment, monitor the system using multiple interfaces:

```bash
# View live trading logs
tail -f logs/unified_live_trading.log

# View system logs
tail -f logs/system/system_health.log

# View trading metrics
python3 scripts/display_trade_metrics.py

# Check wallet balance
python3 scripts/update_dashboard_real_balance.py
```

#### Dashboard Access

- **Main Dashboard**: http://localhost:8501 (Streamlit)
- **Health Endpoint**: http://localhost:8080/health (if health server running)
- **Metrics API**: http://localhost:8080/metrics (if API server running)

#### Real-time Monitoring

```bash
# Monitor trading activity
python3 scripts/check_live_trading_status.py

# Monitor system health
python3 scripts/system_status_check.py

# Monitor wallet balance changes
python3 scripts/analyze_live_metrics_profitability.py
```

#### Telegram Alerts

The system automatically sends alerts to your configured Telegram chat for:
- Trade executions and results
- System errors and warnings
- Wallet balance changes
- Performance metrics updates

## Deployment Options

### Standard Deployment

The standard deployment uses Docker Compose to run all components:

```bash
./deploy_production.sh
```

### Deployment with Fallbacks

If you encounter issues with the Rust components, you can deploy with fallbacks enabled:

```bash
./deploy_production.sh --force-fallback
```

This will use Python fallback implementations for:
- Carbon Core
- Solana transaction utilities

### Deployment without Verification

If you want to skip the verification steps:

```bash
./deploy_production.sh --skip-verification
```

### Deployment without Simulation

If you want to skip the simulation test:

```bash
./deploy_production.sh --skip-simulation
```

### Deployment without Building Carbon Core

If you want to skip building the Carbon Core binary:

```bash
./deploy_production.sh --skip-build
```

### Deployment to Different Environment

You can deploy to different environments:

```bash
./deploy_production.sh --environment simulation
```

Available environments:
- `production`: Production environment
- `simulation`: Simulation environment
- `development`: Development environment

## Troubleshooting

### Carbon Core Build Issues

If the Carbon Core build fails:

1. Check Rust installation:
   ```bash
   rustc --version
   cargo --version
   ```

2. Check Python development headers:
   ```bash
   python3-config --includes
   ```

3. Try building with debug output:
   ```bash
   RUST_BACKTRACE=1 ./build_carbon_core.sh
   ```

4. If the build still fails, use the fallback implementation:
   ```bash
   export CARBON_CORE_FALLBACK=true
   ./deploy_production.sh
   ```

### API Issues

If you encounter API issues:

1. Check API keys in `.env` file
2. Verify API endpoints are accessible:
   ```bash
   curl -s "https://api.helius.xyz/v0/addresses/vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg/balances?api-key=YOUR_API_KEY"
   ```

3. Configure fallback API keys:
   ```bash
   export HELIUS_FALLBACK_API_KEY=your_fallback_key
   export BIRDEYE_FALLBACK_API_KEY=your_fallback_key
   ```

### Docker Issues

If you encounter Docker issues:

1. Check Docker installation:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Check Docker daemon:
   ```bash
   docker ps
   ```

3. Check Docker logs:
   ```bash
   docker-compose logs
   ```

4. Restart Docker:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Monitoring and Alerting

The system includes monitoring and alerting components:

1. **Dashboard**: Access the dashboard at `http://localhost:8501`
2. **Health Endpoint**: Check system health at `http://localhost:8080/health`
3. **Telegram Alerts**: Receive alerts via Telegram

To configure Telegram alerts:

1. Create a Telegram bot using BotFather
2. Get your chat ID
3. Add the bot token and chat ID to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

## Backup and Recovery

### Backup

Regularly backup the following:

1. **Configuration Files**:
   ```bash
   cp config.yaml config.yaml.bak
   cp .env .env.bak
   ```

2. **Wallet Keypair**:
   ```bash
   cp phase_4_deployment/keys/wallet_keypair.json wallet_keypair.json.bak
   ```

3. **Database** (if used):
   ```bash
   docker-compose exec db pg_dump -U postgres > backup.sql
   ```

### Recovery

To recover from a backup:

1. **Configuration Files**:
   ```bash
   cp config.yaml.bak config.yaml
   cp .env.bak .env
   ```

2. **Wallet Keypair**:
   ```bash
   cp wallet_keypair.json.bak phase_4_deployment/keys/wallet_keypair.json
   chmod 600 phase_4_deployment/keys/wallet_keypair.json
   ```

3. **Database** (if used):
   ```bash
   cat backup.sql | docker-compose exec -T db psql -U postgres
   ```

## Security Considerations

1. **Wallet Security**:
   - Store keypair files with restricted permissions (`chmod 600`)
   - Consider using a hardware wallet for production
   - Use a dedicated wallet for the trading system

2. **API Key Security**:
   - Store API keys in `.env` file, not in code
   - Use different API keys for different environments
   - Rotate API keys regularly

3. **Network Security**:
   - Use a firewall to restrict access to the system
   - Use HTTPS for all external communications
   - Consider using a VPN for remote access

4. **Docker Security**:
   - Keep Docker and Docker Compose updated
   - Use non-root users in containers
   - Limit container capabilities

## Conclusion

Following this guide will help you deploy the Q5 Trading System to production with proper security, monitoring, and fallback mechanisms. If you encounter any issues, refer to the troubleshooting section or contact the development team.
