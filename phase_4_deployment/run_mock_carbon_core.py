#!/usr/bin/env python3
"""
Run mock Carbon Core

This script runs the mock Carbon Core for testing.
"""

import os
import sys
import asyncio
import logging
import argparse
import subprocess
from typing import Dict, Any, List, Optional, Union, Callable

# Install required packages
try:
    import zmq
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyzmq"])
    import zmq

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import mock Carbon Core
from phase_4_deployment.python_comm_layer.mock_carbon_core import MockCarbonCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run mock Carbon Core")
    parser.add_argument("--pub-endpoint", default="tcp://127.0.0.1:5555", help="Publisher endpoint")
    parser.add_argument("--sub-endpoint", default="tcp://127.0.0.1:5556", help="Subscriber endpoint")
    parser.add_argument("--req-endpoint", default="tcp://127.0.0.1:5557", help="Request-reply endpoint")
    parser.add_argument("--config", default="../carbon_core_config.yaml", help="Path to configuration file")

    args = parser.parse_args()

    # Create mock Carbon Core
    carbon_core = MockCarbonCore(
        pub_endpoint=args.pub_endpoint,
        sub_endpoint=args.sub_endpoint,
        req_endpoint=args.req_endpoint,
        config_path=args.config,
    )

    try:
        # Start mock Carbon Core
        await carbon_core.start()
        logger.info("Mock Carbon Core started")

        # Run until interrupted
        logger.info("Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Stop mock Carbon Core
        await carbon_core.stop()
        logger.info("Mock Carbon Core stopped")

if __name__ == "__main__":
    asyncio.run(main())
