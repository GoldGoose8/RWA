#!/usr/bin/env python3
"""
Fix the keypair file from the private key in .env
"""

import os
import json
import base58
from dotenv import load_dotenv
from solders.keypair import Keypair

# Load environment variables
load_dotenv()

def fix_keypair():
    """Fix the keypair file."""
    print("🔧 Fixing Keypair File")
    print("=" * 30)
    
    # Get private key from .env
    private_key_str = os.getenv('WALLET_PRIVATE_KEY')
    wallet_address = os.getenv('WALLET_ADDRESS')
    
    if not private_key_str:
        print("❌ WALLET_PRIVATE_KEY not found in .env")
        return False
    
    if not wallet_address:
        print("❌ WALLET_ADDRESS not found in .env")
        return False
    
    print(f"Wallet Address: {wallet_address}")
    print(f"Private Key: {private_key_str[:10]}...{private_key_str[-10:]}")
    
    try:
        # Decode the base58 private key
        private_key_bytes = base58.b58decode(private_key_str)
        print(f"✅ Decoded private key: {len(private_key_bytes)} bytes")
        
        # Create keypair from private key
        keypair = Keypair.from_bytes(private_key_bytes)
        print(f"✅ Created keypair")
        
        # Verify the public key matches
        derived_address = str(keypair.pubkey())
        print(f"Derived Address: {derived_address}")
        
        if derived_address == wallet_address:
            print("✅ Address matches!")
        else:
            print(f"❌ Address mismatch!")
            print(f"   Expected: {wallet_address}")
            print(f"   Derived:  {derived_address}")
            return False
        
        # Convert to the format expected by the system (64-byte array)
        keypair_bytes = bytes(keypair)
        keypair_array = list(keypair_bytes)
        
        print(f"✅ Keypair array: {len(keypair_array)} bytes")
        
        # Save to file
        keypair_path = 'wallet/trading_wallet_keypair.json'
        os.makedirs(os.path.dirname(keypair_path), exist_ok=True)
        
        with open(keypair_path, 'w') as f:
            json.dump(keypair_array, f)
        
        # Set proper permissions
        os.chmod(keypair_path, 0o600)
        
        print(f"✅ Saved keypair to {keypair_path}")
        print(f"✅ Set permissions to 600")
        
        # Test loading the keypair
        print("\n🧪 Testing keypair loading...")
        with open(keypair_path, 'r') as f:
            loaded_array = json.load(f)
        
        test_keypair = Keypair.from_bytes(bytes(loaded_array))
        test_address = str(test_keypair.pubkey())
        
        if test_address == wallet_address:
            print("✅ Keypair loads correctly!")
            return True
        else:
            print("❌ Keypair loading test failed!")
            return False
        
    except Exception as e:
        print(f"❌ Error fixing keypair: {e}")
        return False

if __name__ == "__main__":
    success = fix_keypair()
    if success:
        print("\n🎉 Keypair fixed successfully!")
    else:
        print("\n❌ Failed to fix keypair!")
    exit(0 if success else 1)
