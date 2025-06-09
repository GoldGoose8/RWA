#!/usr/bin/env python3
"""
Base Filter Module

This module provides the base class for all filters in the Synergy7 Trading System.
Filters are used to screen signals based on various criteria.
"""

import os
import sys
import json
import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Callable
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('filters')

class BaseFilter(ABC):
    """
    Base class for all filters.
    
    Filters are used to screen signals based on various criteria.
    Each filter should implement the filter_signal method.
    """
    
    def __init__(self, config: Dict[str, Any] = None, cache_ttl: int = 60):
        """
        Initialize the base filter.
        
        Args:
            config: Filter configuration
            cache_ttl: Cache time-to-live in seconds
        """
        self.name = self.__class__.__name__
        self.config = config or {}
        self.cache_ttl = cache_ttl
        self.enabled = self.config.get('enabled', True)
        self.cache = {}
        self.cache_timestamps = {}
        
        logger.info(f"Initialized {self.name} filter with cache_ttl={cache_ttl}s")
    
    def is_cache_valid(self, key: str) -> bool:
        """
        Check if a cache entry is still valid.
        
        Args:
            key: Cache key
            
        Returns:
            True if the cache entry is valid, False otherwise
        """
        if key not in self.cache_timestamps:
            return False
        
        return (time.time() - self.cache_timestamps[key]) < self.cache_ttl
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if valid, None otherwise
        """
        if not self.is_cache_valid(key):
            return None
        
        return self.cache.get(key)
    
    def set_in_cache(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cache = {}
        self.cache_timestamps = {}
        logger.debug(f"{self.name} cache cleared")
    
    @abstractmethod
    async def filter_signal(self, signal: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Filter a signal based on specific criteria.
        
        Args:
            signal: Signal to filter
            
        Returns:
            Tuple of (passed_filter, metadata)
            - passed_filter: True if the signal passes the filter, False otherwise
            - metadata: Additional metadata about the filter result
        """
        pass
    
    async def __call__(self, signal: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Call the filter on a signal.
        
        Args:
            signal: Signal to filter
            
        Returns:
            Tuple of (passed_filter, metadata)
        """
        if not self.enabled:
            return True, {"filter": self.name, "status": "skipped", "reason": "Filter disabled"}
        
        try:
            return await self.filter_signal(signal)
        except Exception as e:
            logger.error(f"Error in {self.name} filter: {str(e)}")
            # If there's an error, we let the signal pass but mark it
            return True, {"filter": self.name, "status": "error", "reason": str(e)}

class FilterChain:
    """
    Chain of filters to apply to signals.
    
    This class manages a collection of filters and applies them in sequence.
    """
    
    def __init__(self, filters: List[BaseFilter] = None, parallel: bool = True):
        """
        Initialize the filter chain.
        
        Args:
            filters: List of filters to apply
            parallel: Whether to run filters in parallel
        """
        self.filters = filters or []
        self.parallel = parallel
        logger.info(f"Initialized FilterChain with {len(self.filters)} filters, parallel={parallel}")
    
    def add_filter(self, filter_obj: BaseFilter) -> None:
        """
        Add a filter to the chain.
        
        Args:
            filter_obj: Filter to add
        """
        self.filters.append(filter_obj)
        logger.info(f"Added {filter_obj.name} to filter chain")
    
    async def apply_filter(self, filter_obj: BaseFilter, signal: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Apply a single filter to a signal.
        
        Args:
            filter_obj: Filter to apply
            signal: Signal to filter
            
        Returns:
            Tuple of (passed_filter, metadata)
        """
        start_time = time.time()
        passed, metadata = await filter_obj(signal)
        elapsed = time.time() - start_time
        
        # Add timing information to metadata
        metadata["execution_time"] = elapsed
        
        logger.debug(f"Filter {filter_obj.name} {'passed' if passed else 'rejected'} signal in {elapsed:.3f}s")
        return passed, metadata
    
    async def apply_filters_sequential(self, signal: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Apply filters sequentially to a signal.
        
        Args:
            signal: Signal to filter
            
        Returns:
            Tuple of (passed_all_filters, filter_results)
        """
        results = []
        
        for filter_obj in self.filters:
            passed, metadata = await self.apply_filter(filter_obj, signal)
            results.append(metadata)
            
            if not passed:
                return False, results
        
        return True, results
    
    async def apply_filters_parallel(self, signal: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Apply filters in parallel to a signal.
        
        Args:
            signal: Signal to filter
            
        Returns:
            Tuple of (passed_all_filters, filter_results)
        """
        tasks = [self.apply_filter(filter_obj, signal) for filter_obj in self.filters]
        results = await asyncio.gather(*tasks)
        
        # Unpack results
        passed_list, metadata_list = zip(*results)
        
        # Signal passes if all filters pass
        passed_all = all(passed_list)
        
        return passed_all, list(metadata_list)
    
    async def apply_filters(self, signal: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Apply all filters to a signal.
        
        Args:
            signal: Signal to filter
            
        Returns:
            Tuple of (passed_all_filters, filter_results)
        """
        if self.parallel:
            return await self.apply_filters_parallel(signal)
        else:
            return await self.apply_filters_sequential(signal)
    
    async def filter_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter a list of signals.
        
        Args:
            signals: List of signals to filter
            
        Returns:
            List of signals that passed all filters, with filter metadata added
        """
        filtered_signals = []
        
        for signal in signals:
            passed, results = await self.apply_filters(signal)
            
            if passed:
                # Add filter results to signal metadata
                if 'metadata' not in signal:
                    signal['metadata'] = {}
                
                signal['metadata']['filter_results'] = results
                filtered_signals.append(signal)
        
        logger.info(f"Filtered {len(signals)} signals, {len(filtered_signals)} passed all filters")
        return filtered_signals
    
    def clear_caches(self) -> None:
        """Clear caches for all filters."""
        for filter_obj in self.filters:
            filter_obj.clear_cache()
        
        logger.debug("Cleared caches for all filters")
