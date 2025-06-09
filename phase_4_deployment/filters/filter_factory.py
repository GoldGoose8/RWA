#!/usr/bin/env python3
"""
Filter Factory Module

This module provides a factory for creating filter instances based on configuration.
"""

import os
import sys
import json
import logging
import yaml
from typing import Dict, List, Any, Optional, Type

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import filters
from phase_4_deployment.filters.base_filter import BaseFilter, FilterChain
from phase_4_deployment.filters.wallet_alpha_filter import AlphaWalletFilter
from phase_4_deployment.filters.liquidity_guard import LiquidityGuard
from phase_4_deployment.filters.volatility_screener import VolatilityScreener

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('filter_factory')

class FilterFactory:
    """
    Factory for creating filter instances based on configuration.
    """
    
    # Map of filter names to filter classes
    FILTER_CLASSES = {
        'alpha_wallet': AlphaWalletFilter,
        'liquidity_guard': LiquidityGuard,
        'volatility_screener': VolatilityScreener
    }
    
    @classmethod
    def create_filter(cls, filter_name: str, config: Dict[str, Any] = None) -> Optional[BaseFilter]:
        """
        Create a filter instance.
        
        Args:
            filter_name: Name of the filter to create
            config: Filter configuration
            
        Returns:
            Filter instance or None if filter not found
        """
        if filter_name not in cls.FILTER_CLASSES:
            logger.warning(f"Unknown filter: {filter_name}")
            return None
        
        filter_class = cls.FILTER_CLASSES[filter_name]
        
        try:
            filter_instance = filter_class(config)
            logger.info(f"Created {filter_name} filter")
            return filter_instance
        except Exception as e:
            logger.error(f"Error creating {filter_name} filter: {str(e)}")
            return None
    
    @classmethod
    def create_filter_chain(cls, config: Dict[str, Any]) -> FilterChain:
        """
        Create a filter chain from configuration.
        
        Args:
            config: Filter configuration
            
        Returns:
            FilterChain instance
        """
        # Check if filters are enabled
        if not config.get('enabled', True):
            logger.info("Filters disabled in configuration")
            return FilterChain([])
        
        # Create filter instances
        filters = []
        
        for filter_name, filter_config in config.items():
            # Skip non-filter keys
            if filter_name in ['enabled', 'cache_ttl', 'parallel_execution']:
                continue
            
            # Skip disabled filters
            if isinstance(filter_config, dict) and not filter_config.get('enabled', True):
                logger.info(f"Filter {filter_name} disabled in configuration")
                continue
            
            filter_instance = cls.create_filter(filter_name, filter_config)
            
            if filter_instance:
                filters.append(filter_instance)
        
        # Create filter chain
        parallel = config.get('parallel_execution', True)
        filter_chain = FilterChain(filters, parallel)
        
        logger.info(f"Created filter chain with {len(filters)} filters, parallel={parallel}")
        return filter_chain
    
    @classmethod
    def create_filter_chain_from_file(cls, config_path: str) -> FilterChain:
        """
        Create a filter chain from a configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            FilterChain instance
        """
        try:
            # Load configuration from file
            with open(config_path, 'r') as f:
                if config_path.endswith('.json'):
                    config = json.load(f)
                elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                else:
                    logger.error(f"Unsupported configuration file format: {config_path}")
                    return FilterChain([])
            
            # Extract filter configuration
            if 'filters' in config:
                filter_config = config['filters']
            else:
                logger.warning(f"No 'filters' section found in {config_path}")
                return FilterChain([])
            
            return cls.create_filter_chain(filter_config)
        except Exception as e:
            logger.error(f"Error loading filter configuration from {config_path}: {str(e)}")
            return FilterChain([])
    
    @classmethod
    async def close_filters(cls, filter_chain: FilterChain) -> None:
        """
        Close all filters in a filter chain.
        
        Args:
            filter_chain: FilterChain instance
        """
        for filter_obj in filter_chain.filters:
            if hasattr(filter_obj, 'close') and callable(filter_obj.close):
                try:
                    await filter_obj.close()
                except Exception as e:
                    logger.error(f"Error closing {filter_obj.name} filter: {str(e)}")
        
        logger.info(f"Closed {len(filter_chain.filters)} filters")
