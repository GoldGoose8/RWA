#!/usr/bin/env python3
"""
Position Flattener - Critical Risk Management Component
Ensures all positions are closed when trading sessions end to prevent overnight losses.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import glob
import os

logger = logging.getLogger(__name__)

class PositionFlattener:
    """Flattens all open positions when trading sessions end."""
    
    def __init__(self, wallet_manager, tx_builder, tx_executor, telegram_notifier=None):
        """Initialize position flattener."""
        self.wallet_manager = wallet_manager
        self.tx_builder = tx_builder
        self.tx_executor = tx_executor
        self.telegram_notifier = telegram_notifier
        
        # Position tracking
        self.net_position_sol = 0.0
        self.total_buy_volume = 0.0
        self.total_sell_volume = 0.0
        self.trades_analyzed = []
        
    def analyze_session_trades(self, trades_folder: str = "output/enhanced_live_trading/trades/") -> Dict[str, float]:
        """Analyze all trades from current session to calculate net position."""
        
        if not os.path.exists(trades_folder):
            logger.warning(f"Trades folder not found: {trades_folder}")
            return {'net_position': 0.0, 'buy_volume': 0.0, 'sell_volume': 0.0}
        
        trade_files = glob.glob(os.path.join(trades_folder, "trade_*.json"))
        trade_files.sort()  # Chronological order
        
        buy_volume = 0.0
        sell_volume = 0.0
        successful_trades = []
        
        for trade_file in trade_files:
            try:
                with open(trade_file, 'r') as f:
                    trade_data = json.load(f)
                
                # Only count successful trades
                if trade_data.get('transaction_result', {}).get('success', False):
                    signal = trade_data.get('signal', {})
                    action = signal.get('action', '')
                    size = signal.get('size', 0.0)
                    
                    if action == 'BUY':
                        buy_volume += size
                    elif action == 'SELL':
                        sell_volume += size
                    
                    successful_trades.append(trade_data)
                    
            except Exception as e:
                logger.error(f"Error analyzing trade file {trade_file}: {e}")
        
        net_position = buy_volume - sell_volume
        
        self.net_position_sol = net_position
        self.total_buy_volume = buy_volume
        self.total_sell_volume = sell_volume
        self.trades_analyzed = successful_trades
        
        logger.info(f"Position analysis: BUY {buy_volume:.4f} SOL, SELL {sell_volume:.4f} SOL, NET {net_position:+.4f} SOL")
        
        return {
            'net_position': net_position,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'total_trades': len(successful_trades)
        }
    
    async def check_position_risk(self, current_price: float, risk_threshold_usd: float = 50.0) -> Dict[str, Any]:
        """Check if current position poses significant risk."""
        
        position_value_usd = abs(self.net_position_sol) * current_price
        risk_level = "LOW"
        
        if position_value_usd > risk_threshold_usd:
            risk_level = "HIGH"
        elif position_value_usd > risk_threshold_usd * 0.5:
            risk_level = "MEDIUM"
        
        risk_assessment = {
            'net_position_sol': self.net_position_sol,
            'position_value_usd': position_value_usd,
            'current_price': current_price,
            'risk_level': risk_level,
            'should_flatten': risk_level in ["HIGH", "MEDIUM"],
            'risk_threshold': risk_threshold_usd
        }
        
        logger.info(f"Position risk: {risk_level} (${position_value_usd:.2f} exposure)")
        
        return risk_assessment
    
    async def create_flattening_transaction(self, current_price: float) -> Optional[Dict[str, Any]]:
        """Create transaction to flatten the current position."""
        
        if abs(self.net_position_sol) < 0.001:  # Less than 0.001 SOL, ignore
            logger.info("Position too small to flatten")
            return None
        
        # Determine flattening action
        if self.net_position_sol > 0:
            # Net long position, need to SELL
            action = "SELL"
            size = self.net_position_sol
        else:
            # Net short position, need to BUY
            action = "BUY"
            size = abs(self.net_position_sol)
        
        # Create flattening signal
        flattening_signal = {
            'action': action,
            'market': 'SOL-USDC',
            'price': current_price,
            'size': size,
            'confidence': 1.0,  # 100% confidence for risk management
            'timestamp': datetime.now().isoformat(),
            'strategy': 'position_flattening',
            'metadata': {
                'signal_strength': 1.0,
                'market_regime': 'risk_management',
                'volatility': 0.0,
                'reason': 'session_end_flattening'
            }
        }
        
        logger.info(f"Creating flattening transaction: {action} {size:.4f} SOL at ${current_price:.2f}")
        
        try:
            # Build transaction
            transaction = await self.tx_builder.build_transaction(flattening_signal)
            
            if transaction:
                logger.info("✅ Flattening transaction built successfully")
                return {
                    'signal': flattening_signal,
                    'transaction': transaction,
                    'reason': 'position_flattening'
                }
            else:
                logger.error("❌ Failed to build flattening transaction")
                return None
                
        except Exception as e:
            logger.error(f"Error creating flattening transaction: {e}")
            return None
    
    async def execute_position_flattening(self, current_price: float, force_flatten: bool = False) -> Dict[str, Any]:
        """Execute position flattening if needed."""
        
        logger.info("🔄 Starting position flattening analysis...")
        
        # Analyze current session trades
        position_analysis = self.analyze_session_trades()
        
        # Check position risk
        risk_assessment = await self.check_position_risk(current_price)
        
        # Determine if flattening is needed
        should_flatten = force_flatten or risk_assessment['should_flatten']
        
        result = {
            'position_analysis': position_analysis,
            'risk_assessment': risk_assessment,
            'flattening_executed': False,
            'transaction_result': None,
            'reason': 'no_action_needed'
        }
        
        if not should_flatten:
            logger.info("✅ Position within acceptable risk limits, no flattening needed")
            result['reason'] = 'risk_acceptable'
            return result
        
        logger.warning(f"⚠️ Position flattening required: {risk_assessment['risk_level']} risk")
        
        # Send Telegram alert about flattening
        if self.telegram_notifier and self.telegram_notifier.enabled:
            await self.telegram_notifier.notify_error(
                f"Position flattening required: {self.net_position_sol:+.4f} SOL (${risk_assessment['position_value_usd']:.2f} exposure)",
                "Position Flattener"
            )
        
        # Create and execute flattening transaction
        flattening_tx = await self.create_flattening_transaction(current_price)
        
        if not flattening_tx:
            logger.error("❌ Failed to create flattening transaction")
            result['reason'] = 'transaction_creation_failed'
            return result
        
        try:
            # Execute the flattening transaction
            logger.info("🔄 Executing position flattening transaction...")
            tx_result = await self.tx_executor.send_transaction(flattening_tx['transaction'])
            
            result['transaction_result'] = tx_result
            
            if tx_result.get('success', False):
                logger.info(f"✅ Position flattening successful: {tx_result.get('signature')}")
                result['flattening_executed'] = True
                result['reason'] = 'flattening_successful'
                
                # Send success notification
                if self.telegram_notifier and self.telegram_notifier.enabled:
                    message = f"""
