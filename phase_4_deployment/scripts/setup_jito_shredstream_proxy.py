#!/usr/bin/env python3
"""
Jito ShredStream Proxy Setup Script

This script helps set up the Jito ShredStream proxy according to the latest documentation.
It generates the necessary Docker commands and configuration for running the proxy.
"""

import os
import json
import logging
import argparse
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('jito_shredstream_setup')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Set up Jito ShredStream proxy')
    parser.add_argument('--keypair', type=str, default=None,
                        help='Path to the keypair file (default: keys/jito_shredstream_keypair.json)')
    parser.add_argument('--regions', type=str, default='amsterdam,ny',
                        help='Comma-delimited regions to receive shreds from (default: amsterdam,ny)')
    parser.add_argument('--dest-ports', type=str, default='127.0.0.1:8001',
                        help='Comma-delimited IP:Port combinations to receive shreds on (default: 127.0.0.1:8001)')
    parser.add_argument('--block-engine-url', type=str, default='https://mainnet.block-engine.jito.wtf',
                        help='Block Engine URL (default: https://mainnet.block-engine.jito.wtf)')
    parser.add_argument('--network', type=str, default='host',
                        choices=['host', 'bridge'],
                        help='Docker network type (default: host)')
    parser.add_argument('--src-bind-port', type=int, default=20000,
                        help='Source bind port for bridge networking (default: 20000)')
    parser.add_argument('--run', action='store_true',
                        help='Run the Docker command instead of just printing it')
    return parser.parse_args()

