#!/usr/bin/env python3
"""
Carbon Core Manager

This module manages the Carbon Core component, handling the transition between
the native Rust binary and the Python fallback implementation.
"""

import os
import sys
import time
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("carbon_core_manager")

class CarbonCoreManager:
    """
    Manages the Carbon Core component, handling the transition between
    the native Rust binary and the Python fallback implementation.
    """

    def __init__(self, config_path: str = "carbon_core_config.yaml"):
        """
        Initialize the CarbonCoreManager.

        Args:
            config_path: Path to the Carbon Core configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.binary_path = self._get_binary_path()
        self.process = None
        self.fallback_enabled = os.environ.get("CARBON_CORE_FALLBACK", "true").lower() == "true"
        self.using_fallback = False
        self.fallback_client = None

        logger.info(f"Initialized CarbonCoreManager with binary path: {self.binary_path}")
        logger.info(f"Fallback enabled: {self.fallback_enabled}")

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        try:
            import yaml
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            logger.info(f"Loaded configuration from {self.config_path}")
            return config or {}
        except Exception as e:
            logger.warning(f"Error loading configuration from {self.config_path}: {str(e)}")
            logger.warning("Using default configuration")
            return {}

    def _get_binary_path(self) -> str:
        """
        Get the path to the Carbon Core binary.

        Returns:
            Path to the Carbon Core binary
        """
        # Check environment variable
        binary_path = os.environ.get("CARBON_CORE_BINARY_PATH")

        if binary_path:
            return binary_path

        # Check common locations
        common_paths = [
            "bin/carbon_core",
            "../bin/carbon_core",
            "carbon_core/target/release/carbon_core",
            "../carbon_core/target/release/carbon_core"
        ]

        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path

        # Default to bin/carbon_core
        return "bin/carbon_core"

    async def start(self) -> bool:
        """
        Start the Carbon Core component.

        Returns:
            True if started successfully, False otherwise
        """
        # Check if binary exists and is executable
        if os.path.exists(self.binary_path) and os.access(self.binary_path, os.X_OK):
            logger.info(f"Found Carbon Core binary at {self.binary_path}")

            try:
                # Start the Carbon Core process
                logger.info("Starting Carbon Core process...")

                self.process = subprocess.Popen(
                    [self.binary_path, "--config", self.config_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Wait for process to start
                await asyncio.sleep(1.0)

                # Check if process is running
                if self.process.poll() is not None:
                    stdout, stderr = self.process.communicate()
                    logger.error(f"Carbon Core process failed to start: {stderr}")

                    if self.fallback_enabled:
                        logger.warning("Falling back to Python implementation")
                        return await self._start_fallback()
                    else:
                        return False

                logger.info("Carbon Core process started successfully")
                self.using_fallback = False
                return True
            except Exception as e:
                logger.error(f"Error starting Carbon Core process: {str(e)}")

                if self.fallback_enabled:
                    logger.warning("Falling back to Python implementation")
                    return await self._start_fallback()
                else:
                    return False
        else:
            logger.warning(f"Carbon Core binary not found at {self.binary_path}")

            if self.fallback_enabled:
                logger.warning("Falling back to Python implementation")
                return await self._start_fallback()
            else:
                logger.error("Carbon Core binary not found and fallback is disabled")
                return False

    async def _start_fallback(self) -> bool:
        """
        Start the Python fallback implementation.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Import the fallback client
            from phase_4_deployment.core.carbon_core_client import CarbonCoreClient

            # Create fallback client with fallback configuration
            fallback_config = self.config.copy() if self.config else {}
            if 'fallback' not in fallback_config:
                fallback_config['fallback'] = {}
            fallback_config['fallback']['enabled'] = True
            fallback_config['core'] = {'enabled': False}

            # Create a temporary config file for the fallback
            import yaml
            fallback_config_path = "carbon_core_fallback_config.yaml"
            with open(fallback_config_path, 'w') as f:
                yaml.dump(fallback_config, f)

            # Create fallback client
            self.fallback_client = CarbonCoreClient(fallback_config_path)

            # Start fallback client
            success = await self.fallback_client.start()

            if success:
                logger.info("Carbon Core fallback started successfully")
                self.using_fallback = True
                return True
            else:
                # Try direct fallback module import
                try:
                    from phase_4_deployment.core.carbon_core_fallback import CarbonCoreFallback

                    # Create fallback implementation
                    self.fallback_implementation = CarbonCoreFallback(self.config_path)

                    # Start fallback implementation
                    success = await self.fallback_implementation.start()

                    if success:
                        logger.info("Carbon Core fallback implementation started successfully")
                        self.using_fallback = True
                        return True
                    else:
                        logger.error("Failed to start Carbon Core fallback implementation")
                        return False
                except Exception as e:
                    logger.error(f"Error starting Carbon Core fallback implementation: {str(e)}")
                    return False
        except Exception as e:
            logger.error(f"Error starting Carbon Core fallback: {str(e)}")
            return False

    async def stop(self) -> None:
        """Stop the Carbon Core component."""
        if self.using_fallback and self.fallback_client:
            # Stop fallback client
            await self.fallback_client.stop()
            logger.info("Carbon Core fallback stopped")
        elif self.process:
            # Stop Carbon Core process
            try:
                self.process.terminate()
                await asyncio.sleep(1.0)

                if self.process.poll() is None:
                    # Force kill if not terminated
                    self.process.kill()

                logger.info("Carbon Core process stopped")
            except Exception as e:
                logger.error(f"Error stopping Carbon Core process: {str(e)}")

        self.process = None
        self.fallback_client = None

    async def is_healthy(self) -> bool:
        """
        Check if the Carbon Core component is healthy.

        Returns:
            True if healthy, False otherwise
        """
        if self.using_fallback:
            if hasattr(self, 'fallback_implementation') and self.fallback_implementation:
                # For direct fallback implementation, just check if it's running
                return getattr(self.fallback_implementation, 'running', True)
            elif self.fallback_client:
                # For fallback client, check if it's connected or running
                if hasattr(self.fallback_client, 'is_healthy'):
                    return await self.fallback_client.is_healthy()
                else:
                    return getattr(self.fallback_client, 'connected', True) or getattr(self.fallback_client, 'running', True)
            else:
                logger.warning("No fallback implementation available")
                return False
        elif self.process:
            # Check if process is still running
            if self.process.poll() is None:
                return True
            else:
                logger.warning("Carbon Core process is not running")
                return False
        else:
            logger.warning("Carbon Core is not running")
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from the Carbon Core component.

        Returns:
            Dictionary with metrics
        """
        if self.using_fallback:
            if hasattr(self, 'fallback_implementation') and self.fallback_implementation:
                # Get metrics from direct fallback implementation
                try:
                    request = {
                        "request": "get_metrics",
                        "data": {}
                    }
                    response = await self.fallback_implementation._process_request(request)

                    if response and "status" in response and response["status"] == "success":
                        metrics = response.get("data", {})
                        metrics["using_fallback"] = True
                        metrics["status"] = "running"
                        metrics["timestamp"] = time.time()
                        return metrics
                    else:
                        return {
                            "status": "error",
                            "using_fallback": True,
                            "error": "Failed to get metrics from fallback implementation",
                            "timestamp": time.time()
                        }
                except Exception as e:
                    logger.error(f"Error getting metrics from fallback implementation: {str(e)}")
                    return {
                        "status": "error",
                        "using_fallback": True,
                        "error": str(e),
                        "timestamp": time.time()
                    }
            elif self.fallback_client:
                # Get metrics from fallback client
                try:
                    # Try to get all metrics
                    metrics = await self.fallback_client.get_all_metrics()
                    if metrics:
                        metrics["using_fallback"] = True
                        metrics["status"] = "running"
                        return metrics

                    # Fallback to system metrics
                    metrics = await self.fallback_client.get_system_metrics()
                    if metrics:
                        return {
                            "status": "running",
                            "using_fallback": True,
                            "system_metrics": metrics,
                            "timestamp": time.time()
                        }

                    # If all else fails, return basic status
                    return {
                        "status": "running",
                        "using_fallback": True,
                        "timestamp": time.time()
                    }
                except Exception as e:
                    logger.error(f"Error getting metrics from fallback client: {str(e)}")
                    return {
                        "status": "error",
                        "using_fallback": True,
                        "error": str(e),
                        "timestamp": time.time()
                    }
            else:
                return {
                    "status": "not_running",
                    "using_fallback": True,
                    "timestamp": time.time()
                }
        elif self.process and self.process.poll() is None:
            # Get metrics from Carbon Core process
            try:
                # Create a client to get metrics if we don't have one
                if not hasattr(self, 'client') or not self.client:
                    from phase_4_deployment.core.carbon_core_client import CarbonCoreClient
                    self.client = CarbonCoreClient(self.config_path)
                    await self.client.connect()

                # Get all metrics
                metrics = await self.client.get_all_metrics()
                if metrics:
                    metrics["using_fallback"] = False
                    metrics["status"] = "running"
                    return metrics

                # Fallback to system metrics
                metrics = await self.client.get_system_metrics()
                if metrics:
                    return {
                        "status": "running",
                        "using_fallback": False,
                        "system_metrics": metrics,
                        "timestamp": time.time()
                    }

                # If all else fails, return basic status
                return {
                    "status": "running",
                    "using_fallback": False,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting metrics from Carbon Core process: {str(e)}")
                return {
                    "status": "error",
                    "using_fallback": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
        else:
            return {
                "status": "not_running",
                "using_fallback": self.using_fallback,
                "timestamp": time.time()
            }

async def main():
    """Main function."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Carbon Core Manager")
    parser.add_argument("--config", type=str, default="carbon_core_config.yaml", help="Path to configuration file")
    args = parser.parse_args()

    # Create Carbon Core manager
    manager = CarbonCoreManager(args.config)

    # Start Carbon Core
    if await manager.start():
        try:
            # Run health check loop
            while True:
                is_healthy = await manager.is_healthy()
                logger.info(f"Carbon Core health: {'healthy' if is_healthy else 'unhealthy'}")

                if not is_healthy:
                    logger.warning("Attempting to restart Carbon Core...")
                    await manager.stop()
                    if not await manager.start():
                        logger.error("Failed to restart Carbon Core")
                        break

                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            # Stop Carbon Core
            await manager.stop()
    else:
        logger.error("Failed to start Carbon Core")

if __name__ == "__main__":
    asyncio.run(main())
