# Monitoring Setup Guide

This guide provides detailed instructions for setting up comprehensive monitoring for the Synergy7 Trading System with the optimized momentum strategy.

## Overview

The monitoring system consists of several components:

1. **Unified Dashboard**: Real-time visualization of system performance
2. **Alert System**: Notifications for important events and threshold breaches
3. **Logging System**: Detailed logging of system activities
4. **Performance Tracking**: Tracking of strategy performance metrics
5. **System Health Monitoring**: Monitoring of system resource usage and API health

## Unified Dashboard Setup

The unified dashboard provides a comprehensive view of the trading system's performance and status.

### Installation

```bash
# Install required packages
pip install streamlit plotly matplotlib pandas

# Run the dashboard
python phase_4_deployment/unified_dashboard/run_dashboard.py
```

### Configuration

Edit the dashboard configuration in `phase_4_deployment/unified_dashboard/config.yaml`:

```yaml
dashboard:
  port: 8501
  theme: "light"
  auto_refresh_seconds: 60
  sections:
    - name: "System Overview"
      enabled: true
      position: 1
    - name: "Strategy Performance"
      enabled: true
      position: 2
    - name: "Risk Management"
      enabled: true
      position: 3
    - name: "Market Data"
      enabled: true
      position: 4
    - name: "API Health"
      enabled: true
      position: 5
```

### Custom Visualizations

Add custom visualizations for the momentum strategy by creating a new file `phase_4_deployment/unified_dashboard/components/momentum_visualizations.py`:

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def render_momentum_metrics(data):
    """Render momentum strategy specific metrics."""
    st.header("Momentum Strategy Metrics")
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Win Rate", f"{data['win_rate']:.2%}", 
                 f"{data['win_rate_change']:.2%}")
    
    with col2:
        st.metric("Avg Trade Return", f"{data['avg_trade_return']:.2%}", 
                 f"{data['avg_trade_return_change']:.2%}")
    
    with col3:
        st.metric("Sharpe Ratio", f"{data['sharpe_ratio']:.2f}", 
                 f"{data['sharpe_ratio_change']:.2f}")
    
    with col4:
        st.metric("Max Drawdown", f"{data['max_drawdown']:.2%}", 
                 f"{data['max_drawdown_change']:.2%}")
    
    # Create momentum signal chart
    st.subheader("Momentum Signal Strength")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['momentum_signal'],
        mode='lines',
        name='Momentum Signal',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['threshold'] * np.ones(len(data['dates'])),
        mode='lines',
        name='Buy Threshold',
        line=dict(color='green', width=1, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=-data['threshold'] * np.ones(len(data['dates'])),
        mode='lines',
        name='Sell Threshold',
        line=dict(color='red', width=1, dash='dash')
    ))
    
    fig.update_layout(
        title='Momentum Signal Strength',
        xaxis_title='Date',
        yaxis_title='Signal Strength',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
```

## Alert System Setup

The alert system sends notifications for important events and threshold breaches.

### Telegram Alerts Setup

1. Create a Telegram bot using BotFather and get the API token
2. Create a Telegram group and add the bot
3. Get the chat ID using the `getUpdates` API endpoint

Configure Telegram alerts in `config.yaml`:

```yaml
monitoring:
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "5135869709"
    alert_levels:
      critical: true
      warning: true
      info: false
```

Create the Telegram alert handler in `phase_4_deployment/monitoring/telegram_alerts.py`:

```python
import requests
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramAlertHandler:
    def __init__(self, config):
        self.enabled = config.get("enabled", False)
        self.bot_token = config.get("bot_token", "")
        self.chat_id = config.get("chat_id", "")
        self.alert_levels = config.get("alert_levels", {
            "critical": True,
            "warning": True,
            "info": False
        })
        
        if self.enabled and (not self.bot_token or not self.chat_id):
            logger.warning("Telegram alerts enabled but missing bot_token or chat_id")
            self.enabled = False
    
    def send_alert(self, message, level="info"):
        """Send an alert to Telegram."""
        if not self.enabled or not self.alert_levels.get(level, False):
            return False
        
        # Format message with timestamp and level
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{level.upper()}] {timestamp}\n\n{message}"
        
        # Add emoji based on level
        if level == "critical":
            formatted_message = "🚨 " + formatted_message
        elif level == "warning":
            formatted_message = "⚠️ " + formatted_message
        elif level == "info":
            formatted_message = "ℹ️ " + formatted_message
        
        # Send message
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Telegram alert sent: {level}")
                return True
            else:
                logger.error(f"Failed to send Telegram alert: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {str(e)}")
            return False
```

### Email Alerts Setup

Configure email alerts in `config.yaml`:

```yaml
monitoring:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    recipients:
      - "recipient1@example.com"
      - "recipient2@example.com"
    alert_levels:
      critical: true
      warning: false
      info: false
