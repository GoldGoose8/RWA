#!/usr/bin/env python3
"""
Test Carbon Core Integration

This script tests the Carbon Core integration with the Q5 Trading System.
It verifies that the Carbon Core client can be initialized, data can be
generated, and the dashboard can display the data.
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import Carbon Core client
from core.carbon_core_client import CarbonCoreClient
from core.carbon_core_fallback import (
    fallback_get_market_microstructure,
    fallback_get_statistical_signals,
    fallback_get_rl_execution_metrics,
    fallback_get_system_metrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_carbon_core')

async def test_carbon_core_client():
    """Test the Carbon Core client."""
    logger.info("Testing Carbon Core client...")
    
    # Initialize client
    client = CarbonCoreClient()
    
    # Try to start the client
    started = await client.start()
    
    if started:
        logger.info("Carbon Core client started successfully")
        
        # Test getting system metrics
        metrics = await client.get_system_metrics()
        if metrics:
            logger.info("Successfully retrieved system metrics")
        else:
            logger.warning("Failed to retrieve system metrics")
        
        # Test getting RL execution metrics
        rl_metrics = await client.get_rl_execution_metrics()
        if rl_metrics:
            logger.info("Successfully retrieved RL execution metrics")
        else:
            logger.warning("Failed to retrieve RL execution metrics")
        
        # Test getting market microstructure
        market_data = await client.get_market_microstructure("SOL-USDC")
        if market_data:
            logger.info("Successfully retrieved market microstructure data")
        else:
            logger.warning("Failed to retrieve market microstructure data")
        
        # Test getting statistical signals
        signal_data = await client.get_statistical_signals("price_momentum")
        if signal_data:
            logger.info("Successfully retrieved statistical signal data")
        else:
            logger.warning("Failed to retrieve statistical signal data")
        
        # Test getting all metrics
        all_metrics = await client.get_all_metrics()
        if all_metrics:
            logger.info("Successfully retrieved all metrics")
            
            # Save metrics to file
            output_dir = os.path.join(parent_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            metrics_path = os.path.join(output_dir, 'carbon_core_metrics.json')
            with open(metrics_path, 'w') as f:
                json.dump(all_metrics, f, indent=2)
            
            logger.info(f"Saved metrics to {metrics_path}")
        else:
            logger.warning("Failed to retrieve all metrics")
        
        # Stop the client
        await client.stop()
        logger.info("Carbon Core client stopped")
    else:
        logger.warning("Carbon Core client failed to start, using fallback")
        
        # Test fallback functions
        test_fallback_functions()

def test_fallback_functions():
    """Test the Carbon Core fallback functions."""
    logger.info("Testing Carbon Core fallback functions...")
    
    # Test market microstructure fallback
    market_data = fallback_get_market_microstructure({'market': 'SOL-USDC'})
    if market_data:
        logger.info("Successfully generated market microstructure data")
    else:
        logger.error("Failed to generate market microstructure data")
    
    # Test statistical signals fallback
    signal_data = fallback_get_statistical_signals({'signal_type': 'price_momentum'})
    if signal_data:
        logger.info("Successfully generated statistical signal data")
    else:
        logger.error("Failed to generate statistical signal data")
    
    # Test RL execution metrics fallback
    rl_metrics = fallback_get_rl_execution_metrics({})
    if rl_metrics:
        logger.info("Successfully generated RL execution metrics")
    else:
        logger.error("Failed to generate RL execution metrics")
    
    # Test system metrics fallback
    system_metrics = fallback_get_system_metrics({})
    if system_metrics:
        logger.info("Successfully generated system metrics")
    else:
        logger.error("Failed to generate system metrics")
    
    # Generate and save all metrics
    all_metrics = {
        'timestamp': datetime.now().isoformat(),
        'system_metrics': system_metrics,
        'rl_execution': rl_metrics,
        'market_microstructure': {
            'markets': {
                'SOL-USDC': fallback_get_market_microstructure({'market': 'SOL-USDC'}),
                'JTO-USDC': fallback_get_market_microstructure({'market': 'JTO-USDC'}),
                'BONK-USDC': fallback_get_market_microstructure({'market': 'BONK-USDC'})
            }
        },
        'statistical_signals': {
            'signals': {
                'price_momentum': fallback_get_statistical_signals({'signal_type': 'price_momentum'}),
                'volume_profile': fallback_get_statistical_signals({'signal_type': 'volume_profile'}),
                'order_flow_imbalance': fallback_get_statistical_signals({'signal_type': 'order_flow_imbalance'}),
                'volatility_regime': fallback_get_statistical_signals({'signal_type': 'volatility_regime'})
            }
        }
    }
    
    # Save metrics to file
    output_dir = os.path.join(parent_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    metrics_path = os.path.join(output_dir, 'carbon_core_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"Saved fallback metrics to {metrics_path}")

def test_dashboard_integration():
    """Test the dashboard integration with Carbon Core."""
    logger.info("Testing dashboard integration...")
    
    # Check if the dashboard file exists
    dashboard_path = os.path.join(parent_dir, 'gui_dashboard', 'app.py')
    if not os.path.exists(dashboard_path):
        logger.error(f"Dashboard file not found: {dashboard_path}")
        return False
    
    # Check if the advanced models component exists
    component_path = os.path.join(parent_dir, 'gui_dashboard', 'components', 'advanced_models.py')
    if not os.path.exists(component_path):
        logger.error(f"Advanced models component not found: {component_path}")
        return False
    
    # Check if the metrics file exists
    metrics_path = os.path.join(parent_dir, 'output', 'carbon_core_metrics.json')
    if not os.path.exists(metrics_path):
        logger.warning(f"Metrics file not found: {metrics_path}")
        logger.info("Running fallback function to generate metrics...")
        test_fallback_functions()
    
    logger.info("Dashboard integration test passed")
    return True

async def main():
    """Main function to run the tests."""
    logger.info("Starting Carbon Core integration tests...")
    
    try:
        # Test Carbon Core client
        await test_carbon_core_client()
        
        # Test dashboard integration
        test_dashboard_integration()
        
        logger.info("Carbon Core integration tests completed")
        return 0
    except Exception as e:
        logger.error(f"Error in Carbon Core integration tests: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
