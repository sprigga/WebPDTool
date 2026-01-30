# Low Priority Issues

**Code quality improvements** - Minor issues that don't affect functionality but improve code quality.

---

## 1. Print Statement for Debugging

**File**: `backend/app/api/testplan/mutations.py`
**Lines**: 117-119
**Severity**: 🔵 Low

```python
except Exception as e:
    db.rollback()
    import traceback
    error_traceback = traceback.format_exc()
    print(f"Upload error traceback:\n{error_traceback}")  # ← Should use logger
    raise HTTPException(status_code=500, detail=f"Error uploading test plan: {str(e)}")
```

**Issue**: Using `print()` for production error logging. Print statements:
- Don't respect log levels
- May not appear in production logs
- Can't be configured/routed like logger output

**Fix**:
```python
import logging

logger = logging.getLogger(__name__)

# In exception handler:
except Exception as e:
    db.rollback()
    logger.error(f"Upload error: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail=f"Error uploading test plan: {str(e)}")
```

---

## 2. Hardcoded Instrument List

**File**: `backend/app/api/measurements.py`
**Lines**: 328-353
**Severity**: 🔵 Low

```python
@router.get("/instruments/available")
async def get_available_instruments():
    """Get list of all available instruments based on PDTool4 configuration"""
    try:
        available_instruments = {
            "power_supplies": [
                {"id": "DAQ973A", "type": "DAQ973A", "description": "Keysight DAQ973A"},
                {"id": "MODEL2303", "type": "MODEL2303", "description": "Keysight Model 2303"},
                # ... 20+ hardcoded entries
            ],
            "multimeters": [...],
            "communication": [...],
            "rf_analyzers": [...]
        }
        return available_instruments
```

**Issue**: Large hardcoded dictionary that should be loaded from configuration for:
- Easier maintenance
- Runtime customization
- Environment-specific configs

**Fix**:
```python
# config.py or instruments.yaml:
AVAILABLE_INSTRUMENTS = {
    "power_supplies": [...],
    "multimeters": [...],
    ...
}

# measurements.py:
from app.config import AVAILABLE_INSTRUMENTS

@router.get("/instruments/available")
async def get_available_instruments():
    return AVAILABLE_INSTRUMENTS
```

---

## 3. Hardcoded Measurement Templates

**File**: `backend/app/api/measurements.py`
**Lines**: 371-457
**Severity**: 🔵 Low

```python
@router.get("/measurement-templates")
async def get_measurement_templates():
    """Get measurement templates based on PDTool4's measurement module patterns"""
    templates = {
        "PowerSet": {
            "DAQ973A": {
                "required": ["Instrument", "Channel", "Item"],
                "optional": ["Volt", "Curr", "Sense", "Range"],
                "example": {...}
            },
            # ... 200+ lines of hardcoded templates
        }
    }
```

**Issue**: 87 lines of hardcoded template data that should be in:
- Configuration file (YAML/JSON)
- Database table
- Separate constants module

**Fix**: Extract to `app/config/instrument_templates.py` or YAML file.

---

## 4. Inconsistent Docstring Return Types

**Files**: Multiple
**Severity**: 🔵 Low

Different docstring return formats across endpoints:

| Format | Example |
|--------|---------|
| No type | `Returns:\n    Stop status` |
| With type | `Returns:\n    Created test plan item` |
| Descriptive | `Returns:\n    Control operation result` |
| Generic | `Returns:\n    Updated test session` |

**Issue**: Inconsistent docstring format makes API documentation less clear.

**Recommended format**:
```python
"""
Create a new test session

Args:
    session_data: Test session creation data
    db: Database session

Returns:
    TestSession: The created test session with id, serial_number, etc.

Raises:
    404: If station not found
"""
```

---

## 5. Empty/Minimal `__init__.py` Files

**Files**:
- `backend/app/api/__init__.py` (1 line, empty)
- `backend/app/api/testplan/__init__.py`
- `backend/app/api/results/__init__.py`

**Severity**: 🔵 Low

`backend/app/api/__init__.py` is essentially empty (only has a module docstring reference).

