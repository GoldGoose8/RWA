#!/usr/bin/env python3
"""
Liquidity Guard Filter Module

This module provides a filter that screens signals based on market liquidity
to avoid thin order books and high slippage.
"""

import os
import sys
import json
import time
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional, Tuple
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
logger = logging.getLogger('liquidity_guard')

class LiquidityGuard(BaseFilter):
    """
    Filter that screens signals based on market liquidity.
    
    This filter checks if a market has sufficient liquidity to execute trades
    without excessive slippage.
    """
    
    def __init__(self, config: Dict[str, Any] = None, cache_ttl: int = 300):
        """
        Initialize the liquidity guard filter.
        
        Args:
            config: Filter configuration
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        super().__init__(config, cache_ttl)
        
        # Load configuration
        self.min_liquidity_usd = self.config.get('min_liquidity_usd', 50000)
        self.order_book_depth = self.config.get('order_book_depth', 10)
        
        # Load API configuration
        self.birdeye_api_key = os.environ.get('BIRDEYE_API_KEY', '')
        self.birdeye_endpoint = self.config.get('birdeye_endpoint', 'https://api.birdeye.so/v1')
        self.jupiter_endpoint = self.config.get('jupiter_endpoint', 'https://quote-api.jup.ag/v6')
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"Initialized LiquidityGuard with min_liquidity_usd={self.min_liquidity_usd}, "
                   f"order_book_depth={self.order_book_depth}")
    
    async def get_market_liquidity_birdeye(self, token_address: str) -> Dict[str, Any]:
        """
        Get market liquidity data from Birdeye API.
        
        Args:
            token_address: Token address to check
            
        Returns:
            Dictionary containing liquidity data
        """
        # Check cache first
        cache_key = f"liquidity_birdeye_{token_address}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Query Birdeye API for token liquidity
            url = f"{self.birdeye_endpoint}/defi/token_liquidity"
            
            params = {
                "token_address": token_address
            }
            
            headers = {
                "X-API-KEY": self.birdeye_api_key
            }
            
            response = await self.http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract liquidity data
            liquidity_data = {
                "source": "birdeye",
                "token_address": token_address,
                "timestamp": int(time.time()),
                "total_liquidity_usd": 0,
                "pools": []
            }
            
            if 'data' in data and 'items' in data['data']:
                # Sum up liquidity across all pools
                total_liquidity = 0
                
                for pool in data['data']['items']:
                    pool_liquidity = pool.get('liquidity', 0)
                    total_liquidity += pool_liquidity
                    
                    liquidity_data['pools'].append({
                        "pool_address": pool.get('address', ''),
                        "dex": pool.get('dex', 'unknown'),
                        "liquidity_usd": pool_liquidity,
                        "volume_24h": pool.get('volume24h', 0)
                    })
                
                liquidity_data['total_liquidity_usd'] = total_liquidity
            
            # Cache the results
            self.set_in_cache(cache_key, liquidity_data)
            
            return liquidity_data
        except Exception as e:
            logger.error(f"Error getting liquidity from Birdeye for {token_address}: {str(e)}")
            return {
                "source": "birdeye",
                "token_address": token_address,
                "timestamp": int(time.time()),
                "total_liquidity_usd": 0,
                "error": str(e),
                "pools": []
            }
    
    async def get_market_liquidity_jupiter(self, token_address: str) -> Dict[str, Any]:
        """
        Get market liquidity data from Jupiter API.
        
        Args:
            token_address: Token address to check
            
        Returns:
            Dictionary containing liquidity data
        """
        # Check cache first
        cache_key = f"liquidity_jupiter_{token_address}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Query Jupiter API for token liquidity
            # Use USDC as the quote token
            usdc_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            url = f"{self.jupiter_endpoint}/quote"
            
            params = {
                "inputMint": token_address,
                "outputMint": usdc_address,
                "amount": "1000000",  # 1 token in lamports
                "slippageBps": 50,    # 0.5% slippage
                "onlyDirectRoutes": "false",
                "asLegacyTransaction": "false"
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract liquidity data
            liquidity_data = {
                "source": "jupiter",
                "token_address": token_address,
                "timestamp": int(time.time()),
                "total_liquidity_usd": 0,
                "routes": []
            }
            
            if 'outAmount' in data:
                # Calculate approximate liquidity based on the best route
                out_amount = int(data.get('outAmount', 0))
                price_impact = data.get('priceImpactPct', 0)
                
                # Estimate total liquidity based on price impact
                # This is a rough approximation: if 1 token causes X% price impact,
                # then total liquidity is approximately (1 / X) * out_amount
                if price_impact > 0:
                    estimated_liquidity = (1 / price_impact) * out_amount / 1000000  # Convert from lamports to USDC
                else:
                    estimated_liquidity = out_amount / 1000000 * 100  # Assume very high liquidity
                
                liquidity_data['total_liquidity_usd'] = estimated_liquidity
                
                # Extract route information
                if 'routePlan' in data:
                    for route in data['routePlan']:
                        liquidity_data['routes'].append({
                            "market_id": route.get('id', ''),
                            "dex": route.get('label', 'unknown'),
                            "percent": route.get('percent', 0)
                        })
            
            # Cache the results
            self.set_in_cache(cache_key, liquidity_data)
            
            return liquidity_data
        except Exception as e:
            logger.error(f"Error getting liquidity from Jupiter for {token_address}: {str(e)}")
            return {
                "source": "jupiter",
                "token_address": token_address,
                "timestamp": int(time.time()),
                "total_liquidity_usd": 0,
                "error": str(e),
                "routes": []
            }
    
    async def get_order_book_depth(self, token_address: str) -> Dict[str, Any]:
        """
        Get order book depth for a token.
        
        Args:
            token_address: Token address to check
            
        Returns:
            Dictionary containing order book depth data
        """
        # Check cache first
        cache_key = f"order_book_{token_address}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Query Birdeye API for order book
            url = f"{self.birdeye_endpoint}/orderbook"
            
            params = {
                "token_address": token_address,
                "depth": self.order_book_depth
            }
            
            headers = {
                "X-API-KEY": self.birdeye_api_key
            }
            
            response = await self.http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract order book data
            order_book_data = {
                "token_address": token_address,
                "timestamp": int(time.time()),
                "bid_depth": 0,
                "ask_depth": 0,
                "spread_pct": 0,
                "bids": [],
                "asks": []
            }
            
            if 'data' in data:
                # Extract bids and asks
                bids = data['data'].get('bids', [])
                asks = data['data'].get('asks', [])
                
                # Calculate bid and ask depth
                bid_depth = sum(bid.get('size', 0) * bid.get('price', 0) for bid in bids)
                ask_depth = sum(ask.get('size', 0) * ask.get('price', 0) for ask in asks)
                
                # Calculate spread
                best_bid = bids[0].get('price', 0) if bids else 0
                best_ask = asks[0].get('price', 0) if asks else 0
                
                if best_bid > 0 and best_ask > 0:
                    spread_pct = (best_ask - best_bid) / best_bid * 100
                else:
                    spread_pct = 0
                
                order_book_data.update({
                    "bid_depth": bid_depth,
                    "ask_depth": ask_depth,
                    "spread_pct": spread_pct,
                    "bids": bids[:self.order_book_depth],
                    "asks": asks[:self.order_book_depth]
                })
            
            # Cache the results
            self.set_in_cache(cache_key, order_book_data)
            
            return order_book_data
        except Exception as e:
            logger.error(f"Error getting order book for {token_address}: {str(e)}")
            return {
                "token_address": token_address,
                "timestamp": int(time.time()),
                "bid_depth": 0,
                "ask_depth": 0,
                "spread_pct": 0,
                "error": str(e),
                "bids": [],
                "asks": []
            }
    
    async def calculate_liquidity_score(self, token_address: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate liquidity score for a token.
        
        Args:
            token_address: Token address to check
            
        Returns:
            Tuple of (liquidity_score, metadata)
        """
        # Get liquidity data from multiple sources
        birdeye_data = await self.get_market_liquidity_birdeye(token_address)
        jupiter_data = await self.get_market_liquidity_jupiter(token_address)
        order_book_data = await self.get_order_book_depth(token_address)
        
        # Combine liquidity data
        birdeye_liquidity = birdeye_data.get('total_liquidity_usd', 0)
        jupiter_liquidity = jupiter_data.get('total_liquidity_usd', 0)
        
        # Use the maximum liquidity value from the two sources
        total_liquidity = max(birdeye_liquidity, jupiter_liquidity)
        
        # Calculate liquidity score (0-1)
        liquidity_score = min(1.0, total_liquidity / self.min_liquidity_usd)
        
        # Extract order book metrics
        bid_depth = order_book_data.get('bid_depth', 0)
        ask_depth = order_book_data.get('ask_depth', 0)
        spread_pct = order_book_data.get('spread_pct', 0)
        
        # Prepare metadata
        metadata = {
            "total_liquidity_usd": total_liquidity,
            "birdeye_liquidity_usd": birdeye_liquidity,
            "jupiter_liquidity_usd": jupiter_liquidity,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "spread_pct": spread_pct,
            "pool_count": len(birdeye_data.get('pools', [])),
            "route_count": len(jupiter_data.get('routes', []))
        }
        
        return liquidity_score, metadata
    
    async def filter_signal(self, signal: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Filter a signal based on market liquidity.
        
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
                "liquidity_score": 0.0
            }
        
        # Calculate liquidity score
        liquidity_score, liquidity_metadata = await self.calculate_liquidity_score(token_address)
        
        # Check if liquidity meets threshold
        total_liquidity = liquidity_metadata['total_liquidity_usd']
        passed = total_liquidity >= self.min_liquidity_usd
        
        # Prepare metadata
        metadata = {
            "filter": self.name,
            "status": "passed" if passed else "rejected",
            "reason": f"Liquidity: ${total_liquidity:.2f} (min: ${self.min_liquidity_usd})",
            "liquidity_score": liquidity_score,
            **liquidity_metadata
        }
        
        return passed, metadata
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
