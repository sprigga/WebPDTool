# WebPDTool Architecture Overview

## Project Summary

WebPDTool is a web-based automated testing system refactored from PDTool4 desktop application. It executes hardware tests on manufactured products with complete PDTool4 compatibility.

**Key Features:**
- Complete PDTool4 compatibility layer with 7 limit types and 3 value types
- Async test execution using asyncio and instrument connection pooling
- JWT-based authentication with Pinia state management
- Modular FastAPI backend with 9 API router modules
- Vue 3 frontend with Element Plus UI components
- MySQL 8.0 database with comprehensive schema

## Technology Stack

### Frontend
- **Vue 3.4+** with Composition API
- **Element Plus 2.5+** UI components
- **Pinia 2.1+** state management
- **Vite 5.0+** build tool
- **Axios 1.6+** HTTP client

### Backend
- **FastAPI 0.104+** web framework
- **SQLAlchemy 2.0+** async ORM
- **Pydantic 2.0+** data validation
- **Python-JOSE** JWT token handling
- **Alembic 1.12+** database migrations

### DevOps
- **Docker + Docker Compose** containerization
- **Nginx** reverse proxy
- **MySQL 8.0+** database

## Architecture Patterns

### 1. Measurement Abstraction Layer

**Core Components:**
- `BaseMeasurement` abstract base class (three-phase lifecycle)
- 17 measurement implementations (PowerSet, PowerRead, SFCtest, etc.)
- Registry system for dynamic measurement lookup
- PDTool4 validation logic with 7 limit types and 3 value types

**PDTool4 Compatibility:**
- Exact replication of `test_point_runAllTest.py` validation logic
- CSV import with complete field mapping
- runAllTest mode continues execution after failures

### 2. Test Execution Engine

**Orchestration Components:**
- `TestEngine` - async test session management
- `MeasurementService` - measurement dispatching
- `InstrumentManager` - connection pooling with state tracking

**Execution Flow:**
```
User (TestMain.vue) → POST /api/tests/sessions/start → TestEngine.execute_test_session()
→ MeasurementService.execute_measurement() → BaseMeasurement subclass
→ InstrumentManager → validate_result() → Save TestResult → Return status
```

### 3. Frontend Architecture

**View Components (10):**
- `TestMain.vue` - Primary test execution interface (495 lines)
- `ReportAnalysis.vue` - Statistical analysis with charts (added 2026-03-10)
- `TestPlanManage.vue` - Test plan CRUD operations
- `UserManage.vue` - User management (admin only)
- Additional views for project, station, history management

**State Management:**
- `auth.js` - Authentication state with JWT tokens
- `project.js` - Project and station data with caching
- `users.js` - User management state

**API Layer:**
- 9 Axios API clients with JWT interceptors
- Comprehensive error handling and response validation

### 4. Backend API Organization

**Router Modules (9):**
1. `auth.py` - Authentication endpoints
2. `users.py` - User CRUD with role-based access
3. `projects.py` - Project management
4. `stations.py` - Station management
5. `testplan/` - Modular sub-routers (queries, mutations, validation)
6. `tests.py` - Test session management
7. `measurements.py` - Measurement type information
8. `measurement-results/` - 7 sub-routers for results handling
9. `dut_control.py` - DUT communication

### 5. Database Schema

**Core Tables (7):**
- `users` - User accounts with bcrypt password hashing
- `projects` - Project definitions with codes
- `stations` - Station definitions with project relationships
- `test_plans` - CSV-imported test specifications
- `test_sessions` - Test execution tracking
- `test_results` - Individual test item results
- `sfc_logs` - SFC communication logs

**Relationships:**
```
projects (1) —→ (N) stations —→ (N) test_plans
stations (1) —→ (N) test_sessions —→ (N) test_results
users    (1) —→ (N) test_sessions
```

## Key Implementation Details

### PDTool4 Compatibility Layer

**Validation Logic:**
- 7 limit types: lower, upper, both, equality, inequality, partial, none
- 3 value types: string, integer, float
- Automatic instrument error detection
- runAllTest mode continues execution on failures

**Measurement Registry:**
- Legacy command name support (SFCtest, getSN, OPjudge, etc.)
- Case-insensitive lookup with normalization
- Dynamic class registration and lookup

### Modern Architecture Features

**Async/Await Pattern:**
- All database operations use async/await
- Instrument I/O is non-blocking
- Concurrent test execution support

**JWT Authentication:**
- 8-hour token expiration
- Pinia storage with localStorage fallback
- Axios interceptor for automatic header injection

**Error Handling:**
- FastAPI HTTPException with appropriate status codes
- Frontend API client with response interceptors
- Comprehensive measurement error categorization

## Development Commands

### Docker Environment (Primary)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Database initialization
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/schema.sql
```

### Local Development
```bash
# Backend (Python 3.11+)
cd backend
python -m venv venv
source venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# Frontend (Node.js 16+)
cd frontend
npm install
npm run dev
```

## Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 9080 | Nginx serving Vue SPA |
| Backend | 9100 | uvicorn FastAPI server |
| Database | 33306 | MySQL container (internal 3306) |
| API Docs | 9100/docs | Swagger UI |

## Key Files by Purpose

### Test Execution
- `backend/app/services/test_engine.py` - Test orchestration
- `backend/app/services/measurement_service.py` - Measurement dispatching (81KB)
- `frontend/src/views/TestMain.vue` - Main test interface (495 lines)

### Measurement Layer
- `backend/app/measurements/base.py` - Base class and validation logic
- `backend/app/measurements/implementations.py` - 17 measurement implementations (96KB)
- `backend/app/measurements/registry.py` - Registry system

### Instrument Drivers
- `backend/app/services/instruments/` - 30+ instrument driver implementations
- Communication modules: `comport_command.py`, `tcpip_command.py`, etc.

### Database API
- `backend/app/api/` - 9 router modules
- `backend/app/models/` - SQLAlchemy ORM models (7 tables)
- `backend/app/schemas/` - Pydantic validation schemas

## Architecture Strengths

1. **Complete PDTool4 Compatibility:** Exact replication of legacy behavior with modern architecture
2. **Modular Design:** Clear separation of concerns with extensible components
3. **Async Performance:** Non-blocking I/O for concurrent test execution
4. **Comprehensive Error Handling:** Detailed error categorization and recovery
5. **Modern Frontend:** Vue 3 Composition API with state management and routing

This architecture successfully bridges legacy PDTool4 functionality with modern web development practices, providing a scalable and maintainable testing platform.