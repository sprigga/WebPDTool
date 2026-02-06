# Medium Priority - Architectural Recommendations

**Status**: Not Implemented (Requires Breaking Changes)

These are recommendations from the code review that involve more significant architectural changes and could break frontend compatibility. They should be implemented in a future release with proper planning.

---

## Issue 6: Complex Response Models Without Proper Nesting

**File**: `backend/app/api/results/sessions.py`
**Lines**: 44-59
**Status**: ⚠️ Deferred

### Current Behavior

The `TestSessionResponse` model includes both session metadata AND all test results in a single endpoint:

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
    results: List[MeasurementResultResponse] = []  # ← Can be very large
```

### Problem

For test sessions with many test items (50-100+), this creates very large API responses when listing sessions, as each session includes ALL its detailed results.

### Recommended Architecture

Split into two separate endpoints:

#### 1. Session List Endpoint (Lightweight)
```python
@router.get("/sessions")
async def get_test_sessions(...):
    """List sessions with summary data only"""
    return [
        {
            "id": s.id,
            "project_name": s.project.name,
            "station_name": s.station.name,
            "serial_number": s.serial_number,
            "status": s.status,
            "total_tests": s.total_tests,
            "passed_tests": s.passed_tests,
            "failed_tests": s.failed_tests,
            "error_tests": s.error_tests,
            "started_at": s.started_at,
            "completed_at": s.completed_at
            # NO detailed results array
        }
        for s in sessions
    ]
```

#### 2. Session Results Endpoint (Detail)
```python
@router.get("/sessions/{session_id}/results")
async def get_session_results(session_id: int, ...):
    """Get detailed results for a specific session"""
    return {
        "session_id": session_id,
        "results": [
            # Full result details here
        ]
    }
```

### Benefits

- **Performance**: Reduce API response size by 90%+ for session lists
- **Scalability**: Handle sessions with 100+ test items efficiently
- **User Experience**: Faster page loads in frontend
- **Backwards Compatibility**: Can add new endpoint while keeping old one deprecated

### Implementation Plan

1. Create new endpoint `/api/results/sessions/{session_id}/results`
2. Update frontend to call new endpoint when user clicks on session detail
3. Deprecate `results` field in session list endpoint (keep for backwards compatibility)
4. After frontend migration, remove deprecated field in next major version

### Estimated Impact

- **Frontend Changes**: Medium (update API calls in session detail view)
- **Backend Changes**: Small (add new endpoint, modify existing response)
- **Database Changes**: None
- **Breaking Changes**: None if properly phased

---

## Issue 7: Inconsistent Naming Conventions

**File**: `backend/app/api/results/sessions.py`
**Severity**: 🟡 Medium
**Status**: ⚠️ Deferred

### Current Naming

```python
class MeasurementResultResponse(BaseModel):  # Full name
class TestSessionResponse(BaseModel):        # Shortened name
```

### Problem

Inconsistent naming patterns:
- `MeasurementResultResponse` - uses full descriptive name
- `TestSessionResponse` - uses shortened "Test" prefix (redundant since it's already a test session)

### Recommended Naming

```python
# Option 1: Consistent Shortened Names
class SessionResponse(BaseModel):
    """Session summary info"""
    # ... basic fields only

class SessionDetailResponse(BaseModel):
    """Session info + results"""
    # ... includes results array

class MeasurementResponse(BaseModel):
    """Individual measurement result"""
    # ... measurement fields

# Option 2: Consistent Full Names
class TestSessionSummaryResponse(BaseModel):
    """Test session summary"""

class TestSessionDetailResponse(BaseModel):
    """Test session with full details"""

class TestMeasurementResultResponse(BaseModel):
    """Individual test measurement result"""
```

### Recommendation

Use **Option 1** (Shortened Names) because:
- Cleaner API and code readability
- Follows REST convention (resource names are implicit in URL path)
- Reduces verbosity while maintaining clarity
- Aligns with the separation in Issue 6

### Implementation Considerations

This is a **breaking change** that affects:
- Frontend TypeScript interfaces
- API response schemas
- Pydantic model imports throughout backend

Should be implemented alongside Issue 6 as part of a coordinated API versioning update.

---

## Implementation Priority

**Recommendation**: Implement in release v0.8.0 or later

1. ✅ **First**: Implement all other medium-priority fixes (Issues 1-5) ← **DONE**
2. ⏳ **Next**: Plan API v2 with breaking changes
3. ⏳ **Then**: Implement Issues 6 & 7 together in coordinated release
4. ⏳ **Finally**: Migrate frontend and deprecate old endpoints

## Related Documents

- See `docs/code_review/MEDIUM.md` for implemented fixes
- See `docs/code_review/HIGH.md` for critical issues
- See `docs/code_review/LOW.md` for minor improvements
