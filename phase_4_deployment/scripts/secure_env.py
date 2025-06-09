#!/usr/bin/env python3
"""
Secure Environment Script for Q5 Trading System

This script secures the environment variables by:
1. Migrating wallet credentials to secure storage
2. Removing sensitive information from .env file
3. Updating .env file with secure placeholders
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv, set_key

# Add parent directory to path to import secure_wallet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wallet_sync.secure_wallet import SecureWallet
from wallet_sync.migrate_wallet import migrate_wallet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('secure_env')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Secure environment variables')
    parser.add_argument('--env-file', type=str, default='.env',
                        help='Path to .env file (default: .env)')
    parser.add_argument('--backup', action='store_true',
                        help='Create backup of .env file')
    parser.add_argument('--force', action='store_true',
                        help='Force update even if wallet already exists')
    return parser.parse_args()

def secure_env_file(args):
    """
    Secure environment variables in .env file.
    
    Args:
        args: Command line arguments
    """
    # Load environment variables
    env_path = Path(args.env_file)
    if not env_path.exists():
        logger.error(f"Environment file not found: {env_path}")
        return False
    
    load_dotenv(env_path)
    
    # Create backup if requested
    if args.backup:
        backup_path = f"{env_path}.bak"
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        with open(backup_path, 'w') as f:
            f.write(env_content)
        
        logger.info(f"Backup of .env file created: {backup_path}")
    
    # Migrate wallet to secure storage
    from argparse import Namespace
    wallet_args = Namespace(
        env_file=args.env_file,
        wallet_dir=None,
        remove_private_key=True,
        force=args.force
    )
    
    if not migrate_wallet(wallet_args):
        logger.error("Failed to migrate wallet to secure storage")
        return False
    
    # Update other sensitive variables
    sensitive_vars = [
        'TELEGRAM_BOT_TOKEN',
        'DB_CONNECTION_STRING'
    ]
    
    # Read .env file
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update sensitive variables
    updated = False
    with open(env_path, 'w') as f:
        for line in lines:
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                f.write(line)
                continue
            
            # Check if line contains sensitive variable
            is_sensitive = False
            for var in sensitive_vars:
                if line.startswith(f"{var}="):
                    # Check if already secured
                    if "***SECURELY_STORED***" in line:
                        f.write(line)
                    else:
                        f.write(f"{var}=***SECURELY_STORED***\n")
                        updated = True
                        logger.info(f"Secured sensitive variable: {var}")
                    is_sensitive = True
                    break
            
            # Write line if not sensitive
            if not is_sensitive:
                f.write(line)
    
    if updated:
        logger.info("Updated .env file with secure placeholders")
    else:
        logger.info("No additional sensitive variables found to secure")
    
    return True

def main():
    """Main function."""
    args = parse_args()
    
    logger.info("Starting environment security process")
    
    if secure_env_file(args):
        logger.info("Environment security process completed successfully")
        return 0
    else:
        logger.error("Environment security process failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
