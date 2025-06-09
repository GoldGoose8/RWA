#!/usr/bin/env python3
"""
Test script for the live trading script.

This script tests the live trading script with dry run mode.
"""

import os
import sys
import json
import time
import logging
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_live_trading')

# Load environment variables
load_dotenv()

async def test_live_trading_imports():
    """Test importing the live trading script."""
    try:
        # Add the parent directory to the path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(parent_dir)

        # Try to import the live trading script
        import start_live_trading
        from shared.utils.monitoring import get_monitoring_service

        logger.info("Successfully imported live trading script modules")
        return True

    except Exception as e:
        logger.error(f"Error importing live trading script: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_live_trading_dry_run():
    """Test the live trading script with dry run mode."""
    try:
        # Set environment variables for dry run
        os.environ['DRY_RUN'] = 'true'
        os.environ['PAPER_TRADING'] = 'true'

        # Get the path to the live trading script
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "start_live_trading.py"
        )

        # Run the script with a timeout
        logger.info(f"Running live trading script with dry run mode: {script_path}")

        # Create a subprocess
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )

        # Wait for a bit to let the script initialize
        await asyncio.sleep(10)

        # Check if the process is still running
        if process.poll() is None:
            logger.info("Live trading script is running")

            # Terminate the process
            logger.info("Terminating live trading script")
            process.terminate()

            # Wait for the process to terminate
            try:
                process.wait(timeout=5)
                logger.info("Live trading script terminated")
            except subprocess.TimeoutExpired:
                logger.warning("Live trading script did not terminate, killing it")
                process.kill()
                process.wait()

            return True
        else:
            # Process has already terminated
            stdout, stderr = process.communicate()
            logger.error(f"Live trading script terminated with exit code: {process.returncode}")
            logger.error(f"Stdout: {stdout}")
            logger.error(f"Stderr: {stderr}")
            return False

    except Exception as e:
        logger.error(f"Error testing live trading script: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_liljito_integration():
    """Test the Lil' Jito integration in the live trading script."""
    try:
        # Check if the live trading script imports the Lil' Jito client
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "start_live_trading.py"
        )

        with open(script_path, 'r') as f:
            content = f.read()

        if "from rpc_execution.lil_jito_client import LilJitoClient" in content:
            logger.info("Live trading script imports Lil' Jito client")

            # Check if the script initializes the Lil' Jito client
            if "liljito_client = LilJitoClient()" in content:
                logger.info("Live trading script initializes Lil' Jito client")
                return True
            else:
                logger.error("Live trading script does not initialize Lil' Jito client")
                return False
        else:
            logger.error("Live trading script does not import Lil' Jito client")
            return False

    except Exception as e:
        logger.error(f"Error testing Lil' Jito integration: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_stream_data_integration():
    """Test the stream data integration in the live trading script."""
    try:
        # Check if the live trading script imports the stream data ingestor
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "start_live_trading.py"
        )

        with open(script_path, 'r') as f:
            content = f.read()

        if "from stream_data_ingestor.client import StreamDataIngestor, StreamType" in content:
            logger.info("Live trading script imports stream data ingestor")

            # Check if the script initializes the stream data ingestor
            if "liljito_stream = StreamDataIngestor(" in content:
                logger.info("Live trading script initializes stream data ingestor")
                return True
            else:
                logger.error("Live trading script does not initialize stream data ingestor")
                return False
        else:
            logger.error("Live trading script does not import stream data ingestor")
            return False

    except Exception as e:
        logger.error(f"Error testing stream data integration: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main_async():
    """Async main function."""
    # Test importing the live trading script
    import_success = await test_live_trading_imports()
    if not import_success:
        logger.error("Failed to import live trading script")
        return 1

    # Test the Lil' Jito integration
    liljito_success = await test_liljito_integration()
    if not liljito_success:
        logger.error("Failed to test Lil' Jito integration")
        return 1

    # Test the stream data integration
    stream_data_success = await test_stream_data_integration()
    if not stream_data_success:
        logger.error("Failed to test stream data integration")
        return 1

    # Test the live trading script with dry run mode
    dry_run_success = await test_live_trading_dry_run()
    if not dry_run_success:
        logger.error("Failed to test live trading script with dry run mode")
        return 1

    logger.info("All tests passed successfully!")
    return 0

def main():
    """Main function."""
    return asyncio.run(main_async())

if __name__ == "__main__":
    sys.exit(main())
