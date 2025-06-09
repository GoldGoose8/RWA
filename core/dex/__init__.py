"""
DEX Integration Package
Provides simplified transaction building for decentralized exchanges.
"""

from core.dex.unified_transaction_builder import UnifiedTransactionBuilder

# Common Solana token addresses
COMMON_TOKENS = {
    'SOL': 'So11111111111111111111111111111111111111112',
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'BONK': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
    'JUP': 'JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN',
    'RAY': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R'
}

def get_token_mint(symbol: str) -> str:
    """Get token mint address by symbol."""
    return COMMON_TOKENS.get(symbol.upper(), symbol)

__all__ = [
    "UnifiedTransactionBuilder",
    "get_token_mint",
    "COMMON_TOKENS"
]
