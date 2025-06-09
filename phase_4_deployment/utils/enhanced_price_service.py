#!/usr/bin/env python3
"""
🔧 PHASE 2: Enhanced Price Service with QuickNode Integration
Provides price data from QuickNode, Jupiter, CoinGecko, and fallback sources
"""

import logging
import asyncio
import httpx
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedPriceService:
    """🔧 PHASE 2: Enhanced price service with QuickNode, Jupiter, and CoinGecko integration."""

    def __init__(self):
        """Initialize the enhanced price service."""
        # QuickNode configuration
        self.quicknode_api_key = os.getenv('QUICKNODE_API_KEY')
        self.quicknode_price_url = os.getenv('QUICKNODE_PRICE_API_URL', 'https://api.quicknode.com/v1/solana/mainnet/prices')
        self.quicknode_enabled = os.getenv('QUICKNODE_PRICE_FEEDS_ENABLED', 'true').lower() == 'true'
        
        # Jupiter configuration
        self.jupiter_api_url = os.getenv('JUPITER_API_URL', 'https://quote-api.jup.ag/v6')
        self.jupiter_fallback = os.getenv('QUICKNODE_PRICE_FALLBACK_JUPITER', 'true').lower() == 'true'
        
        # CoinGecko configuration
        self.coingecko_fallback = os.getenv('QUICKNODE_PRICE_FALLBACK_COINGECKO', 'true').lower() == 'true'
        
        # Cache configuration
        self.cache_duration = int(os.getenv('QUICKNODE_PRICE_CACHE', '30'))
        self.price_cache = {}
        
        # HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(float(os.getenv('QUICKNODE_PRICE_TIMEOUT', '10'))),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        # Fallback prices
        self.fallback_prices = {
            "So11111111111111111111111111111111111111112": {  # SOL
                "value": 180.0,
                "symbol": "SOL",
                "last_updated": datetime.now().isoformat()
            },
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {  # USDC
                "value": 1.0,
                "symbol": "USDC",
                "last_updated": datetime.now().isoformat()
            },
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {  # USDT
                "value": 1.0,
                "symbol": "USDT",
                "last_updated": datetime.now().isoformat()
            }
        }
        
        logger.info(f"🔧 Enhanced Price Service initialized - QuickNode: {self.quicknode_enabled}")

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    def _is_cache_valid(self, token_address: str) -> bool:
        """Check if cached price is still valid."""
        if token_address not in self.price_cache:
            return False
        
        cache_entry = self.price_cache[token_address]
        cache_time = cache_entry.get('timestamp', 0)
        return (time.time() - cache_time) < self.cache_duration

    def _cache_price(self, token_address: str, price_data: Dict[str, Any], source: str):
        """Cache price data."""
        self.price_cache[token_address] = {
            'data': price_data,
            'source': source,
            'timestamp': time.time()
        }

    async def get_token_price(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        🔧 PHASE 2: Get token price from multiple sources with priority:
        1. Cache (if valid)
        2. QuickNode Price Feeds
        3. Jupiter Quote API
        4. CoinGecko
        5. Fallback prices
        """
        try:
            # Check cache first
            if self._is_cache_valid(token_address):
                cached = self.price_cache[token_address]
                logger.info(f"🔧 Using cached price for {token_address} from {cached['source']}")
                return cached['data']

            # Try QuickNode Price Feeds first
            if self.quicknode_enabled and self.quicknode_api_key:
                price_data = await self._get_quicknode_price(token_address)
                if price_data:
                    self._cache_price(token_address, price_data, 'quicknode')
                    return price_data

            # Fallback to Jupiter Quote API
            if self.jupiter_fallback:
                price_data = await self._get_jupiter_price(token_address)
                if price_data:
                    self._cache_price(token_address, price_data, 'jupiter')
                    return price_data

            # Fallback to CoinGecko (for SOL only)
            if self.coingecko_fallback and token_address == "So11111111111111111111111111111111111111112":
                price_data = await self._get_coingecko_price()
                if price_data:
                    self._cache_price(token_address, price_data, 'coingecko')
                    return price_data

            # Final fallback to hardcoded prices
            return self._get_fallback_price(token_address)

        except Exception as e:
            logger.error(f"❌ Error getting price for {token_address}: {e}")
            return self._get_fallback_price(token_address)

    async def _get_quicknode_price(self, token_address: str) -> Optional[Dict[str, Any]]:
        """🔧 PHASE 2: Get price from QuickNode Price Feeds."""
        try:
            headers = {
                "Authorization": f"Bearer {self.quicknode_api_key}",
                "Content-Type": "application/json"
            }
            
            # QuickNode price API call
            response = await self.http_client.get(
                f"{self.quicknode_price_url}/{token_address}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'price' in data:
                    price = float(data['price'])
                    logger.info(f"✅ QuickNode price for {token_address}: ${price}")
                    return {
                        "value": price,
                        "updateUnixTime": int(time.time()),
                        "updateHumanTime": datetime.now().isoformat(),
                        "source": "quicknode"
                    }
            else:
                logger.warning(f"⚠️ QuickNode price API error {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.warning(f"⚠️ QuickNode price fetch error: {e}")
        
        return None

    async def _get_jupiter_price(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get price from Jupiter Quote API."""
        try:
            # Use Jupiter quote to get current price (quote 1 token for USDC)
            usdc_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            response = await self.http_client.get(
                f"{self.jupiter_api_url}/quote",
                params={
                    "inputMint": token_address,
                    "outputMint": usdc_address,
                    "amount": 1000000000 if token_address == "So11111111111111111111111111111111111111112" else 1000000,  # 1 SOL or 1 token
                    "slippageBps": 50
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'outAmount' in data and 'inAmount' in data:
                    # Calculate price based on quote
                    in_amount = float(data['inAmount'])
                    out_amount = float(data['outAmount'])
                    
                    # Adjust for decimals
                    if token_address == "So11111111111111111111111111111111111111112":  # SOL
                        price = (out_amount / 1000000) / (in_amount / 1000000000)  # USDC has 6 decimals, SOL has 9
                    else:
                        price = (out_amount / 1000000) / (in_amount / 1000000)  # Both 6 decimals
                    
                    logger.info(f"✅ Jupiter price for {token_address}: ${price}")
                    return {
                        "value": price,
                        "updateUnixTime": int(time.time()),
                        "updateHumanTime": datetime.now().isoformat(),
                        "source": "jupiter"
                    }
                    
        except Exception as e:
            logger.warning(f"⚠️ Jupiter price fetch error: {e}")
        
        return None

    async def _get_coingecko_price(self) -> Optional[Dict[str, Any]]:
        """Get SOL price from CoinGecko."""
        try:
            response = await self.http_client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "solana",
                    "vs_currencies": "usd"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "solana" in data and "usd" in data["solana"]:
                    price = float(data["solana"]["usd"])
                    logger.info(f"✅ CoinGecko SOL price: ${price}")
                    return {
                        "value": price,
                        "updateUnixTime": int(time.time()),
                        "updateHumanTime": datetime.now().isoformat(),
                        "source": "coingecko"
                    }
                    
        except Exception as e:
            logger.warning(f"⚠️ CoinGecko price fetch error: {e}")
        
        return None

    def _get_fallback_price(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get fallback price for a token."""
        if token_address in self.fallback_prices:
            price_data = self.fallback_prices[token_address].copy()
            logger.info(f"🔄 Using fallback price for {price_data['symbol']}: ${price_data['value']}")
            return {
                "value": price_data["value"],
                "updateUnixTime": int(datetime.now().timestamp()),
                "updateHumanTime": datetime.now().isoformat(),
                "source": "fallback"
            }
        
        logger.warning(f"No fallback price available for token: {token_address}")
        return None

    async def get_multiple_prices(self, token_addresses: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get prices for multiple tokens concurrently."""
        tasks = [self.get_token_price(addr) for addr in token_addresses]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            addr: result if not isinstance(result, Exception) else None
            for addr, result in zip(token_addresses, results)
        }

# Global instance
_enhanced_price_service = None

async def get_enhanced_price_service() -> EnhancedPriceService:
    """Get the global enhanced price service instance."""
    global _enhanced_price_service
    if _enhanced_price_service is None:
        _enhanced_price_service = EnhancedPriceService()
    return _enhanced_price_service
