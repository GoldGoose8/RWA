#!/usr/bin/env python3
"""
Carbon Core Client

This module provides a client for communicating with the Carbon Core Rust component.
It handles IPC communication, data serialization/deserialization, and fallback mechanisms.
"""

import os
import json
import time
import logging
import asyncio
import subprocess
import importlib
import zmq
import zmq.asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('carbon_core_client')

class CarbonCoreClient:
    """
    Client for communicating with the Carbon Core Rust component.
    
    This client handles:
    - Starting and stopping the Carbon Core process
    - Communicating with Carbon Core via ZeroMQ
    - Serializing and deserializing messages
    - Providing fallback mechanisms when Carbon Core is unavailable
    """
    
    def __init__(self, config_path: str = "configs/carbon_core_config.yaml"):
        """
        Initialize the Carbon Core client.
        
        Args:
            config_path: Path to the Carbon Core configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.process = None
        self.context = zmq.asyncio.Context()
        self.pub_socket = None
        self.sub_socket = None
        self.req_socket = None
        self.running = False
        self.fallback_module = None
        
        # Load fallback module if enabled
        if self.config['fallback']['enabled']:
            try:
                module_name = self.config['fallback']['python_module']
                self.fallback_module = importlib.import_module(module_name)
                logger.info(f"Loaded fallback module: {module_name}")
            except ImportError as e:
                logger.warning(f"Failed to load fallback module: {str(e)}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the Carbon Core configuration.
        
        Returns:
            Configuration dictionary
        """
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded Carbon Core configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load Carbon Core configuration: {str(e)}")
            # Return default configuration
            return {
                'core': {'enabled': False},
                'fallback': {'enabled': True, 'mode': 'python', 'python_module': 'core.carbon_core_fallback'}
            }
    
    async def start(self) -> bool:
        """
        Start the Carbon Core process and initialize communication.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.config['core']['enabled']:
            logger.info("Carbon Core is disabled in configuration, using fallback")
            return False
        
        try:
            # Start Carbon Core process
            binary_path = self.config['core']['binary_path']
            if not os.path.exists(binary_path):
                logger.warning(f"Carbon Core binary not found at {binary_path}, using fallback")
                return False
            
            # Start the process
            self.process = subprocess.Popen(
                [binary_path, "--config", self.config_path],
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
                return False
            
            # Initialize ZeroMQ sockets
            await self._init_sockets()
            
            self.running = True
            logger.info("Carbon Core started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start Carbon Core: {str(e)}")
            return False
    
    async def _init_sockets(self) -> None:
        """Initialize ZeroMQ sockets for communication with Carbon Core."""
        try:
            # Publisher socket (for sending commands to Carbon Core)
            self.pub_socket = self.context.socket(zmq.PUB)
            self.pub_socket.connect(self.config['communication']['zeromq']['pub_endpoint'])
            
            # Subscriber socket (for receiving data from Carbon Core)
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.connect(self.config['communication']['zeromq']['sub_endpoint'])
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            
            # Request-reply socket (for synchronous communication)
            self.req_socket = self.context.socket(zmq.REQ)
            self.req_socket.connect(self.config['communication']['zeromq']['req_endpoint'])
            
            logger.info("ZeroMQ sockets initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ZeroMQ sockets: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the Carbon Core process and clean up resources."""
        self.running = False
        
        # Close ZeroMQ sockets
        if self.pub_socket:
            self.pub_socket.close()
        
        if self.sub_socket:
            self.sub_socket.close()
        
        if self.req_socket:
            self.req_socket.close()
        
        # Terminate Carbon Core process
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        logger.info("Carbon Core stopped")
    
    async def send_command(self, command: str, data: Dict[str, Any]) -> None:
        """
        Send a command to Carbon Core.
        
        Args:
            command: Command name
            data: Command data
        """
        if not self.running or not self.pub_socket:
            logger.warning(f"Cannot send command {command}: Carbon Core not running")
            return
        
        try:
            message = {
                'command': command,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            await self.pub_socket.send_string(json.dumps(message))
            logger.debug(f"Sent command: {command}")
        except Exception as e:
            logger.error(f"Failed to send command {command}: {str(e)}")
    
    async def request(self, request_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a request to Carbon Core and wait for a response.
        
        Args:
            request_type: Type of request
            data: Request data
        
        Returns:
            Response data or None if request failed
        """
        if not self.running or not self.req_socket:
            logger.warning(f"Cannot send request {request_type}: Carbon Core not running")
            return self._fallback_request(request_type, data)
        
        try:
            message = {
                'request': request_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            # Send request
            await self.req_socket.send_string(json.dumps(message))
            
            # Wait for response with timeout
            response = await asyncio.wait_for(self.req_socket.recv_string(), timeout=5.0)
            
            # Parse response
            response_data = json.loads(response)
            logger.debug(f"Received response for {request_type}")
            
            return response_data
        
        except asyncio.TimeoutError:
            logger.error(f"Request {request_type} timed out")
            return self._fallback_request(request_type, data)
        
        except Exception as e:
            logger.error(f"Failed to send request {request_type}: {str(e)}")
            return self._fallback_request(request_type, data)
    
    def _fallback_request(self, request_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle a request using the fallback mechanism.
        
        Args:
            request_type: Type of request
            data: Request data
        
        Returns:
            Response data or None if fallback failed
        """
        if not self.config['fallback']['enabled'] or not self.fallback_module:
            logger.warning(f"No fallback available for request {request_type}")
            return None
        
        try:
            # Call the appropriate fallback method
            method_name = f"fallback_{request_type}"
            if hasattr(self.fallback_module, method_name):
                method = getattr(self.fallback_module, method_name)
                result = method(data)
                logger.info(f"Used fallback for request {request_type}")
                return result
            else:
                logger.warning(f"No fallback method {method_name} available")
                return None
        
        except Exception as e:
            logger.error(f"Fallback for request {request_type} failed: {str(e)}")
            return None
    
    async def get_market_microstructure(self, market: str) -> Optional[Dict[str, Any]]:
        """
        Get market microstructure data for a specific market.
        
        Args:
            market: Market symbol (e.g., 'SOL-USDC')
        
        Returns:
            Market microstructure data or None if request failed
        """
        return await self.request('get_market_microstructure', {'market': market})
    
    async def get_statistical_signals(self, signal_type: str) -> Optional[Dict[str, Any]]:
        """
        Get statistical signals of a specific type.
        
        Args:
            signal_type: Signal type (e.g., 'price_momentum')
        
        Returns:
            Statistical signal data or None if request failed
        """
        return await self.request('get_statistical_signals', {'signal_type': signal_type})
    
    async def get_rl_execution_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get reinforcement learning execution metrics.
        
        Returns:
            RL execution metrics or None if request failed
        """
        return await self.request('get_rl_execution_metrics', {})
    
    async def get_system_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get Carbon Core system metrics.
        
        Returns:
            System metrics or None if request failed
        """
        return await self.request('get_system_metrics', {})
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all Carbon Core metrics.
        
        Returns:
            Dictionary containing all metrics
        """
        # Get all metrics in parallel
        tasks = [
            self.get_system_metrics(),
            self.get_rl_execution_metrics()
        ]
        
        # Add market microstructure tasks for each market
        if self.config['market_microstructure']['enabled']:
            for market in self.config['market_microstructure']['markets']:
                tasks.append(self.get_market_microstructure(market))
        
        # Add statistical signal tasks for each signal type
        if self.config['statistical_signal_processing']['enabled']:
            for signal_type in self.config['statistical_signal_processing']['signal_types']:
                tasks.append(self.get_statistical_signals(signal_type))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': results[0] if not isinstance(results[0], Exception) else None,
            'rl_execution': results[1] if not isinstance(results[1], Exception) else None,
            'market_microstructure': {'markets': {}},
            'statistical_signals': {'signals': {}}
        }
        
        # Process market microstructure results
        if self.config['market_microstructure']['enabled']:
            markets = self.config['market_microstructure']['markets']
            for i, market in enumerate(markets):
                result_index = 2 + i
                if result_index < len(results) and not isinstance(results[result_index], Exception):
                    metrics['market_microstructure']['markets'][market] = results[result_index]
        
        # Process statistical signal results
        if self.config['statistical_signal_processing']['enabled']:
            signal_types = self.config['statistical_signal_processing']['signal_types']
            offset = 2 + len(self.config['market_microstructure']['markets'])
            for i, signal_type in enumerate(signal_types):
                result_index = offset + i
                if result_index < len(results) and not isinstance(results[result_index], Exception):
                    metrics['statistical_signals']['signals'][signal_type] = results[result_index]
        
        return metrics
