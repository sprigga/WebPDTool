# Backend Architecture - Complete Analysis

This document provides a comprehensive analysis of the WebPDTool backend architecture, including detailed UML diagrams following the Mermaid style guide.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Analysis](#module-analysis)
3. [UML Diagrams](#uml-diagrams)
4. [Request Flows](#request-flows)
5. [Design Patterns](#design-patterns)

---

## Architecture Overview

### Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3)                        │
│                  Element Plus + Pinia                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│                    SQLAlchemy 2.0+                          │
│                    Pydantic 2.0+                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database (MySQL 8.0)                    │
│                      utf8mb4 charset                        │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
backend/app/
├── api/                    # API router layer (FastAPI routes)
├── core/                   # Core infrastructure
├── models/                 # SQLAlchemy ORM models (7 tables)
├── schemas/                # Pydantic validation schemas
├── services/               # Business logic layer
├── measurements/           # Measurement abstraction layer
├── utils/                  # Utilities (CSV parser, helpers)
├── instrumentation/        # Instrument drivers (23 drivers)
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
└── dependencies.py         # Dependency injection
```

---

## Module Analysis

### 1. Core Module (`app/core/`)

**Purpose:** Infrastructure and shared utilities

| File | Purpose |
|------|---------|
| `database.py` | Async database connection pooling |
| `security.py` | JWT authentication and password hashing |
| `logging.py` | Application logging setup |
| `api_helpers.py` | API utilities to reduce duplication |
| `exceptions.py` | Custom exception definitions |
| `constants.py` | Static constants and messages |
| `measurement_constants.py` | PDTool4 compatibility constants |

### 2. Models Module (`app/models/`)

**Purpose:** SQLAlchemy ORM database models

**7 Database Tables:**
- `users` - User accounts with roles
- `projects` - Test projects
- `stations` - Test stations
- `test_plans` - Test plan definitions
- `test_sessions` - Test execution sessions
- `test_results` - Individual test results
- `sfc_logs` - SFC web service logs

### 3. Schemas Module (`app/schemas/`)

**Purpose:** Pydantic validation models for request/response

| Schema File | Purpose |
|-------------|---------|
| `user.py` | User authentication models |
| `project.py` | Project management |
| `station.py` | Station management |
| `testplan.py` | Test plan CRUD |
| `test_session.py` | Test session handling |
| `test_result.py` | Test result display |
| `measurement.py` | Instrument API models |

### 4. API Module (`app/api/`)

**Purpose:** FastAPI router layer with endpoints

**API Routers:**
- `auth.py` - Authentication (login/logout)
- `projects.py` - Project CRUD
- `stations.py` - Station CRUD
- `testplan/` - Test plan endpoints
- `tests.py` - Test execution endpoints
- `measurements.py` - Instrument management
- `results/` - Results endpoints

### 5. Services Module (`app/services/`)

**Purpose:** Business logic layer

| Service | Purpose |
|---------|---------|
| `test_engine.py` | Orchestrates async test execution |
| `measurement_service.py` | Core measurement dispatch logic (2,103 lines) |
| `test_plan_service.py` | Test plan management (933 lines) |
| `instrument_manager.py` | Instrument connection pooling |
| `instrument_connection.py` | Base instrument connection protocol |
| `report_service.py` | Automatic CSV report generation |
| `dut_comms/` | DUT communication (relay, chassis) |
| `instruments/` | Hardware drivers (23 drivers) |

### 6. Measurements Module (`app/measurements/`)

**Purpose:** Measurement abstraction layer (PDTool4 compatibility)

**Components:**
- `base.py` - Abstract base class `BaseMeasurement` and `MeasurementResult`
- `implementations.py` - Concrete measurement implementations and `MEASUREMENT_REGISTRY` dictionary
- `__init__.py` - Package exports and public API

---

## UML Diagrams

### Package Structure Diagram

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
graph TB
    subgraph Backend["backend/app/"]
        direction TB
        API[api/]
        Core[core/]
        Models[models/]
        Schemas[schemas/]
        Services[services/]
        Measurements[measurements/]
        Utils[utils/]
        Main[main.py]
        Config[config.py]
        Dep[dependencies.py]

        subgraph API_Sub["API Layer"]
            AuthAPI[auth.py]
            ProjectsAPI[projects.py]
            StationsAPI[stations.py]
            TestplanAPI[testplan/]
            TestsAPI[tests.py]
            MeasurementsAPI[measurements.py]
            ResultsAPI[results/]
        end

        subgraph Services_Sub["Service Layer"]
            TestEngine[test_engine.py]
            MeasurementService[measurement_service.py]
            TestPlanService[test_plan_service.py]
            InstrumentManager[instrument_manager.py]
            ReportService[report_service.py]
            DUTComms[dut_comms/]
            Instruments[instruments/]
        end

        subgraph Measurements_Sub["Measurement Layer"]
            Base[base.py]
            Implementations["implementations.py<br/>(includes MEASUREMENT_REGISTRY)"]
            Init[__init__.py]
        end
    end

    API --> API_Sub
    Services --> Services_Sub
    Measurements --> Measurements_Sub
    Core --> Database[database.py]
    Core --> Security[security.py]
    Core --> Logging[logging.py]
```

### Class Diagram - Core Components

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
classDiagram
    class TestEngine {
        <<Service>>
        +async execute_test_session()
        +async execute_single_test()
        +async run_all_tests()
        +update_session_status()
        -_execute_test_loop()
    }

    class MeasurementService {
        <<Service>>
        +execute_measurement()
        +validate_result()
        -_execute_power_set()
        -_execute_power_read()
        -_execute_command_test()
        -_execute_sfc_test()
        -measurement_dispatch
    }

    class InstrumentManager {
        <<Singleton>>
        +get_instrument()
        +connect_instrument()
        +disconnect_instrument()
        -_connection_pool
        -_state_lock
    }

    class TestPlanService {
        <<Service>>
        +create_test_plan()
        +get_test_plan()
        +delete_test_plan()
        +validate_unique_id()
        -test_plan_map
    }

    class ReportService {
        <<Service>>
        +save_session_report()
        +generate_csv()
        -_build_report_path()
    }

    class BaseMeasurement {
        <<Abstract>>
        +async prepare(params)
        +async execute(params) MeasurementResult
        +async cleanup()
        +validate_result() Tuple[bool, str]
        #item_no
        #item_name
        #test_type
    }

    class MeasurementResult {
        <<Dataclass>>
        +success: bool
        +value: Any
        +error_message: Optional[str]
        +execution_duration_ms: int
    }

    class MEASUREMENT_REGISTRY {
        <<Dict>>
        +POWER_SET: PowerSetMeasurement
        +POWER_READ: PowerReadMeasurement
        +COMMAND_TEST: CommandTestMeasurement
        +get_measurement_class(test_command) type
    }

    TestEngine --> MeasurementService : uses
    TestEngine --> TestPlanService : queries
    MeasurementService --> MEASUREMENT_REGISTRY : lookup
    MeasurementService --> BaseMeasurement : creates
    MeasurementService --> InstrumentManager : uses
    MeasurementService --> MeasurementResult : returns
    BaseMeasurement <|-- PowerSetMeasurement
    BaseMeasurement <|-- PowerReadMeasurement
    BaseMeasurement <|-- CommandTestMeasurement
    BaseMeasurement <|-- SFCtestMeasurement
    MEASUREMENT_REGISTRY --> BaseMeasurement : manages
```

### Database Entity Relationship Diagram

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
erDiagram
    users ||--o{ test_sessions : "executes"
    projects ||--o{ stations : "has"
    projects ||--o{ test_plans : "has"
    stations ||--o{ test_plans : "contains"
    stations ||--o{ test_sessions : "uses"
    test_sessions ||--o{ test_results : "generates"
    test_sessions ||--o{ sfc_logs : "logs"
    test_plans ||--o{ test_results : "references"

    users {
        int id PK
        varchar username UK
        varchar password_hash
        enum role "ADMIN/ENGINEER/OPERATOR"
        varchar full_name
        boolean is_active
        timestamp created_at
    }

    projects {
        int id PK
        varchar project_code UK
        varchar project_name
        text description
        boolean is_active
        timestamp created_at
    }

    stations {
        int id PK
        int project_id FK
        varchar station_code
        varchar station_name
        varchar ip_address
        boolean is_active
        timestamp created_at
    }

    test_plans {
        int id PK
        int station_id FK
        int project_id FK
        int item_no
        varchar item_name
        varchar item_key
        varchar test_type
        json parameters
        decimal lower_limit
        decimal upper_limit
        varchar limit_type
        varchar value_type
        varchar eq_limit
        varchar unit
        boolean enabled
        int sequence_order
        int timeout
        timestamp created_at
    }

    test_sessions {
        int id PK
        int project_id FK
        int station_id FK
        int user_id FK
        int test_plan_id FK
        varchar serial_number
        enum status "PENDING/RUNNING/COMPLETED/FAILED/ABORTED"
        enum final_result "PASS/FAIL/ABORT"
        timestamp start_time
        timestamp end_time
        int total_items
        int pass_items
        int fail_items
        timestamp created_at
    }

    test_results {
        bigint id PK
        int test_session_id FK
        int test_plan_id FK
        int item_no
        varchar item_name
        decimal measured_value
        decimal lower_limit
        decimal upper_limit
        enum result "PASS/FAIL/ERROR"
        text error_message
        int execution_duration_ms
        timestamp test_time
    }

    sfc_logs {
        bigint id PK
        int test_session_id FK
        varchar log_type
        json log_data
        timestamp created_at
    }
```

### API Endpoint Flow Diagram

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
flowchart LR
    subgraph Client["Frontend Client"]
        Vue[Vue 3 App]
    end

    subgraph API["API Layer"]
        Auth[POST /api/auth/login]
        Projects[GET /api/projects]
        Stations[GET /api/stations]
        TestPlanUpload[POST /api/testplan/upload]
        SessionStart[POST /api/tests/sessions/start]
        SessionStatus[GET /api/tests/sessions/:id/status]
        SessionResults[GET /api/tests/sessions/:id/results]
        Instruments[GET /api/measurements/instruments]
        ResultsList[GET /api/results/sessions]
    end

    subgraph Service["Service Layer"]
        AuthService[AuthService]
        TestEngine[TestEngine]
        MeasurementService[MeasurementService]
        InstrumentManager[InstrumentManager]
        TestPlanService[TestPlanService]
        ReportService[ReportService]
    end

    subgraph Data["Data Layer"]
        DB[(MySQL Database)]
        Instruments[(Hardware Instruments)]
    end

    Vue --> Auth
    Vue --> Projects
    Vue --> Stations
    Vue --> TestPlanUpload
    Vue --> SessionStart
    Vue --> SessionStatus
    Vue --> SessionResults
    Vue --> Instruments
    Vue --> ResultsList

    Auth --> AuthService
    AuthService --> DB

    Projects --> DB
    Stations --> DB

    TestPlanUpload --> TestPlanService
    TestPlanService --> DB

    SessionStart --> TestEngine
    TestEngine --> DB
    TestEngine --> MeasurementService
    MeasurementService --> InstrumentManager
    InstrumentManager --> Instruments

    SessionStatus --> TestEngine
    SessionResults --> DB

    Instruments --> InstrumentManager

    ResultsList --> DB

    TestEngine --> ReportService
    ReportService --> DB
```

### Sequence Diagram - Test Execution Flow

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "sequence": {
    "diagramMarginX": 50,
    "diagramMarginY": 10,
    "actorMargin": 50,
    "width": 150,
    "height": 65,
    "boxMargin": 10,
    "messageMargin": 35,
    "noteMargin": 10,
    "activationMargin": 5
  }
}}%%
sequenceDiagram
    participant User as 👤 User
    participant Frontend as Vue Frontend
    participant API as FastAPI
    participant Engine as TestEngine
    participant MeasureSvc as MeasurementService
    participant Instrument as InstrumentManager
    participant Hardware as Hardware
    participant DB as Database

    User->>Frontend: 1. Input serial number
    Frontend->>API: 2. POST /api/tests/sessions/start
    API->>DB: 3. Create test_session (PENDING)
    DB-->>API: 4. Return session_id
    API-->>Frontend: 5. Return session_id

    Frontend->>API: 6. POST /api/tests/sessions/{id}/start
    API->>Engine: 7. execute_test_session()
    Engine->>DB: 8. Update status (RUNNING)

    loop For each test point
        Engine->>MeasureSvc: 9. execute_measurement()
        MeasureSvc->>MeasureSvc: 10. Get measurement class

        MeasureSvc->>MeasureSvc: 11. prepare(params)
        MeasureSvc->>Instrument: 12. Get instrument connection
        Instrument-->>MeasureSvc: 13. Return connection

        MeasureSvc->>Hardware: 14. Execute measurement
        Hardware-->>MeasureSvc: 15. Return value

        MeasureSvc->>MeasureSvc: 16. validate_result()
        MeasureSvc->>MeasureSvc: 17. cleanup()

        MeasureSvc-->>Engine: 18. Return MeasurementResult
        Engine->>DB: 19. Save test_result
    end

    Engine->>DB: 20. Update session (COMPLETED)
    Engine->>DB: 21. Update statistics
    Engine-->>API: 22. Return final status

    API-->>Frontend: 23. Return completion status
    Frontend->>Frontend: 24. Display results

    Note over Engine,DB: runAllTest mode:<br/>continues on failures
```

### Component Diagram - Measurement Abstraction

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
flowchart TB
    subgraph Input["Test Request"]
        CSV[CSV Test Plan]
        APIRequest[API Request]
    end

    subgraph Registry["Measurement Registry<br/>(in implementations.py)"]
        Reg["MEASUREMENT_REGISTRY<br/>(Dict)"]
        GetClass["get_measurement_class()<br/>(Function with alias support)"]
    end

    subgraph Abstraction["Measurement Abstraction Layer"]
        Base[BaseMeasurement]
        Prepare[prepare]
        Execute[execute]
        Cleanup[cleanup]
        Validate[validate_result]
    end

    subgraph Implementations["Concrete Implementations"]
        PowerSet[PowerSetMeasurement]
        PowerRead[PowerReadMeasurement]
        CommandTest[CommandTestMeasurement]
        SFCtest[SFCtestMeasurement]
        GetSN[GetSNMeasurement]
        OPjudge[OPJudgeMeasurement]
        Other[OtherMeasurement]
    end

    subgraph Output["Measurement Result"]
        Result[MeasurementResult]
        Value[measured_value]
        Success[success]
        Error[error_message]
        Duration[execution_duration_ms]
    end

    CSV --> GetClass
    APIRequest --> GetClass
    GetClass --> Reg
    Reg --> Base

    Base --> Prepare
    Base --> Execute
    Base --> Cleanup
    Base --> Validate

    Base -.-> PowerSet
    Base -.-> PowerRead
    Base -.-> CommandTest
    Base -.-> SFCtest
    Base -.-> GetSN
    Base -.-> OPjudge
    Base -.-> Other

    PowerSet --> Result
    PowerRead --> Result
    CommandTest --> Result
    SFCtest --> Result
    GetSN --> Result
    OPjudge --> Result
    Other --> Result

    Result --> Value
    Result --> Success
    Result --> Error
    Result --> Duration

    style Base fill:#E8F5E9
    style Result fill:#FFF3E0
    style Reg fill:#E3F2FD
```

### State Machine - Test Session

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "state": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80
  }
}}%%
stateDiagram-v2
    [*] --> PENDING: create_session()

    PENDING --> RUNNING: start_execution()
    PENDING --> ABORTED: cancel_before_start()

    RUNNING --> COMPLETED: all_tests_passed()
    RUNNING --> FAILED: any_test_failed()
    RUNNING --> ABORTED: user_cancel()
    RUNNING --> ERROR: execution_error()

    note right of RUNNING
        runAllTest mode:
        - Continues on failures
        - Collects all errors
        - Reports at end
    end note

    COMPLETED --> [*]
    FAILED --> [*]
    ABORTED --> [*]
    ERROR --> [*]

    classDef active fill:#E8F5E9,stroke:#4CAF50
    classDef error fill:#FFEBEE,stroke:#F44336
    classDef warning fill:#FFF3E0,stroke:#FF9800

    class RUNNING active
    class FAILED,ERROR error
    class ABORTED warning
```

---

## Request Flows

### 1. Authentication Flow

```
User → Login.vue
  ↓ POST /api/auth/login
AuthAPI → AuthService
  ↓ verify_password()
Database → User record
  ↓ create_access_token()
AuthService → JWT Token
  ↓ Return to frontend
Frontend → Store in Pinia + localStorage
  ↓ Add to Axios interceptor
All subsequent requests → Include Authorization header
```

### 2. Test Plan Import Flow

```
TestPlanManage.vue
  ↓ POST /api/testplan/upload (with CSV file)
TestPlanAPI → TestPlanCSVParser
  ↓ parse_csv_file()
CSV Parser → TestPlanCSVRow[]
  ↓ csv_row_to_testplan_dict()
TestPlanService → validate_unique_id()
  ↓ For each row:
    ↓ Create TestPlan model
    ↓ Add to database
  ↓ Commit transaction
  ↓ Return upload statistics
```

### 3. Test Execution Flow (runAllTest mode)

```
TestMain.vue
  ↓ POST /api/tests/sessions/start
TestsAPI → TestEngine.execute_test_session()
  ↓ Create session (PENDING)
  ↓ Update to RUNNING
  ↓ For each test point:
    ↓ MeasurementService.execute_measurement()
    ↓ Get measurement class from registry
    ↓ measurement.prepare()
    ↓ measurement.execute()
    ↓ validate_result() (PDTool4 logic)
    ↓ measurement.cleanup()
    ↓ Save test_result
    ↓ runAllTest: continue on failure
  ↓ Update session (COMPLETED/FAILED)
ReportService → Auto-save CSV report
  ↓ Return session status
```

---

## Design Patterns

### 1. Measurement Abstraction Pattern

```python
# Base class defines interface
class BaseMeasurement(ABC):
    @abstractmethod
    async def prepare(self, params): pass
    @abstractmethod
    async def execute(self, params): pass
    @abstractmethod
    async def cleanup(self): pass

# Concrete implementations
class PowerSetMeasurement(BaseMeasurement):
    async def execute(self, params):
        # PowerSet-specific logic
        pass
```

### 2. Registry Pattern

```python
# Dictionary-based registry in implementations.py
MEASUREMENT_REGISTRY = {
    "POWER_SET": PowerSetMeasurement,
    "POWER_READ": PowerReadMeasurement,
    "COMMAND_TEST": CommandTestMeasurement,
    # ... other measurement types
}

# Lookup with alias support via get_measurement_class()
cls = get_measurement_class('PowerSet')  # Supports aliases
measurement = cls()
```

### 3. Singleton Pattern (InstrumentManager)

```python
# Ensures single connection pool
instrument_manager = InstrumentManager()
instance = instrument_manager.get_instrument(instrument_id)
```

### 4. Dependency Injection (FastAPI)

```python
@router.get("/sessions")
async def get_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    # Use injected dependencies
    pass
```

### 5. Strategy Pattern (Limit Validation)

```python
LIMIT_TYPE_MAP = {
    'lower': LOWER_LIMIT_TYPE,
    'upper': UPPER_LIMIT_TYPE,
    'both': BOTH_LIMIT_TYPE,
    # ... 7 limit types
}
```

---

## Key Statistics

| Metric | Value |
|--------|-------|
| Total Backend Code | 24,190 lines |
| API Endpoints | ~50 endpoints |
| Database Tables | 7 tables |
| Measurement Types | 13 types |
| Instrument Drivers | 23 drivers |
| Limit Types | 7 types |
| Value Types | 3 types |

---

## Extensibility

### Adding a New Measurement Type

1. Create class in `measurements/implementations.py`:
   ```python
   class NewMeasurement(BaseMeasurement):
       async def prepare(self, params: Dict[str, Any]) -> None:
           # Setup logic
           pass

       async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
           # Execution logic
           return MeasurementResult(success=True, value=result)

       async def cleanup(self) -> None:
           # Cleanup logic
           pass
   ```

2. Register in `MEASUREMENT_REGISTRY` dictionary (same file):
   ```python
   MEASUREMENT_REGISTRY = {
       # ... existing entries
       "NEW_TYPE": NewMeasurement,
   }
   ```

3. Update command mapping in `get_measurement_class()` if needed for aliases

4. Use in test plan CSV with `test_type=NEW_TYPE` or alias

5. Export from `__init__.py` if needed in other modules

### Adding a New Instrument Driver

1. Create class in `services/instruments/`
2. Inherit from `BaseInstrumentDriver`
3. Register in `INSTRUMENT_DRIVERS` dict
4. Use in measurement implementations

---

`★ Insight ─────────────────────────────────────`
1. The **measurement abstraction layer** is the core of PDTool4 compatibility - it enables runtime registration of new test types without modifying core code
2. **Dictionary-based registry** (MEASUREMENT_REGISTRY) with `get_measurement_class()` function provides flexible lookup with alias support, making the system highly extensible
3. **Three-phase execution** (prepare → execute → cleanup) ensures proper resource management and hardware state control
4. **Co-located design** - Registry and implementations in the same file (`implementations.py`) simplifies the architecture for this scale of system
`─────────────────────────────────────────────────`
