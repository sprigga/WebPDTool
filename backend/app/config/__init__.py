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
from pathlib import Path

# 使用 pathlib 計算 config.py 的路徑，與 config.py 中的 .env 路徑計算方式一致
# __file__ = /path/to/backend/app/config/__init__.py
# .parent = /path/to/backend/app/config
# .parent.parent = /path/to/backend/app
# / "config.py" = /path/to/backend/app/config.py
config_file_path = Path(__file__).resolve().parent.parent / "config.py"

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
