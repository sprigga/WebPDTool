# High Priority Issues

**Should fix soon** - These issues affect code consistency, maintainability, or could cause bugs in edge cases.

---

## 1. Inconsistent Role Checking

**File**: `backend/app/api/projects.py`
**Lines**: 84, 129, 166
**Severity**: 🟠 High

```python
# Direct string comparison
if current_user.get("role") != "admin":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only administrators can create projects"
    )
```

**Issue**: Direct string comparison instead of using the centralized `PermissionChecker` helper that's used in `stations.py`.

**Expected pattern** (from `stations.py`):
```python
from app.core.api_helpers import PermissionChecker

PermissionChecker.check_admin(current_user, "delete stations")
```

**Fix**:
```python
# Replace direct role checks with PermissionChecker
PermissionChecker.check_admin(current_user, "create projects")
PermissionChecker.check_admin(current_user, "update projects")
PermissionChecker.check_admin(current_user, "delete projects")
```

---

## 2. Pydantic v1/v2 Mixed Usage

**Files**: `backend/app/api/projects.py`, `backend/app/api/stations.py`
**Severity**: 🟠 High

**In `projects.py` (Pydantic v1)**:
```python
db_project = ProjectModel(**project.dict())  # Line 101
update_data = project.dict(exclude_unset=True)  # Line 141
```

**In `stations.py` (Pydantic v2)**:
```python
db_station = StationModel(**station.model_dump())  # Line 115
update_data = station.model_dump(exclude_unset=True)  # Line 163
```

**Issue**: The codebase is using both Pydantic v1 (`.dict()`) and v2 (`.model_dump()`) methods. This suggests:
- Unclear which Pydantic version is being used
- Potential compatibility issues
- Inconsistent code patterns

**Fix**: Standardize on Pydantic v2 syntax:
```python
# Replace all .dict() with .model_dump()
data = schema.model_dump()  # v2
data_with_unset = schema.model_dump(exclude_unset=True)  # v2
```

---

## 3. Chinese Comments in Production Code

**File**: `backend/app/api/tests.py`
**Lines**: 181-193, 340-355
**Severity**: 🟠 High

```python
# 原有程式碼: Calculate elapsed time (wall-clock time)
# elapsed_time = None
# if session.start_time:
#     end = session.end_time if session.end_time else datetime.utcnow()
#     elapsed_time = int((end - session.start_time).total_seconds())

# 修改: Calculate elapsed time by summing all test items' execution_duration_ms
elapsed_time = None
if results:
    # 累計所有測項的執行時間(毫秒),並轉換為秒(保留3位小數)
    total_duration_ms = sum(int(r.execution_duration_ms or 0) for r in results)
    if total_duration_ms > 0:
        elapsed_time = round(total_duration_ms / 1000.0, 3)
```

**Issue**: Comments in Chinese may cause:
- Encoding issues in some environments
- Reduced maintainability for international teams
- Potential display problems in CI/CD logs

**Fix**:
```python
# Original: Calculate elapsed time (wall-clock time)
# Modified: Calculate elapsed time by summing all test items' execution_duration_ms
elapsed_time = None
if results:
    # Sum execution duration of all test items (ms), convert to seconds (3 decimal places)
    total_duration_ms = sum(int(r.execution_duration_ms or 0) for r in results)
    if total_duration_ms > 0:
        elapsed_time = round(total_duration_ms / 1000.0, 3)
```

Also in `testplan/mutations.py` lines 91-98, 120:
```python
# 使用 TestPlanService 建立測試計畫項目
# 使用 TestPlanService 更新測試計畫項目
# 使用 TestPlanService 刪除測試計畫項目
# 使用 TestPlanService 批次刪除測試計畫項目
# 使用 TestPlanService 重新排序測試計畫項目
```

---

## 4. Decimal Type Conversion in API Layer

**File**: `backend/app/api/measurements.py`
**Lines**: 79-92
**Severity**: 🟠 High

```python
# 修正: 將所有 measured_value 轉換為字串類型以符合 schema 定義
measured_value = result.measured_value
if measured_value is not None:
    from decimal import Decimal
    if isinstance(measured_value, Decimal):
        measured_value = str(float(measured_value))  # Decimal -> float -> str
    elif isinstance(measured_value, (int, float)):
        measured_value = str(measured_value)
    elif not isinstance(measured_value, str):
        measured_value = str(measured_value)
```

**Issue**: Complex type conversion logic in the API layer. This belongs in:
1. The service layer (`measurement_service.py`)
2. The Pydantic schema/validator
3. The measurement result dataclass

**Fix**: Move to Pydantic validator in schema:
```python
class MeasurementResponse(BaseModel):
    measured_value: Optional[str] = None

    @classmethod
    def from_measurement_result(cls, result: MeasurementResult) -> "MeasurementResponse":
        measured_value = str(result.measured_value) if result.measured_value else None
        return cls(
            test_point_id=result.test_point_id,
            measured_value=measured_value,
            # ... other fields
        )
```

---

## 5. Inconsistent Error Messages

**Files**: Multiple
**Severity**: 🟠 High

Different patterns for "not found" errors across the codebase:

| Pattern | Example | File |
|---------|---------|------|
| Constant | `ErrorMessages.PROJECT_NOT_FOUND` | `stations.py` |
| Raw string | `"Project not found"` | `projects.py` |
| F-string | `f"Station {station_id} not found"` | `dut_control.py` |
| Generic | `"Station not found"` | `stations.py` (old) |

**Issue**: Inconsistent error messages make:
- Frontend error handling difficult
- Internationalization harder
- Testing less predictable

**Fix**: Use `ErrorMessages` constants consistently:
```python
from app.core.constants import ErrorMessages

# All files should use:
raise HTTPException(status_code=404, detail=ErrorMessages.PROJECT_NOT_FOUND)
raise HTTPException(status_code=404, detail=ErrorMessages.STATION_NOT_FOUND)
```

---

## 6. Missing Input Sanitization for Query Parameters

**File**: `backend/app/api/results/sessions.py`
**Lines**: 63-70
**Severity**: 🟠 High

```python
@router.get("/sessions", response_model=List[TestSessionResponse])
async def get_test_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: int | None = Query(None),  # No validation
    station_id: int | None = Query(None),  # No validation
    status: str | None = Query(None),      # No validation
    ...
):
```

**Issue**: Query parameters are passed directly to database filters without validation. If invalid values are passed (e.g., negative IDs, invalid status strings), it could cause unexpected behavior.

**Fix**:
```python
from app.core.constants import VALID_SESSION_STATUSES

@router.get("/sessions", response_model=List[TestSessionResponse])
async def get_test_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: int | None = Query(None, gt=0),
    station_id: int | None = Query(None, gt=0),
    status: str | None = Query(None, regex=f"^({'|'.join(VALID_SESSION_STATUSES})$")),
    ...
):
```
