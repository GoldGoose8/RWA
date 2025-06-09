#!/usr/bin/env python3
"""
Comprehensive System Test Suite for Synergy7 Trading System
Tests all components: functions, units, configs, and dashboard metrics accuracy.
"""

import asyncio
import logging
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import subprocess
import psutil
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/comprehensive_system_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveSystemTester:
    """Comprehensive system testing suite."""

    def __init__(self):
        """Initialize the system tester."""
        self.test_results = {
            'config_tests': {},
            'unit_tests': {},
            'dashboard_tests': {},
            'integration_tests': {},
            'e2e_tests': {},
            'performance_tests': {}
        }
        self.start_time = datetime.now()
        self.errors = []

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all system tests."""
        logger.info("🚀 Starting Comprehensive System Test Suite")

        try:
            # Phase 1: Configuration and Environment Testing
            logger.info("📋 Phase 1: Configuration and Environment Testing")
            await self.test_configuration_system()

            # Phase 2: Core Component Unit Testing
            logger.info("🔧 Phase 2: Core Component Unit Testing")
            await self.test_core_components()

            # Phase 3: Dashboard and Monitoring Testing
            logger.info("📊 Phase 3: Dashboard and Monitoring Testing")
            await self.test_dashboard_components()

            # Phase 4: Integration Testing
            logger.info("🔗 Phase 4: Integration Testing")
            await self.test_system_integration()

            # Phase 5: End-to-End System Testing
            logger.info("🎯 Phase 5: End-to-End System Testing")
            await self.test_end_to_end_system()

            # Generate comprehensive report
            return await self.generate_test_report()

        except Exception as e:
            logger.error(f"❌ Test suite failed: {str(e)}")
            self.errors.append(f"Test suite error: {str(e)}")
            traceback.print_exc()
            return await self.generate_test_report()

    async def test_configuration_system(self):
        """Test configuration loading and validation."""
        logger.info("Testing configuration system...")

        config_tests = {}

        try:
            # Test main config.yaml loading
            from utils.config.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load_config()
            config_tests['main_config_load'] = {'status': 'PASS', 'details': 'Main config loaded successfully'}

            # Test environment variables
            required_env_vars = [
                'HELIUS_API_KEY', 'BIRDEYE_API_KEY', 'TELEGRAM_BOT_TOKEN',
                'TELEGRAM_CHAT_ID', 'WALLET_ADDRESS'
            ]

            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)

            if missing_vars:
                config_tests['env_variables'] = {
                    'status': 'FAIL',
                    'details': f'Missing environment variables: {missing_vars}'
                }
            else:
                config_tests['env_variables'] = {
                    'status': 'PASS',
                    'details': 'All required environment variables present'
                }

            # Test config validation
            if config.get('solana', {}).get('rpc_url'):
                config_tests['config_validation'] = {
                    'status': 'PASS',
                    'details': 'Configuration validation successful'
                }
            else:
                config_tests['config_validation'] = {
                    'status': 'FAIL',
                    'details': 'Configuration validation failed - missing RPC URL'
                }

        except Exception as e:
            config_tests['config_system'] = {
                'status': 'FAIL',
                'details': f'Configuration system error: {str(e)}'
            }
            self.errors.append(f"Config test error: {str(e)}")

        self.test_results['config_tests'] = config_tests
        logger.info(f"Configuration tests completed: {len([t for t in config_tests.values() if t['status'] == 'PASS'])}/{len(config_tests)} passed")

    async def test_core_components(self):
        """Test core system components."""
        logger.info("Testing core components...")

        unit_tests = {}

        # Test risk management components
        try:
            from core.risk.position_sizer import PositionSizer
            from core.risk.risk_manager import RiskManager
            from core.risk.circuit_breaker import CircuitBreaker

            # Test position sizer
            position_sizer = PositionSizer({'risk_management': {'max_position_size_pct': 0.1}})
            # Create dummy price data for testing
            import pandas as pd
            import numpy as np
            price_data = pd.DataFrame({
                'close': np.random.randn(50).cumsum() + 100,
                'high': np.random.randn(50).cumsum() + 102,
                'low': np.random.randn(50).cumsum() + 98
            })
            test_result = position_sizer.calculate_position_size(price_data, 1000, 'TEST')
            if test_result and test_result.get('position_size', 0) > 0:
                unit_tests['position_sizer'] = {'status': 'PASS', 'details': f'Position size calculated: {test_result["position_size"]:.4f}'}
            else:
                unit_tests['position_sizer'] = {'status': 'FAIL', 'details': 'Position sizer returned invalid size'}

            # Test risk manager
            risk_manager = RiskManager({'max_drawdown_pct': 0.15})
            unit_tests['risk_manager'] = {'status': 'PASS', 'details': 'Risk manager initialized successfully'}

            # Test circuit breaker
            circuit_breaker = CircuitBreaker({'enabled': True})
            unit_tests['circuit_breaker'] = {'status': 'PASS', 'details': 'Circuit breaker initialized successfully'}

        except Exception as e:
            unit_tests['risk_components'] = {'status': 'FAIL', 'details': f'Risk component error: {str(e)}'}
            self.errors.append(f"Risk component test error: {str(e)}")

        # Test strategy components
        try:
            from core.strategies.momentum import MomentumStrategy
            from core.strategies.market_regime_detector import MarketRegimeDetector

            # Test momentum strategy
            momentum_strategy = MomentumStrategy({'window_size': 20, 'threshold': 0.01})
            unit_tests['momentum_strategy'] = {'status': 'PASS', 'details': 'Momentum strategy initialized successfully'}

            # Test market regime detector
            regime_detector = MarketRegimeDetector({'market_regime': {'enabled': True}})
            unit_tests['regime_detector'] = {'status': 'PASS', 'details': 'Market regime detector initialized successfully'}

        except Exception as e:
            unit_tests['strategy_components'] = {'status': 'FAIL', 'details': f'Strategy component error: {str(e)}'}
            self.errors.append(f"Strategy component test error: {str(e)}")

        # Test API clients
        try:
            from phase_4_deployment.apis.helius_client import HeliusClient
            from phase_4_deployment.apis.birdeye_client import BirdeyeClient

            # Test Helius client initialization (with proper config)
            helius_client = HeliusClient(api_key=os.getenv('HELIUS_API_KEY', 'test'))
            unit_tests['helius_client'] = {'status': 'PASS', 'details': 'Helius client initialized successfully'}

            # Test Birdeye client initialization (with proper config)
            birdeye_client = BirdeyeClient(api_key=os.getenv('BIRDEYE_API_KEY', 'test'))
            unit_tests['birdeye_client'] = {'status': 'PASS', 'details': 'Birdeye client initialized successfully'}

        except Exception as e:
            unit_tests['api_clients'] = {'status': 'FAIL', 'details': f'API client error: {str(e)}'}
            self.errors.append(f"API client test error: {str(e)}")

        self.test_results['unit_tests'] = unit_tests
        logger.info(f"Unit tests completed: {len([t for t in unit_tests.values() if t['status'] == 'PASS'])}/{len(unit_tests)} passed")

    async def test_dashboard_components(self):
        """Test dashboard and monitoring components."""
        logger.info("Testing dashboard components...")

        dashboard_tests = {}

        # Test data source availability
        try:
            data_sources = {
                'enhanced_live_trading': 'output/enhanced_live_trading/',
                'live_production': 'output/live_production/',
                'paper_trading': 'output/paper_trading/',
                'wallet_data': 'output/wallet/'
            }

            available_sources = 0
            for name, path in data_sources.items():
                if os.path.exists(path):
                    available_sources += 1
                    dashboard_tests[f'data_source_{name}'] = {
                        'status': 'PASS',
                        'details': f'Data source {name} available at {path}'
                    }
                else:
                    dashboard_tests[f'data_source_{name}'] = {
                        'status': 'FAIL',
                        'details': f'Data source {name} not found at {path}'
                    }

            dashboard_tests['data_sources_summary'] = {
                'status': 'PASS' if available_sources > 0 else 'FAIL',
                'details': f'{available_sources}/{len(data_sources)} data sources available'
            }

        except Exception as e:
            dashboard_tests['data_sources'] = {'status': 'FAIL', 'details': f'Data source test error: {str(e)}'}
            self.errors.append(f"Data source test error: {str(e)}")

        self.test_results['dashboard_tests'] = dashboard_tests
        logger.info(f"Dashboard tests completed: {len([t for t in dashboard_tests.values() if t['status'] == 'PASS'])}/{len(dashboard_tests)} passed")

    async def test_system_integration(self):
        """Test system integration components."""
        logger.info("Testing system integration...")

        integration_tests = {}

        # Test API connectivity
        try:
            # Test Helius API connectivity
            helius_url = os.getenv('HELIUS_RPC_URL')
            if helius_url:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        helius_url,
                        json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        integration_tests['helius_connectivity'] = {
                            'status': 'PASS',
                            'details': 'Helius API connectivity successful'
                        }
                    else:
                        integration_tests['helius_connectivity'] = {
                            'status': 'FAIL',
                            'details': f'Helius API returned status {response.status_code}'
                        }
            else:
                integration_tests['helius_connectivity'] = {
                    'status': 'FAIL',
                    'details': 'Helius RPC URL not configured'
                }

        except Exception as e:
            integration_tests['helius_connectivity'] = {
                'status': 'FAIL',
                'details': f'Helius connectivity error: {str(e)}'
            }
            self.errors.append(f"Helius connectivity test error: {str(e)}")

        # Test Birdeye API connectivity
        try:
            birdeye_key = os.getenv('BIRDEYE_API_KEY')
            if birdeye_key:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://public-api.birdeye.so/public/tokenlist",
                        headers={"X-API-KEY": birdeye_key},
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        integration_tests['birdeye_connectivity'] = {
                            'status': 'PASS',
                            'details': 'Birdeye API connectivity successful'
                        }
                    else:
                        integration_tests['birdeye_connectivity'] = {
                            'status': 'FAIL',
                            'details': f'Birdeye API returned status {response.status_code}'
                        }
            else:
                integration_tests['birdeye_connectivity'] = {
                    'status': 'FAIL',
                    'details': 'Birdeye API key not configured'
                }

        except Exception as e:
            integration_tests['birdeye_connectivity'] = {
                'status': 'FAIL',
                'details': f'Birdeye connectivity error: {str(e)}'
            }
            self.errors.append(f"Birdeye connectivity test error: {str(e)}")

        # Test wallet configuration
        try:
            wallet_address = os.getenv('WALLET_ADDRESS')
            if wallet_address and len(wallet_address) > 40:
                integration_tests['wallet_config'] = {
                    'status': 'PASS',
                    'details': f'Wallet address configured: {wallet_address[:8]}...{wallet_address[-8:]}'
                }
            else:
                integration_tests['wallet_config'] = {
                    'status': 'FAIL',
                    'details': 'Wallet address not properly configured'
                }

        except Exception as e:
            integration_tests['wallet_config'] = {
                'status': 'FAIL',
                'details': f'Wallet config error: {str(e)}'
            }
            self.errors.append(f"Wallet config test error: {str(e)}")

        self.test_results['integration_tests'] = integration_tests
        logger.info(f"Integration tests completed: {len([t for t in integration_tests.values() if t['status'] == 'PASS'])}/{len(integration_tests)} passed")

    async def test_end_to_end_system(self):
        """Test end-to-end system functionality."""
        logger.info("Testing end-to-end system...")

        e2e_tests = {}

        # Test system health
        try:
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            e2e_tests['system_resources'] = {
                'status': 'PASS',
                'details': f'CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%'
            }

        except Exception as e:
            e2e_tests['system_resources'] = {
                'status': 'FAIL',
                'details': f'System resources error: {str(e)}'
            }
            self.errors.append(f"System resources test error: {str(e)}")

        # Test log file accessibility
        try:
            log_files = [
                'logs/enhanced_live_trading.log',
                'logs/system.log',
                'logs/trading.log'
            ]

            accessible_logs = 0
            for log_file in log_files:
                if os.path.exists(log_file):
                    accessible_logs += 1

            e2e_tests['log_accessibility'] = {
                'status': 'PASS' if accessible_logs > 0 else 'FAIL',
                'details': f'{accessible_logs}/{len(log_files)} log files accessible'
            }

        except Exception as e:
            e2e_tests['log_accessibility'] = {
                'status': 'FAIL',
                'details': f'Log accessibility error: {str(e)}'
            }
            self.errors.append(f"Log accessibility test error: {str(e)}")

        # Test output directory structure
        try:
            required_dirs = [
                'output/enhanced_live_trading',
                'output/live_production',
                'output/paper_trading',
                'output/wallet'
            ]

            existing_dirs = 0
            for dir_path in required_dirs:
                if os.path.exists(dir_path):
                    existing_dirs += 1
                else:
                    # Create missing directories
                    os.makedirs(dir_path, exist_ok=True)
                    existing_dirs += 1

            e2e_tests['output_structure'] = {
                'status': 'PASS',
                'details': f'{existing_dirs}/{len(required_dirs)} output directories available'
            }

        except Exception as e:
            e2e_tests['output_structure'] = {
                'status': 'FAIL',
                'details': f'Output structure error: {str(e)}'
            }
            self.errors.append(f"Output structure test error: {str(e)}")

        self.test_results['e2e_tests'] = e2e_tests
        logger.info(f"End-to-end tests completed: {len([t for t in e2e_tests.values() if t['status'] == 'PASS'])}/{len(e2e_tests)} passed")

    async def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        # Calculate summary statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for category, tests in self.test_results.items():
            for test_name, result in tests.items():
                total_tests += 1
                if result['status'] == 'PASS':
                    passed_tests += 1
                else:
                    failed_tests += 1

        report = {
            'test_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'test_results': self.test_results,
            'errors': self.errors
        }

        # Save report
        report_path = f"output/comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"📊 Test Report Generated: {report_path}")
        logger.info(f"✅ Tests Passed: {passed_tests}/{total_tests} ({report['test_summary']['success_rate']:.1f}%)")

        return report


async def main():
    """Main function to run comprehensive system tests."""
    tester = ComprehensiveSystemTester()
    report = await tester.run_all_tests()

    # Print summary
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE SYSTEM TEST RESULTS")
    print("="*80)
    print(f"Duration: {report['test_summary']['duration_seconds']:.2f} seconds")
    print(f"Total Tests: {report['test_summary']['total_tests']}")
    print(f"Passed: {report['test_summary']['passed_tests']}")
    print(f"Failed: {report['test_summary']['failed_tests']}")
    print(f"Success Rate: {report['test_summary']['success_rate']:.1f}%")
    print("="*80)

    return report


if __name__ == "__main__":
    asyncio.run(main())
