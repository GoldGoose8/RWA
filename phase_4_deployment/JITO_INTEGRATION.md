# Jito Integration for Q5 Trading System

This document describes the integration of Jito Labs' services into the Q5 Trading System, providing MEV protection, low-latency execution, and ShredStream access.

## Overview

The Jito integration consists of several components:

1. **Jito Client**: Core client for interacting with Jito's REST API
2. **Jito Executor**: Executor for sending transactions with MEV protection
3. **Jito Monitor**: Monitoring and metrics collection for Jito transactions
4. **Authentication**: Utilities for authenticating with Jito services

## Directory Structure

```
📦 phase_4_deployment/
├── rpc_execution/
│   ├── jito_client.py         # Core Jito API client
│   ├── jito_executor.py       # Transaction executor using Jito
│   └── tx_builder.py          # Transaction builder
├── core/
│   └── jito_monitor.py        # Monitoring for Jito transactions
├── keys/
│   ├── jito_auth.py           # Authentication utilities
│   └── jito_shredstream_keypair.json  # Ed25519 keypair for authentication
├── configs/
│   └── jito_config.yaml       # Configuration for Jito integration
├── scripts/
│   └── jito_dry_run.py        # Script to test Jito integration
└── output/
    ├── tx_history.json        # Transaction history
    └── jito_metrics.json      # Jito metrics
```

## Configuration

The Jito integration is configured via `configs/jito_config.yaml`, which includes:

- RPC endpoints for Jito and fallback
- Authentication settings
- Transaction parameters
- Monitoring settings
- ShredStream configuration

## Authentication

Jito's ShredStream service requires authentication with an Ed25519 keypair. The keypair is stored in `keys/jito_shredstream_keypair.json` and used for authentication.

To generate a new keypair:

```bash
python3 keys/jito_auth.py --keypair keys/jito_shredstream_keypair.json
```

## Usage

### Basic Usage

```python
from rpc_execution.jito_executor import JitoExecutor
from rpc_execution.tx_builder import TxBuilder

# Create executor
executor = JitoExecutor()

# Create transaction builder
tx_builder = TxBuilder("wallet_address")

# Build transaction from signal
signal = {
    "action": "BUY",
    "market": "SOL-USDC",
    "price": 25.10,
    "size": 10.0,
    "confidence": 0.92
}
tx = tx_builder.build_swap_tx(signal)

# Send transaction
result = await executor.send_transaction(tx)

# Check result
if result['success']:
    print(f"Transaction sent: {result['signature']}")
else:
    print(f"Failed: {result['error']}")
```

### Dry Run Mode

To test without sending actual transactions:

```python
# Enable dry run mode
executor = JitoExecutor(dry_run=True)

# Send transaction (simulated)
result = await executor.send_transaction(tx)
```

Or run the dry run script:

```bash
python3 scripts/jito_dry_run.py --transactions 5
```

### Monitoring

To monitor Jito transactions:

```python
from core.jito_monitor import JitoMonitor

# Create monitor
monitor = JitoMonitor()

# Start monitoring loop
monitor_task = asyncio.create_task(monitor.monitor_loop())

# Get metrics summary
summary = monitor.get_metrics_summary()
```

## Integration with Q5 System

The Jito integration is designed to work seamlessly with the Q5 Trading System:

1. **Signal Generation**: Strategies generate trading signals
2. **Signal Enrichment**: Signals are enriched with metadata
3. **Transaction Building**: `tx_builder.py` builds transactions from signals
4. **Execution**: `jito_executor.py` sends transactions via Jito
5. **Monitoring**: `jito_monitor.py` monitors transaction performance

## Metrics and Logging

The integration provides comprehensive metrics and logging:

- Transaction success/failure rates
- Response times
- Fallback usage
- Alerts for performance issues

Metrics are stored in `output/jito_metrics.json` and can be visualized in the dashboard.

## Troubleshooting

Common issues and solutions:

1. **Authentication Failures**: Ensure the Ed25519 keypair is correctly generated and registered with Jito Labs.
2. **RPC Errors**: Check the Jito RPC URL and fallback URL in the configuration.
3. **Transaction Failures**: Verify that transactions are correctly built and signed.
4. **High Fallback Rate**: If many transactions are falling back to the public RPC, check Jito's service status.

## References

- [Jito Labs Documentation](https://jito-labs.gitbook.io/mev/)
- [Solana Transaction Structure](https://docs.solana.com/developing/programming-model/transactions)
- [Ed25519 Key Generation](https://docs.solana.com/wallet-guide/paper-wallet#ed25519-key-generation)
