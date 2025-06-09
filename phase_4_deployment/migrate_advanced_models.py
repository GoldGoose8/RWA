#!/usr/bin/env python3
"""
Migrate Advanced Models Component

This script migrates the advanced models component from the old dashboard to the new unified dashboard.
"""

import os
import sys
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    # Get the path to the project root
    project_root = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
    
    # Get the path to the old advanced models component
    old_component_path = os.path.join(
        project_root,
        'gui_dashboard',
        'components',
        'advanced_models.py'
    )
    
    # Get the path to the new advanced models component
    new_component_path = os.path.join(
        project_root,
        'unified_dashboard',
        'components',
        'advanced_models.py'
    )
    
    # Check if the old component exists
    if not os.path.exists(old_component_path):
        logger.error(f"Old component not found: {old_component_path}")
        return 1
    
    # Create the new component directory if it doesn't exist
    os.makedirs(os.path.dirname(new_component_path), exist_ok=True)
    
    # Read the old component
    with open(old_component_path, 'r') as f:
        content = f.read()
    
    # Update imports to use the unified dashboard's data service
    content = content.replace(
        "from core.carbon_core_client import CarbonCoreClient",
        "# Import data service\nimport sys\nimport os\n\n# Add the parent directory to the Python path\nparent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nif parent_dir not in sys.path:\n    sys.path.append(parent_dir)\n\nfrom data_service import data_service"
    )
    
    # Update the render_advanced_models function to use the unified dashboard's data service
    content = content.replace(
        "def render_advanced_models(data: Dict[str, Any]):",
        "def render_advanced_models(data: Dict[str, Any]):\n    \"\"\"\n    Render advanced models section showing Market Microstructure,\n    Statistical Signal Processing, and RL Execution metrics.\n\n    Args:\n        data: Dashboard data from the unified dashboard\n    \"\"\""
    )
    
    # Write the new component
    with open(new_component_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Migrated advanced models component to: {new_component_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
