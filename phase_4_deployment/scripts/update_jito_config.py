#!/usr/bin/env python3
"""
Update Jito Configuration

This script updates the Jito configuration with the provided parameters.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path

def update_config(config_path: str, **kwargs) -> None:
    """
    Update the Jito configuration with the provided parameters.
    
    Args:
        config_path: Path to the configuration file
        **kwargs: Parameters to update
    """
    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        sys.exit(1)
    
    # Update parameters
    for key, value in kwargs.items():
        if '.' in key:
            # Handle nested parameters
            parts = key.split('.')
            current = config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            # Handle top-level parameters
            config[key] = value
    
    # Save configuration
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"Configuration updated successfully: {config_path}")
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")
        sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Update Jito Configuration')
    parser.add_argument('--config', type=str, default=None, help='Path to the configuration file')
    parser.add_argument('--jito-url', type=str, help='Jito RPC URL')
    parser.add_argument('--fallback-url', type=str, help='Fallback RPC URL')
    parser.add_argument('--shredstream-url', type=str, help='ShredStream URL')
    parser.add_argument('--keypair-path', type=str, help='Path to the Ed25519 keypair')
    parser.add_argument('--use-auth-for-tx', type=bool, help='Whether to use authentication for transaction submission')
    parser.add_argument('--max-retries', type=int, help='Maximum number of retry attempts')
    parser.add_argument('--retry-delay', type=float, help='Delay between retry attempts in seconds')
    parser.add_argument('--timeout', type=float, help='Timeout for HTTP requests in seconds')
    parser.add_argument('--default-tip', type=int, help='Default tip amount in micro-lamports')
    parser.add_argument('--skip-preflight', type=bool, help='Whether to skip preflight transaction checks')
    parser.add_argument('--enable-shredstream', type=bool, help='Whether to enable ShredStream service')
    
    args = parser.parse_args()
    
    # Set default config path
    if args.config is None:
        args.config = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'configs', 'jito_config.yaml'
        )
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Build parameters to update
    params = {}
    if args.jito_url:
        params['rpc.jito_url'] = args.jito_url
    if args.fallback_url:
        params['rpc.fallback_url'] = args.fallback_url
    if args.shredstream_url:
        params['rpc.shredstream_url'] = args.shredstream_url
    if args.keypair_path:
        params['auth.keypair_path'] = args.keypair_path
    if args.use_auth_for_tx is not None:
        params['auth.use_auth_for_tx'] = args.use_auth_for_tx
    if args.max_retries is not None:
        params['transaction.max_retries'] = args.max_retries
    if args.retry_delay is not None:
        params['transaction.retry_delay'] = args.retry_delay
    if args.timeout is not None:
        params['transaction.timeout'] = args.timeout
    if args.default_tip is not None:
        params['transaction.default_tip'] = args.default_tip
    if args.skip_preflight is not None:
        params['transaction.skip_preflight'] = args.skip_preflight
    if args.enable_shredstream is not None:
        params['shredstream.enabled'] = args.enable_shredstream
    
    # Update configuration
    if params:
        update_config(args.config, **params)
    else:
        print("No parameters provided to update")
        sys.exit(1)

if __name__ == "__main__":
    main()
