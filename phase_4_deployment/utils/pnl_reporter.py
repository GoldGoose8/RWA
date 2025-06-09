#!/usr/bin/env python3
"""
PnL Reporter for Synergy7 Trading System

This script calculates and reports PnL metrics via Telegram.
It can be triggered on demand without stopping the running system.
"""

import os
import sys
import json
import logging
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pnl_reporter")

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import trading alerts module
try:
    from utils.trading_alerts import get_trading_alerts
except ImportError:
    logger.warning("Could not import trading_alerts module, using direct Telegram API")

class PnLReporter:
    """PnL Reporter for Synergy7 Trading System."""

    def __init__(self, telegram_bot_token: str, telegram_chat_id: str):
        """
        Initialize the PnL reporter.

        Args:
            telegram_bot_token: Telegram bot token
            telegram_chat_id: Telegram chat ID
        """
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Base directories
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(self.base_dir, "output")
        self.tx_history_dir = os.path.join(self.output_dir, "transactions")
        self.wallet_dir = os.path.join(self.output_dir, "wallet")

        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"Output directory: {self.output_dir}")

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def send_telegram_message(self, message: str) -> bool:
        """
        Send a message to Telegram.

        Args:
            message: Message to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"

        payload = {
            "chat_id": self.telegram_chat_id,
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

    def load_transaction_history(self) -> List[Dict[str, Any]]:
        """
        Load transaction history from files.

        Returns:
            List of transaction data
        """
        transactions = []

        # Check if transaction history directory exists
        if not os.path.exists(self.tx_history_dir):
            logger.warning(f"Transaction history directory not found: {self.tx_history_dir}")
            return transactions

        # Load transaction history files
        for filename in os.listdir(self.tx_history_dir):
            if filename.endswith(".json") and "tx_history" in filename:
                try:
                    file_path = os.path.join(self.tx_history_dir, filename)
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        if "transactions" in data:
                            transactions.extend(data["transactions"])
                except Exception as e:
                    logger.error(f"Error loading transaction history file {filename}: {str(e)}")

        # Sort transactions by timestamp
        transactions.sort(key=lambda x: x.get("timestamp", 0))

        logger.info(f"Loaded {len(transactions)} transactions")
        return transactions

    def load_wallet_balance(self) -> Dict[str, Any]:
        """
        Load wallet balance from files.

        Returns:
            Wallet balance data
        """
        wallet_balance = {}

        # Check if wallet directory exists
        if not os.path.exists(self.wallet_dir):
            logger.warning(f"Wallet directory not found: {self.wallet_dir}")
            return wallet_balance

        # Load wallet balance files
        for filename in os.listdir(self.wallet_dir):
            if filename.endswith(".json") and "wallet_balance" in filename:
                try:
                    file_path = os.path.join(self.wallet_dir, filename)
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        wallet_balance = data
                except Exception as e:
                    logger.error(f"Error loading wallet balance file {filename}: {str(e)}")

        logger.info(f"Loaded wallet balance data")
        return wallet_balance

    def calculate_pnl_metrics(self, transactions: List[Dict[str, Any]], wallet_balance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate PnL metrics from transaction history and wallet balance.

        Args:
            transactions: Transaction history
            wallet_balance: Wallet balance data

        Returns:
            PnL metrics
        """
        # Initialize metrics
        metrics = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "buy_trades": 0,
            "sell_trades": 0,
            "total_volume_usdc": 0.0,  # Volume in USDC (price * size)
            "total_volume_sol": 0.0,   # Volume in SOL (size)
            "total_volume_usd": 0.0,
            "total_fees_sol": 0.0,
            "total_fees_usd": 0.0,
            "total_profit_sol": 0.0,
            "total_profit_usd": 0.0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "avg_profit_per_trade_sol": 0.0,
            "avg_profit_per_trade_usd": 0.0,
            "max_profit_sol": 0.0,
            "max_loss_sol": 0.0,
            "current_position": None,
            "open_positions": [],
            "closed_positions": [],
            "initial_balance_sol": 0.0,
            "current_balance_sol": 0.0,
            "pnl_sol": 0.0,
            "pnl_pct": 0.0,
            "sol_price_usd": 180.0,  # Default SOL price (May 2024)
            "start_time": None,
            "end_time": None,
            "duration": None,
            "winning_trades": []  # Store details of winning trades
        }

        # Get SOL price from environment or default
        sol_price_usd = float(os.environ.get("SOL_PRICE_USD", 180.0))
        metrics["sol_price_usd"] = sol_price_usd

        # Calculate initial and current balance
        if wallet_balance:
            # Extract wallet balance
            if isinstance(wallet_balance, dict) and "wallet_balance" in wallet_balance:
                wallet_data = wallet_balance["wallet_balance"]

                # Sum up all wallet balances
                total_balance = 0.0
                for key, value in wallet_data.items():
                    if isinstance(value, (int, float)):
                        total_balance += float(value)
                    elif isinstance(value, dict):
                        total_balance += sum(float(v) for v in value.values() if isinstance(v, (int, float)))

                metrics["current_balance_sol"] = total_balance

            # Get initial balance from config or first transaction
            if "initial_balance" in wallet_balance:
                # Use the initial balance from the wallet_balance file
                initial_balance = float(wallet_balance["initial_balance"])
                # Accept the initial balance as is (40 SOL = 1000 USD at $25/SOL)
                metrics["initial_balance_sol"] = initial_balance
                logger.info(f"Using initial balance from wallet_balance: {initial_balance} SOL (${initial_balance * sol_price_usd:.2f})")
            elif transactions and "pre_balance" in transactions[0]:
                initial_balance = float(transactions[0]["pre_balance"])
                metrics["initial_balance_sol"] = initial_balance
                logger.info(f"Using initial balance from first transaction: {initial_balance} SOL (${initial_balance * sol_price_usd:.2f})")
            else:
                # Default to current balance minus profit
                metrics["initial_balance_sol"] = metrics["current_balance_sol"]

        # Process transactions
        position_map = {}  # Map to track open positions

        for tx in transactions:
            # Skip invalid transactions
            if "status" not in tx or tx["status"] not in ["confirmed", "finalized"]:
                metrics["failed_trades"] += 1
                continue

            # Count successful trades
            metrics["total_trades"] += 1
            metrics["successful_trades"] += 1

            # Extract transaction data
            tx_type = tx.get("type", "unknown")
            action = tx.get("action", "unknown").upper()
            market = tx.get("market", "unknown")
            price = float(tx.get("price", 0.0))
            size = float(tx.get("size", 0.0))
            fee = float(tx.get("fee", 0.0))
            timestamp = tx.get("timestamp", 0)

            # Update time range
            if metrics["start_time"] is None or timestamp < metrics["start_time"]:
                metrics["start_time"] = timestamp
            if metrics["end_time"] is None or timestamp > metrics["end_time"]:
                metrics["end_time"] = timestamp

            # Calculate volume
            volume_usdc = price * size  # This is in USDC (price is in USDC per SOL)
            volume_sol = size           # This is the actual SOL amount traded
            volume_usd = volume_usdc    # USDC is approximately 1:1 with USD

            # Update volume metrics
            metrics["total_volume_usdc"] += volume_usdc
            metrics["total_volume_sol"] += volume_sol
            metrics["total_volume_usd"] += volume_usd
            metrics["total_fees_sol"] += fee
            metrics["total_fees_usd"] += fee * sol_price_usd

            # Track buy/sell trades
            if action == "BUY":
                metrics["buy_trades"] += 1

                # Create or update position
                position_key = f"{market}"
                if position_key not in position_map:
                    position_map[position_key] = {
                        "market": market,
                        "entry_price": price,
                        "entry_size": size,
                        "entry_time": timestamp,
                        "exit_price": None,
                        "exit_size": None,
                        "exit_time": None,
                        "profit_sol": None,
                        "profit_pct": None,
                        "status": "open"
                    }
                else:
                    # Average down/up
                    position = position_map[position_key]
                    total_size = position["entry_size"] + size
                    position["entry_price"] = ((position["entry_price"] * position["entry_size"]) + (price * size)) / total_size
                    position["entry_size"] = total_size
                    position["status"] = "open"

            elif action == "SELL":
                metrics["sell_trades"] += 1

                # Find matching position
                position_key = f"{market}"
                if position_key in position_map:
                    position = position_map[position_key]

                    # Calculate profit/loss
                    if position["entry_price"] > 0 and position["entry_size"] > 0:
                        # Calculate profit in SOL
                        profit_sol = (price - position["entry_price"]) * min(size, position["entry_size"])
                        profit_pct = (price - position["entry_price"]) / position["entry_price"] * 100

                        # Update position
                        position["exit_price"] = price
                        position["exit_size"] = size
                        position["exit_time"] = timestamp
                        position["profit_sol"] = profit_sol
                        position["profit_pct"] = profit_pct

                        # Update metrics
                        metrics["total_profit_sol"] += profit_sol
                        metrics["total_profit_usd"] += profit_sol * sol_price_usd

                        if profit_sol > 0:
                            metrics["win_count"] += 1
                            metrics["max_profit_sol"] = max(metrics["max_profit_sol"], profit_sol)

                            # Store winning trade details for reporting
                            winning_trade = {
                                "market": market,
                                "entry_price": position["entry_price"],
                                "exit_price": price,
                                "size": min(size, position["entry_size"]),
                                "profit_sol": profit_sol,
                                "profit_pct": profit_pct,
                                "entry_time": datetime.fromtimestamp(position["entry_time"]).strftime("%Y-%m-%d %H:%M:%S") if isinstance(position["entry_time"], (int, float)) else position["entry_time"],
                                "exit_time": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                            }
                            metrics["winning_trades"].append(winning_trade)
                        else:
                            metrics["loss_count"] += 1
                            metrics["max_loss_sol"] = min(metrics["max_loss_sol"], profit_sol)

                        # Check if position is fully closed
                        if size >= position["entry_size"]:
                            position["status"] = "closed"
                            metrics["closed_positions"].append(position.copy())

                            # Reduce position size or remove if fully closed
                            if size > position["entry_size"]:
                                # Create a new position for the excess
                                new_position = {
                                    "market": market,
                                    "entry_price": price,
                                    "entry_size": size - position["entry_size"],
                                    "entry_time": timestamp,
                                    "exit_price": None,
                                    "exit_size": None,
                                    "exit_time": None,
                                    "profit_sol": None,
                                    "profit_pct": None,
                                    "status": "open"
                                }
                                position_map[position_key] = new_position
                            else:
                                # Remove fully closed position
                                del position_map[position_key]
                        else:
                            # Reduce position size
                            position["entry_size"] -= size

        # Add open positions to metrics
        metrics["open_positions"] = [pos for pos in position_map.values() if pos["status"] == "open"]
        metrics["current_position"] = metrics["open_positions"][0] if metrics["open_positions"] else None

        # Calculate derived metrics
        if metrics["total_trades"] > 0:
            metrics["avg_profit_per_trade_sol"] = metrics["total_profit_sol"] / metrics["total_trades"]
            metrics["avg_profit_per_trade_usd"] = metrics["total_profit_usd"] / metrics["total_trades"]

        if metrics["win_count"] + metrics["loss_count"] > 0:
            metrics["win_rate"] = metrics["win_count"] / (metrics["win_count"] + metrics["loss_count"]) * 100

        # Calculate PnL
        metrics["pnl_sol"] = metrics["total_profit_sol"] - metrics["total_fees_sol"]

        if metrics["initial_balance_sol"] > 0:
            metrics["pnl_pct"] = (metrics["pnl_sol"] / metrics["initial_balance_sol"]) * 100

        # Calculate duration
        if metrics["start_time"] is not None and metrics["end_time"] is not None:
            start_dt = datetime.fromtimestamp(metrics["start_time"])
            end_dt = datetime.fromtimestamp(metrics["end_time"])
            metrics["duration"] = (end_dt - start_dt).total_seconds() / 3600  # Hours

        return metrics

    def format_pnl_message(self, metrics: Dict[str, Any]) -> str:
        """
        Format PnL metrics as a Telegram message.

        Args:
            metrics: PnL metrics

        Returns:
            Formatted message
        """
        # Format timestamps
        start_time_str = datetime.fromtimestamp(metrics["start_time"]).strftime("%Y-%m-%d %H:%M:%S") if metrics["start_time"] else "N/A"
        end_time_str = datetime.fromtimestamp(metrics["end_time"]).strftime("%Y-%m-%d %H:%M:%S") if metrics["end_time"] else "N/A"
        duration_str = f"{metrics['duration']:.2f}" if metrics["duration"] is not None else "N/A"

        # Handle current position
        current_position_str = "None"
        if metrics["current_position"] and isinstance(metrics["current_position"], dict) and "market" in metrics["current_position"]:
            current_position_str = metrics["current_position"]["market"]

        # Create message
        message = f"""
📊 *Synergy7 Trading System - PnL Report* 📊

*Trading Period*:
- Start: {start_time_str}
- End: {end_time_str}
- Duration: {duration_str} hours

*Balance*:
- Initial: {metrics["initial_balance_sol"]:.4f} SOL (${metrics["initial_balance_sol"] * metrics["sol_price_usd"]:.2f})
- Current: {metrics["current_balance_sol"]:.4f} SOL (${metrics["current_balance_sol"] * metrics["sol_price_usd"]:.2f})

*Profit & Loss*:
- Total P&L: {metrics["pnl_sol"]:.4f} SOL (${metrics["pnl_sol"] * metrics["sol_price_usd"]:.2f})
- P&L %: {metrics["pnl_pct"]:.2f}%
- Fees Paid: {metrics["total_fees_sol"]:.4f} SOL (${metrics["total_fees_sol"] * metrics["sol_price_usd"]:.2f})

*Trading Activity*:
- Total Trades: {metrics["total_trades"]}
- Successful: {metrics["successful_trades"]}
- Failed: {metrics["failed_trades"]}
- Buy Trades: {metrics["buy_trades"]}
- Sell Trades: {metrics["sell_trades"]}

*Performance*:
- Win/Loss: {metrics["win_count"]}/{metrics["loss_count"]}
- Win Rate: {metrics["win_rate"]:.2f}%
- Avg Profit/Trade: {metrics["avg_profit_per_trade_sol"]:.4f} SOL (${metrics["avg_profit_per_trade_usd"]:.2f})
- Max Profit: {metrics["max_profit_sol"]:.4f} SOL
- Max Loss: {metrics["max_loss_sol"]:.4f} SOL

*Volume*:
- Total Volume (SOL): {metrics["total_volume_sol"]:.4f} SOL
- Total Volume (USD): ${metrics["total_volume_usd"]:.2f}

*Current Position*: {current_position_str}
"""

        # Add winning trades section if there are any
        if metrics["winning_trades"]:
            message += "\n*Winning Trades*:\n"
            for i, trade in enumerate(metrics["winning_trades"], 1):
                message += f"{i}. {trade['market']}: Entry ${trade['entry_price']:.4f} → Exit ${trade['exit_price']:.4f} | "
                message += f"Size: {trade['size']:.4f} | "
                message += f"Profit: {trade['profit_sol']:.4f} SOL ({trade['profit_pct']:.2f}%)\n"

        message += f"\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message

    async def report_pnl(self) -> bool:
        """
        Calculate and report PnL metrics via Telegram.

        Returns:
            bool: True if report was sent successfully, False otherwise
        """
        try:
            # Load data
            transactions = self.load_transaction_history()
            wallet_balance = self.load_wallet_balance()

            # Calculate metrics
            metrics = self.calculate_pnl_metrics(transactions, wallet_balance)

            # Format message
            message = self.format_pnl_message(metrics)

            # Send message
            success = await self.send_telegram_message(message)

            return success
        except Exception as e:
            logger.error(f"Error reporting PnL: {str(e)}")
            return False

async def main():
    """Main function."""
    # Get Telegram credentials from environment or use hardcoded values
    # Note: In production, these should be loaded from environment variables
    telegram_bot_token = "8081711336:AAHkahgcFf3Fy5V9Bdy8dB5AyE4o-8BsyrQ"
    telegram_chat_id = "5135869709"

    # Create PnL reporter
    reporter = PnLReporter(telegram_bot_token, telegram_chat_id)

    # Report PnL
    success = await reporter.report_pnl()

    # Close HTTP client
    await reporter.close()

    if success:
        logger.info("PnL report sent successfully")
    else:
        logger.error("Failed to send PnL report")

if __name__ == "__main__":
    asyncio.run(main())
