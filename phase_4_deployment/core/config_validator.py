#!/usr/bin/env python3
"""
Configuration Validator for Q5 Trading System

This module validates the configuration file to ensure all required settings are present
and have valid values.
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
import re

logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""
    pass

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration file.
    
    Args:
        config: The configuration dictionary
        
    Returns:
        bool: True if the configuration is valid
        
    Raises:
        ConfigValidationError: If the configuration is invalid
    """
    try:
        # Validate required top-level sections
        required_sections = [
            "mode", "solana", "wallet", "strategies", "risk", 
            "execution", "monitoring", "apis", "logging"
        ]
        
        for section in required_sections:
            if section not in config:
                raise ConfigValidationError(f"Missing required section: {section}")
        
        # Validate mode section
        validate_mode_section(config["mode"])
        
        # Validate solana section
        validate_solana_section(config["solana"])
        
        # Validate wallet section
        validate_wallet_section(config["wallet"])
        
        # Validate strategies section
        validate_strategies_section(config["strategies"])
        
        # Validate risk section
        validate_risk_section(config["risk"])
        
        # Validate execution section
        validate_execution_section(config["execution"])
        
        # Validate monitoring section
        validate_monitoring_section(config["monitoring"])
        
        # Validate APIs section
        validate_apis_section(config["apis"])
        
        # Validate logging section
        validate_logging_section(config["logging"])
        
        # Validate Carbon Core section if present
        if "carbon_core" in config:
            validate_carbon_core_section(config["carbon_core"])
        
        # Validate deployment section if present
        if "deployment" in config:
            validate_deployment_section(config["deployment"])
        
        logger.info("Configuration validation successful")
        return True
        
    except ConfigValidationError as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during configuration validation: {str(e)}")
        raise ConfigValidationError(f"Unexpected error: {str(e)}")

def validate_mode_section(mode: Dict[str, Any]) -> None:
    """Validate the mode section."""
    required_fields = ["live_trading", "paper_trading", "backtesting", "simulation"]
    
    for field in required_fields:
        if field not in mode:
            raise ConfigValidationError(f"Missing required field in mode section: {field}")
        
        if not isinstance(mode[field], bool):
            raise ConfigValidationError(f"Field in mode section must be boolean: {field}")
    
    # Check that only one mode is enabled
    enabled_modes = [mode for mode, enabled in mode.items() if enabled]
    if len(enabled_modes) > 1:
        raise ConfigValidationError(f"Only one mode can be enabled at a time. Enabled modes: {enabled_modes}")

def validate_solana_section(solana: Dict[str, Any]) -> None:
    """Validate the solana section."""
    required_fields = ["rpc_url", "fallback_rpc_url", "commitment", "max_retries", "retry_delay", "tx_timeout"]
    
    for field in required_fields:
        if field not in solana:
            raise ConfigValidationError(f"Missing required field in solana section: {field}")
    
    # Validate numeric fields
    numeric_fields = ["max_retries", "retry_delay", "tx_timeout"]
    for field in numeric_fields:
        if not isinstance(solana[field], (int, float)) or solana[field] <= 0:
            raise ConfigValidationError(f"Field in solana section must be a positive number: {field}")
    
    # Validate commitment level
    valid_commitments = ["processed", "confirmed", "finalized"]
    if solana["commitment"] not in valid_commitments:
        raise ConfigValidationError(f"Invalid commitment level: {solana['commitment']}. Must be one of {valid_commitments}")

def validate_wallet_section(wallet: Dict[str, Any]) -> None:
    """Validate the wallet section."""
    required_fields = ["address", "state_sync_interval", "position_update_interval", "max_positions"]
    
    for field in required_fields:
        if field not in wallet:
            raise ConfigValidationError(f"Missing required field in wallet section: {field}")
    
    # Validate numeric fields
    numeric_fields = ["state_sync_interval", "position_update_interval", "max_positions"]
    for field in numeric_fields:
        if not isinstance(wallet[field], (int, float)) or wallet[field] <= 0:
            raise ConfigValidationError(f"Field in wallet section must be a positive number: {field}")

