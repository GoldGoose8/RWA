#!/usr/bin/env python3
"""
Trading Alerts Module

This module provides functions for sending trading-related alerts via Telegram,
including trade notifications, performance metrics, and system metrics.
"""

import os
import json
import logging
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("trading_alerts")

class TradingAlerts:
    """Trading alerts for the Synergy7 Trading System."""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize the trading alerts.

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Initialize metrics storage
        self.metrics = {
            'wallet_balance': 0.0,
            'initial_balance': 0.0,
            'total_pnl_usd': 0.0,
            'total_pnl_pct': 0.0,
            'win_count': 0,
            'loss_count': 0,
            'total_trades': 0,
            'avg_profit_per_trade': 0.0,
            'max_drawdown': 0.0,
            'signals_generated': 0,
            'signals_filtered': 0,
            'current_position': None
        }

        # Trade history
        self.trade_history = []

        logger.info("Initialized trading alerts")

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def send_message(self, message: str) -> bool:
        """
        Send a message to Telegram.

        Args:
            message: Message to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Sent Telegram message")
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False

    async def send_trade_notification(self, trade_data: Dict[str, Any]) -> bool:
        """
        Send a trade notification.

        Args:
            trade_data: Trade data

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        # Extract trade data
        action = trade_data.get('action', 'unknown').upper()
        market = trade_data.get('market', 'unknown')
        price = trade_data.get('price', 0.0)
        size = trade_data.get('size', 0.0)
        confidence = trade_data.get('confidence', 0.0)
        timestamp = trade_data.get('timestamp', datetime.now().isoformat())

        # Format message
        if action == 'BUY':
            emoji = "🟢"
        elif action == 'SELL':
            emoji = "🔴"
        else:
            emoji = "⚪"

        message = f"{emoji} *TRADE NOTIFICATION: {action}*\n\n"
        message += f"*Market*: {market}\n"
        message += f"*Price*: ${price:.4f}\n"
        message += f"*Size*: {size:.4f}\n"
        message += f"*Total*: ${price * size:.2f}\n"
        message += f"*Confidence*: {confidence:.2f}\n"
        message += f"*Time*: {timestamp}\n"

        # Add to trade history
        self.trade_history.append(trade_data)
        self.metrics['total_trades'] += 1

        # Update current position
        if action == 'BUY':
            self.metrics['current_position'] = {
                'market': market,
                'entry_price': price,
                'size': size,
                'entry_time': timestamp
            }
        elif action == 'SELL' and self.metrics['current_position']:
            # Calculate profit/loss
            entry_price = self.metrics['current_position'].get('entry_price', 0.0)
            entry_size = self.metrics['current_position'].get('size', 0.0)

            if entry_price > 0:
                pnl_usd = (price - entry_price) * min(size, entry_size)
                pnl_pct = (price - entry_price) / entry_price * 100

                # Update metrics
                self.metrics['total_pnl_usd'] += pnl_usd

                if pnl_usd > 0:
                    self.metrics['win_count'] += 1
                else:
                    self.metrics['loss_count'] += 1

                # Add profit/loss to message
                message += f"\n*Profit/Loss*: ${pnl_usd:.2f} ({pnl_pct:.2f}%)\n"

                if pnl_usd > 0:
                    message += "✅ *Profitable Trade*\n\n"

                    # Add detailed trade summary for winning trades
                    message += "*Trade Summary*:\n"
                    message += f"Entry: ${entry_price:.4f} at {self.metrics['current_position'].get('entry_time', 'unknown')}\n"
                    message += f"Exit: ${price:.4f} at {timestamp}\n"
                    message += f"Size: {min(size, entry_size):.4f}\n"
                    message += f"Holding Period: {self._calculate_holding_period(self.metrics['current_position'].get('entry_time', timestamp), timestamp)}\n"
                    message += f"ROI: {pnl_pct:.2f}%"
                else:
                    message += "❌ *Losing Trade*"

            # Reset current position
            self.metrics['current_position'] = None

        return await self.send_message(message)

    async def send_performance_metrics(self) -> bool:
        """
        Send performance metrics.

        Returns:
            bool: True if metrics were sent successfully, False otherwise
        """
        # Calculate derived metrics
        if self.metrics['total_trades'] > 0:
            self.metrics['avg_profit_per_trade'] = self.metrics['total_pnl_usd'] / self.metrics['total_trades']

        if self.metrics['win_count'] + self.metrics['loss_count'] > 0:
            win_rate = self.metrics['win_count'] / (self.metrics['win_count'] + self.metrics['loss_count']) * 100
        else:
            win_rate = 0.0

        if self.metrics['initial_balance'] > 0:
            self.metrics['total_pnl_pct'] = self.metrics['total_pnl_usd'] / self.metrics['initial_balance'] * 100

        # Format message
        message = "📊 *PERFORMANCE METRICS*\n\n"

        message += f"*Wallet Balance*: ${self.metrics['wallet_balance']:.2f}\n"
        message += f"*Total P&L*: ${self.metrics['total_pnl_usd']:.2f} ({self.metrics['total_pnl_pct']:.2f}%)\n"
        message += f"*Win/Loss*: {self.metrics['win_count']}/{self.metrics['loss_count']}\n"
        message += f"*Win Rate*: {win_rate:.2f}%\n"
        message += f"*Total Trades*: {self.metrics['total_trades']}\n"
        message += f"*Avg Profit/Trade*: ${self.metrics['avg_profit_per_trade']:.2f}\n"
        message += f"*Max Drawdown*: {self.metrics['max_drawdown']:.2f}%\n"

        if self.metrics['current_position']:
            message += f"\n*Current Position*: {self.metrics['current_position']['market']}\n"
            message += f"*Entry Price*: ${self.metrics['current_position']['entry_price']:.4f}\n"
            message += f"*Size*: {self.metrics['current_position']['size']:.4f}\n"
        else:
            message += "\n*Current Position*: None\n"

        message += f"\n*Time*: {datetime.now().isoformat()}"

        return await self.send_message(message)

    async def send_system_metrics(self, system_data: Dict[str, Any]) -> bool:
        """
        Send system metrics.

        Args:
            system_data: System metrics data

        Returns:
            bool: True if metrics were sent successfully, False otherwise
        """
        # Extract system data
        signals_generated = system_data.get('signals_generated', 0)
        signals_filtered = system_data.get('signals_filtered', 0)
        filter_effectiveness = 0.0

        if signals_generated > 0:
            filter_effectiveness = signals_filtered / signals_generated * 100

        # Update metrics
        self.metrics['signals_generated'] = signals_generated
        self.metrics['signals_filtered'] = signals_filtered

        # Format message
        message = "🖥️ *SYSTEM METRICS*\n\n"

        message += f"*Signals Generated*: {signals_generated}\n"
        message += f"*Signals Filtered*: {signals_filtered}\n"
        message += f"*Filter Effectiveness*: {filter_effectiveness:.2f}%\n"

        # Add component status
        if 'components' in system_data:
            message += "\n*Component Status*:\n"
            for component, status in system_data['components'].items():
                emoji = "✅" if status else "❌"
                message += f"{emoji} {component}\n"

        message += f"\n*Time*: {datetime.now().isoformat()}"

        return await self.send_message(message)

    def update_wallet_balance(self, balance: float, is_initial: bool = False) -> None:
        """
        Update wallet balance.

        Args:
            balance: Wallet balance in USD
            is_initial: Whether this is the initial balance
        """
        self.metrics['wallet_balance'] = balance

        if is_initial:
            self.metrics['initial_balance'] = balance

    def update_max_drawdown(self, drawdown: float) -> None:
        """
        Update maximum drawdown.

        Args:
            drawdown: Drawdown percentage
        """
        self.metrics['max_drawdown'] = max(self.metrics['max_drawdown'], drawdown)

    def _calculate_holding_period(self, entry_time, exit_time) -> str:
        """
        Calculate the holding period between entry and exit times.

        Args:
            entry_time: Entry timestamp (can be string ISO format or timestamp)
            exit_time: Exit timestamp (can be string ISO format or timestamp)

        Returns:
            Formatted holding period string
        """
        try:
            # Convert entry_time to datetime if it's a timestamp or ISO string
            if isinstance(entry_time, (int, float)):
                entry_dt = datetime.fromtimestamp(entry_time)
            elif isinstance(entry_time, str):
                try:
                    entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                except ValueError:
                    # If ISO parsing fails, try a common format
                    entry_dt = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
            else:
                return "unknown"

            # Convert exit_time to datetime if it's a timestamp or ISO string
            if isinstance(exit_time, (int, float)):
                exit_dt = datetime.fromtimestamp(exit_time)
            elif isinstance(exit_time, str):
                try:
                    exit_dt = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                except ValueError:
                    # If ISO parsing fails, try a common format
                    exit_dt = datetime.strptime(exit_time, "%Y-%m-%d %H:%M:%S")
            else:
                return "unknown"

            # Calculate the difference
            diff = exit_dt - entry_dt

            # Format the holding period
            total_seconds = diff.total_seconds()

            if total_seconds < 60:
                return f"{int(total_seconds)} seconds"
            elif total_seconds < 3600:
                return f"{int(total_seconds / 60)} minutes"
            elif total_seconds < 86400:
                hours = int(total_seconds / 3600)
                minutes = int((total_seconds % 3600) / 60)
                return f"{hours} hours, {minutes} minutes"
            else:
                days = int(total_seconds / 86400)
                hours = int((total_seconds % 86400) / 3600)
                return f"{days} days, {hours} hours"
        except Exception as e:
            logger.error(f"Error calculating holding period: {str(e)}")
            return "unknown"

