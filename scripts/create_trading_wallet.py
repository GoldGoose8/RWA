#!/usr/bin/env python3
"""
Trading Wallet Generator
========================

Creates a new Solana wallet for trading with proper security measures.
Generates keypair, saves to secure location, and updates configuration.
"""

import os
import sys
import json
import base58
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solana.rpc.api import Client
    from dotenv import load_dotenv, set_key
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    print("Please run: pip3 install solders solana python-dotenv")
    sys.exit(1)

class TradingWalletGenerator:
    """Generates and configures a new trading wallet."""
    
    def __init__(self):
        """Initialize the wallet generator."""
        self.project_root = Path(__file__).parent.parent
        self.keys_dir = self.project_root / "keys"
        self.env_file = self.project_root / ".env"
        
        # Load existing environment
        load_dotenv(self.env_file)
        
    def create_keys_directory(self):
        """Create keys directory if it doesn't exist."""
        self.keys_dir.mkdir(exist_ok=True, mode=0o700)  # Secure permissions
        print(f"✅ Keys directory created: {self.keys_dir}")
        
    def generate_keypair(self) -> Keypair:
        """Generate a new Solana keypair."""
        print("🔐 Generating new Solana keypair...")
        keypair = Keypair()
        print(f"✅ New keypair generated")
        return keypair
        
    def save_keypair_json(self, keypair: Keypair, filename: str = "trading_wallet.json") -> Path:
        """Save keypair to JSON file in Solana CLI format."""
        keypair_path = self.keys_dir / filename
        
        # Convert to Solana CLI format (array of bytes)
        private_key_bytes = list(keypair.secret())
        
        # Save to JSON file
        with open(keypair_path, 'w') as f:
            json.dump(private_key_bytes, f)
        
        # Set secure permissions
        os.chmod(keypair_path, 0o600)
        
        print(f"✅ Keypair saved to: {keypair_path}")
        return keypair_path
        
    def update_env_file(self, keypair: Keypair, keypair_path: Path):
        """Update .env file with wallet information."""
        print("📝 Updating .env file with wallet configuration...")
        
        # Get wallet address and private key
        wallet_address = str(keypair.pubkey())
        private_key_base58 = base58.b58encode(keypair.secret()).decode('utf-8')
        
        # Update .env file
        set_key(self.env_file, "WALLET_ADDRESS", wallet_address)
        set_key(self.env_file, "WALLET_PRIVATE_KEY", private_key_base58)
        set_key(self.env_file, "KEYPAIR_PATH", str(keypair_path))
        
        print(f"✅ Updated .env file:")
        print(f"   WALLET_ADDRESS={wallet_address}")
        print(f"   WALLET_PRIVATE_KEY=***HIDDEN***")
        print(f"   KEYPAIR_PATH={keypair_path}")
        
    def test_wallet_connection(self, keypair: Keypair) -> Dict[str, Any]:
        """Test wallet connection using available RPC endpoints."""
        print("🔍 Testing wallet connection...")
        
        wallet_address = str(keypair.pubkey())
        results = {}
        
        # Try Helius RPC first (since it's configured)
        helius_url = os.getenv("HELIUS_RPC_URL")
        if helius_url and "your_" not in helius_url:
            try:
                client = Client(helius_url)
                balance_response = client.get_balance(keypair.pubkey())
                balance_lamports = balance_response.value
                balance_sol = balance_lamports / 1_000_000_000
                
                results["helius"] = {
                    "status": "success",
                    "balance_lamports": balance_lamports,
                    "balance_sol": balance_sol,
                    "endpoint": helius_url
                }
                print(f"✅ Helius RPC: Wallet balance = {balance_sol:.9f} SOL")
                
            except Exception as e:
                results["helius"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"❌ Helius RPC error: {e}")
        
        # Try public RPC as fallback
        try:
            public_client = Client("https://api.mainnet-beta.solana.com")
            balance_response = public_client.get_balance(keypair.pubkey())
            balance_lamports = balance_response.value
            balance_sol = balance_lamports / 1_000_000_000
            
            results["public_rpc"] = {
                "status": "success",
                "balance_lamports": balance_lamports,
                "balance_sol": balance_sol,
                "endpoint": "https://api.mainnet-beta.solana.com"
            }
            print(f"✅ Public RPC: Wallet balance = {balance_sol:.9f} SOL")
            
        except Exception as e:
            results["public_rpc"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ Public RPC error: {e}")
            
        return results
        
    def display_wallet_info(self, keypair: Keypair):
        """Display wallet information and important notes."""
        wallet_address = str(keypair.pubkey())
        
        print("\n" + "=" * 60)
        print("🎉 TRADING WALLET CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📍 Wallet Address: {wallet_address}")
        print(f"🔐 Private Key: ***SECURELY STORED***")
        print(f"📁 Keypair File: {self.keys_dir}/trading_wallet.json")
        print(f"⚙️ Configuration: Updated in .env file")
        
        print("\n🚨 IMPORTANT SECURITY NOTES:")
        print("1. 🔒 Private key is stored securely in keys/ directory")
        print("2. 🚫 Never share your private key with anyone")
        print("3. 💾 Backup your keypair file to a secure location")
        print("4. 🔐 Keys directory has restricted permissions (700)")
        print("5. 📝 .env file contains wallet configuration")
        
        print("\n💰 FUNDING YOUR WALLET:")
        print("1. 📤 Send SOL to this address for trading")
        print("2. 💡 Recommended: Start with 1-2 SOL for testing")
        print("3. ⚠️ This is a MAINNET wallet - use real SOL")
        print("4. 🔍 Check balance at: https://explorer.solana.com/")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Fund your wallet with SOL")
        print("2. Configure QuickNode RPC endpoint")
        print("3. Run: python3 scripts/validate_live_config.py")
        print("4. Start trading: python3 scripts/unified_live_trading.py")
        
        print("=" * 60)
        
    def create_backup_info(self, keypair: Keypair) -> Dict[str, str]:
        """Create backup information for the wallet."""
        wallet_address = str(keypair.pubkey())
        private_key_base58 = base58.b58encode(keypair.secret()).decode('utf-8')
        
        backup_info = {
            "wallet_address": wallet_address,
            "private_key_base58": private_key_base58,
            "keypair_path": str(self.keys_dir / "trading_wallet.json"),
            "created_at": str(Path(__file__).stat().st_mtime),
            "network": "mainnet-beta",
            "purpose": "RWA Trading System",
            "security_note": "Keep this information secure and never share the private key"
        }
        
        # Save backup info (without private key for security)
        backup_info_safe = backup_info.copy()
        backup_info_safe["private_key_base58"] = "***STORED_IN_KEYPAIR_FILE***"
        
        backup_path = self.keys_dir / "wallet_info.json"
        with open(backup_path, 'w') as f:
            json.dump(backup_info_safe, f, indent=2)
        
        os.chmod(backup_path, 0o600)
        print(f"✅ Wallet info saved to: {backup_path}")
        
        return backup_info

def main():
    """Main wallet generation function."""
    print("🚀 RWA Trading System - Wallet Generator")
    print("=" * 50)
    print("Creating a new Solana wallet for live trading...")
    print("")
    
    # Check if wallet already exists
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        existing_address = os.getenv("WALLET_ADDRESS")
        if existing_address and "your_" not in existing_address:
            print(f"⚠️ Existing wallet found: {existing_address}")
            response = input("Do you want to create a new wallet? This will replace the existing one. (y/N): ")
            if response.lower() != 'y':
                print("❌ Wallet creation cancelled.")
                return 1
    
    try:
        # Initialize generator
        generator = TradingWalletGenerator()
        
        # Create keys directory
        generator.create_keys_directory()
        
        # Generate new keypair
        keypair = generator.generate_keypair()
        
        # Save keypair to file
        keypair_path = generator.save_keypair_json(keypair)
        
        # Update .env file
        generator.update_env_file(keypair, keypair_path)
        
        # Test wallet connection
        connection_results = generator.test_wallet_connection(keypair)
        
        # Create backup info
        backup_info = generator.create_backup_info(keypair)
        
        # Display wallet information
        generator.display_wallet_info(keypair)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error creating wallet: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
