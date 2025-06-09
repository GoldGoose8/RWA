# RPC Execution Module

This module provides a unified interface for executing transactions using different RPC providers.

## Overview

The RPC Execution module consists of the following components:

- **RPC Clients**: Implementations of the `RpcClientInterface` for different RPC providers (Helius, Jito, etc.)
- **Transaction Executor**: A unified interface for executing transactions using different RPC clients
- **Transaction Preparation Service**: A high-level API for building, signing, and serializing transactions (from the `solana_tx_utils` package)

## Components

### RPC Client Interface

The `RpcClientInterface` defines a common interface for all RPC clients:

```python
class RpcClientInterface:
    async def send_transaction(self, transaction: str, opts: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a transaction to the RPC endpoint."""
        raise NotImplementedError("Subclasses must implement send_transaction")
    
    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        """Get the status of a transaction."""
        raise NotImplementedError("Subclasses must implement get_transaction_status")
    
    async def simulate_transaction(self, transaction: str, opts: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate a transaction."""
        raise NotImplementedError("Subclasses must implement simulate_transaction")
    
    async def close(self) -> None:
        """Close the client and release resources."""
        raise NotImplementedError("Subclasses must implement close")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics."""
        raise NotImplementedError("Subclasses must implement get_metrics")
```

### RPC Clients

#### Helius Client

The `HeliusClient` implements the `RpcClientInterface` for the Helius RPC provider:

```python
from rpc_execution.transaction_executor import RpcClientInterface

class HeliusClient(RpcClientInterface):
    def __init__(self, api_key: Optional[str] = None, fallback_rpc_url: Optional[str] = None):
        # Initialize the client
        ...
    
    async def send_transaction(self, transaction: str, opts: Dict[str, Any] = None) -> Dict[str, Any]:
        # Send a transaction to the Helius RPC endpoint
        ...
    
    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        # Get the status of a transaction
        ...
    
    async def simulate_transaction(self, transaction: str, opts: Dict[str, Any] = None) -> Dict[str, Any]:
        # Simulate a transaction
        ...
    
    async def close(self) -> None:
        # Close the client and release resources
        ...
    
    def get_metrics(self) -> Dict[str, Any]:
        # Get client metrics
        ...
```

### Transaction Executor

The `TransactionExecutor` provides a unified interface for executing transactions using different RPC clients:

```python
class TransactionExecutor:
    def __init__(self,
                 rpc_client: RpcClientInterface,
                 config_path: Optional[str] = None,
                 keypair_path: Optional[str] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 circuit_breaker_threshold: int = 5,
                 circuit_breaker_reset_time: float = 60.0):
        # Initialize the executor
        ...
    
    async def execute_transaction(self,
                                 transaction: Union[str, bytes, Dict[str, Any]],
                                 opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Execute a transaction
        ...
    
    async def execute_bundle(self,
                           transactions: List[Union[str, bytes, Dict[str, Any]]],
                           opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Execute a bundle of transactions
        ...
    
    async def simulate_bundle(self,
                            transactions: List[Union[str, bytes, Dict[str, Any]]],
                            opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Simulate a bundle of transactions
        ...
    
    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        # Get the status of a transaction
        ...
    
    async def close(self) -> None:
        # Close the executor and release resources
        ...
    
    def get_metrics(self) -> Dict[str, Any]:
        # Get executor metrics
        ...
```

## Usage

### Basic Usage

```python
from rpc_execution.helius_client import HeliusClient
from rpc_execution.transaction_executor import TransactionExecutor

# Initialize the RPC client
helius_client = HeliusClient()

# Initialize the transaction executor
executor = TransactionExecutor(
    rpc_client=helius_client,
    keypair_path="path/to/keypair.json",
    max_retries=3,
    retry_delay=1.0
)

# Execute a transaction
result = await executor.execute_transaction("serialized_transaction")

if result['success']:
    print(f"Transaction executed successfully: {result['signature']}")
else:
    print(f"Transaction execution failed: {result.get('error', 'Unknown error')}")

# Close the executor
await executor.close()
```

### Integration with Transaction Preparation Service

```python
from solana_tx_utils.tx_prep import TransactionPreparationService
from rpc_execution.helius_client import HeliusClient
from rpc_execution.transaction_executor import TransactionExecutor

# Initialize the transaction preparation service
tx_prep_service = TransactionPreparationService("https://api.mainnet-beta.solana.com")
tx_prep_service.load_keypair("default", "path/to/keypair.json")

# Initialize the RPC client
helius_client = HeliusClient()

# Initialize the transaction executor
executor = TransactionExecutor(
    rpc_client=helius_client,
    keypair_path="path/to/keypair.json",
    max_retries=3,
    retry_delay=1.0
)

# Build and sign a transaction
blockhash = tx_prep_service.get_recent_blockhash()
pubkey = tx_prep_service.get_active_pubkey()
instructions = [...]  # Define your instructions
tx_bytes = tx_prep_service.build_transaction(...)
signed_tx_bytes = tx_prep_service.sign_transaction(tx_bytes, is_versioned=True)

# Execute the transaction
result = await executor.execute_transaction(signed_tx_bytes)

# Close the executor
await executor.close()
```

## Error Handling

The `TransactionExecutor` implements robust error handling with retries and circuit breaking:

- **Retries**: Failed transactions are retried up to `max_retries` times with exponential backoff
- **Circuit Breaking**: If too many transactions fail in a row, the circuit breaker opens and rejects new transactions for a period of time
- **Error Classification**: Errors are classified as retryable or non-retryable based on their type

## Metrics

The `TransactionExecutor` collects metrics about transaction execution:

- **Total Transactions**: Total number of transactions executed
- **Successful Transactions**: Number of successful transactions
- **Failed Transactions**: Number of failed transactions
- **Retried Transactions**: Number of retried transactions
- **Circuit Breaker Trips**: Number of times the circuit breaker has tripped
- **Average Execution Time**: Average time to execute a transaction
- **Total Execution Time**: Total time spent executing transactions

## License

MIT
