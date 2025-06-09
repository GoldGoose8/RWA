#!/usr/bin/env python3
"""
Alpha Wallet Filter Module

This module provides a filter that screens signals based on wallet activity
from known "alpha" wallets (whales, smart money, etc.).
"""

import os
import sys
import json
import time
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import base filter
from phase_4_deployment.filters.base_filter import BaseFilter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('alpha_wallet_filter')

class AlphaWalletFilter(BaseFilter):
    """
    Filter that screens signals based on wallet activity from known "alpha" wallets.
    
    This filter checks if a token has been interacted with by a minimum number of
    alpha wallets within a specified lookback period.
    """
    
    def __init__(self, config: Dict[str, Any] = None, cache_ttl: int = 300):
        """
        Initialize the alpha wallet filter.
        
        Args:
            config: Filter configuration
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        super().__init__(config, cache_ttl)
        
        # Load configuration
        self.min_wallet_count = self.config.get('min_wallet_count', 5)
        self.lookback_period = self.config.get('lookback_period', 24)  # hours
        self.momentum_threshold = self.config.get('momentum_threshold', 0.1)
        
        # Load API configuration
        self.helius_api_key = os.environ.get('HELIUS_API_KEY', '')
        self.helius_endpoint = self.config.get('helius_endpoint', 'https://api.helius.xyz/v0')
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Load alpha wallets
        self.alpha_wallets = self._load_alpha_wallets()
        
        logger.info(f"Initialized AlphaWalletFilter with min_wallet_count={self.min_wallet_count}, "
                   f"lookback_period={self.lookback_period}h, "
                   f"alpha_wallets_count={len(self.alpha_wallets)}")
    
    def _load_alpha_wallets(self) -> Set[str]:
        """
        Load alpha wallet addresses from file or default list.
        
        Returns:
            Set of alpha wallet addresses
        """
        # Path to alpha wallets file
        alpha_wallets_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data', 'alpha_wallets.json'
        )
        
        # Default alpha wallets (known Solana whales and smart money)
        default_alpha_wallets = {
            "5ZWj7a1f8tWkjBESHKgrLmZhGYdFkK9fpN4e7R5Xmknp",  # Example whale
            "HN8Hmb3L3F1ZZnEQw4WTkqnVRhD4T8HC2mXvcQsPJQdz",  # Example whale
            "4Rf9mGD7FeYknun5JczX5nGLTfQuS1GRjUzVgTs5MbJN",  # Example whale
            "7NsngNMtXJNdHgeK4znQDZ5PJ9W1xZ7hHv9vuoAVeD8",   # Example whale
            "2LbxJ9WP2yUHiQSQUZ9XM4xjKFUQcLUXAuUy5ZF9RYeZ",  # Example whale
            "6VzWGL51jLUGYvEGLJrGNnzBqvE2U8Q5zPGY3gSCq2GL",  # Example whale
            "9LR6QXt7zaeNX9gXbzTQgWQRNuA1wBJKFXUMVY3aBNqs",  # Example whale
            "4YJ8np7RYXBxD8JqGN2Q2Wd5zXJPqZp7SMeA1HZSXbhS",  # Example whale
            "5sjXzaafpCJA3KNPxTbiuYCWUwZxzXBHuYTvUgXp1nM3",  # Example whale
            "GZNsQP1hyUJmHSrVRQEjuwKWGq8uwMZgMrWZxcidXzgE"   # Example whale
        }
        
        try:
            # Try to load from file
            if os.path.exists(alpha_wallets_path):
                with open(alpha_wallets_path, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    return set(data)
                elif isinstance(data, dict) and 'wallets' in data:
                    return set(data['wallets'])
                else:
                    logger.warning(f"Invalid format in {alpha_wallets_path}, using default alpha wallets")
                    return default_alpha_wallets
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(alpha_wallets_path), exist_ok=True)
                
                # Save default wallets to file
                with open(alpha_wallets_path, 'w') as f:
                    json.dump(list(default_alpha_wallets), f, indent=2)
                
                logger.info(f"Created default alpha wallets file at {alpha_wallets_path}")
                return default_alpha_wallets
        except Exception as e:
            logger.error(f"Error loading alpha wallets: {str(e)}")
            return default_alpha_wallets
    
    async def get_token_wallet_activity(self, token_address: str) -> List[Dict[str, Any]]:
        """
        Get wallet activity for a token.
        
        Args:
            token_address: Token address to check
            
        Returns:
            List of wallet activity records
        """
        # Check cache first
        cache_key = f"wallet_activity_{token_address}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Calculate lookback timestamp
        lookback_time = datetime.now() - timedelta(hours=self.lookback_period)
        lookback_timestamp = int(lookback_time.timestamp())
        
        try:
            # Query Helius API for token activity
            url = f"{self.helius_endpoint}/token-events"
            
            payload = {
                "query": {
                    "tokens": [token_address],
                    "types": ["TRANSFER", "SWAP"],
                    "startTime": lookback_timestamp,
                    "endTime": int(time.time())
                },
                "options": {
                    "limit": 100
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.helius_api_key}"
            }
            
            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract wallet activity
            activities = []
            
            if 'result' in data and isinstance(data['result'], list):
                for event in data['result']:
                    # Extract wallet addresses from event
                    source_wallet = event.get('sourceWallet')
                    destination_wallet = event.get('destinationWallet')
                    
                    if source_wallet:
                        activities.append({
                            'wallet_address': source_wallet,
                            'token_address': token_address,
                            'timestamp': event.get('timestamp', 0),
                            'type': event.get('type', 'UNKNOWN'),
                            'amount': event.get('amount', 0)
                        })
                    
                    if destination_wallet:
                        activities.append({
                            'wallet_address': destination_wallet,
                            'token_address': token_address,
                            'timestamp': event.get('timestamp', 0),
                            'type': event.get('type', 'UNKNOWN'),
                            'amount': event.get('amount', 0)
                        })
            
            # Cache the results
            self.set_in_cache(cache_key, activities)
            
            return activities
        except Exception as e:
            logger.error(f"Error getting wallet activity for {token_address}: {str(e)}")
            return []
    
    async def calculate_alpha_score(self, token_address: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate alpha score for a token based on alpha wallet activity.
        
        Args:
            token_address: Token address to check
            
        Returns:
            Tuple of (alpha_score, metadata)
        """
        # Get wallet activity
        activities = await self.get_token_wallet_activity(token_address)
        
        if not activities:
            return 0.0, {
                "alpha_wallets": 0,
                "total_wallets": 0,
                "alpha_ratio": 0.0,
                "activity_count": 0
            }
        
        # Extract unique wallets
        all_wallets = set(activity['wallet_address'] for activity in activities)
        alpha_wallets = all_wallets.intersection(self.alpha_wallets)
        
        # Calculate alpha score
        alpha_count = len(alpha_wallets)
        total_count = len(all_wallets)
        activity_count = len(activities)
        
        # Alpha ratio is the percentage of wallets that are alpha wallets
        alpha_ratio = alpha_count / total_count if total_count > 0 else 0
        
        # Alpha score is a combination of alpha ratio and activity count
        alpha_score = alpha_ratio * min(1.0, activity_count / 100)
        
        return alpha_score, {
            "alpha_wallets": alpha_count,
            "total_wallets": total_count,
            "alpha_ratio": alpha_ratio,
            "activity_count": activity_count
        }
    
    async def filter_signal(self, signal: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Filter a signal based on alpha wallet activity.
        
        Args:
            signal: Signal to filter
            
        Returns:
            Tuple of (passed_filter, metadata)
        """
        # Extract token address from signal
        token_address = signal.get('token_address')
        
        if not token_address:
            return False, {
                "filter": self.name,
                "status": "rejected",
                "reason": "No token address in signal",
                "alpha_score": 0.0
            }
        
        # Calculate alpha score
        alpha_score, alpha_metadata = await self.calculate_alpha_score(token_address)
        
        # Check if alpha score meets threshold
        passed = alpha_metadata['alpha_wallets'] >= self.min_wallet_count
        
        # Prepare metadata
        metadata = {
            "filter": self.name,
            "status": "passed" if passed else "rejected",
            "reason": f"Alpha wallets: {alpha_metadata['alpha_wallets']} (min: {self.min_wallet_count})",
            "alpha_score": alpha_score,
            **alpha_metadata
        }
        
        return passed, metadata
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
