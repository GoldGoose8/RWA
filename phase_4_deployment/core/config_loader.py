#!/usr/bin/env python3
"""
Configuration Loader for Q5 Trading System

This module loads the configuration file, applies environment variable overrides,
and validates the configuration.
"""

import os
import re
import yaml
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from .config_validator import load_and_validate_config, ConfigValidationError

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Configuration loader for Q5 Trading System."""
    
    def __init__(self, config_path: str = "config.yaml", env_file: str = ".env"):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the configuration file
            env_file: Path to the environment file
        """
        self.config_path = config_path
        self.env_file = env_file
        self.config = None
        
    def load(self) -> Dict[str, Any]:
        """
        Load the configuration file, apply environment variable overrides,
        and validate the configuration.
        
        Returns:
            Dict[str, Any]: The validated configuration dictionary
            
        Raises:
            ConfigValidationError: If the configuration is invalid
        """
        # Load environment variables
        self._load_env_vars()
        
        # Load and validate the configuration
        self.config = load_and_validate_config(self.config_path)
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate the configuration again after applying overrides
        try:
            from .config_validator import validate_config
            validate_config(self.config)
        except ConfigValidationError as e:
            logger.error(f"Configuration validation failed after applying environment overrides: {str(e)}")
            raise
        
        return self.config
    
    def _load_env_vars(self) -> None:
        """Load environment variables from the .env file."""
        try:
            if os.path.exists(self.env_file):
                load_dotenv(self.env_file)
                logger.info(f"Loaded environment variables from {self.env_file}")
            else:
                logger.warning(f"Environment file not found: {self.env_file}")
        except Exception as e:
            logger.error(f"Error loading environment variables: {str(e)}")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to the configuration."""
        if not self.config:
            return
        
        # Process the configuration recursively
        self._process_config_dict(self.config)
    
    def _process_config_dict(self, config_dict: Dict[str, Any], prefix: str = "") -> None:
        """
        Process a configuration dictionary recursively.
        
        Args:
            config_dict: The configuration dictionary to process
            prefix: The prefix for environment variable names
        """
        for key, value in config_dict.items():
            if isinstance(value, dict):
                # Process nested dictionaries
                new_prefix = f"{prefix}_{key}" if prefix else key
                self._process_config_dict(value, new_prefix)
            elif isinstance(value, list):
                # Process lists
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        new_prefix = f"{prefix}_{key}_{i}" if prefix else f"{key}_{i}"
                        self._process_config_dict(item, new_prefix)
            elif isinstance(value, str):
                # Process string values for environment variable references
                config_dict[key] = self._replace_env_vars(value)
    
    def _replace_env_vars(self, value: str) -> str:
        """
        Replace environment variable references in a string.
        
        Args:
            value: The string value to process
            
        Returns:
            str: The processed string with environment variables replaced
        """
        if not isinstance(value, str):
            return value
        
        # Find all ${ENV_VAR} patterns
        pattern = r'\${([A-Za-z0-9_]+)}'
        matches = re.findall(pattern, value)
        
        # Replace each match with the corresponding environment variable
        result = value
        for match in matches:
            env_value = os.environ.get(match)
            if env_value is not None:
                result = result.replace(f"${{{match}}}", env_value)
            else:
                logger.warning(f"Environment variable not found: {match}")
        
        return result
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the loaded configuration.
        
        Returns:
            Optional[Dict[str, Any]]: The loaded configuration dictionary, or None if not loaded
        """
        return self.config
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a value from the configuration using a dot-separated key path.
        
        Args:
            key_path: The dot-separated key path (e.g., "solana.rpc_url")
            default: The default value to return if the key is not found
            
        Returns:
            Any: The value at the specified key path, or the default value if not found
        """
        if not self.config:
            return default
        
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

def load_config(config_path: str = "config.yaml", env_file: str = ".env") -> Dict[str, Any]:
    """
    Load the configuration file, apply environment variable overrides,
    and validate the configuration.
    
    Args:
        config_path: Path to the configuration file
        env_file: Path to the environment file
        
    Returns:
        Dict[str, Any]: The validated configuration dictionary
        
    Raises:
        ConfigValidationError: If the configuration is invalid
    """
    loader = ConfigLoader(config_path, env_file)
    return loader.load()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Load the configuration
    try:
        config = load_config()
        print("Configuration loaded successfully")
        
        # Print some configuration values
        print(f"Mode: {config['mode']}")
        print(f"Solana RPC URL: {config['solana']['rpc_url']}")
        print(f"Wallet Address: {config['wallet']['address']}")
    except ConfigValidationError as e:
        print(f"Configuration validation failed: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        exit(1)