**Issue**: While not a bug, the main API `__init__.py` could export the routers for cleaner imports.

**Optional improvement**:
```python
"""
API Router Module

Exports all API routers for easy importing.
"""

from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.stations import router as stations_router
from app.api.tests import router as tests_router
from app.api.measurements import router as measurements_router
from app.api.dut_control import router as dut_control_router
from app.api.testplan import router as testplan_router
from app.api.results import router as results_router

__all__ = [
    "auth_router",
    "projects_router",
    "stations_router",
    "tests_router",
    "measurements_router",
    "dut_control_router",
    "testplan_router",
    "results_router",
]
```

---

## 6. Redundant Exception Handling

**File**: `backend/app/api/dut_control.py`
**Lines**: 119-123, 264-268, 356-360

```python
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Relay control error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

**Issue**: The `except HTTPException: raise` pattern is redundant - re-raising without modification serves no purpose.

**Simpler**:
```python
except Exception as e:
    logger.error(f"Relay control error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

The HTTPException will naturally propagate without the explicit catch-and-re-raise.

---

## 7. Inconsistent Query Parameter Naming

**Files**: Multiple

**In `tests.py`**:
```python
async def list_test_sessions(
    station_id: int = None,
    serial_number: str = None,
    limit: int = 50,
    offset: int = 0,
```

**In `results/sessions.py`**:
```python
async def get_test_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
```

**Issue**: `offset` vs `skip` for the same concept. Inconsistent parameter naming makes the API less predictable.

**Fix**: Standardize on one name throughout (FastAPI convention uses `offset`):
```python
async def list_test_sessions(
    station_id: int = None,
    serial_number: str = None,
    offset: int = 0,     # Changed from skip to offset
    limit: int = 50,
```

---

## 8. Commented-Out Code

**File**: `backend/app/api/tests.py`
**Lines**: 181-186

```python
# 原有程式碼: Calculate elapsed time (wall-clock time)
# elapsed_time = None
# if session.start_time:
#     end = session.end_time if session.end_time else datetime.utcnow()
#     elapsed_time = int((end - session.start_time).total_seconds())
```

**Issue**: Commented-out code should be removed. Use git history to see old code.

**Fix**: Delete the commented-out code and rely on git history:
```bash
git log -p --all -S 'wall-clock time'
```

---

## 9. Missing Field Descriptions in Pydantic Models

**File**: `backend/app/api/measurements.py`
**Lines**: 19-37

```python
class MeasurementRequest(BaseModel):
    measurement_type: str
    test_point_id: str
    switch_mode: str
    test_params: Dict[str, Any]
    run_all_test: bool = False
```

**Issue**: No Field descriptions for API documentation.

**Fix**:
```python
class MeasurementRequest(BaseModel):
    """Request model for measurement execution"""
    measurement_type: str = Field(
        ...,
        description="Type of measurement (PowerSet, PowerRead, CommandTest, etc.)"
    )
    test_point_id: str = Field(
        ...,
        description="Identifier for the test point"
    )
    switch_mode: str = Field(
        ...,
        description="Instrument switch mode (e.g., 'DAQ973A', 'comport')"
    )
    test_params: Dict[str, Any] = Field(
        ...,
        description="Test-specific parameters as key-value pairs"
    )
    run_all_test: bool = Field(
        default=False,
        description="Continue execution after failures (runAllTest mode)"
    )
```

---

## 10. Inconsistent Status Codes

**Files**: Multiple

Some endpoints use `status.HTTP_XXX_YYY`, others use raw integers:

| With constant | Raw integer | File |
|---------------|-------------|------|
| `status.HTTP_201_CREATED` | - | `projects.py:66` |
| - | `404` | `projects.py:61` |
| - | `400` | `stations.py:68` |
| `status.HTTP_403_FORBIDDEN` | - | `stations.py:87` |
| `status.HTTP_500_INTERNAL_SERVER_ERROR` | - | `measurements.py:106` |
| - | `500` | `dut_control.py:109` |

**Issue**: Inconsistent HTTP status code usage.

**Fix**: Use `status.HTTP_XXX_YYY` constants throughout for better IDE support and readability.
