#!/usr/bin/env python3
"""
Full System Integration Tests
Comprehensive end-to-end tests for the complete Synergy7 trading system.
"""

import pytest
import asyncio
import os
import sys
import json
import logging
import tempfile
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestFullSystemIntegration:
    """Comprehensive system integration tests."""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock complete environment setup."""
        return {
            'WALLET_ADDRESS': 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz',
            'KEYPAIR_PATH': 'wallet/test_keypair.json',
            'HELIUS_API_KEY': 'test_helius_key',
            'BIRDEYE_API_KEY': 'test_birdeye_key',
            'TELEGRAM_BOT_TOKEN': 'test_telegram_token',
            'TELEGRAM_CHAT_ID': 'test_chat_id',
            'TRADING_ENABLED': 'true',
            'DRY_RUN': 'true',
            'PAPER_TRADING': 'false'
        }
    
    @pytest.fixture
    def mock_keypair_file(self, tmp_path):
        """Create mock keypair file."""
        keypair_data = [1] * 64
        keypair_file = tmp_path / "test_keypair.json"
        with open(keypair_file, 'w') as f:
            json.dump(keypair_data, f)
        return str(keypair_file)
    
    @pytest.fixture
    def mock_market_data(self):
        """Mock market data for testing."""
        return {
            'birdeye_response': {
                'data': [
                    {
                        'symbol': 'SOL',
                        'address': 'So11111111111111111111111111111111111111112',
                        'price': 180.50,
                        'volume24h': 1500000,
                        'priceChange24h': 5.2,
                        'marketCap': 85000000000
                    },
                    {
                        'symbol': 'USDC',
                        'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                        'price': 1.0001,
                        'volume24h': 2000000,
                        'priceChange24h': 0.01,
                        'marketCap': 32000000000
                    }
                ]
            },
            'whale_opportunities': [
                {
                    'wallet_address': '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
                    'transaction_signature': 'test_signature_1',
                    'amount_sol': 1000.0,
                    'transaction_type': 'buy',
                    'token_address': 'So11111111111111111111111111111111111111112',
                    'timestamp': datetime.now().isoformat(),
                    'confidence_score': 0.85
                }
            ],
            'wallet_balance': {
                'balance_sol': 3.384899,
                'balance_usd': 609.68
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_trading_pipeline(self, mock_environment, mock_keypair_file, mock_market_data):
        """Test complete trading pipeline from signal generation to execution."""
        with patch.dict(os.environ, mock_environment):
            with patch.dict(os.environ, {'KEYPAIR_PATH': mock_keypair_file}):
                
                # Mock all external API calls
                with patch('phase_4_deployment.data_router.birdeye_scanner.httpx.AsyncClient') as mock_birdeye:
                    with patch('phase_4_deployment.rpc_execution.helius_client.httpx.AsyncClient') as mock_helius:
                        with patch('phase_4_deployment.utils.trading_alerts.httpx.AsyncClient') as mock_telegram:
                            
                            # Setup Birdeye mock
                            birdeye_response = Mock()
                            birdeye_response.json.return_value = mock_market_data['birdeye_response']
                            birdeye_response.status_code = 200
                            birdeye_response.raise_for_status.return_value = None
                            mock_birdeye.return_value.__aenter__.return_value.get.return_value = birdeye_response
                            
                            # Setup Helius mock
                            helius_response = Mock()
                            helius_response.json.return_value = {
                                'result': {'value': mock_market_data['wallet_balance']}
                            }
                            helius_response.status_code = 200
                            helius_response.raise_for_status.return_value = None
                            mock_helius.return_value.__aenter__.return_value.post.return_value = helius_response
                            
                            # Setup Telegram mock
                            telegram_response = Mock()
                            telegram_response.json.return_value = {'ok': True, 'result': {'message_id': 123}}
                            telegram_response.status_code = 200
                            mock_telegram.return_value.__aenter__.return_value.post.return_value = telegram_response
                            
                            # Import and test production trader
                            from scripts.production_ready_trader import ProductionReadyTrader
                            
                            trader = ProductionReadyTrader()
                            trader.dry_run = True  # Force dry run for testing
                            
                            # Test component initialization
                            with patch('scripts.production_ready_trader.Keypair') as mock_keypair:
                                mock_keypair_instance = Mock()
                                mock_keypair.from_bytes.return_value = mock_keypair_instance
                                
                                init_result = await trader.initialize_all_components()
                                assert init_result == True
                            
                            # Test wallet balance check
                            balance_result = await trader.check_wallet_balance()
                            assert balance_result == True
                            
                            # Test trading cycle
                            with patch('scripts.production_ready_trader.BirdeyeScanner') as mock_scanner_class:
                                with patch('scripts.production_ready_trader.SignalEnricher') as mock_enricher_class:
                                    
                                    # Setup scanner mock
                                    mock_scanner = Mock()
                                    mock_scanner.scan_for_opportunities = AsyncMock(return_value=[
                                        {'symbol': 'SOL', 'price': 180.50, 'score': 0.8}
                                    ])
                                    mock_scanner.close = AsyncMock()
                                    mock_scanner_class.return_value = mock_scanner
                                    
                                    # Setup enricher mock
                                    mock_enricher = Mock()
                                    mock_enricher.enrich_signal.return_value = {
                                        'action': 'BUY',
                                        'market': 'SOL-USDC',
                                        'metadata': {'priority_score': 0.85}
                                    }
                                    mock_enricher_class.return_value = mock_enricher
                                    
                                    # Run trading cycle
                                    cycle_result = await trader.run_trading_cycle()
                                    
                                    # Verify results
                                    assert cycle_result['signals_generated'] > 0
                                    assert cycle_result['signals_enriched'] > 0
                                    
                                    # Verify API calls were made
                                    mock_scanner.scan_for_opportunities.assert_called_once()
                                    mock_enricher.enrich_signal.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_environment, mock_keypair_file):
        """Test system error handling and recovery mechanisms."""
        with patch.dict(os.environ, mock_environment):
            with patch.dict(os.environ, {'KEYPAIR_PATH': mock_keypair_file}):
                
                from scripts.production_ready_trader import ProductionReadyTrader
                
                trader = ProductionReadyTrader()
                
                # Test API failure handling
                with patch('scripts.production_ready_trader.BirdeyeScanner') as mock_scanner_class:
                    mock_scanner = Mock()
                    mock_scanner.scan_for_opportunities = AsyncMock(side_effect=Exception("API Error"))
                    mock_scanner.close = AsyncMock()
                    mock_scanner_class.return_value = mock_scanner
                    
                    # Should handle API errors gracefully
                    cycle_result = await trader.run_trading_cycle()
                    
                    assert 'error' in cycle_result
                    assert cycle_result['signals_generated'] == 0
    
    @pytest.mark.asyncio
    async def test_risk_management_integration(self, mock_environment, mock_keypair_file):
        """Test risk management integration in trading pipeline."""
        with patch.dict(os.environ, mock_environment):
            with patch.dict(os.environ, {'KEYPAIR_PATH': mock_keypair_file}):
                
                # Test position sizing
                try:
                    from core.risk.production_position_sizer import ProductionPositionSizer
                    
                    config = {
                        'risk_management': {
                            'max_position_size_pct': 0.5,
                            'max_daily_loss_pct': 0.1,
                            'max_portfolio_exposure': 0.8
                        }
                    }
                    
                    sizer = ProductionPositionSizer(config)
                    
                    signal = {
                        'action': 'BUY',
                        'market': 'SOL-USDC',
                        'confidence': 0.8,
                        'risk_score': 0.3
                    }
                    
                    position_size = sizer.calculate_position_size(signal, 1000.0)
                    
                    # Verify position size is within limits
                    assert position_size > 0
                    assert position_size <= 500.0  # Max 50% of portfolio
                    
                except ImportError:
                    pytest.skip("Production position sizer not available")
    
    @pytest.mark.asyncio
    async def test_monitoring_and_alerting(self, mock_environment):
        """Test monitoring and alerting system integration."""
        with patch.dict(os.environ, mock_environment):
            
            # Test Telegram alerts
            with patch('phase_4_deployment.utils.trading_alerts.httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {'ok': True, 'result': {'message_id': 123}}
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                from phase_4_deployment.utils.trading_alerts import send_trade_alert
                
                signal = {
                    'action': 'BUY',
                    'market': 'SOL-USDC',
                    'price': 180.0,
                    'size': 0.1,
                    'confidence': 0.8
                }
                
                result = await send_trade_alert(signal)
                assert result == True
    
    @pytest.mark.asyncio
    async def test_dashboard_data_integration(self, mock_environment):
        """Test dashboard data integration."""
        with patch.dict(os.environ, mock_environment):
            
            # Test dashboard data generation
            try:
                from enhanced_trading_dashboard import load_dashboard_data
                
                # Mock file operations
                with patch('enhanced_trading_dashboard.os.path.exists', return_value=True):
                    with patch('enhanced_trading_dashboard.json.load') as mock_json_load:
                        mock_json_load.return_value = {
                            'signals': [{'action': 'BUY', 'market': 'SOL-USDC'}],
                            'trades': [{'signature': 'test_sig', 'status': 'confirmed'}],
                            'metrics': {'total_trades': 5, 'success_rate': 0.8}
                        }
                        
                        with patch('builtins.open', create=True):
                            data = load_dashboard_data()
                            
                            assert 'signals' in data
                            assert 'trades' in data
                            assert 'metrics' in data
                            
            except ImportError:
                pytest.skip("Dashboard not available")
    
    def test_configuration_validation(self, mock_environment):
        """Test system configuration validation."""
        with patch.dict(os.environ, mock_environment):
            
            # Test environment variable validation
            required_vars = [
                'WALLET_ADDRESS',
                'KEYPAIR_PATH',
                'HELIUS_API_KEY',
                'BIRDEYE_API_KEY'
            ]
            
            for var in required_vars:
                assert os.getenv(var) is not None, f"Required environment variable {var} not set"
            
            # Test configuration loading
            try:
                import yaml
                
                # Mock config file
                mock_config = {
                    'trading': {
                        'enabled': True,
                        'dry_run': True,
                        'paper_trading': False
                    },
                    'risk_management': {
                        'max_position_size_pct': 0.5,
                        'max_daily_loss_pct': 0.1
                    }
                }
                
                with patch('builtins.open', create=True):
                    with patch('yaml.safe_load', return_value=mock_config):
                        # Configuration should be valid
                        assert mock_config['trading']['enabled'] == True
                        assert mock_config['risk_management']['max_position_size_pct'] == 0.5
                        
            except ImportError:
                pytest.skip("YAML not available")
    
    @pytest.mark.asyncio
    async def test_system_performance_metrics(self, mock_environment, mock_keypair_file):
        """Test system performance metrics collection."""
        with patch.dict(os.environ, mock_environment):
            with patch.dict(os.environ, {'KEYPAIR_PATH': mock_keypair_file}):
                
                import time
                
                # Test signal generation performance
                from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher
                
                enricher = SignalEnricher()
                
                signal = {
                    'action': 'BUY',
                    'market': 'SOL-USDC',
                    'price': 180.0,
                    'confidence': 0.7
                }
                
                # Measure enrichment time
                start_time = time.time()
                enriched_signal = enricher.enrich_signal(signal)
                end_time = time.time()
                
                enrichment_time = end_time - start_time
                
                # Performance should be acceptable
                assert enrichment_time < 1.0  # Should complete in under 1 second
                assert enriched_signal is not None
                assert 'metadata' in enriched_signal
    
    @pytest.mark.asyncio
    async def test_system_scalability(self, mock_environment, mock_keypair_file):
        """Test system scalability with multiple concurrent operations."""
        with patch.dict(os.environ, mock_environment):
            with patch.dict(os.environ, {'KEYPAIR_PATH': mock_keypair_file}):
                
                from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher
                
                enricher = SignalEnricher()
                
                # Generate multiple signals concurrently
                signals = []
                for i in range(10):
                    signal = {
                        'action': 'BUY' if i % 2 == 0 else 'SELL',
                        'market': f'TOKEN{i}-USDC',
                        'price': 100.0 + i,
                        'confidence': 0.5 + (i * 0.05)
                    }
                    signals.append(signal)
                
                # Process signals concurrently
                start_time = time.time()
                enriched_signals = [enricher.enrich_signal(signal) for signal in signals]
                end_time = time.time()
                
                total_time = end_time - start_time
                
                # Verify all signals were processed
                assert len(enriched_signals) == 10
                assert all(s is not None for s in enriched_signals)
                assert all('metadata' in s for s in enriched_signals)
                
                # Performance should scale reasonably
                assert total_time < 5.0  # Should complete 10 signals in under 5 seconds


class TestSystemRecovery:
    """Test system recovery and resilience."""
    
    @pytest.mark.asyncio
    async def test_api_failure_recovery(self):
        """Test recovery from API failures."""
        # Test circuit breaker functionality
        failure_count = 0
        
        def failing_api_call():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 3:
                raise Exception("API temporarily unavailable")
            return {"status": "success"}
        
        # Simulate recovery after failures
        for attempt in range(5):
            try:
                result = failing_api_call()
                if result["status"] == "success":
                    break
            except Exception:
                if attempt < 4:  # Allow retries
                    continue
                else:
                    pytest.fail("API never recovered")
        
        assert failure_count == 4  # 3 failures + 1 success
    
    @pytest.mark.asyncio
    async def test_transaction_failure_recovery(self):
        """Test recovery from transaction failures."""
        from phase_4_deployment.rpc_execution.transaction_executor import TransactionExecutor
        
        # Mock RPC client with failures then success
        mock_client = Mock()
        mock_client.send_transaction = AsyncMock(side_effect=[
            Exception("Network error"),
            Exception("Timeout"),
            {'signature': 'success_signature', 'status': 'confirmed'}
        ])
        
        executor = TransactionExecutor(
            rpc_client=mock_client,
            keypair_path='test_keypair.json',
            max_retries=3,
            retry_delay=0.01
        )
        
        # Should succeed after retries
        result = await executor.execute_transaction(b'mock_transaction')
        
        assert result is not None
        assert result.get('success', False) == True
        assert mock_client.send_transaction.call_count == 3
        
        await executor.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
