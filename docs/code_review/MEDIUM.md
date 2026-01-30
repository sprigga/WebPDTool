# Medium Priority Issues

**Fix when possible** - Code quality improvements that could cause issues in edge cases or affect maintainability.

---

## 1. Unused Import

**File**: `backend/app/api/tests.py`
**Line**: 4
**Severity**: 🟡 Medium

```python
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
```

**Issue**: `BackgroundTasks` is imported but never used in the file.

**Fix**: Remove the unused import:
```python
from fastapi import APIRouter, Depends, HTTPException, status
```

---

## 2. Missing Return Type Hints

**File**: `backend/app/api/dut_control.py`
**Lines**: 125-128, 149-152, 172-175, 271-274, 298-301, 325-328, 363-366
**Severity**: 🟡 Medium

```python
async def switch_relay_on(
    channel: int = 1,
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):  # ← Missing return type
```

**Issue**: Missing return type hints reduce code clarity and IDE support.

**Fix**:
```python
async def switch_relay_on(
    channel: int = 1,
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> ControlResponse:
```

Apply to all endpoints in `dut_control.py`:
- `switch_relay_on` → `ControlResponse`
- `switch_relay_off` → `ControlResponse`
- `get_relay_status` → `ControlResponse`
- `rotate_chassis_clockwise` → `ControlResponse`
- `rotate_chassis_counterclockwise` → `ControlResponse`
- `stop_chassis_rotation` → `ControlResponse`
- `get_chassis_status` → `ControlResponse`

---

## 3. Inline Import in Function

**File**: `backend/app/api/tests.py`
**Lines**: 343-355
**Severity**: 🟡 Medium

```python
# 修改: 自動生成 CSV 報告，支援前端驅動模式
try:
    from app.services.report_service import report_service  # ← Inline import
    report_path = report_service.save_session_report(session_id, db)
    if report_path:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"CSV report generated for session {session_id}: {report_path}")
except Exception as report_error:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to generate CSV report for session {session_id}: {report_error}")
```

**Issue**: Lazy importing inside try/except suggests optional functionality but:
- Makes code harder to test
- Hides dependency at runtime
- Logger is also created inline (should be at module level)

**Fix**:
```python
# At module level:
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from app.services.report_service import report_service
    REPORT_SERVICE_AVAILABLE = True
except ImportError:
    REPORT_SERVICE_AVAILABLE = False
    report_service = None
    logger.warning("Report service not available")

# In function:
if REPORT_SERVICE_AVAILABLE and report_service:
    try:
        report_path = report_service.save_session_report(session_id, db)
        if report_path:
            logger.info(f"CSV report generated for session {session_id}: {report_path}")
    except Exception as report_error:
        logger.error(f"Failed to generate CSV report: {report_error}")
```

---

## 4. Magic Numbers

**File**: `backend/app/api/tests.py`
**Lines**: 191-193
**Severity**: 🟡 Medium

```python
total_duration_ms = sum(int(r.execution_duration_ms or 0) for r in results)
if total_duration_ms > 0:
    elapsed_time = round(total_duration_ms / 1000.0, 3)
```

**Issue**: `1000` (milliseconds per second) and `3` (decimal places) are magic numbers.

**Fix**:
```python
# At module level or in constants file:
MS_PER_SECOND = 1000
DEFAULT_DECIMAL_PLACES = 3

# In function:
total_duration_ms = sum(int(r.execution_duration_ms or 0) for r in results)
if total_duration_ms > 0:
    elapsed_time = round(total_duration_ms / MS_PER_SECOND, DEFAULT_DECIMAL_PLACES)
```

---

## 5. Duplicate Statistics Calculation Logic

**File**: `backend/app/api/results/sessions.py`
**Lines**: 114, 189
**Severity**: 🟡 Medium

```python
# In get_test_sessions (line 114):
stats = calculate_test_statistics(results)

# In get_test_session (line 189):
stats = calculate_test_statistics(results)
```

**While `calculate_test_statistics` helper is used, the conversion logic is duplicated:**

```python
# Lines 117-132 (first occurrence)
result_responses = [
    MeasurementResultResponse(
        id=r.id,
        test_session_id=r.test_session_id,
        item_no=r.item_no,
        item_name=r.item_name,
        result=r.result,
        measured_value=r.measured_value,
        min_limit=r.min_limit,
        max_limit=r.max_limit,
        error_message=r.error_message,
        execution_duration_ms=r.execution_duration_ms,
        created_at=r.created_at
    )
    for r in results
]

# Lines 192-207 (second occurrence - identical)
result_responses = [
    MeasurementResultResponse(
        # ... same fields
    )
    for r in results
]
```

**Issue**: Duplicate conversion logic that could be extracted to a helper function.

**Fix**:
```python
def convert_results_to_response(results: List[TestResultModel]) -> List[MeasurementResultResponse]:
    """Convert database results to API response format."""
    return [
        MeasurementResultResponse(
            id=r.id,
            test_session_id=r.test_session_id,
            item_no=r.item_no,
            item_name=r.item_name,
            result=r.result,
            measured_value=r.measured_value,
            min_limit=r.min_limit,
            max_limit=r.max_limit,
            error_message=r.error_message,
            execution_duration_ms=r.execution_duration_ms,
            created_at=r.created_at
        )
        for r in results
    ]

# Then use:
result_responses = convert_results_to_response(results)
```

---

## 6. Complex Response Models Without Proper Nesting

**File**: `backend/app/api/results/sessions.py`
**Lines**: 44-59
**Severity**: 🟡 Medium

```python
class TestSessionResponse(BaseModel):
    id: int
    project_name: str
    station_name: str
    serial_number: str
    operator_id: str | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    results: List[MeasurementResultResponse] = []  # Nested list
```

**Issue**: The model includes both session info AND all results. For sessions with many test items, this creates very large responses.

**Consider**: Separating into two endpoints:
1. `/sessions` - returns session list without detailed results
2. `/sessions/{id}/results` - returns detailed results for a specific session

**Current behavior**:
```python
@router.get("/sessions", response_model=List[TestSessionResponse])
# Returns ALL results for each session - potentially huge response
```

**Recommended**:
```python
@router.get("/sessions")
async def get_test_sessions(...):
    # Return only session info, no detailed results
    return [
        {
            "id": s.id,
            "project_name": s.project.name,
            "station_name": s.station.name,
            "serial_number": s.serial_number,
            "total_tests": s.total_tests,
            "passed_tests": s.passed_tests,
            # ... but NOT the full results list
        }
        for s in sessions
    ]

@router.get("/sessions/{session_id}/results")
async def get_session_results(session_id: int, ...):
    # Return only the results for a specific session
    return result_responses
```

---

## 7. Inconsistent Naming Conventions

**File**: `backend/app/api/results/sessions.py`
**Severity**: 🟡 Medium

```python
class MeasurementResultResponse(BaseModel):  # Full name "MeasurementResult"
class TestSessionResponse(BaseModel):         # Shortened to "Test"
```

**Issue**: Inconsistent naming - `MeasurementResultResponse` vs `TestSessionResponse`. Also, `get_test_sessions` returns `List[TestSessionResponse]` - the "Test" prefix is redundant since it's already a test session.

**Suggested**:
```python
class SessionResponse(BaseModel):
    # Contains session summary info

class SessionDetailResponse(BaseModel):
    # Contains session info + results

class MeasurementResponse(BaseModel):
    # Individual measurement result
```
