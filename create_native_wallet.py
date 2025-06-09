#!/usr/bin/env python3
"""
Create Native Solana Wallet for RWA Trading System

This script creates a new native Solana keypair and displays the private key
for importing into Phantom wallet.
"""

import os
import sys
import base58
from solders.keypair import Keypair

def create_native_wallet():
    """Create a new native Solana wallet."""
    print("🔑 Creating new native Solana wallet for RWA Trading System...")
    
    # Generate new keypair
    keypair = Keypair()
    
    # Get public and private keys
    public_key = str(keypair.pubkey())
    private_key_bytes = bytes(keypair)
    private_key = base58.b58encode(private_key_bytes).decode('utf-8')
    
    # Display wallet information
    print(f"\n✅ New wallet created successfully!")
    print(f"📍 Public Key (Wallet Address): {public_key}")
    print(f"🔐 Private Key (for Phantom import): {private_key}")
    
    print(f"\n📋 Next steps:")
    print(f"1. Copy the private key above and import it into Phantom wallet")
    print(f"2. Fund the wallet address: {public_key}")
    print(f"3. Update your .env file with:")
    print(f"   WALLET_ADDRESS={public_key}")
    print(f"   WALLET_PRIVATE_KEY={private_key}")
    print(f"4. Run live trading to test with real transactions")
    
    # Save to .env format for easy copying
    env_content = f"""
# Native Wallet Configuration for RWA Trading System
WALLET_ADDRESS={public_key}
WALLET_PRIVATE_KEY={private_key}
"""
    
    with open('wallet_config.txt', 'w') as f:
        f.write(env_content)
    
    print(f"\n💾 Wallet configuration saved to: wallet_config.txt")
    print(f"   You can copy these values to your .env file")
    
    return public_key, private_key

if __name__ == "__main__":
    create_native_wallet()