def validate_strategies_section(strategies: List[Dict[str, Any]]) -> None:
    """Validate the strategies section."""
    if not isinstance(strategies, list):
        raise ConfigValidationError("Strategies section must be a list")
    
    if len(strategies) == 0:
        raise ConfigValidationError("At least one strategy must be defined")
    
    for i, strategy in enumerate(strategies):
        if "name" not in strategy:
            raise ConfigValidationError(f"Strategy at index {i} is missing a name")
        
        if "enabled" not in strategy:
            raise ConfigValidationError(f"Strategy '{strategy['name']}' is missing the enabled field")
        
        if not isinstance(strategy["enabled"], bool):
            raise ConfigValidationError(f"Strategy '{strategy['name']}' enabled field must be a boolean")
        
        if "params" not in strategy:
            raise ConfigValidationError(f"Strategy '{strategy['name']}' is missing the params field")
        
        if not isinstance(strategy["params"], dict):
            raise ConfigValidationError(f"Strategy '{strategy['name']}' params field must be a dictionary")

def validate_risk_section(risk: Dict[str, Any]) -> None:
    """Validate the risk section."""
    required_fields = [
        "max_position_size_usd", "max_position_size_pct", "stop_loss_pct", 
        "take_profit_pct", "max_drawdown_pct", "daily_loss_limit_usd"
    ]
    
    for field in required_fields:
        if field not in risk:
            raise ConfigValidationError(f"Missing required field in risk section: {field}")
    
    # Validate numeric fields
    numeric_fields = required_fields
    for field in numeric_fields:
        if not isinstance(risk[field], (int, float)) or risk[field] <= 0:
            raise ConfigValidationError(f"Field in risk section must be a positive number: {field}")
    
    # Validate percentage fields
    percentage_fields = ["max_position_size_pct", "stop_loss_pct", "take_profit_pct", "max_drawdown_pct"]
    for field in percentage_fields:
        if risk[field] > 1.0:
            raise ConfigValidationError(f"Percentage field in risk section should be between 0 and 1: {field}")

def validate_execution_section(execution: Dict[str, Any]) -> None:
    """Validate the execution section."""
    required_fields = [
        "slippage_tolerance", "max_spread_pct", "min_liquidity_usd", 
        "order_type", "retry_failed_orders", "max_order_retries"
    ]
    
    for field in required_fields:
        if field not in execution:
            raise ConfigValidationError(f"Missing required field in execution section: {field}")
    
    # Validate numeric fields
    numeric_fields = ["slippage_tolerance", "max_spread_pct", "min_liquidity_usd", "max_order_retries"]
    for field in numeric_fields:
        if not isinstance(execution[field], (int, float)) or execution[field] <= 0:
            raise ConfigValidationError(f"Field in execution section must be a positive number: {field}")
    
    # Validate percentage fields
    percentage_fields = ["slippage_tolerance", "max_spread_pct"]
    for field in percentage_fields:
        if execution[field] > 1.0:
            raise ConfigValidationError(f"Percentage field in execution section should be between 0 and 1: {field}")
    
    # Validate order type
    valid_order_types = ["market", "limit"]
    if execution["order_type"] not in valid_order_types:
        raise ConfigValidationError(f"Invalid order type: {execution['order_type']}. Must be one of {valid_order_types}")
    
    # Validate boolean fields
    if not isinstance(execution["retry_failed_orders"], bool):
        raise ConfigValidationError("retry_failed_orders field in execution section must be a boolean")

def validate_monitoring_section(monitoring: Dict[str, Any]) -> None:
    """Validate the monitoring section."""
    required_fields = ["enabled", "update_interval", "telegram_alerts", "email_alerts", "log_level"]
    
    for field in required_fields:
        if field not in monitoring:
            raise ConfigValidationError(f"Missing required field in monitoring section: {field}")
    
    # Validate numeric fields
    numeric_fields = ["update_interval", "performance_report_interval"]
    for field in numeric_fields:
        if field in monitoring and (not isinstance(monitoring[field], (int, float)) or monitoring[field] <= 0):
            raise ConfigValidationError(f"Field in monitoring section must be a positive number: {field}")
    
    # Validate boolean fields
    boolean_fields = ["enabled", "telegram_alerts", "email_alerts"]
    for field in boolean_fields:
        if not isinstance(monitoring[field], bool):
            raise ConfigValidationError(f"Field in monitoring section must be a boolean: {field}")
    
    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if monitoring["log_level"] not in valid_log_levels:
        raise ConfigValidationError(f"Invalid log level: {monitoring['log_level']}. Must be one of {valid_log_levels}")

