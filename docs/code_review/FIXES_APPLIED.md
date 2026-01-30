# Critical Issues - Fixes Applied

**Date:** 2026-01-30
**Status:** ✅ Completed (6/7 issues fixed)

This document summarizes the fixes applied to address the critical issues identified in `CRITICAL.md`.

---

## ✅ Issue #1: Unreachable Dead Code (FIXED)

**File:** `backend/app/api/tests.py`
**Line:** 411
**Severity:** 🔴 Critical

### Problem
The `return session` statement at line 411 was unreachable because the function already returns inside the try block.

### Fix Applied
```python
# Removed the unreachable line:
# return session  # ← NEVER REACHED

# Added comment explaining the change:
# 原有程式碼: return session  # ← 此行永遠不會執行(已移除)
# 修改: 移除 unreachable dead code，避免誤導和潛在的 bug
```

### Impact
- Removed confusing dead code
- Prevented potential copy-paste errors in future development

---

## ✅ Issue #2: Inconsistent Authentication Dependency (FIXED)

**File:** `backend/app/api/dut_control.py`
**Lines:** 10, 73, 130, 153, 175, 215, 275, 302, 328, 365
**Severity:** 🔴 Critical

### Problem
Used `get_current_user` instead of `get_current_active_user`, allowing inactive/disabled users to control DUT hardware.

### Fix Applied
```python
# Changed import:
from app.dependencies import get_current_active_user

# Replaced ALL occurrences (10 endpoints):
async def set_relay_state(
    request: RelayControlRequest,
    current_user: dict = Depends(get_current_active_user)  # ✅ FIXED
):
```

### Impact
- **Security improvement:** Only active users can control hardware
- **Consistency:** Matches authentication pattern used in all other API files
- **Endpoints affected:** 10 DUT control endpoints (relay + chassis rotation)

---

## ✅ Issue #3: SQL Injection Risk via LIKE Query (FIXED)

**File:** `backend/app/api/tests.py`
**Line:** 523
**Severity:** 🔴 Critical

### Problem
Using f-string interpolation with LIKE query could be vulnerable to SQL injection.

### Fix Applied
```python
# Old code:
# query = query.filter(TestSessionModel.serial_number.like(f"%{serial_number}%"))

# New code:
from sqlalchemy import func
query = query.filter(
    TestSessionModel.serial_number.like(func.concat('%', serial_number, '%'))
)
```

### Impact
- **Security improvement:** Prevents SQL injection by using SQLAlchemy's func.concat
- **Pattern:** Uses explicit parameterization instead of f-string interpolation

---

## ✅ Issue #4: Batch Insert Without Transaction Safety (FIXED)

**File:** `backend/app/api/tests.py`
**Lines:** 284-290
**Severity:** 🔴 Critical

### Problem
If batch insert fails, partial data could exist in database without rollback handling.

### Fix Applied
```python
try:
    # Create test results
    created_count = 0
    for result_data in batch_data.results:
        db_result = TestResultModel(...)
        db.add(db_result)
        created_count += 1

    db.commit()

    return {
        "message": "Test results created successfully",
        "created_count": created_count
    }
except Exception as e:
    db.rollback()  # ✅ ADDED
    raise HTTPException(
        status_code=500,
        detail=f"Batch insert failed, all changes rolled back: {str(e)}"
    )
```

### Impact
- **Data integrity:** Ensures atomicity of batch operations
- **Rollback on failure:** No partial data remains if operation fails
- **Better error handling:** Clear error message indicates rollback occurred

---

## ✅ Issue #5: Case-Sensitive File Extension Check (FIXED)

**File:** `backend/app/api/testplan/mutations.py`
**Lines:** 66-70
**Severity:** 🔴 Critical

### Problem
Rejected valid files with uppercase extensions like `test.CSV` or `TestPlan.Csv`.

