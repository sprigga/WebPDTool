# WebPDTool Codebase Analysis

**Date:** March 11, 2026  
**Project:** WebPDTool - Web-based PDTool4 Testing System  
**Architecture Version:** Vue 3 + FastAPI + SQLAlchemy 2.0 + MySQL 8.0

---

## 1. Project Overview

WebPDTool is a complete web-based refactoring of PDTool4, a desktop application for automated hardware testing. The system executes test plans on manufactured products, validates results against specifications, and provides comprehensive reporting and test management capabilities.

### Key Characteristics:
- **Full PDTool4 Compatibility:** Identical measurement validation logic and test execution behavior
- **Modern Web Stack:** Vue 3 frontend with FastAPI backend (async)
- **Measurement Abstraction:** 7 limit types × 3 value types = 21 validation configurations
- **Async-First Architecture:** All database and I/O operations are asynchronous
- **Containerized:** Docker Compose for complete environment setup
- **Real-time Logging:** Redis integration for distributed log streaming
- **Role-Based Access:** Admin, Engineer, Operator roles with granular permissions

---

## 2. Technology Stack

### Backend
```
FastAPI 0.104+          # Web framework
SQLAlchemy 2.0+         # Async ORM
Pydantic 2.0+           # Data validation
Uvicorn                 # ASGI server
Python 3.9+             # Language
MySQL 8.0+              # Database
Redis 5.0+              # Logging & caching (optional)
Pytest                  # Testing framework
```

### Frontend
```
Vue 3.4+                # Framework (Composition API)
Vite 5.0+               # Build tool
Pinia 2.1+              # State management
Element Plus 2.5+       # UI component library
Axios 1.6+              # HTTP client
ECharts 6.0+            # Data visualization
```

### DevOps
```
Docker & Docker Compose # Containerization
Nginx                   # Reverse proxy (frontend)
MySQL 8.0               # Database service
Redis                   # Logging service
Ubuntu/Linux            # Base OS
```

---

## 3. Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                            │
├─────────────────────────────────────────────────────────────┤
│  Vue 3 SPA (Vite)                                           │
│  - TestMain (Test Execution UI)                             │
│  - TestPlanManage (CRUD)                                    │
│  - ProjectManage, UserManage, Reports                       │
│  - Real-time test monitoring                                │
│  - Pinia State Management (auth, projects, users)           │
│  - Axios API Client with JWT interceptors                   │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP/HTTPS (Port 9080)
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                   Nginx Reverse Proxy                        │
│                  (Port 9080/9100)                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    Frontend              Backend
    (SPA Assets)          (FastAPI)
                          (Port 9100)
