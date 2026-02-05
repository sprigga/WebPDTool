# Bug Fix: Circular Import Error on Application Startup

**Date:** 2026-01-30
**Severity:** High (Application fails to start)
**Status:** Fixed

## Problem Description

When starting the FastAPI backend application, the following error occurred:

```
ImportError: cannot import name 'settings' from 'app.config'
(/home/ubuntu/python_code/WebPDTool/backend/app/config/__init__.py)
```

### Root Cause

The issue was caused by a **Python module naming collision** between two items with the same name:

1. **`backend/app/config.py`** - A module file containing:
   - `Settings` class (Pydantic settings configuration)
   - Global `settings` instance

2. **`backend/app/config/`** - A directory/package containing:
   - `__init__.py`
   - `instruments.py` (instrument configurations)
   - `MEASUREMENT_TEMPLATES`, `AVAILABLE_INSTRUMENTS`

### How Python's Module Resolution Works

When executing `from app.config import settings`, Python's import system:

1. First looks for `app/config/__init__.py` (found - the directory package)
2. The package's `__init__.py` only exported `AVAILABLE_INSTRUMENTS` and `MEASUREMENT_TEMPLATES`
3. The `config.py` file was never considered because the directory takes precedence

```
Import statement: from app.config import settings
                      ↓
              Resolves to: app/config/ (directory package)
                      ↓
          __init__.py exports: AVAILABLE_INSTRUMENTS, MEASUREMENT_TEMPLATES
                      ↓
              Result: ImportError - 'settings' not found
```

### Affected Files

Multiple files were importing `settings` from `app.config`:
- `backend/app/main.py`
- `backend/app/core/database.py`
- `backend/app/core/security.py`
- `backend/app/api/auth.py`
- `backend/scripts/test_redis_logging.py`

## Solution

Updated `backend/app/config/__init__.py` to load and export the `settings` object from the sibling `config.py` file using `importlib.util.spec_from_file_location()`.

### Implementation

**File:** `backend/app/config/__init__.py`

```python
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
```

### Why This Approach Works

1. **`importlib.util.spec_from_file_location()`** - Loads a Python module from a specific file path, bypassing normal module resolution
2. **Avoids circular import** - Directly loads `config.py` without triggering the `app.config` package import
3. **Preserves backward compatibility** - All existing imports `from app.config import settings` work without modification
4. **Clean isolation** - Uses a temporary module name (`_app_config_module`) that's deleted after use

## Verification

After the fix, the following commands succeed:

```bash
cd backend

# Test settings import
python -c "from app.config import settings; print(f'{settings.APP_NAME} v{settings.APP_VERSION}')"
# Output: WebPDTool v0.1.0

# Test full app import
python -c "from app.main import app; print(f'{app.title}')"
# Output: WebPDTool
```

## Alternative Solutions Considered

### 1. Rename `config.py` to `settings.py`
**Pros:** Clean solution, no import tricks needed
**Cons:** Would require updating all imports across the codebase (6+ files)

### 2. Rename `config/` directory to `configurations/`
**Pros:** Clear naming, eliminates collision
**Cons:** Would require updating all imports for instrument configs

### 3. Use relative import: `from ..config import settings`
**Pros:** More explicit
**Cons:** Still causes circular import because Python resolves `..config` to the package

### 4. Selected Solution: Load via `importlib.util`
**Pros:** Minimal code change, preserves backward compatibility
**Cons:** Slightly more complex `__init__.py` (but well-documented)

## Lessons Learned

1. **Avoid naming collisions** between `.py` files and directories with the same name at the same level
2. **Python module resolution** prefers directories (packages) over single-file modules
3. **`importlib.util.spec_from_file_location()`** is a useful tool for loading modules by file path when normal import won't work
4. When refactoring, check for potential naming conflicts before creating new directories or files

## References

- Python Module Resolution: https://docs.python.org/3/reference/import.html
- `importlib.util.spec_from_file_location()`: https://docs.python.org/3/library/importlib.html#importlib.util.spec_from_file_location
