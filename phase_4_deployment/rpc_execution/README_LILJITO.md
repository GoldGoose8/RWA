# Lil' Jito Client for Q5 Trading System

This module provides a client for interacting with Lil' Jito RPC services, which offers bundle transaction capabilities for Solana.

## Overview

The Lil' Jito client implements the RpcClientInterface for use with the TransactionExecutor. It provides methods for sending transactions, sending bundles, simulating transactions and bundles, and getting transaction status.

## Features

- **Transaction Sending**: Send transactions to the Solana blockchain via Lil' Jito
- **Bundle Support**: Send multiple transactions as a bundle to be executed atomically
- **Transaction Simulation**: Simulate transactions and bundles before sending them
- **Fallback RPC**: Automatically fall back to a secondary RPC endpoint if the primary one fails
- **Metrics Collection**: Collect metrics about RPC requests, responses, and errors
- **Configurable**: Configure the client with custom RPC URLs, API keys, and connection parameters

## Usage

### Basic Usage

```python
import asyncio
from rpc_execution.lil_jito_client import LilJitoClient

async def main():
    # Create a Lil' Jito client
    client = LilJitoClient(
        api_key="your_api_key",
        rpc_url="https://lil-jito.quiknode.pro/your_api_key/",
        fallback_rpc_url="https://api.mainnet-beta.solana.com",
        max_connections=100,
        timeout=30.0
    )
    
    # Send a transaction
    result = await client.send_transaction(
        transaction="your_serialized_transaction",
        opts={
            "encoding": "base58",
            "skip_preflight": True,
            "preflight_commitment": "confirmed"
        }
    )
    
    print(f"Transaction result: {result}")
    
    # Close the client
    await client.close()

asyncio.run(main())
```

### Sending a Bundle

```python
import asyncio
from rpc_execution.lil_jito_client import LilJitoClient

async def main():
    # Create a Lil' Jito client
    client = LilJitoClient()
    
    # Send a bundle of transactions
    result = await client.send_bundle(
        transactions=["tx1", "tx2", "tx3"],
        opts={
            "encoding": "base58",
            "skip_preflight": True,
            "preflight_commitment": "confirmed"
        }
    )
    
    print(f"Bundle result: {result}")
    
    # Close the client
    await client.close()

asyncio.run(main())
```

### Simulating a Transaction

```python
import asyncio
from rpc_execution.lil_jito_client import LilJitoClient

async def main():
    # Create a Lil' Jito client
    client = LilJitoClient()
    
    # Simulate a transaction
    result = await client.simulate_transaction(
        transaction="your_serialized_transaction",
        opts={
            "encoding": "base58",
            "commitment": "confirmed",
            "sig_verify": False,
            "replace_recent_blockhash": True
        }
    )
    
    print(f"Simulation result: {result}")
    
    # Close the client
    await client.close()

asyncio.run(main())
```

### Getting Transaction Status

```python
import asyncio
from rpc_execution.lil_jito_client import LilJitoClient

async def main():
    # Create a Lil' Jito client
    client = LilJitoClient()
    
    # Get transaction status
    result = await client.get_transaction_status("your_transaction_signature")
    
    print(f"Transaction status: {result}")
    
    # Close the client
    await client.close()

asyncio.run(main())
```

### Getting Metrics

```python
import asyncio
from rpc_execution.lil_jito_client import LilJitoClient

async def main():
    # Create a Lil' Jito client
    client = LilJitoClient()
    
    # Get metrics
    metrics = client.get_metrics()
    
    print(f"Client metrics: {metrics}")
    
    # Close the client
    await client.close()

asyncio.run(main())
```

## Integration with Transaction Executor

The Lil' Jito client can be used with the TransactionExecutor:

```python
import asyncio
from rpc_execution.lil_jito_client import LilJitoClient
from rpc_execution.transaction_executor import TransactionExecutor

async def main():
    # Create a Lil' Jito client
    client = LilJitoClient()
    
    # Create a transaction executor
    executor = TransactionExecutor(
        rpc_client=client,
        keypair_path="path/to/keypair.json",
        max_retries=3,
        retry_delay=1.0
    )
    
    # Execute a transaction
    result = await executor.execute_transaction(
        transaction="your_serialized_transaction"
    )
    
    print(f"Transaction result: {result}")
    
    # Close the executor (which will also close the client)
    await executor.close()

asyncio.run(main())
```

## Environment Variables

The Lil' Jito client uses the following environment variables:

- `LILJITO_QUICKNODE_API_KEY`: API key for Lil' Jito QuickNode
- `LILJITO_QUICKNODE_RPC_URL`: RPC URL for Lil' Jito QuickNode
- `FALLBACK_RPC_URL`: Fallback RPC URL to use if the primary one fails

## License

MIT