```

### Backend Layered Architecture

```
┌─────────────────────────────────────────────────────┐
│           API Layer (app/api/)                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ 9 Router Modules:                            │  │
│  │ • auth.py - Authentication & JWT tokens     │  │
│  │ • users.py - User management (CRUD)         │  │
│  │ • projects.py - Project management          │  │
│  │ • stations.py - Station/test location mgmt  │  │
│  │ • testplans.py - Test plan CRUD             │  │
│  │ • tests.py - Test execution orchestration   │  │
│  │ • measurements.py - Measurement endpoints   │  │
│  │ • dut_control.py - Device control           │  │
│  │ • results/ subdirectory (7 sub-routers)     │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│        Service Layer (app/services/)                │
│  ┌──────────────────────────────────────────────┐  │
│  │ • TestEngine - Test orchestration            │  │
│  │ • MeasurementService - Measurement logic     │  │
│  │ • InstrumentManager - Hardware connections  │  │
│  │ • TestPlanService - Test plan operations    │  │
│  │ • ReportService - Analytics & reporting     │  │
│  │ • AuthService - User authentication         │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│    Measurement Layer (app/measurements/)            │
│  ┌──────────────────────────────────────────────┐  │
│  │ BaseMeasurement (Abstract Base Class)        │  │
│  │ • prepare()/execute()/cleanup() methods      │  │
│  │ • validate_result() - PDTool4 logic          │  │
│  │ • MeasurementResult dataclass                │  │
│  │                                              │  │
│  │ Implementations:                             │  │
│  │ • PowerRead, PowerSet, CommandTest           │  │
│  │ • SFCMeasurement, GetSNMeasurement           │  │
│  │ • OPJudgeMeasurement, Other, Dummy           │  │
│  │ • ComPort, Console, TCPIP                    │  │
│  │ • ChassisRotation, Relay, Wait               │  │
│  │ • RF Tools, CMW100, L6MPU, MDO34             │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│    Data Layer (app/models/ & app/schemas/)          │
│  ┌──────────────────────────────────────────────┐  │
│  │ ORM Models (SQLAlchemy):                     │  │
│  │ • User - Role-based authentication           │  │
│  │ • Project - Test campaign container          │  │
│  │ • Station - Test location/equipment          │  │
│  │ • TestPlan - CSV-imported test specs         │  │
│  │ • TestSession - Execution tracking           │  │
│  │ • TestResult - Individual test outcomes      │  │
│  │ • SFCLog - Manufacturing data logs           │  │
│  │                                              │  │
│  │ Pydantic Schemas (Validation):               │  │
│  │ • UserSchema, ProjectSchema, etc.            │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│      Core Modules (app/core/)                       │
│  ┌──────────────────────────────────────────────┐  │
│  │ • database.py - SQLAlchemy engine setup      │  │
│  │ • security.py - JWT token management        │  │
│  │ • logging_v2.py - Enhanced logging system    │  │
│  │ • exceptions.py - Custom exception classes   │  │
│  │ • constants.py - Application constants      │  │
│  │ • instrument_config.py - Hardware config    │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │
│      MySQL 8.0 Database (webpdtool schema)          │
│      Redis (optional logging backend)               │
└──────────────────────────────────────────────────────┘
```

---

## 4. Core Components & Responsibilities

### 4.1 Backend Components

#### **API Layer** (`backend/app/api/`)
The API layer exposes FastAPI routes organized by domain:

| Module | Routes | Responsibility |
|--------|--------|-----------------|
| `auth.py` | POST /api/auth/login, /logout, /refresh | JWT token generation, user authentication |
| `users.py` | GET/POST/PUT/DELETE /api/users | User CRUD operations, role management |
| `projects.py` | GET/POST/PUT /api/projects | Project management, listing, filtering |
| `stations.py` | GET/POST /api/stations | Test location/equipment management |
| `testplans.py` | GET/POST /api/testplans | Test plan CRUD, CSV import |
| `tests.py` | POST /api/tests/sessions/start, /results | Test execution control, session management |
| `measurements.py` | GET /api/measurements/instruments | Hardware status, instrument connectivity |
| `dut_control.py` | POST /api/dut/reset, /power | Device under test control (relays, power) |
| `results/` (7 sub-routers) | Various /api/tests/results/* routes | Test result queries, export, analysis |

**Key Pattern:** Async endpoints using `async def` with dependency injection for database sessions and authentication.

#### **Service Layer** (`backend/app/services/`)
Business logic orchestration:

| Service | Purpose | Key Methods |
|---------|---------|------------|
| `test_engine.py` | Test session orchestration | `start_test_session()`, `execute_test()`, `pause_test()`, `abort_test()` |
| `measurement_service.py` | Measurement execution coordination | `execute_measurement()`, `validate_measurement()`, `collect_errors()` |
| `instrument_manager.py` | Hardware connection pooling (Singleton) | `connect()`, `send_command()`, `get_status()` |
| `test_plan_service.py` | Test plan operations | `import_test_plan()`, `get_test_plan()`, `validate_test_plan()` |
| `report_service.py` | Analytics & reporting | `generate_report()`, `calculate_statistics()`, `export_data()` |
| `auth.py` | User authentication | `authenticate_user()`, `create_token()` |

**Key Pattern:** All methods are async and interact with SQLAlchemy's AsyncSession.

#### **Measurement Abstraction** (`backend/app/measurements/`)
Core innovation for PDTool4 compatibility:

```python
# BaseMeasurement defines the execution lifecycle
class BaseMeasurement(ABC):
    async def prepare(self, params: Dict[str, Any]) -> None:
        """Setup phase - configure instruments, allocate resources"""
    
    async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
        """Execution phase - perform actual measurement"""
    
    async def cleanup(self) -> None:
        """Cleanup phase - release resources, reset state"""
    
    def validate_result(self, measured_value, lower_limit, upper_limit,
                       limit_type, value_type) -> Tuple[bool, str]:
        """PDTool4 validation logic for 7 limit types × 3 value types"""
```

**Implementations (20+ measurement types):**
- **Power Measurements:** PowerRead, PowerSet (multi-channel)
- **Communication:** ComPort (serial), Console (UART), TCPIP (network)
- **Functional Tests:** CommandTest, SFCMeasurement, GetSNMeasurement, OPJudgeMeasurement
- **RF Testing:** RF_Tool_LTE_TX, RF_Tool_LTE_RX, CMW100_BLE, CMW100_WiFi, L6MPU_LTE_Check
- **Hardware Control:** ChassisRotation, Relay, Wait, MDO34
- **Utility:** Other, Dummy

#### **Data Models** (`backend/app/models/`)
SQLAlchemy 2.0 ORM models with async relationships:

```
User (username, password_hash, role, email)
  ├─ TestSession (user_id, station_id, status, result)
  │   └─ TestResult (test_plan_id, measured_value, validation_result)
  │
Project (project_code, project_name)
  ├─ Station (station_code, station_name, project_id)
  │   ├─ TestPlan (CSV fields + name, limits, value_type, limit_type)
  │   └─ TestSession (references)
  │
