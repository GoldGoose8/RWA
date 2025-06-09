#!/usr/bin/env python3
"""
Helius API Client for Synergy7 Trading System

This module provides a client for interacting with the Helius API with
enhanced circuit breaker and rate limiting capabilities.
"""

import os
import json
import logging
import asyncio
import random
import time
from typing import Dict, List, Any, Optional, Union, Callable

# Import API manager
from phase_4_deployment.apis.api_manager import get_api_manager

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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("helius_client")

class HeliusClient:
    """
    Enhanced client for interacting with the Helius API.

    This client includes circuit breaker and rate limiting capabilities
    to prevent API outages from affecting the system.
    """

    def __init__(self, api_key: str = None, rpc_url: str = None, config: Dict[str, Any] = None):
        """
        Initialize the Helius client.

        Args:
            api_key: Helius API key (optional, can be provided in config or environment)
            rpc_url: Helius RPC URL (optional, can be provided in config or environment)
            config: Configuration dictionary
        """
        self.config = config or {}
        self.api_key = api_key or self.config.get("api_key") or os.environ.get("HELIUS_API_KEY")
        self.rpc_url = rpc_url or self.config.get("rpc_url") or os.environ.get("HELIUS_RPC_URL")

        if not self.rpc_url and self.api_key:
            self.rpc_url = f"https://mainnet.helius-rpc.com/?api-key={self.api_key}"

        # Initialize API manager
        self.api_manager = get_api_manager(config)

        # Initialize circuit breaker
        circuit_breaker_config = config.get("circuit_breaker", {}) if config else {}
        self.circuit_breaker = CircuitBreaker(
            "helius_api",
            failure_threshold=circuit_breaker_config.get("failure_threshold", 5),
            reset_timeout=circuit_breaker_config.get("reset_timeout_seconds", 300)
        )

        # Initialize rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms minimum between requests

        logger.info("Initialized Helius client with enhanced circuit breaker and rate limiting")

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

        # Get retry policy config
        retry_policy_config = {}
        if hasattr(self, 'config') and self.config:
            retry_policy_config = self.config.get("retry_policy", {})

        # Call the function with circuit breaker and retry
        return await self.circuit_breaker.call(
            retry_with_backoff,
            lambda: func(*args, **kwargs),
            max_retries=retry_policy_config.get("max_retries", 3),
            base_delay=retry_policy_config.get("backoff_factor", 2),
            max_delay=retry_policy_config.get("max_backoff_seconds", 30),
            jitter=0.1
        )

    async def get_balance(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get the balance of a Solana address.

        Args:
            address: Solana address

        Returns:
            Balance information or None if the call failed
        """
        endpoint = f"/addresses/{address}/balances"
        cache_key = f"helius_balance_{address}"

        async def make_request():
            return await self.api_manager.call_api(
                api_type="helius",
                endpoint=endpoint,
                cache_key=cache_key,
                cache_ttl=60  # Cache for 60 seconds
            )

        try:
            result = await self._rate_limited_call(make_request)
            return result
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {str(e)}")
            return None

    async def get_token_metadata(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a token.

        Args:
            mint_address: Token mint address

        Returns:
            Token metadata or None if the call failed
        """
        endpoint = f"/tokens/metadata"
        params = {"mintAccounts": [mint_address]}
        cache_key = f"helius_token_metadata_{mint_address}"

        async def make_request():
            return await self.api_manager.call_api(
                api_type="helius",
                endpoint=endpoint,
                method="POST",
                data=params,
                cache_key=cache_key,
                cache_ttl=3600  # Cache for 1 hour
            )

        try:
            result = await self._rate_limited_call(make_request)

            if result and "tokens" in result and len(result["tokens"]) > 0:
                return result["tokens"][0]

            return None
        except Exception as e:
            logger.error(f"Error getting token metadata for {mint_address}: {str(e)}")
            return None

    async def get_recent_blockhash(self) -> Optional[str]:
        """
        Get a recent blockhash.

        Returns:
            Recent blockhash or None if the call failed
        """
        endpoint = ""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": [{"commitment": "confirmed"}]
        }

        async def make_request():
            return await self.api_manager.call_api(
                api_type="solana_rpc",
                endpoint=endpoint,
                method="POST",
                data=data
            )

        try:
            result = await self._rate_limited_call(make_request)

            if result and "result" in result and "value" in result["result"] and "blockhash" in result["result"]["value"]:
                return result["result"]["value"]["blockhash"]

            return None
        except Exception as e:
            logger.error(f"Error getting recent blockhash: {str(e)}")
            return None

    async def get_transaction(self, signature: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details.

        Args:
            signature: Transaction signature

        Returns:
            Transaction details or None if the call failed
        """
        endpoint = ""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {"encoding": "json", "maxSupportedTransactionVersion": 0}
            ]
        }

        async def make_request():
            return await self.api_manager.call_api(
                api_type="solana_rpc",
                endpoint=endpoint,
                method="POST",
                data=data
            )

        try:
            result = await self._rate_limited_call(make_request)

            if result and "result" in result:
                return result["result"]

            return None
        except Exception as e:
            logger.error(f"Error getting transaction {signature}: {str(e)}")
            return None

    async def send_transaction(self, transaction: str) -> Optional[str]:
        """
        Send a transaction.

        Args:
            transaction: Base64-encoded transaction

        Returns:
            Transaction signature or None if the call failed
        """
        endpoint = ""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                transaction,
                {"encoding": "base64", "skipPreflight": False, "preflightCommitment": "confirmed"}
            ]
        }

        async def make_request():
            return await self.api_manager.call_api(
                api_type="solana_rpc",
                endpoint=endpoint,
                method="POST",
                data=data
            )

        try:
            result = await self._rate_limited_call(make_request)

            if result and "result" in result:
                return result["result"]

            return None
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            return None

    async def get_account_info(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get account information.

        Args:
            address: Account address

        Returns:
            Account information or None if the call failed
        """
        endpoint = ""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                address,
                {"encoding": "jsonParsed", "commitment": "confirmed"}
            ]
        }

        async def make_request():
            return await self.api_manager.call_api(
                api_type="solana_rpc",
                endpoint=endpoint,
                method="POST",
                data=data
            )

        try:
            result = await self._rate_limited_call(make_request)

            if result and "result" in result and "value" in result["result"]:
                return result["result"]["value"]

            return None
        except Exception as e:
            logger.error(f"Error getting account info for {address}: {str(e)}")
            return None

    async def get_token_accounts(self, owner_address: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get token accounts for an owner.

        Args:
            owner_address: Owner address

        Returns:
            List of token accounts or None if the call failed
        """
        endpoint = ""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                owner_address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"}
            ]
        }

        async def make_request():
            return await self.api_manager.call_api(
                api_type="solana_rpc",
                endpoint=endpoint,
                method="POST",
                data=data,
                cache_key=f"helius_token_accounts_{owner_address}",
                cache_ttl=300  # Cache for 5 minutes
            )

        try:
            result = await self._rate_limited_call(make_request)

            if result and "result" in result and "value" in result["result"]:
                return result["result"]["value"]

            return None
        except Exception as e:
            logger.error(f"Error getting token accounts for {owner_address}: {str(e)}")
            return None

    async def close(self):
        """Close the client and release resources."""
        # Nothing to close in this implementation
        pass

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """
        Get the status of the circuit breaker.

        Returns:
            Dictionary containing circuit breaker status
        """
        return {
            "state": self.circuit_breaker.state,
            "failure_count": self.circuit_breaker.failure_count,
            "last_failure_time": self.circuit_breaker.last_failure_time
        }