def validate_apis_section(apis: Dict[str, Any]) -> None:
    """Validate the APIs section."""
    required_apis = ["helius", "birdeye"]
    
    for api in required_apis:
        if api not in apis:
            raise ConfigValidationError(f"Missing required API configuration: {api}")
        
        if "enabled" not in apis[api]:
            raise ConfigValidationError(f"Missing enabled field in {api} API configuration")
        
        if not isinstance(apis[api]["enabled"], bool):
            raise ConfigValidationError(f"Enabled field in {api} API configuration must be a boolean")
        
        if apis[api]["enabled"]:
            if "api_key" not in apis[api]:
                raise ConfigValidationError(f"Missing api_key field in {api} API configuration")
            
            if "endpoint" not in apis[api]:
                raise ConfigValidationError(f"Missing endpoint field in {api} API configuration")

def validate_logging_section(logging_config: Dict[str, Any]) -> None:
    """Validate the logging section."""
    required_fields = ["level", "format"]
    
    for field in required_fields:
        if field not in logging_config:
            raise ConfigValidationError(f"Missing required field in logging section: {field}")
    
    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if logging_config["level"] not in valid_log_levels:
        raise ConfigValidationError(f"Invalid log level: {logging_config['level']}. Must be one of {valid_log_levels}")

def validate_carbon_core_section(carbon_core: Dict[str, Any]) -> None:
    """Validate the Carbon Core section."""
    required_fields = ["enabled", "binary_path", "log_level", "max_memory_mb", "worker_threads"]
    
    for field in required_fields:
        if field not in carbon_core:
            raise ConfigValidationError(f"Missing required field in carbon_core section: {field}")
    
    # Validate boolean fields
    if not isinstance(carbon_core["enabled"], bool):
        raise ConfigValidationError("enabled field in carbon_core section must be a boolean")
    
    # Validate numeric fields
    numeric_fields = ["max_memory_mb", "worker_threads", "update_interval_ms"]
    for field in numeric_fields:
        if field in carbon_core and (not isinstance(carbon_core[field], (int, float)) or carbon_core[field] <= 0):
            raise ConfigValidationError(f"Field in carbon_core section must be a positive number: {field}")
    
    # Validate subsections
    subsections = ["market_microstructure", "statistical_signal_processing", "rl_execution", "communication"]
    for subsection in subsections:
        if subsection in carbon_core:
            if "enabled" not in carbon_core[subsection]:
                raise ConfigValidationError(f"Missing enabled field in carbon_core.{subsection} section")
            
            if not isinstance(carbon_core[subsection]["enabled"], bool):
                raise ConfigValidationError(f"enabled field in carbon_core.{subsection} section must be a boolean")

def validate_deployment_section(deployment: Dict[str, Any]) -> None:
    """Validate the deployment section."""
    required_sections = ["docker", "streamlit"]
    
    for section in required_sections:
        if section not in deployment:
            raise ConfigValidationError(f"Missing required section in deployment: {section}")
    
    # Validate docker section
    docker_required_fields = ["image", "container_name", "restart_policy"]
    for field in docker_required_fields:
        if field not in deployment["docker"]:
            raise ConfigValidationError(f"Missing required field in deployment.docker section: {field}")
    
    # Validate streamlit section
    streamlit_required_fields = ["port", "headless"]
    for field in streamlit_required_fields:
        if field not in deployment["streamlit"]:
            raise ConfigValidationError(f"Missing required field in deployment.streamlit section: {field}")
    
    # Validate numeric fields
    if not isinstance(deployment["streamlit"]["port"], int) or deployment["streamlit"]["port"] <= 0:
        raise ConfigValidationError("port field in deployment.streamlit section must be a positive integer")
    
    # Validate boolean fields
    if not isinstance(deployment["streamlit"]["headless"], bool):
        raise ConfigValidationError("headless field in deployment.streamlit section must be a boolean")

def load_and_validate_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate the configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict[str, Any]: The validated configuration dictionary
        
    Raises:
        ConfigValidationError: If the configuration is invalid
    """
    try:
        # Check if the file exists
        if not os.path.exists(config_path):
            raise ConfigValidationError(f"Configuration file not found: {config_path}")
        
        # Load the configuration file
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate the configuration
        validate_config(config)
        
        return config
        
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"Error parsing YAML configuration: {str(e)}")
    except Exception as e:
        if isinstance(e, ConfigValidationError):
            raise
        else:
            raise ConfigValidationError(f"Error loading configuration: {str(e)}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Load and validate the configuration
    try:
        config = load_and_validate_config("config.yaml")
        print("Configuration validation successful")
    except ConfigValidationError as e:
        print(f"Configuration validation failed: {str(e)}")
        exit(1)
