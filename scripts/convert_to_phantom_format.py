#!/usr/bin/env python3
"""
Convert Native Wallet to Phantom Format
=======================================

Converts the native Solana wallet private key to Phantom wallet format.
"""

import os
import sys
import json
import base58
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

def convert_to_phantom_format():
    """Convert native wallet private key to Phantom format."""
    try:
        # Get wallet info from environment
        wallet_address = os.getenv('WALLET_ADDRESS')
        private_key_base58 = os.getenv('WALLET_PRIVATE_KEY')
        
        if not wallet_address or not private_key_base58:
            print("❌ No native wallet found in environment")
            print("💡 Create one first: python3 scripts/create_native_solana_wallet.py")
            return
        
        print("🔐 NATIVE WALLET TO PHANTOM FORMAT CONVERTER")
        print("=" * 70)
        print(f"📍 Wallet Address: {wallet_address}")
        print()
        
        # Decode base58 private key to bytes
        private_key_bytes = base58.b58decode(private_key_base58)
        
        # Convert to different formats
        private_key_array = list(private_key_bytes)

        print("🔑 PHANTOM WALLET IMPORT FORMATS:")
        print("=" * 70)
        print()
        print("FORMAT 1: Base58 String (Recommended for Phantom)")
        print("Copy this string:")
        print(f"{private_key_base58}")
        print()
        print("FORMAT 2: Byte Array (Alternative)")
        print("Copy this array:")
        print(json.dumps(private_key_array))
        print()
        print("FORMAT 3: Hex String")
        hex_string = private_key_bytes.hex()
        print(f"{hex_string}")
        print()
        print("=" * 70)
        print()

        print("📋 PHANTOM WALLET IMPORT INSTRUCTIONS:")
        print("1. Open Phantom wallet")
        print("2. Click 'Add / Connect Wallet'")
        print("3. Select 'Import Private Key'")
        print("4. Try FORMAT 1 first (base58 string)")
        print("5. If that doesn't work, try FORMAT 2 (array)")
        print("6. Name your wallet (e.g., 'Trading Wallet')")
        print("7. Click 'Import'")
        print()
        
        print("🔒 SECURITY NOTES:")
        print("• This private key gives full access to the wallet")
        print("• Never share this private key with anyone")
        print("• Only import into trusted wallet applications")
        print("• Consider this a hot wallet for trading only")
        print()
        
        print("✅ VERIFICATION:")
        print(f"After importing, verify the wallet address matches:")
        print(f"Expected: {wallet_address}")
        print()
        
        # Also save to file for easy copying
        output_file = project_root / 'keys' / 'phantom_import_format.json'
        with open(output_file, 'w') as f:
            json.dump({
                'wallet_address': wallet_address,
                'private_key_base58': private_key_base58,
                'private_key_array': private_key_array,
                'private_key_hex': hex_string,
                'instructions': [
                    'Try private_key_base58 first (most common format)',
                    'If that fails, try private_key_array',
                    'This is the same wallet as your native trading wallet',
                    'Address should match the wallet_address field above'
                ]
            }, f, indent=2)
        
        print(f"💾 Format also saved to: {output_file}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error converting to Phantom format: {e}")

def main():
    """Main function."""
    convert_to_phantom_format()

if __name__ == "__main__":
    main()
