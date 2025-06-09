"""
Risk Monitoring and Alerting System for Synergy7 Enhanced Trading System.

This module provides real-time risk monitoring with immediate alerting
for VaR breaches, position limits, correlation exposure, and other risk metrics.
"""

import os
import sys
import asyncio
import logging
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict, deque

# Configure specialized logger
logger = logging.getLogger('risk')

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of risk alerts."""
    VAR_BREACH = "var_breach"
    POSITION_LIMIT = "position_limit"
    CORRELATION_LIMIT = "correlation_limit"
    DRAWDOWN_LIMIT = "drawdown_limit"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    VOLATILITY_SPIKE = "volatility_spike"
    CONCENTRATION_RISK = "concentration_risk"
    LIQUIDITY_RISK = "liquidity_risk"

@dataclass
class RiskAlert:
    """Risk alert data structure."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    strategy_name: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

class RiskAlertManager:
    """
    Comprehensive risk monitoring and alerting system.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the risk alert manager."""
        self.config = config
        self.risk_config = config.get('risk_management', {})
        self.alert_config = config.get('alerts', {})

        # Risk thresholds from configuration (ensure all are float)
        self.thresholds = {
            'portfolio_var_limit': self._safe_float(self.risk_config.get('portfolio_var_limit_pct', 0.02)),
            'max_position_size_pct': self._safe_float(self.risk_config.get('max_position_size_pct', 0.15)),
            'max_single_asset_pct': self._safe_float(self.risk_config.get('max_single_asset_pct', 0.20)),
            'correlation_threshold': self._safe_float(self.risk_config.get('correlation_threshold', 0.7)),
            'max_correlated_exposure': self._safe_float(self.risk_config.get('max_correlated_exposure', 0.3)),
            'daily_loss_limit_pct': self._safe_float(self.risk_config.get('daily_loss_limit_pct', 0.05)),
            'max_drawdown_pct': self._safe_float(self.risk_config.get('max_drawdown_pct', 0.10)),
            'volatility_spike_threshold': self._safe_float(self.risk_config.get('volatility_spike_threshold', 0.05)),
            'concentration_limit': self._safe_float(self.risk_config.get('concentration_limit', 0.4))
        }

        # Alert settings
        self.telegram_enabled = self.alert_config.get('telegram_enabled', True)
        self.email_enabled = self.alert_config.get('email_enabled', False)
        self.alert_cooldown_minutes = self.alert_config.get('cooldown_minutes', 15)

        # Alert tracking
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.last_alert_times = defaultdict(lambda: datetime.min)
        self.alert_callbacks = []

        # Telegram configuration
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')

        logger.info("Risk Alert Manager initialized")

    def _safe_float(self, value, default=0.0):
        """Safely convert value to float, handling environment variable placeholders."""
        try:
            if isinstance(value, str) and value.startswith('${'):
                # Environment variable placeholder, use default
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def add_alert_callback(self, callback: Callable[[RiskAlert], None]):
        """Add a callback function to be called when alerts are triggered."""
        self.alert_callbacks.append(callback)

    async def check_var_limits(self, portfolio_var: float, portfolio_cvar: float) -> List[RiskAlert]:
        """Check VaR and CVaR limits."""
        alerts = []

        try:
            # Portfolio VaR check
            if portfolio_var > self.thresholds['portfolio_var_limit']:
                severity = AlertSeverity.CRITICAL if portfolio_var > self.thresholds['portfolio_var_limit'] * 1.5 else AlertSeverity.HIGH

                alert = RiskAlert(
                    alert_type=AlertType.VAR_BREACH,
                    severity=severity,
                    message=f"Portfolio VaR breach: {portfolio_var:.4f} > {self.thresholds['portfolio_var_limit']:.4f}",
                    metric_name="portfolio_var",
                    current_value=portfolio_var,
                    threshold_value=self.thresholds['portfolio_var_limit'],
                    timestamp=datetime.now(),
                    additional_data={
                        'portfolio_cvar': portfolio_cvar,
                        'breach_percentage': ((portfolio_var / self.thresholds['portfolio_var_limit']) - 1) * 100
                    }
                )
                alerts.append(alert)

                logger.warning(f"VaR limit breach detected: {portfolio_var:.4f}")

            return alerts

        except Exception as e:
            logger.error(f"Error checking VaR limits: {str(e)}")
            return []

    async def check_position_limits(self, positions: Dict[str, Any]) -> List[RiskAlert]:
        """Check position size limits."""
        alerts = []

        try:
            portfolio_value = sum(pos.get('value', 0) for pos in positions.values())

            for position_id, position in positions.items():
                position_value = position.get('value', 0)
                position_pct = (position_value / portfolio_value) if portfolio_value > 0 else 0

                # Check individual position size limit
                if position_pct > self.thresholds['max_position_size_pct']:
                    severity = AlertSeverity.CRITICAL if position_pct > self.thresholds['max_position_size_pct'] * 1.2 else AlertSeverity.HIGH

                    alert = RiskAlert(
                        alert_type=AlertType.POSITION_LIMIT,
                        severity=severity,
                        message=f"Position size limit breach: {position_id} = {position_pct:.2%} > {self.thresholds['max_position_size_pct']:.2%}",
                        metric_name="position_size_pct",
                        current_value=position_pct,
                        threshold_value=self.thresholds['max_position_size_pct'],
                        timestamp=datetime.now(),
                        strategy_name=position.get('strategy'),
                        additional_data={
                            'position_id': position_id,
                            'position_value': position_value,
                            'portfolio_value': portfolio_value
                        }
                    )
                    alerts.append(alert)

                    logger.warning(f"Position size limit breach: {position_id} = {position_pct:.2%}")

            return alerts

        except Exception as e:
            logger.error(f"Error checking position limits: {str(e)}")
            return []

    async def check_correlation_limits(self, correlation_matrix: Dict[str, Dict[str, float]],
                                     positions: Dict[str, Any]) -> List[RiskAlert]:
        """Check correlation exposure limits."""
        alerts = []

        try:
            portfolio_value = sum(pos.get('value', 0) for pos in positions.values())

            # Check for high correlation exposure
            for asset1 in correlation_matrix:
                for asset2 in correlation_matrix[asset1]:
                    if asset1 != asset2:
                        correlation = abs(correlation_matrix[asset1][asset2])

                        if correlation > self.thresholds['correlation_threshold']:
                            # Calculate combined exposure
                            exposure1 = positions.get(asset1, {}).get('value', 0) / portfolio_value if portfolio_value > 0 else 0
                            exposure2 = positions.get(asset2, {}).get('value', 0) / portfolio_value if portfolio_value > 0 else 0
                            combined_exposure = exposure1 + exposure2

                            if combined_exposure > self.thresholds['max_correlated_exposure']:
                                severity = AlertSeverity.HIGH if combined_exposure < self.thresholds['max_correlated_exposure'] * 1.2 else AlertSeverity.CRITICAL

                                alert = RiskAlert(
                                    alert_type=AlertType.CORRELATION_LIMIT,
                                    severity=severity,
                                    message=f"High correlation exposure: {asset1}-{asset2} correlation={correlation:.3f}, combined exposure={combined_exposure:.2%}",
                                    metric_name="correlation_exposure",
                                    current_value=combined_exposure,
                                    threshold_value=self.thresholds['max_correlated_exposure'],
                                    timestamp=datetime.now(),
                                    additional_data={
                                        'asset1': asset1,
                                        'asset2': asset2,
                                        'correlation': correlation,
                                        'exposure1': exposure1,
                                        'exposure2': exposure2
                                    }
                                )
                                alerts.append(alert)

                                logger.warning(f"Correlation limit breach: {asset1}-{asset2} = {combined_exposure:.2%}")

            return alerts

        except Exception as e:
            logger.error(f"Error checking correlation limits: {str(e)}")
            return []

    async def check_drawdown_limits(self, current_drawdown: float, max_drawdown: float) -> List[RiskAlert]:
        """Check drawdown limits."""
        alerts = []

        try:
            # Daily drawdown check
            if current_drawdown < -self.thresholds['daily_loss_limit_pct']:
                severity = AlertSeverity.CRITICAL if current_drawdown < -self.thresholds['daily_loss_limit_pct'] * 1.5 else AlertSeverity.HIGH

                alert = RiskAlert(
                    alert_type=AlertType.DAILY_LOSS_LIMIT,
                    severity=severity,
                    message=f"Daily loss limit breach: {current_drawdown:.2%} < -{self.thresholds['daily_loss_limit_pct']:.2%}",
                    metric_name="daily_drawdown",
                    current_value=current_drawdown,
                    threshold_value=-self.thresholds['daily_loss_limit_pct'],
                    timestamp=datetime.now(),
                    additional_data={'max_drawdown': max_drawdown}
                )
                alerts.append(alert)

                logger.warning(f"Daily loss limit breach: {current_drawdown:.2%}")

            # Maximum drawdown check
            if max_drawdown < -self.thresholds['max_drawdown_pct']:
                severity = AlertSeverity.CRITICAL

                alert = RiskAlert(
                    alert_type=AlertType.DRAWDOWN_LIMIT,
                    severity=severity,
                    message=f"Maximum drawdown limit breach: {max_drawdown:.2%} < -{self.thresholds['max_drawdown_pct']:.2%}",
                    metric_name="max_drawdown",
                    current_value=max_drawdown,
                    threshold_value=-self.thresholds['max_drawdown_pct'],
                    timestamp=datetime.now(),
                    additional_data={'current_drawdown': current_drawdown}
                )
                alerts.append(alert)

                logger.critical(f"Maximum drawdown limit breach: {max_drawdown:.2%}")

            return alerts

        except Exception as e:
            logger.error(f"Error checking drawdown limits: {str(e)}")
            return []

    async def check_volatility_spikes(self, current_volatility: float,
                                    historical_volatility: List[float]) -> List[RiskAlert]:
        """Check for volatility spikes."""
        alerts = []

        try:
            if len(historical_volatility) < 10:
                return alerts

            avg_volatility = sum(historical_volatility) / len(historical_volatility)
            volatility_spike = (current_volatility - avg_volatility) / avg_volatility

            if volatility_spike > self.thresholds['volatility_spike_threshold']:
                severity = AlertSeverity.HIGH if volatility_spike < self.thresholds['volatility_spike_threshold'] * 2 else AlertSeverity.CRITICAL

                alert = RiskAlert(
                    alert_type=AlertType.VOLATILITY_SPIKE,
                    severity=severity,
                    message=f"Volatility spike detected: {current_volatility:.4f} vs avg {avg_volatility:.4f} (+{volatility_spike:.1%})",
                    metric_name="volatility_spike",
                    current_value=volatility_spike,
                    threshold_value=self.thresholds['volatility_spike_threshold'],
                    timestamp=datetime.now(),
                    additional_data={
                        'current_volatility': current_volatility,
                        'average_volatility': avg_volatility
                    }
                )
                alerts.append(alert)

                logger.warning(f"Volatility spike detected: {volatility_spike:.1%}")

            return alerts

        except Exception as e:
            logger.error(f"Error checking volatility spikes: {str(e)}")
            return []

    async def send_telegram_alert(self, alert: RiskAlert) -> bool:
        """Send alert via Telegram."""
        try:
            if not self.telegram_enabled or not self.telegram_bot_token or not self.telegram_chat_id:
                return False

            # Format alert message
            severity_emoji = {
                AlertSeverity.INFO: "ℹ️",
                AlertSeverity.WARNING: "⚠️",
                AlertSeverity.HIGH: "🚨",
                AlertSeverity.CRITICAL: "🔥"
            }

            emoji = severity_emoji.get(alert.severity, "⚠️")

            message = f"""
{emoji} *RISK ALERT - {alert.severity.value.upper()}*

*Type*: {alert.alert_type.value.replace('_', ' ').title()}
*Message*: {alert.message}

*Details*:
• Current Value: {alert.current_value:.4f}
• Threshold: {alert.threshold_value:.4f}
• Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

            if alert.strategy_name:
                message += f"• Strategy: {alert.strategy_name}\n"

            if alert.additional_data:
                message += "\n*Additional Info*:\n"
                for key, value in alert.additional_data.items():
                    if isinstance(value, float):
                        message += f"• {key.replace('_', ' ').title()}: {value:.4f}\n"
                    else:
                        message += f"• {key.replace('_', ' ').title()}: {value}\n"

            # Send via Telegram
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10)
                response.raise_for_status()

                logger.info(f"Risk alert sent via Telegram: {alert.alert_type.value}")
                return True

        except Exception as e:
            logger.error(f"Error sending Telegram alert: {str(e)}")
            return False

    async def process_alert(self, alert: RiskAlert) -> bool:
        """Process and send a risk alert."""
        try:
            # Check cooldown period
            alert_key = f"{alert.alert_type.value}_{alert.metric_name}"
            current_time = datetime.now()

            if current_time - self.last_alert_times[alert_key] < timedelta(minutes=self.alert_cooldown_minutes):
                logger.debug(f"Alert {alert_key} in cooldown period, skipping")
                return False

            # Store alert
            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)
            self.last_alert_times[alert_key] = current_time

            # Log alert
            logger.warning(f"Risk Alert: {alert.message}")

            # Send notifications
            telegram_sent = await self.send_telegram_alert(alert)

            # Call registered callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {str(e)}")

            return telegram_sent

        except Exception as e:
            logger.error(f"Error processing alert: {str(e)}")
            return False

    async def monitor_risk_metrics(self, risk_data: Dict[str, Any]) -> List[RiskAlert]:
        """Monitor all risk metrics and generate alerts."""
        try:
            all_alerts = []

            # VaR/CVaR monitoring
            portfolio_var = risk_data.get('portfolio_var', 0)
            portfolio_cvar = risk_data.get('portfolio_cvar', 0)
            var_alerts = await self.check_var_limits(portfolio_var, portfolio_cvar)
            all_alerts.extend(var_alerts)

            # Position limits monitoring
            positions = risk_data.get('positions', {})
            position_alerts = await self.check_position_limits(positions)
            all_alerts.extend(position_alerts)

            # Correlation monitoring
            correlation_matrix = risk_data.get('correlation_matrix', {})
            correlation_alerts = await self.check_correlation_limits(correlation_matrix, positions)
            all_alerts.extend(correlation_alerts)

            # Drawdown monitoring
            current_drawdown = risk_data.get('current_drawdown', 0)
            max_drawdown = risk_data.get('max_drawdown', 0)
            drawdown_alerts = await self.check_drawdown_limits(current_drawdown, max_drawdown)
            all_alerts.extend(drawdown_alerts)

            # Volatility monitoring
            current_volatility = risk_data.get('current_volatility', 0)
            historical_volatility = risk_data.get('historical_volatility', [])
            volatility_alerts = await self.check_volatility_spikes(current_volatility, historical_volatility)
            all_alerts.extend(volatility_alerts)

            # Process all alerts
            for alert in all_alerts:
                await self.process_alert(alert)

            return all_alerts

        except Exception as e:
            logger.error(f"Error monitoring risk metrics: {str(e)}")
            return []

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alerts and alert history."""
        try:
            current_time = datetime.now()

            # Active alerts (within last hour)
            active_alerts = [alert for alert in self.alert_history
                           if (current_time - alert.timestamp).total_seconds() < 3600]

            # Alert counts by severity
            severity_counts = defaultdict(int)
            for alert in active_alerts:
                severity_counts[alert.severity.value] += 1

            # Alert counts by type
            type_counts = defaultdict(int)
            for alert in active_alerts:
                type_counts[alert.alert_type.value] += 1

            return {
                'timestamp': current_time.isoformat(),
                'active_alerts_count': len(active_alerts),
                'total_alerts_today': len([a for a in self.alert_history
                                         if (current_time - a.timestamp).days == 0]),
                'severity_breakdown': dict(severity_counts),
                'type_breakdown': dict(type_counts),
                'last_alert_time': self.alert_history[-1].timestamp.isoformat() if self.alert_history else None,
                'alert_history_size': len(self.alert_history)
            }

        except Exception as e:
            logger.error(f"Error getting alert summary: {str(e)}")
            return {}
