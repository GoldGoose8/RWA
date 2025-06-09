#!/usr/bin/env python3
"""
Transaction Processor

This module provides a processor for transaction data.
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

class TransactionProcessor:
    """Processor for transaction data."""
    
    def __init__(self):
        """Initialize the transaction processor."""
        # Initialize transaction cache
        self.transactions = {}
        
        # Initialize transaction metrics
        self.metrics = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "total_volume": 0.0,
            "average_fee": 0.0,
            "total_fees": 0.0,
            "transactions_per_second": 0.0,
            "last_update": datetime.now().isoformat(),
        }
        
        # Initialize transaction history
        self.transaction_history = []
        
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
        
        logger.info("Initialized transaction processor")
    
    def process(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process transaction data.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            Dict[str, Any]: Processed transaction data
        """
        try:
            # Extract transaction signature
            signature = transaction_data.get("signature", "")
            
            if not signature:
                logger.warning("Transaction data missing signature")
                return {}
            
            # Extract transaction status
            status = transaction_data.get("meta", {}).get("status", {})
            is_successful = status.get("Ok") is not None
            
            # Extract transaction fee
            fee = transaction_data.get("meta", {}).get("fee", 0)
            
            # Extract transaction timestamp
            timestamp = transaction_data.get("blockTime", int(time.time()))
            
            # Extract transaction instructions
            instructions = self._extract_instructions(transaction_data)
            
            # Extract transaction accounts
            accounts = self._extract_accounts(transaction_data)
            
            # Extract transaction tokens
            tokens = self._extract_tokens(transaction_data)
            
            # Extract transaction volume
            volume = self._extract_volume(transaction_data)
            
            # Extract transaction type
            tx_type = self._extract_transaction_type(transaction_data)
            
            # Create processed transaction
            processed_transaction = {
                "signature": signature,
                "status": "success" if is_successful else "failed",
                "fee": fee,
                "timestamp": timestamp,
                "instructions": instructions,
                "accounts": accounts,
                "tokens": tokens,
                "volume": volume,
                "type": tx_type,
            }
            
            # Update transaction cache
            self.transactions[signature] = processed_transaction
            
            # Update transaction history
            self.transaction_history.append(processed_transaction)
            
            # Limit transaction history to 1000 transactions
            if len(self.transaction_history) > 1000:
                self.transaction_history.pop(0)
            
            # Update metrics
            self._update_metrics(processed_transaction)
            
            return processed_transaction
        except Exception as e:
            logger.error(f"Error processing transaction data: {str(e)}")
            return {}
    
    def get_transaction(self, signature: str) -> Dict[str, Any]:
        """
        Get transaction by signature.
        
        Args:
            signature: Transaction signature
            
        Returns:
            Dict[str, Any]: Transaction data
        """
        return self.transactions.get(signature, {})
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get transaction metrics.
        
        Returns:
            Dict[str, Any]: Transaction metrics
        """
        return self.metrics
    
    def get_transaction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get transaction history.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List[Dict[str, Any]]: Transaction history
        """
        return self.transaction_history[-limit:]
    
    def _extract_instructions(self, transaction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract instructions from transaction data.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            List[Dict[str, Any]]: Instructions
        """
        instructions = []
        
        # Extract message
        message = transaction_data.get("transaction", {}).get("message", {})
        
        # Extract account keys
        account_keys = message.get("accountKeys", [])
        
        # Extract instructions
        raw_instructions = message.get("instructions", [])
        
        for instruction in raw_instructions:
            # Extract program ID
            program_id_index = instruction.get("programIdIndex", 0)
            program_id = account_keys[program_id_index] if program_id_index < len(account_keys) else ""
            
            # Extract accounts
            accounts = []
            for account_index in instruction.get("accounts", []):
                if account_index < len(account_keys):
                    accounts.append(account_keys[account_index])
            
            # Extract data
            data = instruction.get("data", "")
            
            # Get program name
            program_name = self.program_ids.get(program_id, "Unknown Program")
            
            # Add instruction
            instructions.append({
                "program_id": program_id,
                "program_name": program_name,
                "accounts": accounts,
                "data": data,
            })
        
        return instructions
    
    def _extract_accounts(self, transaction_data: Dict[str, Any]) -> List[str]:
        """
        Extract accounts from transaction data.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            List[str]: Accounts
        """
        # Extract message
        message = transaction_data.get("transaction", {}).get("message", {})
        
        # Extract account keys
        account_keys = message.get("accountKeys", [])
        
        return account_keys
    
    def _extract_tokens(self, transaction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tokens from transaction data.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            List[Dict[str, Any]]: Tokens
        """
        tokens = []
        
        # Extract token balances
        token_balances = transaction_data.get("meta", {}).get("postTokenBalances", [])
        
        for token_balance in token_balances:
            # Extract mint
            mint = token_balance.get("mint", "")
            
            # Extract owner
            owner = token_balance.get("owner", "")
            
            # Extract amount
            amount = token_balance.get("uiTokenAmount", {}).get("uiAmount", 0)
            
            # Add token
            tokens.append({
                "mint": mint,
                "owner": owner,
                "amount": amount,
            })
        
        return tokens
    
    def _extract_volume(self, transaction_data: Dict[str, Any]) -> float:
        """
        Extract volume from transaction data.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            float: Volume in SOL
        """
        # Extract pre and post balances
        pre_balances = transaction_data.get("meta", {}).get("preBalances", [])
        post_balances = transaction_data.get("meta", {}).get("postBalances", [])
        
        # Calculate volume as the sum of absolute balance changes
        volume = 0.0
        
        for i in range(min(len(pre_balances), len(post_balances))):
            balance_change = abs(post_balances[i] - pre_balances[i])
            volume += balance_change
        
        # Convert from lamports to SOL
        volume_sol = volume / 1_000_000_000.0
        
        return volume_sol
    
    def _extract_transaction_type(self, transaction_data: Dict[str, Any]) -> str:
        """
        Extract transaction type from transaction data.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            str: Transaction type
        """
        # Extract instructions
        instructions = self._extract_instructions(transaction_data)
        
        # Check for token swap
        for instruction in instructions:
            program_id = instruction.get("program_id", "")
            program_name = instruction.get("program_name", "")
            
            if program_id == "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4" or program_id == "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB":
                return "token_swap"
            
            if program_id == "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP" or program_id == "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc":
                return "token_swap"
            
            if program_id == "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX":
                return "token_swap"
            
            if program_id == "M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K":
                return "nft_trade"
        
        # Check for token transfer
        token_balances = transaction_data.get("meta", {}).get("postTokenBalances", [])
        if token_balances:
            return "token_transfer"
        
        # Check for SOL transfer
        pre_balances = transaction_data.get("meta", {}).get("preBalances", [])
        post_balances = transaction_data.get("meta", {}).get("postBalances", [])
        
        if len(pre_balances) >= 2 and len(post_balances) >= 2:
            if pre_balances[0] > post_balances[0] and post_balances[1] > pre_balances[1]:
                return "sol_transfer"
        
        return "unknown"
    
    def _update_metrics(self, transaction: Dict[str, Any]) -> None:
        """
        Update transaction metrics.
        
        Args:
            transaction: Processed transaction
        """
        # Update total transactions
        self.metrics["total_transactions"] += 1
        
        # Update successful/failed transactions
        if transaction.get("status") == "success":
            self.metrics["successful_transactions"] += 1
        else:
            self.metrics["failed_transactions"] += 1
        
        # Update total volume
        self.metrics["total_volume"] += transaction.get("volume", 0.0)
        
        # Update total fees
        self.metrics["total_fees"] += transaction.get("fee", 0) / 1_000_000_000.0
        
        # Update average fee
        self.metrics["average_fee"] = self.metrics["total_fees"] / self.metrics["total_transactions"]
        
        # Update transactions per second
        # This is a simple moving average over the last 10 seconds
        now = datetime.now()
        recent_transactions = [tx for tx in self.transaction_history if now.timestamp() - tx.get("timestamp", 0) <= 10]
        self.metrics["transactions_per_second"] = len(recent_transactions) / 10.0
        
        # Update last update timestamp
        self.metrics["last_update"] = datetime.now().isoformat()
