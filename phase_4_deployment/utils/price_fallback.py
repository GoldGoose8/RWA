#!/usr/bin/env python3
"""
Price Fallback Service
Provides fallback price data when primary APIs are down.
"""

import logging
import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PriceFallbackService:
    """Provides fallback price data when primary APIs fail."""

    def __init__(self):
        """Initialize the price fallback service."""
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
            }
        }

        # Try to get real-time prices from alternative sources
        # Note: CoinGecko update will be called separately when needed

    async def _update_prices_from_coingecko(self):
        """Try to get real-time prices from CoinGecko as fallback."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get SOL price from CoinGecko
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": "solana",
                        "vs_currencies": "usd"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if "solana" in data and "usd" in data["solana"]:
                        sol_price = data["solana"]["usd"]
                        self.fallback_prices["So11111111111111111111111111111111111111112"]["value"] = sol_price
                        logger.info(f"✅ Updated SOL price from CoinGecko: ${sol_price}")

        except Exception as e:
            logger.warning(f"Could not update prices from CoinGecko: {e}")

    def get_token_price(self, token_address: str) -> Optional[Dict[str, Any]]:
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

    def get_token_metadata(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get fallback metadata for a token."""
        if token_address in self.fallback_prices:
            price_data = self.fallback_prices[token_address]
            return {
                "address": token_address,
                "symbol": price_data["symbol"],
                "name": price_data["symbol"],
                "decimals": 9 if price_data["symbol"] == "SOL" else 6,
                "source": "fallback"
            }

        return None

# Global instance
_price_fallback = None

def get_price_fallback() -> PriceFallbackService:
    """Get the global price fallback service instance."""
    global _price_fallback
    if _price_fallback is None:
        _price_fallback = PriceFallbackService()
    return _price_fallback
