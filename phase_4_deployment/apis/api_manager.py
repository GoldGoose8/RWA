#!/usr/bin/env python3
"""
API Manager for Q5 Trading System

This module provides a centralized API manager that handles API redundancy,
fallbacks, and caching for external API calls.
"""

import os
import json
import time
import logging
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar

# Import API helpers
try:
    from phase_4_deployment.utils.api_helpers_wrapper import CircuitBreaker, APICache, retry_with_backoff
except ImportError:
    # Fallback to local implementations
    import time
    import asyncio
    from typing import Callable, TypeVar

    T = TypeVar('T')

    class CircuitBreaker:
        def __init__(self, name: str, failure_threshold: int = 3, reset_timeout: float = 60.0):
            self.name = name
            self.failure_threshold = failure_threshold
            self.reset_timeout = reset_timeout
            self.failure_count = 0
            self.last_failure_time = 0
            self.state = "CLOSED"

        async def call(self, func: Callable[..., T], *args, **kwargs) -> Optional[T]:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.state = "HALF-OPEN"
                else:
                    return None
            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF-OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                raise

    class APICache:
        def __init__(self):
            self.cache = {}
            self.expiry = {}

        def get(self, key: str):
            if key in self.cache and self.expiry.get(key, 0) > time.time():
                return self.cache[key]
            return None

        def set(self, key: str, value, ttl: int = 60):
            self.cache[key] = value
            self.expiry[key] = time.time() + ttl

    async def retry_with_backoff(func: Callable[..., T], *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs) -> Optional[T]:
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    raise
                await asyncio.sleep(base_delay * (2 ** attempt))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_manager")

# Type variable for generic return type
T = TypeVar('T')

class APIProvider:
    """
    Represents an API provider with its configuration and status.
    """

    def __init__(self, name: str, base_url: str, api_key: str, priority: int = 1):
        """
        Initialize the API provider.

        Args:
            name: Name of the API provider
            base_url: Base URL for API calls
            api_key: API key for authentication
            priority: Priority of this provider (lower is higher priority)
        """
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.priority = priority
        self.circuit_breaker = CircuitBreaker(name)
        self.available = True
        self.last_check = datetime.now()

        logger.info(f"Initialized API provider: {name} with priority {priority}")

    async def is_available(self) -> bool:
        """
        Check if the API provider is available.

        Returns:
            True if available, False otherwise
        """
        # Only check availability if circuit breaker is closed
        if self.circuit_breaker.state == "CLOSED":
            return True

        # If circuit breaker is open, check if it's time to try again
        if self.circuit_breaker.state == "OPEN":
            current_time = time.time()
            if current_time - self.circuit_breaker.last_failure_time > self.circuit_breaker.reset_timeout:
                # Move to HALF-OPEN state
                self.circuit_breaker.state = "HALF-OPEN"
                logger.info(f"Circuit breaker for {self.name} moved to HALF-OPEN state")
                return True
            else:
                return False

        # If circuit breaker is HALF-OPEN, allow the call
        return True

