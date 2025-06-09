#!/usr/bin/env python3
"""
Robust RPC Manager for Synergy7 Trading System

Handles multiple RPC endpoints with automatic failover, health checking,
and intelligent routing to ensure maximum uptime and reliability.
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    logger.warning("httpx not available, using basic HTTP client")
    httpx = None


class EndpointStatus(Enum):
    """Endpoint status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class RpcEndpoint:
    """RPC endpoint configuration."""
    name: str
    url: str
    api_key: Optional[str] = None
    priority: int = 1  # Lower number = higher priority
    timeout: float = 30.0
    max_retries: int = 3
    status: EndpointStatus = EndpointStatus.UNKNOWN
    last_check: float = 0.0
    consecutive_failures: int = 0
    response_time: float = 0.0
    features: List[str] = None  # e.g., ['bundles', 'streaming']
    
    def __post_init__(self):
        if self.features is None:
            self.features = []


class RobustRpcManager:
    """
    Robust RPC manager with automatic failover and health monitoring.
    
    Features:
    - Multiple endpoint support with priority-based routing
    - Automatic health checking and failover
    - Circuit breaker pattern for failed endpoints
    - Performance monitoring and optimization
    - Intelligent request routing based on endpoint capabilities
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the RPC manager."""
        self.config = config or {}
        self.endpoints: Dict[str, RpcEndpoint] = {}
        self.current_primary: Optional[str] = None
        self.health_check_interval = 60.0  # Check health every minute
        self.circuit_breaker_threshold = 3  # Failures before marking as failed
        self.recovery_check_interval = 300.0  # Check failed endpoints every 5 minutes
        
        # Performance tracking
        self.request_count = 0
        self.success_count = 0
        self.total_response_time = 0.0
        
        # Initialize endpoints from environment
        self._load_endpoints_from_env()
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor_loop())
        
        logger.info(f"🔧 RobustRpcManager initialized with {len(self.endpoints)} endpoints")
    
    def _load_endpoints_from_env(self):
        """Load endpoint configurations from environment variables."""
        # QuickNode endpoint
        quicknode_url = os.getenv('QUICKNODE_RPC_URL')
        quicknode_api_key = os.getenv('QUICKNODE_API_KEY')
        if quicknode_url:
            self.endpoints['quicknode'] = RpcEndpoint(
                name='quicknode',
                url=quicknode_url,
                api_key=quicknode_api_key,
                priority=2,  # Lower priority due to connectivity issues
                timeout=15.0,  # Shorter timeout for faster failover
                features=['bundles', 'high_performance']
            )
        
        # Helius endpoint (primary)
        helius_url = os.getenv('HELIUS_RPC_URL')
        helius_api_key = os.getenv('HELIUS_API_KEY')
        if helius_url:
            self.endpoints['helius'] = RpcEndpoint(
                name='helius',
                url=helius_url,
                api_key=helius_api_key,
                priority=1,  # Highest priority - most reliable
                timeout=30.0,
                features=['enhanced_apis', 'reliable']
            )
        
        # Jito endpoint
        jito_url = os.getenv('JITO_RPC_URL')
        if jito_url:
            self.endpoints['jito'] = RpcEndpoint(
                name='jito',
                url=jito_url,
                priority=3,
                timeout=20.0,
                features=['mev_protection', 'bundles']
            )
        
        # Set initial primary endpoint
        self._select_primary_endpoint()
    
    def _select_primary_endpoint(self):
        """Select the best available primary endpoint."""
        # Sort by priority (lower number = higher priority) and status
        available_endpoints = [
            ep for ep in self.endpoints.values() 
            if ep.status != EndpointStatus.FAILED
        ]
        
        if not available_endpoints:
            logger.error("❌ No available endpoints!")
            return
        
        # Sort by priority, then by status
        available_endpoints.sort(key=lambda x: (x.priority, x.consecutive_failures))
        
        new_primary = available_endpoints[0].name
        if new_primary != self.current_primary:
            old_primary = self.current_primary
            self.current_primary = new_primary
            logger.info(f"🔄 Primary endpoint changed: {old_primary} -> {new_primary}")
    
    async def _health_check_endpoint(self, endpoint: RpcEndpoint) -> bool:
        """Check the health of a specific endpoint."""
        if not httpx:
            logger.warning(f"⚠️ Cannot health check {endpoint.name} - httpx not available")
            return False
        
        test_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth",
            "params": []
        }
        
        try:
            start_time = time.time()
            
            headers = {"Content-Type": "application/json"}
            if endpoint.api_key:
                headers["Authorization"] = f"Bearer {endpoint.api_key}"
            
            async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
                response = await client.post(endpoint.url, json=test_payload, headers=headers)
                
                response_time = time.time() - start_time
                endpoint.response_time = response_time
                endpoint.last_check = time.time()
                
                if response.status_code == 200:
                    endpoint.consecutive_failures = 0
                    endpoint.status = EndpointStatus.HEALTHY
                    logger.debug(f"✅ {endpoint.name} health check passed ({response_time:.3f}s)")
                    return True
                else:
                    endpoint.consecutive_failures += 1
                    if endpoint.consecutive_failures >= self.circuit_breaker_threshold:
                        endpoint.status = EndpointStatus.FAILED
                        logger.warning(f"❌ {endpoint.name} marked as failed after {endpoint.consecutive_failures} failures")
                    else:
                        endpoint.status = EndpointStatus.DEGRADED
                    return False
                    
        except Exception as e:
            endpoint.consecutive_failures += 1
            endpoint.last_check = time.time()
            
            if endpoint.consecutive_failures >= self.circuit_breaker_threshold:
                endpoint.status = EndpointStatus.FAILED
                logger.warning(f"❌ {endpoint.name} marked as failed: {str(e)}")
            else:
                endpoint.status = EndpointStatus.DEGRADED
                logger.debug(f"⚠️ {endpoint.name} health check failed: {str(e)}")
            
            return False
    
    async def _health_monitor_loop(self):
        """Continuous health monitoring loop."""
        while True:
            try:
                # Check all endpoints
                for endpoint in self.endpoints.values():
                    # Check healthy/degraded endpoints regularly
                    if endpoint.status in [EndpointStatus.HEALTHY, EndpointStatus.DEGRADED, EndpointStatus.UNKNOWN]:
                        if time.time() - endpoint.last_check > self.health_check_interval:
                            await self._health_check_endpoint(endpoint)
                    
                    # Check failed endpoints less frequently for recovery
                    elif endpoint.status == EndpointStatus.FAILED:
                        if time.time() - endpoint.last_check > self.recovery_check_interval:
                            logger.info(f"🔄 Checking if {endpoint.name} has recovered...")
                            await self._health_check_endpoint(endpoint)
                
                # Reselect primary if needed
                self._select_primary_endpoint()
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in health monitor loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def make_request(self, payload: Dict[str, Any], 
                          preferred_endpoint: Optional[str] = None,
                          require_features: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Make an RPC request with automatic failover.
        
        Args:
            payload: JSON-RPC payload
            preferred_endpoint: Preferred endpoint name (optional)
            require_features: Required endpoint features (optional)
            
        Returns:
            RPC response or error
        """
        self.request_count += 1
        
        # Determine endpoint order
        endpoint_order = self._get_endpoint_order(preferred_endpoint, require_features)
        
        if not endpoint_order:
            return {
                'error': 'No available endpoints',
                'code': -32000
            }
        
        last_error = None
        
        # Try endpoints in order
        for endpoint_name in endpoint_order:
            endpoint = self.endpoints[endpoint_name]
            
            try:
                start_time = time.time()
                result = await self._make_single_request(endpoint, payload)
                response_time = time.time() - start_time
                
                if 'error' not in result:
                    # Success
                    self.success_count += 1
                    self.total_response_time += response_time
                    endpoint.consecutive_failures = 0
                    endpoint.status = EndpointStatus.HEALTHY
                    
                    logger.debug(f"✅ Request successful via {endpoint_name} ({response_time:.3f}s)")
                    return result
                else:
                    # RPC error
                    last_error = result['error']
                    logger.warning(f"⚠️ RPC error from {endpoint_name}: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                endpoint.consecutive_failures += 1
                
                if endpoint.consecutive_failures >= self.circuit_breaker_threshold:
                    endpoint.status = EndpointStatus.FAILED
                    logger.warning(f"❌ {endpoint_name} marked as failed")
                
                logger.warning(f"⚠️ Request failed via {endpoint_name}: {str(e)}")
        
        # All endpoints failed
        return {
            'error': f'All endpoints failed. Last error: {last_error}',
            'code': -32001
        }
    
    def _get_endpoint_order(self, preferred_endpoint: Optional[str] = None,
                           require_features: Optional[List[str]] = None) -> List[str]:
        """Get ordered list of endpoints to try."""
        available_endpoints = []
        
        for name, endpoint in self.endpoints.items():
            # Skip failed endpoints
            if endpoint.status == EndpointStatus.FAILED:
                continue
            
            # Check required features
            if require_features:
                if not all(feature in endpoint.features for feature in require_features):
                    continue
            
            available_endpoints.append((name, endpoint))
        
        if not available_endpoints:
            return []
        
        # Sort by priority and status
        available_endpoints.sort(key=lambda x: (x[1].priority, x[1].consecutive_failures))
        
        endpoint_names = [name for name, _ in available_endpoints]
        
        # Move preferred endpoint to front if specified and available
        if preferred_endpoint and preferred_endpoint in endpoint_names:
            endpoint_names.remove(preferred_endpoint)
            endpoint_names.insert(0, preferred_endpoint)
        
        return endpoint_names
    
    async def _make_single_request(self, endpoint: RpcEndpoint, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to a single endpoint."""
        if not httpx:
            raise Exception("httpx not available for HTTP requests")
        
        headers = {"Content-Type": "application/json"}
        if endpoint.api_key:
            headers["Authorization"] = f"Bearer {endpoint.api_key}"
        
        async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
            response = await client.post(endpoint.url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current manager status."""
        total_requests = self.request_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = (self.total_response_time / self.success_count) if self.success_count > 0 else 0
        
        return {
            'current_primary': self.current_primary,
            'total_requests': total_requests,
            'success_count': self.success_count,
            'success_rate_pct': round(success_rate, 2),
            'avg_response_time_ms': round(avg_response_time * 1000, 2),
            'endpoints': {
                name: {
                    'status': ep.status.value,
                    'consecutive_failures': ep.consecutive_failures,
                    'response_time_ms': round(ep.response_time * 1000, 2),
                    'last_check': ep.last_check,
                    'priority': ep.priority,
                    'features': ep.features
                }
                for name, ep in self.endpoints.items()
            }
        }
    
    async def force_health_check(self):
        """Force immediate health check of all endpoints."""
        logger.info("🔄 Forcing health check of all endpoints...")
        
        for endpoint in self.endpoints.values():
            await self._health_check_endpoint(endpoint)
        
        self._select_primary_endpoint()
        logger.info("✅ Health check completed")
