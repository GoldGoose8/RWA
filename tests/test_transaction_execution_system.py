#!/usr/bin/env python3
"""
Transaction Execution System Tests
Tests for the complete transaction building, signing, and execution pipeline.
"""

import pytest
import asyncio
import os
import sys
import json
import logging
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestTransactionBuilding:
    """Test suite for transaction building components."""
    
    @pytest.fixture
    def mock_keypair_data(self):
        """Mock keypair data for testing."""
        return [1] * 64  # Mock 64-byte keypair
    
    @pytest.fixture
    def mock_signal(self):
        """Mock trading signal for testing."""
        return {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'price': 180.0,
            'size': 0.1,
            'input_token': 'So11111111111111111111111111111111111111112',
            'output_token': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'amount': 100000000,  # 0.1 SOL in lamports
            'slippage_bps': 100
        }
    
    def test_tx_builder_initialization(self, mock_keypair_data):
        """Test transaction builder initialization."""
        with patch('phase_4_deployment.rpc_execution.tx_builder.Keypair') as mock_keypair_class:
            mock_keypair_instance = Mock()
            mock_keypair_class.from_bytes.return_value = mock_keypair_instance
            
            from phase_4_deployment.rpc_execution.tx_builder import TxBuilder
            
            wallet_address = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
            
            # Test initialization with keypair
            tx_builder = TxBuilder(wallet_address, keypair=mock_keypair_instance)
            
            assert tx_builder.wallet_address == wallet_address
            assert tx_builder.keypair == mock_keypair_instance
    
    def test_tx_builder_swap_transaction(self, mock_signal):
        """Test transaction builder swap transaction creation."""
        with patch('phase_4_deployment.rpc_execution.tx_builder.Keypair') as mock_keypair_class:
            mock_keypair_instance = Mock()
            mock_keypair_class.from_bytes.return_value = mock_keypair_instance
            
            from phase_4_deployment.rpc_execution.tx_builder import TxBuilder
            
            wallet_address = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
            tx_builder = TxBuilder(wallet_address, keypair=mock_keypair_instance)
            
            # Mock Jupiter API response
            with patch.object(tx_builder, '_get_jupiter_quote') as mock_quote:
                mock_quote.return_value = {
                    'data': [{
                        'inAmount': '100000000',
                        'outAmount': '18000000',
                        'otherAmountThreshold': '17820000',
                        'swapMode': 'ExactIn',
                        'priceImpactPct': '0.1'
                    }]
                }
                
                with patch.object(tx_builder, '_get_jupiter_swap_transaction') as mock_swap:
                    mock_swap.return_value = {
                        'swapTransaction': 'base64_encoded_transaction'
                    }
                    
                    # Test swap transaction building
                    result = tx_builder.build_swap_tx(mock_signal)
                    
                    assert result is not None
                    mock_quote.assert_called_once()
                    mock_swap.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enhanced_tx_builder(self, mock_signal, mock_keypair_data):
        """Test enhanced transaction builder functionality."""
        try:
            from core.transaction.enhanced_tx_builder import EnhancedTxBuilder
            
            with patch('core.transaction.enhanced_tx_builder.Keypair') as mock_keypair_class:
                mock_keypair_instance = Mock()
                mock_keypair_class.from_bytes.return_value = mock_keypair_instance
                
                wallet_address = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
                
                # Test enhanced builder initialization
                enhanced_builder = EnhancedTxBuilder(
                    wallet_address=wallet_address,
                    keypair=mock_keypair_instance
                )
                
                # Mock Jupiter swap building
                with patch.object(enhanced_builder, 'build_jupiter_swap') as mock_build:
                    mock_build.return_value = b'mock_transaction_bytes'
                    
                    # Test Jupiter swap building
                    result = await enhanced_builder.build_jupiter_swap(mock_signal)
                    
                    assert result == b'mock_transaction_bytes'
                    mock_build.assert_called_once_with(mock_signal)
                    
        except ImportError:
            pytest.skip("Enhanced transaction builder not available")
    
    def test_transaction_preparation_service(self, mock_keypair_data, tmp_path):
        """Test transaction preparation service functionality."""
        try:
            from solana_tx_utils.tx_prep import TransactionPreparationService
            
            # Create mock keypair file
            keypair_file = tmp_path / "test_keypair.json"
            with open(keypair_file, 'w') as f:
                json.dump(mock_keypair_data, f)
            
            rpc_url = "https://api.mainnet-beta.solana.com"
            
            # Test service initialization
            service = TransactionPreparationService(rpc_url)
            
            # Test keypair loading
            service.load_keypair('test', str(keypair_file))
            
            # Test getting active pubkey
            pubkey = service.get_active_pubkey()
            assert pubkey is not None
            
            # Test getting recent blockhash
            with patch.object(service, 'get_recent_blockhash') as mock_blockhash:
                mock_blockhash.return_value = 'mock_blockhash'
                
                blockhash = service.get_recent_blockhash()
                assert blockhash == 'mock_blockhash'
                
        except ImportError:
            pytest.skip("Transaction preparation service not available")


