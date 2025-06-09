#!/usr/bin/env python3
"""
Trade Metrics Display for Synergy7 Trading System

This script displays real-time trade metrics in the terminal using rich text formatting.
It monitors the metrics files and updates the display as new data becomes available.
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.traceback import install as install_rich_traceback
except ImportError:
    print("Rich library not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.traceback import install as install_rich_traceback

# Install rich traceback handler
install_rich_traceback()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="output/logs/trade_metrics_display.log"
)
logger = logging.getLogger("trade_metrics_display")

class TradeMetricsDisplay:
    """
    Display trade metrics in the terminal using rich text formatting.
    """

    def __init__(self, metrics_dir: str, refresh_interval: float = 1.0, max_trades: int = 10):
        """
        Initialize the trade metrics display.

        Args:
            metrics_dir: Directory containing metrics files
            refresh_interval: Refresh interval in seconds
            max_trades: Maximum number of trades to display
        """
        self.metrics_dir = Path(metrics_dir)
        self.refresh_interval = refresh_interval
        self.max_trades = max_trades
        self.console = Console()
        self.layout = self._create_layout()
        self.trades = []
        self.portfolio = {
            "balance": 0.0,
            "equity": 0.0,
            "pnl": 0.0,
            "positions": {}
        }
        self.metrics = {
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        }
        self.system_metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "api_calls": 0,
            "errors": 0
        }
        self.market_data = {}
        self.start_time = datetime.now()
        self.last_update = datetime.now()

        # Create output directory for logs
        os.makedirs("output/logs", exist_ok=True)

        logger.info(f"Initialized trade metrics display with metrics_dir: {metrics_dir}")

    def _create_layout(self) -> Layout:
        """
        Create the layout for the display.

        Returns:
            Layout object
        """
        layout = Layout(name="root")

        # Split into header and body
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body")
        )

        # Split body into left and right
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )

        # Split left into trades and portfolio
        layout["left"].split(
            Layout(name="trades", ratio=3),
            Layout(name="portfolio", ratio=2)
        )

        # Split right into metrics and system
        layout["right"].split(
            Layout(name="metrics", ratio=2),
            Layout(name="system", ratio=1),
            Layout(name="market", ratio=2)
        )

        return layout

    def _generate_header(self) -> Panel:
        """
        Generate the header panel.

        Returns:
            Panel object
        """
        now = datetime.now()
        runtime = now - self.start_time
        hours, remainder = divmod(runtime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        title = Text("Synergy7 Trading System - Live Metrics", style="bold cyan")
        subtitle = Text(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} | Running: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} | Last Update: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}", style="dim")

        header_text = Text()
        header_text.append(title)
        header_text.append("\n")
        header_text.append(subtitle)

        return Panel(header_text, border_style="blue")

    def _generate_trades_panel(self) -> Panel:
        """
        Generate the trades panel.

        Returns:
            Panel object
        """
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Time", style="dim", width=10)
        table.add_column("Market", style="cyan")
        table.add_column("Action", style="green")
        table.add_column("Amount", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Value", justify="right")
        table.add_column("Status", style="yellow")

        for trade in self.trades[:self.max_trades]:
            # Format timestamp
            timestamp = datetime.fromisoformat(trade["timestamp"])
            time_str = timestamp.strftime("%H:%M:%S")

            # Format action with color
            action = trade["action"]
            action_style = "green" if action == "buy" else "red"
            action_text = Text(action.upper(), style=action_style)

            # Format status with color
            status = trade["status"]
            status_style = "green" if status == "executed" else "red"

            # Format values
            amount = f"{trade['amount']:.4f}"
            price = f"${trade['price']:.2f}"
            value = f"${trade['value']:.2f}"

            table.add_row(
                time_str,
                trade["market"],
                action_text,
                amount,
                price,
                value,
                Text(status, style=status_style)
            )

        return Panel(table, title="Recent Trades", border_style="green")

    def _generate_portfolio_panel(self) -> Panel:
        """
        Generate the portfolio panel.

        Returns:
            Panel object
        """
        # Create main table
        table = Table(show_header=True, header_style="bold yellow", expand=True)
        table.add_column("Metric", style="yellow")
        table.add_column("Value", justify="right", style="cyan")

        # Add portfolio metrics
        table.add_row("Balance", f"${self.portfolio['balance']:.2f}")
        table.add_row("Equity", f"${self.portfolio['equity']:.2f}")

        # Format P&L with color
        pnl = self.portfolio['pnl']
        pnl_style = "green" if pnl >= 0 else "red"
        pnl_text = Text(f"${pnl:.2f}", style=pnl_style)
        pnl_change = f"{pnl / (self.portfolio['equity'] - pnl) * 100:.2f}%" if pnl != 0 and self.portfolio['equity'] != pnl else "0.00%"
        pnl_change_text = Text(f" ({pnl_change})", style=pnl_style)

        pnl_row = Text()
        pnl_row.append(pnl_text)
        pnl_row.append(pnl_change_text)

        table.add_row("P&L", pnl_row)

        # Create positions table if there are positions
        positions_text = Text()

        if self.portfolio["positions"]:
            positions_table = Table(show_header=True, header_style="bold blue", box=None)
            positions_table.add_column("Market", style="cyan")
            positions_table.add_column("Amount", justify="right")
            positions_table.add_column("Value", justify="right")

            for market, position in self.portfolio["positions"].items():
                if position["amount"] > 0:
                    positions_table.add_row(
                        market,
                        f"{position['amount']:.4f}",
                        f"${position['value']:.2f}"
                    )

            positions_text.append(Text("\n\n[bold]Positions:[/bold]\n"))
            positions_text.append(Text(str(positions_table)))

        # Combine tables
        portfolio_content = Text()
        portfolio_content.append(Text(str(table)))
        portfolio_content.append(positions_text)

        return Panel(portfolio_content, title="Portfolio", border_style="yellow")

    def _generate_metrics_panel(self) -> Panel:
        """
        Generate the metrics panel.

        Returns:
            Panel object
        """
        table = Table(show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        # Add performance metrics
        win_rate = f"{self.metrics['win_rate'] * 100:.2f}%"
        profit_factor = f"{self.metrics['profit_factor']:.2f}"
        sharpe_ratio = f"{self.metrics['sharpe_ratio']:.2f}"
        max_drawdown = f"{self.metrics['max_drawdown'] * 100:.2f}%"

        table.add_row("Win Rate", win_rate)
        table.add_row("Profit Factor", profit_factor)
        table.add_row("Sharpe Ratio", sharpe_ratio)
        table.add_row("Max Drawdown", max_drawdown)

        # Add trade statistics
        total_trades = len(self.trades)
        successful_trades = len([t for t in self.trades if t["status"] == "executed"])
        failed_trades = total_trades - successful_trades

        table.add_row("Total Trades", str(total_trades))
        table.add_row("Successful", str(successful_trades))
        table.add_row("Failed", str(failed_trades))

        return Panel(table, title="Performance Metrics", border_style="cyan")

    def _generate_system_panel(self) -> Panel:
        """
        Generate the system panel.

        Returns:
            Panel object
        """
        # Create progress bars for CPU and memory
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[bold]{task.percentage:.0f}%"),
            expand=True
        )

        cpu_task = progress.add_task("CPU", total=100, completed=self.system_metrics["cpu_usage"])
        memory_task = progress.add_task("MEM", total=100, completed=self.system_metrics["memory_usage"])

        # Create table for other metrics
        table = Table(show_header=True, header_style="bold red", box=None, expand=True)
        table.add_column("Metric", style="red")
        table.add_column("Value", justify="right")

        table.add_row("API Calls", str(self.system_metrics["api_calls"]))
        table.add_row("Errors", str(self.system_metrics["errors"]))

        # Combine progress and table
        system_content = Text()
        system_content.append(Text(str(progress)))
        system_content.append("\n\n")
        system_content.append(Text(str(table)))

        return Panel(system_content, title="System Health", border_style="red")

    def _generate_market_panel(self) -> Panel:
        """
        Generate the market panel.

        Returns:
            Panel object
        """
        table = Table(show_header=True, header_style="bold green", expand=True)
        table.add_column("Market", style="cyan")
        table.add_column("Price", justify="right")
        table.add_column("Change", justify="right")

        for market, data in self.market_data.items():
            # Format price
            price = f"${data['price']:.4f}"

            # Format change with color
            change = data["change_24h"]
            change_style = "green" if change >= 0 else "red"
            change_text = Text(f"{change:.2f}%", style=change_style)

            table.add_row(market, price, change_text)

        return Panel(table, title="Market Data", border_style="green")

    def update_display(self) -> Layout:
        """
        Update the display with current data.

        Returns:
            Updated layout
        """
        # Update layout components
        self.layout["header"].update(self._generate_header())
        self.layout["trades"].update(self._generate_trades_panel())
        self.layout["portfolio"].update(self._generate_portfolio_panel())
        self.layout["metrics"].update(self._generate_metrics_panel())
        self.layout["system"].update(self._generate_system_panel())
        self.layout["market"].update(self._generate_market_panel())

        return self.layout

    def load_metrics(self) -> bool:
        """
        Load metrics from files.

        Returns:
            True if metrics were loaded, False otherwise
        """
        try:
            # Check for simulation data file
            simulation_file = self.metrics_dir / "simulation_data.json"
            if simulation_file.exists():
                with open(simulation_file, "r") as f:
                    data = json.load(f)

                # Update trades
                self.trades = data.get("trades", [])

                # Update portfolio
                self.portfolio = data.get("portfolio", {})

                # Update metrics
                self.metrics = data.get("metrics", {}).get("performance", {})

                # Update system metrics
                self.system_metrics = data.get("metrics", {}).get("system", {})

                # Update market data
                self.market_data = data.get("market_data", {})

                self.last_update = datetime.now()
                return True

            # Check for live trade test files
            trade_file = self.metrics_dir / "trade_details.json"
            if trade_file.exists():
                with open(trade_file, "r") as f:
                    trade_data = json.load(f)
                    self.trades = [trade_data]

                # Check for close details
                close_file = self.metrics_dir / "close_details.json"
                if close_file.exists():
                    with open(close_file, "r") as f:
                        close_data = json.load(f)
                        self.trades.append(close_data)

                # Update portfolio (simulated)
                self.portfolio = {
                    "balance": 10000.0,
                    "equity": 10000.0 + (trade_data.get("value", 0) - trade_data.get("fee", 0)),
                    "pnl": trade_data.get("value", 0) - trade_data.get("fee", 0),
                    "positions": {
                        trade_data.get("market", "Unknown"): {
                            "amount": trade_data.get("amount", 0),
                            "value": trade_data.get("value", 0)
                        }
                    }
                }

                # Update metrics (simulated)
                self.metrics = {
                    "win_rate": 0.5,
                    "profit_factor": 1.5,
                    "sharpe_ratio": 1.0,
                    "max_drawdown": 0.05
                }

                # Update system metrics (simulated)
                self.system_metrics = {
                    "cpu_usage": 20.0,
                    "memory_usage": 30.0,
                    "api_calls": 100,
                    "errors": 0
                }

                # Update market data (simulated)
                self.market_data = {
                    trade_data.get("market", "Unknown"): {
                        "price": trade_data.get("price", 0),
                        "change_24h": 1.5
                    }
                }

                self.last_update = datetime.now()
                return True

            # Check for metrics API
            try:
                import requests
                response = requests.get("http://localhost:8080/metrics", timeout=1)
                if response.status_code == 200:
                    metrics_data = response.json()

                    # Update trades
                    transactions = metrics_data.get("transactions", {})
                    self.trades = []
                    for tx_id, tx_data in transactions.items():
                        self.trades.append({
                            "id": tx_id,
                            "timestamp": tx_data.get("timestamp", datetime.now().isoformat()),
                            "market": tx_data.get("market", "Unknown"),
                            "action": tx_data.get("action", "buy"),
                            "amount": tx_data.get("amount", 0),
                            "price": tx_data.get("price", 0),
                            "value": tx_data.get("value", 0),
                            "status": tx_data.get("status", "executed"),
                            "fee": tx_data.get("fee", 0)
                        })

                    # Update portfolio
                    wallet_balances = metrics_data.get("wallet_balances", {})
                    self.portfolio = {
                        "balance": next(iter(wallet_balances.values()), {}).get("balance", 0),
                        "equity": next(iter(wallet_balances.values()), {}).get("balance", 0),
                        "pnl": 0.0,
                        "positions": {}
                    }

                    # Update market data
                    market_microstructure = metrics_data.get("market_microstructure", {})
                    self.market_data = {}
                    for market, data in market_microstructure.items():
                        self.market_data[market] = {
                            "price": 0.0,  # Not provided in the API
                            "change_24h": 0.0  # Not provided in the API
                        }

                    self.last_update = datetime.now()
                    return True
            except Exception as e:
                logger.warning(f"Error fetching metrics from API: {str(e)}")

            return False
        except Exception as e:
            logger.error(f"Error loading metrics: {str(e)}")
            return False

    def run(self):
        """Run the trade metrics display."""
        logger.info("Starting trade metrics display...")

        try:
            with Live(self.update_display(), refresh_per_second=1/self.refresh_interval) as live:
                while True:
                    # Load metrics
                    self.load_metrics()

                    # Update display
                    live.update(self.update_display())

                    # Wait for next update
                    time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            logger.info("Trade metrics display stopped by user")
        except Exception as e:
            logger.error(f"Error in trade metrics display: {str(e)}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Display trade metrics in the terminal")
    parser.add_argument("--metrics-dir", default="output/dashboard", help="Directory containing metrics files")
    parser.add_argument("--refresh-interval", type=float, default=1.0, help="Refresh interval in seconds")
    parser.add_argument("--max-trades", type=int, default=10, help="Maximum number of trades to display")

    args = parser.parse_args()

    # Create display
    display = TradeMetricsDisplay(
        args.metrics_dir,
        args.refresh_interval,
        args.max_trades
    )

    # Run display
    display.run()

if __name__ == "__main__":
    main()