🔄 *POSITION FLATTENED* 🔄

*Action*: {flattening_tx['signal']['action']}
*Size*: {flattening_tx['signal']['size']:.4f} SOL
*Price*: ${current_price:.2f}
*Reason*: Session end risk management

*Signature*: `{tx_result.get('signature', 'N/A')[:16]}...`

Position successfully flattened! ✅
"""
                    await self.telegram_notifier.send_message(message)
                
            else:
                logger.error(f"❌ Position flattening failed: {tx_result.get('error')}")
                result['reason'] = 'flattening_failed'
                
                # Send failure notification
                if self.telegram_notifier and self.telegram_notifier.enabled:
                    await self.telegram_notifier.notify_error(
                        f"Position flattening FAILED: {tx_result.get('error', 'Unknown error')}",
                        "Position Flattener"
                    )
            
        except Exception as e:
            logger.error(f"Error executing flattening transaction: {e}")
            result['reason'] = 'execution_error'
            result['error'] = str(e)
        
        return result
    
    async def emergency_flatten_all(self, current_price: float) -> Dict[str, Any]:
        """Emergency function to flatten all positions regardless of risk assessment."""
        
        logger.warning("🚨 EMERGENCY POSITION FLATTENING INITIATED")
        
        # Send emergency alert
        if self.telegram_notifier and self.telegram_notifier.enabled:
            await self.telegram_notifier.notify_error(
                "EMERGENCY POSITION FLATTENING INITIATED - All positions will be closed immediately",
                "Emergency Flattener"
            )
        
        return await self.execute_position_flattening(current_price, force_flatten=True)
