#!/usr/bin/env python3
"""
Live Trading Configuration Validator
====================================

This script validates that all required configuration for live trading is properly set up:
- API endpoints (QuickNode, Helius, Jito)
- Wallet configuration
- Environment variables
- Network connectivity
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiveConfigValidator:
    """Validates live trading configuration and connectivity."""
    
    def __init__(self):
        """Initialize the validator."""
        self.results = {
            "overall_status": "unknown",
            "checks": {},
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Load environment variables
        load_dotenv()
        
    def validate_environment_file(self) -> bool:
        """Validate .env file exists and has required variables."""
        logger.info("🔍 Validating environment configuration...")
        
        required_vars = [
            "QUICKNODE_RPC_URL",
            "QUICKNODE_API_KEY", 
            "HELIUS_RPC_URL",
            "HELIUS_API_KEY",
            "WALLET_ADDRESS",
            "WALLET_PRIVATE_KEY",
            "JITO_RPC_URL"
        ]
        
        missing_vars = []
        placeholder_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            elif "your_" in value.lower() or "here" in value.lower():
                placeholder_vars.append(var)
        
        if missing_vars:
            self.results["errors"].append(f"Missing environment variables: {missing_vars}")
            self.results["checks"]["env_file"] = {"status": "FAILED", "missing": missing_vars}
            return False
            
        if placeholder_vars:
            self.results["warnings"].append(f"Placeholder values detected: {placeholder_vars}")
            self.results["checks"]["env_file"] = {"status": "INCOMPLETE", "placeholders": placeholder_vars}
            return False
            
        self.results["checks"]["env_file"] = {"status": "PASSED"}
        logger.info("✅ Environment file validation passed")
        return True
    
    async def test_quicknode_connectivity(self) -> bool:
        """Test QuickNode RPC connectivity."""
        logger.info("🔍 Testing QuickNode connectivity...")
        
        quicknode_url = os.getenv("QUICKNODE_RPC_URL")
        if not quicknode_url or "your-" in quicknode_url:
            self.results["errors"].append("QuickNode RPC URL not configured")
            self.results["checks"]["quicknode_rpc"] = {"status": "NOT_CONFIGURED"}
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getHealth"
                }
                
                response = await client.post(quicknode_url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result and result["result"] == "ok":
                        self.results["checks"]["quicknode_rpc"] = {"status": "PASSED", "health": "ok"}
                        logger.info("✅ QuickNode RPC connectivity test passed")
                        return True
                    else:
                        self.results["warnings"].append("QuickNode RPC responded but health check failed")
                        self.results["checks"]["quicknode_rpc"] = {"status": "DEGRADED", "response": result}
                        return False
                else:
                    self.results["errors"].append(f"QuickNode RPC returned status {response.status_code}")
                    self.results["checks"]["quicknode_rpc"] = {"status": "FAILED", "status_code": response.status_code}
                    return False
                    
        except Exception as e:
            self.results["errors"].append(f"QuickNode RPC connection failed: {str(e)}")
            self.results["checks"]["quicknode_rpc"] = {"status": "FAILED", "error": str(e)}
            return False
    
    async def test_helius_connectivity(self) -> bool:
        """Test Helius RPC connectivity."""
        logger.info("🔍 Testing Helius connectivity...")
        
        helius_url = os.getenv("HELIUS_RPC_URL")
        if not helius_url or "your_" in helius_url:
            self.results["errors"].append("Helius RPC URL not configured")
            self.results["checks"]["helius_rpc"] = {"status": "NOT_CONFIGURED"}
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getHealth"
                }
                
                response = await client.post(helius_url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result and result["result"] == "ok":
                        self.results["checks"]["helius_rpc"] = {"status": "PASSED", "health": "ok"}
                        logger.info("✅ Helius RPC connectivity test passed")
                        return True
                    else:
                        self.results["warnings"].append("Helius RPC responded but health check failed")
                        self.results["checks"]["helius_rpc"] = {"status": "DEGRADED", "response": result}
                        return False
                else:
                    self.results["errors"].append(f"Helius RPC returned status {response.status_code}")
                    self.results["checks"]["helius_rpc"] = {"status": "FAILED", "status_code": response.status_code}
                    return False
                    
        except Exception as e:
            self.results["errors"].append(f"Helius RPC connection failed: {str(e)}")
            self.results["checks"]["helius_rpc"] = {"status": "FAILED", "error": str(e)}
            return False
    
    async def test_jito_connectivity(self) -> bool:
        """Test Jito bundle endpoint connectivity."""
        logger.info("🔍 Testing Jito connectivity...")
        
        jito_url = os.getenv("JITO_RPC_URL", "https://mainnet.block-engine.jito.wtf/api/v1")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test basic connectivity to Jito endpoint
                response = await client.get(f"{jito_url.rstrip('/api/v1')}/", timeout=5.0)
                
                if response.status_code in [200, 404]:  # 404 is expected for root path
                    self.results["checks"]["jito_endpoint"] = {"status": "PASSED", "reachable": True}
                    logger.info("✅ Jito endpoint connectivity test passed")
                    return True
                else:
                    self.results["warnings"].append(f"Jito endpoint returned unexpected status {response.status_code}")
                    self.results["checks"]["jito_endpoint"] = {"status": "DEGRADED", "status_code": response.status_code}
                    return False
                    
        except Exception as e:
            self.results["errors"].append(f"Jito endpoint connection failed: {str(e)}")
            self.results["checks"]["jito_endpoint"] = {"status": "FAILED", "error": str(e)}
            return False
    
    def validate_wallet_configuration(self) -> bool:
        """Validate wallet configuration."""
        logger.info("🔍 Validating wallet configuration...")
        
        wallet_address = os.getenv("WALLET_ADDRESS")
        wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
        keypair_path = os.getenv("KEYPAIR_PATH", "keys/trading_wallet.json")
        
        issues = []
        
        if not wallet_address or "your_" in wallet_address:
            issues.append("WALLET_ADDRESS not configured")
            
        if not wallet_private_key or "your_" in wallet_private_key:
            issues.append("WALLET_PRIVATE_KEY not configured")
            
        # Check if keypair file exists
        if not Path(keypair_path).exists():
            issues.append(f"Keypair file not found: {keypair_path}")
            
        if issues:
            self.results["errors"].extend(issues)
            self.results["checks"]["wallet_config"] = {"status": "FAILED", "issues": issues}
            return False
            
        self.results["checks"]["wallet_config"] = {"status": "PASSED"}
        logger.info("✅ Wallet configuration validation passed")
        return True
    
    def validate_config_files(self) -> bool:
        """Validate configuration files exist and are valid."""
        logger.info("🔍 Validating configuration files...")
        
        config_files = [
            "config.yaml",
            "config/live_production.yaml"
        ]
        
        missing_files = []
        for config_file in config_files:
            if not Path(config_file).exists():
                missing_files.append(config_file)
        
        if missing_files:
            self.results["errors"].append(f"Missing configuration files: {missing_files}")
            self.results["checks"]["config_files"] = {"status": "FAILED", "missing": missing_files}
            return False
            
        self.results["checks"]["config_files"] = {"status": "PASSED"}
        logger.info("✅ Configuration files validation passed")
        return True
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation checks."""
        logger.info("🚀 Starting live trading configuration validation...")
        logger.info("=" * 60)
        
        # Run all validation checks
        checks = [
            self.validate_environment_file(),
            self.validate_config_files(),
            self.validate_wallet_configuration(),
            await self.test_quicknode_connectivity(),
            await self.test_helius_connectivity(),
            await self.test_jito_connectivity()
        ]
        
        # Determine overall status
        if all(checks):
            self.results["overall_status"] = "READY"
            logger.info("🎉 All validation checks passed - System ready for live trading!")
        elif any(checks):
            self.results["overall_status"] = "PARTIAL"
            logger.warning("⚠️ Some validation checks failed - Review issues before live trading")
        else:
            self.results["overall_status"] = "NOT_READY"
            logger.error("❌ Multiple validation checks failed - System not ready for live trading")
        
        # Add recommendations
        if self.results["warnings"]:
            self.results["recommendations"].append("Review and fix all warnings before live trading")
        if self.results["errors"]:
            self.results["recommendations"].append("Fix all errors before attempting live trading")
            
        return self.results
    
    def print_summary(self):
        """Print validation summary."""
        logger.info("\n" + "=" * 60)
        logger.info("LIVE TRADING CONFIGURATION VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        # Overall status
        status_emoji = {
            "READY": "🟢",
            "PARTIAL": "🟡", 
            "NOT_READY": "🔴",
            "unknown": "⚪"
        }
        
        logger.info(f"Overall Status: {status_emoji[self.results['overall_status']]} {self.results['overall_status']}")
        logger.info("")
        
        # Individual checks
        for check_name, check_result in self.results["checks"].items():
            status = check_result["status"]
            status_emoji_check = {"PASSED": "✅", "FAILED": "❌", "DEGRADED": "⚠️", "NOT_CONFIGURED": "🔧", "INCOMPLETE": "🟡"}
            logger.info(f"{status_emoji_check.get(status, '❓')} {check_name}: {status}")
        
        # Warnings and errors
        if self.results["warnings"]:
            logger.info("\n⚠️ WARNINGS:")
            for warning in self.results["warnings"]:
                logger.info(f"  • {warning}")
                
        if self.results["errors"]:
            logger.info("\n❌ ERRORS:")
            for error in self.results["errors"]:
                logger.info(f"  • {error}")
                
        if self.results["recommendations"]:
            logger.info("\n💡 RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                logger.info(f"  • {rec}")
        
        logger.info("=" * 60)

async def main():
    """Main function."""
    validator = LiveConfigValidator()
    results = await validator.run_all_validations()
    validator.print_summary()
    
    # Save results to file
    output_file = "output/live_config_validation.json"
    os.makedirs("output", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Detailed results saved to: {output_file}")
    
    # Exit with appropriate code
    if results["overall_status"] == "READY":
        return 0
    elif results["overall_status"] == "PARTIAL":
        return 1
    else:
        return 2

if __name__ == "__main__":
    exit(asyncio.run(main()))