```

## Logging System Setup

Configure comprehensive logging for the trading system.

### Logging Configuration

Configure logging in `config.yaml`:

```yaml
logging:
  level: INFO
  file: logs/trading_system.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  rotation: daily
  backup_count: 30
  components:
    strategy:
      level: DEBUG
      file: logs/strategy.log
    risk:
      level: INFO
      file: logs/risk.log
    api:
      level: INFO
      file: logs/api.log
```

Create a centralized logging setup in `shared/utils/logging_setup.py`:

```python
import logging
import os
from logging.handlers import TimedRotatingFileHandler
import sys

def setup_logging(config):
    """Set up logging based on configuration."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.get("file", "logs/trading_system.log"))
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.get("level", "INFO")))
    
    # Create formatter
    formatter = logging.Formatter(config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set up file handler with rotation
    file_handler = TimedRotatingFileHandler(
        config.get("file", "logs/trading_system.log"),
        when=config.get("rotation", "midnight"),
        backupCount=config.get("backup_count", 30)
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Set up component-specific loggers
    components = config.get("components", {})
    for component_name, component_config in components.items():
        component_logger = logging.getLogger(component_name)
        component_logger.setLevel(getattr(logging, component_config.get("level", "INFO")))
        
        # Create component log directory if it doesn't exist
        component_log_dir = os.path.dirname(component_config.get("file", f"logs/{component_name}.log"))
        os.makedirs(component_log_dir, exist_ok=True)
        
        # Set up component file handler
        component_file_handler = TimedRotatingFileHandler(
            component_config.get("file", f"logs/{component_name}.log"),
            when=config.get("rotation", "midnight"),
            backupCount=config.get("backup_count", 30)
        )
        component_file_handler.setFormatter(formatter)
        component_logger.addHandler(component_file_handler)
    
    logging.info("Logging system initialized")
    return root_logger
```

## Performance Tracking Setup

Set up comprehensive performance tracking for the momentum strategy.

### Performance Metrics Collection

Create a performance tracker in `core/strategies/performance_tracker.py`:

```python
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger("strategy")

class PerformanceTracker:
    def __init__(self, strategy_name, config):
        self.strategy_name = strategy_name
        self.config = config
        self.metrics = {
            "trades": [],
            "daily_pnl": {},
            "drawdowns": [],
            "sharpe_ratio": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "total_return": 0,
            "num_trades": 0,
            "avg_trade_return": 0
        }
        
        # Create output directory
        self.output_dir = config.get("output_dir", "output/performance")
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Initialized performance tracker for {strategy_name}")
    
    def record_trade(self, trade_data):
        """Record a completed trade."""
        self.metrics["trades"].append(trade_data)
        self.metrics["num_trades"] += 1
        
        # Update daily P&L
        trade_date = trade_data["exit_time"].strftime("%Y-%m-%d")
        if trade_date not in self.metrics["daily_pnl"]:
            self.metrics["daily_pnl"][trade_date] = 0
        self.metrics["daily_pnl"][trade_date] += trade_data["profit_loss"]
        
        # Recalculate metrics
        self._calculate_metrics()
        
        # Save metrics
        self._save_metrics()
        
        logger.info(f"Recorded trade: {trade_data['trade_id']}, P&L: {trade_data['profit_loss']:.2f}")
    
    def record_equity(self, timestamp, equity):
        """Record equity point for drawdown calculation."""
        self.metrics["drawdowns"].append({
            "timestamp": timestamp,
            "equity": equity
        })
        
        # Calculate drawdown
        self._calculate_drawdown()
        
        # Save metrics periodically (every 10 points)
        if len(self.metrics["drawdowns"]) % 10 == 0:
            self._save_metrics()
    
    def _calculate_metrics(self):
        """Calculate performance metrics."""
        if not self.metrics["trades"]:
            return
        
        # Calculate win rate
        winning_trades = [t for t in self.metrics["trades"] if t["profit_loss"] > 0]
        self.metrics["win_rate"] = len(winning_trades) / len(self.metrics["trades"])
        
        # Calculate profit factor
        total_profit = sum(t["profit_loss"] for t in winning_trades)
        losing_trades = [t for t in self.metrics["trades"] if t["profit_loss"] <= 0]
        total_loss = abs(sum(t["profit_loss"] for t in losing_trades)) if losing_trades else 1
        self.metrics["profit_factor"] = total_profit / total_loss
        
        # Calculate average trade return
        self.metrics["avg_trade_return"] = sum(t["profit_loss"] for t in self.metrics["trades"]) / len(self.metrics["trades"])
        
        # Calculate total return
        self.metrics["total_return"] = sum(t["profit_loss"] for t in self.metrics["trades"])
        
        # Calculate Sharpe ratio if we have daily P&L
        if len(self.metrics["daily_pnl"]) > 1:
            daily_returns = list(self.metrics["daily_pnl"].values())
            self.metrics["sharpe_ratio"] = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
    
    def _calculate_drawdown(self):
        """Calculate drawdown metrics."""
        if len(self.metrics["drawdowns"]) < 2:
            return
        
        # Extract equity values
        equity_values = [d["equity"] for d in self.metrics["drawdowns"]]
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_values)
        
        # Calculate drawdowns
        drawdowns = 1 - np.array(equity_values) / running_max
        
        # Update max drawdown
        self.metrics["max_drawdown"] = max(drawdowns)
    
    def _save_metrics(self):
        """Save metrics to file."""
        # Create a copy of metrics for saving
        metrics_to_save = self.metrics.copy()
        
        # Convert non-serializable objects
        metrics_to_save["trades"] = [self._trade_to_dict(t) for t in metrics_to_save["trades"]]
        metrics_to_save["drawdowns"] = [self._drawdown_to_dict(d) for d in metrics_to_save["drawdowns"]]
        
        # Add timestamp
        metrics_to_save["last_updated"] = datetime.now().isoformat()
        
        # Save to file
        file_path = os.path.join(self.output_dir, f"{self.strategy_name}_metrics.json")
        with open(file_path, "w") as f:
            json.dump(metrics_to_save, f, indent=2)
    
    def _trade_to_dict(self, trade):
        """Convert trade object to serializable dict."""
        if isinstance(trade, dict):
            result = trade.copy()
            # Convert datetime objects
            for key, value in result.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
            return result
        else:
            # If trade is not a dict, convert it
            return {
                "trade_id": getattr(trade, "trade_id", "unknown"),
                "entry_time": getattr(trade, "entry_time", datetime.now()).isoformat(),
                "exit_time": getattr(trade, "exit_time", datetime.now()).isoformat(),
                "entry_price": getattr(trade, "entry_price", 0),
                "exit_price": getattr(trade, "exit_price", 0),
                "size": getattr(trade, "size", 0),
                "profit_loss": getattr(trade, "profit_loss", 0),
                "is_long": getattr(trade, "is_long", True)
            }
    
    def _drawdown_to_dict(self, drawdown):
        """Convert drawdown object to serializable dict."""
        if isinstance(drawdown, dict):
            result = drawdown.copy()
            # Convert datetime objects
            for key, value in result.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
            return result
        else:
            return {
                "timestamp": getattr(drawdown, "timestamp", datetime.now()).isoformat(),
                "equity": getattr(drawdown, "equity", 0)
            }
```

## System Health Monitoring

Set up monitoring for system health and API status.

### System Resource Monitoring

Create a system monitor in `phase_4_deployment/monitoring/system_monitor.py`:

```python
import psutil
import os
import logging
import json
import time
from datetime import datetime

logger = logging.getLogger("system")

class SystemMonitor:
    def __init__(self, config):
        self.config = config
        self.metrics = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "network": []
        }
        
        # Create output directory
        self.output_dir = config.get("output_dir", "output/system")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set sampling interval
        self.sampling_interval = config.get("sampling_interval", 60)  # seconds
        
        # Set history length
        self.history_length = config.get("history_length", 1440)  # 24 hours at 1 minute interval
        
        logger.info("Initialized system monitor")
    
    def start_monitoring(self):
        """Start monitoring system resources."""
        logger.info("Starting system resource monitoring")
        
        while True:
            try:
                # Collect metrics
                self._collect_metrics()
                
                # Save metrics
                self._save_metrics()
                
                # Prune old metrics
                self._prune_metrics()
                
                # Sleep
                time.sleep(self.sampling_interval)
            except Exception as e:
                logger.error(f"Error in system monitoring: {str(e)}")
                time.sleep(self.sampling_interval)
    
    def _collect_metrics(self):
        """Collect system resource metrics."""
        timestamp = datetime.now().isoformat()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics["cpu"].append({
            "timestamp": timestamp,
            "percent": cpu_percent
        })
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics["memory"].append({
            "timestamp": timestamp,
            "percent": memory.percent,
            "used": memory.used,
            "total": memory.total
        })
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.metrics["disk"].append({
            "timestamp": timestamp,
            "percent": disk.percent,
            "used": disk.used,
            "total": disk.total
        })
        
        # Network usage
        network = psutil.net_io_counters()
        self.metrics["network"].append({
            "timestamp": timestamp,
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv
        })
    
    def _save_metrics(self):
        """Save metrics to file."""
        file_path = os.path.join(self.output_dir, "system_metrics.json")
        with open(file_path, "w") as f:
            json.dump(self.metrics, f)
    
    def _prune_metrics(self):
        """Prune old metrics to maintain history length."""
        for metric_type in self.metrics:
            if len(self.metrics[metric_type]) > self.history_length:
                self.metrics[metric_type] = self.metrics[metric_type][-self.history_length:]
```

### API Health Monitoring

Create an API health monitor in `phase_4_deployment/monitoring/api_monitor.py`:

```python
import requests
import asyncio
import logging
import json
import os
import time
from datetime import datetime

logger = logging.getLogger("api")

class APIMonitor:
    def __init__(self, config):
        self.config = config
        self.apis = config.get("apis", {})
        self.metrics = {}
        
        # Initialize metrics for each API
        for api_name in self.apis:
            self.metrics[api_name] = {
                "status": "unknown",
                "response_times": [],
                "errors": [],
                "last_checked": None
            }
        
        # Create output directory
        self.output_dir = config.get("output_dir", "output/api")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set check interval
        self.check_interval = config.get("check_interval", 300)  # seconds
        
        # Set history length
        self.history_length = config.get("history_length", 288)  # 24 hours at 5 minute interval
        
        logger.info("Initialized API monitor")
    
    async def start_monitoring(self):
        """Start monitoring APIs."""
        logger.info("Starting API health monitoring")
        
        while True:
            try:
                # Check all APIs
                await self._check_apis()
                
                # Save metrics
                self._save_metrics()
                
                # Prune old metrics
                self._prune_metrics()
                
                # Sleep
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in API monitoring: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_apis(self):
        """Check health of all APIs."""
        for api_name, api_config in self.apis.items():
            try:
                # Get health check URL
                health_url = api_config.get("health_url")
                if not health_url:
                    logger.warning(f"No health URL configured for {api_name}")
                    continue
                
                # Record start time
                start_time = time.time()
                
                # Make request
                response = requests.get(health_url, timeout=10)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Update metrics
                self.metrics[api_name]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
                self.metrics[api_name]["response_times"].append({
                    "timestamp": datetime.now().isoformat(),
                    "response_time": response_time
                })
                self.metrics[api_name]["last_checked"] = datetime.now().isoformat()
                
                logger.info(f"API {api_name} health check: {self.metrics[api_name]['status']}, response time: {response_time:.3f}s")
            except Exception as e:
                # Update metrics
                self.metrics[api_name]["status"] = "error"
                self.metrics[api_name]["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                })
                self.metrics[api_name]["last_checked"] = datetime.now().isoformat()
                
                logger.error(f"API {api_name} health check failed: {str(e)}")
    
    def _save_metrics(self):
        """Save metrics to file."""
        file_path = os.path.join(self.output_dir, "api_metrics.json")
        with open(file_path, "w") as f:
            json.dump(self.metrics, f, indent=2)
    
    def _prune_metrics(self):
        """Prune old metrics to maintain history length."""
        for api_name in self.metrics:
            if "response_times" in self.metrics[api_name] and len(self.metrics[api_name]["response_times"]) > self.history_length:
                self.metrics[api_name]["response_times"] = self.metrics[api_name]["response_times"][-self.history_length:]
            
            if "errors" in self.metrics[api_name] and len(self.metrics[api_name]["errors"]) > self.history_length:
                self.metrics[api_name]["errors"] = self.metrics[api_name]["errors"][-self.history_length:]
```

## Integration with Unified Runner

Integrate all monitoring components with the unified runner in `phase_4_deployment/unified_runner.py`:

```python
# Add monitoring setup
from phase_4_deployment.monitoring.telegram_alerts import TelegramAlertHandler
from phase_4_deployment.monitoring.system_monitor import SystemMonitor
from phase_4_deployment.monitoring.api_monitor import APIMonitor
from shared.utils.logging_setup import setup_logging

# Initialize logging
setup_logging(config.get("logging", {}))

# Initialize alert handlers
telegram_handler = TelegramAlertHandler(config.get("monitoring", {}).get("telegram", {}))

# Initialize system monitor
system_monitor = SystemMonitor(config.get("monitoring", {}).get("system", {}))

# Initialize API monitor
api_monitor = APIMonitor(config.get("monitoring", {}).get("api", {}))

# Start monitoring in background tasks
asyncio.create_task(api_monitor.start_monitoring())
threading.Thread(target=system_monitor.start_monitoring, daemon=True).start()
```

## Conclusion

This monitoring setup provides comprehensive visibility into the trading system's performance, health, and status. The unified dashboard, alert system, logging system, performance tracking, and system health monitoring work together to ensure that you have complete awareness of how the system is functioning and can quickly respond to any issues that arise.