SFCLog (manufacturing_data, logging)
```

### 4.2 Frontend Components

#### **Views** (`frontend/src/views/`)
Main page-level components:

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `Login.vue` | Authentication | JWT token handling, role-based redirect |
| `TestMain.vue` | Test execution interface (PDTool4 clone) | Real-time test monitoring, runAllTest mode, error display |
| `TestPlanManage.vue` | Test plan CRUD | CSV import, test parameter editing |
| `ProjectManage.vue` | Project/station management | Create/edit projects and test stations |
| `UserManage.vue` | User administration | CRUD users, role assignment (admin only) |
| `TestResults.vue` | Result query & export | Filter/search results, download CSV/PDF |
| `TestHistory.vue` | Historical sessions | View past test executions, trending |
| `ReportAnalysis.vue` | Analytics & charts | ECharts visualization, pass rates, trending |
| `TestExecution.vue` | Execution monitoring | Real-time test progress, pause/abort controls |
| `SystemConfig.vue` | System settings | Configure instruments, logging, timeouts |

#### **State Management** (`frontend/src/stores/`)
Pinia stores for centralized state:

```javascript
auth.js
  ├─ token (JWT from localStorage)
  ├─ user (current user object)
  ├─ login(username, password)
  ├─ logout()
  └─ isAuthenticated (computed)

project.js
  ├─ currentProject
  ├─ currentStation
  ├─ projects[]
  ├─ setCurrentProject()
  └─ async fetchProjects()

users.js
  ├─ users[]
  ├─ fetchUsers()
  ├─ createUser()
  ├─ updateUser()
  └─ deleteUser()
```

#### **API Clients** (`frontend/src/api/`)
Axios-based API communication:

- `client.js` - Global axios instance with JWT interceptors
- `auth.js` - Auth endpoints (login, logout, refresh)
- `users.js` - User CRUD endpoints
- `projects.js` - Project management endpoints
- `tests.js` - Test execution endpoints
- `measurements.js` - Measurement/instrument endpoints
- `results.js` - Test result queries

**Key Pattern:** Centralized error handling via axios response interceptor.

---

## 5. Database Schema

### Core Tables (7 tables × ~15 columns each)

```sql
-- Users: Role-based authentication
CREATE TABLE users (
  id INT PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  password_hash VARCHAR(255),
  role ENUM('ADMIN', 'ENGINEER', 'OPERATOR'),
  full_name, email, is_active,
  created_at, updated_at
);

-- Projects: Test campaigns
CREATE TABLE projects (
  id INT PRIMARY KEY,
  project_code VARCHAR(50) UNIQUE,
  project_name VARCHAR(100),
  description, is_active,
  created_at, updated_at
);

-- Stations: Test locations/equipment
CREATE TABLE stations (
  id INT PRIMARY KEY,
  station_code, station_name,
  project_id INT FOREIGN KEY,
  test_plan_path, is_active,
  created_at, updated_at
);

-- Test Plans: CSV-imported specifications
CREATE TABLE test_plans (
  id INT PRIMARY KEY,
  project_id, station_id,
  item_no, item_name,
  test_type, test_time_unit,
  upper_limit, lower_limit,
  expected_value, limit_type,
  value_type, parameters (JSON),
  is_active, created_at, updated_at
);

-- Test Sessions: Execution tracking
CREATE TABLE test_sessions (
  id INT PRIMARY KEY,
  user_id, station_id,
  serial_number, dut_sn,
  start_time, end_time,
  status ENUM('PENDING','RUNNING','COMPLETED','FAILED','ABORTED'),
  final_result ENUM('PASS','FAIL','ABORT'),
  run_all_test BOOLEAN,
  error_message, created_at
);

-- Test Results: Individual test outcomes
CREATE TABLE test_results (
  id INT PRIMARY KEY,
  test_plan_id, test_session_id,
  item_no, item_name,
  measured_value, lower_limit, upper_limit,
  limit_type, value_type,
  validation_result ENUM('PASS','FAIL','ERROR'),
  error_message, execution_time,
  created_at
);

-- SFC Logs: Manufacturing integration
CREATE TABLE sfc_logs (
  id INT PRIMARY KEY,
  session_id, log_data (JSON),
  timestamp, created_at
);
```

### Indexes for Performance
- `users.idx_username`, `idx_role`
- `projects.idx_project_code`
- `stations.idx_station_code`
- `test_sessions.idx_status`, `idx_user_id`
- `test_results.idx_test_session_id`, `idx_session_id`

---

## 6. Data Flow Patterns

### 6.1 Test Execution Flow
```
User (TestMain.vue)
  │ POST /api/tests/sessions/start {serial_number, station_id}
  │
  ▼
API Layer (tests.py)
  │ Validates input, creates TestSession (PENDING)
  │
  ▼
TestEngine.start_test_session()
  │ Saves session to DB, sets status = RUNNING
  │ Fetches TestPlan items for station
  │
  ▼
