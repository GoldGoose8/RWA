#!/usr/bin/env python3
"""
Launch Live Trading Dashboard

This script launches the Streamlit dashboard aligned with the live trading system.
All simulation and placeholder code has been removed.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    """Launch the live trading dashboard."""
    
    print("🚀 LAUNCHING RWA TRADING SYSTEM LIVE DASHBOARD")
    print("=" * 60)
    print("⚠️  This dashboard shows REAL TRADING DATA")
    print("⚠️  All simulation and placeholder code removed")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("phase_4_deployment").exists():
        print("❌ Error: Must run from project root directory")
        print("   Current directory:", os.getcwd())
        return 1
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit found")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"])
    
    # Launch the main live dashboard
    dashboard_path = "phase_4_deployment/dashboard/streamlit_dashboard.py"
    
    if not Path(dashboard_path).exists():
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return 1
    
    print(f"🌊 Starting live dashboard: {dashboard_path}")
    print("📊 Dashboard features:")
    print("   • Live trading session monitoring")
    print("   • Real transaction history from blockchain")
    print("   • Orca DEX integration status")
    print("   • Live wallet balance tracking")
    print("   • Real-time strategy performance")
    print("")
    print("🔗 Dashboard will be available at: http://localhost:8501")
    print("🔄 Dashboard updates manually - click refresh for latest data")
    print("")
    
    try:
        # Launch streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            dashboard_path,
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
