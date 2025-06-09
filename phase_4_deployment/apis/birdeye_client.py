#!/usr/bin/env python3
"""
Birdeye API Client for Q5 Trading System

This module provides a client for interacting with the Birdeye API.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

# Import API manager
from phase_4_deployment.apis.api_manager import get_api_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("birdeye_client")

class BirdeyeClient:
    """
    Client for interacting with the Birdeye API.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Birdeye client.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.api_manager = get_api_manager(config)

        logger.info("Initialized Birdeye client")

    async def get_token_price(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        🔧 FIXED: Get the price of a token with enhanced error handling.

        Args:
            token_address: Token address

        Returns:
            Token price information or None if the call failed
        """
        endpoint = f"/defi/price?address={token_address}"
        cache_key = f"birdeye_price_{token_address}"

        try:
            result = await self.api_manager.call_api(
                api_type="birdeye",
                endpoint=endpoint,
                cache_key=cache_key,
                cache_ttl=60  # Cache for 60 seconds
            )

            # 🔧 FIXED: Validate response structure
            if result and 'data' in result:
                return result
            elif result:
                logger.warning(f"Unexpected Birdeye price response structure: {result}")
                return result  # Return anyway, might still be usable
            else:
                logger.warning(f"No price data returned for token {token_address}")
                return None

        except Exception as e:
            logger.error(f"Error getting token price for {token_address}: {e}")
            return None

    async def get_token_metadata(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a token.

        Args:
            token_address: Token address

        Returns:
            Token metadata or None if the call failed
        """
        endpoint = f"/defi/token_meta?address={token_address}"
        cache_key = f"birdeye_metadata_{token_address}"

        result = await self.api_manager.call_api(
            api_type="birdeye",
            endpoint=endpoint,
            cache_key=cache_key,
            cache_ttl=3600  # Cache for 1 hour
        )

        return result

    async def get_token_list(self, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Get a list of tokens.

        Args:
            limit: Maximum number of tokens to return
            offset: Offset for pagination

        Returns:
            List of tokens or None if the call failed
        """
        endpoint = f"/defi/token_list?limit={limit}&offset={offset}"
        cache_key = f"birdeye_token_list_{limit}_{offset}"

        result = await self.api_manager.call_api(
            api_type="birdeye",
            endpoint=endpoint,
            cache_key=cache_key,
            cache_ttl=3600  # Cache for 1 hour
        )

        return result

    async def get_order_book(self, market_address: str) -> Optional[Dict[str, Any]]:
        """
        Get the order book for a market.

        Args:
            market_address: Market address

        Returns:
            Order book or None if the call failed
        """
        endpoint = f"/defi/orderbook?market={market_address}"

        result = await self.api_manager.call_api(
            api_type="birdeye",
            endpoint=endpoint
        )

        return result

    async def get_recent_trades(self, market_address: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Get recent trades for a market.

        Args:
            market_address: Market address
            limit: Maximum number of trades to return

        Returns:
            Recent trades or None if the call failed
        """
        endpoint = f"/defi/trades?market={market_address}&limit={limit}"

        result = await self.api_manager.call_api(
            api_type="birdeye",
            endpoint=endpoint
        )

        return result

    async def get_token_historical_price(self, token_address: str,
                                        resolution: str = "1D",
                                        count: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get historical price data for a token.

        Args:
            token_address: Token address
            resolution: Time resolution (e.g., "1H", "1D", "1W")
            count: Number of data points to return

        Returns:
            Historical price data or None if the call failed
        """
        endpoint = f"/defi/price_history?address={token_address}&type={resolution}&count={count}"
        cache_key = f"birdeye_price_history_{token_address}_{resolution}_{count}"

        result = await self.api_manager.call_api(
            api_type="birdeye",
            endpoint=endpoint,
            cache_key=cache_key,
            cache_ttl=300  # Cache for 5 minutes
        )

        return result

    async def get_token_markets(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get markets for a token.

        Args:
            token_address: Token address

        Returns:
            Markets information or None if the call failed
        """
        endpoint = f"/defi/markets?address={token_address}"
        cache_key = f"birdeye_markets_{token_address}"

        result = await self.api_manager.call_api(
            api_type="birdeye",
            endpoint=endpoint,
            cache_key=cache_key,
            cache_ttl=3600  # Cache for 1 hour
        )

        return result

    async def get_token_holders(self, token_address: str, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Get holders of a token.

        Args:
            token_address: Token address
            limit: Maximum number of holders to return
            offset: Offset for pagination

        Returns:
            Token holders or None if the call failed
        """
        endpoint = f"/defi/token_holders?address={token_address}&limit={limit}&offset={offset}"
        cache_key = f"birdeye_holders_{token_address}_{limit}_{offset}"

        result = await self.api_manager.call_api(
            api_type="birdeye",
            endpoint=endpoint,
            cache_key=cache_key,
            cache_ttl=3600  # Cache for 1 hour
        )

        return result
