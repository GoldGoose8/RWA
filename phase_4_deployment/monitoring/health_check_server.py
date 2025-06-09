#!/usr/bin/env python3
"""
Health Check Server

This module provides a health check server for monitoring the trading system.
"""

import os
import sys
import json
import time
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

# Install required packages
try:
    import zmq
    import zmq.asyncio
    from aiohttp import web
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyzmq", "aiohttp"])
    import zmq
    import zmq.asyncio
    from aiohttp import web

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import communication layer client
from phase_4_deployment.python_comm_layer.client import RustCommClient, CommunicationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthCheckServer:
    """Health check server for monitoring the trading system."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        carbon_core_pub_endpoint: str = "tcp://127.0.0.1:5556",
        carbon_core_sub_endpoint: str = "tcp://127.0.0.1:5555",
        carbon_core_req_endpoint: str = "tcp://127.0.0.1:5557",
        host: str = "0.0.0.0",
        port: int = 8080,
    ):
        """
        Initialize the health check server.
        
        Args:
            config: Configuration dictionary
            carbon_core_pub_endpoint: Carbon Core publisher endpoint
            carbon_core_sub_endpoint: Carbon Core subscriber endpoint
            carbon_core_req_endpoint: Carbon Core request-reply endpoint
            host: Server host
            port: Server port
        """
        self.config = config
        self.host = host
        self.port = port
        
        # Create communication client for Carbon Core
        self.carbon_core_client = RustCommClient(
            pub_endpoint=carbon_core_pub_endpoint,
            sub_endpoint=carbon_core_sub_endpoint,
            req_endpoint=carbon_core_req_endpoint,
        )
        
        # Initialize component status
        self.component_status = {
            "carbon_core": {"status": "unknown", "last_update": None},
            "signal_generator": {"status": "unknown", "last_update": None},
            "strategy_runner": {"status": "unknown", "last_update": None},
            "risk_manager": {"status": "unknown", "last_update": None},
            "transaction_preparer": {"status": "unknown", "last_update": None},
            "transaction_executor": {"status": "unknown", "last_update": None},
        }
        
        # Initialize metrics
        self.metrics = {
            "system": {
                "start_time": datetime.now().isoformat(),
                "uptime_seconds": 0,
                "last_update": datetime.now().isoformat(),
            },
            "carbon_core": {},
            "signal_generator": {},
            "strategy_runner": {},
            "risk_manager": {},
            "transaction_preparer": {},
            "transaction_executor": {},
        }
        
        # Initialize alerts
        self.alerts = []
        
        # Initialize state
        self.running = False
        self.tasks = []
        self.app = None
        self.runner = None
        self.site = None
        
        logger.info("Initialized health check server")
    
    async def start(self):
        """Start the health check server."""
        if self.running:
            logger.warning("Health check server is already running")
            return
        
        logger.info("Starting health check server...")
        
        # Connect to Carbon Core
        await self.carbon_core_client.connect()
        logger.info("Connected to Carbon Core")
        
        # Subscribe to component status
        await self._subscribe_to_component_status()
        
        # Subscribe to metrics
        await self._subscribe_to_metrics()
        
        # Create web application
        self.app = web.Application()
        self.app.add_routes([
            web.get("/", self._handle_root),
            web.get("/health", self._handle_health),
            web.get("/livez", self._handle_livez),
            web.get("/readyz", self._handle_readyz),
            web.get("/metrics", self._handle_metrics),
            web.get("/status", self._handle_status),
            web.get("/alerts", self._handle_alerts),
        ])
        
        # Start web server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"Web server started at http://{self.host}:{self.port}")
        
        # Set running flag
        self.running = True
        
        # Start health check tasks
        self.tasks = [
            asyncio.create_task(self._run_health_check()),
            asyncio.create_task(self._run_metrics_update()),
        ]
        
        logger.info("Health check server started")
    
    async def stop(self):
        """Stop the health check server."""
        if not self.running:
            logger.warning("Health check server is not running")
            return
        
        logger.info("Stopping health check server...")
        
        # Set running flag
        self.running = False
        
        # Cancel tasks
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Stop web server
        if self.site:
            await self.site.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        # Disconnect from Carbon Core
        await self.carbon_core_client.disconnect()
        logger.info("Disconnected from Carbon Core")
        
        logger.info("Health check server stopped")
    
    async def _subscribe_to_component_status(self):
        """Subscribe to component status."""
        logger.info("Subscribing to component status...")
        
        # Subscribe to Carbon Core status
        await self.carbon_core_client.subscribe("status/carbon_core", self._handle_component_status_update)
        logger.info("Subscribed to Carbon Core status")
        
        # Subscribe to Signal Generator status
        await self.carbon_core_client.subscribe("status/signal_generator", self._handle_component_status_update)
        logger.info("Subscribed to Signal Generator status")
        
        # Subscribe to Strategy Runner status
        await self.carbon_core_client.subscribe("status/strategy_runner", self._handle_component_status_update)
        logger.info("Subscribed to Strategy Runner status")
        
        # Subscribe to Risk Manager status
        await self.carbon_core_client.subscribe("status/risk_manager", self._handle_component_status_update)
        logger.info("Subscribed to Risk Manager status")
        
        # Subscribe to Transaction Preparer status
        await self.carbon_core_client.subscribe("status/transaction_preparer", self._handle_component_status_update)
        logger.info("Subscribed to Transaction Preparer status")
        
        # Subscribe to Transaction Executor status
        await self.carbon_core_client.subscribe("status/transaction_executor", self._handle_component_status_update)
        logger.info("Subscribed to Transaction Executor status")
    
    async def _subscribe_to_metrics(self):
        """Subscribe to metrics."""
        logger.info("Subscribing to metrics...")
        
        # Subscribe to Carbon Core metrics
        await self.carbon_core_client.subscribe("metrics/carbon_core", self._handle_metrics_update)
        logger.info("Subscribed to Carbon Core metrics")
        
        # Subscribe to Signal Generator metrics
        await self.carbon_core_client.subscribe("metrics/signal_generator", self._handle_metrics_update)
        logger.info("Subscribed to Signal Generator metrics")
        
        # Subscribe to Strategy Runner metrics
        await self.carbon_core_client.subscribe("metrics/strategy_runner", self._handle_metrics_update)
        logger.info("Subscribed to Strategy Runner metrics")
        
        # Subscribe to Risk Manager metrics
        await self.carbon_core_client.subscribe("metrics/risk_manager", self._handle_metrics_update)
        logger.info("Subscribed to Risk Manager metrics")
        
        # Subscribe to Transaction Preparer metrics
        await self.carbon_core_client.subscribe("metrics/transaction_preparer", self._handle_metrics_update)
        logger.info("Subscribed to Transaction Preparer metrics")
        
        # Subscribe to Transaction Executor metrics
        await self.carbon_core_client.subscribe("metrics/transaction_executor", self._handle_metrics_update)
        logger.info("Subscribed to Transaction Executor metrics")
    
    async def _run_health_check(self):
        """Run health check."""
        logger.info("Starting health check loop...")
        
        try:
            while self.running:
                # Check component status
                await self._check_component_status()
                
                # Sleep for health check interval
                await asyncio.sleep(self.config.get("monitoring", {}).get("health_check_interval_ms", 10000) / 1000)
        except asyncio.CancelledError:
            logger.info("Health check loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in health check loop: {str(e)}")
    
    async def _run_metrics_update(self):
        """Run metrics update."""
        logger.info("Starting metrics update loop...")
        
        try:
            while self.running:
                # Update system metrics
                self._update_system_metrics()
                
                # Sleep for metrics interval
                await asyncio.sleep(self.config.get("monitoring", {}).get("metrics_interval_ms", 5000) / 1000)
        except asyncio.CancelledError:
            logger.info("Metrics update loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in metrics update loop: {str(e)}")
    
    async def _check_component_status(self):
        """Check component status."""
        try:
            # Check if components are alive
            now = datetime.now()
            
            for component, status in self.component_status.items():
                if status["last_update"] is None:
                    continue
                
                # Calculate time since last update
                last_update = datetime.fromisoformat(status["last_update"])
                time_since_update = (now - last_update).total_seconds()
                
                # Check if component is alive
                if time_since_update > 60:  # 60 seconds timeout
                    # Component is not responding
                    if status["status"] != "error":
                        # Update status
                        status["status"] = "error"
                        
                        # Add alert
                        self._add_alert(
                            level="error",
                            component=component,
                            message=f"{component} is not responding for {time_since_update:.1f} seconds",
                        )
                        
                        logger.error(f"{component} is not responding for {time_since_update:.1f} seconds")
        except Exception as e:
            logger.error(f"Error checking component status: {str(e)}")
    
    def _update_system_metrics(self):
        """Update system metrics."""
        try:
            # Update uptime
            start_time = datetime.fromisoformat(self.metrics["system"]["start_time"])
            uptime_seconds = (datetime.now() - start_time).total_seconds()
            
            # Update system metrics
            self.metrics["system"].update({
                "uptime_seconds": uptime_seconds,
                "last_update": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error updating system metrics: {str(e)}")
    
    def _add_alert(self, level: str, component: str, message: str):
        """
        Add an alert.
        
        Args:
            level: Alert level ("info", "warning", "error", "critical")
            component: Component name
            message: Alert message
        """
        # Create alert
        alert = {
            "level": level,
            "component": component,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add alert to list
        self.alerts.append(alert)
        
        # Limit alerts to 100
        if len(self.alerts) > 100:
            self.alerts.pop(0)
        
        # Log alert
        if level == "info":
            logger.info(f"Alert: {message}")
        elif level == "warning":
            logger.warning(f"Alert: {message}")
        elif level == "error":
            logger.error(f"Alert: {message}")
        elif level == "critical":
            logger.critical(f"Alert: {message}")
    
    async def _handle_component_status_update(self, message: Dict[str, Any]):
        """
        Handle component status update.
        
        Args:
            message: Component status update message
        """
        try:
            # Extract component
            topic = message.get("topic", "")
            component = topic.split("/")[1] if len(topic.split("/")) > 1 else ""
            
            if not component or component not in self.component_status:
                return
            
            # Extract status
            status = message.get("data", {}).get("status", "unknown")
            
            # Update component status
            self.component_status[component].update({
                "status": status,
                "last_update": datetime.now().isoformat(),
            })
            
            logger.debug(f"Updated {component} status: {status}")
        except Exception as e:
            logger.error(f"Error handling component status update: {str(e)}")
    
    async def _handle_metrics_update(self, message: Dict[str, Any]):
        """
        Handle metrics update.
        
        Args:
            message: Metrics update message
        """
        try:
            # Extract component
            topic = message.get("topic", "")
            component = topic.split("/")[1] if len(topic.split("/")) > 1 else ""
            
            if not component or component not in self.metrics:
                return
            
            # Extract metrics
            metrics = message.get("data", {})
            
            # Update metrics
            self.metrics[component] = metrics
            
            logger.debug(f"Updated {component} metrics")
        except Exception as e:
            logger.error(f"Error handling metrics update: {str(e)}")
    
    async def _handle_root(self, request):
        """
        Handle root request.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        return web.Response(text="Q5 Trading System Health Check Server", content_type="text/plain")
    
    async def _handle_health(self, request):
        """
        Handle health request.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        # Check if all components are healthy
        all_healthy = all(status["status"] == "ok" for status in self.component_status.values())
        
        if all_healthy:
            return web.Response(text="OK", content_type="text/plain")
        else:
            return web.Response(text="ERROR", status=500, content_type="text/plain")
    
    async def _handle_livez(self, request):
        """
        Handle livez request.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        return web.Response(text="OK", content_type="text/plain")
    
    async def _handle_readyz(self, request):
        """
        Handle readyz request.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        # Check if all components are ready
        all_ready = all(status["status"] in ["ok", "warning"] for status in self.component_status.values())
        
        if all_ready:
            return web.Response(text="OK", content_type="text/plain")
        else:
            return web.Response(text="ERROR", status=500, content_type="text/plain")
    
    async def _handle_metrics(self, request):
        """
        Handle metrics request.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        return web.json_response(self.metrics)
    
    async def _handle_status(self, request):
        """
        Handle status request.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        return web.json_response(self.component_status)
    
    async def _handle_alerts(self, request):
        """
        Handle alerts request.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        return web.json_response(self.alerts)

async def main():
    """Main function."""
    # Load configuration
    import yaml
    
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        config = {}
    
    # Create health check server
    health_check_server = HealthCheckServer(config)
    
    try:
        # Start health check server
        await health_check_server.start()
        
        # Run until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Stop health check server
        await health_check_server.stop()

if __name__ == "__main__":
    asyncio.run(main())