For each TestPlan item:
  │ MeasurementService.execute_measurement()
  │   ├─ Get measurement class from registry
  │   ├─ Call measurement.prepare(params)
  │   ├─ Call measurement.execute(params) → MeasurementResult
  │   │   └─ Call instrument via InstrumentManager
  │   ├─ Call measurement.cleanup()
  │   ├─ Validate result via validate_result()
  │   ├─ Save TestResult to DB
  │   └─ If runAllTest mode: continue on failure
  │
  ▼
TestEngine.complete_test_session()
  │ Calculate final_result (PASS if all PASS, else FAIL)
  │ Save summary to TestSession
  │
  ▼
API Response to Frontend
  │ Returns {status, results[], error_summary}
  │
  ▼
Frontend UI (TestMain.vue)
  │ Updates real-time progress
  │ Displays pass/fail results
  │ Shows error details
```

### 6.2 Test Plan Import Flow
```
User uploads CSV file
  │
  ▼
API: POST /api/testplans/import
  │
  ▼
CSV Parser (app/utils/csv_parser.py)
  │ Maps PDTool4 columns to database fields
  │ Validates required fields
  │ Parses limits (upper/lower)
  │ Extracts measurement parameters
  │
  ▼
TestPlanService.import_test_plan()
  │ Creates/updates TestPlan records
  │ Stores JSON parameters field
  │
  ▼
Database: INSERT/UPDATE test_plans
  │
  ▼
Frontend: Show import status
  │ Display created/updated count
```

### 6.3 Authentication Flow
```
User Login (Login.vue)
  │ {username, password} → POST /api/auth/login
  │
  ▼
AuthService.authenticate_user()
  │ Query User from DB
  │ Verify password (bcrypt)
  │ Generate JWT token
  │
  ▼
API Response: {access_token, token_type, user}
  │
  ▼
Frontend (auth.js store)
  │ Save token to localStorage
  │ Save user object to Pinia store
  │ Axios interceptor: Authorization: Bearer <token>
  │
  ▼
Axios Request
  │ Interceptor adds Authorization header
  │ Backend validates token via get_current_user()
  │
  ▼
If token expired: Refresh via /api/auth/refresh
```

---

## 7. Critical Architecture Patterns

### 7.1 PDTool4 Validation Compatibility

The measurement system replicates PDTool4's exact validation rules through the `validate_result()` method:

```python
limit_type='lower'      # value >= lower_limit
limit_type='upper'      # value <= upper_limit
limit_type='both'       # lower_limit <= value <= upper_limit
limit_type='equality'   # value == expected_value
limit_type='inequality' # value != expected_value
limit_type='partial'    # substring match (string values only)
limit_type='none'       # always PASS (no validation)

value_type='string'     # Cast to string, compare as strings
value_type='integer'    # Cast to int, numeric comparison
value_type='float'      # Cast to float, numeric comparison with tolerance
```

**Implementation:** `backend/app/measurements/base.py` lines 150-250

### 7.2 runAllTest Mode

Execution continues even after test failures, matching PDTool4 behavior:

```python
# In MeasurementService.execute_measurement()
errors = []
for test_item in test_plan_items:
    try:
        result = await measurement.execute(params)
        validate_result()  # May return FAIL, but continues
    except Exception as e:
        if not run_all_test:
            raise  # Stop on first error
        else:
            errors.append(e)  # Collect and continue
            result.status = 'ERROR'

# Frontend displays error_summary at session end
return {status: 'COMPLETED', final_result: 'FAIL', errors: errors}
```

### 7.3 Singleton Instrument Manager

Ensures single connection pool across all test executions:

```python
class InstrumentManager:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    async def connect(self, instrument_id: str):
        async with self._lock:
            # Reuse existing connection or create new
```

### 7.4 Async/Await Throughout

All I/O operations use async patterns:

```python
# Database operations
async def get_test_plan(db: AsyncSession, station_id: int):
    result = await db.execute(
        select(TestPlan).filter_by(station_id=station_id)
    )
    return result.scalars().all()

# Measurement execution
async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
    await instrument.send_command(cmd)
    result = await parse_response()
    return result

# Test orchestration
async def start_test_session(...):
    for test_item in items:
        result = await measurement_service.execute_measurement(...)
