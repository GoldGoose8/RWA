#!/usr/bin/env python3
"""
Production Execution System for Synergy7 Trading System

This script demonstrates the complete execution system with all components
integrated for live trading production environment.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductionExecutionSystem:
    """
    Complete production execution system that integrates all execution components
    for live trading with proper error handling and monitoring.
    """

    def __init__(self):
        """Initialize the production execution system."""
        self.config = {
            'execution': {
                'max_concurrent_executions': 3,
                'execution_timeout': 30.0,
                'retry_delay': 2.0,
                'transaction_timeout': 30.0,
                'max_retries': 3
            },
            'order_management': {
                'db_path': 'output/production_orders.db',
                'max_history_size': 10000,
                'cleanup_interval': 3600,
                'order_timeout': 300
            },
            'metrics': {
                'metrics_db_path': 'output/production_metrics.db',
                'metrics_retention_days': 30,
                'cleanup_interval': 3600
            }
        }
        
        # Components
        self.execution_engine = None
        self.transaction_executor = None
        self.order_manager = None
        self.metrics = None
        self.modern_executor = None
        self.unified_tx_builder = None
        
        # System state
        self.running = False
        self.initialized = False
        
        logger.info("🚀 ProductionExecutionSystem initialized")

    async def initialize(self):
        """Initialize all execution system components."""
        try:
            logger.info("🔧 Initializing production execution system...")
            
            # Validate environment
            if not self._validate_environment():
                return False
            
            # Initialize core execution components
            await self._initialize_core_components()
            
            # Initialize modern executor and transaction builder
            await self._initialize_modern_components()
            
            # Initialize execution engine with all dependencies
            await self._initialize_execution_engine()
            
            self.initialized = True
            logger.info("✅ Production execution system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize production execution system: {e}")
            return False

    def _validate_environment(self) -> bool:
        """Validate required environment variables."""
        required_vars = [
            'WALLET_ADDRESS',
            'HELIUS_API_KEY',
            'KEYPAIR_PATH'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            return False
        
        # Check if keypair file exists
        keypair_path = os.getenv('KEYPAIR_PATH')
        if not os.path.exists(keypair_path):
            logger.error(f"❌ Keypair file not found: {keypair_path}")
            return False
        
        logger.info("✅ Environment validation passed")
        return True

    async def _initialize_core_components(self):
        """Initialize core execution components."""
        try:
            # Initialize execution metrics
            from core.execution.execution_metrics import ExecutionMetrics
            self.metrics = ExecutionMetrics(self.config['metrics'])
            await self.metrics.initialize()
            logger.info("✅ Execution metrics initialized")
            
            # Initialize order manager
            from core.execution.order_manager import OrderManager
            self.order_manager = OrderManager(self.config['order_management'])
            await self.order_manager.initialize()
            logger.info("✅ Order manager initialized")
            
            # Initialize transaction executor
            from core.execution.transaction_executor import TransactionExecutor
            self.transaction_executor = TransactionExecutor(self.config['execution'])
            logger.info("✅ Transaction executor initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize core components: {e}")
            raise

    async def _initialize_modern_components(self):
        """Initialize modern executor and transaction builder."""
        try:
            # Load keypair
            from solders.keypair import Keypair
            import json
            
            keypair_path = os.getenv('KEYPAIR_PATH')
            with open(keypair_path, 'r') as f:
                keypair_data = json.load(f)
            
            if isinstance(keypair_data, list) and len(keypair_data) == 64:
                keypair_bytes = bytes(keypair_data)
                keypair = Keypair.from_bytes(keypair_bytes)
            else:
                raise ValueError("Invalid keypair format")
            
            logger.info("✅ Keypair loaded successfully")
            
            # Initialize modern transaction executor
            from phase_4_deployment.rpc_execution.modern_transaction_executor import ModernTransactionExecutor
            
            helius_api_key = os.getenv('HELIUS_API_KEY')
            self.modern_executor = ModernTransactionExecutor(
                config={
                    'primary_rpc': os.getenv('QUICKNODE_RPC_URL'),
                    'fallback_rpc': None,  # No fallback RPC - QuickNode only
                    'jito_rpc': "https://ny.mainnet.block-engine.jito.wtf/api/v1",
                    'helius_api_key': None,  # Removed Helius
                    'quicknode_api_key': os.getenv('QUICKNODE_API_KEY'),
                    'timeout': 10.0,
                    'max_retries': 2,
                    'circuit_breaker_enabled': True,
                    'failure_threshold': 2,
                    'reset_timeout': 30
                }
            )
            await self.modern_executor.initialize()
            logger.info("✅ Modern transaction executor initialized")
            
            # Initialize unified transaction builder
            from core.dex.unified_transaction_builder import UnifiedTransactionBuilder
            
            wallet_address = os.getenv('WALLET_ADDRESS')
            self.unified_tx_builder = UnifiedTransactionBuilder(wallet_address, keypair)
            await self.unified_tx_builder.initialize()
            logger.info("✅ Unified transaction builder initialized")
            
            # Initialize transaction executor with modern components
            await self.transaction_executor.initialize(
                modern_executor=self.modern_executor,
                unified_tx_builder=self.unified_tx_builder
            )
            logger.info("✅ Transaction executor initialized with modern components")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize modern components: {e}")
            raise

    async def _initialize_execution_engine(self):
        """Initialize the main execution engine."""
        try:
            from core.execution.execution_engine import ExecutionEngine
            
            self.execution_engine = ExecutionEngine(self.config['execution'])
            await self.execution_engine.initialize(
                modern_executor=self.modern_executor,
                unified_tx_builder=self.unified_tx_builder,
                order_manager=self.order_manager,
                metrics=self.metrics
            )
            logger.info("✅ Execution engine initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize execution engine: {e}")
            raise

    async def start(self):
        """Start the production execution system."""
        if not self.initialized:
            logger.error("❌ System not initialized. Call initialize() first.")
            return False
        
        if self.running:
            logger.warning("⚠️ System already running")
            return True
        
        try:
            logger.info("🚀 Starting production execution system...")
            
            # Start execution engine
            await self.execution_engine.start()
            
            self.running = True
            logger.info("✅ Production execution system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start production execution system: {e}")
            return False

    async def stop(self):
        """Stop the production execution system."""
        if not self.running:
            logger.warning("⚠️ System not running")
            return
        
        try:
            logger.info("🛑 Stopping production execution system...")
            
            # Stop execution engine
            await self.execution_engine.stop()
            
            self.running = False
            logger.info("✅ Production execution system stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping production execution system: {e}")

    async def submit_trading_signal(self, signal: dict) -> str:
        """Submit a trading signal for execution."""
        if not self.running:
            raise RuntimeError("Execution system not running")
        
        try:
            logger.info(f"📝 Submitting trading signal: {signal['action']} {signal['market']} {signal['size']}")
            
            order_id = await self.execution_engine.submit_order(signal)
            logger.info(f"✅ Trading signal submitted with order ID: {order_id}")
            
            return order_id
            
        except Exception as e:
            logger.error(f"❌ Failed to submit trading signal: {e}")
            raise

    async def get_order_status(self, order_id: str) -> dict:
        """Get the status of an order."""
        try:
            return await self.execution_engine.get_order_status(order_id)
        except Exception as e:
            logger.error(f"❌ Failed to get order status: {e}")
            return None

    def get_system_status(self) -> dict:
        """Get comprehensive system status."""
        try:
            status = {
                'system': {
                    'initialized': self.initialized,
                    'running': self.running,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if self.execution_engine:
                status['execution_engine'] = self.execution_engine.get_execution_stats()
            
            if self.transaction_executor:
                status['transaction_executor'] = self.transaction_executor.get_metrics()
            
            if self.order_manager:
                status['order_manager'] = self.order_manager.get_statistics()
            
            if self.metrics:
                status['execution_metrics'] = self.metrics.get_current_stats()
                status['method_performance'] = self.metrics.get_method_performance()
                status['window_performance'] = self.metrics.get_window_performance('5min')
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get system status: {e}")
            return {'error': str(e)}

    async def run_demo(self):
        """Run a demonstration of the execution system."""
        try:
            logger.info("🎯 Running production execution system demo...")
            
            # Create sample trading signals
            demo_signals = [
                {
                    'id': 'demo_1',
                    'action': 'SELL',
                    'market': 'SOL-USDC',
                    'size': 0.01,
                    'price': 180.0,
                    'confidence': 0.8,
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'id': 'demo_2',
                    'action': 'BUY',
                    'market': 'SOL-USDC',
                    'size': 0.005,
                    'price': 180.0,
                    'confidence': 0.7,
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            # Submit signals
            order_ids = []
            for signal in demo_signals:
                order_id = await self.submit_trading_signal(signal)
                order_ids.append(order_id)
                await asyncio.sleep(2)  # Brief delay between submissions
            
            # Monitor execution
            logger.info("📊 Monitoring order execution...")
            for _ in range(30):  # Monitor for 30 seconds
                await asyncio.sleep(1)
                
                # Check order statuses
                all_completed = True
                for order_id in order_ids:
                    status = await self.get_order_status(order_id)
                    if status and status['status'] in ['pending', 'executing']:
                        all_completed = False
                
                if all_completed:
                    break
            
            # Print final status
            logger.info("📊 Final system status:")
            status = self.get_system_status()
            
            print("\n" + "="*60)
            print("PRODUCTION EXECUTION SYSTEM STATUS")
            print("="*60)
            
            if 'execution_engine' in status:
                stats = status['execution_engine']
                print(f"Total Orders: {stats['total_orders']}")
                print(f"Successful: {stats['successful_executions']}")
                print(f"Failed: {stats['failed_executions']}")
                print(f"Success Rate: {stats['success_rate_pct']}%")
                print(f"Avg Execution Time: {stats['average_execution_time']}s")
            
            if 'execution_metrics' in status:
                metrics = status['execution_metrics']
                print(f"Total Value Traded: {metrics['total_value_traded']} SOL")
                print(f"Total Fees Paid: {metrics['total_fees_paid']} SOL")
            
            print("="*60)
            
            logger.info("✅ Demo completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise


async def main():
    """Main function to run the production execution system."""
    system = ProductionExecutionSystem()
    
    try:
        # Initialize system
        if not await system.initialize():
            logger.error("❌ Failed to initialize system")
            return
        
        # Start system
        if not await system.start():
            logger.error("❌ Failed to start system")
            return
        
        # Run demo
        await system.run_demo()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        # Stop system
        await system.stop()
        logger.info("👋 Production execution system shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
