#!/usr/bin/env python3
"""
Stream Data Ingestion Client

This module provides a client for consuming data from low-latency streams
such as QuickNode Yellowstone gRPC and Jito ShredStream.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Union, List, Callable, Awaitable
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stream_data_ingestor')

class StreamType(Enum):
    """Enum for stream types."""
    QUICKNODE_YELLOWSTONE = "quicknode_yellowstone"
    JITO_SHREDSTREAM = "jito_shredstream"
    HELIUS_WEBHOOK = "helius_webhook"
    CUSTOM_WEBSOCKET = "custom_websocket"

class StreamDataIngestor:
    """
    Client for consuming data from low-latency streams.

    This class provides a unified interface for consuming data from different
    stream sources such as QuickNode Yellowstone gRPC and Jito ShredStream.
    """

    def __init__(self,
                 stream_type: StreamType,
                 stream_url: str,
                 api_key: Optional[str] = None,
                 subscription_params: Optional[Dict[str, Any]] = None,
                 max_reconnect_attempts: int = 5,
                 reconnect_delay: float = 1.0,
                 buffer_size: int = 1000):
        """
        Initialize the stream data ingestor.

        Args:
            stream_type: Type of stream to consume
            stream_url: URL of the stream
            api_key: API key for authentication (if required)
            subscription_params: Parameters for subscription (if required)
            max_reconnect_attempts: Maximum number of reconnect attempts
            reconnect_delay: Delay between reconnect attempts in seconds
            buffer_size: Size of the buffer for storing messages
        """
        self.stream_type = stream_type
        self.stream_url = stream_url
        self.api_key = api_key
        self.subscription_params = subscription_params or {}
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.buffer_size = buffer_size

        # Connection state
        self.connected = False
        self.reconnect_attempts = 0
        self.last_reconnect_time = 0

        # Message buffer
        self.buffer = asyncio.Queue(maxsize=buffer_size)

        # Callbacks
        self.on_message_callbacks = []
        self.on_connect_callbacks = []
        self.on_disconnect_callbacks = []
        self.on_error_callbacks = []

        # Metrics
        self.metrics = {
            'total_messages': 0,
            'processed_messages': 0,
            'dropped_messages': 0,
            'reconnect_attempts': 0,
            'successful_reconnects': 0,
            'failed_reconnects': 0,
            'connection_uptime': 0,
            'last_message_time': 0,
            'buffer_high_water_mark': 0,
        }

        # Connection objects
        self.websocket = None
        self.http_client = None
        self.task = None

        logger.info(f"Initialized {stream_type.value} stream data ingestor with URL: {stream_url}")

    async def connect(self) -> bool:
        """
        Connect to the stream.

        Returns:
            True if connection was successful, False otherwise
        """
        if self.connected:
            logger.warning("Already connected to stream")
            return True

        logger.info(f"Connecting to {self.stream_type.value} stream at {self.stream_url}")

        try:
            if self.stream_type == StreamType.QUICKNODE_YELLOWSTONE:
                await self._connect_quicknode_yellowstone()
            elif self.stream_type == StreamType.JITO_SHREDSTREAM:
                await self._connect_jito_shredstream()
            elif self.stream_type == StreamType.HELIUS_WEBHOOK:
                await self._connect_helius_webhook()
            elif self.stream_type == StreamType.CUSTOM_WEBSOCKET:
                await self._connect_custom_websocket()
            else:
                logger.error(f"Unsupported stream type: {self.stream_type.value}")
                return False

            self.connected = True
            self.reconnect_attempts = 0
            self.metrics['connection_uptime'] = time.time()

            # Call on_connect callbacks
            for callback in self.on_connect_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Error in on_connect callback: {str(e)}")

            logger.info(f"Connected to {self.stream_type.value} stream")
            return True
        except Exception as e:
            logger.error(f"Error connecting to {self.stream_type.value} stream: {str(e)}")

            # Call on_error callbacks
            for callback in self.on_error_callbacks:
                try:
                    await callback(str(e))
                except Exception as e:
                    logger.error(f"Error in on_error callback: {str(e)}")

            return False

    async def disconnect(self) -> None:
        """Disconnect from the stream."""
        if not self.connected:
            logger.warning("Not connected to stream")
            return

        logger.info(f"Disconnecting from {self.stream_type.value} stream")

        try:
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                self.task = None

            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            if self.http_client:
                await self.http_client.aclose()
                self.http_client = None

            self.connected = False

            # Update metrics
            if self.metrics['connection_uptime'] > 0:
                self.metrics['connection_uptime'] = time.time() - self.metrics['connection_uptime']

            # Call on_disconnect callbacks
            for callback in self.on_disconnect_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Error in on_disconnect callback: {str(e)}")

            logger.info(f"Disconnected from {self.stream_type.value} stream")
        except Exception as e:
            logger.error(f"Error disconnecting from {self.stream_type.value} stream: {str(e)}")

    async def start(self) -> None:
        """Start consuming data from the stream."""
        if not await self.connect():
            logger.error(f"Failed to connect to {self.stream_type.value} stream")
            return

        logger.info(f"Starting to consume data from {self.stream_type.value} stream")

        # Start the consumer task
        self.task = asyncio.create_task(self._consume())

    async def stop(self) -> None:
        """Stop consuming data from the stream."""
        await self.disconnect()

    async def get_message(self) -> Optional[Dict[str, Any]]:
        """
        Get a message from the buffer.

        Returns:
            Message from the buffer, or None if the buffer is empty
        """
        try:
            return await self.buffer.get()
        except Exception as e:
            logger.error(f"Error getting message from buffer: {str(e)}")
            return None

    def on_message(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Register a callback for when a message is received.

        Args:
            callback: Callback function that takes a message and returns None
        """
        self.on_message_callbacks.append(callback)

    def on_connect(self, callback: Callable[[], Awaitable[None]]) -> None:
        """
        Register a callback for when a connection is established.

        Args:
            callback: Callback function that takes no arguments and returns None
        """
        self.on_connect_callbacks.append(callback)

    def on_disconnect(self, callback: Callable[[], Awaitable[None]]) -> None:
        """
        Register a callback for when a connection is closed.

        Args:
            callback: Callback function that takes no arguments and returns None
        """
        self.on_disconnect_callbacks.append(callback)

    def on_error(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """
        Register a callback for when an error occurs.

        Args:
            callback: Callback function that takes an error message and returns None
        """
        self.on_error_callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the stream.

        Returns:
            Dictionary containing metrics
        """
        # Update buffer high water mark
        self.metrics['buffer_high_water_mark'] = max(
            self.metrics['buffer_high_water_mark'],
            self.buffer.qsize()
        )

        return self.metrics

    async def _connect_quicknode_yellowstone(self) -> None:
        """Connect to QuickNode Yellowstone gRPC stream."""
        # QuickNode Yellowstone uses WebSocket for the initial connection
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.websocket = await websockets.connect(
            self.stream_url,
            extra_headers=headers
        )

        # Send subscription message
        subscription_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {
                    "mentions": self.subscription_params.get("mentions", []),
                    "commitment": self.subscription_params.get("commitment", "confirmed")
                },
                {
                    "commitment": self.subscription_params.get("commitment", "confirmed"),
                    "encoding": self.subscription_params.get("encoding", "json")
                }
            ]
        }

        await self.websocket.send(json.dumps(subscription_message))

        # Wait for subscription confirmation
        response = await self.websocket.recv()
        response_data = json.loads(response)

        if "error" in response_data:
            raise Exception(f"Error subscribing to QuickNode Yellowstone: {response_data['error']}")

        logger.info(f"Subscribed to QuickNode Yellowstone with subscription ID: {response_data.get('result')}")

    async def _connect_jito_shredstream(self) -> None:
        """Connect to Jito ShredStream."""
        # Jito ShredStream uses WebSocket
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.websocket = await websockets.connect(
            self.stream_url,
            extra_headers=headers
        )

        # Send subscription message
        subscription_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "subscribe",
            "params": self.subscription_params.get("params", [])
        }

        await self.websocket.send(json.dumps(subscription_message))

        # Wait for subscription confirmation
        response = await self.websocket.recv()
        response_data = json.loads(response)

        if "error" in response_data:
            raise Exception(f"Error subscribing to Jito ShredStream: {response_data['error']}")

        logger.info(f"Subscribed to Jito ShredStream with subscription ID: {response_data.get('result')}")

    async def _connect_helius_webhook(self) -> None:
        """Connect to Helius webhook."""
        # Helius webhooks are HTTP-based, so we create an HTTP client
        self.http_client = httpx.AsyncClient()

        # For Helius webhooks, we don't need to establish a persistent connection
        # Instead, we'll poll the webhook URL periodically
        logger.info("Helius webhook connection established (HTTP client created)")

    async def _connect_custom_websocket(self) -> None:
        """Connect to a custom WebSocket."""
        # Custom WebSocket connection
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.websocket = await websockets.connect(
            self.stream_url,
            extra_headers=headers
        )

        # Send subscription message if provided
        if "subscription_message" in self.subscription_params:
            subscription_message = self.subscription_params["subscription_message"]
            await self.websocket.send(json.dumps(subscription_message))

            # Wait for subscription confirmation if expected
            if self.subscription_params.get("expect_confirmation", False):
                response = await self.websocket.recv()
                response_data = json.loads(response)

                if "error" in response_data:
                    raise Exception(f"Error subscribing to custom WebSocket: {response_data['error']}")

                logger.info(f"Subscribed to custom WebSocket with response: {response_data}")

        logger.info("Custom WebSocket connection established")

    async def _consume(self) -> None:
        """Consume data from the stream."""
        while self.connected:
            try:
                if self.stream_type in [StreamType.QUICKNODE_YELLOWSTONE, StreamType.JITO_SHREDSTREAM, StreamType.CUSTOM_WEBSOCKET]:
                    await self._consume_websocket()
                elif self.stream_type == StreamType.HELIUS_WEBHOOK:
                    await self._consume_helius_webhook()
                else:
                    logger.error(f"Unsupported stream type for consumption: {self.stream_type.value}")
                    break
            except Exception as e:
                logger.error(f"Error consuming data from {self.stream_type.value} stream: {str(e)}")

                # Call on_error callbacks
                for callback in self.on_error_callbacks:
                    try:
                        await callback(str(e))
                    except Exception as e:
                        logger.error(f"Error in on_error callback: {str(e)}")

                # Try to reconnect
                if await self._reconnect():
                    logger.info(f"Reconnected to {self.stream_type.value} stream")
                else:
                    logger.error(f"Failed to reconnect to {self.stream_type.value} stream")
                    break

    async def _consume_websocket(self) -> None:
        """Consume data from a WebSocket stream."""
        if not self.websocket:
            raise Exception("WebSocket not connected")

        try:
            async for message in self.websocket:
                # Parse the message
                try:
                    message_data = json.loads(message)
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON message: {message[:100]}...")
                    continue

                # Update metrics
                self.metrics['total_messages'] += 1
                self.metrics['last_message_time'] = time.time()

                # Process the message
                await self._process_message(message_data)
        except ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {str(e)}")
            self.connected = False
            raise

    async def _consume_helius_webhook(self) -> None:
        """Consume data from a Helius webhook."""
        if not self.http_client:
            raise Exception("HTTP client not created")

        # For Helius webhooks, we poll the webhook URL periodically
        poll_interval = self.subscription_params.get("poll_interval", 1.0)

        while self.connected:
            try:
                # Poll the webhook URL
                response = await self.http_client.get(
                    self.stream_url,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                )
                response.raise_for_status()

                # Parse the response
                try:
                    message_data = response.json()
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON response: {response.text[:100]}...")
                    await asyncio.sleep(poll_interval)
                    continue

                # Update metrics
                self.metrics['total_messages'] += 1
                self.metrics['last_message_time'] = time.time()

                # Process the message
                await self._process_message(message_data)

                # Wait for the next poll
                await asyncio.sleep(poll_interval)
            except httpx.HTTPError as e:
                logger.warning(f"HTTP error polling Helius webhook: {str(e)}")
                await asyncio.sleep(poll_interval)

    async def _process_message(self, message: Dict[str, Any]) -> None:
        """
        Process a message from the stream.

        Args:
            message: Message to process
        """
        # Add the message to the buffer
        try:
            # Use put_nowait to avoid blocking if the buffer is full
            self.buffer.put_nowait(message)
            self.metrics['processed_messages'] += 1
        except asyncio.QueueFull:
            logger.warning("Message buffer full, dropping message")
            self.metrics['dropped_messages'] += 1

        # Call on_message callbacks
        for callback in self.on_message_callbacks:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error in on_message callback: {str(e)}")

    async def _reconnect(self) -> bool:
        """
        Reconnect to the stream.

        Returns:
            True if reconnection was successful, False otherwise
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Maximum reconnect attempts ({self.max_reconnect_attempts}) reached")
            return False

        self.reconnect_attempts += 1
        self.metrics['reconnect_attempts'] += 1
        self.last_reconnect_time = time.time()

        # Exponential backoff
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))
        logger.info(f"Reconnecting to {self.stream_type.value} stream in {delay:.2f} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")

        await asyncio.sleep(delay)

        # Disconnect first to clean up any existing connections
        await self.disconnect()

        # Try to connect again
        if await self.connect():
            self.metrics['successful_reconnects'] += 1
            return True
        else:
            self.metrics['failed_reconnects'] += 1
            return False