```

---

## 8. API Endpoint Structure

### Authentication Endpoints
```
POST   /api/auth/login                 # {username, password} → {access_token, user}
POST   /api/auth/logout                # Invalidate session
POST   /api/auth/refresh               # Refresh expired token
```

### User Management Endpoints
```
GET    /api/users                      # List users (paginated, filterable)
GET    /api/users/{id}                 # Get specific user
POST   /api/users                      # Create user (admin only)
PUT    /api/users/{id}                 # Update user
PUT    /api/users/{id}/password        # Change password
DELETE /api/users/{id}                 # Delete user (admin only)
```

### Project Management Endpoints
```
GET    /api/projects                   # List all projects
POST   /api/projects                   # Create project
PUT    /api/projects/{id}              # Update project
GET    /api/projects/{id}/stations     # Get project's stations
```

### Station Endpoints
```
GET    /api/stations                   # List stations (by project)
POST   /api/stations                   # Create station
GET    /api/stations/{id}/testplans    # Get station's test plans
```

### Test Plan Endpoints
```
GET    /api/testplans                  # List test plans
POST   /api/testplans                  # Create test plan
POST   /api/testplans/import           # Import from CSV
GET    /api/testplans/{id}             # Get test plan details
PUT    /api/testplans/{id}             # Update test plan
```

### Test Execution Endpoints
```
POST   /api/tests/sessions/start       # Start test session
  {serial_number, station_id, run_all_test}
GET    /api/tests/sessions/{id}/status # Get execution status
POST   /api/tests/sessions/{id}/pause  # Pause execution
POST   /api/tests/sessions/{id}/abort  # Abort execution
GET    /api/tests/sessions/{id}/results # Get test results
```

### Measurement Endpoints
```
GET    /api/measurements/instruments   # List instrument status
POST   /api/measurements/reset         # Reset instrument state
```

### Results & Reporting Endpoints
```
GET    /api/tests/results              # Query test results (filters)
GET    /api/tests/results/export       # Export results (CSV/PDF)
GET    /api/tests/reports/summary      # Session summary
GET    /api/tests/reports/analysis     # Statistical analysis
GET    /api/tests/reports/trending     # Pass rate trends
```

### DUT Control Endpoints
```
POST   /api/dut/reset                  # Reset device under test
POST   /api/dut/power                  # Control power relay
GET    /api/dut/status                 # Get DUT status
```

---

## 9. Frontend Component Overview

### View Component Relationships
```
Router
  ├─ Login.vue (unauthenticated)
  │   └─ on successful login → TestMain
  │
  ├─ TestMain.vue (dashboard)
  │   ├─ Real-time test execution
  │   ├─ Progress monitoring
  │   ├─ Error display (runAllTest)
  │   └─ Result visualization
  │
  ├─ TestPlanManage.vue (project manager role)
  │   ├─ CRUD test plans
  │   ├─ CSV import
  │   └─ Parameter editing
  │
  ├─ ProjectManage.vue (engineer role)
  │   ├─ Create/edit projects
  │   └─ Manage stations
  │
  ├─ UserManage.vue (admin role)
  │   ├─ Create/edit users
  │   ├─ Role assignment
  │   └─ Account status control
  │
  ├─ TestResults.vue (all roles)
  │   ├─ Filter/search results
  │   └─ Export functionality
  │
  ├─ TestHistory.vue
  │   ├─ Previous sessions
  │   └─ Trending analysis
  │
  ├─ ReportAnalysis.vue
  │   ├─ ECharts dashboards
  │   └─ Statistical breakdowns
  │
  ├─ TestExecution.vue
  │   └─ Detailed execution monitoring
  │
  └─ SystemConfig.vue
      └─ System-level settings
```

### Global State Management
```
Pinia Stores
  ├─ auth.js
  │   ├─ token (reactive)
  │   ├─ user (reactive)
  │   ├─ login(username, password)
  │   ├─ logout()
  │   └─ isAuthenticated (computed)
  │
  ├─ project.js
  │   ├─ projects[]
  │   ├─ currentProject
  │   ├─ currentStation
  │   └─ async fetchProjects()
  │
  └─ users.js
      ├─ users[]
      ├─ async fetchUsers()
      ├─ async createUser()
      └─ async updateUser()
```

---

## 10. Measurement System Implementation

### Measurement Lifecycle

Every measurement follows a three-phase lifecycle:

```python
class PowerReadMeasurement(BaseMeasurement):
    async def prepare(self, params: Dict[str, Any]) -> None:
        """
        Phase 1: Setup
        - Parse parameters (channel, range, tolerance)
        - Configure measurement equipment
        - Set timeouts
        """
        channel = params.get('channel', 1)
        range_val = params.get('range', 'AUTO')
        await self.instrument_manager.select_channel(channel)
        await self.instrument_manager.set_range(range_val)
    
    async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
        """
        Phase 2: Execute
        - Send commands to instrument
        - Collect raw data
        - Return measurement result
        """
        try:
            reading = await self.instrument.read_power()
            return MeasurementResult(
                value=reading,
                unit='V',
                timestamp=datetime.now(timezone.utc),
                success=True
            )
        except Exception as e:
            return MeasurementResult(
                value=None,
                error=str(e),
                success=False
            )
    
    async def cleanup(self) -> None:
        """
        Phase 3: Cleanup
        - Reset to safe state
        - Release resources
        - Log completion
        """
        await self.instrument.reset()
