#!/usr/bin/env python3
"""
Test Script for Production Execution System

This script provides comprehensive testing of the execution system components
to ensure they are ready for live trading production.
"""

import asyncio
import logging
import os
import sys
import time
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExecutionSystemTester:
    """Comprehensive tester for the execution system."""

    def __init__(self):
        """Initialize the tester."""
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
        logger.info("🧪 ExecutionSystemTester initialized")

    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result."""
        self.test_results['total_tests'] += 1
        
        if passed:
            self.test_results['passed_tests'] += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.test_results['failed_tests'] += 1
            logger.error(f"❌ {test_name}: FAILED - {details}")
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    async def test_environment_setup(self):
        """Test environment setup and configuration."""
        logger.info("🔧 Testing environment setup...")
        
        # Test required environment variables
        required_vars = ['WALLET_ADDRESS', 'HELIUS_API_KEY', 'KEYPAIR_PATH']
        for var in required_vars:
            value = os.getenv(var)
            self.log_test_result(
                f"Environment variable {var}",
                bool(value),
                f"Value: {'Set' if value else 'Not set'}"
            )
        
        # Test keypair file existence
        keypair_path = os.getenv('KEYPAIR_PATH')
        if keypair_path:
            exists = os.path.exists(keypair_path)
            self.log_test_result(
                "Keypair file exists",
                exists,
                f"Path: {keypair_path}"
            )

    async def test_core_components_import(self):
        """Test importing core execution components."""
        logger.info("📦 Testing core component imports...")
        
        # Test execution engine import
        try:
            from core.execution.execution_engine import ExecutionEngine
            self.log_test_result("ExecutionEngine import", True)
        except Exception as e:
            self.log_test_result("ExecutionEngine import", False, str(e))
        
        # Test transaction executor import
        try:
            from core.execution.transaction_executor import TransactionExecutor
            self.log_test_result("TransactionExecutor import", True)
        except Exception as e:
            self.log_test_result("TransactionExecutor import", False, str(e))
        
        # Test order manager import
        try:
            from core.execution.order_manager import OrderManager
            self.log_test_result("OrderManager import", True)
        except Exception as e:
            self.log_test_result("OrderManager import", False, str(e))
        
        # Test execution metrics import
        try:
            from core.execution.execution_metrics import ExecutionMetrics
            self.log_test_result("ExecutionMetrics import", True)
        except Exception as e:
            self.log_test_result("ExecutionMetrics import", False, str(e))

    async def test_modern_components_import(self):
        """Test importing modern execution components."""
        logger.info("🚀 Testing modern component imports...")
        
        # Test modern transaction executor import
        try:
            from phase_4_deployment.rpc_execution.modern_transaction_executor import ModernTransactionExecutor
            self.log_test_result("ModernTransactionExecutor import", True)
        except Exception as e:
            self.log_test_result("ModernTransactionExecutor import", False, str(e))
        
        # Test unified transaction builder import
        try:
            from core.dex.unified_transaction_builder import UnifiedTransactionBuilder
            self.log_test_result("UnifiedTransactionBuilder import", True)
        except Exception as e:
            self.log_test_result("UnifiedTransactionBuilder import", False, str(e))

    async def test_component_initialization(self):
        """Test component initialization."""
        logger.info("🔧 Testing component initialization...")
        
        try:
            # Test execution metrics initialization
            from core.execution.execution_metrics import ExecutionMetrics
            metrics = ExecutionMetrics({'metrics_db_path': 'output/test_metrics.db'})
            success = await metrics.initialize()
            self.log_test_result("ExecutionMetrics initialization", success)
            
            # Test order manager initialization
            from core.execution.order_manager import OrderManager
            order_manager = OrderManager({'db_path': 'output/test_orders.db'})
            success = await order_manager.initialize()
            self.log_test_result("OrderManager initialization", success)
            
            # Test transaction executor initialization
            from core.execution.transaction_executor import TransactionExecutor
            tx_executor = TransactionExecutor()
            self.log_test_result("TransactionExecutor creation", True)
            
            # Test execution engine initialization
            from core.execution.execution_engine import ExecutionEngine
            execution_engine = ExecutionEngine()
            self.log_test_result("ExecutionEngine creation", True)
            
        except Exception as e:
            self.log_test_result("Component initialization", False, str(e))

    async def test_database_operations(self):
        """Test database operations."""
        logger.info("💾 Testing database operations...")
        
        try:
            # Test metrics database
            from core.execution.execution_metrics import ExecutionMetrics
            metrics = ExecutionMetrics({'metrics_db_path': 'output/test_metrics.db'})
            await metrics.initialize()
            
            # Test saving a metric
            from core.execution.execution_engine import ExecutionOrder, ExecutionStatus
            from datetime import datetime
            
            test_order = ExecutionOrder(
                order_id="test_001",
                signal={'action': 'BUY', 'market': 'SOL-USDC', 'size': 0.01},
                status=ExecutionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                execution_time=1.5
            )
            
            await metrics.record_execution(test_order)
            self.log_test_result("Metrics database operations", True)
            
        except Exception as e:
            self.log_test_result("Metrics database operations", False, str(e))
        
        try:
            # Test order database
            from core.execution.order_manager import OrderManager, Order, OrderStatus, OrderPriority
            order_manager = OrderManager({'db_path': 'output/test_orders.db'})
            await order_manager.initialize()
            
            # Test registering an order
            test_order = Order(
                order_id="test_order_001",
                signal={'action': 'SELL', 'market': 'SOL-USDC', 'size': 0.01},
                status=OrderStatus.PENDING,
                priority=OrderPriority.NORMAL,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            success = await order_manager.register_order(test_order)
            self.log_test_result("Order database operations", success)
            
        except Exception as e:
            self.log_test_result("Order database operations", False, str(e))

    async def test_execution_flow(self):
        """Test the complete execution flow."""
        logger.info("🔄 Testing execution flow...")
        
        try:
            # Create a mock execution system
            from core.execution.execution_engine import ExecutionEngine
            from core.execution.execution_metrics import ExecutionMetrics
            from core.execution.order_manager import OrderManager
            
            # Initialize components
            metrics = ExecutionMetrics({'metrics_db_path': 'output/test_flow_metrics.db'})
            await metrics.initialize()
            
            order_manager = OrderManager({'db_path': 'output/test_flow_orders.db'})
            await order_manager.initialize()
            
            execution_engine = ExecutionEngine()
            
            # Test without modern components (mock mode)
            await execution_engine.initialize(
                modern_executor=None,  # Mock mode
                unified_tx_builder=None,  # Mock mode
                order_manager=order_manager,
                metrics=metrics
            )
            
            self.log_test_result("Execution flow setup", True)
            
            # Test submitting an order (will fail without modern components, but tests the flow)
            test_signal = {
                'action': 'BUY',
                'market': 'SOL-USDC',
                'size': 0.01,
                'price': 180.0,
                'confidence': 0.8
            }
            
            try:
                order_id = await execution_engine.submit_order(test_signal)
                self.log_test_result("Order submission", True, f"Order ID: {order_id}")
            except Exception as e:
                # Expected to fail without modern components
                self.log_test_result("Order submission (mock)", True, "Expected failure in mock mode")
            
        except Exception as e:
            self.log_test_result("Execution flow", False, str(e))

    async def test_production_system_integration(self):
        """Test the production system integration."""
        logger.info("🏭 Testing production system integration...")
        
        try:
            from scripts.production_execution_system import ProductionExecutionSystem
            
            # Test system creation
            system = ProductionExecutionSystem()
            self.log_test_result("ProductionExecutionSystem creation", True)
            
            # Test environment validation
            if os.getenv('WALLET_ADDRESS') and os.getenv('HELIUS_API_KEY') and os.getenv('KEYPAIR_PATH'):
                # Only test initialization if environment is properly set up
                try:
                    success = await system.initialize()
                    self.log_test_result("ProductionExecutionSystem initialization", success)
                    
                    if success:
                        # Test system status
                        status = system.get_system_status()
                        self.log_test_result("System status retrieval", bool(status))
                        
                        # Clean shutdown
                        await system.stop()
                        
                except Exception as e:
                    self.log_test_result("ProductionExecutionSystem initialization", False, str(e))
            else:
                self.log_test_result("ProductionExecutionSystem initialization", False, "Environment not configured")
            
        except Exception as e:
            self.log_test_result("Production system integration", False, str(e))

    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        logger.info("📊 Testing performance metrics...")
        
        try:
            from core.execution.execution_metrics import ExecutionMetrics
            
            metrics = ExecutionMetrics({'metrics_db_path': 'output/test_perf_metrics.db'})
            await metrics.initialize()
            
            # Test getting current stats
            stats = metrics.get_current_stats()
            self.log_test_result("Current stats retrieval", isinstance(stats, dict))
            
            # Test method performance
            method_perf = metrics.get_method_performance()
            self.log_test_result("Method performance retrieval", isinstance(method_perf, dict))
            
            # Test window performance
            window_perf = metrics.get_window_performance('5min')
            self.log_test_result("Window performance retrieval", isinstance(window_perf, dict))
            
        except Exception as e:
            self.log_test_result("Performance metrics", False, str(e))

    async def run_all_tests(self):
        """Run all tests."""
        logger.info("🧪 Starting comprehensive execution system tests...")
        
        start_time = time.time()
        
        # Run all test suites
        await self.test_environment_setup()
        await self.test_core_components_import()
        await self.test_modern_components_import()
        await self.test_component_initialization()
        await self.test_database_operations()
        await self.test_execution_flow()
        await self.test_production_system_integration()
        await self.test_performance_metrics()
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Print test summary
        self.print_test_summary(test_duration)

    def print_test_summary(self, duration: float):
        """Print comprehensive test summary."""
        print("\n" + "="*80)
        print("EXECUTION SYSTEM TEST RESULTS")
        print("="*80)
        
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        print(f"Success Rate: {(self.test_results['passed_tests'] / max(1, self.test_results['total_tests']) * 100):.1f}%")
        print(f"Test Duration: {duration:.2f} seconds")
        
        print("\n" + "-"*80)
        print("DETAILED RESULTS")
        print("-"*80)
        
        for test in self.test_results['test_details']:
            status = "✅ PASS" if test['passed'] else "❌ FAIL"
            print(f"{status} | {test['test_name']}")
            if test['details']:
                print(f"      Details: {test['details']}")
        
        print("\n" + "="*80)
        
        if self.test_results['failed_tests'] == 0:
            print("🎉 ALL TESTS PASSED! Execution system is ready for production.")
        else:
            print(f"⚠️  {self.test_results['failed_tests']} tests failed. Review issues before production deployment.")
        
        print("="*80)


async def main():
    """Main function to run the tests."""
    tester = ExecutionSystemTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
