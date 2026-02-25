# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WebPDTool is a web-based automated testing system refactored from the desktop application PDTool4. It executes hardware tests on manufactured products, validates results against test plans, and records outcomes. The system uses a 3-tier architecture: Vue 3 frontend, FastAPI backend, and MySQL database.

**Key Architecture:** Complete PDTool4 compatibility layer with measurement abstraction, supporting 7 limit types (lower/upper/both/equality/inequality/partial/none) and 3 value types (string/integer/float). The `runAllTest` mode continues executing tests after failures, matching PDTool4 behavior exactly.

## Development Commands

### Docker Environment (Primary)

```bash
# Start all services (recommended)
docker-compose up -d

# View logs
docker-compose logs -f backend  # Backend logs
docker-compose logs -f frontend # Frontend logs

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Database initialization (first time only)
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/schema.sql
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_data.sql
```

### Local Development

```bash
# Backend (requires Python 3.11+)
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# Frontend (requires Node.js 16+)
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173

# Database access
mysql -h localhost -P 33306 -u pdtool -p webpdtool
# Default password: pdtool123
```

### Testing

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_api/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Run refactoring validation suite
python scripts/test_refactoring.py
```

### Test Plan Import

```bash
cd backend

# Import single CSV file
python scripts/import_testplan.py \
  --project "PROJECT_CODE" \
  --station "STATION_CODE" \
  --csv-file "/path/to/testplan.csv"

# Batch import all test plans
bash scripts/batch_import.sh
```

## Architecture Overview

### Core Components

**Frontend (Vue 3 + Element Plus)**
- `frontend/src/views/TestMain.vue` - Main test execution interface (495 lines, PDTool4 UI clone)
- `frontend/src/views/TestPlanManage.vue` - Test plan CRUD interface
- `frontend/src/views/ProjectManage.vue` - Project and station management
- `frontend/src/views/UserManage.vue` - User management interface (admin only)
- `frontend/src/stores/` - Pinia state management (auth, project, users)
- `frontend/src/api/` - Axios API client with JWT interceptors

**Backend (FastAPI + SQLAlchemy 2.0)**
- `backend/app/main.py` - FastAPI application entry point, router registration
- `backend/app/api/` - 8 API router modules (auth, users, projects, stations, testplan, tests, measurements, results)
- `backend/app/services/` - Business logic layer
- `backend/app/models/` - SQLAlchemy ORM models (7 tables)
- `backend/app/measurements/` - Measurement abstraction layer
- `backend/app/core/` - Database, logging, security core modules

**Database (MySQL 8.0)**
- `database/schema.sql` - Complete database schema with indexes
- `database/seed_data.sql` - Initial data (users, test projects)

### Critical Architecture Patterns

#### Measurement Abstraction Layer

The measurement system is the heart of PDTool4 compatibility:

**Base Class:** `backend/app/measurements/base.py`
- `BaseMeasurement` abstract class defines the measurement interface
- Three-phase execution: `prepare()` → `execute()` → `cleanup()`
- `validate_result()` implements PDTool4's complete validation logic:
  - 7 limit types: lower, upper, both, equality, inequality, partial, none
  - 3 value types: string, integer, float
  - Auto-detects instrument errors ("No instrument found", "Error:")
- `MeasurementResult` dataclass for standardized results

**Registry:** `backend/app/measurements/registry.py`
- `MEASUREMENT_REGISTRY` maps test types to measurement classes
- Runtime registration system for extensibility

**Implementations:** `backend/app/measurements/implementations.py`
- PowerSet, PowerRead, CommandTest, SFCtest, getSN, OPjudge, Other
- Each inherits from `BaseMeasurement` and implements specific hardware logic

#### Test Execution Engine

**TestEngine:** `backend/app/services/test_engine.py`
- Orchestrates async test execution using asyncio
- Manages test session lifecycle (PENDING → RUNNING → COMPLETED/FAILED/ABORTED)
- Coordinates with InstrumentManager for hardware access
- Implements `runAllTest` mode: continues execution after failures, collects error summary

**InstrumentManager:** `backend/app/services/instrument_manager.py`
- Singleton pattern ensures single connection pool
- Tracks instrument states (IDLE/BUSY/ERROR/OFFLINE)
- Handles connection pooling and reset logic

**MeasurementService:** `backend/app/services/measurement_service.py` (81KB, critical)
- Bridges TestEngine and measurement implementations
- Implements runAllTest error collection logic
- Validates parameters and handles measurement execution

#### PDTool4 Compatibility

**Validation Logic:**
```python
# From base.py, integrated from PDTool4's test_point_runAllTest.py
def validate_result(self, measured_value, lower_limit, upper_limit,
                   limit_type='both', value_type='float') -> Tuple[bool, str]
