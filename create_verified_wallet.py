#!/usr/bin/env python3
"""
Create and Verify Native Solana Wallet

This script creates a new native Solana keypair and thoroughly verifies
that the private key correctly generates the public key to prevent fund loss.
"""

import base58
from solders.keypair import Keypair

def create_and_verify_wallet():
    """Create a new wallet and verify the keys match."""
    print("🔑 Creating and verifying new native Solana wallet...")
    
    # Generate new keypair
    keypair = Keypair()
    
    # Get public and private keys
    public_key = str(keypair.pubkey())
    private_key_bytes = bytes(keypair)
    private_key = base58.b58encode(private_key_bytes).decode('utf-8')
    
    print(f"\n✅ New wallet generated!")
    print(f"📍 Public Key:  {public_key}")
    print(f"🔐 Private Key: {private_key}")
    
    # VERIFICATION STEP 1: Re-derive public key from private key
    print(f"\n🔧 VERIFICATION STEP 1: Re-deriving public key from private key...")
    try:
        # Convert private key back to keypair
        private_key_bytes_check = base58.b58decode(private_key)
        keypair_check = Keypair.from_bytes(private_key_bytes_check)
        public_key_check = str(keypair_check.pubkey())
        
        print(f"Original Public:  {public_key}")
        print(f"Derived Public:   {public_key_check}")
        print(f"Keys Match: {public_key == public_key_check}")
        
        if public_key == public_key_check:
            print("✅ VERIFICATION 1 PASSED: Private key correctly generates public key")
        else:
            print("❌ VERIFICATION 1 FAILED: Key mismatch!")
            return None, None
            
    except Exception as e:
        print(f"❌ VERIFICATION 1 ERROR: {e}")
        return None, None
    
    # VERIFICATION STEP 2: Test multiple conversions
    print(f"\n🔧 VERIFICATION STEP 2: Testing multiple conversions...")
    try:
        for i in range(3):
            test_keypair = Keypair.from_bytes(base58.b58decode(private_key))
            test_public = str(test_keypair.pubkey())
            if test_public != public_key:
                print(f"❌ VERIFICATION 2 FAILED: Inconsistent conversion {i+1}")
                return None, None
        
        print("✅ VERIFICATION 2 PASSED: Consistent key conversion")
        
    except Exception as e:
        print(f"❌ VERIFICATION 2 ERROR: {e}")
        return None, None
    
    # VERIFICATION STEP 3: Test signing (to ensure keypair is valid)
    print(f"\n🔧 VERIFICATION STEP 3: Testing keypair signing capability...")
    try:
        test_message = b"test message for verification"
        signature = keypair.sign_message(test_message)
        print("✅ VERIFICATION 3 PASSED: Keypair can sign messages")
        
    except Exception as e:
        print(f"❌ VERIFICATION 3 ERROR: {e}")
        return None, None
    
    print(f"\n🎉 ALL VERIFICATIONS PASSED!")
    print(f"✅ This wallet is SAFE to use - private key correctly controls the public address")
    
    # Save to file for backup
    wallet_info = f"""# VERIFIED SOLANA WALLET
# Generated and verified: All tests passed
# Safe to use - private key correctly generates public key

WALLET_ADDRESS={public_key}
WALLET_PRIVATE_KEY={private_key}

# Verification Results:
# ✅ Private key generates correct public key
# ✅ Key conversion is consistent
# ✅ Keypair can sign messages
"""
    
    with open('verified_wallet_config.txt', 'w') as f:
        f.write(wallet_info)
    
    print(f"\n💾 Verified wallet saved to: verified_wallet_config.txt")
    
    return public_key, private_key

if __name__ == "__main__":
    public_key, private_key = create_and_verify_wallet()
    
    if public_key and private_key:
        print(f"\n📋 FINAL WALLET DETAILS:")
        print(f"Address:     {public_key}")
        print(f"Private Key: {private_key}")
        
        print(f"\n📱 PHANTOM IMPORT INSTRUCTIONS:")
        print(f"1. Open Phantom wallet")
        print(f"2. Click 'Add/Import Account'")
        print(f"3. Select 'Import Private Key'")
        print(f"4. Paste EXACTLY: {private_key}")
        print(f"5. Verify the address shows: {public_key}")
        
        print(f"\n⚠️  IMPORTANT: If Phantom shows a different address, DO NOT USE!")
    else:
        print(f"\n❌ Wallet creation failed - please try again")
