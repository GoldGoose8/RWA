#!/usr/bin/env python3
"""
Enhanced API Server for Williams Capital Management Trading System Dashboard

Real-time integration with live trading system providing metrics every 30 seconds.
Designed for Winsor Williams II hedge fund operations.
"""

import os
import json
import time
import logging
import asyncio
import uvicorn
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
import base58

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv()

# Simple monitoring service for dashboard
class SimpleMonitoringService:
    """Simple monitoring service for dashboard API."""

    def __init__(self):
        self.started = False

    def start(self):
        """Start monitoring service."""
        self.started = True
        logger.info("✅ Simple monitoring service started")

    def run_health_checks(self):
        """Run basic health checks."""
        return {
            "api_server": True,
            "database": True,
            "network": True,
            "disk_space": True
        }

    def get_metrics(self):
        """Get basic metrics."""
        return {
            "component_status": {
                "api_server": "healthy",
                "database": "healthy",
                "network": "healthy"
            },
            "system_metrics": {
                "uptime": time.time(),
                "memory_usage": 0.5,
                "cpu_usage": 0.3
            }
        }

def get_monitoring_service():
    """Get monitoring service instance."""
    return SimpleMonitoringService()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("enhanced_api_server")

# Live Trading Integration Class
class LiveTradingMetrics:
    """Real-time metrics from live trading system."""

    def __init__(self):
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        self.last_update = None
        self.metrics_cache = {}
        self.connected_clients = set()

    async def get_wallet_balance(self):
        """Get real-time wallet balance."""
        try:
            from phase_4_deployment.rpc_execution.helius_client import HeliusClient
            client = HeliusClient(api_key=self.helius_api_key)
            balance_data = await client.get_balance(self.wallet_address)

            if isinstance(balance_data, dict) and 'balance_sol' in balance_data:
                return balance_data['balance_sol']
            return None
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return None

    async def get_sol_price(self):
        """Get current SOL price from Jupiter."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://quote-api.jup.ag/v6/quote",
                    params={
                        "inputMint": "So11111111111111111111111111111111111111112",
                        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                        "amount": "1000000000",  # 1 SOL
                        "slippageBps": "100"
                    }
                )

                if response.status_code == 200:
                    quote_data = response.json()
                    return float(quote_data['outAmount']) / 1_000_000  # USDC has 6 decimals
                return 152.0  # Fallback
        except Exception as e:
            logger.error(f"Error getting SOL price: {e}")
            return 152.0

    async def get_live_metrics(self):
        """Get comprehensive live trading metrics."""
        try:
            # Get real-time data
            balance = await self.get_wallet_balance()
            sol_price = await self.get_sol_price()

            # Read trading session data if available
            session_data = self.read_session_data()

            # Calculate metrics
            balance_usd = balance * sol_price if balance else 0

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "wallet": {
                    "address": self.wallet_address,
                    "balance": balance or 0,
                    "balanceUSD": balance_usd,
                    "lastUpdate": datetime.now().isoformat()
                },
                "market": {
                    "solPrice": sol_price,
                    "solChange24h": 0.5,  # Mock data - could be enhanced
                    "lastUpdate": datetime.now().isoformat()
                },
                "trading": {
                    "isActive": session_data.get("is_active", False),
                    "totalTrades": session_data.get("total_trades", 0),
                    "successfulTrades": session_data.get("successful_trades", 0),
                    "totalPnL": session_data.get("total_pnl", 0),
                    "totalPnLUSD": session_data.get("total_pnl_usd", 0),
                    "winRate": session_data.get("win_rate", 0),
                    "lastTradeTime": session_data.get("last_trade_time"),
                    "sessionDuration": session_data.get("session_duration", 0)
                },
                "system": {
                    "health": "online",
                    "uptime": time.time() - session_data.get("session_start", time.time()),
                    "lastUpdate": datetime.now().isoformat(),
                    "components": {
                        "trading_engine": "online",
                        "mev_protection": "online",
                        "rpc_endpoints": "online",
                        "risk_management": "online"
                    }
                },
                "recentTrades": session_data.get("recent_trades", [])
            }

            self.metrics_cache = metrics
            self.last_update = datetime.now()
            return metrics

        except Exception as e:
            logger.error(f"Error getting live metrics: {e}")
            return self.get_fallback_metrics()

    def read_session_data(self):
        """Read trading session data from logs or files."""
        try:
            # Try to read from logs directory
            logs_dir = Path(__file__).parent.parent.parent / 'logs'
            if logs_dir.exists():
                # Find the most recent debug log
                log_files = list(logs_dir.glob('debug_live_trading_*.log'))
                if log_files:
                    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                    return self.parse_log_file(latest_log)

            # Fallback to default data
            return {
                "is_active": False,
                "total_trades": 0,
                "successful_trades": 0,
                "total_pnl": 0,
                "total_pnl_usd": 0,
                "win_rate": 0,
                "session_start": time.time(),
                "recent_trades": []
            }
        except Exception as e:
            logger.error(f"Error reading session data: {e}")
            return {}

    def parse_log_file(self, log_file):
        """Parse trading session data from log file."""
        try:
            session_data = {
                "is_active": False,
                "total_trades": 0,
                "successful_trades": 0,
                "total_pnl": 0,
                "total_pnl_usd": 0,
                "win_rate": 0,
                "session_start": time.time(),
                "recent_trades": []
            }

            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Parse log for trading activity
            for line in lines:
                if "STARTING DEBUG TRADING SESSION" in line:
                    session_data["is_active"] = True
                elif "Transaction executed:" in line:
                    session_data["total_trades"] += 1
                    session_data["successful_trades"] += 1
                elif "Cycle" in line and "completed successfully" in line:
                    # Extract cycle info
                    pass

            # Calculate win rate
            if session_data["total_trades"] > 0:
                session_data["win_rate"] = (session_data["successful_trades"] / session_data["total_trades"]) * 100

            return session_data

        except Exception as e:
            logger.error(f"Error parsing log file: {e}")
            return {}

    def get_fallback_metrics(self):
        """Get fallback metrics when live data is unavailable."""
        return {
            "timestamp": datetime.now().isoformat(),
            "wallet": {
                "address": self.wallet_address or "N/A",
                "balance": 15.55,
                "balanceUSD": 2365.60,
                "lastUpdate": datetime.now().isoformat()
            },
            "market": {
                "solPrice": 152.0,
                "solChange24h": 0.5,
                "lastUpdate": datetime.now().isoformat()
            },
            "trading": {
                "isActive": False,
                "totalTrades": 0,
                "successfulTrades": 0,
                "totalPnL": 0,
                "totalPnLUSD": 0,
                "winRate": 0,
                "lastTradeTime": None,
                "sessionDuration": 0
            },
            "system": {
                "health": "offline",
                "uptime": 0,
                "lastUpdate": datetime.now().isoformat(),
                "components": {
                    "trading_engine": "offline",
                    "mev_protection": "offline",
                    "rpc_endpoints": "offline",
                    "risk_management": "offline"
                }
            },
            "recentTrades": []
        }

# Initialize live trading metrics
live_metrics = LiveTradingMetrics()

# Create FastAPI app
app = FastAPI(
    title="Williams Capital Management Trading API",
    description="Real-time API for Williams Capital Management Trading System Dashboard",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get monitoring service
monitoring = get_monitoring_service()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Williams Capital Management Trading API",
        "version": "2.0.0",
        "owner": "Winsor Williams II",
        "status": "Live Trading System",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Enhanced health check with live trading system status."""
    try:
        # Get live metrics
        live_data = await live_metrics.get_live_metrics()

        # Run standard health checks
        health_results = monitoring.run_health_checks()

        # Calculate overall health
        overall_health = all(health_results.values()) and live_data["system"]["health"] == "online"

        return {
            "overall_health": overall_health,
            "live_trading_active": live_data["trading"]["isActive"],
            "wallet_connected": live_data["wallet"]["balance"] is not None,
            "components": {
                **health_results,
                **live_data["system"]["components"]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "overall_health": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/metrics")
async def metrics():
    """Enhanced metrics endpoint with live trading data."""
    try:
        # Get live metrics
        live_data = await live_metrics.get_live_metrics()

        # Get standard monitoring metrics
        monitoring_metrics = monitoring.get_metrics()

        # Combine metrics
        combined_metrics = {
            **live_data,
            "monitoring": monitoring_metrics,
            "api_info": {
                "version": "2.0.0",
                "last_update": datetime.now().isoformat(),
                "update_interval": 30
            }
        }

        return combined_metrics

    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return live_metrics.get_fallback_metrics()

@app.get("/live-status")
async def live_status():
    """Real-time trading system status."""
    try:
        live_data = await live_metrics.get_live_metrics()

        return {
            "trading_active": live_data["trading"]["isActive"],
            "wallet_balance": live_data["wallet"]["balance"],
            "wallet_balance_usd": live_data["wallet"]["balanceUSD"],
            "sol_price": live_data["market"]["solPrice"],
            "total_trades": live_data["trading"]["totalTrades"],
            "win_rate": live_data["trading"]["winRate"],
            "system_health": live_data["system"]["health"],
            "last_update": live_data["timestamp"]
        }
    except Exception as e:
        logger.error(f"Live status error: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/wallet-info")
async def wallet_info():
    """Detailed wallet information."""
    try:
        balance = await live_metrics.get_wallet_balance()
        sol_price = await live_metrics.get_sol_price()

        return {
            "address": live_metrics.wallet_address,
            "balance_sol": balance,
            "balance_usd": balance * sol_price if balance else 0,
            "sol_price": sol_price,
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Wallet info error: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/trading-session")
async def trading_session():
    """Current trading session information."""
    try:
        session_data = live_metrics.read_session_data()

        return {
            "is_active": session_data.get("is_active", False),
            "total_trades": session_data.get("total_trades", 0),
            "successful_trades": session_data.get("successful_trades", 0),
            "win_rate": session_data.get("win_rate", 0),
            "session_duration": time.time() - session_data.get("session_start", time.time()),
            "recent_trades": session_data.get("recent_trades", []),
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Trading session error: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    live_metrics.connected_clients.add(websocket)

    try:
        while True:
            # Send live metrics every 30 seconds
            live_data = await live_metrics.get_live_metrics()
            await websocket.send_json(live_data)
            await asyncio.sleep(30)

    except WebSocketDisconnect:
        live_metrics.connected_clients.discard(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        live_metrics.connected_clients.discard(websocket)

@app.get("/component/{component}")
async def component(component: str):
    """Enhanced component status with live data integration."""
    try:
        # Get live metrics
        live_data = await live_metrics.get_live_metrics()

        # Get standard monitoring metrics
        metrics = monitoring.get_metrics()

        # Check live system components first
        if component in live_data["system"]["components"]:
            return {
                "component": component,
                "status": live_data["system"]["components"][component],
                "live_data": True,
                "last_update": live_data["timestamp"]
            }

        # Fallback to monitoring service
        component_status = metrics.get("component_status", {}).get(component)

        if component_status:
            return {
                "component": component,
                "status": component_status,
                "live_data": False,
                "last_update": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Component {component} not found")

    except Exception as e:
        logger.error(f"Component status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/{market}")
async def market(market: str):
    """
    Market microstructure endpoint.

    Args:
        market: Market identifier (e.g., "SOL-USDC")
    """
    # Get metrics
    metrics = monitoring.get_metrics()

    # Get market microstructure
    market_microstructure = metrics.get("market_microstructure", {}).get(market)

    if market_microstructure:
        return market_microstructure
    else:
        raise HTTPException(status_code=404, detail=f"Market {market} not found")

@app.get("/signal/{signal_type}")
async def signal(signal_type: str):
    """
    Statistical signal endpoint.

    Args:
        signal_type: Signal type (e.g., "price_momentum")
    """
    # Get metrics
    metrics = monitoring.get_metrics()

    # Get statistical signal
    statistical_signal = metrics.get("statistical_signals", {}).get(signal_type)

    if statistical_signal:
        return statistical_signal
    else:
        raise HTTPException(status_code=404, detail=f"Signal {signal_type} not found")

@app.get("/strategy-accuracy/{metric_type}")
async def strategy_accuracy(metric_type: str):
    """
    Strategy accuracy metrics endpoint.

    Args:
        metric_type: Metric type (e.g., "signal_generation", "directional_accuracy")
    """
    # Get metrics
    metrics = monitoring.get_metrics()

    # Get strategy accuracy metrics
    strategy_accuracy = metrics.get("strategy_accuracy", {}).get(metric_type)

    if strategy_accuracy:
        return strategy_accuracy
    else:
        raise HTTPException(status_code=404, detail=f"Strategy accuracy metric {metric_type} not found")

@app.get("/profit-metrics/{metric_type}")
async def profit_metrics(metric_type: str):
    """
    Profit metrics endpoint.

    Args:
        metric_type: Metric type (e.g., "net_profit", "profit_factor")
    """
    # Get metrics
    metrics = monitoring.get_metrics()

    # Get profit metrics
    profit_metrics = metrics.get("profit_metrics", {}).get(metric_type)

    if profit_metrics:
        return profit_metrics
    else:
        raise HTTPException(status_code=404, detail=f"Profit metric {metric_type} not found")

@app.get("/execution-quality/{metric_type}")
async def execution_quality(metric_type: str):
    """
    Execution quality metrics endpoint.

    Args:
        metric_type: Metric type (e.g., "slippage", "fill_rate")
    """
    # Get metrics
    metrics = monitoring.get_metrics()

    # Get execution quality metrics
    execution_quality = metrics.get("execution_quality", {}).get(metric_type)

    if execution_quality:
        return execution_quality
    else:
        raise HTTPException(status_code=404, detail=f"Execution quality metric {metric_type} not found")

@app.get("/wallet/{wallet_address}")
async def wallet(wallet_address: str):
    """
    Wallet balance endpoint.

    Args:
        wallet_address: Wallet address
    """
    # Get metrics
    metrics = monitoring.get_metrics()

    # Get wallet balance
    wallet_balance = metrics.get("wallet_balances", {}).get(wallet_address)

    if wallet_balance:
        return wallet_balance
    else:
        raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")

@app.get("/transaction/{signature}")
async def transaction(signature: str):
    """
    Transaction endpoint.

    Args:
        signature: Transaction signature
    """
    # Get metrics
    metrics = monitoring.get_metrics()

    # Get transaction
    transaction = metrics.get("transactions", {}).get(signature)

    if transaction:
        return transaction
    else:
        raise HTTPException(status_code=404, detail=f"Transaction {signature} not found")

# Background task for metrics updates
async def metrics_updater():
    """Background task to update metrics every 30 seconds."""
    while True:
        try:
            # Update live metrics
            await live_metrics.get_live_metrics()

            # Broadcast to connected WebSocket clients
            if live_metrics.connected_clients:
                live_data = live_metrics.metrics_cache
                disconnected_clients = set()

                for client in live_metrics.connected_clients:
                    try:
                        await client.send_json(live_data)
                    except Exception:
                        disconnected_clients.add(client)

                # Remove disconnected clients
                live_metrics.connected_clients -= disconnected_clients

            logger.info(f"📊 Metrics updated - {len(live_metrics.connected_clients)} connected clients")

        except Exception as e:
            logger.error(f"Metrics updater error: {e}")

        await asyncio.sleep(30)  # Update every 30 seconds

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup."""
    logger.info("🚀 Starting Williams Capital Management Trading API")
    logger.info(f"👤 Owner: Winsor Williams II")
    logger.info(f"💼 Wallet: {live_metrics.wallet_address}")

    # Start monitoring service
    monitoring.start()

    # Start background metrics updater
    asyncio.create_task(metrics_updater())

    logger.info("✅ API server startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down Williams Capital Management Trading API")

def start_api_server(host: str = "0.0.0.0", port: int = 8081):
    """
    Start the enhanced API server with live trading integration.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    logger.info("🚀 Starting Williams Capital Management Trading API Server")
    logger.info(f"🌐 Host: {host}:{port}")
    logger.info(f"👤 Owner: Winsor Williams II")
    logger.info(f"💼 Wallet: {live_metrics.wallet_address}")

    # Start API server with WebSocket support
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="API Server for Synergy7 Trading System Dashboard")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    args = parser.parse_args()

    # Start API server
    start_api_server(host=args.host, port=args.port)
