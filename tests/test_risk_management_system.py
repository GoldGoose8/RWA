#!/usr/bin/env python3
"""
Risk Management System Tests
Tests for the complete risk management and monitoring pipeline.
"""

import pytest
import asyncio
import os
import sys
import json
import logging
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestProductionPositionSizer:
    """Test suite for production position sizer."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'risk_management': {
                'max_position_size_pct': 0.5,
                'max_daily_loss_pct': 0.1,
                'max_portfolio_exposure': 0.8,
                'min_position_size_usd': 10.0,
                'max_position_size_usd': 1000.0
            },
            'trading': {
                'default_position_size_pct': 0.1,
                'max_concurrent_positions': 5
            }
        }
    
    def test_production_position_sizer_initialization(self, mock_config):
        """Test production position sizer initialization."""
        from core.risk.production_position_sizer import ProductionPositionSizer
        
        sizer = ProductionPositionSizer(mock_config)
        
        assert sizer.max_position_size_pct == 0.5
        assert sizer.max_daily_loss_pct == 0.1
        assert sizer.max_portfolio_exposure == 0.8
    
    def test_position_size_calculation(self, mock_config):
        """Test position size calculation logic."""
        from core.risk.production_position_sizer import ProductionPositionSizer
        
        sizer = ProductionPositionSizer(mock_config)
        
        # Test basic position sizing
        signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'confidence': 0.8,
            'risk_score': 0.3
        }
        
        portfolio_value = 1000.0  # $1000 portfolio
        
        position_size = sizer.calculate_position_size(signal, portfolio_value)
        
        # Should be within configured limits
        assert position_size > 0
        assert position_size <= portfolio_value * 0.5  # Max 50% position
        assert position_size >= 10.0  # Min position size
    
    def test_position_size_with_high_confidence(self, mock_config):
        """Test position sizing with high confidence signal."""
        from core.risk.production_position_sizer import ProductionPositionSizer
        
        sizer = ProductionPositionSizer(mock_config)
        
        high_confidence_signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'confidence': 0.95,
            'risk_score': 0.2
        }
        
        low_confidence_signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'confidence': 0.4,
            'risk_score': 0.7
        }
        
        portfolio_value = 1000.0
        
        high_position = sizer.calculate_position_size(high_confidence_signal, portfolio_value)
        low_position = sizer.calculate_position_size(low_confidence_signal, portfolio_value)
        
        # High confidence should result in larger position
        assert high_position > low_position
    
    def test_position_size_limits(self, mock_config):
        """Test position size limits enforcement."""
        from core.risk.production_position_sizer import ProductionPositionSizer
        
        sizer = ProductionPositionSizer(mock_config)
        
        signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'confidence': 1.0,  # Maximum confidence
            'risk_score': 0.0   # Minimum risk
        }
        
        # Test with small portfolio
        small_portfolio = 50.0  # $50 portfolio
        small_position = sizer.calculate_position_size(signal, small_portfolio)
        
        # Should respect minimum position size
        assert small_position >= 10.0
        
        # Test with large portfolio
        large_portfolio = 10000.0  # $10,000 portfolio
        large_position = sizer.calculate_position_size(signal, large_portfolio)
        
        # Should respect maximum position size
        assert large_position <= 1000.0


class TestRiskMonitoring:
    """Test suite for risk monitoring components."""
    
    @pytest.fixture
    def mock_portfolio_data(self):
        """Mock portfolio data for testing."""
        return {
            'total_value_usd': 5000.0,
            'total_value_sol': 27.78,
            'positions': [
                {
                    'symbol': 'SOL',
                    'amount': 25.0,
                    'value_usd': 4500.0,
                    'pnl_usd': 200.0,
                    'pnl_pct': 4.65
                },
                {
                    'symbol': 'USDC',
                    'amount': 500.0,
                    'value_usd': 500.0,
                    'pnl_usd': 0.0,
                    'pnl_pct': 0.0
                }
            ],
            'daily_pnl_usd': 150.0,
            'daily_pnl_pct': 3.1
        }
    
    def test_portfolio_risk_assessment(self, mock_portfolio_data):
        """Test portfolio risk assessment."""
        try:
            from core.risk.portfolio_risk_manager import PortfolioRiskManager
            
            config = {
                'risk_management': {
                    'max_portfolio_risk': 0.15,
                    'max_daily_loss_pct': 0.05,
                    'max_position_concentration': 0.4,
                    'var_confidence_level': 0.95
                }
            }
            
            risk_manager = PortfolioRiskManager(config)
            
            # Test risk assessment
            risk_metrics = risk_manager.assess_portfolio_risk(mock_portfolio_data)
            
            assert 'total_risk_score' in risk_metrics
            assert 'concentration_risk' in risk_metrics
            assert 'daily_pnl_risk' in risk_metrics
            assert 'position_risks' in risk_metrics
            
            # Risk score should be between 0 and 1
            assert 0 <= risk_metrics['total_risk_score'] <= 1
            
        except ImportError:
            pytest.skip("Portfolio risk manager not available")
    
    def test_risk_alert_generation(self, mock_portfolio_data):
        """Test risk alert generation."""
        try:
            from core.risk.portfolio_risk_manager import PortfolioRiskManager
            
            config = {
                'risk_management': {
                    'max_portfolio_risk': 0.05,  # Very low threshold for testing
                    'max_daily_loss_pct': 0.02,  # Very low threshold
                    'max_position_concentration': 0.3,  # Low threshold
                    'var_confidence_level': 0.95
                }
            }
            
            risk_manager = PortfolioRiskManager(config)
            
            # Test with high-risk portfolio
            high_risk_portfolio = {
                **mock_portfolio_data,
                'daily_pnl_usd': -300.0,  # Large loss
                'daily_pnl_pct': -6.0     # Large percentage loss
            }
            
            alerts = risk_manager.generate_risk_alerts(high_risk_portfolio)
            
            assert len(alerts) > 0
            assert any('daily_loss' in alert['type'] for alert in alerts)
            
        except ImportError:
            pytest.skip("Portfolio risk manager not available")
    
    def test_position_concentration_risk(self, mock_portfolio_data):
        """Test position concentration risk assessment."""
        try:
            from core.risk.portfolio_risk_manager import PortfolioRiskManager
            
            config = {
                'risk_management': {
                    'max_position_concentration': 0.5,
                    'concentration_warning_threshold': 0.4
                }
            }
            
            risk_manager = PortfolioRiskManager(config)
            
            # Test concentration calculation
            concentration_risk = risk_manager.calculate_concentration_risk(mock_portfolio_data)
            
            assert 'max_position_pct' in concentration_risk
            assert 'concentration_score' in concentration_risk
            assert 'is_concentrated' in concentration_risk
            
            # SOL position is 90% of portfolio (4500/5000)
            assert concentration_risk['max_position_pct'] > 0.8
            assert concentration_risk['is_concentrated'] == True
            
        except ImportError:
            pytest.skip("Portfolio risk manager not available")


class TestTelegramAlerts:
    """Test suite for Telegram alert system."""
    
    @pytest.fixture
    def mock_telegram_config(self):
        """Mock Telegram configuration."""
        return {
            'telegram': {
                'bot_token': 'test_bot_token',
                'chat_id': 'test_chat_id',
                'enabled': True
            }
        }
    
    @pytest.mark.asyncio
    async def test_telegram_notifier_initialization(self, mock_telegram_config):
        """Test Telegram notifier initialization."""
        try:
            from core.notifications.telegram_notifier import TelegramNotifier
            
            with patch.dict(os.environ, {
                'TELEGRAM_BOT_TOKEN': 'test_bot_token',
                'TELEGRAM_CHAT_ID': 'test_chat_id'
            }):
                notifier = TelegramNotifier()
                
                assert notifier.bot_token == 'test_bot_token'
                assert notifier.chat_id == 'test_chat_id'
                
        except ImportError:
            pytest.skip("Telegram notifier not available")
    
    @pytest.mark.asyncio
    async def test_trade_alert_sending(self, mock_telegram_config):
        """Test trade alert sending."""
        try:
            from phase_4_deployment.utils.trading_alerts import send_trade_alert
            
            with patch('phase_4_deployment.utils.trading_alerts.httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {'ok': True, 'result': {'message_id': 123}}
                mock_response.status_code = 200
                
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                # Test trade alert
                signal = {
                    'action': 'BUY',
                    'market': 'SOL-USDC',
                    'price': 180.0,
                    'size': 0.1,
                    'confidence': 0.8,
                    'transaction_signature': 'test_signature'
                }
                
                result = await send_trade_alert(signal)
                
                assert result == True
                mock_client.return_value.__aenter__.return_value.post.assert_called_once()
                
        except ImportError:
            pytest.skip("Trading alerts not available")
    
    @pytest.mark.asyncio
    async def test_risk_alert_sending(self):
        """Test risk alert sending."""
        try:
            from core.notifications.telegram_notifier import TelegramNotifier
            
            with patch('core.notifications.telegram_notifier.httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {'ok': True, 'result': {'message_id': 123}}
                mock_response.status_code = 200
                
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                with patch.dict(os.environ, {
                    'TELEGRAM_BOT_TOKEN': 'test_bot_token',
                    'TELEGRAM_CHAT_ID': 'test_chat_id'
                }):
                    notifier = TelegramNotifier()
                    
                    # Test risk alert
                    risk_alert = {
                        'type': 'high_risk',
                        'message': 'Portfolio risk exceeds threshold',
                        'risk_score': 0.85,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    result = await notifier.send_risk_alert(risk_alert)
                    
                    assert result == True
                    
        except ImportError:
            pytest.skip("Telegram notifier not available")


class TestSystemMonitoring:
    """Test suite for system monitoring components."""
    
    @pytest.mark.asyncio
    async def test_system_health_check(self):
        """Test system health check functionality."""
        try:
            from core.monitoring.performance_monitor import IntegratedMonitoringService
            
            monitoring = IntegratedMonitoringService()
            
            # Test component registration
            def mock_health_check():
                return True
            
            monitoring.register_component('test_component', mock_health_check)
            
            # Test health check
            health_status = monitoring.get_system_health()
            
            assert 'test_component' in health_status
            assert health_status['test_component'] == True
            
        except ImportError:
            pytest.skip("Monitoring service not available")
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self):
        """Test performance metrics collection."""
        try:
            from core.monitoring.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Test metric recording
            monitor.record_trade_execution_time(1.5)
            monitor.record_signal_generation_time(0.8)
            monitor.record_api_response_time('birdeye', 0.3)
            
            # Test metric retrieval
            metrics = monitor.get_performance_metrics()
            
            assert 'trade_execution_times' in metrics
            assert 'signal_generation_times' in metrics
            assert 'api_response_times' in metrics
            
            # Verify recorded values
            assert 1.5 in metrics['trade_execution_times']
            assert 0.8 in metrics['signal_generation_times']
            assert 'birdeye' in metrics['api_response_times']
            
        except ImportError:
            pytest.skip("Performance monitor not available")
    
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker functionality."""
        try:
            from core.monitoring.system_metrics import SystemMetricsMonitor
            
            monitor = SystemMetricsMonitor()
            
            # Test circuit breaker registration
            def failing_function():
                raise Exception("Test failure")
            
            def working_function():
                return "success"
            
            # Test failure tracking
            for _ in range(5):
                try:
                    monitor.track_api_call('test_api', failing_function)
                except:
                    pass
            
            # Test success tracking
            result = monitor.track_api_call('test_api', working_function)
            assert result == "success"
            
        except ImportError:
            pytest.skip("System metrics monitor not available")


class TestWalletSecurity:
    """Test suite for wallet security components."""
    
    def test_wallet_balance_monitoring(self):
        """Test wallet balance monitoring."""
        from tests.test_wallet_security import test_wallet_balance_check
        
        # Run existing wallet security test
        result = test_wallet_balance_check()
        assert result == True
    
    def test_transaction_validation(self):
        """Test transaction validation."""
        from tests.test_wallet_security import test_transaction_validation
        
        # Run existing transaction validation test
        result = test_transaction_validation()
        assert result == True
    
    def test_keypair_security(self):
        """Test keypair security measures."""
        from tests.test_wallet_security import test_keypair_security
        
        # Run existing keypair security test
        result = test_keypair_security()
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
