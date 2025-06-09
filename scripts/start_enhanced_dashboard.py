#!/usr/bin/env python3
"""
Enhanced Dashboard Startup Script
=================================

Starts the enhanced API server with live trading integration and React dashboard.
Designed for Winsor Williams II hedge fund operations.
"""

import asyncio
import subprocess
import sys
import time
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedDashboardManager:
    """Manager for enhanced dashboard with live trading integration."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.api_process = None
        self.react_process = None
        
        # Configuration
        self.api_host = "0.0.0.0"
        self.api_port = 8081
        self.react_port = 3000
        
        logger.info("🚀 WILLIAMS CAPITAL MANAGEMENT - ENHANCED DASHBOARD")
        logger.info("👤 Owner: Winsor Williams II")
        logger.info("💼 Live Trading Integration Active")
        
    def validate_environment(self):
        """Validate environment configuration."""
        logger.info("🔍 Validating environment configuration...")
        
        required_vars = [
            'WALLET_ADDRESS',
            'WALLET_PRIVATE_KEY', 
            'HELIUS_API_KEY',
            'QUICKNODE_RPC_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            logger.error(f"❌ Missing environment variables: {missing_vars}")
            return False
            
        logger.info("✅ Environment configuration validated")
        return True
        
    def start_api_server(self):
        """Start the enhanced API server."""
        logger.info("🔧 Starting enhanced API server...")
        
        try:
            api_script = self.project_root / 'phase_4_deployment' / 'dashboard' / 'api_server.py'
            
            self.api_process = subprocess.Popen([
                sys.executable, str(api_script),
                '--host', self.api_host,
                '--port', str(self.api_port)
            ], cwd=str(self.project_root))
            
            logger.info(f"✅ API server started on {self.api_host}:{self.api_port}")
            logger.info(f"📊 Live metrics updating every 30 seconds")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start API server: {e}")
            return False
            
    def start_react_dashboard(self):
        """Start the React dashboard."""
        logger.info("🎨 Starting React dashboard...")
        
        try:
            react_dir = self.project_root / 'react-dashboard'
            
            # Check if node_modules exists
            if not (react_dir / 'node_modules').exists():
                logger.info("📦 Installing React dependencies...")
                subprocess.run(['npm', 'install'], cwd=str(react_dir), check=True)
                
            # Set environment variable for API URL
            env = os.environ.copy()
            env['REACT_APP_API_URL'] = f'http://localhost:{self.api_port}'
            
            self.react_process = subprocess.Popen([
                'npm', 'start'
            ], cwd=str(react_dir), env=env)
            
            logger.info(f"✅ React dashboard started on http://localhost:{self.react_port}")
            logger.info(f"🔗 Connected to API: http://localhost:{self.api_port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start React dashboard: {e}")
            return False
            
    def wait_for_api_ready(self, timeout=30):
        """Wait for API server to be ready."""
        logger.info("⏳ Waiting for API server to be ready...")
        
        import requests
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f'http://localhost:{self.api_port}/health', timeout=5)
                if response.status_code == 200:
                    logger.info("✅ API server is ready")
                    return True
            except:
                pass
                
            time.sleep(2)
            
        logger.error("❌ API server failed to start within timeout")
        return False
        
    def start_dashboard(self):
        """Start the complete enhanced dashboard system."""
        logger.info("🚀 STARTING ENHANCED DASHBOARD SYSTEM")
        logger.info("=" * 60)
        
        # Validate environment
        if not self.validate_environment():
            return False
            
        # Start API server
        if not self.start_api_server():
            return False
            
        # Wait for API to be ready
        if not self.wait_for_api_ready():
            self.cleanup()
            return False
            
        # Start React dashboard
        if not self.start_react_dashboard():
            self.cleanup()
            return False
            
        logger.info("=" * 60)
        logger.info("🎉 ENHANCED DASHBOARD SYSTEM STARTED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"🌐 Dashboard URL: http://localhost:{self.react_port}")
        logger.info(f"📊 API URL: http://localhost:{self.api_port}")
        logger.info(f"👤 Owner: Winsor Williams II")
        logger.info(f"💼 Wallet: {os.getenv('WALLET_ADDRESS', 'N/A')}")
        logger.info(f"🔄 Live Updates: Every 30 seconds")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop the dashboard system")
        
        return True
        
    def cleanup(self):
        """Clean up processes."""
        logger.info("🧹 Cleaning up processes...")
        
        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait()
            logger.info("✅ API server stopped")
            
        if self.react_process:
            self.react_process.terminate()
            self.react_process.wait()
            logger.info("✅ React dashboard stopped")
            
    def run(self):
        """Run the enhanced dashboard system."""
        try:
            if self.start_dashboard():
                # Keep running until interrupted
                while True:
                    time.sleep(1)
                    
                    # Check if processes are still running
                    if self.api_process and self.api_process.poll() is not None:
                        logger.error("❌ API server process died")
                        break
                        
                    if self.react_process and self.react_process.poll() is not None:
                        logger.error("❌ React dashboard process died")
                        break
                        
        except KeyboardInterrupt:
            logger.info("🛑 Dashboard system interrupted by user")
        except Exception as e:
            logger.error(f"❌ Dashboard system error: {e}")
        finally:
            self.cleanup()

def main():
    """Main function."""
    dashboard_manager = EnhancedDashboardManager()
    dashboard_manager.run()

if __name__ == "__main__":
    main()
