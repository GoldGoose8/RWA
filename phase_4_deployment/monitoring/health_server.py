#!/usr/bin/env python3
"""
Health Server for Synergy7 Trading System

This module provides a health server for the Synergy7 Trading System.
"""

import os
import json
import time
import logging
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any, Optional, Union

# Import monitoring service
try:
    # First try to import from utils (the real implementation)
    from shared.utils.monitoring import get_monitoring_service
except ImportError:
    # Fall back to mock implementation if real one is not available
    try:
        from phase_4_deployment.monitoring.mock_monitoring_service import get_monitoring_service
    except ImportError:
        # Last resort, try relative import
        from .mock_monitoring_service import get_monitoring_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("health_server")

# Create FastAPI app
app = FastAPI(
    title="Synergy7 Trading System Health Server",
    description="Health server for Synergy7 Trading System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get monitoring service
monitoring = get_monitoring_service()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Synergy7 Trading System Health Server"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    # Run health checks
    health_results = monitoring.run_health_checks()

    # Calculate overall health
    overall_health = all(health_results.values())

    return {
        "overall_health": overall_health,
        "components": health_results,
        "timestamp": time.time()
    }

@app.get("/livez")
async def livez():
    """Liveness probe endpoint."""
    return {"status": "alive"}

@app.get("/readyz")
async def readyz():
    """Readiness probe endpoint."""
    # Run health checks
    health_results = monitoring.run_health_checks()

    # Calculate overall health
    overall_health = all(health_results.values())

    if overall_health:
        return {"status": "ready"}
    else:
        return {"status": "not ready", "components": health_results}

def start_health_server(host: str = "0.0.0.0", port: int = 8080):
    """
    Start the health server in a separate thread.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    # Start monitoring service
    monitoring.start()

    # Start health server in a separate thread
    import threading
    thread = threading.Thread(
        target=lambda: uvicorn.run(app, host=host, port=port),
        daemon=True
    )
    thread.start()
    logger.info(f"Health server started on http://{host}:{port}")

    return thread

if __name__ == "__main__":
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Health Server for Synergy7 Trading System")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    args = parser.parse_args()

    # Start health server
    start_health_server(host=args.host, port=args.port)
