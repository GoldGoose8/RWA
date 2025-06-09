# Stream Data Ingestion Module

This module provides a client for consuming data from low-latency streams such as QuickNode Yellowstone gRPC and Jito ShredStream.

## Overview

The Stream Data Ingestion module consists of the following components:

- **StreamDataIngestor**: A client for consuming data from different stream sources
- **StreamType**: An enum for different types of streams (QuickNode Yellowstone, Jito ShredStream, Helius Webhook, Custom WebSocket)

## Features

- **Unified Interface**: A single interface for consuming data from different stream sources
- **Automatic Reconnection**: Automatically reconnects to the stream if the connection is lost
- **Message Buffering**: Buffers messages to avoid losing data if the consumer is slow
- **Callback System**: Register callbacks for different events (message received, connection established, connection closed, error occurred)
- **Metrics Collection**: Collects metrics about the stream (messages received, processed, dropped, etc.)

## Usage

### Basic Usage

```python
import asyncio
from stream_data_ingestor.client import StreamDataIngestor, StreamType

# Create a stream data ingestor
ingestor = StreamDataIngestor(
    stream_type=StreamType.QUICKNODE_YELLOWSTONE,
    stream_url="wss://your-quicknode-url",
    api_key="your-api-key",
    subscription_params={
        "mentions": ["your-program-id"],
        "commitment": "confirmed"
    }
)

# Register callbacks
async def on_message(message):
    print(f"Received message: {message}")

async def on_connect():
    print("Connected to stream")

async def on_disconnect():
    print("Disconnected from stream")

async def on_error(error):
    print(f"Error: {error}")

ingestor.on_message(on_message)
ingestor.on_connect(on_connect)
ingestor.on_disconnect(on_disconnect)
ingestor.on_error(on_error)

# Start consuming data
await ingestor.start()

# Wait for some messages
await asyncio.sleep(60)  # Run for 60 seconds

# Stop consuming data
await ingestor.stop()
```

### Supported Stream Types

#### QuickNode Yellowstone

```python
ingestor = StreamDataIngestor(
    stream_type=StreamType.QUICKNODE_YELLOWSTONE,
    stream_url="wss://your-quicknode-url",
    api_key="your-api-key",
    subscription_params={
        "mentions": ["your-program-id"],
        "commitment": "confirmed"
    }
)
```

#### Jito ShredStream

```python
ingestor = StreamDataIngestor(
    stream_type=StreamType.JITO_SHREDSTREAM,
    stream_url="wss://your-jito-url",
    api_key="your-api-key",
    subscription_params={
        "params": ["your-subscription-params"]
    }
)
```

#### Helius Webhook

```python
ingestor = StreamDataIngestor(
    stream_type=StreamType.HELIUS_WEBHOOK,
    stream_url="https://your-helius-webhook-url",
    api_key="your-api-key",
    subscription_params={
        "poll_interval": 1.0  # Poll every 1 second
    }
)
```

#### Custom WebSocket

```python
ingestor = StreamDataIngestor(
    stream_type=StreamType.CUSTOM_WEBSOCKET,
    stream_url="wss://your-websocket-url",
    api_key="your-api-key",
    subscription_params={
        "subscription_message": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "subscribe",
            "params": ["your-subscription-params"]
        },
        "expect_confirmation": True
    }
)
```

### Getting Messages

You can get messages from the buffer using the `get_message` method:

```python
# Get a message from the buffer
message = await ingestor.get_message()
```

### Getting Metrics

You can get metrics about the stream using the `get_metrics` method:

```python
# Get metrics
metrics = ingestor.get_metrics()
print(f"Total messages: {metrics['total_messages']}")
print(f"Processed messages: {metrics['processed_messages']}")
print(f"Dropped messages: {metrics['dropped_messages']}")
```

## Integration with Signal Generation

The Stream Data Ingestion module can be integrated with the Signal Generation module to generate trading signals from stream data:

```python
import asyncio
from stream_data_ingestor.client import StreamDataIngestor, StreamType
from signal_generation.generator import SignalGenerator

# Create a stream data ingestor
ingestor = StreamDataIngestor(
    stream_type=StreamType.QUICKNODE_YELLOWSTONE,
    stream_url="wss://your-quicknode-url",
    api_key="your-api-key",
    subscription_params={
        "mentions": ["your-program-id"],
        "commitment": "confirmed"
    }
)

# Create a signal generator
signal_generator = SignalGenerator()

# Register callback to generate signals from messages
async def on_message(message):
    # Generate signals from the message
    signals = signal_generator.generate_signals(message)
    
    # Process the signals
    for signal in signals:
        print(f"Generated signal: {signal}")

ingestor.on_message(on_message)

# Start consuming data
await ingestor.start()

# Wait for some messages
await asyncio.sleep(60)  # Run for 60 seconds

# Stop consuming data
await ingestor.stop()
```

## License

MIT
