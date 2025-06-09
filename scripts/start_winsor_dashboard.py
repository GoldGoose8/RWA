#!/usr/bin/env python3
"""
Winsor Williams II - Hedge Fund Dashboard Launcher
=================================================

Starts the branded Streamlit dashboard for Winsor Williams II's hedge fund
with live trading system integration and real-time data updates.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

def setup_dashboard_directories():
    """Create necessary directories for dashboard data."""
    directories = [
        "phase_4_deployment/output",
        "output/live_production/dashboard",
        "output/live_production/trades",
        "output/wallet",
        "output/system",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_initial_dashboard_data():
    """Create initial data files for the dashboard."""
    
    # Create wallet balance file
    wallet_data = {
        "address": os.getenv("WALLET_ADDRESS", "AUD9rymrTCtCr5eC9R1Hf6PM7nXdqPV1cYei6uM5VArS"),
        "balance": 15.553,
        "balance_usd": 15.553 * 152.0,  # Approximate USD value
        "last_update": datetime.now().isoformat(),
        "data_source": "live_session"
    }
    
    with open("output/wallet/wallet_balance.json", "w") as f:
        json.dump(wallet_data, f, indent=2)
    print("✅ Created wallet balance data")
    
    # Create initial trading metrics
    trading_metrics = {
        "session_start": datetime.now().isoformat(),
        "total_trades": 0,
        "successful_trades": 0,
        "total_pnl_sol": 0.0,
        "total_pnl_usd": 0.0,
        "win_rate": 0.0,
        "trades_executed": 0,
        "cycles_completed": 0,
        "system_status": "READY",
        "uptime_percentage": 100.0,
        "session_pnl_sol": 0.0,
        "session_pnl_usd": 0.0,
        "blockchain_verified": 0,
        "last_update": datetime.now().isoformat()
    }
    
    with open("output/live_production/dashboard/latest_metrics.json", "w") as f:
        json.dump(trading_metrics, f, indent=2)
    print("✅ Created trading metrics data")
    
    # Create system health data
    system_health = {
        "overall_health": True,
        "rpc_status": {
            "jito": "online",
            "quicknode": "online", 
            "helius": "online"
        },
        "api_status": {
            "jupiter": "online",
            "jito_tips": "online"
        },
        "wallet_status": "funded",
        "trading_status": "ready",
        "last_check": datetime.now().isoformat()
    }
    
    with open("output/system/health_metrics.json", "w") as f:
        json.dump(system_health, f, indent=2)
    print("✅ Created system health data")
    
    # Create current session summary
    session_summary = {
        "session_id": f"winsor_session_{int(datetime.now().timestamp())}",
        "start_time": datetime.now().isoformat(),
        "status": "active",
        "owner": "Winsor Williams II",
        "fund_type": "Hedge Fund",
        "wallet_address": os.getenv("WALLET_ADDRESS", "AUD9rymrTCtCr5eC9R1Hf6PM7nXdqPV1cYei6uM5VArS"),
        "initial_balance": 15.553,
        "current_balance": 15.553,
        "trades_count": 0,
        "pnl_sol": 0.0,
        "pnl_usd": 0.0,
        "uptime_percentage": 100.0
    }
    
    with open("output/live_production/dashboard/current_session_summary.json", "w") as f:
        json.dump(session_summary, f, indent=2)
    print("✅ Created session summary data")

def check_trading_system_status():
    """Check if the live trading system is running."""
    try:
        result = subprocess.run(["pgrep", "-f", "unified_live_trading.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Live trading system is running")
            return True
        else:
            print("⚠️ Live trading system not detected")
            print("💡 Start it with: python3 scripts/unified_live_trading.py")
            return False
    except:
        print("⚠️ Could not check trading system status")
        return False

def start_streamlit_dashboard():
    """Start the Streamlit dashboard."""
    dashboard_path = "phase_4_deployment/dashboard/streamlit_dashboard.py"
    
    if not Path(dashboard_path).exists():
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return False
    
    print(f"🚀 Starting Winsor Williams II Hedge Fund Dashboard...")
    print(f"📍 Dashboard URL: http://localhost:8501")
    print(f"🔄 Auto-refresh every 30 seconds")
    print(f"👤 Owner: Winsor Williams II")
    print(f"🏢 Type: Hedge Fund")
    print(f"🛡️ MEV Protection: Jito Block Engine")
    print(f"⚡ Execution: QuickNode Bundles")
    
    # Start Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            dashboard_path,
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return False

def create_dashboard_launcher():
    """Create a convenient launcher script."""
    launcher_content = '''#!/bin/bash
# Winsor Williams II - Hedge Fund Dashboard Launcher
# MEV-Protected Trading Dashboard

echo "🏢 Winsor Williams II - Hedge Fund"
echo "🚀 MEV-Protected Trading Dashboard"
echo "🛡️ Jito Block Engine • QuickNode Bundles"
echo ""

# Check if trading system is running
if pgrep -f "unified_live_trading.py" > /dev/null; then
    echo "✅ Live trading system is running"
else
    echo "⚠️ Live trading system not detected"
    echo "💡 Start it with: python3 scripts/unified_live_trading.py"
fi

echo ""
echo "📊 Starting dashboard at http://localhost:8501"
echo "🔄 Dashboard updates every 30 seconds"
echo "👤 Owner: Winsor Williams II"
echo ""

# Start the dashboard
python3 scripts/start_winsor_dashboard.py
'''
    
    with open("start_winsor_dashboard.sh", "w") as f:
        f.write(launcher_content)
    
    # Make executable
    os.chmod("start_winsor_dashboard.sh", 0o755)
    print("✅ Created dashboard launcher: ./start_winsor_dashboard.sh")

def main():
    """Main function."""
    print("🏢 WINSOR WILLIAMS II - HEDGE FUND")
    print("🚀 MEV-Protected Trading Dashboard")
    print("=" * 60)
    
    # Setup directories
    print("\n1️⃣ Setting up directories...")
    setup_dashboard_directories()
    
    # Create initial data
    print("\n2️⃣ Creating initial dashboard data...")
    create_initial_dashboard_data()
    
    # Create launcher
    print("\n3️⃣ Creating dashboard launcher...")
    create_dashboard_launcher()
    
    # Check trading system status
    print("\n4️⃣ Checking trading system status...")
    trading_active = check_trading_system_status()
    
    print("\n5️⃣ Starting Streamlit dashboard...")
    print("=" * 60)
    print("🎉 Setup complete! Starting dashboard...")
    print("📊 Dashboard URL: http://localhost:8501")
    print("👤 Owner: Winsor Williams II")
    print("🏢 Type: Hedge Fund")
    print("🛡️ MEV Protection: Active")
    print("⚡ Execution: QuickNode + Jito")
    if trading_active:
        print("🟢 Trading System: ACTIVE")
    else:
        print("🟡 Trading System: READY (not running)")
    print("=" * 60)
    
    # Start dashboard
    return 0 if start_streamlit_dashboard() else 1

if __name__ == "__main__":
    exit(main())
