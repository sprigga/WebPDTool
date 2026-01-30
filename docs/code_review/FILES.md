# Individual File Reviews

Detailed analysis of each API file.

---

## auth.py (129 lines)

**Purpose**: Authentication endpoints (login, logout, token refresh)

### Summary
Well-structured authentication module with proper JWT token handling.

### Issues Found
| Severity | Issue | Line |
|----------|-------|------|
| 🔴 Critical | Sync DB in async endpoint | 20, 56, 94, 114 |
| 🔴 Critical | Direct role check without helper | - |

### Code Quality
- ✅ Good: Comprehensive docstrings
- ✅ Good: Uses OAuth2PasswordRequestForm for Swagger compatibility
- ✅ Good: Token expiration from config
- ⚠️ Note: Logout is client-side only (JWT stateless)

### Recommendations
1. Migrate to AsyncSession
2. Consider token refresh endpoint with validation
3. Add rate limiting for login attempts

---

## projects.py (182 lines)

**Purpose**: Project CRUD operations

### Summary
Basic project management with admin-only write operations.

### Issues Found
| Severity | Issue | Line |
|----------|-------|------|
| 🔴 Critical | Sync DB in async endpoint | 20, 42, 66, 109, 151 |
| 🟠 High | Direct role checks | 84, 129, 166 |
| 🟠 High | Pydantic v1 syntax | 101, 141 |

### Code Quality
- ✅ Good: Consistent error handling
- ✅ Good: Proper use of HTTP status codes
- ⚠️ Note: No permission checker helper used

### Recommendations
1. Use `PermissionChecker.check_admin()` instead of direct role checks
2. Update to Pydantic v2 `model_dump()`
3. Add pagination to `get_projects()`

---

## stations.py (211 lines)

**Purpose**: Station CRUD operations

### Summary
Well-refactored station management using helper functions.

### Issues Found
| Severity | Issue | Line |
|----------|-------|------|
| 🔴 Critical | Sync DB in async endpoint | All endpoints |
| 🟠 High | Pydantic v2 syntax (inconsistent) | 115, 163 |

### Code Quality
- ✅ Good: Uses `get_entity_or_404` helper
- ✅ Good: Uses `PermissionChecker` helper
- ✅ Good: Refactored from manual checks
- ✅ Good: Uses Pydantic v2 `model_dump()`

### Recommendations
1. Migrate to AsyncSession
2. Consider soft delete instead of hard delete
3. Add station code uniqueness validation

---

## tests.py (530 lines)

**Purpose**: Test session and result management

### Summary
Comprehensive test execution API with some critical bugs.

### Issues Found
| Severity | Issue | Line |
|----------|-------|------|
| 🔴 Critical | Unreachable return statement | 411 |
| 🔴 Critical | SQL injection risk (LIKE) | 523 |
| 🔴 Critical | Batch insert without transaction | 284-290 |
| 🟡 Medium | Unused import (BackgroundTasks) | 4 |
| 🟡 Medium | Inline import | 343-355 |
| 🟡 Medium | Magic numbers | 191-193 |
| 🟠 High | Chinese comments | 181-193, 340-355 |

### Code Quality
- ✅ Good: Comprehensive endpoint coverage
- ✅ Good: Session lifecycle management
- ⚠️ Note: Complex elapsed time calculation logic
- ⚠️ Note: Report generation embedded in endpoint

### Recommendations
1. **URGENT**: Remove dead code at line 411
2. Add transaction wrapper for batch operations
3. Use parameterized queries for LIKE filters
4. Move report generation to service layer

---

## measurements.py (499 lines)

**Purpose**: Measurement execution and instrument control

### Summary
Complex measurement API with PDTool4 compatibility layer.

### Issues Found
| Severity | Issue | Line |
|----------|-------|------|
| 🔴 Critical | Sync DB in async endpoint | All endpoints |
| 🟠 High | Decimal conversion in API layer | 79-92 |
| 🔵 Low | Hardcoded instrument list | 328-353 |
| 🔵 Low | Hardcoded templates | 371-457 |

### Code Quality
- ✅ Good: Detailed measurement type documentation
- ✅ Good: Support for dependencies
- ✅ Good: Background task support for batch
- ⚠️ Note: 87 lines of hardcoded template data

### Recommendations
1. Move decimal conversion to service layer or Pydantic validator
2. Extract instrument templates to configuration
3. Add rate limiting for measurement execution
4. Consider WebSocket for real-time updates

---

## dut_control.py (391 lines)

**Purpose**: DUT hardware control (relay, chassis rotation)

