"""
Enhanced API Manager for Synergy7 System.

This module provides an enhanced API manager with improved fallback mechanisms,
circuit breakers, and metrics tracking.
"""

import os
import time
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum

import httpx

# Configure logging
logger = logging.getLogger(__name__)

class APIProviderStatus(Enum):
    """API provider status."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class APIProvider:
    """API provider configuration."""
    
    def __init__(self, name: str, base_url: str, api_key: str = "", priority: int = 1):
        """
        Initialize API provider.
        
        Args:
            name: Provider name
            base_url: Base URL
            api_key: API key
            priority: Priority (lower is higher priority)
        """
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.priority = priority
        self.status = APIProviderStatus.AVAILABLE
        self.last_check = time.time()
        self.success_count = 0
        self.failure_count = 0
        self.last_success = 0
        self.last_failure = 0
        self.error_window = []
        self.error_window_size = 10
        self.error_threshold = 0.5  # 50% error rate
        
    def update_status(self, success: bool) -> None:
        """
        Update provider status based on success/failure.
        
        Args:
            success: Whether the API call was successful
        """
        current_time = time.time()
        
        # Update counters
        if success:
            self.success_count += 1
            self.last_success = current_time
        else:
            self.failure_count += 1
            self.last_failure = current_time
        
        # Update error window
        self.error_window.append(0 if success else 1)
        if len(self.error_window) > self.error_window_size:
            self.error_window.pop(0)
        
        # Calculate error rate
        error_rate = sum(self.error_window) / len(self.error_window) if self.error_window else 0
        
        # Update status
        if error_rate >= self.error_threshold:
            self.status = APIProviderStatus.DEGRADED
            if error_rate >= 0.8:  # 80% error rate
                self.status = APIProviderStatus.UNAVAILABLE
        else:
            self.status = APIProviderStatus.AVAILABLE
        
        self.last_check = current_time


class APICache:
    """Cache for API responses."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize API cache.
        
        Args:
            max_size: Maximum cache size
        """
        self.cache = {}
        self.expiry = {}
        self.max_size = max_size
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key in self.cache and time.time() < self.expiry.get(key, 0):
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        # Check if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.expiry.keys(), key=lambda k: self.expiry[k])
            self.cache.pop(oldest_key, None)
            self.expiry.pop(oldest_key, None)
        
        self.cache[key] = value
        self.expiry[key] = time.time() + ttl


class EnhancedAPIManager:
    """Enhanced API manager with improved fallback mechanisms."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'EnhancedAPIManager':
        """
        Get singleton instance of EnhancedAPIManager.
        
        Returns:
            EnhancedAPIManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the API manager."""
        self.providers = {}
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.cache = APICache()
        self.metrics = {
            "calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "successes": 0,
            "failures": 0,
            "fallbacks": 0
        }
        self.initialized = False
        
    async def initialize(self) -> None:
        """Initialize API providers."""
        if self.initialized:
            return
        
        # Initialize Birdeye API providers
        self.providers["birdeye"] = []
        
        # Primary Birdeye API
        birdeye_api_key = os.environ.get("BIRDEYE_API_KEY", "a2679724762a47b58dde41b20fb55ce9")
        self.providers["birdeye"].append(
            APIProvider(
                name="birdeye_primary",
                base_url="https://public-api.birdeye.so",
                api_key=birdeye_api_key,
                priority=1
            )
        )
        
        # Initialize Solana RPC providers
        self.providers["solana_rpc"] = []
        
        # Primary Solana RPC provider (Helius)
        helius_api_key = os.environ.get("HELIUS_API_KEY", "dda9f776-9a40-447d-9ca4-22a27c21169e")
        helius_rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_api_key}"
        self.providers["solana_rpc"].append(
            APIProvider(
                name="helius",
                base_url=helius_rpc_url,
                api_key=helius_api_key,
                priority=1
            )
        )
        
        # Fallback Solana RPC provider (QuickNode)
        quicknode_api_key = os.environ.get("QUICKNODE_API_KEY", "QN_6bc9e73d888f418682d564eb13db68a8")
        quicknode_rpc_url = f"https://solana-mainnet.g.alchemy.com/v2/{quicknode_api_key}"
        self.providers["solana_rpc"].append(
            APIProvider(
                name="quicknode",
                base_url=quicknode_rpc_url,
                api_key=quicknode_api_key,
                priority=2
            )
        )
        
        # Initialize Jupiter API providers
        self.providers["jupiter"] = []
        
        # Jupiter API (no key required)
        self.providers["jupiter"].append(
            APIProvider(
                name="jupiter",
                base_url="https://quote-api.jup.ag/v6",
                priority=1
            )
        )
        
        self.initialized = True
    
    def add_provider(self, api_type: str, provider: APIProvider) -> None:
        """
        Add an API provider.
        
        Args:
            api_type: API type (e.g., "birdeye", "solana_rpc")
            provider: API provider
        """
        if api_type not in self.providers:
            self.providers[api_type] = []
        
        self.providers[api_type].append(provider)
        
        # Sort providers by priority
        self.providers[api_type].sort(key=lambda p: p.priority)
    
    async def get_provider(self, api_type: str) -> Optional[APIProvider]:
        """
        Get the best available provider for an API type.
        
        Args:
            api_type: API type
            
        Returns:
            Best available provider or None if none available
        """
        if not self.initialized:
            await self.initialize()
        
        if api_type not in self.providers:
            logger.error(f"No providers for API type: {api_type}")
            return None
        
        # Find the best available provider
        for provider in self.providers[api_type]:
            if provider.status != APIProviderStatus.UNAVAILABLE:
                return provider
        
        # If we get here, all providers are unavailable
        logger.error(f"All providers for API type {api_type} are unavailable")
        
        # Return the first provider as a last resort
        if self.providers[api_type]:
            logger.warning(f"Using unavailable provider for {api_type} as last resort")
            return self.providers[api_type][0]
        
        return None
    
    async def call_api(self, api_type: str, endpoint: str, method: str = "GET", 
                      params: Dict[str, Any] = None, data: Dict[str, Any] = None,
                      headers: Dict[str, str] = None, cache_key: str = None,
                      cache_ttl: int = 60, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """
        Call an API with automatic fallback and caching.
        
        Args:
            api_type: Type of API (e.g., "birdeye", "solana_rpc")
            endpoint: API endpoint (e.g., "/addresses/{address}/balances")
            method: HTTP method (e.g., "GET", "POST")
            params: Query parameters
            data: Request body
            headers: Additional headers
            cache_key: Cache key (if None, no caching is used)
            cache_ttl: Cache TTL in seconds
            retry_count: Current retry count (for internal use)
            
        Returns:
            API response or None if all providers failed
        """
        if not self.initialized:
            await self.initialize()
        
        # Update metrics
        self.metrics["calls"] += 1
        
        # Check cache
        if cache_key:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                self.metrics["cache_hits"] += 1
                return cached_result
            self.metrics["cache_misses"] += 1
        
        # Get provider
        provider = await self.get_provider(api_type)
        if not provider:
            return None
        
        # Prepare headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Add API key header if needed
        if provider.api_key:
            if api_type == "birdeye":
                request_headers["X-API-KEY"] = provider.api_key
        
        # Prepare URL
        url = f"{provider.base_url}{endpoint}"
        
        try:
            # Make the request
            if method.upper() == "GET":
                response = await self.http_client.get(url, params=params, headers=request_headers)
            elif method.upper() == "POST":
                response = await self.http_client.post(url, params=params, json=data, headers=request_headers)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Check response
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Update provider status
            provider.update_status(True)
            
            # Update metrics
            self.metrics["successes"] += 1
            
            # Cache result
            if cache_key:
                self.cache.set(cache_key, result, cache_ttl)
            
            return result
        except Exception as e:
            logger.error(f"Error calling {api_type} API ({provider.name}): {str(e)}")
            
            # Update provider status
            provider.update_status(False)
            
            # Update metrics
            self.metrics["failures"] += 1
            
            # Try next provider if available
            if retry_count < len(self.providers[api_type]) - 1:
                logger.warning(f"Trying next provider for {api_type}")
                self.metrics["fallbacks"] += 1
                return await self.call_api(
                    api_type=api_type,
                    endpoint=endpoint,
                    method=method,
                    params=params,
                    data=data,
                    headers=headers,
                    cache_key=cache_key,
                    cache_ttl=cache_ttl,
                    retry_count=retry_count + 1
                )
            
            # If we get here, all providers failed
            logger.error(f"All providers for {api_type} failed")
            return None
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.http_client.aclose()


# Convenience function to get the API manager instance
def get_api_manager() -> EnhancedAPIManager:
    """
    Get the API manager instance.
    
    Returns:
        EnhancedAPIManager instance
    """
    return EnhancedAPIManager.get_instance()