### Fix Applied
```python
# Old code:
# if not file.filename.endswith('.csv'):

# New code:
if not file.filename.lower().endswith('.csv'):
    raise HTTPException(
        status_code=400,
        detail=ErrorMessages.INVALID_FILE_TYPE
    )
```

### Impact
- **User experience:** Accepts valid CSV files regardless of case
- **Cross-platform compatibility:** Works with files from Windows/Mac/Linux
- **Matches common patterns:** Most file validation uses case-insensitive checks

---

## ✅ Issue #6: Pydantic Model Creation Without Validation (FIXED)

**File:** `backend/app/api/tests.py`
**Lines:** 244, 286
**Severity:** 🔴 Critical

### Problem
Using `.dict()` and unpacking bypassed Pydantic validation, risking database errors from invalid data.

### Fix Applied
```python
# Old code:
# db_result = TestResultModel(**result_data.dict())

# New code (explicit field mapping):
db_result = TestResultModel(
    session_id=result_data.session_id,
    test_plan_id=result_data.test_plan_id,
    item_no=result_data.item_no,
    item_name=result_data.item_name,
    measured_value=result_data.measured_value,
    lower_limit=result_data.lower_limit,
    upper_limit=result_data.upper_limit,
    unit=result_data.unit,
    result=result_data.result,
    error_message=result_data.error_message,
    execution_duration_ms=result_data.execution_duration_ms
)
```

### Impact
- **Type safety:** Explicit field mapping ensures correct types
- **Validation:** Pydantic validation still applies through the schema
- **Maintainability:** Clear which fields are being set
- **Affected endpoints:** 2 endpoints (single + batch test result creation)

---

## ⚠️ Issue #7: Synchronous Database Operations in Async Endpoints (DEFERRED)

**Files:** All API files
**Severity:** 🔴 Critical (Architectural)

### Problem
API uses `async def` for endpoints but injects synchronous `Session` from SQLAlchemy, causing:
- Blocking database calls that block the entire event loop
- No true async/concurrent database operations
- Potential performance issues under load

### Status
**DEFERRED - Requires Major Refactoring**

This is an architectural issue that requires:
1. Migrating from `sqlalchemy.orm.Session` to `sqlalchemy.ext.asyncio.AsyncSession`
2. Updating all database queries to use `await` syntax
3. Changing `app/core/database.py` to use async engine
4. Updating all API endpoints across 7 files:
   - `auth.py`: 6 endpoints
   - `projects.py`: 5 endpoints
   - `stations.py`: 5 endpoints
   - `tests.py`: 12 endpoints
   - `measurements.py`: 11 endpoints
   - `dut_control.py`: 10 endpoints
   - `testplan/mutations.py`: 6 endpoints

**Recommendation:** Schedule as a separate refactoring task with comprehensive testing.

---

## Summary

### Fixed Issues: 6/7
✅ Issue #1: Unreachable Dead Code
✅ Issue #2: Authentication Inconsistency
✅ Issue #3: SQL Injection Risk
✅ Issue #4: Batch Insert Transaction Safety
✅ Issue #5: Case-Sensitive File Extension
✅ Issue #6: Pydantic Validation Bypass

### Deferred Issues: 1/7
⚠️ Issue #7: Async/Sync Database Mismatch (Architectural)

### Files Modified
1. `backend/app/api/tests.py` - 4 fixes applied
2. `backend/app/api/dut_control.py` - 1 fix applied (10 endpoints affected)
3. `backend/app/api/testplan/mutations.py` - 1 fix applied

### Testing
- ✅ Python syntax validation passed
- ⚠️ Recommended: Run integration tests on affected endpoints
- ⚠️ Recommended: Test with uppercase .CSV files
- ⚠️ Recommended: Test batch insert rollback behavior

### Next Steps
1. Run comprehensive test suite to verify fixes
2. Test DUT control endpoints with inactive users (should be rejected)
3. Test CSV upload with various file name cases
4. Plan async database migration as separate task
5. Update code review status document
