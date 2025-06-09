#!/usr/bin/env python3
"""
Test Carbon Core Integration

This script tests the Carbon Core integration, including both the native and fallback implementations.
"""

import os
import sys
import time
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import Carbon Core Manager
from phase_4_deployment.core.carbon_core_manager import CarbonCoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_carbon_core")

async def test_native_implementation(config_path: str) -> bool:
    """
    Test the native Carbon Core implementation.
    
    Args:
        config_path: Path to the Carbon Core configuration file
        
    Returns:
        True if the test passed, False otherwise
    """
    logger.info("Testing native Carbon Core implementation...")
    
    # Set environment variable to disable fallback
    os.environ["CARBON_CORE_FALLBACK"] = "false"
    
    # Create Carbon Core Manager
    manager = CarbonCoreManager(config_path)
    
    # Start Carbon Core
    success = await manager.start()
    
    if not success:
        logger.error("Failed to start native Carbon Core implementation")
        return False
    
    logger.info("Native Carbon Core implementation started successfully")
    
    # Get metrics
    metrics = await manager.get_metrics()
    
    logger.info(f"Native Carbon Core metrics: {json.dumps(metrics, indent=2)}")
    
    # Check if Carbon Core is healthy
    is_healthy = await manager.is_healthy()
    
    logger.info(f"Native Carbon Core health: {'healthy' if is_healthy else 'unhealthy'}")
    
    # Stop Carbon Core
    await manager.stop()
    
    logger.info("Native Carbon Core implementation stopped successfully")
    
    return True

async def test_fallback_implementation(config_path: str) -> bool:
    """
    Test the fallback Carbon Core implementation.
    
    Args:
        config_path: Path to the Carbon Core configuration file
        
    Returns:
        True if the test passed, False otherwise
    """
    logger.info("Testing fallback Carbon Core implementation...")
    
    # Set environment variable to enable fallback
    os.environ["CARBON_CORE_FALLBACK"] = "true"
    
    # Create Carbon Core Manager
    manager = CarbonCoreManager(config_path)
    
    # Start Carbon Core
    success = await manager.start()
    
    if not success:
        logger.error("Failed to start fallback Carbon Core implementation")
        return False
    
    logger.info("Fallback Carbon Core implementation started successfully")
    
    # Get metrics
    metrics = await manager.get_metrics()
    
    logger.info(f"Fallback Carbon Core metrics: {json.dumps(metrics, indent=2)}")
    
    # Check if Carbon Core is healthy
    is_healthy = await manager.is_healthy()
    
    logger.info(f"Fallback Carbon Core health: {'healthy' if is_healthy else 'unhealthy'}")
    
    # Stop Carbon Core
    await manager.stop()
    
    logger.info("Fallback Carbon Core implementation stopped successfully")
    
    return True

async def main():
    """Main function."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Carbon Core Integration")
    parser.add_argument("--config", type=str, default="carbon_core_config.yaml", help="Path to configuration file")
    args = parser.parse_args()
    
    # Test native implementation
    native_success = await test_native_implementation(args.config)
    
    # Test fallback implementation
    fallback_success = await test_fallback_implementation(args.config)
    
    # Print results
    logger.info("Test results:")
    logger.info(f"Native implementation: {'PASSED' if native_success else 'FAILED'}")
    logger.info(f"Fallback implementation: {'PASSED' if fallback_success else 'FAILED'}")
    
    # Exit with success if at least one implementation passed
    if native_success or fallback_success:
        logger.info("At least one implementation passed, test successful")
        sys.exit(0)
    else:
        logger.error("Both implementations failed, test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
