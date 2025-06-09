# Q5 System Tests

This directory contains tests for the Q5 System.

## Overview

The tests in this directory are designed to verify the functionality of the Q5 System components, including:

- Lil' Jito client
- Stream data ingestor
- Streamlit dashboard
- Live trading script

## Running Tests

You can run all tests using the `run_tests.py` script in the parent directory:

```bash
cd /path/to/HedgeFund/phase_4_deployment
python run_tests.py
```

To run a specific test, use the `--test` or `-t` option:

```bash
python run_tests.py --test test_liljito_client.py
```

To list all available tests, use the `--list` or `-l` option:

```bash
python run_tests.py --list
```

To enable verbose output, use the `--verbose` or `-v` option:

```bash
python run_tests.py --verbose
```

## Test Files

### `test_liljito_client.py`

Tests the Lil' Jito client with various operations, including:

- Getting transaction status
- Simulating transactions
- Getting metrics

### `test_stream_data_ingestor.py`

Tests the stream data ingestor with various stream types, including:

- Mock stream
- Helius stream
- Lil' Jito stream

### `test_streamlit_dashboard.py`

Tests the Streamlit dashboard, including:

- Checking if Streamlit is installed
- Checking if the dashboard file exists
- Checking if the dashboard imports are valid
- Checking if the Stream Data tab is present
- Starting the Streamlit server and checking if it's running

### `test_live_trading.py`

Tests the live trading script, including:

- Importing the live trading script
- Testing the Lil' Jito integration
- Testing the stream data integration
- Testing the live trading script with dry run mode

## Environment Variables

The tests require the following environment variables to be set:

- `LILJITO_QUICKNODE_API_KEY`: API key for Lil' Jito QuickNode
- `HELIUS_API_KEY`: API key for Helius
- `WALLET_ADDRESS`: Wallet address for testing
- `DRY_RUN`: Set to `true` for testing
- `PAPER_TRADING`: Set to `true` for testing

You can set these environment variables in a `.env` file in the parent directory.

## Adding New Tests

To add a new test, create a new file in this directory with the prefix `test_` and the `.py` extension. The test should return `0` for success and non-zero for failure.

## Troubleshooting

If a test fails, check the following:

- Make sure all required environment variables are set
- Make sure all required dependencies are installed
- Check the logs for error messages

If you need help, please contact the Q5 System team.
