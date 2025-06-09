#!/usr/bin/env python3
"""
Simple Configuration Loader

This module provides a simple function for loading configuration files.
"""

import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("config_loader")

def load_config(config_path):
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        if config is None:
            logger.warning(f"Empty configuration file: {config_path}")
            return {}
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {str(e)}")
        return {}
