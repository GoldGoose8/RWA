#!/usr/bin/env python3
"""
Birdeye Data Source

This module provides a data source for Birdeye API.
"""

import os
import sys
import json
import time
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

# Install required packages
try:
    import httpx
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BirdeyeDataSource:
    """Data source for Birdeye API."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.birdeye.so/v1",
    ):
        """
        Initialize the Birdeye data source.
        
        Args:
            api_key: Birdeye API key
            endpoint: Birdeye API endpoint
        """
        self.api_key = api_key
        self.endpoint = endpoint
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers={"X-API-KEY": api_key}
        )
        
        # Initialize cache
        self.cache = {
            "order_books": {},
            "token_prices": {},
            "token_metadata": {},
        }
        
        # Initialize cache expiry
        self.cache_expiry = {
            "order_books": {},
            "token_prices": {},
            "token_metadata": {},
        }
        
        # Cache TTL in seconds
        self.cache_ttl = {
            "order_books": 5,  # 5 seconds
            "token_prices": 60,  # 1 minute
            "token_metadata": 3600,  # 1 hour
        }
        
        logger.info("Initialized Birdeye data source")
    
    async def get_order_book(self, market: str) -> Dict[str, Any]:
        """
        Get order book for a market.
        
        Args:
            market: Market symbol (e.g., "SOL-USDC")
            
        Returns:
            Dict[str, Any]: Order book data
        """
        try:
            # Check cache
            if market in self.cache["order_books"]:
                cache_time = self.cache_expiry["order_books"].get(market, 0)
                if time.time() - cache_time < self.cache_ttl["order_books"]:
                    return self.cache["order_books"][market]
            
            # Parse market symbol
            base_token, quote_token = market.split("-")
            
            # Get token addresses
            base_address = await self._get_token_address(base_token)
            quote_address = await self._get_token_address(quote_token)
            
            if not base_address or not quote_address:
                logger.error(f"Could not find token addresses for {market}")
                return {}
            
            # Get order book
            response = await self.http_client.get(
                f"{self.endpoint}/defi/orderbook",
                params={
                    "token_address": base_address,
                    "vsToken": quote_address,
                    "depth": 20,
                }
            )
            response.raise_for_status()
            
            # Parse response
            order_book = response.json()
            
            # Cache order book
            self.cache["order_books"][market] = order_book
            self.cache_expiry["order_books"][market] = time.time()
            
            return order_book
        except Exception as e:
            logger.error(f"Error getting order book for {market}: {str(e)}")
            return {}
    
    async def get_token_price(self, token: str) -> Dict[str, Any]:
        """
        Get token price.
        
        Args:
            token: Token symbol or address
            
        Returns:
            Dict[str, Any]: Token price data
        """
        try:
            # Check cache
            if token in self.cache["token_prices"]:
                cache_time = self.cache_expiry["token_prices"].get(token, 0)
                if time.time() - cache_time < self.cache_ttl["token_prices"]:
                    return self.cache["token_prices"][token]
            
            # Get token address
            token_address = await self._get_token_address(token)
            
            if not token_address:
                logger.error(f"Could not find token address for {token}")
                return {}
            
            # Get token price
            response = await self.http_client.get(
                f"{self.endpoint}/defi/price",
                params={"token_address": token_address}
            )
            response.raise_for_status()
            
            # Parse response
            price_data = response.json()
            
            # Cache token price
            self.cache["token_prices"][token] = price_data
            self.cache_expiry["token_prices"][token] = time.time()
            
            return price_data
        except Exception as e:
            logger.error(f"Error getting token price for {token}: {str(e)}")
            return {}
    
    async def get_token_metadata(self, token: str) -> Dict[str, Any]:
        """
        Get token metadata.
        
        Args:
            token: Token symbol or address
            
        Returns:
            Dict[str, Any]: Token metadata
        """
        try:
            # Check cache
            if token in self.cache["token_metadata"]:
                cache_time = self.cache_expiry["token_metadata"].get(token, 0)
                if time.time() - cache_time < self.cache_ttl["token_metadata"]:
                    return self.cache["token_metadata"][token]
            
            # Get token address
            token_address = await self._get_token_address(token)
            
            if not token_address:
                logger.error(f"Could not find token address for {token}")
                return {}
            
            # Get token metadata
            response = await self.http_client.get(
                f"{self.endpoint}/token/metadata",
                params={"token_address": token_address}
            )
            response.raise_for_status()
            
            # Parse response
            metadata = response.json()
            
            # Cache token metadata
            self.cache["token_metadata"][token] = metadata
            self.cache_expiry["token_metadata"][token] = time.time()
            
            return metadata
        except Exception as e:
            logger.error(f"Error getting token metadata for {token}: {str(e)}")
            return {}
    
    async def close(self) -> None:
        """Close the data source."""
        logger.info("Closing Birdeye data source")
        
        # Close HTTP client
        await self.http_client.aclose()
        
        logger.info("Birdeye data source closed")
    
    async def _get_token_address(self, token: str) -> str:
        """
        Get token address from symbol or address.
        
        Args:
            token: Token symbol or address
            
        Returns:
            str: Token address
        """
        # Check if token is already an address
        if token.startswith("1") or token.startswith("2") or token.startswith("3") or token.startswith("4") or token.startswith("5") or token.startswith("6") or token.startswith("7") or token.startswith("8") or token.startswith("9") or token.startswith("A") or token.startswith("B") or token.startswith("C") or token.startswith("D") or token.startswith("E") or token.startswith("F"):
            return token
        
        # Common token addresses
        token_addresses = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "JTO": "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        }
        
        # Check if token is in common token addresses
        if token.upper() in token_addresses:
            return token_addresses[token.upper()]
        
        # Search for token
        try:
            response = await self.http_client.get(
                f"{self.endpoint}/token/search",
                params={"query": token}
            )
            response.raise_for_status()
            
            # Parse response
            search_results = response.json()
            
            if search_results.get("success") and search_results.get("data"):
                for result in search_results["data"]:
                    if result.get("symbol", "").upper() == token.upper():
                        return result.get("address", "")
            
            return ""
        except Exception as e:
            logger.error(f"Error searching for token {token}: {str(e)}")
            return ""

async def main():
    """Main function for testing."""
    # Create Birdeye data source
    birdeye = BirdeyeDataSource(
        api_key=os.environ.get("BIRDEYE_API_KEY", ""),
    )
    
    try:
        # Get order book for SOL-USDC
        order_book = await birdeye.get_order_book("SOL-USDC")
        print(f"SOL-USDC order book: {json.dumps(order_book, indent=2)}")
        
        # Get token price for SOL
        price_data = await birdeye.get_token_price("SOL")
        print(f"SOL price data: {json.dumps(price_data, indent=2)}")
        
        # Get token metadata for SOL
        metadata = await birdeye.get_token_metadata("SOL")
        print(f"SOL metadata: {json.dumps(metadata, indent=2)}")
    finally:
        # Close the data source
        await birdeye.close()

if __name__ == "__main__":
    asyncio.run(main())
