#!/usr/bin/env python3
"""
Health Check Server for Q5 Trading System

This module provides a simple HTTP server for health checks.
"""

import os
import json
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from aiohttp import web

from shared.utils.monitoring import get_monitoring_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('health_server')

class HealthServer:
    """
    Health check server for the Q5 Trading System.
    """

    def __init__(self, host: str = '0.0.0.0', port: int = 8081):
        """
        Initialize the health check server.

        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.monitoring = get_monitoring_service()
        self.setup_routes()
        self.server_task = None

        # Try to start on the specified port, if it fails, try alternative ports
        self.original_port = port

    def setup_routes(self) -> None:
        """Set up server routes."""
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/livez', self.livez_handler)
        self.app.router.add_get('/readyz', self.readyz_handler)
        self.app.router.add_get('/metrics', self.metrics_handler)

    async def health_handler(self, request: web.Request) -> web.Response:
        """
        Handle health check requests.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        health_status = self.monitoring.run_health_checks()
        overall_health = all(health_status.values())

        response_data = {
            'status': 'healthy' if overall_health else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'components': health_status
        }

        return web.json_response(
            response_data,
            status=200 if overall_health else 503
        )

    async def livez_handler(self, request: web.Request) -> web.Response:
        """
        Handle liveness check requests.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        # Liveness just checks if the server is running
        return web.json_response({
            'status': 'alive',
            'timestamp': datetime.now().isoformat()
        })

    async def readyz_handler(self, request: web.Request) -> web.Response:
        """
        Handle readiness check requests.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        # Readiness checks if the system is ready to handle requests
        health_status = self.monitoring.run_health_checks()
        overall_health = all(health_status.values())

        response_data = {
            'status': 'ready' if overall_health else 'not_ready',
            'timestamp': datetime.now().isoformat(),
            'components': health_status
        }

        return web.json_response(
            response_data,
            status=200 if overall_health else 503
        )

    async def metrics_handler(self, request: web.Request) -> web.Response:
        """
        Handle metrics requests.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        metrics = self.monitoring.get_metrics()
        return web.json_response(metrics)

    async def start(self) -> None:
        """Start the health check server."""
        runner = web.AppRunner(self.app)
        await runner.setup()

        # Try the original port first
        try:
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            logger.info(f"Health check server started on http://{self.host}:{self.port}")
            return
        except OSError as e:
            logger.warning(f"Could not start health check server on port {self.port}: {str(e)}")
            logger.warning("Trying alternative ports...")

        # Try alternative ports
        alternative_ports = [8081, 8082, 8083, 8084, 8085]
        for alt_port in alternative_ports:
            if alt_port == self.port:
                continue

            try:
                site = web.TCPSite(runner, self.host, alt_port)
                await site.start()
                self.port = alt_port
                logger.info(f"Health check server started on alternative port http://{self.host}:{self.port}")
                return
            except OSError as e:
                logger.warning(f"Could not start health check server on port {alt_port}: {str(e)}")

        logger.error("Could not start health check server on any port")
        logger.warning("Continuing without health check server")

    def start_in_thread(self) -> None:
        """Start the health check server in a separate thread."""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start())
            loop.run_forever()

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        logger.info("Health check server started in background thread")

    async def stop(self) -> None:
        """Stop the health check server."""
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
        logger.info("Health check server stopped")

def start_health_server(host: str = '0.0.0.0', port: int = 8080) -> HealthServer:
    """
    Start the health check server.

    Args:
        host: Server host
        port: Server port

    Returns:
        HealthServer instance
    """
    server = HealthServer(host, port)
    server.start_in_thread()
    return server

if __name__ == "__main__":
    # Example usage
    server = HealthServer()

    # Register some example components
    monitoring = get_monitoring_service()
    monitoring.register_component('api', lambda: True)
    monitoring.register_component('database', lambda: True)

    # Start the server
    asyncio.run(server.start())
