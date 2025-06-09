#!/usr/bin/env python3
"""
Account Processor

This module provides a processor for account data.
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AccountProcessor:
    """Processor for account data."""
    
    def __init__(self):
        """Initialize the account processor."""
        # Initialize account cache
        self.accounts = {}
        
        # Initialize account metrics
        self.metrics = {
            "total_accounts": 0,
            "token_accounts": 0,
            "system_accounts": 0,
            "program_accounts": 0,
            "last_update": datetime.now().isoformat(),
        }
        
        # Initialize token metadata cache
        self.token_metadata = {
            "So11111111111111111111111111111111111111112": {
                "symbol": "SOL",
                "name": "Wrapped SOL",
                "decimals": 9,
                "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
            },
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                "symbol": "USDC",
                "name": "USD Coin",
                "decimals": 6,
                "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png",
            },
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
                "symbol": "USDT",
                "name": "USDT",
                "decimals": 6,
                "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB/logo.png",
            },
            "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL": {
                "symbol": "JTO",
                "name": "Jito",
                "decimals": 9,
                "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL/logo.png",
            },
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {
                "symbol": "BONK",
                "name": "Bonk",
                "decimals": 5,
                "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263/logo.png",
            },
        }
        
        # Initialize program ID cache
        self.program_ids = {
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "Token Program",
            "11111111111111111111111111111111": "System Program",
            "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL": "Associated Token Account Program",
            "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter Aggregator v6",
            "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB": "Jupiter Aggregator v4",
            "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP": "Orca Whirlpool",
            "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca Whirlpool",
            "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX": "Openbook v2",
            "7sPptkymzvayoSbLXzBsXEF8TSf3typNnAWkrKrDizNb": "Meteora",
            "M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K": "Magic Eden v2",
        }
        
        logger.info("Initialized account processor")
    
    def process(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process account data.
        
        Args:
            account_data: Account data
            
        Returns:
            Dict[str, Any]: Processed account data
        """
        try:
            # Extract account address
            address = account_data.get("pubkey", "")
            
            if not address:
                logger.warning("Account data missing address")
                return {}
            
            # Extract account owner
            owner = account_data.get("owner", "")
            
            # Extract account data
            data = account_data.get("data", "")
            
            # Extract account lamports
            lamports = account_data.get("lamports", 0)
            
            # Extract account executable flag
            executable = account_data.get("executable", False)
            
            # Extract account rent epoch
            rent_epoch = account_data.get("rentEpoch", 0)
            
            # Determine account type
            account_type = self._determine_account_type(owner, data)
            
            # Extract token data if token account
            token_data = {}
            if account_type == "token":
                token_data = self._extract_token_data(data)
            
            # Create processed account
            processed_account = {
                "address": address,
                "owner": owner,
                "lamports": lamports,
                "executable": executable,
                "rent_epoch": rent_epoch,
                "type": account_type,
                "token_data": token_data,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Update account cache
            self.accounts[address] = processed_account
            
            # Update metrics
            self._update_metrics(processed_account)
            
            return processed_account
        except Exception as e:
            logger.error(f"Error processing account data: {str(e)}")
            return {}
    
    def get_account(self, address: str) -> Dict[str, Any]:
        """
        Get account by address.
        
        Args:
            address: Account address
            
        Returns:
            Dict[str, Any]: Account data
        """
        return self.accounts.get(address, {})
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get account metrics.
        
        Returns:
            Dict[str, Any]: Account metrics
        """
        return self.metrics
    
    def _determine_account_type(self, owner: str, data: Any) -> str:
        """
        Determine account type.
        
        Args:
            owner: Account owner
            data: Account data
            
        Returns:
            str: Account type
        """
        # Check if program account
        if owner == "BPFLoader2111111111111111111111111111111111":
            return "program"
        
        # Check if token account
        if owner == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
            return "token"
        
        # Check if system account
        if owner == "11111111111111111111111111111111":
            return "system"
        
        # Check if stake account
        if owner == "Stake11111111111111111111111111111111111111":
            return "stake"
        
        # Check if vote account
        if owner == "Vote111111111111111111111111111111111111111":
            return "vote"
        
        # Check if config account
        if owner == "Config1111111111111111111111111111111111111":
            return "config"
        
        # Check if sysvar account
        if owner == "Sysvar1111111111111111111111111111111111111":
            return "sysvar"
        
        # Unknown account type
        return "unknown"
    
    def _extract_token_data(self, data: Any) -> Dict[str, Any]:
        """
        Extract token data from account data.
        
        Args:
            data: Account data
            
        Returns:
            Dict[str, Any]: Token data
        """
        token_data = {}
        
        # Check if data is parsed
        if isinstance(data, dict) and "parsed" in data:
            parsed_data = data.get("parsed", {})
            
            # Check if token account
            if parsed_data.get("type") == "account":
                info = parsed_data.get("info", {})
                
                # Extract token data
                mint = info.get("mint", "")
                owner = info.get("owner", "")
                amount = info.get("tokenAmount", {}).get("amount", "0")
                decimals = info.get("tokenAmount", {}).get("decimals", 0)
                ui_amount = info.get("tokenAmount", {}).get("uiAmount", 0)
                
                # Get token metadata
                token_metadata = self.token_metadata.get(mint, {})
                
                # Create token data
                token_data = {
                    "mint": mint,
                    "owner": owner,
                    "amount": amount,
                    "decimals": decimals,
                    "ui_amount": ui_amount,
                    "symbol": token_metadata.get("symbol", ""),
                    "name": token_metadata.get("name", ""),
                    "logo": token_metadata.get("logo", ""),
                }
        
        return token_data
    
    def _update_metrics(self, account: Dict[str, Any]) -> None:
        """
        Update account metrics.
        
        Args:
            account: Processed account
        """
        # Update total accounts
        self.metrics["total_accounts"] += 1
        
        # Update account type counts
        account_type = account.get("type", "unknown")
        if account_type == "token":
            self.metrics["token_accounts"] += 1
        elif account_type == "system":
            self.metrics["system_accounts"] += 1
        elif account_type == "program":
            self.metrics["program_accounts"] += 1
        
        # Update last update timestamp
        self.metrics["last_update"] = datetime.now().isoformat()