```

This method replicates PDTool4's exact validation rules:
- `limit_type='lower'` - Only lower bound check
- `limit_type='upper'` - Only upper bound check
- `limit_type='both'` - Range check (lower ≤ value ≤ upper)
- `limit_type='equality'` - Exact match (value == expected)
- `limit_type='inequality'` - Not equal (value != expected)
- `limit_type='partial'` - Substring match for strings
- `limit_type='none'` - Always passes

**runAllTest Mode:**
- Frontend: `TestMain.vue` UI toggle and error display
- Backend: `measurement_service.py` continues execution on failures
- Behavior: Identical to PDTool4 - collects all failures, reports at end

### Data Flow

1. **Test Execution Flow:**
   ```
   User (TestMain.vue)
   → POST /api/tests/sessions/start
   → TestEngine.execute_test_session()
   → MeasurementService.execute_measurement()
   → BaseMeasurement subclass.prepare/execute/cleanup()
   → InstrumentManager (hardware interaction)
   → validate_result() (PDTool4 logic)
   → Save TestResult to database
   → Return status to frontend
   ```

2. **Test Plan Import Flow:**
   ```
   CSV file
   → scripts/import_testplan.py
   → Parse CSV with app/utils/csv_parser.py
   → Create/update Project, Station, TestPlan models
   → Commit to database
   ```

3. **Authentication Flow:**
   ```
   Login (Login.vue)
   → POST /api/auth/login
   → Validate credentials (services/auth.py)
   → Generate JWT token
   → Store in Pinia auth store + localStorage
   → Axios interceptor adds Authorization header to all requests
   ```

### Database Relationships

```
projects (1) ──→ (N) stations
stations (1) ──→ (N) test_plans
stations (1) ──→ (N) test_sessions
users    (1) ──→ (N) test_sessions
test_sessions (1) ──→ (N) test_results
test_plans    (1) ──→ (N) test_results
test_sessions (1) ──→ (N) sfc_logs
```

**Key Tables:**
- `users` - Admin/Engineer/Operator roles with bcrypt password hashing
- `test_plans` - CSV-imported test specifications with JSON parameters field
- `test_sessions` - Test execution tracking with start/end time, final_result (PASS/FAIL/ABORT)
- `test_results` - Individual test item results with measured_value and validation outcome

## Environment Configuration

### Required Environment Variables

```bash
# Backend (.env in backend/)
DATABASE_URL=mysql+asyncmy://pdtool:pdtool123@db:3306/webpdtool
SECRET_KEY=your-secret-key-minimum-32-characters-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8 hours
DEBUG=false  # Set to false in production

# Database (docker-compose.yml or .env)
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=webpdtool
MYSQL_USER=pdtool
MYSQL_PASSWORD=pdtool123

# Ports
FRONTEND_PORT=9080
BACKEND_PORT=9100
MYSQL_PORT=33306
```

### Service Ports

- **Frontend:** 9080 (Nginx serving Vue SPA)
- **Backend:** 9100 (uvicorn FastAPI server)
- **Database:** 33306 (MySQL container, internal 3306)
- **API Docs:** http://localhost:9100/docs (Swagger UI)

## Common Development Tasks

### Adding a New Measurement Type

1. Create measurement class in `backend/app/measurements/implementations.py`:
   ```python
   class NewMeasurement(BaseMeasurement):
       async def prepare(self, params: Dict[str, Any]) -> None:
           # Setup logic

       async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
           # Execution logic

       async def cleanup(self) -> None:
           # Cleanup logic
   ```

2. Register in `backend/app/measurements/registry.py`:
   ```python
   MEASUREMENT_REGISTRY.register('NewType', NewMeasurement)
   ```

3. Update test plan CSV with new `test_type` value

### Modifying API Endpoints

1. Add route in appropriate router (e.g., `backend/app/api/tests.py`)
2. Implement business logic in service layer (e.g., `backend/app/services/test_engine.py`)
3. Update frontend API client (e.g., `frontend/src/api/tests.js`)
4. Add Pydantic schema if needed (`backend/app/schemas/`)

### Database Schema Changes

1. Create Alembic migration:
   ```bash
   cd backend
   alembic revision --autogenerate -m "Description"
   ```

2. Review generated migration in `backend/alembic/versions/`

3. Apply migration:
   ```bash
   alembic upgrade head
   ```

4. Update SQLAlchemy models in `backend/app/models/`

### Frontend Component Development

- Use Composition API (`<script setup>`) for all new components
- State management via Pinia stores in `frontend/src/stores/`
- API calls through centralized clients in `frontend/src/api/`
- Element Plus UI components for consistency
- Follow existing patterns in `TestMain.vue` for test-related UIs

### Managing Users

User management allows administrators to create, edit, and delete user accounts with role-based access control.

**File Locations:**
- Backend API: `backend/app/api/users.py` - User CRUD endpoints
- Backend Schemas: `backend/app/schemas/user.py` - User data validation schemas
- Backend Models: `backend/app/models/user.py` - User ORM model with UserRole enum
- Frontend View: `frontend/src/views/UserManage.vue` - User management UI
- Frontend Store: `frontend/src/stores/users.js` - User state management
- Frontend API: `frontend/src/api/users.js` - User API client functions

**User Roles:**
- `admin` - Full system access including user management (can create, edit, delete users)
- `engineer` - Test plan management and test execution
- `operator` - Test execution only

**API Endpoints Summary:**
- `GET /api/users` - List users with pagination and filtering (offset, limit, search, role, is_active)
- `GET /api/users/{id}` - Get specific user
- `POST /api/users` - Create new user (admin only)
- `PUT /api/users/{id}` - Update user (admin only; allows full_name, email, is_active)
- `PUT /api/users/{id}/password` - Change password (admin or self)
- `DELETE /api/users/{id}` - Delete user (admin only; prevents self-deletion)

**Documentation:**
- Complete API reference: `docs/api/users-api.md`
- Interactive API docs: http://localhost:9100/docs (Swagger UI)

## Important Implementation Details

### Async/Await Pattern

All database operations and measurement executions use async/await:
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_test_plan(db: AsyncSession, station_id: int):
    result = await db.execute(select(TestPlan).filter_by(station_id=station_id))
    return result.scalars().all()
```

