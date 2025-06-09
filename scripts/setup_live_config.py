#!/usr/bin/env python3
"""
Live Trading Configuration Setup Assistant
==========================================

Interactive script to help users configure their live trading environment.
Guides through setting up API keys, endpoints, and wallet configuration.
"""

import os
import sys
import json
import getpass
from pathlib import Path
from typing import Dict, Any, Optional

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n🔧 {title}")
    print("-" * 40)

def get_user_input(prompt: str, default: str = "", sensitive: bool = False) -> str:
    """Get user input with optional default and sensitive handling."""
    if default:
        display_prompt = f"{prompt} [{default}]: "
    else:
        display_prompt = f"{prompt}: "
    
    if sensitive:
        value = getpass.getpass(display_prompt)
    else:
        value = input(display_prompt)
    
    return value.strip() if value.strip() else default

def validate_solana_address(address: str) -> bool:
    """Basic validation for Solana address format."""
    if not address:
        return False
    # Basic length check for Solana addresses (typically 32-44 characters)
    return len(address) >= 32 and len(address) <= 44 and address.isalnum()

def setup_quicknode_config() -> Dict[str, str]:
    """Setup QuickNode configuration."""
    print_section("QuickNode Configuration")
    print("QuickNode provides high-performance Solana RPC endpoints.")
    print("Sign up at: https://www.quicknode.com/")
    print("")
    
    config = {}
    
    # RPC URL
    print("1. QuickNode RPC URL:")
    print("   Example: https://your-endpoint.solana-mainnet.quiknode.pro/your-api-key/")
    config["QUICKNODE_RPC_URL"] = get_user_input("Enter your QuickNode RPC URL")
    
    # API Key
    print("\n2. QuickNode API Key:")
    print("   Found in your QuickNode dashboard")
    config["QUICKNODE_API_KEY"] = get_user_input("Enter your QuickNode API key", sensitive=True)
    
    return config

def setup_helius_config() -> Dict[str, str]:
    """Setup Helius configuration."""
    print_section("Helius Configuration")
    print("Helius provides enhanced Solana APIs and RPC services.")
    print("Sign up at: https://www.helius.dev/")
    print("")
    
    config = {}
    
    # API Key
    print("1. Helius API Key:")
    print("   Found in your Helius dashboard")
    api_key = get_user_input("Enter your Helius API key", sensitive=True)
    config["HELIUS_API_KEY"] = api_key
    
    # Construct RPC URL
    if api_key:
        config["HELIUS_RPC_URL"] = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
        config["FALLBACK_RPC_URL"] = config["HELIUS_RPC_URL"]
        print(f"✅ Helius RPC URL configured: {config['HELIUS_RPC_URL']}")
    
    return config

def setup_wallet_config() -> Dict[str, str]:
    """Setup wallet configuration."""
    print_section("Wallet Configuration")
    print("⚠️  WARNING: Your private key will be stored in the .env file.")
    print("⚠️  Ensure this file is secure and never shared!")
    print("")
    
    config = {}
    
    # Wallet address
    print("1. Trading Wallet Address:")
    print("   Your Solana wallet's public key")
    while True:
        address = get_user_input("Enter your wallet address")
        if validate_solana_address(address):
            config["WALLET_ADDRESS"] = address
            break
        else:
            print("❌ Invalid Solana address format. Please try again.")
    
    # Private key
    print("\n2. Trading Wallet Private Key:")
    print("   Your wallet's private key (base58 encoded)")
    print("   ⚠️  This will be stored securely in .env file")
    config["WALLET_PRIVATE_KEY"] = get_user_input("Enter your wallet private key", sensitive=True)
    
    # Keypair path
    print("\n3. Keypair File Path:")
    print("   Optional: Path to JSON keypair file")
    keypair_path = get_user_input("Enter keypair file path", "keys/trading_wallet.json")
    config["KEYPAIR_PATH"] = keypair_path
    
    return config

