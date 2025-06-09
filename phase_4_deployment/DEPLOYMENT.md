# Q5 Trading System Deployment Guide

This guide provides instructions for deploying the Q5 Trading System to a production environment.

## Prerequisites

Before deploying the Q5 Trading System, ensure that you have the following prerequisites installed:

- Docker
- Docker Compose
- Python 3.9 or later

## Configuration

The Q5 Trading System uses a YAML configuration file to define its behavior. The configuration file is located at `phase_4_deployment/production_config.yaml`.

Before deploying the system, you should review and update the configuration file to match your requirements. The following sections should be updated:

### API Keys

Update the API keys in the `apis` section:

```yaml
apis:
  helius:
    enabled: true
    api_key: "your_helius_api_key"
    rpc_endpoint: "https://mainnet.helius-rpc.com/?api-key=your_helius_api_key"
    ws_endpoint: "wss://mainnet.helius-rpc.com/?api-key=your_helius_api_key"
  
  birdeye:
    enabled: true
    api_key: "your_birdeye_api_key"
    endpoint: "https://api.birdeye.so/v1"
```

### Wallet Settings

Update the wallet settings in the `wallet` section:

```yaml
wallet:
  address: "your_wallet_address"
  keypair_path: "keys/wallet_keypair.json"
  max_transaction_fee: 10000  # in lamports
```

### Monitoring Settings

Update the monitoring settings in the `monitoring` section:

```yaml
monitoring:
  enabled: true
  log_level: "info"
  metrics_interval_ms: 5000
  health_check_interval_ms: 10000
  telegram_alerts: true
  telegram_chat_id: "your_telegram_chat_id"
  telegram_bot_token: "your_telegram_bot_token"
```

### Strategy Settings

Update the strategy settings in the `strategies` section:

```yaml
strategies:
  - name: "momentum_sol_usdc"
    type: "momentum"
    enabled: true
    markets:
      - "SOL-USDC"
    weight: 1.0
    parameters:
      window_size: 20
      threshold: 0.01
      max_value: 0.05
      smoothing_factor: 0.1
      max_position_size: 0.1
```

## Wallet Setup

The Q5 Trading System requires a Solana wallet for trading. You should create a wallet keypair and save it to the `keys` directory.

1. Generate a wallet keypair:

```bash
python phase_4_deployment/utils/generate_test_wallet.py --output phase_4_deployment/keys/wallet_keypair.json
```

2. Fund the wallet with SOL:

You can fund the wallet using a Solana wallet application like Phantom or Solflare. The wallet address is printed when you generate the keypair.

## Deployment

The Q5 Trading System can be deployed using the `deploy.py` script. The script provides several commands for deploying and managing the system.

### Deploy

To deploy the Q5 Trading System, run the following command:

```bash
python phase_4_deployment/deploy.py deploy --mode paper
```

This will deploy the system in paper trading mode. The available modes are:

- `live`: Live trading with real transactions
- `paper`: Paper trading with simulated transactions
- `backtest`: Backtesting with historical data
- `simulation`: Simulation with simulated data

### Stop

To stop the Q5 Trading System, run the following command:

```bash
python phase_4_deployment/deploy.py stop
```

### Logs

To view the logs of the Q5 Trading System, run the following command:

```bash
python phase_4_deployment/deploy.py logs
```

To follow the logs, add the `--follow` flag:

```bash
python phase_4_deployment/deploy.py logs --follow
```

To view the logs of a specific service, add the `--service` flag:

```bash
python phase_4_deployment/deploy.py logs --service q5_trading_bot
```

### Status

To view the status of the Q5 Trading System, run the following command:

```bash
python phase_4_deployment/deploy.py status
```

### Build

To build the Docker image without deploying, run the following command:

```bash
python phase_4_deployment/deploy.py build
```

## Monitoring

The Q5 Trading System provides several monitoring endpoints:

- Health Check: `http://localhost:8080/health`
- Status: `http://localhost:8080/status`
- Metrics: `http://localhost:8080/metrics`
- Alerts: `http://localhost:8080/alerts`

The system also provides a Streamlit dashboard for visualizing the trading system's status and performance:

- Streamlit Dashboard: `http://localhost:8501`

## Troubleshooting

If you encounter issues with the deployment, check the following:

1. Docker and Docker Compose are installed and running
2. The configuration file is correctly formatted and contains valid values
3. The wallet keypair file exists and is correctly formatted
4. The API keys are valid and have the necessary permissions
5. The system has network access to the required APIs

If you still encounter issues, check the logs for error messages:

```bash
python phase_4_deployment/deploy.py logs
```

## Security Considerations

The Q5 Trading System handles sensitive information such as API keys and wallet keypairs. To ensure the security of your deployment, consider the following:

1. Use a dedicated wallet with limited funds for trading
2. Store API keys and wallet keypairs securely
3. Limit access to the deployment environment
4. Use a firewall to restrict access to the monitoring endpoints
5. Regularly update the system to include security patches

## Backup and Recovery

To backup the Q5 Trading System, you should backup the following:

1. Configuration file: `phase_4_deployment/production_config.yaml`
2. Wallet keypair: `phase_4_deployment/keys/wallet_keypair.json`
3. Environment variables: `.env`

To recover the system, restore these files and redeploy the system.

## Upgrading

To upgrade the Q5 Trading System, follow these steps:

1. Stop the system: `python phase_4_deployment/deploy.py stop`
2. Pull the latest changes: `git pull`
3. Update the configuration file if necessary
4. Rebuild the Docker image: `python phase_4_deployment/deploy.py build`
5. Deploy the system: `python phase_4_deployment/deploy.py deploy --mode paper`
