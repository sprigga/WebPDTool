# Critical Issues

**Status Update (2026-01-30):** ✅ 6/7 issues fixed - See `FIXES_APPLIED.md` for details

**Must fix immediately** - These issues represent bugs, security vulnerabilities, or critical architectural problems.

---

## 1. Unreachable Dead Code ✅ FIXED

**File**: `backend/app/api/tests.py`
**Lines**: 405-411
**Severity**: 🔴 Critical
**Status**: ✅ Fixed on 2026-01-30

```python
@router.post("/instruments/{instrument_id}/reset", response_model=dict)
async def reset_instrument(
    instrument_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Reset a specific instrument"""
    try:
        await instrument_manager.reset_instrument(instrument_id)
        return {
            "instrument_id": instrument_id,
            "status": "reset_completed",
            "message": f"Instrument {instrument_id} has been reset"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting instrument: {str(e)}"
        )

    return session  # ← Line 411: NEVER REACHED
```

**Issue**: The `return session` statement at line 411 is unreachable because the function already returns inside the try block. This is dead code that suggests a copy-paste error.

**Fix**:
```python
# Remove the unreachable return statement
# The function should end after the except block
```

---

## 2. Inconsistent Authentication Dependency ✅ FIXED

**File**: `backend/app/api/dut_control.py`
**Lines**: 10, 73, 130, 153, 175, 215, 275, 302, 328, 365
**Severity**: 🔴 Critical
**Status**: ✅ Fixed on 2026-01-30 (10 endpoints updated)

```python
from app.dependencies import get_current_user  # Line 10 - WRONG!

async def set_relay_state(
    request: RelayControlRequest,
    current_user: dict = Depends(get_current_user)  # Line 73 - WRONG!
):
```

**Issue**: Uses `get_current_user` instead of `get_current_active_user`. This could allow inactive/disabled users to control DUT hardware (relays, chassis rotation).

**Expected pattern** (used in all other API files):
```python
from app.dependencies import get_current_active_user

async def set_relay_state(
    request: RelayControlRequest,
    current_user: dict = Depends(get_current_active_user)
):
```

**Fix**: Replace all `get_current_user` with `get_current_active_user` in `dut_control.py`.

---

## 3. SQL Injection Risk via LIKE Query ✅ FIXED

**File**: `backend/app/api/tests.py`
**Line**: 523
**Severity**: 🔴 Critical
**Status**: ✅ Fixed on 2026-01-30 (using func.concat)

```python
if serial_number:
    query = query.filter(TestSessionModel.serial_number.like(f"%{serial_number}%"))
```

**Issue**: While SQLAlchemy ORM provides some protection, using f-string interpolation with LIKE is not the recommended pattern. This could be vulnerable if `serial_number` contains special SQL characters.

**Fix**:
```python
if serial_number:
    query = query.filter(TestSessionModel.serial_number.like(f"%{serial_number}%"))
    # Better: use bind parameter pattern
    query = query.filter(TestSessionModel.serial_number.like(
        literal(f"%{serial_number}%")
    ))
```

---

## 4. Synchronous Database Operations in Async Endpoints ⚠️ DEFERRED

**Files**: All API files
**Severity**: 🔴 Critical (Architectural)
**Status**: ⚠️ Deferred - Requires major refactoring (see FIXES_APPLIED.md)

```python
from sqlalchemy.orm import Session  # Synchronous!

@router.get("/sessions", response_model=List[TestSession])
async def list_test_sessions(
    db: Session = Depends(get_db),  # ← SYNC Session in ASYNC endpoint
    ...
):
```

**Issue**: The API uses `async def` for endpoints but injects synchronous `Session` from SQLAlchemy. This causes:
- Blocking database calls that block the entire event loop
- No true async/concurrent database operations
- Potential performance issues under load

**Current setup** (`app/core/database.py`):
```python
def get_db():
    db = SessionLocal()  # Synchronous session
    try:
        yield db
    finally:
        db.close()
```

**Should be**:
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async def get_db():
    async with async_session() as session:
        yield session
```

**Impact**: All endpoints need migration to `AsyncSession`:
- `auth.py`: 6 endpoints
- `projects.py`: 5 endpoints
- `stations.py`: 5 endpoints
- `tests.py`: 12 endpoints
- `measurements.py`: 11 endpoints
- `dut_control.py`: 10 endpoints

---

## 5. Batch Insert Without Transaction Safety ✅ FIXED

**File**: `backend/app/api/tests.py`
**Lines**: 284-290
**Severity**: 🔴 Critical
**Status**: ✅ Fixed on 2026-01-30 (added try-except-rollback)

```python
@router.post("/sessions/{session_id}/results/batch", response_model=dict)
async def create_test_results_batch(...):
    # Create test results
    created_count = 0
    for result_data in batch_data.results:
        db_result = TestResultModel(**result_data.dict())
        db.add(db_result)
        created_count += 1

    db.commit()  # ← If this fails, partial data exists
```

**Issue**: If any insert fails or commit fails, the database could contain partial results. There's no transaction rollback handling.

**Fix**:
```python
try:
    created_count = 0
    for result_data in batch_data.results:
        db_result = TestResultModel(**result_data.dict())
        db.add(db_result)
        created_count += 1

    db.commit()
except Exception as e:
    db.rollback()
    raise HTTPException(
        status_code=500,
        detail=f"Batch insert failed, rolled back: {str(e)}"
    )
```

---

## 6. Case-Sensitive File Extension Check ✅ FIXED

**File**: `backend/app/api/testplan/mutations.py`
**Lines**: 66-70
**Severity**: 🔴 Critical
**Status**: ✅ Fixed on 2026-01-30 (using .lower())

```python
# Validate file type
if not file.filename.endswith('.csv'):
    raise HTTPException(
        status_code=400,
        detail=ErrorMessages.INVALID_FILE_TYPE
    )
```

**Issue**: Rejects valid files with uppercase extensions like `test.CSV` or `TestPlan.Csv`.

**Fix**:
```python
if not file.filename.lower().endswith('.csv'):
    raise HTTPException(
        status_code=400,
        detail=ErrorMessages.INVALID_FILE_TYPE
    )
```

---

## 7. Pydantic Model Creation Without Validation ✅ FIXED

**File**: `backend/app/api/tests.py`
**Line**: 244, 286
**Severity**: 🔴 Critical
**Status**: ✅ Fixed on 2026-01-30 (explicit field mapping)

```python
# Directly unpack dict to model without validation
db_result = TestResultModel(**result_data.dict())
db.add(db_result)
```

**Issue**: Using `.dict()` and unpacking bypasses Pydantic validation. If `result_data.dict()` contains invalid keys or wrong types, it could cause database errors.

**Fix**:
```python
# Use the model's validate method or proper construction
db_result = TestResultModel(
    session_id=result_data.session_id,
    item_no=result_data.item_no,
    item_name=result_data.item_name,
    result=result_data.result,
    # ... explicitly set each field
)
```
