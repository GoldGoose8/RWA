#!/usr/bin/env python3
"""
Complete Trading System Launcher
================================

Starts both the live trading system and the Winsor Williams II dashboard
in a coordinated manner for complete hedge fund operations.
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from datetime import datetime

class TradingSystemLauncher:
    """Manages the complete trading system startup."""
    
    def __init__(self):
        self.trading_process = None
        self.dashboard_process = None
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        self.shutdown()
    
    def check_prerequisites(self):
        """Check if all prerequisites are met."""
        print("🔍 Checking prerequisites...")
        
        # Check environment variables
        required_env_vars = [
            "WALLET_ADDRESS",
            "WALLET_PRIVATE_KEY", 
            "QUICKNODE_RPC_URL",
            "HELIUS_RPC_URL",
            "JITO_RPC_URL",
            "JUPITER_QUOTE_ENDPOINT"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        # Check required files
        required_files = [
            ".env",
            "config.yaml",
            "config/live_production.yaml",
            "keys/trading_wallet.json",
            "scripts/unified_live_trading.py",
            "phase_4_deployment/dashboard/streamlit_dashboard.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing files: {', '.join(missing_files)}")
            return False
        
        print("✅ All prerequisites met")
        return True
    
    def start_trading_system(self):
        """Start the live trading system."""
        print("🚀 Starting live trading system...")
        
        try:
            self.trading_process = subprocess.Popen([
                sys.executable, "scripts/unified_live_trading.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if it's still running
            if self.trading_process.poll() is None:
                print("✅ Live trading system started successfully")
                return True
            else:
                stdout, stderr = self.trading_process.communicate()
                print(f"❌ Trading system failed to start:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting trading system: {e}")
            return False
    
    def start_dashboard(self):
        """Start the dashboard."""
        print("📊 Starting Winsor Williams II dashboard...")
        
        try:
            # First run the dashboard setup
            setup_result = subprocess.run([
                sys.executable, "scripts/start_winsor_dashboard.py"
            ], capture_output=True, text=True, timeout=30)
            
            if setup_result.returncode != 0:
                print(f"⚠️ Dashboard setup had issues: {setup_result.stderr}")
            
            # Start Streamlit dashboard
            self.dashboard_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run",
                "phase_4_deployment/dashboard/streamlit_dashboard.py",
                "--server.port", "8501",
                "--server.address", "localhost",
                "--server.headless", "false",
                "--browser.gatherUsageStats", "false"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Give it a moment to start
            time.sleep(5)
            
            # Check if it's still running
            if self.dashboard_process.poll() is None:
                print("✅ Dashboard started successfully")
                print("📍 Dashboard URL: http://localhost:8501")
                return True
            else:
                stdout, stderr = self.dashboard_process.communicate()
                print(f"❌ Dashboard failed to start:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor both processes and restart if needed."""
        print("👁️ Monitoring processes...")
        
        while self.running:
            try:
                # Check trading system
                if self.trading_process and self.trading_process.poll() is not None:
                    print("⚠️ Trading system stopped, restarting...")
                    self.start_trading_system()
                
                # Check dashboard
                if self.dashboard_process and self.dashboard_process.poll() is not None:
                    print("⚠️ Dashboard stopped, restarting...")
                    self.start_dashboard()
                
                # Wait before next check
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n🛑 Shutdown requested by user")
                break
            except Exception as e:
                print(f"⚠️ Error in monitoring: {e}")
                time.sleep(5)
    
    def shutdown(self):
        """Shutdown all processes."""
        print("🛑 Shutting down trading system...")
        
        if self.trading_process:
            try:
                self.trading_process.terminate()
                self.trading_process.wait(timeout=10)
                print("✅ Trading system stopped")
            except subprocess.TimeoutExpired:
                self.trading_process.kill()
                print("🔥 Trading system force killed")
            except Exception as e:
                print(f"⚠️ Error stopping trading system: {e}")
        
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=10)
                print("✅ Dashboard stopped")
            except subprocess.TimeoutExpired:
                self.dashboard_process.kill()
                print("🔥 Dashboard force killed")
            except Exception as e:
                print(f"⚠️ Error stopping dashboard: {e}")
    
    def run(self):
        """Run the complete trading system."""
        print("🏢 WINSOR WILLIAMS II - HEDGE FUND")
        print("🚀 Complete Trading System Launcher")
        print("🛡️ MEV-Protected • Jito Block Engine")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met. Please fix the issues above.")
            return 1
        
        # Start trading system
        if not self.start_trading_system():
            print("❌ Failed to start trading system")
            return 1
        
        # Start dashboard
        if not self.start_dashboard():
            print("❌ Failed to start dashboard")
            self.shutdown()
            return 1
        
        print("\n🎉 COMPLETE TRADING SYSTEM ACTIVE!")
        print("=" * 60)
        print("🟢 Live Trading System: RUNNING")
        print("📊 Dashboard: http://localhost:8501")
        print("👤 Owner: Winsor Williams II")
        print("🏢 Type: Hedge Fund")
        print("🛡️ MEV Protection: Active")
        print("⚡ Execution: QuickNode + Jito")
        print("=" * 60)
        print("💡 Press Ctrl+C to stop all systems")
        print("📊 Monitor performance at: http://localhost:8501")
        
        # Monitor processes
        try:
            self.monitor_processes()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
        
        print("🎯 All systems stopped. Trading session complete.")
        return 0

def main():
    """Main function."""
    launcher = TradingSystemLauncher()
    return launcher.run()

if __name__ == "__main__":
    exit(main())
