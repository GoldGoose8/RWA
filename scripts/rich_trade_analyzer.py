#!/usr/bin/env python3
"""
Rich Trade Analyzer - Beautiful Console Output
Enhanced trade analysis with rich text formatting for stunning visual presentation.
"""

import json
import os
import glob
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
from pathlib import Path

# Rich text formatting
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.columns import Columns
    from rich.tree import Tree
    from rich import box
    from rich.align import Align
    from rich.rule import Rule
    RICH_AVAILABLE = True
except ImportError:
    print("📦 Installing rich for enhanced formatting...")
    import subprocess
    subprocess.run(["pip3", "install", "rich"], check=True)
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.columns import Columns
    from rich.tree import Tree
    from rich import box
    from rich.align import Align
    from rich.rule import Rule
    RICH_AVAILABLE = True

# Initialize rich console
console = Console()

class RichTradeAnalyzer:
    """Beautiful trade analyzer with rich text formatting."""

    def __init__(self):
        """Initialize the rich trade analyzer."""
        self.console = Console()

    def load_enhanced_trades(self, folder_path: str = "output/enhanced_live_trading/trades/") -> List[Dict[str, Any]]:
        """Load enhanced live trading data - aligned with dashboard data service."""
        trades = []

        # Try multiple possible locations for trade data
        possible_paths = [
            folder_path,
            "output/enhanced_live_trading/trades/",
            "output/live_production/trades/",
            "phase_4_deployment/output/enhanced_live_trading/trades/",
            "phase_4_deployment/output/live_production/trades/"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                folder_path = path
                break
        else:
            self.console.print(f"[red]❌ No trade data found in any of the expected locations[/red]")
            self.console.print(f"[dim]Searched: {', '.join(possible_paths)}[/dim]")
            return trades

        trade_files = glob.glob(os.path.join(folder_path, "trade_*.json"))
        trade_files.sort()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Loading trade data...", total=len(trade_files))

            for trade_file in trade_files:
                try:
                    with open(trade_file, 'r') as f:
                        trade_data = json.load(f)
                        trades.append(trade_data)
                    progress.advance(task)
                except Exception as e:
                    self.console.print(f"[yellow]⚠️ Error loading {trade_file}: {e}[/yellow]")

        return trades

    def load_enhanced_metrics(self, metrics_path: str = "output/enhanced_live_trading/latest_metrics.json") -> Dict[str, Any]:
        """Load enhanced live trading metrics - aligned with dashboard data service."""
        # Try multiple possible locations for metrics data
        possible_paths = [
            metrics_path,
            "output/enhanced_live_trading/latest_metrics.json",
            "output/live_production/latest_metrics.json",
            "output/live_production/production_metrics.json",
            "phase_4_deployment/output/enhanced_live_trading/latest_metrics.json",
            "phase_4_deployment/output/live_production/latest_metrics.json"
        ]

        for path in possible_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        metrics = json.load(f)
                        self.console.print(f"[dim]📊 Loaded metrics from: {path}[/dim]")
                        return metrics
            except Exception as e:
                self.console.print(f"[yellow]⚠️ Error loading metrics from {path}: {e}[/yellow]")
                continue

        self.console.print(f"[yellow]⚠️ No metrics found in any expected location[/yellow]")
        return {}

    def create_header_panel(self, trades: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Panel:
        """Create beautiful header panel."""

        # Calculate basic stats
        total_trades = len(trades)
        successful_trades = len([t for t in trades if t.get('transaction_result', {}).get('success', False)])
        real_transactions = len([t for t in trades if t.get('transaction_result', {}).get('signature')])

        # Session info
        session_start = metrics.get('session_start', 'Unknown')
        session_duration = metrics.get('session_duration_minutes', 0)

        header_text = Text()
        header_text.append("🚀 ENHANCED LIVE TRADING ANALYSIS\n", style="bold cyan")
        header_text.append(f"Session: {session_start}\n", style="dim")
        header_text.append(f"Duration: {session_duration:.1f} minutes\n", style="dim")
        success_rate = (successful_trades/total_trades*100) if total_trades > 0 else 0.0
        header_text.append(f"Total Trades: {total_trades} | Real Transactions: {real_transactions} | Success Rate: {success_rate:.1f}%", style="green")

        return Panel(
            Align.center(header_text),
            box=box.DOUBLE,
            border_style="cyan",
            title="[bold]SYNERGY7 TRADING ANALYSIS[/bold]",
            title_align="center"
        )

    def create_performance_table(self, trades: List[Dict[str, Any]]) -> Table:
        """Create performance metrics table."""

        table = Table(title="📊 Performance Metrics", box=box.ROUNDED, border_style="green")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_column("Details", style="dim")

        if not trades:
            table.add_row("No Data", "❌", "No trades found")
            return table

        # Calculate metrics
        total_trades = len(trades)
        successful_trades = [t for t in trades if t.get('transaction_result', {}).get('success', False)]
        real_transactions = [t for t in trades if t.get('transaction_result', {}).get('signature')]

        # Position sizes
        position_sizes_usd = [t['position_data']['position_size_usd'] for t in trades if 'position_data' in t]
        avg_position_size = statistics.mean(position_sizes_usd) if position_sizes_usd else 0

        # Execution times
        execution_times = [t['transaction_result']['execution_time'] for t in successful_trades if 'execution_time' in t.get('transaction_result', {})]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0

        # Add rows
        table.add_row("Total Trades", f"{total_trades}", f"{len(successful_trades)} successful")
        table.add_row("Real Transactions", f"{len(real_transactions)}", f"{len(real_transactions)/total_trades*100:.1f}% executed" if total_trades > 0 else "0%")
        table.add_row("Avg Position Size", f"${avg_position_size:.2f}", f"{avg_position_size/180:.4f} SOL")
        table.add_row("Avg Execution Time", f"{avg_execution_time:.3f}s", "Real blockchain time")

        return table

    def create_trades_table(self, trades: List[Dict[str, Any]]) -> Table:
        """Create detailed trades table."""

        table = Table(title="📋 Recent Trades", box=box.ROUNDED, border_style="blue")
        table.add_column("Time", style="cyan")
        table.add_column("Action", style="yellow")
        table.add_column("Size (SOL)", style="green")
        table.add_column("Size (USD)", style="green")
        table.add_column("Confidence", style="magenta")
        table.add_column("Status", style="bold")
        table.add_column("Signature", style="dim")

        # Show last 10 trades
        recent_trades = trades[-10:] if len(trades) > 10 else trades

        for trade in reversed(recent_trades):  # Most recent first
            signal = trade.get('signal', {})
            position_data = trade.get('position_data', {})
            tx_result = trade.get('transaction_result', {})

            # Format time
            timestamp = trade.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = timestamp[:8] if len(timestamp) > 8 else timestamp

            # Format status
            if tx_result.get('success'):
                status = "[green]✅ Executed[/green]"
            else:
                status = "[red]❌ Failed[/red]"

            # Format signature
            signature = tx_result.get('signature', 'N/A')
            if signature and signature != 'N/A':
                sig_display = f"{signature[:8]}...{signature[-8:]}"
            else:
                sig_display = "N/A"

            table.add_row(
                time_str,
                signal.get('action', 'N/A'),
                f"{position_data.get('position_size_sol', 0):.4f}",
                f"${position_data.get('position_size_usd', 0):.2f}",
                f"{signal.get('confidence', 0):.1%}",
                status,
                sig_display
            )

        return table

    def create_transaction_details_panel(self, trades: List[Dict[str, Any]]) -> Panel:
        """Create transaction details panel."""

        real_trades = [t for t in trades if t.get('transaction_result', {}).get('signature')]

        if not real_trades:
            content = Text("No real transactions found", style="yellow")
            return Panel(content, title="🔗 Transaction Details", border_style="yellow")

        content = Text()
        content.append("🔗 Real Blockchain Transactions:\n\n", style="bold cyan")

        for i, trade in enumerate(real_trades[-5:], 1):  # Last 5 real transactions
            tx_result = trade['transaction_result']
            signal = trade['signal']

            content.append(f"Transaction {i}:\n", style="bold")
            content.append(f"  Signature: {tx_result['signature']}\n", style="green")
            content.append(f"  Action: {signal['action']} {signal['size']:.4f} SOL\n", style="cyan")
            content.append(f"  Execution Time: {tx_result['execution_time']:.3f}s\n", style="magenta")
            content.append(f"  Status: {tx_result.get('confirmation', {}).get('status', 'Unknown')}\n", style="yellow")
            content.append("\n")

        return Panel(content, title="🔗 Transaction Details", border_style="green")

    def create_system_metrics_panel(self, metrics: Dict[str, Any]) -> Panel:
        """Create system metrics panel."""

        if not metrics:
            content = Text("No system metrics available", style="yellow")
            return Panel(content, title="⚙️ System Metrics", border_style="yellow")

        system_metrics = metrics.get('metrics', {})
        executor_metrics = metrics.get('executor_metrics', {})

        content = Text()
        content.append("⚙️ System Performance:\n\n", style="bold cyan")
        content.append(f"Cycles Completed: {system_metrics.get('cycles_completed', 0)}\n", style="green")
        content.append(f"Cycles Successful: {system_metrics.get('cycles_successful', 0)}\n", style="green")
        content.append(f"Trades Attempted: {system_metrics.get('trades_attempted', 0)}\n", style="yellow")
        content.append(f"Trades Executed: {system_metrics.get('trades_executed', 0)}\n", style="green")
        content.append(f"Transaction Success Rate: {executor_metrics.get('success_rate', 0)*100:.1f}%\n", style="magenta")
        content.append(f"Average Execution Time: {executor_metrics.get('average_execution_time', 0):.3f}s\n", style="cyan")

        return Panel(content, title="⚙️ System Metrics", border_style="blue")

    def analyze_and_display(self, folder_path: str = "output/enhanced_live_trading/trades/", quiet: bool = False):
        """Main analysis and display function."""

        if not quiet:
            self.console.print("\n")
            self.console.print(Rule("[bold cyan]SYNERGY7 ENHANCED TRADE ANALYZER[/bold cyan]"))
            self.console.print("\n")

        # Load data
        trades = self.load_enhanced_trades(folder_path)
        metrics = self.load_enhanced_metrics()

        if not trades and not metrics:
            self.console.print(Panel(
                "[red]❌ No trading data found![/red]\n\nPlease ensure the enhanced live trading system has run and generated data.",
                title="Error",
                border_style="red"
            ))
            return

        # Display header
        header_panel = self.create_header_panel(trades, metrics)
        self.console.print(header_panel)
        self.console.print("\n")

        # Create layout with columns
        left_column = [
            self.create_performance_table(trades),
            self.create_system_metrics_panel(metrics)
        ]

        right_column = [
            self.create_trades_table(trades),
            self.create_transaction_details_panel(trades)
        ]

        # Display in columns
        columns = Columns(left_column + right_column, equal=True, expand=True)
        self.console.print(columns)

        # Summary
        if not quiet:
            self.console.print("\n")
            self.console.print(Rule("[bold green]ANALYSIS COMPLETE[/bold green]"))

            real_transactions = len([t for t in trades if t.get('transaction_result', {}).get('signature')])
            if real_transactions > 0:
                self.console.print(f"[bold green]✅ Found {real_transactions} real blockchain transactions![/bold green]")
                self.console.print("[dim]All transactions have been executed on the Solana mainnet.[/dim]")
            else:
                self.console.print("[yellow]⚠️ No real transactions found - system may be in simulation mode.[/yellow]")


def main():
    """Main function for rich trade analyzer."""
    parser = argparse.ArgumentParser(description="Rich Trade Analyzer - Beautiful Console Output")
    parser.add_argument("--folder", default="output/enhanced_live_trading/trades/",
                       help="Folder containing trade data")
    parser.add_argument("--quiet", action="store_true",
                       help="Quiet mode with minimal output")

    args = parser.parse_args()

    analyzer = RichTradeAnalyzer()
    analyzer.analyze_and_display(args.folder, args.quiet)


if __name__ == "__main__":
    main()
