#!/usr/bin/env python3
"""
Production Dashboard Launcher for Synergy7 Trading System

This script starts the complete production dashboard system including:
- Enhanced API server with live trading integration
- React dashboard frontend
- Real-time metrics and monitoring
- WebSocket connections for live updates

Designed for Winsor Williams II hedge fund operations.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard_production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductionDashboardLauncher:
    """Production dashboard launcher and manager."""

    def __init__(self):
        """Initialize the dashboard launcher."""
        self.api_process = None
        self.react_process = None
        self.running = False
        self.project_root = project_root
        
        # Configuration
        self.api_port = 8081
        self.react_port = 3000
        
        logger.info("🏢 Williams Capital Management - Production Dashboard")
        logger.info("👤 Owner: Winsor Williams II")
        logger.info("🚀 Initializing production dashboard launcher...")

    def check_environment(self):
        """Check if the environment is properly configured."""
        logger.info("🔧 Checking environment configuration...")
        
        # Check required environment variables
        required_vars = ['WALLET_ADDRESS', 'HELIUS_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            return False
        
        # Check if React dashboard exists
        react_dir = self.project_root / 'react-dashboard'
        if not react_dir.exists():
            logger.error(f"❌ React dashboard directory not found: {react_dir}")
            return False
        
        # Check if package.json exists
        package_json = react_dir / 'package.json'
        if not package_json.exists():
            logger.error(f"❌ React package.json not found: {package_json}")
            return False
        
        logger.info("✅ Environment configuration validated")
        return True

    def check_dependencies(self):
        """Check if required dependencies are installed."""
        logger.info("📦 Checking dependencies...")
        
        try:
            # Check Python dependencies
            import fastapi
            import uvicorn
            import httpx
            logger.info("✅ Python dependencies available")
            
            # Check if npm is available
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ npm available: {result.stdout.strip()}")
            else:
                logger.error("❌ npm not available")
                return False
            
            # Check React dependencies
            react_dir = self.project_root / 'react-dashboard'
            node_modules = react_dir / 'node_modules'
            if not node_modules.exists():
                logger.warning("⚠️ React dependencies not installed, installing...")
                self.install_react_dependencies()
            else:
                logger.info("✅ React dependencies available")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Missing Python dependency: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Dependency check failed: {e}")
            return False

    def install_react_dependencies(self):
        """Install React dashboard dependencies."""
        logger.info("📦 Installing React dependencies...")
        
        react_dir = self.project_root / 'react-dashboard'
        
        try:
            result = subprocess.run(
                ['npm', 'install'],
                cwd=react_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ React dependencies installed successfully")
            else:
                logger.error(f"❌ Failed to install React dependencies: {result.stderr}")
                raise Exception("React dependency installation failed")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ React dependency installation timed out")
            raise Exception("React dependency installation timeout")
        except Exception as e:
            logger.error(f"❌ Error installing React dependencies: {e}")
            raise

    def start_api_server(self):
        """Start the enhanced API server."""
        logger.info("📡 Starting enhanced API server...")
        
        try:
            # Import and start the API server
            from phase_4_deployment.dashboard.api_server import start_api_server
            
            # Start API server in a separate thread
            api_thread = threading.Thread(
                target=start_api_server,
                args=("0.0.0.0", self.api_port),
                daemon=True
            )
            api_thread.start()
            
            # Give the server time to start
            time.sleep(3)
            
            logger.info(f"✅ API server started on port {self.api_port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start API server: {e}")
            return False

    def start_react_dashboard(self):
        """Start the React dashboard."""
        logger.info("🖥️ Starting React dashboard...")
        
        react_dir = self.project_root / 'react-dashboard'
        
        try:
            # Set environment variables for React
            env = os.environ.copy()
            env['REACT_APP_API_URL'] = f'http://localhost:{self.api_port}'
            env['PORT'] = str(self.react_port)
            env['BROWSER'] = 'none'  # Don't auto-open browser
            
            # Start React development server
            self.react_process = subprocess.Popen(
                ['npm', 'start'],
                cwd=react_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for React to start
            logger.info("⏳ Waiting for React dashboard to start...")
            time.sleep(10)
            
            if self.react_process.poll() is None:
                logger.info(f"✅ React dashboard started on port {self.react_port}")
                return True
            else:
                logger.error("❌ React dashboard failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start React dashboard: {e}")
            return False

    def check_live_trading_status(self):
        """Check if live trading system is running."""
        try:
            # Check for live trading process
            result = subprocess.run(
                ['pgrep', '-f', 'unified_live_trading.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Live trading system is running")
                return True
            else:
                logger.warning("⚠️ Live trading system not detected")
                logger.info("💡 Start it with: python3 scripts/unified_live_trading.py")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Could not check live trading status: {e}")
            return False

    def start_production_dashboard(self):
        """Start the complete production dashboard system."""
        logger.info("🚀 Starting production dashboard system...")
        
        try:
            # Check environment
            if not self.check_environment():
                return False
            
            # Check dependencies
            if not self.check_dependencies():
                return False
            
            # Check live trading status
            self.check_live_trading_status()
            
            # Start API server
            if not self.start_api_server():
                return False
            
            # Start React dashboard
            if not self.start_react_dashboard():
                return False
            
            self.running = True
            
            # Print success message
            self.print_success_message()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start production dashboard: {e}")
            return False

    def print_success_message(self):
        """Print success message with access information."""
        print("\n" + "="*80)
        print("🎉 PRODUCTION DASHBOARD STARTED SUCCESSFULLY")
        print("="*80)
        print(f"🏢 Williams Capital Management")
        print(f"👤 Owner: Winsor Williams II")
        print(f"📊 Dashboard URL: http://localhost:{self.react_port}")
        print(f"📡 API Server: http://localhost:{self.api_port}")
        print(f"🔄 Real-time updates every 30 seconds")
        print(f"🛡️ MEV Protection: Jito Block Engine + QuickNode Bundles")
        print(f"💰 Wallet: {os.getenv('WALLET_ADDRESS', 'N/A')}")
        print("="*80)
        print("📋 Available Endpoints:")
        print(f"   • Dashboard: http://localhost:{self.react_port}")
        print(f"   • API Health: http://localhost:{self.api_port}/health")
        print(f"   • Live Metrics: http://localhost:{self.api_port}/metrics")
        print(f"   • Trading Status: http://localhost:{self.api_port}/live-status")
        print("="*80)
        print("🔧 Controls:")
        print("   • Press Ctrl+C to stop the dashboard")
        print("   • Check logs in logs/dashboard_production.log")
        print("="*80)

    def stop_dashboard(self):
        """Stop the dashboard system."""
        logger.info("🛑 Stopping production dashboard...")
        
        self.running = False
        
        # Stop React process
        if self.react_process:
            try:
                self.react_process.terminate()
                self.react_process.wait(timeout=10)
                logger.info("✅ React dashboard stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping React dashboard: {e}")
                try:
                    self.react_process.kill()
                except:
                    pass
        
        logger.info("✅ Production dashboard stopped")

    def run(self):
        """Run the production dashboard system."""
        try:
            # Start the dashboard
            if not self.start_production_dashboard():
                logger.error("❌ Failed to start production dashboard")
                return 1
            
            # Set up signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Keep running
            while self.running:
                time.sleep(1)
            
            return 0
            
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
            return 0
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return 1
        finally:
            self.stop_dashboard()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"🛑 Received signal {signum}")
        self.running = False


def main():
    """Main function."""
    # Ensure logs directory exists
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Create and run the launcher
    launcher = ProductionDashboardLauncher()
    return launcher.run()


if __name__ == "__main__":
    sys.exit(main())