```

### Measurement Registry

Runtime registration system allows adding new measurement types:

```python
# backend/app/measurements/registry.py
MEASUREMENT_REGISTRY = {
    'PowerRead': PowerReadMeasurement,
    'PowerSet': PowerSetMeasurement,
    'CommandTest': CommandTestMeasurement,
    'SFCtest': SFCMeasurement,
    'getSN': GetSNMeasurement,
    'OPjudge': OPJudgeMeasurement,
    'Other': OtherMeasurement,
    # ... 13+ more types
}

# Usage
measurement_class = get_measurement_class(test_type)
measurement = measurement_class(instrument_manager)
result = await measurement.execute(params)
```

### Validation Example

```python
# Test Plan specifies:
# {value_type: 'float', limit_type: 'both', lower_limit: 4.5, upper_limit: 5.5}

# Measurement returns: 5.2V
# Validation logic in BaseMeasurement.validate_result():

is_valid, message = self.validate_result(
    measured_value=5.2,
    lower_limit=4.5,
    upper_limit=5.5,
    limit_type='both',
    value_type='float'
)
# Result: (True, "Within range 4.5-5.5V")

# If measured_value was 6.0V:
# Result: (False, "Exceeds upper limit 5.5V")
```

---

## 11. Service Layer Deep Dive

### TestEngine (Test Orchestration)
**File:** `backend/app/services/test_engine.py`

Core responsibilities:
- Manage test session lifecycle (PENDING → RUNNING → COMPLETED/FAILED/ABORTED)
- Iterate through test items
- Coordinate with MeasurementService
- Track execution timing and errors
- Implement runAllTest logic

**Key Methods:**
```python
async def start_test_session(session_id: int, serial_number: str, 
                             station_id: int, db: AsyncSession)
async def execute_test_item(test_plan_id: int, params: Dict)
async def pause_test_session(session_id: int)
async def abort_test_session(session_id: int)
async def complete_test_session(session_id: int, final_result: str)
```

### MeasurementService (Measurement Execution)
**File:** `backend/app/services/measurement_service.py`

Core responsibilities:
- Bridge TestEngine and measurement implementations
- Handle parameter validation
- Call measurement lifecycle methods
- Implement result validation
- Collect errors in runAllTest mode

**Key Methods:**
```python
async def execute_measurement(test_plan: TestPlan, params: Dict)
    → MeasurementResult
async def validate_measurement(result: MeasurementResult, 
                               test_plan: TestPlan) → Tuple[bool, str]
```

### InstrumentManager (Hardware Control)
**File:** `backend/app/services/instrument_manager.py`

Core responsibilities:
- Singleton pattern ensures single connection pool
- Manage instrument connections
- Queue and execute commands
- Track instrument status (IDLE/BUSY/ERROR/OFFLINE)
- Handle connection timeouts and errors

**Key Methods:**
```python
async def connect(instrument_id: str, config: Dict)
async def send_command(instrument_id: str, command: str) → str
async def get_status(instrument_id: str) → str
async def disconnect(instrument_id: str)
```

### ReportService (Analytics)
**File:** `backend/app/services/report_service.py`

Core responsibilities:
- Generate statistical reports
- Calculate pass rates
- Trending analysis
- Export functionality (CSV, PDF)

### AuthService (Authentication)
**File:** `backend/app/services/auth.py`

Core responsibilities:
- User authentication (username/password)
- JWT token generation and validation
- Password hashing (bcrypt)
- User role management

---

## 12. Security & Authentication

### JWT Token Flow
```
User Login
  ↓
POST /api/auth/login {username, password}
  ↓
AuthService.authenticate_user()
  ├─ Query User from database
  ├─ Verify password (bcrypt hash)
  └─ Generate JWT token with user claims
  ↓
Response: {access_token, token_type: "bearer", user}
  ↓
Frontend: Save to localStorage & Pinia store
  ↓
Subsequent Requests
  ├─ Axios interceptor adds: Authorization: Bearer <token>
  ├─ Backend validates token signature
  ├─ Extract user_id from claims
  └─ Grant/deny access based on role
```

### Password Security
- Stored as bcrypt hashes (10 rounds)
- Never transmitted in plain text
- Default passwords must be changed on first login (policy enforced)

### Role-Based Access Control (RBAC)
```
ADMIN
  └─ Full system access
      ├─ User management (create, edit, delete)
      ├─ Project management
      ├─ System configuration
      └─ All test operations

ENGINEER
  └─ Project-level access
      ├─ Test plan management
      ├─ Test execution
      ├─ Report viewing
      └─ NO: User management, system config

OPERATOR
  └─ Limited access
      ├─ Test execution only
      ├─ Result viewing
      └─ NO: Test plan creation, user management
```

### Token Configuration
- Expiration: 8 hours (ACCESS_TOKEN_EXPIRE_MINUTES=480)
- Secret key: Must be changed in production (min 32 characters)
- Algorithm: HS256
- Token refresh: Automatic refresh endpoint available

---

## 13. Testing & Development Workflow

### Test Configuration (`pytest.ini`)
```ini
[pytest]
asyncio_mode = auto
testpaths = tests/
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow = Tests requiring hardware
    fast = Unit tests only
    unit = Unit tests
    integration = Integration tests
    instrument_* = Tests for specific instruments
