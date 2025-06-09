#!/usr/bin/env python3
"""
Wallet Private Key Display
===========================

SECURITY WARNING: This script displays your private key in plain text.
Only run this in a secure environment and never share the output.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

def show_private_key():
    """Display the private key for the configured wallet."""
    print("🔐 WALLET PRIVATE KEY RETRIEVAL")
    print("=" * 50)
    print("⚠️  SECURITY WARNING:")
    print("   This will display your private key in plain text!")
    print("   Never share this key with anyone!")
    print("   Make sure you're in a secure environment!")
    print("=" * 50)
    
    # Confirm user wants to proceed
    confirm = input("\nDo you want to display the private key? (type 'YES' to confirm): ")
    if confirm != "YES":
        print("❌ Operation cancelled for security.")
        return
    
    # Load environment variables
    load_dotenv()
    
    wallet_address = os.getenv("WALLET_ADDRESS")
    private_key_base58 = os.getenv("WALLET_PRIVATE_KEY")
    keypair_path = os.getenv("KEYPAIR_PATH")
    
    if not wallet_address or "your_" in wallet_address:
        print("❌ Wallet not configured in .env file")
        return
    
    print(f"\n📍 Wallet Address: {wallet_address}")
    
    # Show private key from .env file
    if private_key_base58 and "your_" not in private_key_base58:
        print(f"\n🔑 Private Key (Base58):")
        print(f"{private_key_base58}")
    else:
        print("❌ Private key not found in .env file")
    
    # Show keypair file location
    if keypair_path and Path(keypair_path).exists():
        print(f"\n📁 Keypair File: {keypair_path}")
        
        # Read and display keypair file content
        try:
            with open(keypair_path, 'r') as f:
                keypair_data = json.load(f)
            print(f"🔑 Private Key (JSON Array): {keypair_data}")
        except Exception as e:
            print(f"❌ Error reading keypair file: {e}")
    else:
        print(f"❌ Keypair file not found: {keypair_path}")
    
    print("\n" + "=" * 50)
    print("🚨 IMPORTANT REMINDERS:")
    print("1. 🔒 Keep this private key secure")
    print("2. 🚫 Never share it with anyone")
    print("3. 💾 Store a backup in a secure location")
    print("4. 🗑️ Clear your terminal history after this")
    print("5. 🔐 Consider using a hardware wallet for large amounts")
    print("=" * 50)

if __name__ == "__main__":
    show_private_key()
