#!/usr/bin/env python3
"""
Real-time Dashboard Metrics Updater
Continuously monitors live trading session and updates dashboard metrics in real-time.
"""

import os
import json
import glob
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import statistics

class RealTimeDashboardUpdater:
    def __init__(self, update_interval=10):
        """Initialize the real-time dashboard updater."""
        self.update_interval = update_interval  # seconds
        self.running = False
        self.last_trade_count = 0
        self.session_start_time = datetime.now()
        
    def get_current_session_metrics(self):
        """Get metrics for the current live trading session."""
        
        # Find all trade files
        trade_files = glob.glob("output/live_production/trades/trade_*.json")
        trade_files.sort()
        
        if not trade_files:
            return self.get_empty_metrics()
        
        # Filter trades from current session (last 2 hours)
        current_session_trades = []
        cutoff_time = datetime.now() - timedelta(hours=2)
        
        for trade_file in trade_files:
            try:
                # Extract timestamp from filename
                filename = os.path.basename(trade_file)
                timestamp_str = filename.replace('trade_', '').replace('.json', '')
                trade_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if trade_time >= cutoff_time:
                    with open(trade_file, 'r') as f:
                        trade = json.load(f)
                    current_session_trades.append(trade)
                    
            except Exception as e:
                continue
        
        return self.calculate_session_metrics(current_session_trades)
    
    def calculate_session_metrics(self, trades):
        """Calculate comprehensive metrics for the current session."""
        
        if not trades:
            return self.get_empty_metrics()
        
        successful_trades = 0
        failed_trades = 0
        trade_sizes = []
        execution_times = []
        signatures = []
        strategies = {}
        regimes = {}
        
        # Analyze trades
        for trade in trades:
            result = trade.get('result', {})
            signal = trade.get('signal', {})
            position_info = signal.get('position_info', {})
            
            # Count success/failure
            if result.get('success', False):
                successful_trades += 1
                signature = result.get('signature')
                if signature:
                    signatures.append(signature)
            else:
                failed_trades += 1
            
            # Trade size
            trade_size_usd = position_info.get('position_size_usd', 0)
            if trade_size_usd > 0:
                trade_sizes.append(trade_size_usd)
            
            # Execution time
            exec_time = trade.get('execution_time', 0)
            if exec_time > 0:
                execution_times.append(exec_time)
            
            # Strategy tracking
            strategy = signal.get('source', 'unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
            
            # Regime tracking
            regime_info = signal.get('regime_info', {})
            regime = regime_info.get('regime', 'unknown')
            regimes[regime] = regimes.get(regime, 0) + 1
        
        # Calculate metrics
        total_trades = len(trades)
        win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
        avg_trade_size = statistics.mean(trade_sizes) if trade_sizes else 0
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        total_volume = sum(trade_sizes)
        
        # Session timing
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        trades_per_hour = (total_trades / (session_duration / 60)) if session_duration > 0 else 0
        
        # Current market regime (from latest trade)
        current_regime = "DETECTING..."
        if trades:
            latest_trade = trades[-1]
            regime_info = latest_trade.get('signal', {}).get('regime_info', {})
            current_regime = regime_info.get('regime', 'DETECTING...').upper()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "session_start": self.session_start_time.isoformat(),
            "session_duration_minutes": round(session_duration, 1),
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "failed_trades": failed_trades,
            "win_rate": round(win_rate, 1),
            "average_trade_size": round(avg_trade_size, 2),
            "total_volume_usd": round(total_volume, 2),
            "average_execution_time": round(avg_execution_time, 3),
            "trades_per_hour": round(trades_per_hour, 1),
            "current_regime": current_regime,
            "strategies": strategies,
            "regimes": regimes,
            "blockchain_verified_trades": len(signatures),
            "status": "active",
            "trading_enabled": True,
            "last_update": datetime.now().isoformat()
        }
    
    def get_empty_metrics(self):
        """Return empty metrics for when no trades exist."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        
        return {
            "timestamp": datetime.now().isoformat(),
            "session_start": self.session_start_time.isoformat(),
            "session_duration_minutes": round(session_duration, 1),
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "win_rate": 0.0,
            "average_trade_size": 0.0,
            "total_volume_usd": 0.0,
            "average_execution_time": 0.0,
            "trades_per_hour": 0.0,
            "current_regime": "DETECTING...",
            "strategies": {},
            "regimes": {},
            "blockchain_verified_trades": 0,
            "status": "active",
            "trading_enabled": True,
            "last_update": datetime.now().isoformat()
        }
    
    def update_dashboard_files(self, metrics):
        """Update dashboard metrics files."""
        
        # Ensure directories exist
        os.makedirs("output/live_production/dashboard", exist_ok=True)
        os.makedirs("phase_4_deployment/output/dashboard", exist_ok=True)
        
        # Update performance metrics
        performance_file = "output/live_production/dashboard/performance_metrics.json"
        with open(performance_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Update phase_4_deployment metrics
        phase4_file = "phase_4_deployment/output/dashboard/performance_metrics.json"
        with open(phase4_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Create latest cycle data
        cycle_data = {
            "timestamp": datetime.now().isoformat(),
            "cycle_number": metrics["total_trades"],
            "session_duration": metrics["session_duration_minutes"],
            "current_regime": metrics["current_regime"],
            "trades_this_session": metrics["total_trades"],
            "success_rate": metrics["win_rate"],
            "total_volume": metrics["total_volume_usd"],
            "trades_per_hour": metrics["trades_per_hour"],
            "status": "🔴 LIVE SESSION"
        }
        
        cycle_file = "output/live_production/dashboard/latest_cycle.json"
        with open(cycle_file, 'w') as f:
            json.dump(cycle_data, f, indent=2)
    
    def update_loop(self):
        """Main update loop that runs continuously."""
        
        print(f"🔄 Starting real-time dashboard updater (interval: {self.update_interval}s)")
        
        while self.running:
            try:
                # Get current session metrics
                metrics = self.get_current_session_metrics()
                
                # Update dashboard files
                self.update_dashboard_files(metrics)
                
                # Print status if trades changed
                current_trade_count = metrics["total_trades"]
                if current_trade_count != self.last_trade_count:
                    print(f"📊 Dashboard updated: {current_trade_count} trades, "
                          f"{metrics['win_rate']:.1f}% success rate, "
                          f"${metrics['total_volume_usd']:.2f} volume")
                    self.last_trade_count = current_trade_count
                
                # Wait for next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"⚠️ Error updating dashboard: {e}")
                time.sleep(self.update_interval)
    
    def start(self):
        """Start the real-time updater."""
        if self.running:
            print("⚠️ Updater is already running")
            return
        
        self.running = True
        self.session_start_time = datetime.now()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
        print("✅ Real-time dashboard updater started")
    
    def stop(self):
        """Stop the real-time updater."""
        self.running = False
        print("🛑 Real-time dashboard updater stopped")

def main():
    """Main function to run the real-time dashboard updater."""
    
    print("🚀 REAL-TIME DASHBOARD METRICS UPDATER")
    print("=" * 50)
    print("This will continuously update dashboard metrics with live trading data")
    print("Press Ctrl+C to stop")
    print()
    
    # Create and start updater
    updater = RealTimeDashboardUpdater(update_interval=10)  # Update every 10 seconds
    
    try:
        updater.start()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard updater...")
        updater.stop()
        print("✅ Dashboard updater stopped")

if __name__ == "__main__":
    main()
