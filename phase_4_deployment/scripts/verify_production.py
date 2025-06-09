#!/usr/bin/env python3
"""
Production Verification Script for Q5 Trading System

This script verifies that the Q5 Trading System is ready for production deployment
by checking all required components and configurations.
"""

import os
import sys
import json
import time
import logging
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("verify_production")

class ProductionVerifier:
    """
    Verifies that the Q5 Trading System is ready for production deployment.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the production verifier.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.results = {
            "checks": {},
            "overall": {
                "ready": False,
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Initialized production verifier with config path: {config_path}")
    
    async def verify(self) -> Dict[str, Any]:
        """
        Verify that the system is ready for production deployment.
        
        Returns:
            Verification results
        """
        try:
            logger.info("Starting production verification...")
            
            # Run checks
            await self._check_config_files()
            await self._check_api_keys()
            await self._check_wallet_keypair()
            await self._check_carbon_core()
            await self._check_solana_tx_utils()
            await self._check_monitoring()
            await self._check_docker_config()
            
            # Calculate overall results
            self.results["overall"]["passed_checks"] = sum(1 for check in self.results["checks"].values() if check["passed"])
            self.results["overall"]["failed_checks"] = sum(1 for check in self.results["checks"].values() if not check["passed"])
            self.results["overall"]["total_checks"] = len(self.results["checks"])
            self.results["overall"]["ready"] = self.results["overall"]["failed_checks"] == 0
            
            # Log results
            logger.info(f"Production verification completed")
            logger.info(f"Passed checks: {self.results['overall']['passed_checks']}/{self.results['overall']['total_checks']}")
            
            if self.results["overall"]["ready"]:
                logger.info("System is ready for production deployment!")
            else:
                logger.warning(f"System is not ready for production deployment: {self.results['overall']['failed_checks']} failed checks")
            
            return self.results
        except Exception as e:
            logger.error(f"Error during production verification: {str(e)}")
            
            self.results["overall"]["ready"] = False
            
            return self.results
    
    async def _check_config_files(self) -> None:
        """Check configuration files."""
        check_name = "config_files"
        logger.info(f"Checking {check_name}...")
        
        try:
            # Check main config file
            if not os.path.exists(self.config_path):
                raise Exception(f"Configuration file not found: {self.config_path}")
            
            # Load configuration
            from utils.config.config_loader import load_config
            config = load_config(self.config_path)
            
            # Check required sections
            required_sections = ["apis", "rpc", "wallet", "monitoring", "transaction_execution"]
            missing_sections = [section for section in required_sections if section not in config]
            
            if missing_sections:
                raise Exception(f"Missing required configuration sections: {missing_sections}")
            
            # Check environment file
            env_file = ".env"
            if not os.path.exists(env_file):
                raise Exception(f"Environment file not found: {env_file}")
            
            # Check Carbon Core config
            carbon_core_config_path = config.get("carbon_core_config_path", "carbon_core_config.yaml")
            if not os.path.exists(carbon_core_config_path):
                raise Exception(f"Carbon Core configuration file not found: {carbon_core_config_path}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": True,
                "message": "All configuration files are present and valid",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Check {check_name} passed")
        except Exception as e:
            logger.error(f"Check {check_name} failed: {str(e)}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_api_keys(self) -> None:
        """Check API keys."""
        check_name = "api_keys"
        logger.info(f"Checking {check_name}...")
        
        try:
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Check required API keys
            required_keys = {
                "HELIUS_API_KEY": os.environ.get("HELIUS_API_KEY"),
                "BIRDEYE_API_KEY": os.environ.get("BIRDEYE_API_KEY")
            }
            
            missing_keys = [key for key, value in required_keys.items() if not value]
            
            if missing_keys:
                raise Exception(f"Missing required API keys: {missing_keys}")
            
            # Test Helius API key
            helius_api_key = required_keys["HELIUS_API_KEY"]
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.helius.xyz/v0/addresses/vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg/balances?api-key={helius_api_key}"
                )
                
                if response.status_code != 200:
                    raise Exception(f"Helius API key test failed: {response.status_code} {response.text}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": True,
                "message": "All API keys are present and valid",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Check {check_name} passed")
        except Exception as e:
            logger.error(f"Check {check_name} failed: {str(e)}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_wallet_keypair(self) -> None:
        """Check wallet keypair."""
        check_name = "wallet_keypair"
        logger.info(f"Checking {check_name}...")
        
        try:
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Check wallet address
            wallet_address = os.environ.get("WALLET_ADDRESS")
            if not wallet_address:
                raise Exception("WALLET_ADDRESS not found in environment variables")
            
            # Check keypair path
            keypair_path = os.environ.get("KEYPAIR_PATH")
            if not keypair_path:
                raise Exception("KEYPAIR_PATH not found in environment variables")
            
            # Check if keypair file exists
            if not os.path.exists(keypair_path):
                raise Exception(f"Keypair file not found: {keypair_path}")
            
            # Check keypair file permissions
            keypair_stat = os.stat(keypair_path)
            if keypair_stat.st_mode & 0o077:
                raise Exception(f"Keypair file has insecure permissions: {oct(keypair_stat.st_mode)}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": True,
                "message": "Wallet keypair is present and secure",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Check {check_name} passed")
        except Exception as e:
            logger.error(f"Check {check_name} failed: {str(e)}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_carbon_core(self) -> None:
        """Check Carbon Core component."""
        check_name = "carbon_core"
        logger.info(f"Checking {check_name}...")
        
        try:
            # Check Carbon Core binary
            from utils.config.config_loader import load_config
            config = load_config(self.config_path)
            
            carbon_core_binary_path = config.get("core", {}).get("binary_path", "bin/carbon_core")
            
            if not os.path.exists(carbon_core_binary_path):
                raise Exception(f"Carbon Core binary not found: {carbon_core_binary_path}")
            
            # Check if binary is executable
            if not os.access(carbon_core_binary_path, os.X_OK):
                raise Exception(f"Carbon Core binary is not executable: {carbon_core_binary_path}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": True,
                "message": "Carbon Core binary is present and executable",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Check {check_name} passed")
        except Exception as e:
            logger.error(f"Check {check_name} failed: {str(e)}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_solana_tx_utils(self) -> None:
        """Check Solana transaction utilities."""
        check_name = "solana_tx_utils"
        logger.info(f"Checking {check_name}...")
        
        try:
            # Import solana_tx_utils
            import shared.solana_utils.tx_utils
            
            # Check if using fallback
            using_fallback = hasattr(solana_tx_utils, "fallback")
            
            # Create a keypair
            keypair = solana_tx_utils.Keypair()
            pubkey = keypair.pubkey()
            
            # Test encoding/decoding
            test_data = b"Hello, Solana!"
            encoded = solana_tx_utils.encode_base58(test_data)
            decoded = solana_tx_utils.decode_base58(encoded)
            
            if test_data != decoded:
                raise Exception("Encoding/decoding test failed")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": True,
                "message": f"Solana transaction utilities are working correctly (using {'fallback' if using_fallback else 'native'} implementation)",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Check {check_name} passed")
        except Exception as e:
            logger.error(f"Check {check_name} failed: {str(e)}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_monitoring(self) -> None:
        """Check monitoring components."""
        check_name = "monitoring"
        logger.info(f"Checking {check_name}...")
        
        try:
            # Import monitoring service
            from phase_4_deployment.monitoring.monitoring_service import get_monitoring_service
            
            # Initialize monitoring service
            monitoring_service = get_monitoring_service()
            
            # Register a test component
            monitoring_service.register_component(
                "test_component",
                lambda: True
            )
            
            # Run health checks
            health_results = monitoring_service.run_health_checks()
            
            if not health_results.get("test_component", False):
                raise Exception("Test component health check failed")
            
            # Check Telegram alerter
            telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
            telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
            
            if not telegram_bot_token or not telegram_chat_id:
                logger.warning("Telegram alerter is not configured")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": True,
                "message": "Monitoring components are working correctly",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Check {check_name} passed")
        except Exception as e:
            logger.error(f"Check {check_name} failed: {str(e)}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_docker_config(self) -> None:
        """Check Docker configuration."""
        check_name = "docker_config"
        logger.info(f"Checking {check_name}...")
        
        try:
            # Check Docker Compose file
            docker_compose_path = "docker-compose.yml"
            if not os.path.exists(docker_compose_path):
                raise Exception(f"Docker Compose file not found: {docker_compose_path}")
            
            # Check Dockerfile
            dockerfile_path = "docker_deploy/Dockerfile"
            if not os.path.exists(dockerfile_path):
                raise Exception(f"Dockerfile not found: {dockerfile_path}")
            
            # Check entrypoint script
            entrypoint_path = "docker_deploy/entrypoint.sh"
            if not os.path.exists(entrypoint_path):
                raise Exception(f"Entrypoint script not found: {entrypoint_path}")
            
            # Check if entrypoint script is executable
            if not os.access(entrypoint_path, os.X_OK):
                raise Exception(f"Entrypoint script is not executable: {entrypoint_path}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": True,
                "message": "Docker configuration is valid",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Check {check_name} passed")
        except Exception as e:
            logger.error(f"Check {check_name} failed: {str(e)}")
            
            # Record check result
            self.results["checks"][check_name] = {
                "passed": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Production Verification Script for Q5 Trading System")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file")
    parser.add_argument("--output", type=str, default="production_verification.json", help="Path to output file")
    args = parser.parse_args()
    
    # Run production verification
    verifier = ProductionVerifier(args.config)
    results = await verifier.verify()
    
    # Save results to file
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {args.output}")
    
    # Return exit code based on verification results
    return 0 if results["overall"]["ready"] else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
