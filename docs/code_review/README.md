# API Code Review - Backend (`backend/app/api/`)

**Review Date**: 2026-01-30
**Reviewer**: Claude Code
**Scope**: All API endpoints in the WebPDTool backend

---

## Quick Navigation

| Document | Description |
|----------|-------------|
| [SUMMARY.md](./SUMMARY.md) | Executive summary with statistics and key findings |
| [CRITICAL.md](./CRITICAL.md) | 🔴 Critical issues - must fix immediately |
| [HIGH.md](./HIGH.md) | 🟠 High priority issues - should fix soon |
| [MEDIUM.md](./MEDIUM.md) | 🟡 Medium priority issues - fix when possible |
| [LOW.md](./LOW.md) | 🔵 Low priority issues - code quality improvements |
| [FILES.md](./FILES.md) | Detailed analysis by individual file |

---

## Overview

This review covers **16 API files** in the `backend/app/api/` directory:

### Main Router Files (7)
```
backend/app/api/
├── auth.py              # Authentication (login, logout, token refresh)
├── projects.py          # Project CRUD operations
├── stations.py          # Station CRUD operations
├── tests.py             # Test session and result management
├── measurements.py      # Measurement execution and instrument control
├── dut_control.py       # DUT hardware control (relay, chassis)
└── __init__.py          # (empty)
```

### Modular Sub-Files (9)
```
backend/app/api/
├── testplan/
│   ├── __init__.py      # Router aggregator
│   ├── queries.py       # GET endpoints
│   ├── mutations.py     # POST/PUT/DELETE endpoints
│   ├── validation.py    # Validation endpoints
│   └── sessions.py      # Session-related endpoints
└── results/
    ├── __init__.py      # Router aggregator
    ├── sessions.py      # Session listing and details
    ├── measurements.py  # Individual measurement results
    ├── summary.py       # Summary statistics
    ├── export.py        # CSV export
    ├── cleanup.py       # Session cleanup
    └── reports.py       # Saved report management
```

---

## Issue Summary

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 7 | Must fix immediately |
| 🟠 High | 6 | Should fix soon |
| 🟡 Medium | 7 | Fix when possible |
| 🔵 Low | 6 | Code quality |
| **Total** | **26** | |

---

## Top 5 Critical Issues

1. **Unreachable dead code** (`tests.py:411`) - Copy-paste error
2. **Wrong auth dependency** (`dut_control.py`) - Security issue
3. **Sync DB in async endpoints** - Architectural problem affecting all files
4. **Batch insert without transaction** (`tests.py:284-290`) - Data integrity
5. **Case-sensitive file check** (`testplan/mutations.py:66`) - UX issue

See [CRITICAL.md](./CRITICAL.md) for full details.

---

## Quick Fix Checklist

### This Sprint (Critical)
- [ ] Remove dead code at `tests.py:411`
- [ ] Change `get_current_user` to `get_current_active_user` in `dut_control.py`
- [ ] Add transaction wrapper for batch operations in `tests.py`
- [ ] Fix case-sensitive file extension check in `testplan/mutations.py`

### Next Sprint (High Priority)
- [ ] Use `PermissionChecker` in `projects.py` (replace direct role checks)
- [ ] Standardize on Pydantic v2 `model_dump()` across all files
- [ ] Move decimal conversion logic from `measurements.py` to service layer
- [ ] Use `ErrorMessages` constants consistently

### Technical Debt (Medium/Low)
- [ ] Translate Chinese comments to English
- [ ] Extract hardcoded instrument list to config
- [ ] Replace `print()` statements with `logger`
- [ ] Add return type hints to all endpoints
- [ ] Remove unused imports
- [ ] Remove commented-out code

---

## Architecture Observations

### Positive Patterns
1. **Router Modularity**: Large files split into focused modules (testplan → 5, results → 6)
2. **Service Layer**: Transitioning from direct DB queries to service layer
3. **Helper Functions**: `get_entity_or_404`, `PermissionChecker`, `calculate_test_statistics`
4. **Comprehensive Docstrings**: All endpoints have Args/Returns documentation
5. **Schema Validation**: Consistent use of Pydantic models

### Areas for Improvement
1. **Async/Await**: Using sync `Session` in async `def` endpoints
2. **Error Handling**: Inconsistent error message patterns
3. **Type Hints**: Missing return type annotations
4. **Configuration**: Hardcoded data mixed with code

---

## PDTool4 Compatibility

The API maintains good PDTool4 compatibility:

| Feature | API Endpoint | PDTool4 Equivalent |
|---------|--------------|-------------------|
| Test execution | `POST /tests/sessions/{id}/start` | `test_point_runAllTest.py` |
| Measurement types | `GET /measurements/types` | Measurement modules |
| Relay control | `POST /dut-control/relay/set` | `MeasureSwitchON/OFF` |
| Chassis rotation | `POST /dut-control/chassis/rotate` | `MyThread_CW/CCW` |
| Test plan import | `POST /testplan/upload` | CSV import |

---

## Statistics

### Code Metrics
| Metric | Value |
|--------|-------|
| Total lines reviewed | ~3,500 |
| Number of endpoints | ~60 |
| Average file size | ~220 lines |
| Largest file | tests.py (530 lines) |
| Most modular | results/ (6 sub-files) |

### Issues by Category
| Category | Count |
|----------|-------|
| Security | 2 |
| Data Integrity | 2 |
| Architecture | 1 |
| Code Quality | 15 |
| Internationalization | 2 |
| Documentation | 4 |

---

## Next Steps

1. Review [CRITICAL.md](./CRITICAL.md) and create fixes for critical issues
2. Assign high priority items from [HIGH.md](./HIGH.md) to upcoming sprint
3. Create technical debt tickets for medium/low priority items
4. Schedule architecture review for AsyncSession migration
5. Consider implementing the recommended improvements from [FILES.md](./FILES.md)

---

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Project architecture and development guidelines
- [API Documentation](http://localhost:9100/docs) - FastAPI Swagger UI
- [Database Schema](../../database/schema.sql) - Database structure
