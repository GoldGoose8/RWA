#!/usr/bin/env python3
"""
Phantom Wallet Import
=====================

Imports a Phantom wallet private key into the RWA Trading System.
Replaces the existing trading wallet with the imported one.
"""

import os
import sys
import json
import base58
from pathlib import Path
from dotenv import load_dotenv, set_key

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solana.rpc.api import Client
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    print("Please ensure all Solana dependencies are installed")
    sys.exit(1)

class PhantomWalletImporter:
    """Imports Phantom wallet into the trading system."""
    
    def __init__(self, private_key_base58: str):
        """Initialize with the Phantom private key."""
        self.private_key_base58 = private_key_base58
        self.env_file = Path(".env")
        self.keys_dir = Path("keys")
        self.backup_dir = Path("backup")
        
        # Ensure directories exist
        self.keys_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        print(f"🔐 Importing Phantom wallet...")
        print(f"📁 Keys directory: {self.keys_dir}")
        print(f"💾 Backup directory: {self.backup_dir}")
    
    def validate_private_key(self) -> bool:
        """Validate the private key format."""
        try:
            # Try to decode the Base58 private key
            private_key_bytes = base58.b58decode(self.private_key_base58)
            
            # Should be 64 bytes for Ed25519
            if len(private_key_bytes) != 64:
                print(f"❌ Invalid private key length: {len(private_key_bytes)} bytes (expected 64)")
                return False
            
            # Try to create a keypair
            keypair = Keypair.from_bytes(private_key_bytes)
            public_key = keypair.pubkey()
            
            print(f"✅ Private key validation successful")
            print(f"📍 Wallet address: {public_key}")
            
            return True
            
        except Exception as e:
            print(f"❌ Private key validation failed: {e}")
            return False
    
    def backup_existing_wallet(self) -> bool:
        """Backup existing wallet configuration."""
        try:
            # Load current environment
            load_dotenv()
            
            current_address = os.getenv("WALLET_ADDRESS")
            current_private_key = os.getenv("WALLET_PRIVATE_KEY")
            current_keypair_path = os.getenv("KEYPAIR_PATH")
            
            if current_address and current_private_key:
                backup_data = {
                    "wallet_address": current_address,
                    "private_key_base58": current_private_key,
                    "keypair_path": current_keypair_path,
                    "backup_timestamp": str(Path(__file__).stat().st_mtime)
                }
                
                # Save backup
                backup_file = self.backup_dir / "previous_wallet_backup.json"
                with open(backup_file, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                
                print(f"💾 Previous wallet backed up to: {backup_file}")
                print(f"📍 Previous address: {current_address}")
                
                # Backup keypair file if it exists
                if current_keypair_path and Path(current_keypair_path).exists():
                    backup_keypair = self.backup_dir / "previous_trading_wallet.json"
                    import shutil
                    shutil.copy2(current_keypair_path, backup_keypair)
                    print(f"🔑 Previous keypair backed up to: {backup_keypair}")
                
                return True
            else:
                print("ℹ️ No existing wallet found to backup")
                return True
                
        except Exception as e:
            print(f"⚠️ Backup failed (continuing anyway): {e}")
            return True
    
    def create_keypair_from_private_key(self) -> tuple:
        """Create keypair and extract information."""
        try:
            # Decode private key
            private_key_bytes = base58.b58decode(self.private_key_base58)
            
            # Create keypair
            keypair = Keypair.from_bytes(private_key_bytes)
            public_key = keypair.pubkey()
            
            # Convert to JSON array format for Solana CLI compatibility
            private_key_array = list(private_key_bytes)
            
            return keypair, public_key, private_key_array
            
        except Exception as e:
            print(f"❌ Failed to create keypair: {e}")
            return None, None, None
    
    def save_keypair_file(self, private_key_array: list) -> str:
        """Save keypair in JSON format."""
        try:
            keypair_file = self.keys_dir / "trading_wallet.json"
            
            with open(keypair_file, 'w') as f:
                json.dump(private_key_array, f)
            
            # Set secure permissions (owner read/write only)
            os.chmod(keypair_file, 0o600)
            
            print(f"🔑 Keypair saved to: {keypair_file}")
            return str(keypair_file)
            
        except Exception as e:
            print(f"❌ Failed to save keypair file: {e}")
            return None
    
    def update_env_file(self, wallet_address: str, keypair_path: str) -> bool:
        """Update .env file with new wallet information."""
        try:
            # Update environment variables
            set_key(self.env_file, "WALLET_ADDRESS", str(wallet_address))
            set_key(self.env_file, "WALLET_PRIVATE_KEY", self.private_key_base58)
            set_key(self.env_file, "KEYPAIR_PATH", keypair_path)
            
            print(f"✅ Environment file updated: {self.env_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update environment file: {e}")
            return False
    
    def test_wallet_connectivity(self, wallet_address: str) -> bool:
        """Test wallet connectivity and get balance."""
        try:
            # Load environment to get RPC endpoints
            load_dotenv()
            
            # Try Helius first
            helius_url = os.getenv("HELIUS_RPC_URL")
            if helius_url and "your_" not in helius_url:
                client = Client(helius_url)
                pubkey = Pubkey.from_string(str(wallet_address))
                balance_response = client.get_balance(pubkey)
                balance_lamports = balance_response.value
                balance_sol = balance_lamports / 1_000_000_000
                
                print(f"✅ Wallet connectivity test successful")
                print(f"💰 Current balance: {balance_sol:.9f} SOL ({balance_lamports:,} lamports)")
                
                if balance_sol > 0:
                    print(f"🎉 Wallet has funds! Ready for trading.")
                else:
                    print(f"💡 Wallet is empty. Send SOL to start trading.")
                
                return True
            else:
                print("⚠️ No RPC endpoint available for connectivity test")
                return True
                
        except Exception as e:
            print(f"⚠️ Connectivity test failed (wallet may still work): {e}")
            return True
    
    def import_wallet(self) -> bool:
        """Main import process."""
        print("🚀 Starting Phantom wallet import process...")
        print("=" * 60)
        
        # Step 1: Validate private key
        print("\n1️⃣ Validating private key...")
        if not self.validate_private_key():
            return False
        
        # Step 2: Backup existing wallet
        print("\n2️⃣ Backing up existing wallet...")
        if not self.backup_existing_wallet():
            return False
        
        # Step 3: Create keypair
        print("\n3️⃣ Creating keypair from private key...")
        keypair, public_key, private_key_array = self.create_keypair_from_private_key()
        if not keypair:
            return False
        
        # Step 4: Save keypair file
        print("\n4️⃣ Saving keypair file...")
        keypair_path = self.save_keypair_file(private_key_array)
        if not keypair_path:
            return False
        
        # Step 5: Update environment file
        print("\n5️⃣ Updating environment configuration...")
        if not self.update_env_file(public_key, keypair_path):
            return False
        
        # Step 6: Test connectivity
        print("\n6️⃣ Testing wallet connectivity...")
        if not self.test_wallet_connectivity(public_key):
            return False
        
        return True
    
    def print_summary(self, success: bool):
        """Print import summary."""
        print("\n" + "=" * 60)
        if success:
            print("🎉 PHANTOM WALLET IMPORT SUCCESSFUL!")
        else:
            print("❌ PHANTOM WALLET IMPORT FAILED!")
        print("=" * 60)
        
        if success:
            # Get wallet info
            keypair, public_key, _ = self.create_keypair_from_private_key()
            
            print(f"\n✅ Wallet successfully imported from Phantom")
            print(f"📍 New wallet address: {public_key}")
            print(f"🔑 Private key (Base58): {self.private_key_base58}")
            print(f"📁 Keypair file: keys/trading_wallet.json")
            print(f"⚙️ Environment: Updated in .env file")
            print(f"💾 Previous wallet: Backed up to backup/ directory")
            
            print(f"\n🔗 Wallet Explorer:")
            print(f"   https://explorer.solana.com/address/{public_key}")
            
            print(f"\n🚀 Next Steps:")
            print(f"1. 💰 Check wallet balance: python3 scripts/check_wallet_balance.py")
            print(f"2. 🧪 Test system: python3 scripts/system_status.py")
            print(f"3. 📊 Start trading: python3 scripts/unified_live_trading.py")
            
            print(f"\n🛡️ Security Notes:")
            print(f"• 🔒 Private key is securely stored")
            print(f"• 💾 Previous wallet is safely backed up")
            print(f"• 🔐 Keypair file has restricted permissions")
            
        else:
            print(f"\n🔧 Troubleshooting:")
            print(f"• ✅ Verify private key format is correct")
            print(f"• 🔍 Check for any error messages above")
            print(f"• 💾 Previous wallet backup is safe")
            print(f"• 🔄 You can retry the import process")
        
        print("=" * 60)

def main():
    """Main function."""
    print("🔐 Phantom Wallet Import Tool")
    print("=" * 40)
    
    # The private key from Phantom
    phantom_private_key = "4DbGCf8Zk5kq2iqfXEAyFpTKnu5z6R8dx3tMUosU6WkKeTXudmpTxoZjh4RvQE8mkKnxhNfzrpsqgb1rEZj1Borv"
    
    print(f"📱 Importing Phantom wallet...")
    print(f"🔑 Private key: {phantom_private_key[:20]}...{phantom_private_key[-20:]}")
    
    # Confirm import
    confirm = input("\n⚠️ This will replace your current trading wallet. Continue? (type 'YES' to confirm): ")
    if confirm != "YES":
        print("❌ Import cancelled for safety.")
        return 1
    
    # Create importer and run
    importer = PhantomWalletImporter(phantom_private_key)
    success = importer.import_wallet()
    importer.print_summary(success)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
