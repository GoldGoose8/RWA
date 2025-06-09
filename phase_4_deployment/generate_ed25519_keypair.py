#!/usr/bin/env python3
"""
Generate Ed25519 Key Pair for Jito Labs' ShredStream Service

This script generates a new Ed25519 key pair that can be used for
authentication with Jito Labs' ShredStream service.
"""

import os
import json
import base64
import secrets
from datetime import datetime
from typing import Tuple, Dict

try:
    # Try to import nacl for Ed25519 key generation
    import nacl.signing
    USE_NACL = True
except ImportError:
    # Fall back to cryptography if nacl is not available
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        USE_NACL = False
    except ImportError:
        print("Error: Neither PyNaCl nor cryptography package is installed.")
        print("Please install one of them:")
        print("  pip install pynacl")
        print("  or")
        print("  pip install cryptography")
        exit(1)

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(message: str) -> None:
    """Print a formatted header."""
    print(f"\n{BLUE}======================================{NC}")
    print(f"{BLUE}{message}{NC}")
    print(f"{BLUE}======================================{NC}\n")

def generate_keypair_nacl() -> Tuple[bytes, bytes]:
    """
    Generate an Ed25519 key pair using PyNaCl.
    
    Returns:
        Tuple of (private_key, public_key) as bytes
    """
    # Generate a new random signing key
    signing_key = nacl.signing.SigningKey.generate()
    
    # Get the verify key (public key)
    verify_key = signing_key.verify_key
    
    # Return the private and public keys
    return signing_key.encode(), verify_key.encode()

def generate_keypair_cryptography() -> Tuple[bytes, bytes]:
    """
    Generate an Ed25519 key pair using cryptography.
    
    Returns:
        Tuple of (private_key, public_key) as bytes
    """
    # Generate a new private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    
    # Get the public key
    public_key = private_key.public_key()
    
    # Return the private and public keys
    return private_key.private_bytes_raw(), public_key.public_bytes_raw()

def generate_keypair() -> Tuple[bytes, bytes]:
    """
    Generate an Ed25519 key pair.
    
    Returns:
        Tuple of (private_key, public_key) as bytes
    """
    if USE_NACL:
        return generate_keypair_nacl()
    else:
        return generate_keypair_cryptography()

def save_keypair(private_key: bytes, public_key: bytes) -> Tuple[str, str]:
    """
    Save the key pair to files.
    
    Args:
        private_key: Private key bytes
        public_key: Public key bytes
        
    Returns:
        Tuple of (private_key_path, public_key_path)
    """
    # Create directory for keys if it doesn't exist
    keys_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")
    os.makedirs(keys_dir, exist_ok=True)
    
    # Generate a unique filename based on timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create Solana-compatible keypair JSON
    keypair_json = {
        "keypair": base64.b64encode(private_key + public_key).decode('ascii')
    }
    
    # Save private key to JSON file
    keypair_path = os.path.join(keys_dir, f"jito_shredstream_keypair_{timestamp}.json")
    with open(keypair_path, 'w') as f:
        json.dump(keypair_json, f)
    
    # Save public key to text file
    pubkey_path = os.path.join(keys_dir, f"jito_shredstream_pubkey_{timestamp}.txt")
    with open(pubkey_path, 'w') as f:
        f.write(base64.b64encode(public_key).decode('ascii'))
    
    return keypair_path, pubkey_path

def main():
    """Main function."""
    print_header("GENERATING ED25519 KEY PAIR FOR JITO LABS")
    
    print(f"{YELLOW}Generating a new key pair...{NC}")
    private_key, public_key = generate_keypair()
    
    print(f"{GREEN}Key pair generated successfully!{NC}")
    
    # Save keys to files
    keypair_path, pubkey_path = save_keypair(private_key, public_key)
    
    print(f"{YELLOW}Keypair saved to: {NC}{keypair_path}")
    
    # Display the public key
    public_key_b64 = base64.b64encode(public_key).decode('ascii')
    
    print_header("YOUR JITO SHREDSTREAM PUBLIC KEY")
    print(f"{GREEN}{public_key_b64}{NC}")
    print(f"\n{YELLOW}Public key saved to: {NC}{pubkey_path}")
    
    print_header("NEXT STEPS")
    print(f"1. {YELLOW}Keep your private key secure:{NC} {keypair_path}")
    print(f"2. {YELLOW}Submit your public key to Jito Labs{NC}")
    print(f"3. {YELLOW}Use this key exclusively for Jito's ShredStream service{NC}")
    print(f"4. {YELLOW}Do NOT send any funds to this address{NC}")
    
    print(f"\n{GREEN}Done!{NC}")

if __name__ == "__main__":
    main()
