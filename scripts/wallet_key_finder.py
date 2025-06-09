#!/usr/bin/env python3
"""
Wallet Private Key Finder
=========================

This script helps find the private key for the currently active trading wallet.
"""

import os
import sys
import json
import base58
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_current_wallet_address():
    """Get current active wallet address."""
    try:
        trade_dir = Path('backups/trades_backup_20250531_175013')
        trade_files = sorted(trade_dir.glob('trade_*.json'))
        if trade_files:
            with open(trade_files[-1], 'r') as f:
                trade_data = json.load(f)
            return trade_data.get('wallet_address')
    except:
        pass
    return None

def check_keypair_files():
    """Check existing keypair files."""
    current_wallet = get_current_wallet_address()
    
    print("🔍 CHECKING EXISTING KEYPAIR FILES")
    print("=" * 50)
    print(f"Target Wallet: {current_wallet}")
    print()
    
    keys_dir = Path('keys')
    if not keys_dir.exists():
        print("❌ No keys directory found")
        return None
        
    keypair_files = list(keys_dir.glob('*.json'))
    
    for keypair_file in keypair_files:
        try:
            print(f"📄 Checking: {keypair_file.name}")
            
            with open(keypair_file, 'r') as f:
                content = f.read().strip()
            
            # Try to parse as JSON array (Solana keypair format)
            try:
                keypair_data = json.loads(content)
                if isinstance(keypair_data, list) and len(keypair_data) == 64:
                    # This is a Solana keypair array
                    from solders.keypair import Keypair
                    keypair = Keypair.from_bytes(bytes(keypair_data))
                    wallet_address = str(keypair.pubkey())
                    
                    print(f"   Address: {wallet_address}")
                    if wallet_address == current_wallet:
                        print("   ✅ MATCH! This is the current trading wallet")
                        
                        # Convert to base58 private key
                        private_key_base58 = base58.b58encode(bytes(keypair_data[:32])).decode()
                        print(f"   Private Key: {private_key_base58}")
                        return {
                            'address': wallet_address,
                            'private_key': private_key_base58,
                            'keypair_file': str(keypair_file)
                        }
                    else:
                        print("   ❌ Different wallet")
                        
            except json.JSONDecodeError:
                # Try to parse as JSON object
                try:
                    wallet_info = json.loads(content)
                    if 'wallet_address' in wallet_info:
                        print(f"   Address: {wallet_info['wallet_address']}")
                        if wallet_info['wallet_address'] == current_wallet:
                            print("   ✅ MATCH! This is the current trading wallet")
                            return wallet_info
                        else:
                            print("   ❌ Different wallet")
                except:
                    print("   ❓ Unknown format")
                    
        except Exception as e:
            print(f"   ❌ Error reading {keypair_file}: {e}")
        
        print()
    
    return None

def search_for_private_key():
    """Search for the private key in various locations."""
    current_wallet = get_current_wallet_address()
    
    print("🔍 SEARCHING FOR PRIVATE KEY")
    print("=" * 50)
    print(f"Target Wallet: {current_wallet}")
    print()
    
    # Check environment variables
    env_private_key = os.getenv('WALLET_PRIVATE_KEY')
    if env_private_key and env_private_key != 'your_private_key_for_9wPBNeDnNbeP593cDJ12qUeQtGPEzJUyo5cm8hUB6tkc':
        print("🔑 Found private key in environment variable")
        try:
            # Try to derive address from private key
            import base58
            from solders.keypair import Keypair
            
            private_key_bytes = base58.b58decode(env_private_key)
            keypair = Keypair.from_bytes(private_key_bytes)
            derived_address = str(keypair.pubkey())
            
            print(f"   Derived Address: {derived_address}")
            if derived_address == current_wallet:
                print("   ✅ MATCH! Environment variable has correct private key")
                return {
                    'address': derived_address,
                    'private_key': env_private_key,
                    'source': 'environment'
                }
            else:
                print("   ❌ Environment variable has different wallet's private key")
        except Exception as e:
            print(f"   ❌ Error validating environment private key: {e}")
    
    # Check keypair files
    keypair_result = check_keypair_files()
    if keypair_result:
        return keypair_result
    
    print("❌ Private key not found in any checked locations")
    return None

def generate_recommendations():
    """Generate recommendations for next steps."""
    current_wallet = get_current_wallet_address()
    
    print("💡 RECOMMENDATIONS")
    print("=" * 50)
    print()
    print("Since the private key for the current trading wallet was not found,")
    print("you have several options:")
    print()
    print("1. 🔍 FIND THE PRIVATE KEY:")
    print("   - Check your wallet software (Phantom, Solflare, etc.)")
    print("   - Look for backup files or seed phrases")
    print("   - Check other configuration files")
    print()
    print("2. 🔄 SWITCH TO A KNOWN WALLET:")
    print("   - Use one of the wallets with known private keys")
    print("   - Transfer funds from current wallet to known wallet")
    print("   - Update system to use the known wallet")
    print()
    print("3. 🆕 CREATE NEW WALLET:")
    print("   - Generate a new trading wallet")
    print("   - Transfer funds from current wallet")
    print("   - Update all configurations")
    print()
    print("4. 🔒 IMPORT CURRENT WALLET:")
    print("   - If you have the seed phrase or private key")
    print("   - Import into the system")
    print("   - Update .env file")
    print()
    print(f"Current wallet explorer:")
    print(f"https://explorer.solana.com/address/{current_wallet}")

def main():
    """Main function."""
    print("🔑 WALLET PRIVATE KEY FINDER")
    print("=" * 60)
    print()
    
    current_wallet = get_current_wallet_address()
    if not current_wallet:
        print("❌ Could not determine current trading wallet")
        return
    
    # Search for private key
    result = search_for_private_key()
    
    if result:
        print("🎉 SUCCESS!")
        print("=" * 50)
        print(f"Wallet Address: {result['address']}")
        print(f"Private Key: {result['private_key']}")
        print(f"Source: {result.get('source', result.get('keypair_file', 'unknown'))}")
        print()
        print("✅ You can now update your .env file with this private key")
    else:
        generate_recommendations()

if __name__ == "__main__":
    main()
