#!/usr/bin/env python3
"""
Jito Client Module

This module provides a client for interacting with Jito Labs' services,
including transaction submission with MEV protection and ShredStream access.
Enhanced with circuit breaker and rate limiting capabilities.
"""

import os
import json
import logging
import base64
import time
import asyncio
import random
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import httpx
import websockets
from pathlib import Path

# Import circuit breaker and retry utilities
try:
    from shared.utils.api_helpers import CircuitBreaker, retry_with_backoff, retry_policy
except ImportError:
    # Try to import from the new centralized config loader
    try:
        from shared.utils.config_loader import get_config_loader
        # Get configuration for circuit breaker and retry policy
        config_loader = get_config_loader()
        config = config_loader.load_config(environment="production")
        circuit_breaker_config = config.get("deployment", {}).get("circuit_breaker", {})
        retry_policy_config = config.get("deployment", {}).get("retry_policy", {})
    except ImportError:
        # Use default values if config loader is not available
        circuit_breaker_config = {
            "enabled": True,
            "failure_threshold": 5,
            "reset_timeout_seconds": 300
        }
        retry_policy_config = {
            "max_retries": 3,
            "backoff_factor": 2,
            "max_backoff_seconds": 30
        }

    # Define circuit breaker class if not available
    class CircuitBreaker:
        """Circuit breaker pattern implementation."""

        def __init__(self, name: str, failure_threshold: int = 5,
                    reset_timeout: int = 300):
            self.name = name
            self.failure_threshold = failure_threshold
            self.reset_timeout = reset_timeout
            self.state = "CLOSED"
            self.failure_count = 0
            self.last_failure_time = 0

        async def call(self, func: Callable, *args, **kwargs):
            """Call a function with circuit breaker protection."""
            if self.state == "OPEN":
                current_time = time.time()
                if current_time - self.last_failure_time > self.reset_timeout:
                    self.state = "HALF-OPEN"
                else:
                    raise Exception(f"Circuit {self.name} is OPEN")

            try:
                result = await func(*args, **kwargs)

                if self.state == "HALF-OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0

                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                elif self.state == "HALF-OPEN":
                    self.state = "OPEN"

                raise e

    # Define retry_with_backoff function if not available
    async def retry_with_backoff(func: Callable, max_retries: int = 3,
                               base_delay: float = 1.0, max_delay: float = 30.0,
                               jitter: float = 0.1):
        """Retry a function with exponential backoff."""
        retries = 0
        last_exception = None

        while retries <= max_retries:
            try:
                return await func()
            except Exception as e:
                last_exception = e
                retries += 1

                if retries > max_retries:
                    raise last_exception

                delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                delay = delay * (1 + random.uniform(-jitter, jitter))

                await asyncio.sleep(delay)

        raise last_exception if last_exception else Exception("Unknown error in retry_with_backoff")

    # Define retry_policy decorator if not available
    def retry_policy(max_retries: int = 3, base_delay: float = 1.0,
                    max_delay: float = 30.0, jitter: float = 0.1):
        """Decorator for retrying a function with exponential backoff."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                async def func_wrapper():
                    return await func(*args, **kwargs)

                return await retry_with_backoff(
                    func_wrapper,
                    max_retries=max_retries,
                    base_delay=base_delay,
                    max_delay=max_delay,
                    jitter=jitter
                )

            return wrapper

        return decorator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'output', 'jito_client_log.txt'
        )),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('jito_client')

class JitoClient:
    """
    Enhanced client for interacting with Jito Labs' services.

    This client includes circuit breaker and rate limiting capabilities
    to prevent API outages from affecting the system.
    """

    def __init__(self,
                 rpc_url: str = "https://mainnet.block.jito.io",
                 fallback_rpc_url: str = None,  # No public RPC fallback
                 auth_keypair_path: Optional[str] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 30.0):
        """
        Initialize the JitoClient.

        Args:
            rpc_url: Jito RPC URL for transaction submission
            fallback_rpc_url: Fallback RPC URL if Jito fails
            auth_keypair_path: Path to the Ed25519 keypair for authentication
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
            timeout: Timeout for HTTP requests in seconds
        """
        self.rpc_url = rpc_url
        self.fallback_rpc_url = fallback_rpc_url
        self.auth_keypair_path = auth_keypair_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(timeout=timeout)

        # Load authentication keypair if provided
        self.auth_keypair = self._load_auth_keypair() if auth_keypair_path else None

        # Initialize circuit breaker
        circuit_breaker_config = {}
        if hasattr(self, 'config') and self.config:
            circuit_breaker_config = self.config.get("circuit_breaker", {})

        self.circuit_breaker = CircuitBreaker(
            "jito_api",
            failure_threshold=circuit_breaker_config.get("failure_threshold", 5),
            reset_timeout=circuit_breaker_config.get("reset_timeout_seconds", 300)
        )

        # Initialize fallback circuit breaker
        self.fallback_circuit_breaker = CircuitBreaker(
            "fallback_rpc",
            failure_threshold=circuit_breaker_config.get("failure_threshold", 5),
            reset_timeout=circuit_breaker_config.get("reset_timeout_seconds", 300)
        )

        # Initialize rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms minimum between requests

        # Metrics for monitoring
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'fallback_requests': 0,
            'avg_response_time': 0,
            'last_request_time': 0,
            'circuit_breaker_state': 'CLOSED'
        }

        logger.info("Initialized Jito client with enhanced circuit breaker and rate limiting")

    def _load_auth_keypair(self) -> Dict[str, Any]:
        """
        Load the authentication keypair from file.

        Returns:
            Dict containing the keypair data
        """
        try:
            with open(self.auth_keypair_path, 'r') as f:
                keypair_data = json.load(f)
            logger.info(f"Loaded authentication keypair from {self.auth_keypair_path}")
            return keypair_data
        except Exception as e:
            logger.error(f"Failed to load authentication keypair: {str(e)}")
            raise

    async def _sign_challenge(self, challenge: str) -> str:
        """
        Sign a challenge for authentication.

        Args:
            challenge: Challenge string to sign

        Returns:
            Base64-encoded signature
        """
        # This is a placeholder for actual Ed25519 signing
        # In a real implementation, you would use the keypair to sign the challenge

        # For now, we'll just return a dummy signature
        return "dummy_signature"

    async def _authenticate(self) -> Optional[str]:
        """
        Authenticate with Jito services.

        Returns:
            Authentication token if successful, None otherwise
        """
        if not self.auth_keypair:
            logger.warning("No authentication keypair provided, skipping authentication")
            return None

        try:
            # FIXED: Construct correct Jito auth endpoints
            base_url = self.rpc_url.rstrip('/')
            challenge_url = f"{base_url}/auth/challenge"
            auth_url = f"{base_url}/auth/token"

            # Get challenge
            response = await self.http_client.get(challenge_url)
            response.raise_for_status()
            challenge_data = response.json()

            if 'challenge' not in challenge_data:
                logger.error("Invalid challenge response")
                return None

            # Sign challenge
            signature = await self._sign_challenge(challenge_data['challenge'])

            # Submit signature
            auth_response = await self.http_client.post(
                auth_url,
                json={
                    'challenge': challenge_data['challenge'],
                    'signature': signature
                }
            )
            auth_response.raise_for_status()
            auth_data = auth_response.json()

            if 'token' not in auth_data:
                logger.error("Invalid authentication response")
                return None

            logger.info("Successfully authenticated with Jito services")
            return auth_data['token']
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    async def _rate_limited_call(self, func, *args, **kwargs):
        """
        Call a function with rate limiting.

        Args:
            func: Function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the function call
        """
        # Apply rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)

        self.last_request_time = time.time()

        # Call the function with circuit breaker and retry
        retry_policy_config = {}
        if hasattr(self, 'config') and self.config:
            retry_policy_config = self.config.get("retry_policy", {})

        return await self.circuit_breaker.call(
            retry_with_backoff,
            lambda: func(*args, **kwargs),
            max_retries=retry_policy_config.get("max_retries", 3),
            base_delay=retry_policy_config.get("backoff_factor", 2),
            max_delay=retry_policy_config.get("max_backoff_seconds", 30),
            jitter=0.1
        )

    async def send_transaction(self,
                              signed_tx: Union[bytes, str],
                              opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a transaction using Jito RPC with enhanced circuit breaker and rate limiting.

        Args:
            signed_tx: Signed transaction as bytes or base64 string
            opts: Optional transaction options

        Returns:
            Dict containing the response data
        """
        # Update metrics
        self.metrics['total_requests'] += 1
        start_time = time.time()

        # FIXED: Ensure transaction is properly base64 encoded with validation
        if isinstance(signed_tx, bytes):
            try:
                # Validate that the bytes are not empty
                if len(signed_tx) == 0:
                    logger.error("Empty transaction bytes provided")
                    return {
                        'success': False,
                        'error': 'Empty transaction bytes',
                        'provider': None
                    }

                # Encode to base64 and validate
                encoded_tx = base64.b64encode(signed_tx).decode('utf-8')

                # Validate the encoding by attempting to decode it back
                base64.b64decode(encoded_tx, validate=True)
                logger.debug(f"Transaction encoded to base64: {len(encoded_tx)} chars")

            except Exception as e:
                logger.error(f"Failed to encode transaction to base64: {e}")
                return {
                    'success': False,
                    'error': f'Base64 encoding failed: {str(e)}',
                    'provider': None
                }
        else:
            # Validate existing base64 string
            try:
                encoded_tx = signed_tx.strip()

                # Ensure proper base64 padding
                missing_padding = len(encoded_tx) % 4
                if missing_padding:
                    encoded_tx += '=' * (4 - missing_padding)

                # Validate the base64 string
                base64.b64decode(encoded_tx, validate=True)
                logger.debug(f"Validated existing base64 transaction: {len(encoded_tx)} chars")

            except Exception as e:
                logger.error(f"Invalid base64 transaction string: {e}")
                return {
                    'success': False,
                    'error': f'Invalid base64 transaction: {str(e)}',
                    'provider': None
                }

        # Prepare request payload
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                encoded_tx,
                {
                    "encoding": "base64",
                    "skipPreflight": opts.get('skip_preflight', False) if opts else False,
                    "maxRetries": opts.get('max_retries', 0) if opts else 0
                }
            ]
        }

        # Add tip if provided
        if opts and 'tip' in opts:
            payload['params'][1]['tip'] = opts['tip']

        # Update circuit breaker status in metrics
        self.metrics['circuit_breaker_state'] = self.circuit_breaker.state

        # Define the primary request function
        async def make_jito_request():
            # Get authentication token if needed
            auth_token = await self._authenticate() if self.auth_keypair else None

            # Prepare headers
            headers = {}
            if auth_token:
                headers['Authorization'] = f"Bearer {auth_token}"

            # FIXED: Use standard Solana RPC endpoint for Jito
            # Jito uses standard Solana RPC format, not custom API endpoints

            # Send request to standard RPC endpoint
            response = await self.http_client.post(
                self.rpc_url,  # Use standard RPC URL
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()

            if 'result' not in result:
                raise Exception(f"Jito RPC error: {result.get('error')}")

            return result

        try:
            # Try to send via Jito with circuit breaker and rate limiting
            result = await self._rate_limited_call(make_jito_request)

            # Update metrics
            self.metrics['successful_requests'] += 1
            self.metrics['last_request_time'] = time.time() - start_time
            self.metrics['avg_response_time'] = (
                (self.metrics['avg_response_time'] * (self.metrics['successful_requests'] - 1)) +
                self.metrics['last_request_time']
            ) / self.metrics['successful_requests']

            logger.info(f"Transaction sent successfully via Jito: {result['result']}")
            return {
                'success': True,
                'signature': result['result'],
                'provider': 'jito',
                'response_time': self.metrics['last_request_time']
            }
        except Exception as e:
            logger.error(f"Error sending transaction via Jito: {str(e)}")

            # Update metrics
            self.metrics['failed_requests'] += 1

            # Try fallback RPC if available
            if self.fallback_rpc_url:
                logger.info("Trying fallback RPC...")

                # Define the fallback request function
                async def make_fallback_request():
                    response = await self.http_client.post(
                        self.fallback_rpc_url,
                        json=payload
                    )
                    response.raise_for_status()
                    result = response.json()

                    if 'result' not in result:
                        raise Exception(f"Fallback RPC error: {result.get('error')}")

                    return result

                try:
                    # Get retry policy config
                    retry_policy_config = {}
                    if hasattr(self, 'config') and self.config:
                        retry_policy_config = self.config.get("retry_policy", {})

                    # Try to send via fallback RPC with circuit breaker and rate limiting
                    result = await self.fallback_circuit_breaker.call(
                        retry_with_backoff,
                        make_fallback_request,
                        max_retries=retry_policy_config.get("max_retries", 3),
                        base_delay=retry_policy_config.get("backoff_factor", 2),
                        max_delay=retry_policy_config.get("max_backoff_seconds", 30),
                        jitter=0.1
                    )

                    # Update metrics
                    self.metrics['fallback_requests'] += 1
                    self.metrics['last_request_time'] = time.time() - start_time

                    logger.info(f"Transaction sent successfully via fallback RPC: {result['result']}")
                    return {
                        'success': True,
                        'signature': result['result'],
                        'provider': 'fallback',
                        'response_time': self.metrics['last_request_time']
                    }
                except Exception as fallback_error:
                    logger.error(f"Error sending transaction via fallback RPC: {str(fallback_error)}")

            logger.error("Failed to send transaction after all attempts")
            return {
                'success': False,
                'error': str(e),
                'provider': None,
                'response_time': time.time() - start_time
            }

    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        """
        Get the status of a transaction with enhanced circuit breaker and rate limiting.

        Args:
            signature: Transaction signature

        Returns:
            Dict containing the transaction status
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {
                    "encoding": "json",
                    "commitment": "confirmed"
                }
            ]
        }

        # Define the primary request function
        async def make_jito_request():
            response = await self.http_client.post(
                self.rpc_url,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if 'result' not in result:
                raise Exception(f"Jito RPC error: {result.get('error')}")

            return result

        try:
            # Try to get transaction status via Jito with circuit breaker and rate limiting
            result = await self._rate_limited_call(make_jito_request)

            return {
                'success': True,
                'status': result['result'],
                'provider': 'jito'
            }
        except Exception as e:
            logger.warning(f"Failed to get transaction status via Jito: {str(e)}")

            # Try fallback RPC if available
            if self.fallback_rpc_url:
                # Define the fallback request function
                async def make_fallback_request():
                    response = await self.http_client.post(
                        self.fallback_rpc_url,
                        json=payload
                    )
                    response.raise_for_status()
                    result = response.json()

                    if 'result' not in result:
                        raise Exception(f"Fallback RPC error: {result.get('error')}")

                    return result

                try:
                    # Get retry policy config
                    retry_policy_config = {}
                    if hasattr(self, 'config') and self.config:
                        retry_policy_config = self.config.get("retry_policy", {})

                    # Try to get transaction status via fallback RPC with circuit breaker and rate limiting
                    result = await self.fallback_circuit_breaker.call(
                        retry_with_backoff,
                        make_fallback_request,
                        max_retries=retry_policy_config.get("max_retries", 3),
                        base_delay=retry_policy_config.get("backoff_factor", 2),
                        max_delay=retry_policy_config.get("max_backoff_seconds", 30),
                        jitter=0.1
                    )

                    return {
                        'success': True,
                        'status': result['result'],
                        'provider': 'fallback'
                    }
                except Exception as fallback_error:
                    logger.error(f"Error getting transaction status via fallback RPC: {str(fallback_error)}")

            return {
                'success': False,
                'error': str(e),
                'provider': None
            }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics including circuit breaker status.

        Returns:
            Dict containing client metrics
        """
        # Update circuit breaker state in metrics
        self.metrics['circuit_breaker_state'] = self.circuit_breaker.state

        # Add circuit breaker details
        self.metrics['circuit_breaker'] = {
            'state': self.circuit_breaker.state,
            'failure_count': self.circuit_breaker.failure_count,
            'last_failure_time': self.circuit_breaker.last_failure_time,
            'failure_threshold': self.circuit_breaker.failure_threshold,
            'reset_timeout': self.circuit_breaker.reset_timeout
        }

        # Add fallback circuit breaker details
        self.metrics['fallback_circuit_breaker'] = {
            'state': self.fallback_circuit_breaker.state,
            'failure_count': self.fallback_circuit_breaker.failure_count,
            'last_failure_time': self.fallback_circuit_breaker.last_failure_time,
            'failure_threshold': self.fallback_circuit_breaker.failure_threshold,
            'reset_timeout': self.fallback_circuit_breaker.reset_timeout
        }

        return self.metrics

    async def close(self):
        """Close the HTTP client session."""
        await self.http_client.aclose()

    async def connect_to_shredstream(self,
                                    url: str = None,
                                    callback: Callable = None,
                                    max_reconnects: int = 10,
                                    reconnect_delay: float = 5.0) -> None:
        """
        Connect to Jito's ShredStream service.

        Args:
            url: ShredStream WebSocket URL
            callback: Callback function for processing shreds
            max_reconnects: Maximum number of reconnection attempts
            reconnect_delay: Delay between reconnection attempts in seconds
        """
        if not self.auth_keypair:
            logger.error("Authentication keypair is required for ShredStream")
            return

        # Use default URL if not provided
        if url is None:
            url = "wss://shredstream.jito.wtf/stream"

        # Get public key from keypair
        public_key = self.auth_keypair.get('public_key')
        private_key = self.auth_keypair.get('private_key')

        if not public_key or not private_key:
            logger.error("Invalid keypair: missing public_key or private_key")
            return

        logger.info(f"Connecting to ShredStream at {url} with public key {public_key}")

        # Prepare headers for authentication
        headers = {
            "X-Jito-Key": public_key
        }

        # Connect with retries
        for attempt in range(max_reconnects):
            try:
                async with websockets.connect(url, extra_headers=headers) as websocket:
                    logger.info("Connected to ShredStream")

                    # Subscribe to shreds
                    subscribe_msg = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "subscribeShreds",
                        "params": []
                    }

                    await websocket.send(json.dumps(subscribe_msg))
                    logger.info("Sent subscription request")

                    # Wait for subscription confirmation
                    response = await websocket.recv()
                    response_data = json.loads(response)

                    if 'result' in response_data:
                        logger.info(f"Subscription successful: {response_data['result']}")
                    else:
                        logger.error(f"Subscription failed: {response_data.get('error')}")
                        break

                    # Process incoming shreds
                    while True:
                        try:
                            shred = await websocket.recv()
                            shred_data = json.loads(shred)

                            # Call callback if provided
                            if callback:
                                await callback(shred_data)

                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("ShredStream connection closed")
                            break

            except Exception as e:
                logger.error(f"Error connecting to ShredStream (attempt {attempt+1}/{max_reconnects}): {str(e)}")

                if attempt < max_reconnects - 1:
                    logger.info(f"Reconnecting in {reconnect_delay} seconds...")
                    await asyncio.sleep(reconnect_delay)
                else:
                    logger.error("Max reconnection attempts reached")
                    break

async def main():
    """Main function to demonstrate the client."""
    # Example usage
    client = JitoClient(
        auth_keypair_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'keys', 'jito_shredstream_keypair.json'
        )
    )

    # Example transaction (this is just a placeholder)
    example_tx = base64.b64encode(b"example_transaction").decode('utf-8')

    # Send transaction
    result = await client.send_transaction(example_tx)
    print(f"Transaction result: {result}")

    # Get metrics
    metrics = client.get_metrics()
    print(f"Client metrics: {metrics}")

    # Define a callback for ShredStream
    async def shred_callback(shred_data):
        print(f"Received shred: {shred_data}")

    # Test ShredStream connection if keypair is available
    if client.auth_keypair:
        print("Testing ShredStream connection...")
        try:
            # Set a timeout for the test
            shredstream_task = asyncio.create_task(
                client.connect_to_shredstream(callback=shred_callback, max_reconnects=1)
            )

            # Wait for 30 seconds or until the task completes
            try:
                await asyncio.wait_for(shredstream_task, timeout=30)
            except asyncio.TimeoutError:
                print("ShredStream test completed (timeout)")
        except Exception as e:
            print(f"ShredStream test error: {str(e)}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
