#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Q5 System Wallet State Tracker

This module tracks the state of the trading wallet, including:
- Current balance
- Active positions
- Historical trades
- Performance metrics

It synchronizes this data between the live trading system and monitoring tools.
"""

import os
import sys
import json
import logging
import asyncio
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import httpx
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/wallet_sync.log")
    ]
)
logger = logging.getLogger("q5.wallet_sync")

# Load environment variables
load_dotenv()

class WalletStateTracker:
    """
    Tracks and synchronizes wallet state between the live trading system
    and monitoring tools.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the wallet state tracker.

        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)

        # Process environment variables in config values
        self._process_env_vars()

        # Get wallet address with fallback to env var
        wallet_address_config = self.config.get("wallet", {}).get("address", "")
        self.wallet_address = self._resolve_env_var(wallet_address_config) or os.getenv("WALLET_ADDRESS", "")

        # Get RPC URL with fallback to env var
        rpc_url_config = self.config.get("solana", {}).get("rpc_url", "")
        self.rpc_url = self._resolve_env_var(rpc_url_config) or os.getenv("SOLANA_RPC_URL", "")

        # Get API keys
        self.helius_api_key = os.getenv("HELIUS_API_KEY", "")
        self.coingecko_api_key = os.getenv("COINGECKO_API_KEY", "")

        # State storage
        self.wallet_state = {
            "address": self.wallet_address,
            "balance": 0.0,
            "usd_value": 0.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "active_positions": [],
            "historical_trades": [],
            "performance": {
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "sharpe_ratio": 0.0
            }
        }

        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)

        # Paths
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.state_file = self.data_dir / "wallet_state.json"
        self.trades_file = self.data_dir / "historical_trades.csv"

        # Load existing state if available
        self._load_state()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _process_env_vars(self) -> None:
        """Process environment variables in the config recursively."""
        def process_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    process_dict(value)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            process_dict(item)
                        elif isinstance(item, str):
                            d[key][i] = self._resolve_env_var(item)
                elif isinstance(value, str):
                    d[key] = self._resolve_env_var(value)

        process_dict(self.config)

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variables in a string."""
        if not isinstance(value, str):
            return value

        # Check if the string contains environment variable references
        if "${" in value and "}" in value:
            # Extract all environment variables
            import re
            env_vars = re.findall(r'\${([^}]+)}', value)

            # Replace each environment variable with its value
            result = value
            for var in env_vars:
                env_value = os.getenv(var, "")
                result = result.replace(f"${{{var}}}", env_value)

            return result

        return value

    def _load_state(self) -> None:
        """Load wallet state from disk if available."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    self.wallet_state = json.load(f)
                logger.info(f"Loaded wallet state from {self.state_file}")

            if self.trades_file.exists():
                trades_df = pd.read_csv(self.trades_file)
                self.wallet_state["historical_trades"] = trades_df.to_dict("records")
                logger.info(f"Loaded {len(trades_df)} historical trades from {self.trades_file}")
        except Exception as e:
            logger.error(f"Error loading state: {e}")

    def _save_state(self) -> None:
        """Save wallet state to disk."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.wallet_state, f, indent=2)

            # Save trades to CSV
            trades_df = pd.DataFrame(self.wallet_state["historical_trades"])
            if not trades_df.empty:
                trades_df.to_csv(self.trades_file, index=False)

            logger.info(f"Saved wallet state to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    async def update_wallet_balance(self) -> None:
        """Update wallet SOL balance and USD value."""
        try:
            # Get SOL balance
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [self.wallet_address]
            }

            response = await self.client.post(self.rpc_url, json=payload)
            data = response.json()
            if "result" in data:
                # Convert lamports to SOL
                balance_lamports = data["result"]["value"]
                balance_sol = balance_lamports / 1_000_000_000
                self.wallet_state["balance"] = balance_sol

                # Get SOL price in USD
                sol_price = await self._get_sol_price()
                self.wallet_state["usd_value"] = balance_sol * sol_price
                self.wallet_state["last_updated"] = datetime.now(timezone.utc).isoformat()

                logger.info(f"Updated wallet balance: {balance_sol:.4f} SOL (${self.wallet_state['usd_value']:.2f})")
        except Exception as e:
            logger.error(f"Error updating wallet balance: {e}")

    async def _get_sol_price(self) -> float:
        """Get current SOL price in USD from CoinGecko."""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&x_cg_api_key={self.coingecko_api_key}"
            response = await self.client.get(url)
            data = response.json()
            return data.get("solana", {}).get("usd", 0.0)
        except Exception as e:
            logger.error(f"Error getting SOL price: {e}")
            return 0.0

    async def update_active_positions(self) -> None:
        """Update active token positions in the wallet."""
        try:
            # Use Helius API to get token balances
            url = f"https://api.helius.xyz/v0/addresses/{self.wallet_address}/balances?api-key={self.helius_api_key}"
            response = await self.client.get(url)
            data = response.json()

            tokens = data.get("tokens", [])
            active_positions = []

            for token in tokens:
                # Skip tokens with zero balance
                if token.get("amount", 0) == 0:
                    continue

                # Get token price if available
                token_price = await self._get_token_price(token.get("mint"))

                position = {
                    "mint": token.get("mint"),
                    "symbol": token.get("symbol", "Unknown"),
                    "amount": token.get("amount", 0),
                    "decimals": token.get("decimals", 0),
                    "price_usd": token_price,
                    "value_usd": token.get("amount", 0) * token_price / (10 ** token.get("decimals", 0))
                }
                active_positions.append(position)

            self.wallet_state["active_positions"] = active_positions
            logger.info(f"Updated {len(active_positions)} active positions")
        except Exception as e:
            logger.error(f"Error updating active positions: {e}")

    async def _get_token_price(self, mint_address: str) -> float:
        """Get token price in USD."""
        # Implementation would depend on available price sources
        # This is a placeholder
        return 0.0

    async def update_performance_metrics(self) -> None:
        """Update performance metrics based on historical trades."""
        try:
            trades = self.wallet_state["historical_trades"]
            if not trades:
                return

            # Convert to DataFrame for easier analysis
            trades_df = pd.DataFrame(trades)

            # Calculate basic metrics
            total_pnl = trades_df["pnl"].sum()
            wins = trades_df[trades_df["pnl"] > 0]
            losses = trades_df[trades_df["pnl"] < 0]

            win_rate = len(wins) / len(trades_df) if len(trades_df) > 0 else 0
            avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
            avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0
            largest_win = wins["pnl"].max() if len(wins) > 0 else 0
            largest_loss = losses["pnl"].min() if len(losses) > 0 else 0

            # Calculate Sharpe ratio (simplified)
            daily_returns = trades_df.groupby(pd.to_datetime(trades_df["exit_time"]).dt.date)["pnl"].sum()
            sharpe_ratio = daily_returns.mean() / daily_returns.std() if len(daily_returns) > 1 else 0

            # Update performance metrics
            self.wallet_state["performance"] = {
                "total_pnl": float(total_pnl),
                "win_rate": float(win_rate),
                "avg_win": float(avg_win),
                "avg_loss": float(avg_loss),
                "largest_win": float(largest_win),
                "largest_loss": float(largest_loss),
                "sharpe_ratio": float(sharpe_ratio)
            }

            logger.info(f"Updated performance metrics: PnL=${total_pnl:.2f}, Win Rate={win_rate:.2%}")
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")

    async def sync_with_monitoring(self) -> None:
        """Sync wallet state with monitoring systems."""
        # Implementation would depend on monitoring setup
        # This is a placeholder
        pass

    async def run(self, interval_seconds: int = 60) -> None:
        """Run the wallet state tracker continuously."""
        logger.info(f"Starting wallet state tracker for {self.wallet_address}")

        while True:
            try:
                # Update wallet state
                await self.update_wallet_balance()
                await self.update_active_positions()
                await self.update_performance_metrics()

                # Sync with monitoring
                await self.sync_with_monitoring()

                # Save state
                self._save_state()

                # Wait for next update
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in wallet state tracker: {e}")
                await asyncio.sleep(10)  # Short delay before retry

async def main():
    """Main entry point."""
    tracker = WalletStateTracker()
    await tracker.run()

if __name__ == "__main__":
    asyncio.run(main())
