#!/usr/bin/env python3
"""
Test script for Synergy7 integration enhancements.

This script tests the new components and services implemented for the
Synergy7 system integration plan.
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Test the integration enhancements."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall": {
                "success": True,
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    async def test_price_service(self) -> bool:
        """
        Test the price service.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Testing price service...")
        
        try:
            # Import price service
            from shared.utils.price_service import get_price_service
            
            # Get price service instance
            price_service = get_price_service()
            
            # Initialize price service
            await price_service.initialize()
            
            # Test getting SOL price
            sol_price = await price_service.get_sol_price_usd()
            logger.info(f"SOL price: ${sol_price:.2f}")
            
            # Test getting USDC price
            usdc_price = await price_service.get_usdc_price_usd()
            logger.info(f"USDC price: ${usdc_price:.2f}")
            
            # Test conversion
            sol_amount = 10.0
            usd_amount = await price_service.convert_sol_to_usd(sol_amount)
            logger.info(f"{sol_amount} SOL = ${usd_amount:.2f}")
            
            # Close price service
            await price_service.close()
            
            # Record test result
            self.results["tests"]["price_service"] = {
                "success": True,
                "sol_price": sol_price,
                "usdc_price": usdc_price,
                "timestamp": datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            logger.error(f"Error testing price service: {str(e)}")
            
            # Record test result
            self.results["tests"]["price_service"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return False
    
    async def test_enhanced_api_manager(self) -> bool:
        """
        Test the enhanced API manager.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Testing enhanced API manager...")
        
        try:
            # Import API manager
            from phase_4_deployment.apis.enhanced_api_manager import get_api_manager
            
            # Get API manager instance
            api_manager = get_api_manager()
            
            # Initialize API manager
            await api_manager.initialize()
            
            # Test getting Birdeye provider
            birdeye_provider = await api_manager.get_provider("birdeye")
            logger.info(f"Birdeye provider: {birdeye_provider.name}")
            
            # Test getting Solana RPC provider
            solana_provider = await api_manager.get_provider("solana_rpc")
            logger.info(f"Solana RPC provider: {solana_provider.name}")
            
            # Test API call
            sol_address = "So11111111111111111111111111111111111111112"
            result = await api_manager.call_api(
                api_type="birdeye",
                endpoint="/public/price",
                params={"address": sol_address},
                cache_key=f"test_price_{sol_address}",
                cache_ttl=60
            )
            
            if result:
                logger.info(f"API call successful: {result}")
            else:
                logger.warning("API call returned no data")
            
            # Close API manager
            await api_manager.close()
            
            # Record test result
            self.results["tests"]["enhanced_api_manager"] = {
                "success": True,
                "birdeye_provider": birdeye_provider.name,
                "solana_provider": solana_provider.name,
                "timestamp": datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            logger.error(f"Error testing enhanced API manager: {str(e)}")
            
            # Record test result
            self.results["tests"]["enhanced_api_manager"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return False
    
    async def test_advanced_models_wrapper(self) -> bool:
        """
        Test the advanced models wrapper.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Testing advanced models wrapper...")
        
        try:
            # Import advanced models wrapper
            from phase_4_deployment.unified_dashboard.components.advanced_models_wrapper import advanced_models_wrapper
            
            # Test initialization
            logger.info("Advanced models module available: " + 
                      str(advanced_models_wrapper.advanced_models_module is not None))
            logger.info("Fallback module available: " + 
                      str(advanced_models_wrapper.fallback_module is not None))
            
            # Record test result
            self.results["tests"]["advanced_models_wrapper"] = {
                "success": True,
                "advanced_models_available": advanced_models_wrapper.advanced_models_module is not None,
                "fallback_available": advanced_models_wrapper.fallback_module is not None,
                "timestamp": datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            logger.error(f"Error testing advanced models wrapper: {str(e)}")
            
            # Record test result
            self.results["tests"]["advanced_models_wrapper"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return False
    
    async def test_enhanced_wallet_metrics(self) -> bool:
        """
        Test the enhanced wallet metrics.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Testing enhanced wallet metrics...")
        
        try:
            # Import enhanced wallet metrics
            from phase_4_deployment.unified_dashboard.components.enhanced_wallet_metrics import get_token_prices
            
            # Test getting token prices
            prices = await get_token_prices()
            logger.info(f"Token prices: {prices}")
            
            # Record test result
            self.results["tests"]["enhanced_wallet_metrics"] = {
                "success": True,
                "prices": prices,
                "timestamp": datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            logger.error(f"Error testing enhanced wallet metrics: {str(e)}")
            
            # Record test result
            self.results["tests"]["enhanced_wallet_metrics"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return False
    
    async def run_tests(self) -> Dict[str, Any]:
        """
        Run all tests.
        
        Returns:
            Test results
        """
        logger.info("Running integration tests...")
        
        # Test price service
        price_service_result = await self.test_price_service()
        self.results["overall"]["total"] += 1
        if price_service_result:
            self.results["overall"]["passed"] += 1
        else:
            self.results["overall"]["failed"] += 1
            self.results["overall"]["success"] = False
        
        # Test enhanced API manager
        api_manager_result = await self.test_enhanced_api_manager()
        self.results["overall"]["total"] += 1
        if api_manager_result:
            self.results["overall"]["passed"] += 1
        else:
            self.results["overall"]["failed"] += 1
            self.results["overall"]["success"] = False
        
        # Test advanced models wrapper
        advanced_models_result = await self.test_advanced_models_wrapper()
        self.results["overall"]["total"] += 1
        if advanced_models_result:
            self.results["overall"]["passed"] += 1
        else:
            self.results["overall"]["failed"] += 1
            self.results["overall"]["success"] = False
        
        # Test enhanced wallet metrics
        wallet_metrics_result = await self.test_enhanced_wallet_metrics()
        self.results["overall"]["total"] += 1
        if wallet_metrics_result:
            self.results["overall"]["passed"] += 1
        else:
            self.results["overall"]["failed"] += 1
            self.results["overall"]["success"] = False
        
        # Update timestamp
        self.results["timestamp"] = datetime.now().isoformat()
        
        return self.results
    
    def save_results(self, output_path: str) -> None:
        """
        Save test results to file.
        
        Args:
            output_path: Path to output file
        """
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")


async def main():
    """Main function."""
    # Create tester
    tester = IntegrationTester()
    
    # Run tests
    results = await tester.run_tests()
    
    # Save results
    tester.save_results("integration_test_results.json")
    
    # Print summary
    logger.info(f"Tests: {results['overall']['passed']}/{results['overall']['total']} passed")
    logger.info(f"Overall success: {results['overall']['success']}")
    
    # Return exit code
    return 0 if results["overall"]["success"] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
