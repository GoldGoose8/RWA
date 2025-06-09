# Q5 Trading System Monitoring

This directory contains monitoring configurations and dashboards for the Q5 Trading System.

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ with venv or conda environment
- API keys for Helius, Birdeye, and Telegram (optional)

### Automated Installation

1. Run the installation script to set up the Python requirements:

```bash
chmod +x monitoring/install_requirements.sh
./monitoring/install_requirements.sh
```

2. Start the Prometheus server:

```bash
cd monitoring
docker-compose up -d
```

3. Start the Streamlit dashboard:

```bash
chmod +x monitoring/start_streamlit.sh
./monitoring/start_streamlit.sh
```

4. Access the Streamlit dashboard at http://localhost:8501

### Manual Installation

1. Install required Python packages:

```bash
pip install prometheus_client psutil aiohttp pyyaml python-dotenv requests
pip install -r monitoring/streamlit_requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp monitoring/.env.example monitoring/.env
```

3. Create necessary directories:

```bash
mkdir -p monitoring/data/prometheus
```

4. Start Prometheus using Docker Compose:

```bash
docker-compose -f monitoring/docker-compose.yml up -d
```

5. Start the Streamlit dashboard:

```bash
cd monitoring
streamlit run streamlit_dashboard.py
```

## Monitoring Components

### Metrics

The Q5 Trading System exposes the following metrics:

- **API Requests**: Tracks API requests to external services
- **Trading Signals**: Counts trading signals by source, action, and market
- **Transactions**: Tracks transaction success/failure rates
- **Wallet Balance**: Monitors wallet balances
- **System Resources**: Tracks CPU, memory, and disk usage

### Streamlit Dashboard

The monitoring system includes a Streamlit dashboard with the following features:

- **Overview**: System health, wallet balances, and key metrics
- **API Performance**: API request counts, success rates, and latency
- **Trading Activity**: Trading signals and transactions
- **System Resources**: CPU, memory, and disk usage

### Alerting

Alerts are configured for:

- Low wallet balance
- Transaction errors
- Component health issues
- Circuit breaker trips
- System resource usage

Alerts are sent via Telegram if configured.

## Telegram Alerts Setup

1. Create a Telegram bot using BotFather
2. Get your chat ID using the IDBot
3. Add the following to your `.env` file:

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Configuration Files

### Docker Compose Configuration

The `docker-compose.yml` file defines the following services:

- **Prometheus**: Time-series database for storing metrics
- **Node Exporter**: System metrics collector (CPU, memory, disk)

### Prometheus Configuration

The `prometheus.yml` file configures Prometheus to scrape metrics from:

- Q5 Trading System (port 9091)
- Q5 Health Server (port 8080)
- Node Exporter (port 9100)

## Testing Monitoring

To test the monitoring setup:

1. Start the Q5 Trading System with monitoring enabled
2. Run the test metrics generator:

```bash
python generate_test_metrics.py
```

3. Check Prometheus targets at http://localhost:9090/targets
4. View metrics in the Streamlit dashboard at http://localhost:8501
5. Test alerts by triggering conditions (e.g., low balance)

## Streamlit Dashboard Features

The Streamlit dashboard provides the following features:

- **Auto-refresh**: Automatically refreshes the dashboard at a configurable interval
- **Time Range Selection**: Select the time range for metrics display
- **Interactive Charts**: Hover over charts to see detailed information
- **Responsive Layout**: Adapts to different screen sizes
- **Dark Mode**: Easy on the eyes for long monitoring sessions

## Troubleshooting

- If metrics are not showing up, check that the Prometheus server can reach the Q5 Trading System
- If alerts are not being sent, verify Telegram bot token and chat ID
- Check Docker logs for any errors:

```bash
docker logs prometheus
```

- If the Streamlit dashboard is not loading, check that the Streamlit server is running
- If using macOS or Windows, ensure `host.docker.internal` is resolving correctly
- For Linux, modify the Docker Compose file to use network mode "host"
