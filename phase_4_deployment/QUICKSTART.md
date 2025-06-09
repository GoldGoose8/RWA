# Q5 Trading System Quick Start Guide

This guide provides a quick start for deploying the Q5 Trading System.

## Prerequisites

- Docker
- Docker Compose
- Python 3.9 or later

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/q5-trading-system.git
cd q5-trading-system
```

## Step 2: Set Up Configuration

1. Copy the sample environment file:

```bash
cp phase_4_deployment/sample.env .env
```

2. Edit the `.env` file with your API keys and settings:

```bash
nano .env
```

3. Generate a wallet keypair:

```bash
mkdir -p phase_4_deployment/keys
python phase_4_deployment/utils/generate_test_wallet.py --output phase_4_deployment/keys/wallet_keypair.json
```

4. Fund the wallet with SOL (the wallet address is printed when you generate the keypair).

## Step 3: Deploy in Paper Trading Mode

1. Build the Docker image:

```bash
python phase_4_deployment/deploy.py build
```

2. Deploy the system in paper trading mode:

```bash
python phase_4_deployment/deploy.py deploy --mode paper
```

3. Check the status of the deployment:

```bash
python phase_4_deployment/deploy.py status
```

4. View the logs:

```bash
python phase_4_deployment/deploy.py logs
```

## Step 4: Monitor the System

1. Access the health check server:

```
http://localhost:8080/health
```

2. Access the Streamlit dashboard:

```
http://localhost:8501
```

## Step 5: Going Live

1. After testing in paper trading mode, update the `.env` file:

```bash
nano .env
```

2. Set `DRY_RUN=false` and `PAPER_TRADING=false`.

3. Deploy the system in live trading mode:

```bash
python phase_4_deployment/deploy.py deploy --mode live
```

## Common Commands

- Build the Docker image:

```bash
python phase_4_deployment/deploy.py build
```

- Deploy the system:

```bash
python phase_4_deployment/deploy.py deploy --mode <mode>
```

- Stop the system:

```bash
python phase_4_deployment/deploy.py stop
```

- View logs:

```bash
python phase_4_deployment/deploy.py logs
```

- View logs for a specific service:

```bash
python phase_4_deployment/deploy.py logs --service q5_trading_bot
```

- Follow logs:

```bash
python phase_4_deployment/deploy.py logs --follow
```

- Check status:

```bash
python phase_4_deployment/deploy.py status
```

## Troubleshooting

If you encounter issues, check the following:

1. Docker and Docker Compose are installed and running
2. The configuration file is correctly formatted and contains valid values
3. The wallet keypair file exists and is correctly formatted
4. The API keys are valid and have the necessary permissions
5. The system has network access to the required APIs

For more detailed information, refer to the full [Deployment Guide](DEPLOYMENT.md) and [Deployment Checklist](DEPLOYMENT_CHECKLIST.md).
