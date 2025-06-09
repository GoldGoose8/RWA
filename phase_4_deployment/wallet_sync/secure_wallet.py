#!/usr/bin/env python3
"""
Secure Wallet Management Module for Q5 Trading System

This module provides secure wallet management functionality, including:
- Secure loading of wallet keypairs
- Encryption of private keys
- Secure storage of wallet credentials
- Balance monitoring
"""

import os
import json
import base64
import logging
import asyncio
import getpass
import base58
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from solders.keypair import Keypair
from solders.pubkey import Pubkey

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('secure_wallet')

class SecureWallet:
    """
    Secure wallet management for the Q5 Trading System.
    """

    def __init__(self,
                 wallet_dir: str = None,
                 encryption_key_file: str = None):
        """
        Initialize the SecureWallet.

        Args:
            wallet_dir: Directory to store wallet files
            encryption_key_file: Path to encryption key file
        """
        self.wallet_dir = wallet_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'keys'
        )

        # Create wallet directory if it doesn't exist
        os.makedirs(self.wallet_dir, exist_ok=True)

        # Path to encryption key file
        self.encryption_key_file = encryption_key_file or os.path.join(
            self.wallet_dir, '.key'
        )

        # Initialize encryption key
        self.encryption_key = None

        # Current keypair
        self.keypair = None
        self.public_key = None

    def generate_encryption_key(self, password: str, salt: bytes = None) -> bytes:
        """
        Generate an encryption key from a password.

        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if None)

        Returns:
            Encryption key
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        # Save salt to file
        with open(os.path.join(self.wallet_dir, '.salt'), 'wb') as f:
            f.write(salt)

        return key

    def load_encryption_key(self, password: str = None) -> bytes:
        """
        Load or create encryption key.

        Args:
            password: Password to derive key from (if creating new key)

        Returns:
            Encryption key
        """
        # Check if key file exists
        if os.path.exists(self.encryption_key_file):
            with open(self.encryption_key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            # If no password provided, prompt for one
            if password is None:
                password = getpass.getpass("Enter new wallet encryption password: ")
                password_confirm = getpass.getpass("Confirm password: ")

                if password != password_confirm:
                    raise ValueError("Passwords do not match")

            # Generate new key
            self.encryption_key = self.generate_encryption_key(password)

            # Save key to file with restricted permissions
            with open(self.encryption_key_file, 'wb') as f:
                f.write(self.encryption_key)

            # Set file permissions to owner-only
            os.chmod(self.encryption_key_file, 0o600)

        return self.encryption_key

    def encrypt_private_key(self, private_key: str) -> bytes:
        """
        Encrypt a private key.

        Args:
            private_key: Private key to encrypt

        Returns:
            Encrypted private key
        """
        if self.encryption_key is None:
            self.load_encryption_key()

        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(private_key.encode())

    def decrypt_private_key(self, encrypted_private_key: bytes) -> str:
        """
        Decrypt a private key.

        Args:
            encrypted_private_key: Encrypted private key

        Returns:
            Decrypted private key
        """
        if self.encryption_key is None:
            self.load_encryption_key()

        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_private_key).decode()

    def create_wallet(self, private_key: str = None) -> Tuple[str, str]:
        """
        Create a new wallet or import an existing one.

        Args:
            private_key: Private key to import (if None, generate new keypair)

        Returns:
            Tuple of (public key, private key)
        """
        if private_key is None:
            # Generate new keypair
            self.keypair = Keypair()
        else:
            # Import existing keypair
            try:
                # Try to parse as base58 encoded private key
                private_key_bytes = base58.b58decode(private_key)
                self.keypair = Keypair.from_bytes(private_key_bytes)
            except Exception:
                # Try to parse as hex string
                try:
                    private_key_bytes = bytes.fromhex(private_key)
                    self.keypair = Keypair.from_bytes(private_key_bytes)
                except Exception as e:
                    raise ValueError(f"Invalid private key format: {str(e)}")

        self.public_key = self.keypair.pubkey()

        return str(self.public_key), private_key or self.keypair.to_base58_string()

    def save_wallet(self, public_key: str, private_key: str) -> str:
        """
        Save wallet to encrypted file.

        Args:
            public_key: Public key
            private_key: Private key

        Returns:
            Path to wallet file
        """
        # Ensure encryption key is loaded
        if self.encryption_key is None:
            self.load_encryption_key()

        # Encrypt private key
        encrypted_private_key = self.encrypt_private_key(private_key)

        # Create wallet file
        wallet_file = os.path.join(self.wallet_dir, f"{public_key}.wallet")

        # Save encrypted private key to file
        with open(wallet_file, 'wb') as f:
            f.write(encrypted_private_key)

        # Set file permissions to owner-only
        os.chmod(wallet_file, 0o600)

        logger.info(f"Wallet saved to {wallet_file}")

        return wallet_file

    def load_wallet(self, public_key: str = None) -> Tuple[str, str]:
        """
        Load wallet from encrypted file.

        Args:
            public_key: Public key of wallet to load (if None, use environment variable)

        Returns:
            Tuple of (public key, private key)
        """
        # If no public key provided, try to get from environment
        if public_key is None:
            public_key = os.environ.get('WALLET_ADDRESS')
            if not public_key:
                raise ValueError("No wallet address provided or found in environment")

        # Path to wallet file
        wallet_file = os.path.join(self.wallet_dir, f"{public_key}.wallet")

        # Check if wallet file exists
        if not os.path.exists(wallet_file):
            raise FileNotFoundError(f"Wallet file not found: {wallet_file}")

        # Ensure encryption key is loaded
        if self.encryption_key is None:
            self.load_encryption_key()

        # Load encrypted private key from file
        with open(wallet_file, 'rb') as f:
            encrypted_private_key = f.read()

        # Decrypt private key
        private_key = self.decrypt_private_key(encrypted_private_key)

        # Create keypair
        self.create_wallet(private_key)

        return public_key, private_key

# Example usage
async def main():
    """Main function to demonstrate the secure wallet."""
    # Create secure wallet
    wallet = SecureWallet()

    # Check if wallet exists
    wallet_address = os.environ.get('WALLET_ADDRESS')
    wallet_file = os.path.join(wallet.wallet_dir, f"{wallet_address}.wallet")

    if os.path.exists(wallet_file):
        # Load existing wallet
        print(f"Loading existing wallet: {wallet_address}")
        public_key, _ = wallet.load_wallet()
        print(f"Wallet loaded: {public_key}")
    else:
        # Create new wallet from environment variable or generate new one
        private_key = os.environ.get('WALLET_PRIVATE_KEY')
        if private_key:
            print("Creating wallet from environment variable")
            public_key, private_key = wallet.create_wallet(private_key)
        else:
            print("Generating new wallet")
            public_key, private_key = wallet.create_wallet()

        # Save wallet
        wallet_file = wallet.save_wallet(public_key, private_key)
        print(f"New wallet created and saved: {public_key}")

    print("Wallet is ready for use")

def create_new_native_wallet():
    """Create a new native Solana wallet and display private key for Phantom import."""
    print("🔑 Creating new native Solana wallet for RWA Trading System...")

    # Create secure wallet
    wallet = SecureWallet()

    # Generate new keypair
    public_key, private_key = wallet.create_wallet()

    # Display wallet information
    print(f"\n✅ New wallet created successfully!")
    print(f"📍 Public Key (Wallet Address): {public_key}")
    print(f"🔐 Private Key (for Phantom import): {private_key}")

    # Get password for encryption
    password = getpass.getpass("\nEnter password to encrypt wallet for secure storage: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("❌ Passwords do not match")
        return None, None

    # Load encryption key with password
    wallet.load_encryption_key(password)

    # Save wallet
    wallet_file = wallet.save_wallet(public_key, private_key)

    print(f"\n💾 Wallet saved securely to: {wallet_file}")
    print(f"\n📋 Next steps:")
    print(f"1. Copy the private key above and import it into Phantom wallet")
    print(f"2. Fund the wallet address: {public_key}")
    print(f"3. Update your .env file with WALLET_ADDRESS={public_key}")
    print(f"4. Run live trading to test with real transactions")

    return public_key, private_key

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--create-new":
        create_new_native_wallet()
    else:
        asyncio.run(main())