```

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Specific instrument tests
pytest -m instrument_34970a

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_api/test_auth.py

# Verbose output
pytest -v
```

### Test Files Structure
```
tests/
  ├─ conftest.py - Shared fixtures, database setup
  ├─ test_api/ - API endpoint tests
  ├─ test_services/ - Service layer tests
  ├─ test_measurements/ - Measurement implementation tests
  └─ test_instruments/ - Instrument driver tests
```

### Development Environment Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Docker (recommended for development)
docker-compose up -d
# Backend: http://localhost:9100
# Frontend: http://localhost:9080
# API Docs: http://localhost:9100/docs (Swagger UI)
```

---

## 14. Deployment Architecture

### Docker Services (`docker-compose.yml`)

```yaml
services:
  db:
    image: mysql:8.0
    ports: 33306:3306
    environment:
      MYSQL_ROOT_PASSWORD, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
    volumes: database/schema.sql initial setup

  redis:
    image: redis:7
    ports: 6379:6379
    purpose: Logging, real-time data streaming

  backend:
    build: backend/
    ports: 9100:9100
    environment:
      DATABASE_URL, SECRET_KEY, REDIS_URL, DEBUG
    depends_on: db, redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 9100

  frontend:
    build: frontend/
    ports: 9080:9080
    depends_on: backend
    # Nginx reverse proxy serving Vue SPA

  nginx:
    image: nginx:alpine
    ports: 80:80, 443:443
    configuration: nginx.conf
    purpose: Reverse proxy for frontend/backend routing
```

### Environment Variables
```bash
# Backend (.env)
DATABASE_URL=mysql+asyncmy://pdtool:pdtool123@db:3306/webpdtool
SECRET_KEY=<32+ character secret>
ACCESS_TOKEN_EXPIRE_MINUTES=480
DEBUG=false
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO

# Database (docker-compose.yml)
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=webpdtool
MYSQL_USER=pdtool
MYSQL_PASSWORD=pdtool123

# Ports
FRONTEND_PORT=9080
BACKEND_PORT=9100
MYSQL_PORT=33306
```

---

## 15. Key Statistics & Metrics

### Codebase Size
- **Backend:** ~15,000 lines (Python)
- **Frontend:** ~8,000 lines (Vue 3/JavaScript)
- **Database:** ~2,000 lines (SQL schema)
- **Tests:** ~5,000 lines

### Component Distribution
- **ORM Models:** 7 tables with ~100 columns total
- **API Routers:** 9 main routers + 7 sub-routers (40+ endpoints)
- **Measurement Types:** 20+ implementations
- **Frontend Views:** 10 main views
- **Pinia Stores:** 3 central stores
- **Services:** 6 core service classes

### Performance Characteristics
- **Async I/O:** All database and instrument communication
- **Connection Pooling:** Singleton InstrumentManager
- **Batch Operations:** CSV import in single transaction
- **Real-time Logging:** Redis streaming (optional)
- **Session Management:** In-memory state tracking

---

## 16. Known Limitations & Technical Debt

### Current Limitations
1. **Instrument Drivers:** Mostly stub implementations, need real hardware drivers
2. **Real-time Updates:** Uses polling instead of WebSocket (WebSocket planned)
3. **Modbus/SFC Integration:** Stub implementations only
4. **Error Recovery:** Limited retry logic for hardware failures
5. **Distributed Testing:** Single-instance deployment (clustering not implemented)

### Technical Debt Areas
1. **Legacy PDTool4 Code:** Large `PDTool4/` directory with old desktop app (refactoring in progress)
2. **Type Hints:** Some files lack complete type annotations
3. **Error Messages:** Could be more user-friendly with context
4. **Documentation:** API-level comments sparse (Swagger docs available)

### Planned Improvements
- WebSocket support for real-time test monitoring
- Enhanced error recovery with exponential backoff
- Multi-station parallel execution
- Advanced analytics dashboard (ReportAnalysis in progress)
- Hardware abstraction layer improvements

---

## 17. Development Best Practices

### Code Style Guidelines

**Backend (Python):**
- Async/await for all I/O operations
- Type hints on all functions (use `Dict[str, Any]`, `Optional[Type]`)
- PascalCase for classes, snake_case for functions/variables
- Docstrings for public functions
- Use FastAPI HTTPException for API errors
- Use custom exceptions from `app.core.exceptions`

**Frontend (Vue 3):**
- Composition API (`<script setup>`) for all new components
- Reactive state with `ref()` and `computed()`
- Named imports for components: `import { ElButton } from 'element-plus'`
- camelCase for functions/variables, kebab-case for CSS classes
- Centralized API calls through `frontend/src/api/` clients
- Pinia stores for global state

### File Organization

```
backend/
  app/
    api/            # FastAPI routers
    services/       # Business logic
    measurements/   # Measurement abstraction
    models/         # SQLAlchemy ORM
    schemas/        # Pydantic validation
    core/           # Core utilities
    config/         # Configuration