def setup_telegram_config() -> Dict[str, str]:
    """Setup Telegram bot configuration."""
    print_section("Telegram Alerts Configuration")
    print("Optional: Set up Telegram bot for trading alerts.")
    print("1. Create a bot: Message @BotFather on Telegram")
    print("2. Get your chat ID: Message @userinfobot on Telegram")
    print("")
    
    config = {}
    
    setup_telegram = get_user_input("Set up Telegram alerts? (y/n)", "n").lower() == 'y'
    
    if setup_telegram:
        config["TELEGRAM_BOT_TOKEN"] = get_user_input("Enter your Telegram bot token", sensitive=True)
        config["TELEGRAM_CHAT_ID"] = get_user_input("Enter your Telegram chat ID")
    else:
        config["TELEGRAM_BOT_TOKEN"] = "your_telegram_bot_token_here"
        config["TELEGRAM_CHAT_ID"] = "your_telegram_chat_id_here"
    
    return config

def setup_optional_apis() -> Dict[str, str]:
    """Setup optional API configurations."""
    print_section("Optional API Configuration")
    print("These APIs provide additional market data and features.")
    print("")
    
    config = {}
    
    # Birdeye API
    print("1. Birdeye API (Market data):")
    print("   Sign up at: https://birdeye.so/")
    setup_birdeye = get_user_input("Set up Birdeye API? (y/n)", "n").lower() == 'y'
    if setup_birdeye:
        config["BIRDEYE_API_KEY"] = get_user_input("Enter your Birdeye API key", sensitive=True)
    else:
        config["BIRDEYE_API_KEY"] = "your_birdeye_api_key_here"
    
    # CoinGecko API
    print("\n2. CoinGecko API (Price feeds):")
    print("   Sign up at: https://www.coingecko.com/en/api")
    setup_coingecko = get_user_input("Set up CoinGecko API? (y/n)", "n").lower() == 'y'
    if setup_coingecko:
        config["COINGECKO_API_KEY"] = get_user_input("Enter your CoinGecko API key", sensitive=True)
    else:
        config["COINGECKO_API_KEY"] = "your_coingecko_api_key_here"
    
    return config

def write_env_file(config: Dict[str, str]):
    """Write configuration to .env file."""
    print_section("Writing Configuration")
    
    # Read existing .env file
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
    else:
        print("❌ .env file not found. Please run this script from the project root.")
        return False
    
    # Update environment variables
    updated_content = env_content
    for key, value in config.items():
        if value and not value.startswith("your_"):
            # Replace the line with the new value
            import re
            pattern = f"^{key}=.*$"
            replacement = f"{key}={value}"
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.MULTILINE)
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write(updated_content)
    
    print("✅ Configuration written to .env file")
    return True

def main():
    """Main setup function."""
    print_header("RWA Trading System - Live Configuration Setup")
    print("This assistant will help you configure your live trading environment.")
    print("You'll need API keys from QuickNode, Helius, and your wallet information.")
    print("")
    
    # Check if we're in the right directory
    if not Path("config.yaml").exists():
        print("❌ Error: Please run this script from the project root directory.")
        print("   Current directory:", os.getcwd())
        return 1
    
    # Collect all configuration
    all_config = {}
    
    # Required configurations
    all_config.update(setup_quicknode_config())
    all_config.update(setup_helius_config())
    all_config.update(setup_wallet_config())
    
    # Optional configurations
    all_config.update(setup_telegram_config())
    all_config.update(setup_optional_apis())
    
    # Add default Jito configuration
    all_config["JITO_RPC_URL"] = "https://mainnet.block-engine.jito.wtf/api/v1"
    all_config["USE_JITO"] = "true"
    
    # Write configuration
    if write_env_file(all_config):
        print_section("Setup Complete")
        print("✅ Live trading configuration setup complete!")
        print("")
        print("Next steps:")
        print("1. Run: python3 scripts/validate_live_config.py")
        print("2. Review any warnings or errors")
        print("3. Test connectivity before live trading")
        print("")
        print("⚠️  IMPORTANT: Keep your .env file secure and never share it!")
        return 0
    else:
        print("❌ Failed to write configuration")
        return 1

if __name__ == "__main__":
    exit(main())
