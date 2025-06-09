#!/usr/bin/env python3
"""
USDC Token Account Setup for Winsor Williams II
===============================================

This script finds or creates the USDC Associated Token Account (ATA) 
for the main wallet and updates the .env configuration.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    from solders.pubkey import Pubkey
    from solana.rpc.api import Client
    from spl.token.instructions import get_associated_token_address
    from spl.token.constants import TOKEN_PROGRAM_ID
    import base58
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    print("💡 Run: pip install solana spl-token python-dotenv")
    sys.exit(1)

def setup_usdc_account():
    """Setup USDC token account for the wallet."""
    
    # Load environment variables
    load_dotenv()
    
    # Get wallet address and USDC token mint
    wallet_address = os.getenv("WALLET_ADDRESS")
    usdc_mint = os.getenv("USDC_TOKEN", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    quicknode_url = os.getenv("QUICKNODE_RPC_URL")
    
    if not wallet_address:
        print("❌ WALLET_ADDRESS not found in .env file")
        return False
    
    if not quicknode_url:
        print("❌ QUICKNODE_RPC_URL not found in .env file")
        return False
    
    print(f"🏢 Winsor Williams II - USDC Account Setup")
    print(f"👤 Wallet: {wallet_address}")
    print(f"💰 USDC Mint: {usdc_mint}")
    print("=" * 60)
    
    try:
        # Create RPC client
        client = Client(quicknode_url)
        
        # Convert addresses to Pubkey objects
        wallet_pubkey = Pubkey.from_string(wallet_address)
        usdc_mint_pubkey = Pubkey.from_string(usdc_mint)
        
        # Calculate the Associated Token Account (ATA) address for USDC
        usdc_ata = get_associated_token_address(wallet_pubkey, usdc_mint_pubkey)
        
        print(f"🔍 Calculated USDC ATA: {usdc_ata}")
        
        # Check if the USDC ATA exists
        try:
            account_info = client.get_account_info(usdc_ata)
            if account_info.value:
                print(f"✅ USDC token account already exists!")
                print(f"📍 USDC Account Address: {usdc_ata}")
                
                # Try to get token account balance
                try:
                    token_balance = client.get_token_account_balance(usdc_ata)
                    if token_balance.value:
                        balance = float(token_balance.value.amount) / (10 ** token_balance.value.decimals)
                        print(f"💰 Current USDC Balance: {balance:,.6f} USDC")
                    else:
                        print(f"💰 Current USDC Balance: 0.000000 USDC")
                except Exception as e:
                    print(f"⚠️ Could not fetch USDC balance: {e}")
                
            else:
                print(f"⚠️ USDC token account does not exist yet")
                print(f"💡 It will be created automatically on first USDC transaction")
                print(f"📍 Future USDC Account Address: {usdc_ata}")
                
        except Exception as e:
            print(f"⚠️ Could not check USDC account: {e}")
            print(f"📍 Calculated USDC Account Address: {usdc_ata}")
        
        # Update .env file with USDC account address
        update_env_file(usdc_ata)
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up USDC account: {e}")
        return False

def update_env_file(usdc_ata):
    """Update .env file with USDC account address."""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Look for existing WALLET_USDC_ACCOUNT line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("WALLET_USDC_ACCOUNT="):
            lines[i] = f"WALLET_USDC_ACCOUNT={usdc_ata}\n"
            updated = True
            break
    
    # If not found, add it after the token addresses section
    if not updated:
        for i, line in enumerate(lines):
            if "# Wallet-specific token accounts" in line:
                lines[i+1] = f"WALLET_USDC_ACCOUNT={usdc_ata}\n"
                updated = True
                break
    
    # If still not found, add at the end of token section
    if not updated:
        for i, line in enumerate(lines):
            if line.startswith("USDT_TOKEN="):
                lines.insert(i+2, f"\n# Wallet-specific USDC token account\n")
                lines.insert(i+3, f"WALLET_USDC_ACCOUNT={usdc_ata}\n")
                updated = True
                break
    
    if updated:
        # Write back to .env file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        print(f"✅ Updated .env file with USDC account address")
        print(f"📝 Added: WALLET_USDC_ACCOUNT={usdc_ata}")
    else:
        print(f"⚠️ Could not update .env file automatically")
        print(f"💡 Please add this line to your .env file:")
        print(f"   WALLET_USDC_ACCOUNT={usdc_ata}")
    
    return updated

def main():
    """Main function."""
    print("🏢 WINSOR WILLIAMS II - USDC ACCOUNT SETUP")
    print("=" * 60)
    
    success = setup_usdc_account()
    
    if success:
        print("\n🎉 USDC Account Setup Complete!")
        print("✅ USDC Associated Token Account configured")
        print("✅ .env file updated with account address")
        print("✅ Ready for USDC trading operations")
        print("\n💡 Next steps:")
        print("   1. Fund USDC account if needed")
        print("   2. Test trading with small amounts")
        print("   3. Monitor transactions on Solscan")
        return 0
    else:
        print("\n❌ USDC Account Setup Failed")
        print("🔧 Please check your configuration and try again")
        return 1

if __name__ == "__main__":
    exit(main())