frontend/
  src/
    views/          # Page components
    components/     # Reusable components
    stores/         # Pinia state
    api/            # Axios clients
    router/         # Vue Router config
    utils/          # Utilities
    assets/         # Static assets
```

### Adding New Features

1. **New Measurement Type:**
   - Create class in `app/measurements/implementations.py`
   - Inherit from `BaseMeasurement`
   - Register in `app/measurements/registry.py`
   - Update test plan CSV with new `test_type`

2. **New API Endpoint:**
   - Add route in appropriate router (`app/api/*`)
   - Implement business logic in service layer
   - Update frontend API client (`frontend/src/api/`)
   - Add Pydantic schema if needed

3. **Frontend View:**
   - Create `.vue` file in `frontend/src/views/`
   - Use Composition API (`<script setup>`)
   - Use Element Plus components for consistency
   - Add route in `frontend/src/router/`

---

## 18. Architecture Decisions & Rationale

### Why Async/Await Throughout?
- Test execution involves many I/O operations (hardware, database, network)
- Python's asyncio enables efficient concurrent test execution
- FastAPI's async support matches Python's native async patterns
- SQLAlchemy 2.0's async ORM is fully featured and performant

### Why Measurement Abstraction Layer?
- PDTool4 has complex, domain-specific validation logic
- Abstraction allows pluggable measurement implementations
- Easy to add new instrument types without core changes
- Clear separation between measurement logic and orchestration

### Why Pinia + Axios Centralization?
- Single source of truth for application state
- Centralized API client simplifies error handling
- JWT token management in one place
- Easier to add features (logging, analytics) to all API calls

### Why SQLAlchemy 2.0 ORM?
- Modern async support matches FastAPI patterns
- Type-safe queries (Session.execute with select())
- Automatic relationship loading (lazy loading, eager loading)
- Migration management via Alembic
- Multi-database compatibility (MySQL, PostgreSQL, etc.)

### Why Docker Compose?
- Developers get production-like environment locally
- Services isolated in containers
- Easy dependency management (database, redis)
- CI/CD integration straightforward
- Education & troubleshooting with `docker-compose logs`

---

## 19. Testing Strategy

### Unit Tests (`tests/test_*.py`)
- Measurement validation logic
- Service layer business rules
- API request/response validation

### Integration Tests
- Database operations with AsyncSession
- Multi-service interactions (TestEngine + MeasurementService)
- API endpoints with real database

### End-to-End Tests
- Complete test session execution
- CSV import → test execution → result export
- Authentication flow → test execution → logout

### Hardware Tests
- Marked with `@pytest.mark.hardware`
- Require actual instruments or mocks
- Skipped in CI if no hardware available

---

## 20. Quick Reference

### Common Commands

**Backend:**
```bash
# Development server (with hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# Run tests
pytest
pytest tests/test_api/test_auth.py::test_login_success -v
pytest --cov=app tests/

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

**Frontend:**
```bash
# Development server
npm run dev

# Production build
npm run build

# Preview build
npm run preview
```

**Docker:**
```bash
docker-compose up -d      # Start all services
docker-compose down       # Stop all services
docker-compose logs -f backend    # View backend logs
docker-compose exec backend pytest # Run tests in container
```

### API Documentation
- Swagger UI: http://localhost:9100/docs
- ReDoc: http://localhost:9100/redoc
- OpenAPI schema: http://localhost:9100/openapi.json

### Database Access
```bash
# Direct MySQL connection
mysql -h localhost -P 33306 -u pdtool -p webpdtool

# Through Docker container
docker-compose exec db mysql -uroot -p<password> webpdtool

# Useful queries
SELECT * FROM users;
SELECT * FROM test_sessions ORDER BY created_at DESC;
SELECT COUNT(*) as pass_count FROM test_results WHERE validation_result='PASS';
```

---

## Summary

WebPDTool is a well-architected web-based testing system that successfully refactors PDTool4's functionality into a modern, maintainable web application. Key strengths include:

✅ **Clean Architecture:** Clear separation of concerns (API, Service, Measurement, Data layers)
✅ **Async-First Design:** Efficient concurrent operations via asyncio
✅ **PDTool4 Compatibility:** Measurement abstraction replicates complex validation logic exactly
✅ **Developer Experience:** Docker environment, comprehensive logging, clear code organization
✅ **Scalability:** Async patterns support many concurrent tests
✅ **Maintainability:** Modular components, centralized API clients, reusable services

The codebase is production-ready with opportunities for enhancement in real-time monitoring (WebSocket), advanced analytics, and hardware integration improvements.

