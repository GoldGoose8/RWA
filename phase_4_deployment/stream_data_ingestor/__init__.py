"""
Stream Data Ingestion Module

This module provides a client for consuming data from low-latency streams
such as QuickNode Yellowstone gRPC and Jito ShredStream.
"""

from .client import StreamDataIngestor, StreamType

__all__ = ['StreamDataIngestor', 'StreamType']
