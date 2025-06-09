#!/usr/bin/env python3
"""
Generate Test Wallet

This script generates a test wallet for use on the Solana devnet.
"""

import os
import sys
import json
import logging
import secrets
from typing import Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_keypair() -> Tuple[bytes, str, str]:
    """
    Generate a mock Solana keypair.

    Returns:
        Tuple[bytes, str, str]: Keypair bytes, public key, private key
    """
    try:
        # Generate random bytes for private key (32 bytes)
        private_key_bytes = secrets.token_bytes(32)

        # Generate random bytes for public key (32 bytes)
        public_key_bytes = secrets.token_bytes(32)

        # Combine to form keypair bytes
        keypair_bytes = private_key_bytes + public_key_bytes

        # Convert to hex strings for display
        public_key = public_key_bytes.hex()
        private_key = private_key_bytes.hex()

        logger.info(f"Generated mock keypair with public key: {public_key}")

        return keypair_bytes, public_key, private_key
    except Exception as e:
        logger.error(f"Error generating keypair: {str(e)}")
        raise

def save_keypair(keypair_bytes: bytes, output_path: str) -> None:
    """
    Save a keypair to a file.

    Args:
        keypair_bytes: Keypair bytes
        output_path: Output path
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save keypair
        with open(output_path, "w") as f:
            json.dump(list(keypair_bytes), f)

        logger.info(f"Saved keypair to {output_path}")
    except Exception as e:
        logger.error(f"Error saving keypair: {str(e)}")
        raise

def main():
    """Main function."""
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Generate a test wallet for use on the Solana devnet")
    parser.add_argument("--output", default="keys/test_wallet_keypair.json", help="Output path for the keypair")

    args = parser.parse_args()

    try:
        # Generate keypair
        keypair_bytes, public_key, private_key = generate_keypair()

        # Save keypair
        save_keypair(keypair_bytes, args.output)

        # Print information
        print(f"Public Key: {public_key}")
        print(f"Private Key: {private_key}")
        print(f"Keypair saved to: {args.output}")

        # Update test_config.yaml with the public key
        config_path = "phase_4_deployment/test_config.yaml"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = f.read()

            # Replace wallet address
            config = config.replace(
                "address: \"Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr\"",
                f"address: \"{public_key}\""
            )

            with open(config_path, "w") as f:
                f.write(config)

            logger.info(f"Updated wallet address in {config_path}")

        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
