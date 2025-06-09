#!/usr/bin/env python3
"""
Birdeye Scanner for Q5 Trading System

This module provides scanning functionality for trading opportunities using Birdeye API.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Birdeye client
from phase_4_deployment.apis.birdeye_client import BirdeyeClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("birdeye_scanner")

class BirdeyeScanner:
    """
    Scanner for trading opportunities using Birdeye API.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the Birdeye scanner.

        Args:
            api_key: Birdeye API key
        """
        self.api_key = api_key or os.getenv('BIRDEYE_API_KEY')

        # Initialize Birdeye client
        config = {
            'birdeye': {
                'api_key': self.api_key,
                'base_url': 'https://public-api.birdeye.so'
            }
        }
        self.client = BirdeyeClient(config)

        # Popular Solana tokens for scanning
        self.popular_tokens = [
            'So11111111111111111111111111111111111111112',  # SOL
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
            'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',  # BONK
            'JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN',   # JUP
        ]

        logger.info("Initialized Birdeye scanner")

    async def scan_for_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scan for trading opportunities with fallback data sources.

        Args:
            limit: Maximum number of opportunities to return

        Returns:
            List of trading opportunities
        """
        opportunities = []

        try:
            # Scan popular tokens for opportunities (price data only to avoid 404 errors)
            token_symbols = ['SOL', 'USDC', 'USDT', 'BONK', 'JUP']

            for i, token_address in enumerate(self.popular_tokens[:limit]):
                try:
                    # Get only token price (metadata endpoint returns 404)
                    price_data = await self.client.get_token_price(token_address)

                    if price_data:
                        # Use hardcoded symbol mapping to avoid metadata API
                        symbol = token_symbols[i] if i < len(token_symbols) else 'UNKNOWN'

                        # Calculate opportunity score (without metadata)
                        score = self._calculate_opportunity_score(price_data, {'symbol': symbol})

                        opportunity = {
                            'token_address': token_address,
                            'symbol': symbol,
                            'name': f"{symbol} Token",
                            'price': price_data.get('value', 0),
                            'price_change_24h': price_data.get('priceChange24h', 0),
                            'volume_24h': price_data.get('volume24h', 0),
                            'market_cap': price_data.get('marketCap', 0),
                            'score': score,
                            'timestamp': datetime.now().isoformat()
                        }

                        opportunities.append(opportunity)

                        # Longer delay to avoid rate limiting (429 errors)
                        await asyncio.sleep(1.0)

                except Exception as e:
                    logger.warning(f"Error scanning token {token_address}: {e}")
                    continue

            # If no opportunities found, use fallback data
            if not opportunities:
                logger.warning("No opportunities from Birdeye API, using fallback data")
                opportunities = await self._get_fallback_opportunities(limit)

            # Sort by score (highest first)
            opportunities.sort(key=lambda x: x['score'], reverse=True)

            logger.info(f"Found {len(opportunities)} trading opportunities")
            return opportunities

        except Exception as e:
            logger.error(f"Error scanning for opportunities: {e}")
            # Return fallback opportunities on error
            return await self._get_fallback_opportunities(limit)

    def _calculate_opportunity_score(self, price_data: Dict[str, Any],
                                   metadata: Dict[str, Any]) -> float:
        """
        Calculate opportunity score based on price and metadata.

        Args:
            price_data: Price data from Birdeye
            metadata: Token metadata

        Returns:
            Opportunity score (0.0 to 1.0)
        """
        score = 0.0

        try:
            # Price change factor (positive changes get higher scores)
            price_change_24h = price_data.get('priceChange24h', 0)
            if price_change_24h > 0:
                score += min(price_change_24h / 100, 0.3)  # Max 0.3 for price change

            # Volume factor (higher volume gets higher score)
            volume_24h = price_data.get('volume24h', 0)
            if volume_24h > 100000:  # $100k+ volume
                score += 0.2
            elif volume_24h > 50000:  # $50k+ volume
                score += 0.1

            # Market cap factor (reasonable market cap gets higher score)
            market_cap = price_data.get('marketCap', 0)
            if 1000000 <= market_cap <= 100000000:  # $1M to $100M market cap
                score += 0.2
            elif market_cap > 100000000:  # > $100M market cap
                score += 0.1

            # Liquidity factor (if available)
            liquidity = price_data.get('liquidity', 0)
            if liquidity > 500000:  # $500k+ liquidity
                score += 0.2
            elif liquidity > 100000:  # $100k+ liquidity
                score += 0.1

            # Base score for valid tokens
            score += 0.1

        except Exception as e:
            logger.warning(f"Error calculating opportunity score: {e}")
            score = 0.1  # Minimum score

        return min(score, 1.0)  # Cap at 1.0

    async def get_token_analysis(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed analysis for a specific token.

        Args:
            token_address: Token address to analyze

        Returns:
            Token analysis data
        """
        try:
            # Get comprehensive token data
            price_data = await self.client.get_token_price(token_address)
            metadata = await self.client.get_token_metadata(token_address)
            markets = await self.client.get_token_markets(token_address)

            if not price_data or not metadata:
                return None

            analysis = {
                'token_address': token_address,
                'symbol': metadata.get('symbol', 'UNKNOWN'),
                'name': metadata.get('name', 'Unknown Token'),
                'price': price_data.get('value', 0),
                'price_change_24h': price_data.get('priceChange24h', 0),
                'volume_24h': price_data.get('volume24h', 0),
                'market_cap': price_data.get('marketCap', 0),
                'liquidity': price_data.get('liquidity', 0),
                'markets': markets.get('data', []) if markets else [],
                'score': self._calculate_opportunity_score(price_data, metadata),
                'timestamp': datetime.now().isoformat()
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing token {token_address}: {e}")
            return None

    async def _get_fallback_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get fallback trading opportunities when API fails.

        Args:
            limit: Maximum number of opportunities to return

        Returns:
            List of fallback trading opportunities
        """
        fallback_opportunities = []

        try:
            # Create mock opportunities for popular tokens
            token_data = [
                {'symbol': 'SOL', 'price': 180.0, 'change': 2.5, 'volume': 1000000, 'mcap': 80000000000},
                {'symbol': 'USDC', 'price': 1.0, 'change': 0.1, 'volume': 500000, 'mcap': 50000000000},
                {'symbol': 'USDT', 'price': 1.0, 'change': -0.1, 'volume': 400000, 'mcap': 45000000000},
                {'symbol': 'BONK', 'price': 0.000025, 'change': 5.2, 'volume': 800000, 'mcap': 1500000000},
                {'symbol': 'JUP', 'price': 1.2, 'change': 3.1, 'volume': 600000, 'mcap': 2000000000},
            ]

            for i, token in enumerate(token_data[:limit]):
                # Calculate a simple score based on price change and volume
                score = min((token['change'] / 10.0) + (token['volume'] / 1000000.0) * 0.1, 1.0)
                score = max(score, 0.1)  # Minimum score

                opportunity = {
                    'token_address': self.popular_tokens[i] if i < len(self.popular_tokens) else f"fallback_{i}",
                    'symbol': token['symbol'],
                    'name': f"{token['symbol']} Token",
                    'price': token['price'],
                    'price_change_24h': token['change'],
                    'volume_24h': token['volume'],
                    'market_cap': token['mcap'],
                    'score': score,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'fallback'
                }

                fallback_opportunities.append(opportunity)

            logger.info(f"Generated {len(fallback_opportunities)} fallback opportunities")
            return fallback_opportunities

        except Exception as e:
            logger.error(f"Error generating fallback opportunities: {e}")
            return []

    async def close(self):
        """Close the scanner and cleanup resources."""
        try:
            # Close any open connections
            if hasattr(self.client, 'close'):
                await self.client.close()
            logger.info("Birdeye scanner closed")
        except Exception as e:
            logger.warning(f"Error closing scanner: {e}")

# Example usage
async def main():
    """Example usage of BirdeyeScanner."""
    scanner = BirdeyeScanner()

    try:
        # Scan for opportunities
        opportunities = await scanner.scan_for_opportunities(limit=5)

        print(f"Found {len(opportunities)} opportunities:")
        for opp in opportunities:
            print(f"  {opp['symbol']}: ${opp['price']:.6f} (Score: {opp['score']:.2f})")

    finally:
        await scanner.close()

if __name__ == "__main__":
    asyncio.run(main())