def get_tvu_port():
    """
    Get the TVU port from the Solana RPC.
    
    Returns:
        TVU port if successful, None otherwise
    """
    try:
        # Try to run the get_tvu_port.sh script
        logger.info("Attempting to get TVU port...")
        
        # Check if we can access a local Solana RPC
        cmd = 'curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc":"2.0","id":1,"method":"getHealth"}\' http://localhost:8899'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if '"result":"ok"' in result.stdout:
            # We have a local RPC, use LEDGER_DIR approach
            logger.info("Local Solana RPC detected, getting TVU port...")
            
            # Try to find the ledger directory
            ledger_dir = os.environ.get('LEDGER_DIR')
            if not ledger_dir:
                # Try common locations
                common_paths = [
                    os.path.expanduser("~/.local/share/solana/install/active_release/bin/solana-ledger"),
                    os.path.expanduser("~/solana-ledger"),
                    "/var/solana/data"
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        ledger_dir = path
                        break
            
            if ledger_dir:
                cmd = f'export LEDGER_DIR={ledger_dir}; bash -c "$(curl -fsSL https://raw.githubusercontent.com/jito-labs/shredstream-proxy/master/scripts/get_tvu_port.sh)"'
            else:
                logger.warning("Could not find ledger directory, using HOST approach")
                cmd = 'export HOST=http://localhost:8899; bash -c "$(curl -fsSL https://raw.githubusercontent.com/jito-labs/shredstream-proxy/master/scripts/get_tvu_port.sh)"'
        else:
            # No local RPC, try with HOST
            logger.info("No local Solana RPC detected, using default port...")
            return 8001  # Default port if we can't detect
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Parse the output to find the TVU port
        for line in result.stdout.splitlines():
            if "TVU port:" in line:
                port = line.split("TVU port:")[1].strip()
                logger.info(f"Found TVU port: {port}")
                return int(port)
        
        logger.warning("Could not find TVU port in output, using default port 8001")
        return 8001
    except Exception as e:
        logger.error(f"Error getting TVU port: {str(e)}")
        logger.warning("Using default port 8001")
        return 8001

def setup_shredstream_proxy(args):
    """
    Set up the Jito ShredStream proxy.
    
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
    
    # Load keypair to verify it's valid
    try:
        with open(keypair_path, 'r') as f:
            keypair_data = json.load(f)
        
        public_key = keypair_data.get('public_key')
        if not public_key:
            logger.error("Public key not found in keypair file")
            return False
        
        logger.info(f"Using keypair with public key: {public_key}")
    except Exception as e:
        logger.error(f"Failed to load keypair: {str(e)}")
        return False
    
    # Get absolute path to keypair file
    keypair_abs_path = os.path.abspath(keypair_path)
    
    # Try to get TVU port if not specified in dest-ports
    if args.dest_ports == '127.0.0.1:8001':
        tvu_port = get_tvu_port()
        dest_ports = f'127.0.0.1:{tvu_port}'
        logger.info(f"Using detected TVU port: {dest_ports}")
    else:
        dest_ports = args.dest_ports
    
    # Generate Docker command based on network type
    if args.network == 'host':
        docker_cmd = f"""docker run -d \\
--name jito-shredstream-proxy \\
--rm \\
--env RUST_LOG=info \\
--env BLOCK_ENGINE_URL={args.block_engine_url} \\
--env AUTH_KEYPAIR=my_keypair.json \\
--env DESIRED_REGIONS={args.regions} \\
--env DEST_IP_PORTS={dest_ports} \\
--network host \\
-v {keypair_abs_path}:/app/my_keypair.json \\
jitolabs/jito-shredstream-proxy shredstream"""
    else:  # bridge
        docker_cmd = f"""docker run -d \\
--name jito-shredstream-proxy \\
--rm \\
--env RUST_LOG=info \\
--env BLOCK_ENGINE_URL={args.block_engine_url} \\
--env AUTH_KEYPAIR=my_keypair.json \\
--env DESIRED_REGIONS={args.regions} \\
--env SRC_BIND_PORT={args.src_bind_port} \\
--env DEST_IP_PORTS={dest_ports} \\
--network bridge \\
-p {args.src_bind_port}:{args.src_bind_port}/udp \\
-v {keypair_abs_path}:/app/my_keypair.json \\
jitolabs/jito-shredstream-proxy shredstream"""
    
    # Print the Docker command
    print("\n" + "="*50)
    print("JITO SHREDSTREAM PROXY SETUP")
    print("="*50)
    print("\nDocker command to run the Jito ShredStream proxy:")
    print("\n" + docker_cmd)
    print("\n" + "="*50)
    
    # Print firewall configuration
    print("\nFirewall Configuration:")
    print("If you use a firewall, allow access to the following IPs:")
    print("\n🇳🇱 Amsterdam:")
    print("74.118.140.240, 64.130.52.138, 202.8.8.177, 64.130.55.26, 64.130.55.174, 64.130.55.28")
    print("\n🇩🇪 Frankfurt:")
    print("64.130.50.14, 64.130.57.199, 64.130.57.99, 64.130.57.171, 64.130.40.23, 64.130.40.22, 64.130.40.21")
    print("\n🇺🇸 New York:")
    print("141.98.216.96, 64.130.51.137, 64.130.51.41, 64.130.59.205, 64.130.34.189, 64.130.34.190, 64.130.34.141, 64.130.34.142")
    print("\n🇺🇸 Salt Lake City:")
    print("64.130.53.8, 64.130.53.88, 64.130.53.90, 64.130.53.82")
    print("\n🇯🇵 Tokyo:")
    print("202.8.9.160, 202.8.9.22, 208.91.107.252, 64.130.49.142")
    print("\n" + "="*50)
    
    # Run the Docker command if requested
    if args.run:
        logger.info("Running Docker command...")
        try:
            result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Docker container started successfully")
                logger.info("View logs with: docker logs -f jito-shredstream-proxy")
                return True
            else:
                logger.error(f"Failed to start Docker container: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running Docker command: {str(e)}")
            return False
    
    return True

def main():
    """Main function."""
    args = parse_args()
    
    logger.info("Starting Jito ShredStream proxy setup")
    
    if setup_shredstream_proxy(args):
        logger.info("ShredStream proxy setup completed successfully")
        return 0
    else:
        logger.error("ShredStream proxy setup failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
