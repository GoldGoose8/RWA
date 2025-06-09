#!/usr/bin/env python3
"""
Risk Manager

This module provides functionality for managing trading risk.
"""

import os
import sys
import json
import time
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

# Install required packages
try:
    import zmq
    import zmq.asyncio
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyzmq"])
    import zmq
    import zmq.asyncio

# Import communication layer client
from shared.rust.comm_layer.client import RustCommClient, CommunicationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RiskManagerError(Exception):
    """Exception raised for risk manager errors."""
    pass

class RiskManager:
    """Manager for trading risk."""

    def __init__(
        self,
        config: Dict[str, Any],
        carbon_core_pub_endpoint: str = "tcp://127.0.0.1:5556",
        carbon_core_sub_endpoint: str = "tcp://127.0.0.1:5555",
        carbon_core_req_endpoint: str = "tcp://127.0.0.1:5557",
    ):
        """
        Initialize the risk manager.

        Args:
            config: Configuration dictionary
            carbon_core_pub_endpoint: Carbon Core publisher endpoint
            carbon_core_sub_endpoint: Carbon Core subscriber endpoint
            carbon_core_req_endpoint: Carbon Core request-reply endpoint
        """
        self.config = config

        # Create communication client for Carbon Core
        self.carbon_core_client = RustCommClient(
            pub_endpoint=carbon_core_pub_endpoint,
            sub_endpoint=carbon_core_sub_endpoint,
            req_endpoint=carbon_core_req_endpoint,
        )

        # Initialize trade signals
        self.trade_signals = {}

        # Initialize trade orders
        self.trade_orders = {}

        # Initialize portfolio
        self.portfolio = {}

        # Initialize risk metrics
        self.risk_metrics = {
            "total_value": 0.0,
            "total_exposure": 0.0,
            "max_drawdown": 0.0,
            "var_95": 0.0,
            "var_99": 0.0,
            "sharpe_ratio": 0.0,
            "volatility": 0.0,
            "last_update": datetime.now().isoformat(),
        }

        # Initialize state
        self.running = False
        self.tasks = []

        logger.info("Initialized risk manager")

    async def start(self):
        """Start the risk manager."""
        if self.running:
            logger.warning("Risk manager is already running")
            return

        logger.info("Starting risk manager...")

        # Connect to Carbon Core
        await self.carbon_core_client.connect()
        logger.info("Connected to Carbon Core")

        # Subscribe to trade signals
        await self._subscribe_to_trade_signals()

        # Set running flag
        self.running = True

        # Start risk manager tasks
        self.tasks = [
            asyncio.create_task(self._run_risk_manager()),
            asyncio.create_task(self._run_trade_order_publishing()),
            asyncio.create_task(self._run_risk_metrics_publishing()),
        ]

        logger.info("Risk manager started")

    async def stop(self):
        """Stop the risk manager."""
        if not self.running:
            logger.warning("Risk manager is not running")
            return

        logger.info("Stopping risk manager...")

        # Set running flag
        self.running = False

        # Cancel tasks
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Clear tasks
        self.tasks = []

        # Disconnect from Carbon Core
        await self.carbon_core_client.disconnect()
        logger.info("Disconnected from Carbon Core")

        logger.info("Risk manager stopped")

    async def _subscribe_to_trade_signals(self):
        """Subscribe to trade signals."""
        logger.info("Subscribing to trade signals...")

        # Get markets from configuration
        markets = self.config.get("market_microstructure", {}).get("markets", [])

        for market in markets:
            # Subscribe to trade signals
            await self.carbon_core_client.subscribe(f"trade_signals/{market}", self._handle_trade_signal_update)
            logger.info(f"Subscribed to trade signals for {market}")

    async def _run_risk_manager(self):
        """Run risk manager."""
        logger.info("Starting risk manager loop...")

        try:
            while self.running:
                # Process trade signals
                await self._process_trade_signals()

                # Update risk metrics
                await self._update_risk_metrics()

                # Sleep for update interval
                await asyncio.sleep(self.config.get("risk_management", {}).get("update_interval_ms", 1000) / 1000)
        except asyncio.CancelledError:
            logger.info("Risk manager loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in risk manager loop: {str(e)}")

    async def _run_trade_order_publishing(self):
        """Run trade order publishing."""
        logger.info("Starting trade order publishing...")

        try:
            while self.running:
                # Publish trade orders
                for market, trade_order in self.trade_orders.items():
                    try:
                        # Publish trade order
                        await self.carbon_core_client.publish(f"trade_orders/{market}", {
                            "market": market,
                            "trade_order": trade_order,
                            "timestamp": datetime.now().isoformat(),
                        })

                        logger.debug(f"Published trade order for {market}")
                    except Exception as e:
                        logger.error(f"Error publishing trade order for {market}: {str(e)}")

                # Sleep for update interval
                await asyncio.sleep(self.config.get("risk_management", {}).get("publish_interval_ms", 1000) / 1000)
        except asyncio.CancelledError:
            logger.info("Trade order publishing cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in trade order publishing: {str(e)}")

    async def _run_risk_metrics_publishing(self):
        """Run risk metrics publishing."""
        logger.info("Starting risk metrics publishing...")

        try:
            while self.running:
                # Publish risk metrics
                try:
                    # Publish risk metrics
                    await self.carbon_core_client.publish("risk_metrics", {
                        "risk_metrics": self.risk_metrics,
                        "timestamp": datetime.now().isoformat(),
                    })

                    logger.debug("Published risk metrics")
                except Exception as e:
                    logger.error(f"Error publishing risk metrics: {str(e)}")

                # Sleep for update interval
                await asyncio.sleep(self.config.get("risk_management", {}).get("metrics_interval_ms", 5000) / 1000)
        except asyncio.CancelledError:
            logger.info("Risk metrics publishing cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in risk metrics publishing: {str(e)}")

    async def _process_trade_signals(self):
        """Process trade signals."""
        # Get markets from configuration
        markets = self.config.get("market_microstructure", {}).get("markets", [])

        # Process trade signals for each market
        for market in markets:
            if market not in self.trade_signals:
                continue

            try:
                # Get trade signal
                trade_signal = self.trade_signals[market]

                # Apply risk management
                trade_order = self._apply_risk_management(market, trade_signal)

                # Update trade orders
                self.trade_orders[market] = trade_order

                logger.debug(f"Processed trade signal for {market}")
            except Exception as e:
                logger.error(f"Error processing trade signal for {market}: {str(e)}")

    async def _update_risk_metrics(self):
        """Update risk metrics."""
        try:
            # Calculate total value
            total_value = sum(position.get("value", 0.0) for position in self.portfolio.values())

            # Calculate total exposure
            total_exposure = sum(abs(position.get("value", 0.0)) for position in self.portfolio.values())

            # Update risk metrics
            self.risk_metrics.update({
                "total_value": total_value,
                "total_exposure": total_exposure,
                "last_update": datetime.now().isoformat(),
            })

            logger.debug("Updated risk metrics")
        except Exception as e:
            logger.error(f"Error updating risk metrics: {str(e)}")

    def _apply_risk_management(self, market: str, trade_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply risk management to a trade signal.

        Args:
            market: Market symbol
            trade_signal: Trade signal

        Returns:
            Dict[str, Any]: Trade order
        """
        # Get risk management parameters
        risk_params = self.config.get("risk_management", {})

        # Get max position size
        max_position_size = risk_params.get("max_position_size", 1.0)

        # Get max exposure
        max_exposure = risk_params.get("max_exposure", 0.5)

        # Get current position
        current_position = self.portfolio.get(market, {}).get("position", 0.0)

        # Get action
        action = trade_signal.get("action", "hold")

        # Get position size
        position_size = trade_signal.get("position_size", 0.0)

        # Calculate new position
        new_position = current_position

        if action == "buy":
            # Calculate remaining position size before hitting max_position_size
            remaining_size = max_position_size - current_position
            # Limit position size to remaining size
            position_size = min(position_size, remaining_size)
            new_position = current_position + position_size
        elif action == "sell":
            new_position = current_position - position_size

        # Apply max exposure
        total_exposure = sum(abs(position.get("position", 0.0)) for position in self.portfolio.values())
        total_exposure = total_exposure - abs(current_position) + abs(new_position)

        if total_exposure > max_exposure:
            # Scale down position
            scale_factor = max_exposure / total_exposure
            new_position = current_position + (new_position - current_position) * scale_factor

        # Calculate order size
        order_size = new_position - current_position

        # Determine order action
        if order_size > 0:
            order_action = "buy"
        elif order_size < 0:
            order_action = "sell"
        else:
            order_action = "hold"

        # Create trade order
        trade_order = {
            "market": market,
            "action": order_action,
            "size": abs(order_size),
            "price": 0.0,  # Market order
            "type": "market",
            "timestamp": datetime.now().isoformat(),
        }

        return trade_order

    async def _handle_trade_signal_update(self, message: Dict[str, Any]):
        """
        Handle trade signal update.

        Args:
            message: Trade signal update message
        """
        try:
            # Extract market
            market = message.get("data", {}).get("market", "")

            if not market:
                return

            # Extract trade signal
            trade_signal = message.get("data", {}).get("trade_signal", {})

            # Update trade signals
            self.trade_signals[market] = trade_signal

            logger.debug(f"Updated trade signal for {market}")
        except Exception as e:
            logger.error(f"Error handling trade signal update: {str(e)}")