class APIManager:
    """
    Centralized API manager for the Q5 Trading System.

    This class manages API providers, handles fallbacks, and provides
    caching for external API calls.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the API manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.providers: Dict[str, Dict[str, APIProvider]] = {}
        self.cache = APICache()

        # Initialize providers from config
        self._init_providers()

        logger.info("Initialized API manager")

    def _init_providers(self) -> None:
        """Initialize API providers from configuration."""
        # Initialize Helius providers
        self.providers["helius"] = {}

        # Primary Helius provider
        helius_api_key = os.environ.get("HELIUS_API_KEY")
        if helius_api_key:
            self.providers["helius"]["primary"] = APIProvider(
                name="helius_primary",
                base_url="https://api.helius.xyz/v0",
                api_key=helius_api_key,
                priority=1
            )

        # Fallback Helius provider (if configured)
        helius_fallback_api_key = os.environ.get("HELIUS_FALLBACK_API_KEY")
        if helius_fallback_api_key:
            self.providers["helius"]["fallback"] = APIProvider(
                name="helius_fallback",
                base_url="https://api.helius.xyz/v0",
                api_key=helius_fallback_api_key,
                priority=2
            )

        # Initialize Birdeye providers
        self.providers["birdeye"] = {}

        # Primary Birdeye provider
        birdeye_api_key = os.environ.get("BIRDEYE_API_KEY")
        if birdeye_api_key:
            self.providers["birdeye"]["primary"] = APIProvider(
                name="birdeye_primary",
                base_url="https://public-api.birdeye.so",
                api_key=birdeye_api_key,
                priority=1
            )

        # Fallback Birdeye provider (if configured)
        birdeye_fallback_api_key = os.environ.get("BIRDEYE_FALLBACK_API_KEY")
        if birdeye_fallback_api_key:
            self.providers["birdeye"]["fallback"] = APIProvider(
                name="birdeye_fallback",
                base_url="https://public-api.birdeye.so",
                api_key=birdeye_fallback_api_key,
                priority=2
            )

        # Initialize Solana RPC providers
        self.providers["solana_rpc"] = {}

        # Primary Solana RPC provider
        solana_rpc_url = os.environ.get("SOLANA_RPC_URL")
        if solana_rpc_url:
            self.providers["solana_rpc"]["primary"] = APIProvider(
                name="solana_rpc_primary",
                base_url=solana_rpc_url,
                api_key="",
                priority=1
            )

        # Fallback Solana RPC provider
        solana_fallback_rpc_url = os.environ.get("FALLBACK_RPC_URL")
        if solana_fallback_rpc_url:
            self.providers["solana_rpc"]["fallback"] = APIProvider(
                name="solana_rpc_fallback",
                base_url=solana_fallback_rpc_url,
                api_key="",
                priority=2
            )

    async def get_provider(self, api_type: str) -> Optional[APIProvider]:
        """
        Get the best available provider for the given API type.

        Args:
            api_type: Type of API (e.g., "helius", "birdeye", "solana_rpc")

        Returns:
            Best available provider or None if no provider is available
        """
        if api_type not in self.providers:
            logger.error(f"Unknown API type: {api_type}")
            return None

        # Get all providers for this API type
        providers = self.providers[api_type]

        if not providers:
            logger.error(f"No providers configured for API type: {api_type}")
            return None

        # Sort providers by priority
        sorted_providers = sorted(providers.values(), key=lambda p: p.priority)

        # Find the first available provider
        for provider in sorted_providers:
            if await provider.is_available():
                return provider

        # No available provider
        logger.error(f"No available provider for API type: {api_type}")
        return None

    async def call_api(self, api_type: str, endpoint: str, method: str = "GET",
                      params: Dict[str, Any] = None, data: Dict[str, Any] = None,
                      headers: Dict[str, str] = None, cache_key: str = None,
                      cache_ttl: int = 60) -> Optional[Dict[str, Any]]:
        """
        Call an API with automatic fallback, caching, and enhanced rate limiting.

        Args:
            api_type: Type of API (e.g., "helius", "birdeye", "solana_rpc")
            endpoint: API endpoint (e.g., "/addresses/{address}/balances")
            method: HTTP method (e.g., "GET", "POST")
            params: Query parameters
            data: Request body
            headers: Additional headers
            cache_key: Cache key (if None, no caching is used)
            cache_ttl: Cache TTL in seconds

        Returns:
            API response or None if the call failed
        """
        # Check cache first
        if cache_key:
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_response

        # Get provider
        provider = await self.get_provider(api_type)

        if not provider:
            logger.error(f"No available provider for API type: {api_type}")
            return None

        # Prepare headers
        request_headers = headers or {}

        # Add API key header based on API type
        if api_type == "birdeye":
            request_headers["X-API-KEY"] = provider.api_key
        elif api_type == "helius" and not endpoint.endswith(f"?api-key={provider.api_key}"):
            # Add API key as query parameter if not already present
            endpoint = f"{endpoint}{'&' if '?' in endpoint else '?'}api-key={provider.api_key}"

        # Prepare URL
        url = f"{provider.base_url}{endpoint}"

        # 🔧 FIXED: Enhanced API call with rate limiting and authentication
        try:
            async def make_request():
                # 🔧 FIXED: Enhanced rate limiting for Birdeye API
                if api_type == "birdeye":
                    await self._handle_birdeye_rate_limiting()

                async with httpx.AsyncClient(timeout=30.0) as client:
                    if method == "GET":
                        response = await client.get(url, params=params, headers=request_headers)
                    elif method == "POST":
                        response = await client.post(url, params=params, json=data, headers=request_headers)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                    # 🔧 FIXED: Enhanced error handling for rate limiting
                    if response.status_code == 429:  # Rate limited
                        logger.warning(f"Rate limited by {api_type} API, waiting...")
                        await asyncio.sleep(2.0)  # Wait 2 seconds
                        raise Exception("Rate limited - will retry")
                    elif response.status_code == 400 and api_type == "birdeye":
                        logger.warning(f"Birdeye API 400 error, checking authentication...")
                        # Log the response for debugging
                        try:
                            error_data = response.json()
                            logger.error(f"Birdeye API error: {error_data}")
                        except:
                            logger.error(f"Birdeye API error: {response.text}")
                        raise Exception("Birdeye API authentication/request error")

                    response.raise_for_status()
                    return response.json()

            # Use circuit breaker and retry with enhanced backoff
            result = await provider.circuit_breaker.call(
                retry_with_backoff,
                make_request,
                max_retries=5,  # 🔧 FIXED: Increased retries for rate limiting
                base_delay=2.0  # 🔧 FIXED: Longer delay for rate limiting
            )

            # Cache result if needed
            if cache_key and result:
                self.cache.set(cache_key, result, ttl=cache_ttl)

            return result
        except Exception as e:
            logger.error(f"Error calling {api_type} API: {str(e)}")

            # Try fallback provider
            if "fallback" in self.providers[api_type]:
                logger.warning(f"Trying fallback provider for {api_type}")

                # Temporarily remove the primary provider
                primary_provider = self.providers[api_type].pop("primary", None)

                try:
                    # Recursive call with fallback provider
                    result = await self.call_api(
                        api_type=api_type,
                        endpoint=endpoint,
                        method=method,
                        params=params,
                        data=data,
                        headers=headers,
                        cache_key=cache_key,
                        cache_ttl=cache_ttl
                    )

                    return result
                finally:
                    # Restore primary provider
                    if primary_provider:
                        self.providers[api_type]["primary"] = primary_provider

            return None

    async def _handle_birdeye_rate_limiting(self):
        """
        🔧 FIXED: Handle Birdeye API rate limiting with intelligent delays.
        """
        current_time = time.time()

        # Check if we need to wait between Birdeye calls
        if hasattr(self, '_last_birdeye_call'):
            time_since_last_call = current_time - self._last_birdeye_call
            min_interval = 0.5  # 500ms between calls to avoid rate limiting

            if time_since_last_call < min_interval:
                wait_time = min_interval - time_since_last_call
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before Birdeye call")
                await asyncio.sleep(wait_time)

        # Update last call time
        self._last_birdeye_call = time.time()

# Global API manager instance
_api_manager = None

def get_api_manager(config: Dict[str, Any] = None) -> APIManager:
    """
    Get the global API manager instance.

    Args:
        config: Configuration dictionary

    Returns:
        APIManager instance
    """
    global _api_manager
    if _api_manager is None:
        _api_manager = APIManager(config)

    return _api_manager
