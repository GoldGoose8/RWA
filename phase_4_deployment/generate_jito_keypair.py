#!/usr/bin/env python3
"""
Simple script to generate a Jito ShredStream keypair.
"""

import os
import json
from solders.keypair import Keypair

# Generate new keypair
keypair = Keypair()

# Get public and private keys
public_key = str(keypair.pubkey())
private_key = str(keypair)  # This returns the base58 encoded private key

# Create keypair data
keypair_data = {
    "public_key": public_key,
    "private_key": private_key
}

# Output path
output_path = "keys/jito_shredstream_keypair.json"

# Create directory if it doesn't exist
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Save keypair to file
with open(output_path, 'w') as f:
    json.dump(keypair_data, f, indent=2)

# Set file permissions to owner-only
os.chmod(output_path, 0o600)

print(f"Generated new keypair for Jito authentication")
print(f"Public key: {public_key}")
print(f"Keypair saved to: {output_path}")
print(f"IMPORTANT: Register this public key with Jito Labs for ShredStream access")
