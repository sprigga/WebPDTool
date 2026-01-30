"""
Configuration Module

Contains application configuration constants including instrument
definitions and measurement templates.

Note: There are two 'config' items at app level:
- app/config.py: Contains the Settings class and global settings instance
- app/config/: This package containing instrument configurations

When importing 'app.config', Python prefers this directory (package) over config.py.
To access settings from the config.py file, we load it directly using __import__.
"""

# ✅ Fix: Import settings from the sibling config.py file (not this config/ package)
# Use __import__ to load app.config.py as a module and extract settings
import sys
import os

# Add the app directory to the path if not already there
app_dir = os.path.dirname(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Load the config.py module file directly
config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')
# Import the module from the file path
import importlib.util
spec = importlib.util.spec_from_file_location("_app_config_module", config_file_path)
_app_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_app_config_module)
settings = _app_config_module.settings

# Clean up
del spec, _app_config_module

from .instruments import AVAILABLE_INSTRUMENTS, MEASUREMENT_TEMPLATES

__all__ = ["settings", "AVAILABLE_INSTRUMENTS", "MEASUREMENT_TEMPLATES"]