### Summary
Hardware control API with authentication issue.

### Issues Found
| Severity | Issue | Line |
|----------|-------|------|
| 🔴 Critical | Wrong auth dependency | 10, 73, 130, 153, etc. |
| 🟡 Medium | Missing return type hints | Multiple endpoints |
| 🔵 Low | Redundant exception handling | 119-123, 264-268 |

### Code Quality
- ✅ Good: Clear PDTool4 mapping in comments
- ✅ Good: Comprehensive error logging
- ✅ Good: Well-structured request/response models
- ⚠️ Note: Uses `get_current_user` instead of `get_current_active_user`

### Recommendations
1. **URGENT**: Change to `get_current_active_user`
2. Add return type hints to all endpoints
3. Remove redundant `except HTTPException: raise`
4. Add hardware operation rate limiting

---

## testplan/__init__.py (33 lines)

**Purpose**: Test plan router aggregator

### Summary
Clean modular structure combining 4 sub-routers.

### Issues Found
None

### Code Quality
- ✅ Good: Clear separation of concerns
- ✅ Good: Maintains backward compatibility
- ✅ Good: Well-documented module structure

---

## testplan/mutations.py (333 lines)

**Purpose**: Test plan create/update/delete operations

### Summary
Well-structured mutation endpoints with service layer integration.

### Issues Found
| Severity | Issue | Line |
|----------|-------|------|
| 🔴 Critical | Case-sensitive file check | 66 |
| 🔵 Low | Print for debugging | 118-119 |
| 🟠 High | Chinese comments | 91-98, 120, 132, 146, 212 |

### Code Quality
- ✅ Good: Uses `PermissionChecker` helper
- ✅ Good: Uses `get_entity_or_404` helper
- ✅ Good: Service layer integration
- ⚠️ Note: Inline import of CSV parser

### Recommendations
1. Use `.lower().endswith('.csv')` for file check
2. Replace `print()` with `logger.error()`
3. Translate Chinese comments to English

---

## testplan/queries.py

**Purpose**: Test plan query endpoints

**Status**: Not reviewed in detail (not in initial file read)

---

## testplan/validation.py

**Purpose**: Test plan validation endpoints

**Status**: Not reviewed in detail (not in initial file read)

---

## testplan/sessions.py

**Purpose**: Test plan session-related endpoints

**Status**: Not reviewed in detail (not in initial file read)

---

## results/__init__.py (39 lines)

**Purpose**: Results router aggregator

### Summary
Clean modular structure combining 6 sub-routers.

### Issues Found
None

### Code Quality
- ✅ Good: Clear module separation
- ✅ Good: Comprehensive feature coverage
- ✅ Good: Backward compatible exports

---

## results/sessions.py (229 lines)

**Purpose**: Test session listing and detail endpoints

### Summary
Well-structured session query endpoints with helper usage.

### Issues Found
| Severity | Issue | Line |
|----------|-------|------|
| 🔴 Critical | Sync DB in async endpoint | All endpoints |
| 🟡 Medium | Duplicate conversion logic | 117-132, 192-207 |
| 🟡 Medium | Large nested responses | 44-59 |

### Code Quality
- ✅ Good: Uses `calculate_test_statistics` helper
- ✅ Good: Comprehensive filtering support
- ✅ Good: Proper join syntax
- ⚠️ Note: Returns all results in session list (potentially large)

### Recommendations
1. Extract result conversion to helper function
2. Separate session list from detailed results
3. Add response compression for large datasets
4. Consider cursor-based pagination

---

## results/measurements.py

**Purpose**: Individual measurement result endpoints

**Status**: Not reviewed in detail (not in initial file read)

---

## results/summary.py

**Purpose**: Summary statistics endpoint

**Status**: Not reviewed in detail (not in initial file read)

---

## results/export.py

**Purpose**: CSV export endpoint

**Status**: Not reviewed in detail (not in initial file read)

---

## results/cleanup.py

**Purpose**: Session cleanup and deletion endpoints

**Status**: Not reviewed in detail (not in initial file read)

---

## results/reports.py

**Purpose**: Saved report management endpoints

**Status**: Not reviewed in detail (not in initial file read)

---

## Unreviewed Files

The following files exist but were not reviewed in detail:
- `backend/app/api/testplan/queries.py`
- `backend/app/api/testplan/validation.py`
- `backend/app/api/testplan/sessions.py`
- `backend/app/api/results/measurements.py`
- `backend/app/api/results/summary.py`
- `backend/app/api/results/export.py`
- `backend/app/api/results/cleanup.py`
- `backend/app/api/results/reports.py`
