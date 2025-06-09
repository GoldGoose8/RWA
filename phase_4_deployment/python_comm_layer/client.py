#!/usr/bin/env python3
"""
Python-Rust Communication Layer Client

This module provides a client for communicating with the Rust components
of the Q5 Trading System using ZeroMQ.
"""

import os
import json
import time
import logging
import asyncio
import zmq
import zmq.asyncio
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class CommunicationError(Exception):
    """Exception raised for communication errors."""
    pass

class RustCommClient:
    """Client for communicating with Rust components using ZeroMQ."""
    
    def __init__(
        self,
        pub_endpoint: str = "tcp://127.0.0.1:5555",
        sub_endpoint: str = "tcp://127.0.0.1:5556",
        req_endpoint: str = "tcp://127.0.0.1:5557",
        context: Optional[zmq.asyncio.Context] = None,
        timeout: int = 5000,  # milliseconds
    ):
        """
        Initialize the Rust communication client.
        
        Args:
            pub_endpoint: ZeroMQ publisher endpoint
            sub_endpoint: ZeroMQ subscriber endpoint
            req_endpoint: ZeroMQ request-reply endpoint
            context: ZeroMQ context (created if not provided)
            timeout: Request timeout in milliseconds
        """
        self.pub_endpoint = pub_endpoint
        self.sub_endpoint = sub_endpoint
        self.req_endpoint = req_endpoint
        self.context = context or zmq.asyncio.Context.instance()
        self.timeout = timeout
        
        # Initialize sockets
        self.pub_socket = None
        self.sub_socket = None
        self.req_socket = None
        
        # Subscription topics
        self.topics = set()
        
        # Callback handlers for subscription messages
        self.handlers = {}
        
        # Task for handling subscription messages
        self.sub_task = None
        
        # Flag to indicate if the client is running
        self.running = False
    
    async def connect(self) -> None:
        """
        Connect to the Rust component.
        
        Raises:
            CommunicationError: If connection fails
        """
        try:
            # Create publisher socket
            self.pub_socket = self.context.socket(zmq.PUB)
            self.pub_socket.connect(self.pub_endpoint)
            
            # Create subscriber socket
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.connect(self.sub_endpoint)
            
            # Create request-reply socket
            self.req_socket = self.context.socket(zmq.REQ)
            self.req_socket.connect(self.req_endpoint)
            self.req_socket.setsockopt(zmq.RCVTIMEO, self.timeout)
            
            # Start subscription handler
            self.running = True
            self.sub_task = asyncio.create_task(self._handle_subscriptions())
            
            logger.info("Connected to Rust component")
        except Exception as e:
            raise CommunicationError(f"Failed to connect to Rust component: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from the Rust component."""
        self.running = False
        
        # Cancel subscription handler task
        if self.sub_task:
            self.sub_task.cancel()
            try:
                await self.sub_task
            except asyncio.CancelledError:
                pass
            self.sub_task = None
        
        # Close sockets
        if self.pub_socket:
            self.pub_socket.close()
            self.pub_socket = None
        
        if self.sub_socket:
            self.sub_socket.close()
            self.sub_socket = None
        
        if self.req_socket:
            self.req_socket.close()
            self.req_socket = None
        
        logger.info("Disconnected from Rust component")
    
    async def publish(self, topic: str, data: Dict[str, Any]) -> None:
        """
        Publish a message to the Rust component.
        
        Args:
            topic: Message topic
            data: Message data
            
        Raises:
            CommunicationError: If publishing fails
        """
        if not self.pub_socket:
            raise CommunicationError("Not connected to Rust component")
        
        try:
            # Create message
            message = {
                "topic": topic,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }
            
            # Serialize message
            message_json = json.dumps(message)
            
            # Send message
            await self.pub_socket.send_multipart([
                topic.encode("utf-8"),
                message_json.encode("utf-8"),
            ])
            
            logger.debug(f"Published message to topic '{topic}'")
        except Exception as e:
            raise CommunicationError(f"Failed to publish message: {str(e)}")
    
    async def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to a topic from the Rust component.
        
        Args:
            topic: Topic to subscribe to
            handler: Callback function to handle messages
            
        Raises:
            CommunicationError: If subscription fails
        """
        if not self.sub_socket:
            raise CommunicationError("Not connected to Rust component")
        
        try:
            # Subscribe to topic
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, topic.encode("utf-8"))
            self.topics.add(topic)
            
            # Register handler
            self.handlers[topic] = handler
            
            logger.info(f"Subscribed to topic '{topic}'")
        except Exception as e:
            raise CommunicationError(f"Failed to subscribe to topic '{topic}': {str(e)}")
    
    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            
        Raises:
            CommunicationError: If unsubscription fails
        """
        if not self.sub_socket:
            raise CommunicationError("Not connected to Rust component")
        
        try:
            # Unsubscribe from topic
            self.sub_socket.setsockopt(zmq.UNSUBSCRIBE, topic.encode("utf-8"))
            self.topics.discard(topic)
            
            # Remove handler
            if topic in self.handlers:
                del self.handlers[topic]
            
            logger.info(f"Unsubscribed from topic '{topic}'")
        except Exception as e:
            raise CommunicationError(f"Failed to unsubscribe from topic '{topic}': {str(e)}")
    
    async def request(self, request_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request to the Rust component and wait for a response.
        
        Args:
            request_type: Type of request
            data: Request data
            
        Returns:
            Dict[str, Any]: Response data
            
        Raises:
            CommunicationError: If request fails
        """
        if not self.req_socket:
            raise CommunicationError("Not connected to Rust component")
        
        try:
            # Create request
            request = {
                "request": request_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }
            
            # Serialize request
            request_json = json.dumps(request)
            
            # Send request
            await self.req_socket.send(request_json.encode("utf-8"))
            
            # Wait for response
            response_json = await self.req_socket.recv()
            
            # Deserialize response
            response = json.loads(response_json.decode("utf-8"))
            
            logger.debug(f"Received response for request '{request_type}'")
            
            return response
        except zmq.error.Again:
            raise CommunicationError(f"Request '{request_type}' timed out")
        except Exception as e:
            raise CommunicationError(f"Failed to send request '{request_type}': {str(e)}")
    
    async def _handle_subscriptions(self) -> None:
        """Handle subscription messages."""
        if not self.sub_socket:
            return
        
        while self.running:
            try:
                # Wait for message
                multipart = await self.sub_socket.recv_multipart()
                
                if len(multipart) != 2:
                    logger.warning(f"Received invalid multipart message: {multipart}")
                    continue
                
                # Parse message
                topic = multipart[0].decode("utf-8")
                message_json = multipart[1].decode("utf-8")
                message = json.loads(message_json)
                
                # Call handler
                if topic in self.handlers:
                    try:
                        self.handlers[topic](message)
                    except Exception as e:
                        logger.error(f"Error in handler for topic '{topic}': {str(e)}")
                else:
                    logger.warning(f"No handler for topic '{topic}'")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error handling subscription message: {str(e)}")
                await asyncio.sleep(0.1)  # Avoid tight loop on error

class TransactionPrepClient:
    """Client for communicating with the Rust Transaction Preparation Service."""
    
    def __init__(
        self,
        comm_client: Optional[RustCommClient] = None,
        pub_endpoint: str = "tcp://127.0.0.1:5555",
        sub_endpoint: str = "tcp://127.0.0.1:5556",
        req_endpoint: str = "tcp://127.0.0.1:5557",
    ):
        """
        Initialize the Transaction Preparation client.
        
        Args:
            comm_client: Rust communication client (created if not provided)
            pub_endpoint: ZeroMQ publisher endpoint
            sub_endpoint: ZeroMQ subscriber endpoint
            req_endpoint: ZeroMQ request-reply endpoint
        """
        self.comm_client = comm_client or RustCommClient(
            pub_endpoint=pub_endpoint,
            sub_endpoint=sub_endpoint,
            req_endpoint=req_endpoint,
        )
    
    async def connect(self) -> None:
        """
        Connect to the Rust Transaction Preparation Service.
        
        Raises:
            CommunicationError: If connection fails
        """
        await self.comm_client.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from the Rust Transaction Preparation Service."""
        await self.comm_client.disconnect()
    
    async def prepare_transaction(
        self,
        instructions: List[Dict[str, Any]],
        signers: List[str],
        recent_blockhash: Optional[str] = None,
        fee_payer: Optional[str] = None,
        compute_budget: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a transaction.
        
        Args:
            instructions: Transaction instructions
            signers: List of signer public keys
            recent_blockhash: Recent blockhash (fetched if not provided)
            fee_payer: Fee payer public key (first signer if not provided)
            compute_budget: Compute budget parameters
            
        Returns:
            Dict[str, Any]: Prepared transaction data
            
        Raises:
            CommunicationError: If transaction preparation fails
        """
        request_data = {
            "instructions": instructions,
            "signers": signers,
        }
        
        if recent_blockhash:
            request_data["recent_blockhash"] = recent_blockhash
        
        if fee_payer:
            request_data["fee_payer"] = fee_payer
        
        if compute_budget:
            request_data["compute_budget"] = compute_budget
        
        response = await self.comm_client.request("prepare_transaction", request_data)
        
        if response.get("status") != "success":
            raise CommunicationError(f"Failed to prepare transaction: {response.get('error', 'Unknown error')}")
        
        return response.get("data", {})
    
    async def sign_transaction(
        self,
        transaction_data: Dict[str, Any],
        keypair_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sign a transaction.
        
        Args:
            transaction_data: Transaction data
            keypair_path: Path to keypair file (uses default if not provided)
            
        Returns:
            Dict[str, Any]: Signed transaction data
            
        Raises:
            CommunicationError: If transaction signing fails
        """
        request_data = {
            "transaction_data": transaction_data,
        }
        
        if keypair_path:
            request_data["keypair_path"] = keypair_path
        
        response = await self.comm_client.request("sign_transaction", request_data)
        
        if response.get("status") != "success":
            raise CommunicationError(f"Failed to sign transaction: {response.get('error', 'Unknown error')}")
        
        return response.get("data", {})
    
    async def serialize_transaction(
        self,
        transaction_data: Dict[str, Any],
        encoding: str = "base64",
    ) -> str:
        """
        Serialize a transaction.
        
        Args:
            transaction_data: Transaction data
            encoding: Encoding format (base64 or base58)
            
        Returns:
            str: Serialized transaction
            
        Raises:
            CommunicationError: If transaction serialization fails
        """
        request_data = {
            "transaction_data": transaction_data,
            "encoding": encoding,
        }
        
        response = await self.comm_client.request("serialize_transaction", request_data)
        
        if response.get("status") != "success":
            raise CommunicationError(f"Failed to serialize transaction: {response.get('error', 'Unknown error')}")
        
        return response.get("data", {}).get("serialized_transaction", "")
