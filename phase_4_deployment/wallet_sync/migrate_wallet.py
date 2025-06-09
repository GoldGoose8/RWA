#!/usr/bin/env python3
"""
Wallet Migration Script for Q5 Trading System

This script securely migrates wallet credentials from .env file to encrypted storage.
"""

import os
import sys
import logging
import getpass
import argparse
from pathlib import Path
from dotenv import load_dotenv, set_key

# Add parent directory to path to import secure_wallet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wallet_sync.secure_wallet import SecureWallet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('migrate_wallet')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Migrate wallet credentials to secure storage')
    parser.add_argument('--env-file', type=str, default='.env',
                        help='Path to .env file (default: .env)')
    parser.add_argument('--wallet-dir', type=str, default=None,
                        help='Directory to store wallet files (default: phase_4_deployment/keys)')
    parser.add_argument('--remove-private-key', action='store_true',
                        help='Remove private key from .env file after migration')
    parser.add_argument('--force', action='store_true',
                        help='Force migration even if wallet already exists')
    return parser.parse_args()

def migrate_wallet(args):
    """
    Migrate wallet credentials from .env file to secure storage.
    
    Args:
        args: Command line arguments
    """
    # Load environment variables
    env_path = Path(args.env_file)
    if not env_path.exists():
        logger.error(f"Environment file not found: {env_path}")
        return False
    
    load_dotenv(env_path)
    
    # Get wallet credentials from environment
    wallet_address = os.environ.get('WALLET_ADDRESS')
    wallet_private_key = os.environ.get('WALLET_PRIVATE_KEY')
    
    if not wallet_address or not wallet_private_key:
        logger.error("Wallet address or private key not found in environment")
        return False
    
    # Create secure wallet
    wallet = SecureWallet(wallet_dir=args.wallet_dir)
    
    # Check if wallet already exists
    wallet_file = os.path.join(wallet.wallet_dir, f"{wallet_address}.wallet")
    if os.path.exists(wallet_file) and not args.force:
        logger.warning(f"Wallet already exists: {wallet_file}")
        logger.warning("Use --force to overwrite")
        return False
    
    # Get password for encryption
    password = getpass.getpass("Enter password to encrypt wallet: ")
    password_confirm = getpass.getpass("Confirm password: ")
    
    if password != password_confirm:
        logger.error("Passwords do not match")
        return False
    
    # Load or create encryption key
    wallet.load_encryption_key(password)
    
    # Create wallet
    public_key, _ = wallet.create_wallet(wallet_private_key)
    
    # Verify public key matches
    if public_key != wallet_address:
        logger.error(f"Public key mismatch: {public_key} != {wallet_address}")
        return False
    
    # Save wallet
    wallet_file = wallet.save_wallet(public_key, wallet_private_key)
    logger.info(f"Wallet migrated to secure storage: {wallet_file}")
    
    # Remove private key from .env file if requested
    if args.remove_private_key:
        logger.info("Removing private key from .env file")
        # Create backup of .env file
        backup_path = f"{env_path}.bak"
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        with open(backup_path, 'w') as f:
            f.write(env_content)
        
        logger.info(f"Backup of .env file created: {backup_path}")
        
        # Replace private key with placeholder
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        with open(env_path, 'w') as f:
            for line in lines:
                if line.startswith('WALLET_PRIVATE_KEY='):
                    f.write('WALLET_PRIVATE_KEY=***SECURELY_STORED***\n')
                else:
                    f.write(line)
        
        logger.info("Private key removed from .env file")
    
    return True

def main():
    """Main function."""
    args = parse_args()
    
    logger.info("Starting wallet migration")
    
    if migrate_wallet(args):
        logger.info("Wallet migration completed successfully")
        return 0
    else:
        logger.error("Wallet migration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
