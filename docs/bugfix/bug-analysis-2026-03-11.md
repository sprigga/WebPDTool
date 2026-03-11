# Bug Analysis & Fix Report

**Date**: 2026-03-11
**Analysis Method**: Systematic test execution and root cause investigation
**Status**: ✅ Fixed

## Summary

Running `pytest` revealed 7 import errors affecting 7 test files. All errors are import-related issues, not logic bugs in the code itself.

---

## Bug #1: Missing `paramiko` Dependency

### Error
```
ModuleNotFoundError: No module named 'paramiko'
```

### Root Cause
Package `paramiko>=4.0.0` is declared in `backend/pyproject.toml:23` but not installed in the current Python environment.

### Impact
6 test files cannot be imported due to indirect dependency chain:
```
test file → instrument_executor.py → instruments/__init__.py → l6mpu_ssh.py → paramiko
```

### Affected Test Files
1. `tests/test_high_priority_instruments.py`
2. `tests/test_instrument_drivers.py`
3. `tests/test_instruments/test_l6mpu.py`
4. `tests/test_instruments/test_peak_and_smcv.py`
5. `tests/test_instruments_pytest_style.py`
6. `tests/test_medium_priority_instruments.py`

### Fix Applied

The original `.venv` at `backend/.venv` was owned by root with a broken symlink:
```
backend/.venv/bin/python → /usr/local/bin/python3  # broken: target no longer exists
```

Since `uv venv --clear` requires write permission to the root-owned `.venv`, a fresh virtual environment was created at `/home/ubuntu/.venv-webpdtool`:

```bash
UV_PYTHON=python3.11 uv venv /home/ubuntu/.venv-webpdtool
uv pip install --python /home/ubuntu/.venv-webpdtool/bin/python3 -e .
# Also installed test dependencies:
uv pip install --python /home/ubuntu/.venv-webpdtool/bin/python3 pytest pytest-asyncio pytest-cov httpx asyncmy
```

### Permanent Fix (requires sudo)
```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/python_code/WebPDTool/backend/.venv
cd backend
UV_PYTHON=python3.11 uv venv --clear
uv pip install -e ".[dev]"
```

### Verification
```bash
# Use alternate venv until .venv ownership is fixed
PYTHONPATH=backend /home/ubuntu/.venv-webpdtool/bin/python3 -m pytest tests/test_high_priority_instruments.py -v
```

**Result:** `ModuleNotFoundError` is gone. Tests now collect and run (any remaining failures are unrelated async mode issues, not import errors).

---

## Bug #2: Invalid Import Names in test_refactoring.py

### Error
```
ImportError: cannot import name 'LOWER_LIMIT_TYPE' from 'app.measurements.base'
```

### Root Cause
Test file `tests/test_refactoring.py` imports non-existent constants with `_TYPE` suffix that do not match actual exports from `backend/app/measurements/base.py`. This is a refactoring artifact — the API evolved to use class objects but the test file was not updated.

### Code Evidence

**Invalid Imports (tests/test_refactoring.py:9-22)**:
```python
from app.measurements.base import (
    BaseMeasurement,
    MeasurementResult,
    LOWER_LIMIT_TYPE,          # ❌ Does not exist
    UPPER_LIMIT_TYPE,          # ❌ Does not exist
    BOTH_LIMIT_TYPE,           # ❌ Does not exist
    EQUALITY_LIMIT_TYPE,       # ❌ Does not exist
    PARTIAL_LIMIT_TYPE,        # ❌ Does not exist
    INEQUALITY_LIMIT_TYPE,     # ❌ Does not exist
    NONE_LIMIT_TYPE,           # ❌ Does not exist
    INTEGER_VALUE_TYPE,         # ❌ Does not exist
    FLOAT_VALUE_TYPE,           # ❌ Does not exist
    STRING_VALUE_TYPE           # ❌ Does not exist
)
```

**Actual Exports (backend/app/measurements/base.py)**:
```python
# Limit type classes (lines 31-63)
class LOWER_LIMIT(LimitType):
class UPPER_LIMIT(LimitType):
class BOTH_LIMIT(LimitType):
class EQUALITY_LIMIT(LimitType):
class PARTIAL_LIMIT(LimitType):
class INEQUALITY_LIMIT(LimitType):
class NONE_LIMIT(LimitType)

# Value type classes (lines 88-110)
class StringType(ValueType):
class IntegerType(ValueType):
class FloatType(ValueType):
```

### Fix Applied
Updated `tests/test_refactoring.py:9-22` to use correct class names. Old names are preserved as comments for traceability:

```python
from app.measurements.base import (
    BaseMeasurement,
    MeasurementResult,
    # Fixed: _TYPE suffix constants do not exist; use actual class names
    # LOWER_LIMIT_TYPE,    → LOWER_LIMIT
    # UPPER_LIMIT_TYPE,    → UPPER_LIMIT
    # BOTH_LIMIT_TYPE,     → BOTH_LIMIT
    # EQUALITY_LIMIT_TYPE, → EQUALITY_LIMIT
    # PARTIAL_LIMIT_TYPE,  → PARTIAL_LIMIT
    # INEQUALITY_LIMIT_TYPE, → INEQUALITY_LIMIT
    # NONE_LIMIT_TYPE,     → NONE_LIMIT
    # INTEGER_VALUE_TYPE,  → IntegerType
    # FLOAT_VALUE_TYPE,    → FloatType
    # STRING_VALUE_TYPE    → StringType
    LOWER_LIMIT,
    UPPER_LIMIT,
    BOTH_LIMIT,
    EQUALITY_LIMIT,
    PARTIAL_LIMIT,
    INEQUALITY_LIMIT,
    NONE_LIMIT,
    IntegerType,
    FloatType,
    StringType
)
```

### Verification
```bash
PYTHONPATH=backend /home/ubuntu/.venv-webpdtool/bin/python3 -m pytest tests/test_refactoring.py -v
```

**Result:** 9 passed, 1 warning (warning is unrelated: pytest collection warning for `TestMeasurement` class with `__init__`).

---

## Additional Findings

### Warnings (Not Blocking)
1. **SQLAlchemy 2.0 Deprecation**: `backend/app/core/database.py:22` uses deprecated `declarative_base()`
2. **Pytest Collection Warning**: `tests/test_refactoring.py:37` - `TestMeasurement` class has `__init__` constructor, pytest cannot collect it as a test class

These do not prevent test execution but should be addressed for code quality.

---

## Remaining Action Items

1. ✅ Install missing `paramiko` dependency
2. ✅ Fix invalid imports in `tests/test_refactoring.py`
3. ⬜ Fix root-owned `.venv` (requires sudo): `sudo chown -R ubuntu:ubuntu backend/.venv`
4. ⬜ Address SQLAlchemy deprecation warning in `backend/app/core/database.py:22`
5. ⬜ Fix pytest collection warning in `tests/test_measurements_refactoring.py`
