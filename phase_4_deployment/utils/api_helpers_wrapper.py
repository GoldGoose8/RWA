#!/usr/bin/env python3
"""
API Helpers Wrapper

This module provides a wrapper for the utils.api_helpers module to handle
import errors and provide fallback functionality.
"""

import os
import time
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_helpers_wrapper")

# Type variable for generic return type
T = TypeVar('T')

# Try to import the utils.api_helpers module
try:
    # Try multiple possible import paths
    try:
        from utils.api_helpers import CircuitBreaker, APICache, retry_with_backoff
    except ImportError:
        from shared.utils.api_helpers import CircuitBreaker, APICache, retry_with_backoff
    logger.info("Successfully imported api_helpers")
    IMPORT_SUCCESS = True
except ImportError as e:
    logger.warning(f"Failed to import api_helpers: {str(e)}")
    logger.warning("Using fallback implementations")
    IMPORT_SUCCESS = False

# Fallback implementations
if not IMPORT_SUCCESS:
    class CircuitBreaker:
        """
        Fallback implementation of CircuitBreaker.
        """

        def __init__(self, name: str, failure_threshold: int = 3, reset_timeout: float = 60.0):
            """
            Initialize the CircuitBreaker.

            Args:
                name: Name of the service protected by this circuit breaker
                failure_threshold: Number of failures before opening the circuit
                reset_timeout: Time in seconds before attempting to close the circuit again
            """
            self.name = name
            self.failure_threshold = failure_threshold
            self.reset_timeout = reset_timeout
            self.failure_count = 0
            self.last_failure_time = 0
            self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

            logger.info(f"Created fallback CircuitBreaker for {name}")

        async def call(self, func: Callable[..., T], *args, **kwargs) -> Optional[T]:
            """
            Call a function with circuit breaker protection.

            Args:
                func: Async function to call
                *args: Positional arguments for the function
                **kwargs: Keyword arguments for the function

            Returns:
                Result of the function call or None if circuit is open
            """
            current_time = time.time()

            # Check if circuit is OPEN
            if self.state == "OPEN":
                if current_time - self.last_failure_time > self.reset_timeout:
                    # Try to recover - move to HALF-OPEN
                    self.state = "HALF-OPEN"
                    logger.info(f"Circuit breaker for {self.name} moved to HALF-OPEN state")
                else:
                    # Circuit is still OPEN
                    logger.warning(f"Circuit breaker for {self.name} is OPEN, skipping call")
                    return None

            try:
                # Call the function
                result = await func(*args, **kwargs)

                # If successful and in HALF-OPEN state, close the circuit
                if self.state == "HALF-OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info(f"Circuit breaker for {self.name} moved to CLOSED state")

                return result
            except Exception as e:
                # Handle failure
                self.failure_count += 1
                self.last_failure_time = current_time

                if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
                    # Too many failures, open the circuit
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker for {self.name} moved to OPEN state after {self.failure_count} failures")
                elif self.state == "HALF-OPEN":
                    # Failed during recovery attempt, back to OPEN
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker for {self.name} moved back to OPEN state after failed recovery")

                # Re-raise the exception
                raise

    class APICache:
        """
        Fallback implementation of APICache.
        """

        def __init__(self, cache_dir: str = None, default_ttl: int = 3600):
            """
            Initialize the APICache.

            Args:
                cache_dir: Directory to store cache files
                default_ttl: Default time-to-live in seconds
            """
            if cache_dir is None:
                cache_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'cache'
                )

            self.cache_dir = cache_dir
            self.default_ttl = default_ttl
            self.memory_cache = {}
            self.cache_expiry = {}

            # Create cache directory if it doesn't exist
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Initialized fallback APICache with directory: {cache_dir}")

        def get(self, key: str) -> Optional[Any]:
            """
            Get a value from the cache.

            Args:
                key: Cache key

            Returns:
                Cached value or None if not found or expired
            """
            # Check memory cache first
            if key in self.memory_cache:
                # Check if expired
                if key in self.cache_expiry and self.cache_expiry[key] > time.time():
                    return self.memory_cache[key]
                else:
                    # Expired, remove from memory cache
                    del self.memory_cache[key]
                    if key in self.cache_expiry:
                        del self.cache_expiry[key]

            # Check file cache
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)

                    # Check if expired
                    if 'expiry' in cache_data and cache_data['expiry'] > time.time():
                        # Add to memory cache
                        self.memory_cache[key] = cache_data['value']
                        self.cache_expiry[key] = cache_data['expiry']
                        return cache_data['value']
                    else:
                        # Expired, remove file
                        os.remove(cache_file)
                except Exception as e:
                    logger.warning(f"Error reading cache file {cache_file}: {str(e)}")

            return None

        def set(self, key: str, value: Any, ttl: int = None) -> None:
            """
            Set a value in the cache.

            Args:
                key: Cache key
                value: Value to cache
                ttl: Time-to-live in seconds (default: use default_ttl)
            """
            if ttl is None:
                ttl = self.default_ttl

            expiry = time.time() + ttl

            # Add to memory cache
            self.memory_cache[key] = value
            self.cache_expiry[key] = expiry

            # Add to file cache
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'value': value,
                        'expiry': expiry
                    }, f)
            except Exception as e:
                logger.warning(f"Error writing cache file {cache_file}: {str(e)}")

        def invalidate(self, key: str) -> None:
            """
            Invalidate a cache entry.

            Args:
                key: Cache key
            """
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            if key in self.cache_expiry:
                del self.cache_expiry[key]

            # Remove from file cache
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                except Exception as e:
                    logger.warning(f"Error removing cache file {cache_file}: {str(e)}")

        def clear(self) -> None:
            """Clear the entire cache."""
            # Clear memory cache
            self.memory_cache = {}
            self.cache_expiry = {}

            # Clear file cache
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    try:
                        os.remove(os.path.join(self.cache_dir, filename))
                    except Exception as e:
                        logger.warning(f"Error removing cache file {filename}: {str(e)}")

    async def retry_with_backoff(func: Callable[..., T], *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs) -> Optional[T]:
        """
        Fallback implementation of retry_with_backoff.

        Args:
            func: Async function to call
            *args: Positional arguments for the function
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call or None if all retries fail
        """
        retry_count = 0
        last_exception = None

        while retry_count <= max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                retry_count += 1
                last_exception = e

                if retry_count <= max_retries:
                    wait_time = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                    logger.warning(f"Retry {retry_count}/{max_retries} after error: {str(e)}. Waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} retries failed. Last error: {str(e)}")

        if last_exception:
            raise last_exception

        return None
