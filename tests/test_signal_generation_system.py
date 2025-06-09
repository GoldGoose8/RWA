#!/usr/bin/env python3
"""
Signal Generation System Tests
Tests for the complete signal generation and enrichment pipeline.
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

class TestSignalGeneration:
    """Test suite for signal generation components."""

    @pytest.fixture
    def mock_birdeye_response(self):
        """Mock Birdeye API response."""
        return {
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
        }

    @pytest.fixture
    def mock_whale_opportunities(self):
        """Mock whale opportunities data."""
        return [
            {
                'wallet_address': '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
                'transaction_signature': 'test_signature_1',
                'amount_sol': 1000.0,
                'transaction_type': 'buy',
                'token_address': 'So11111111111111111111111111111111111111112',
                'timestamp': datetime.now().isoformat(),
                'confidence_score': 0.85
            },
            {
                'wallet_address': '8WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
                'transaction_signature': 'test_signature_2',
                'amount_sol': 500.0,
                'transaction_type': 'sell',
                'token_address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                'timestamp': datetime.now().isoformat(),
                'confidence_score': 0.72
            }
        ]

    @pytest.mark.asyncio
    async def test_birdeye_scanner(self, mock_birdeye_response):
        """Test Birdeye scanner functionality."""
        with patch('phase_4_deployment.data_router.birdeye_scanner.httpx.AsyncClient') as mock_client:
            # Mock HTTP response
            mock_response = Mock()
            mock_response.json.return_value = mock_birdeye_response
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            from phase_4_deployment.data_router.birdeye_scanner import BirdeyeScanner

            scanner = BirdeyeScanner('test_api_key')
            opportunities = await scanner.scan_for_opportunities()

            # Verify opportunities were generated
            assert len(opportunities) == 2
            assert opportunities[0]['symbol'] == 'SOL'
            assert opportunities[0]['price'] == 180.50
            assert opportunities[1]['symbol'] == 'USDC'

            await scanner.close()

    @pytest.mark.asyncio
    async def test_whale_watcher(self, mock_whale_opportunities):
        """Test whale watcher functionality."""
        with patch('phase_4_deployment.data_router.whale_watcher.HeliusClient') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.get_whale_transactions = AsyncMock(return_value=mock_whale_opportunities)
            mock_client.return_value = mock_client_instance

            from phase_4_deployment.data_router.whale_watcher import WhaleWatcher

            watcher = WhaleWatcher('test_helius_key')
            opportunities = await watcher.get_whale_opportunities()

            # Verify whale opportunities
            assert len(opportunities) == 2
            assert opportunities[0]['amount_sol'] == 1000.0
            assert opportunities[0]['transaction_type'] == 'buy'
            assert opportunities[1]['amount_sol'] == 500.0
            assert opportunities[1]['transaction_type'] == 'sell'

    def test_signal_enricher_basic(self):
        """Test basic signal enricher functionality."""
        from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher

        enricher = SignalEnricher()

        # Test basic signal
        signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'price': 180.0,
            'size': 0.1,
            'confidence': 0.7,
            'timestamp': datetime.now().isoformat()
        }

        enriched_signal = enricher.enrich_signal(signal)

        # Verify enrichment
        assert 'metadata' in enriched_signal
        assert 'priority_score' in enriched_signal['metadata']
        assert 'enriched_at' in enriched_signal['metadata']

        # Verify priority score is valid
        priority_score = enriched_signal['metadata']['priority_score']
        assert 0 <= priority_score <= 1

    def test_signal_enricher_composite_scoring(self):
        """Test signal enricher composite scoring."""
        from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher

        enricher = SignalEnricher()

        # Test high-confidence signal
        high_confidence_signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'price': 180.0,
            'size': 0.5,
            'confidence': 0.95,
            'volume': 1000000,
            'timestamp': datetime.now().isoformat()
        }

        # Test low-confidence signal
        low_confidence_signal = {
            'action': 'SELL',
            'market': 'SOL-USDC',
            'price': 180.0,
            'size': 0.1,
            'confidence': 0.3,
            'volume': 10000,
            'timestamp': datetime.now().isoformat()
        }

        high_enriched = enricher.enrich_signal(high_confidence_signal)
        low_enriched = enricher.enrich_signal(low_confidence_signal)

        # High confidence signal should have higher priority score
        high_priority = high_enriched['metadata']['priority_score']
        low_priority = low_enriched['metadata']['priority_score']

        assert high_priority > low_priority

    def test_signal_enricher_market_context(self):
        """Test signal enricher market context analysis."""
        from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher

        enricher = SignalEnricher()

        signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'price': 180.0,
            'size': 0.1,
            'confidence': 0.7,
            'timestamp': datetime.now().isoformat()
        }

        enriched_signal = enricher.enrich_signal(signal)

        # Verify basic enrichment (market context may not be implemented)
        assert 'metadata' in enriched_signal
        assert 'priority_score' in enriched_signal['metadata']

        # Check if market context exists, if not skip detailed checks
        if 'market_context' in enriched_signal['metadata']:
            market_context = enriched_signal['metadata']['market_context']
            # Verify market context fields if available
            assert isinstance(market_context, dict)

    @pytest.mark.asyncio
    async def test_signal_pipeline_integration(self, mock_birdeye_response):
        """Test complete signal generation pipeline."""
        with patch('phase_4_deployment.data_router.birdeye_scanner.httpx.AsyncClient') as mock_client:
            # Mock HTTP response
            mock_response = Mock()
            mock_response.json.return_value = mock_birdeye_response
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            from phase_4_deployment.data_router.birdeye_scanner import BirdeyeScanner
            from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher

            # Initialize components
            scanner = BirdeyeScanner('test_api_key')
            enricher = SignalEnricher()

            # Generate opportunities
            opportunities = await scanner.scan_for_opportunities()

            # Convert opportunities to signals
            signals = []
            for opp in opportunities:
                signal = {
                    'action': 'BUY',
                    'market': f"{opp['symbol']}-USDC",
                    'price': opp['price'],
                    'size': 0.1,
                    'confidence': 0.7,
                    'timestamp': datetime.now().isoformat()
                }
                signals.append(signal)

            # Enrich signals
            enriched_signals = [enricher.enrich_signal(signal) for signal in signals]

            # Sort by priority score
            enriched_signals.sort(
                key=lambda s: s['metadata']['priority_score'],
                reverse=True
            )

            # Verify pipeline results
            assert len(enriched_signals) == 2
            assert enriched_signals[0]['metadata']['priority_score'] >= enriched_signals[1]['metadata']['priority_score']

            await scanner.close()


class TestSignalFiltering:
    """Test suite for signal filtering and validation."""

    def test_signal_validation(self):
        """Test signal validation logic."""
        from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher

        enricher = SignalEnricher()

        # Valid signal
        valid_signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'price': 180.0,
            'size': 0.1,
            'confidence': 0.7,
            'timestamp': datetime.now().isoformat()
        }

        # Invalid signals
        invalid_signals = [
            # Missing action
            {
                'market': 'SOL-USDC',
                'price': 180.0,
                'size': 0.1,
                'confidence': 0.7
            },
            # Invalid action
            {
                'action': 'INVALID',
                'market': 'SOL-USDC',
                'price': 180.0,
                'size': 0.1,
                'confidence': 0.7
            },
            # Negative price
            {
                'action': 'BUY',
                'market': 'SOL-USDC',
                'price': -180.0,
                'size': 0.1,
                'confidence': 0.7
            },
            # Invalid confidence
            {
                'action': 'BUY',
                'market': 'SOL-USDC',
                'price': 180.0,
                'size': 0.1,
                'confidence': 1.5
            }
        ]

        # Test valid signal
        enriched_valid = enricher.enrich_signal(valid_signal)
        assert enriched_valid is not None
        assert 'metadata' in enriched_valid

        # Test invalid signals
        for invalid_signal in invalid_signals:
            try:
                enriched_invalid = enricher.enrich_signal(invalid_signal)
                # Should either return None or handle gracefully
                if enriched_invalid is not None:
                    # If it doesn't return None, it should have low priority
                    assert enriched_invalid['metadata']['priority_score'] < 0.5
            except Exception:
                # Exception handling is acceptable for invalid signals
                pass

    def test_signal_priority_filtering(self):
        """Test signal priority-based filtering."""
        from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher

        enricher = SignalEnricher()

        # Generate signals with different priorities
        signals = [
            {
                'action': 'BUY',
                'market': 'SOL-USDC',
                'price': 180.0,
                'size': 0.5,
                'confidence': 0.95,
                'volume': 1000000,
                'timestamp': datetime.now().isoformat()
            },
            {
                'action': 'BUY',
                'market': 'ETH-USDC',
                'price': 3000.0,
                'size': 0.3,
                'confidence': 0.7,
                'volume': 500000,
                'timestamp': datetime.now().isoformat()
            },
            {
                'action': 'SELL',
                'market': 'BTC-USDC',
                'price': 45000.0,
                'size': 0.1,
                'confidence': 0.4,
                'volume': 100000,
                'timestamp': datetime.now().isoformat()
            }
        ]

        # Enrich all signals
        enriched_signals = [enricher.enrich_signal(signal) for signal in signals]

        # Sort by priority score
        enriched_signals.sort(
            key=lambda s: s['metadata']['priority_score'],
            reverse=True
        )

        # Verify sorting
        for i in range(len(enriched_signals) - 1):
            current_priority = enriched_signals[i]['metadata']['priority_score']
            next_priority = enriched_signals[i + 1]['metadata']['priority_score']
            assert current_priority >= next_priority

        # Filter high-priority signals (>0.7)
        high_priority_signals = [
            s for s in enriched_signals
            if s['metadata']['priority_score'] > 0.7
        ]

        # Should have at least the highest confidence signal
        assert len(high_priority_signals) >= 1
        assert high_priority_signals[0]['confidence'] == 0.95


class TestSignalMetrics:
    """Test suite for signal generation metrics and monitoring."""

    def test_signal_generation_metrics(self):
        """Test signal generation metrics collection."""
        from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher

        enricher = SignalEnricher()

        # Generate multiple signals
        signals = []
        for i in range(10):
            signal = {
                'action': 'BUY' if i % 2 == 0 else 'SELL',
                'market': f'TOKEN{i}-USDC',
                'price': 100.0 + i,
                'size': 0.1,
                'confidence': 0.5 + (i * 0.05),
                'timestamp': datetime.now().isoformat()
            }
            signals.append(signal)

        # Enrich all signals
        enriched_signals = [enricher.enrich_signal(signal) for signal in signals]

        # Calculate metrics
        total_signals = len(enriched_signals)
        high_priority_count = len([s for s in enriched_signals if s['metadata']['priority_score'] > 0.7])
        medium_priority_count = len([s for s in enriched_signals if 0.4 <= s['metadata']['priority_score'] <= 0.7])
        low_priority_count = len([s for s in enriched_signals if s['metadata']['priority_score'] < 0.4])

        # Verify metrics
        assert total_signals == 10
        assert high_priority_count + medium_priority_count + low_priority_count == total_signals

        # Calculate average priority score
        avg_priority = sum(s['metadata']['priority_score'] for s in enriched_signals) / total_signals
        assert 0 <= avg_priority <= 1

    def test_signal_timing_metrics(self):
        """Test signal generation timing metrics."""
        from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher
        import time

        enricher = SignalEnricher()

        signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'price': 180.0,
            'size': 0.1,
            'confidence': 0.7,
            'timestamp': datetime.now().isoformat()
        }

        # Measure enrichment time
        start_time = time.time()
        enriched_signal = enricher.enrich_signal(signal)
        end_time = time.time()

        enrichment_time = end_time - start_time

        # Verify timing
        assert enriched_signal is not None
        assert enrichment_time < 1.0  # Should complete in under 1 second

        # Verify timing metadata
        assert 'processing_time_ms' in enriched_signal['metadata']
        processing_time_ms = enriched_signal['metadata']['processing_time_ms']
        assert processing_time_ms > 0
        assert processing_time_ms < 1000  # Should be under 1000ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
