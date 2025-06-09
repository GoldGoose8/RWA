#!/usr/bin/env python3
"""
Token Account Setup Guide
=========================

Provides information about WSOL and USDC token accounts for trading.
Shows how to create them using Jupiter or other DEX interfaces.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    from solders.pubkey import Pubkey
    from solana.rpc.api import Client
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    print("Please run: pip3 install python-dotenv")
    sys.exit(1)

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n🔧 {title}")
    print("-" * 40)

def get_wallet_info():
    """Get wallet information from environment."""
    load_dotenv()

    wallet_address = os.getenv("WALLET_ADDRESS")
    if not wallet_address or "your_" in wallet_address:
        print("❌ Wallet address not configured in .env file")
        return None

    return wallet_address

def show_token_info():
    """Show information about required token accounts."""
    print_section("Required Token Accounts for Trading")

    tokens = {
        "WSOL": {
            "mint": "So11111111111111111111111111111111111111112",
            "name": "Wrapped SOL",
            "description": "Wrapped version of SOL for SPL token trading",
            "required": True
        },
        "USDC": {
            "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "name": "USD Coin",
            "description": "Stablecoin pegged to USD",
            "required": True
        },
        "USDT": {
            "mint": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "name": "Tether USD",
            "description": "Another stablecoin option",
            "required": False
        }
    }

    for symbol, info in tokens.items():
        status = "🔴 REQUIRED" if info["required"] else "🟡 OPTIONAL"
        print(f"{status} {symbol} ({info['name']})")
        print(f"   Mint: {info['mint']}")
        print(f"   Use: {info['description']}")
        print()

    return tokens

def show_creation_methods():
    """Show different methods to create token accounts."""
    print_section("How to Create Token Accounts")

    print("🎯 RECOMMENDED METHOD: Use Jupiter DEX Interface")
    print("1. 🌐 Go to: https://jup.ag/")
    print("2. 🔗 Connect your wallet")
    print("3. 💱 Try to swap SOL → USDC (small amount)")
    print("4. ✅ Jupiter will automatically create USDC account")
    print("5. 💱 Try to swap SOL → WSOL (small amount)")
    print("6. ✅ Jupiter will automatically create WSOL account")
    print()

    print("🔧 ALTERNATIVE METHOD: Use Solana CLI")
    print("1. 📥 Install Solana CLI: https://docs.solana.com/cli/install-solana-cli-tools")
    print("2. 🔑 Import your wallet: solana config set --keypair /path/to/keypair.json")
    print("3. 🏦 Create USDC account: spl-token create-account EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    print("4. 🏦 Create WSOL account: spl-token create-account So11111111111111111111111111111111111111112")
    print()

    print("💡 EASIEST METHOD: Fund wallet and start trading")
    print("1. 💰 Send SOL to your wallet")
    print("2. 🚀 Start the trading system")
    print("3. ✅ System will create accounts automatically during first trades")

def show_wallet_funding_info():
    """Show wallet funding information."""
    wallet_address = get_wallet_info()
    if not wallet_address:
        return

    print_section("Wallet Funding Information")

    print(f"📍 Your Trading Wallet: {wallet_address}")
    print(f"🔍 Explorer: https://explorer.solana.com/address/{wallet_address}")
    print()

    print("💰 FUNDING RECOMMENDATIONS:")
    print("• 🧪 Testing: 0.5 - 1 SOL")
    print("• 📈 Small trading: 1 - 5 SOL")
    print("• 💼 Serious trading: 5+ SOL")
    print()

    print("⚠️ IMPORTANT NOTES:")
    print("• 🔒 This is a MAINNET wallet - use real SOL")
    print("• 💸 Keep transaction fees in mind (~0.000005 SOL per transaction)")
    print("• 🛡️ Start small and test the system first")
    print("• 📊 Monitor your trades through the dashboard")

def save_token_info():
    """Save token information to file."""
    wallet_address = get_wallet_info()
    if not wallet_address:
        return

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    token_info = {
        "wallet_address": wallet_address,
        "required_tokens": {
            "WSOL": {
                "mint": "So11111111111111111111111111111111111111112",
                "name": "Wrapped SOL",
                "required": True,
                "creation_method": "Jupiter DEX or first trade"
            },
            "USDC": {
                "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "name": "USD Coin",
                "required": True,
                "creation_method": "Jupiter DEX or first trade"
            }
        },
        "creation_urls": {
            "jupiter": "https://jup.ag/",
            "explorer": f"https://explorer.solana.com/address/{wallet_address}",
            "solana_cli": "https://docs.solana.com/cli/install-solana-cli-tools"
        },
        "notes": [
            "Token accounts are created automatically during first trades",
            "Jupiter DEX is the easiest way to create accounts",
            "Each account creation costs ~0.002 SOL",
            "Accounts persist until manually closed"
        ]
    }

    output_file = output_dir / "token_account_info.json"
    with open(output_file, 'w') as f:
        json.dump(token_info, f, indent=2)

    print(f"💾 Token information saved to: {output_file}")

def main():
    """Main function."""
    print_header("RWA Trading System - Token Account Setup Guide")

    # Show wallet info
    wallet_address = get_wallet_info()
    if not wallet_address:
        print("❌ Please configure your wallet first using:")
        print("   python3 scripts/create_trading_wallet.py")
        return 1

    # Show token information
    show_token_info()

    # Show creation methods
    show_creation_methods()

    # Show funding info
    show_wallet_funding_info()

    # Save information
    save_token_info()

    print_header("Summary")
    print("🎯 QUICK START:")
    print("1. 💰 Fund your wallet with 1-2 SOL")
    print("2. 🌐 Go to https://jup.ag/ and connect wallet")
    print("3. 💱 Make a small SOL → USDC swap")
    print("4. 💱 Make a small SOL → WSOL swap")
    print("5. ✅ Token accounts created automatically!")
    print("6. 🚀 Start live trading system")
    print()
    print("💡 Or just fund wallet and let the trading system create accounts automatically!")

    return 0

if __name__ == "__main__":
    exit(main())