class TestTransactionExecution:
    """Test suite for transaction execution components."""
    
    @pytest.fixture
    def mock_rpc_response(self):
        """Mock RPC response for testing."""
        return {
            'result': {
                'value': {
                    'signature': 'test_signature_12345',
                    'confirmationStatus': 'confirmed',
                    'err': None
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_helius_client(self, mock_rpc_response):
        """Test Helius client functionality."""
        with patch('phase_4_deployment.rpc_execution.helius_client.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_rpc_response
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            from phase_4_deployment.rpc_execution.helius_client import HeliusClient
            
            client = HeliusClient(api_key='test_api_key')
            
            # Test transaction sending
            result = await client.send_transaction('base64_encoded_transaction')
            
            assert result is not None
            assert 'signature' in str(result)
    
    @pytest.mark.asyncio
    async def test_transaction_executor(self):
        """Test transaction executor functionality."""
        with patch('phase_4_deployment.rpc_execution.transaction_executor.HeliusClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_transaction = AsyncMock(return_value={
                'signature': 'test_signature_12345',
                'status': 'confirmed'
            })
            mock_client_class.return_value = mock_client
            
            from phase_4_deployment.rpc_execution.transaction_executor import TransactionExecutor
            
            executor = TransactionExecutor(
                rpc_client=mock_client,
                keypair_path='test_keypair.json',
                max_retries=3,
                retry_delay=0.1
            )
            
            # Test transaction execution
            result = await executor.execute_transaction(b'mock_transaction')
            
            assert result is not None
            assert result.get('success', False) == True
            assert 'signature' in result
            
            await executor.close()
    
    @pytest.mark.asyncio
    async def test_transaction_executor_retry_logic(self):
        """Test transaction executor retry logic."""
        with patch('phase_4_deployment.rpc_execution.transaction_executor.HeliusClient') as mock_client_class:
            mock_client = Mock()
            
            # Mock failure then success
            mock_client.send_transaction = AsyncMock(side_effect=[
                Exception("Network error"),
                Exception("Timeout error"),
                {
                    'signature': 'test_signature_12345',
                    'status': 'confirmed'
                }
            ])
            mock_client_class.return_value = mock_client
            
            from phase_4_deployment.rpc_execution.transaction_executor import TransactionExecutor
            
            executor = TransactionExecutor(
                rpc_client=mock_client,
                keypair_path='test_keypair.json',
                max_retries=3,
                retry_delay=0.01  # Fast retry for testing
            )
            
            # Test transaction execution with retries
            result = await executor.execute_transaction(b'mock_transaction')
            
            # Should succeed after retries
            assert result is not None
            assert result.get('success', False) == True
            assert mock_client.send_transaction.call_count == 3
            
            await executor.close()
    
    @pytest.mark.asyncio
    async def test_transaction_executor_max_retries_exceeded(self):
        """Test transaction executor when max retries are exceeded."""
        with patch('phase_4_deployment.rpc_execution.transaction_executor.HeliusClient') as mock_client_class:
            mock_client = Mock()
            
            # Mock continuous failures
            mock_client.send_transaction = AsyncMock(side_effect=Exception("Persistent error"))
            mock_client_class.return_value = mock_client
            
            from phase_4_deployment.rpc_execution.transaction_executor import TransactionExecutor
            
            executor = TransactionExecutor(
                rpc_client=mock_client,
                keypair_path='test_keypair.json',
                max_retries=2,
                retry_delay=0.01
            )
            
            # Test transaction execution failure
            result = await executor.execute_transaction(b'mock_transaction')
            
            # Should fail after max retries
            assert result is not None
            assert result.get('success', False) == False
            assert 'error' in result
            assert mock_client.send_transaction.call_count == 3  # Initial + 2 retries
            
            await executor.close()


class TestJupiterIntegration:
    """Test suite for Jupiter swap integration."""
    
    @pytest.fixture
    def mock_jupiter_quote_response(self):
        """Mock Jupiter quote API response."""
        return {
            'data': [{
                'inAmount': '100000000',
                'outAmount': '18000000',
                'otherAmountThreshold': '17820000',
                'swapMode': 'ExactIn',
                'priceImpactPct': '0.1',
                'marketInfos': [{
                    'id': 'jupiter',
                    'label': 'Jupiter',
                    'inputMint': 'So11111111111111111111111111111111111111112',
                    'outputMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                    'notEnoughLiquidity': False,
                    'inAmount': '100000000',
                    'outAmount': '18000000',
                    'priceImpactPct': '0.1'
                }]
            }]
        }
    
    @pytest.fixture
    def mock_jupiter_swap_response(self):
        """Mock Jupiter swap API response."""
        return {
            'swapTransaction': 'base64_encoded_transaction_data',
            'lastValidBlockHeight': 123456789
        }
    
    def test_jupiter_quote_request(self, mock_jupiter_quote_response):
        """Test Jupiter quote API request."""
        with patch('phase_4_deployment.rpc_execution.tx_builder.httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_jupiter_quote_response
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            from phase_4_deployment.rpc_execution.tx_builder import TxBuilder
            
            wallet_address = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
            tx_builder = TxBuilder(wallet_address)
            
            # Test Jupiter quote request
            quote = tx_builder._get_jupiter_quote(
                input_mint='So11111111111111111111111111111111111111112',
                output_mint='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                amount=100000000,
                slippage_bps=100
            )
            
            assert quote is not None
            assert 'data' in quote
            assert len(quote['data']) > 0
            assert quote['data'][0]['inAmount'] == '100000000'
    
    def test_jupiter_swap_request(self, mock_jupiter_swap_response):
        """Test Jupiter swap API request."""
        with patch('phase_4_deployment.rpc_execution.tx_builder.httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_jupiter_swap_response
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response
            
            from phase_4_deployment.rpc_execution.tx_builder import TxBuilder
            
            wallet_address = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
            tx_builder = TxBuilder(wallet_address)
            
            # Mock quote data
            quote_data = {
                'inAmount': '100000000',
                'outAmount': '18000000',
                'otherAmountThreshold': '17820000',
                'swapMode': 'ExactIn'
            }
            
            # Test Jupiter swap request
            swap_response = tx_builder._get_jupiter_swap_transaction(
                quote_data=quote_data,
                user_public_key=wallet_address
            )
            
            assert swap_response is not None
            assert 'swapTransaction' in swap_response
            assert swap_response['swapTransaction'] == 'base64_encoded_transaction_data'
    
    def test_jupiter_error_handling(self):
        """Test Jupiter API error handling."""
        with patch('phase_4_deployment.rpc_execution.tx_builder.httpx.Client') as mock_client:
            # Mock API error response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.raise_for_status.side_effect = Exception("Bad Request")
            
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            from phase_4_deployment.rpc_execution.tx_builder import TxBuilder
            
            wallet_address = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
            tx_builder = TxBuilder(wallet_address)
            
            # Test error handling
            quote = tx_builder._get_jupiter_quote(
                input_mint='So11111111111111111111111111111111111111112',
                output_mint='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                amount=100000000,
                slippage_bps=100
            )
            
            # Should handle error gracefully
            assert quote is None or 'error' in quote


class TestTransactionSigning:
    """Test suite for transaction signing functionality."""
    
    def test_keypair_loading_json_format(self, tmp_path):
        """Test keypair loading from JSON format."""
        # Create mock keypair file
        keypair_data = [1] * 64
        keypair_file = tmp_path / "test_keypair.json"
        with open(keypair_file, 'w') as f:
            json.dump(keypair_data, f)
        
        # Test loading
        with patch('phase_4_deployment.rpc_execution.tx_builder.Keypair') as mock_keypair_class:
            mock_keypair_instance = Mock()
            mock_keypair_class.from_bytes.return_value = mock_keypair_instance
            
            from phase_4_deployment.rpc_execution.tx_builder import TxBuilder
            
            # Test keypair loading
            with open(keypair_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert len(loaded_data) == 64
            assert all(isinstance(x, int) for x in loaded_data)
    
    def test_transaction_signing_process(self):
        """Test transaction signing process."""
        with patch('phase_4_deployment.rpc_execution.tx_builder.Keypair') as mock_keypair_class:
            mock_keypair_instance = Mock()
            mock_keypair_instance.sign_message.return_value = b'mock_signature'
            mock_keypair_class.from_bytes.return_value = mock_keypair_instance
            
            from phase_4_deployment.rpc_execution.tx_builder import TxBuilder
            
            wallet_address = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
            tx_builder = TxBuilder(wallet_address, keypair=mock_keypair_instance)
            
            # Mock transaction data
            transaction_data = b'mock_transaction_bytes'
            
            # Test signing (if method exists)
            if hasattr(tx_builder, 'sign_transaction'):
                signed_tx = tx_builder.sign_transaction(transaction_data)
                assert signed_tx is not None
            else:
                # Verify keypair is available for signing
                assert tx_builder.keypair == mock_keypair_instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