# Create a global instance for easy access
_trading_alerts = None

def get_trading_alerts() -> TradingAlerts:
    """
    Get the global trading alerts instance.

    Returns:
        TradingAlerts instance
    """
    global _trading_alerts

    if _trading_alerts is None:
        # Get Telegram credentials from environment
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

        if bot_token and chat_id:
            _trading_alerts = TradingAlerts(bot_token, chat_id)
        else:
            logger.warning("Telegram credentials not found in environment variables")
            # Use default values for testing
            _trading_alerts = TradingAlerts('', '')

    return _trading_alerts

async def send_trade_alert(trade_data: Dict[str, Any]) -> bool:
    """
    Send a trade alert.

    Args:
        trade_data: Trade data

    Returns:
        bool: True if alert was sent successfully, False otherwise
    """
    alerts = get_trading_alerts()
    return await alerts.send_trade_notification(trade_data)

async def send_metrics_alert() -> bool:
    """
    Send a metrics alert.

    Returns:
        bool: True if alert was sent successfully, False otherwise
    """
    alerts = get_trading_alerts()
    return await alerts.send_performance_metrics()

async def send_system_alert(system_data: Dict[str, Any]) -> bool:
    """
    Send a system alert.

    Args:
        system_data: System data

    Returns:
        bool: True if alert was sent successfully, False otherwise
    """
    alerts = get_trading_alerts()
    return await alerts.send_system_metrics(system_data)
