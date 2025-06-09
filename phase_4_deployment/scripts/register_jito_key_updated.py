#!/usr/bin/env python3
"""
Updated Jito ShredStream Key Registration Script

This script helps register your Jito ShredStream public key using the self-service form.
According to the latest Jito documentation, you can now get your public key approved
through their web form instead of manual contact.
"""

import os
import json
import logging
import argparse
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('jito_registration')

# Self-service registration form URL
REGISTRATION_FORM_URL = "https://web.miniextensions.com/WV3gZjFwqNqITsMufIEp"

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Register Jito ShredStream public key')
    parser.add_argument('--keypair', type=str, default=None,
                        help='Path to the keypair file (default: keys/jito_shredstream_keypair.json)')
    parser.add_argument('--open-browser', action='store_true',
                        help='Open the Jito registration form in browser')
    return parser.parse_args()

def register_jito_key(args):
    """
    Register Jito ShredStream public key using the self-service form.
    
    Args:
        args: Command line arguments
    """
    # Default keypair path
    keypair_path = args.keypair or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'keys', 'jito_shredstream_keypair.json'
    )
    
    # Check if keypair file exists
    if not os.path.exists(keypair_path):
        logger.error(f"Keypair file not found: {keypair_path}")
        logger.info("Please run generate_jito_keypair.py first to create a keypair")
        return False
    
    # Load keypair
    try:
        with open(keypair_path, 'r') as f:
            keypair_data = json.load(f)
        
        public_key = keypair_data.get('public_key')
        if not public_key:
            logger.error("Public key not found in keypair file")
            return False
        
        logger.info(f"Loaded public key: {public_key}")
    except Exception as e:
        logger.error(f"Failed to load keypair: {str(e)}")
        return False
    
    # Print registration instructions
    print("\n" + "="*50)
    print("JITO SHREDSTREAM REGISTRATION INSTRUCTIONS (UPDATED)")
    print("="*50)
    print("\nTo register your public key with Jito Labs:")
    
    print("\n1. Fill out the self-service form at:")
    print(f"   {REGISTRATION_FORM_URL}")
    
    print("\n2. Provide the following information in the form:")
    print(f"   - Public Key: {public_key}")
    print("   - Your name/organization")
    print("   - Your email address")
    print("   - Your use case for ShredStream")
    
    print("\n3. Wait for approval (usually within 24-48 hours)")
    
    print("\n4. Once approved, you can use this keypair for ShredStream authentication")
    print(f"   - Keypair file: {keypair_path}")
    print("   - The keypair is already configured in your Jito config")
    
    print("\n5. Set up the ShredStream proxy as described in the documentation:")
    print("   https://docs.jito.wtf/lowlatencytxnfeed/#jito-shredstream-proxy")
    
    print("\n" + "="*50)
    
    # Open browser if requested
    if args.open_browser:
        logger.info(f"Opening Jito registration form in browser: {REGISTRATION_FORM_URL}")
        webbrowser.open(REGISTRATION_FORM_URL)
    
    return True

def main():
    """Main function."""
    args = parse_args()
    
    logger.info("Starting Jito ShredStream key registration process")
    
    if register_jito_key(args):
        logger.info("Registration instructions generated successfully")
        return 0
    else:
        logger.error("Failed to generate registration instructions")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