### JWT Token Management

- Tokens expire after 8 hours (ACCESS_TOKEN_EXPIRE_MINUTES=480)
- Frontend stores token in localStorage and Pinia auth store
- Axios interceptor auto-adds `Authorization: Bearer <token>` header
- Backend validates via `app/dependencies.py::get_current_user()`

### CSV Import Field Mapping

The CSV parser (`backend/app/utils/csv_parser.py`) maps PDTool4 CSV columns to database fields. Critical mappings:
- `項次` → `item_no`
- `品名規格` → `item_name`
- `上限值` → `upper_limit`
- `下限值` → `lower_limit`
- `limit_type`, `value_type` → PDTool4 validation parameters

### Error Handling

- Backend exceptions use FastAPI HTTPException with appropriate status codes
- Frontend API client (`frontend/src/api/client.js`) has response interceptor for error handling
- Measurement failures distinguish between validation failures (FAIL) and execution errors (ERROR)
- runAllTest mode collects errors but continues execution

## Known Limitations

1. **Instrument Drivers:** Current implementations are stubs. Real hardware drivers need implementation in `backend/app/services/instruments/`.

2. **Real-time Updates:** Uses polling instead of WebSocket. WebSocket support is planned but not implemented.

3. **Modbus/SFC Integration:** Stub implementations exist but need connection to actual Modbus devices and SFC web services.

## Security Notes

- Default SECRET_KEY must be changed in production
- Default user passwords (admin123, eng123, op123) must be changed
- CORS_ORIGINS should be restricted to trusted domains in production
- All passwords are bcrypt-hashed before storage
- SQL injection protected by SQLAlchemy ORM parameterized queries

## Debugging Tips

**Backend Issues:**
```bash
# Check backend logs
docker-compose logs -f backend | grep ERROR

# Verify database connection
docker-compose exec backend python -c "from app.core.database import engine; print('DB OK')"

# Check API health
curl http://localhost:9100/health
```

**Frontend Issues:**
```bash
# Check frontend build
cd frontend && npm run build

# Verify API connection
curl http://localhost:9100/docs  # Should show Swagger UI
```

**Database Issues:**
```bash
# Connect to database
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool

# Check tables
SHOW TABLES;
SELECT COUNT(*) FROM test_plans;
```

**Test Execution Issues:**
- Check instrument status: GET `/api/measurements/instruments`
- View session status: GET `/api/tests/sessions/{session_id}/status`
- Review test results: GET `/api/tests/sessions/{session_id}/results`

## Technology Stack Summary

**Frontend:**
- Vue 3.4+ (Composition API)
- Element Plus 2.5+ (UI components)
- Pinia 2.1+ (state management)
- Vue Router 4.2+ (routing)
- Axios 1.6+ (HTTP client)
- Vite 5.0+ (build tool)

**Backend:**
- FastAPI 0.104+ (web framework)
- SQLAlchemy 2.0+ (async ORM)
- Pydantic 2.0+ (data validation)
- Python-JOSE (JWT tokens)
- Alembic 1.12+ (migrations)
- Uvicorn (ASGI server)

**Database:**
- MySQL 8.0+ (utf8mb4 charset)

**DevOps:**
- Docker + Docker Compose
- Nginx (frontend reverse proxy)
