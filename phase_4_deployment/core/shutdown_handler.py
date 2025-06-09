#!/usr/bin/env python3
"""
Shutdown Handler for Q5 Trading System

This module provides a shutdown handler to gracefully handle shutdown signals.
"""

import os
import sys
import signal
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable

logger = logging.getLogger(__name__)

class ShutdownHandler:
    """Shutdown handler for Q5 Trading System."""
    
    def __init__(self):
        """Initialize the shutdown handler."""
        self.shutdown_callbacks = []
        self.is_shutting_down = False
        self.loop = None
    
    def register_callback(self, callback: Callable[[], None]):
        """
        Register a callback to be called on shutdown.
        
        Args:
            callback: Callback function to be called on shutdown
        """
        self.shutdown_callbacks.append(callback)
        logger.debug(f"Registered shutdown callback: {callback.__name__}")
    
    def register_async_callback(self, callback: Callable[[], asyncio.Future]):
        """
        Register an async callback to be called on shutdown.
        
        Args:
            callback: Async callback function to be called on shutdown
        """
        self.shutdown_callbacks.append(callback)
        logger.debug(f"Registered async shutdown callback: {callback.__name__}")
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        # Get the current event loop
        self.loop = asyncio.get_event_loop()
        
        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            self.loop.add_signal_handler(
                sig,
                lambda sig=sig: asyncio.create_task(self.shutdown(sig))
            )
        
        logger.info("Signal handlers set up for graceful shutdown")
    
    async def shutdown(self, sig: signal.Signals = None):
        """
        Shutdown the system gracefully.
        
        Args:
            sig: Signal that triggered the shutdown
        """
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return
        
        self.is_shutting_down = True
        
        if sig:
            logger.info(f"Received signal {sig.name}, shutting down...")
        else:
            logger.info("Shutting down...")
        
        # Call all registered callbacks
        for callback in self.shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in shutdown callback {callback.__name__}: {str(e)}")
        
        # Stop the event loop
        if self.loop:
            self.loop.stop()
        
        logger.info("Shutdown complete")

# Global shutdown handler instance
_shutdown_handler = ShutdownHandler()

def get_shutdown_handler() -> ShutdownHandler:
    """
    Get the global shutdown handler instance.
    
    Returns:
        ShutdownHandler: Global shutdown handler instance
    """
    return _shutdown_handler

def register_shutdown_callback(callback: Callable[[], None]):
    """
    Register a callback to be called on shutdown.
    
    Args:
        callback: Callback function to be called on shutdown
    """
    _shutdown_handler.register_callback(callback)

def register_async_shutdown_callback(callback: Callable[[], asyncio.Future]):
    """
    Register an async callback to be called on shutdown.
    
    Args:
        callback: Async callback function to be called on shutdown
    """
    _shutdown_handler.register_async_callback(callback)

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    _shutdown_handler.setup_signal_handlers()

async def shutdown(sig: signal.Signals = None):
    """
    Shutdown the system gracefully.
    
    Args:
        sig: Signal that triggered the shutdown
    """
    await _shutdown_handler.shutdown(sig)

class ShutdownManager:
    """Context manager for graceful shutdown."""
    
    def __init__(self, *resources):
        """
        Initialize the shutdown manager.
        
        Args:
            resources: Resources to be closed on shutdown
        """
        self.resources = resources
        self.shutdown_handler = get_shutdown_handler()
    
    async def __aenter__(self):
        """Enter the context manager."""
        # Set up signal handlers
        self.shutdown_handler.setup_signal_handlers()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        # Close all resources
        for resource in self.resources:
            try:
                if hasattr(resource, "close"):
                    if asyncio.iscoroutinefunction(resource.close):
                        await resource.close()
                    else:
                        resource.close()
                elif hasattr(resource, "__aexit__"):
                    await resource.__aexit__(exc_type, exc_val, exc_tb)
                elif hasattr(resource, "__exit__"):
                    resource.__exit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                logger.error(f"Error closing resource {resource}: {str(e)}")
        
        # Shutdown the system
        await self.shutdown_handler.shutdown()

async def main():
    """Example usage of the shutdown handler."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create some resources
    class Resource:
        def __init__(self, name):
            self.name = name
        
        def close(self):
            logger.info(f"Closing resource: {self.name}")
    
    class AsyncResource:
        def __init__(self, name):
            self.name = name
        
        async def close(self):
            logger.info(f"Closing async resource: {self.name}")
            await asyncio.sleep(0.1)
    
    # Create resources
    resource1 = Resource("Resource 1")
    resource2 = AsyncResource("Resource 2")
    
    # Use the shutdown manager
    async with ShutdownManager(resource1, resource2):
        # Register a shutdown callback
        def on_shutdown():
            logger.info("Shutdown callback called")
        
        register_shutdown_callback(on_shutdown)
        
        # Register an async shutdown callback
        async def on_async_shutdown():
            logger.info("Async shutdown callback called")
            await asyncio.sleep(0.1)
        
        register_async_shutdown_callback(on_async_shutdown)
        
        # Run the main loop
        logger.info("Running main loop...")
        try:
            # Simulate some work
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
    
    logger.info("Main function completed")

if __name__ == "__main__":
    asyncio.run(main())
