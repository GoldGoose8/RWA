#!/usr/bin/env python3
"""
Reset Trading Metrics

This script resets all trading metrics to start fresh from now,
ensuring only pure live trading data is tracked going forward.
"""

import os
import json
import glob
import shutil
from datetime import datetime
from pathlib import Path

def backup_old_trades():
    """Backup existing trade files to avoid data loss."""
    
    # Create backup directory with timestamp
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backups/trades_backup_{backup_timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup existing trade files
    trade_files = glob.glob("output/live_production/trades/trade_*.json")
    if trade_files:
        print(f"📦 Backing up {len(trade_files)} existing trade files...")
        for trade_file in trade_files:
            trade_path = Path(trade_file)
            backup_path = backup_dir / trade_path.name
            shutil.copy2(trade_file, backup_path)
        print(f"✅ Trade files backed up to: {backup_dir}")
    else:
        print("📝 No existing trade files found to backup")
    
    return backup_dir

def clear_trade_data():
    """Clear existing trade data and metrics."""
    
    # Clear trade files
    trade_files = glob.glob("output/live_production/trades/trade_*.json")
    for trade_file in trade_files:
        os.remove(trade_file)
    print(f"🗑️ Removed {len(trade_files)} trade files")
    
    # Clear dashboard data
    dashboard_dir = Path("output/live_production/dashboard")
    if dashboard_dir.exists():
        for file in dashboard_dir.glob("*.json"):
            os.remove(file)
        print("🗑️ Cleared dashboard data files")

def create_fresh_session():
    """Create a fresh trading session starting now."""
    
    current_time = datetime.now()
    
    # Get current wallet balance (you'll need to update this with actual balance)
    print("💰 Getting current wallet balance...")
    
    # Create fresh session data
    fresh_session = {
        'session_start': current_time.isoformat(),
        'session_duration_minutes': 0.0,
        'trades_executed': 0,
        'successful_trades': 0,
        'win_rate': 0.0,
        'total_volume_sol': 0.0,
        'current_balance_sol': 0.002068,  # Current balance from logs
        'session_start_balance': 0.002068,  # Starting fresh from current balance
        'current_market_regime': 'detecting',
        'regime_confidence': 0.0,
        'recent_signatures': [],
        'system_status': 'ACTIVE',
        'uptime_percentage': 100.0,
        'orca_enabled': True,
        'cycles_completed': 0,
        'session_pnl_sol': 0.0,  # Starting at zero
        'session_pnl_usd': 0.0,  # Starting at zero
        'blockchain_verified': 0,
        'sol_price': 160.79,
        'timestamp': current_time.isoformat(),
        'reset_timestamp': current_time.isoformat(),
        'reset_reason': 'Fresh start - removing mixed simulation data'
    }
    
    # Save fresh session data
    dashboard_dir = Path("output/live_production/dashboard")
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    
    session_file = dashboard_dir / "current_session_summary.json"
    with open(session_file, 'w') as f:
        json.dump(fresh_session, f, indent=2)
    
    # Create fresh performance metrics
    performance_metrics = {
        'total_trades': 0,
        'successful_trades': 0,
        'total_pnl_sol': 0.0,
        'total_pnl_usd': 0.0,
        'session_pnl_sol': 0.0,
        'session_pnl_usd': 0.0,
        'win_rate': 0.0,
        'blockchain_verified': 0,
        'last_update': current_time.isoformat(),
        'reset_timestamp': current_time.isoformat()
    }
    
    performance_file = dashboard_dir / "performance_metrics.json"
    with open(performance_file, 'w') as f:
        json.dump(performance_metrics, f, indent=2)
    
    print("✅ Created fresh session data")
    return fresh_session

def main():
    """Main function to reset trading metrics."""
    
    print("🔄 RESETTING TRADING METRICS")
    print("=" * 50)
    print("⚠️  This will clear all existing trade data")
    print("⚠️  Starting fresh session from current balance")
    print("=" * 50)
    
    try:
        # Step 1: Backup existing data
        backup_dir = backup_old_trades()
        
        # Step 2: Clear existing data
        clear_trade_data()
        
        # Step 3: Create fresh session
        fresh_session = create_fresh_session()
        
        print("\n🎉 RESET COMPLETE!")
        print("=" * 50)
        print(f"✅ Fresh session started at: {fresh_session['session_start']}")
        print(f"💰 Starting balance: {fresh_session['session_start_balance']:.6f} SOL")
        print(f"📊 Session PnL: {fresh_session['session_pnl_sol']:.6f} SOL (${fresh_session['session_pnl_usd']:.2f})")
        print(f"📈 Trades executed: {fresh_session['trades_executed']}")
        print(f"📦 Old data backed up to: {backup_dir}")
        print("\n🚀 Ready for fresh live trading session!")
        
        return fresh_session
        
    except Exception as e:
        print(f"❌ Error resetting metrics: {e}")
        return None

if __name__ == "__main__":
    main()
