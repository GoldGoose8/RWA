#!/usr/bin/env python3
"""
Pump.fun Tracker Module

This module is responsible for tracking token launches on pump.fun platform
and identifying potential trading opportunities.
"""

import os
import json
import logging
import asyncio
import httpx
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'output', 'pumpfun_log.txt'
        )),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('pumpfun_tracker')

class PumpFunTracker:
    """
    Tracker for monitoring token launches on pump.fun platform
    and identifying potential trading opportunities.
    """
    
    def __init__(self, min_liquidity_threshold: float = 5000.0):
        """
        Initialize the PumpFunTracker.
        
        Args:
            min_liquidity_threshold: Minimum liquidity threshold in USD
        """
        self.min_liquidity_threshold = min_liquidity_threshold
        self.base_url = "https://api.pump.fun/v1"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.tracked_launches = set()
        self.load_tracked_launches()
        
    def load_tracked_launches(self, file_path: str = None) -> None:
        """
        Load previously tracked launches to avoid duplicates.
        
        Args:
            file_path: Path to the tracked launches file
        """
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'output', 'tracked_launches.json'
            )
            
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.tracked_launches = set(data.get('launches', []))
                logger.info(f"Loaded {len(self.tracked_launches)} tracked launches")
        except Exception as e:
            logger.error(f"Failed to load tracked launches: {str(e)}")
    
    def save_tracked_launches(self, file_path: str = None) -> None:
        """
        Save tracked launches to avoid duplicates in future scans.
        
        Args:
            file_path: Path to save the tracked launches file
        """
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'output', 'tracked_launches.json'
            )
            
        try:
            with open(file_path, 'w') as f:
                json.dump({'launches': list(self.tracked_launches)}, f, indent=2)
            logger.info(f"Saved {len(self.tracked_launches)} tracked launches")
        except Exception as e:
            logger.error(f"Failed to save tracked launches: {str(e)}")
    
    async def get_upcoming_launches(self) -> List[Dict[str, Any]]:
        """
        Get upcoming token launches on pump.fun.
        
        Returns:
            List of upcoming launch data dictionaries
        """
        try:
            url = f"{self.base_url}/launches/upcoming"
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Filter out already tracked launches
            upcoming_launches = []
            for launch in data.get('launches', []):
                launch_id = launch.get('id')
                if launch_id and launch_id not in self.tracked_launches:
                    upcoming_launches.append(launch)
            
            logger.info(f"Found {len(upcoming_launches)} new upcoming launches")
            return upcoming_launches
            
        except Exception as e:
            logger.error(f"Failed to get upcoming launches: {str(e)}")
            return []
    
    async def get_active_launches(self) -> List[Dict[str, Any]]:
        """
        Get active token launches on pump.fun.
        
        Returns:
            List of active launch data dictionaries
        """
        try:
            url = f"{self.base_url}/launches/active"
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Filter by liquidity threshold
            active_launches = []
            for launch in data.get('launches', []):
                liquidity = launch.get('liquidity', 0)
                if liquidity >= self.min_liquidity_threshold:
                    active_launches.append(launch)
            
            logger.info(f"Found {len(active_launches)} active launches with sufficient liquidity")
            return active_launches
            
        except Exception as e:
            logger.error(f"Failed to get active launches: {str(e)}")
            return []
    
    async def get_launch_details(self, launch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific launch.
        
        Args:
            launch_id: Launch ID
            
        Returns:
            Dictionary with launch details or None if failed
        """
        try:
            url = f"{self.base_url}/launches/{launch_id}"
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            
            return data.get('launch')
            
        except Exception as e:
            logger.error(f"Failed to get launch details for {launch_id}: {str(e)}")
            return None
    
    async def track_launches(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Track upcoming and active launches on pump.fun.
        
        Returns:
            Tuple of (upcoming launches, active launches) with detailed information
        """
        upcoming = await self.get_upcoming_launches()
        active = await self.get_active_launches()
        
        # Get details for upcoming launches
        upcoming_with_details = []
        for launch in upcoming:
            launch_id = launch.get('id')
            if launch_id:
                details = await self.get_launch_details(launch_id)
                if details:
                    upcoming_with_details.append(details)
                    self.tracked_launches.add(launch_id)
        
        # Get details for active launches
        active_with_details = []
        for launch in active:
            launch_id = launch.get('id')
            if launch_id:
                details = await self.get_launch_details(launch_id)
                if details:
                    active_with_details.append(details)
                    self.tracked_launches.add(launch_id)
        
        # Save updated tracked launches
        self.save_tracked_launches()
        
        return upcoming_with_details, active_with_details
    
    async def close(self):
        """Close the HTTP client session."""
        await self.http_client.aclose()

async def main():
    """Main function to demonstrate the tracker."""
    tracker = PumpFunTracker()
    upcoming, active = await tracker.track_launches()
    
    # Save launches to file
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'output'
    )
    
    # Save upcoming launches
    upcoming_path = os.path.join(output_dir, 'upcoming_launches.json')
    with open(upcoming_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'launches': upcoming
        }, f, indent=2)
    
    # Save active launches
    active_path = os.path.join(output_dir, 'active_launches.json')
    with open(active_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'launches': active
        }, f, indent=2)
    
    logger.info(f"Saved {len(upcoming)} upcoming launches and {len(active)} active launches")
    await tracker.close()

if __name__ == "__main__":
    asyncio.run(main())
