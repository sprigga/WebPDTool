# Backend Request Flows - Sequence Diagrams

This document provides detailed sequence diagrams for all major request flows in the WebPDTool backend.

---

## Table of Contents

1. [Authentication Flow](#1-authentication-flow)
2. [Test Plan Import Flow](#2-test-plan-import-flow)
3. [Test Execution Flow (Normal Mode)](#3-test-execution-flow-normal-mode)
4. [Test Execution Flow (runAllTest Mode)](#4-test-execution-flow-runalltest-mode)
5. [Measurement Execution Flow](#5-measurement-execution-flow)
6. [Instrument Connection Flow](#6-instrument-connection-flow)
7. [Results Query Flow](#7-results-query-flow)
8. [CSV Export Flow](#8-csv-export-flow)

---

## 1. Authentication Flow

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
    participant AuthAPI as Auth API
    participant AuthService as AuthService
    participant Security as Security Module
    participant DB as Database

    User->>Frontend: 1. Enter credentials
    Frontend->>AuthAPI: 2. POST /api/auth/login\n{username, password}
    activate AuthAPI

    AuthAPI->>AuthService: 3. authenticate_user()
    activate AuthService

    AuthService->>DB: 4. SELECT * FROM users\nWHERE username = ?
    activate DB
    DB-->>AuthService: 5. User record or None
    deactivate DB

    alt User found
        AuthService->>Security: 6. verify_password()\n(input, hashed_password)
        activate Security
        Security-->>AuthService: 7. True/False
        deactivate Security

        alt Password valid
            AuthService->>Security: 8. create_access_token()\n(data, expires_delta)
            activate Security
            Security-->>AuthService: 9. JWT token string
            deactivate Security

            AuthService-->>AuthAPI: 10. Return access_token
        else Password invalid
            AuthService-->>AuthAPI: 10a. Raise HTTPException(401)
        end
    else User not found
        AuthService-->>AuthAPI: 10b. Raise HTTPException(401)
    end

    deactivate AuthService

    alt Token generated
        AuthAPI-->>Frontend: 11. Return {access_token, token_type}
        Frontend->>Frontend: 12. Store in localStorage\nand Pinia store
        Frontend->>Frontend: 13. Set Axios interceptor\nAuthorization: Bearer <token>
        Frontend-->>User: 14. Redirect to dashboard
    else Authentication failed
        AuthAPI-->>Frontend: 11a. Return error detail
        Frontend-->>User: 14a. Display error message
    end

    deactivate AuthAPI

    Note over Frontend,DB: JWT tokens expire after 8 hours\n(ACCESS_TOKEN_EXPIRE_MINUTES=480)
```

---

## 2. Test Plan Import Flow

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
    participant Frontend as TestPlanManage.vue
    participant API as TestPlan API
    participant Parser as CSV Parser
    participant Service as TestPlanService
    participant DB as Database

    User->>Frontend: 1. Select CSV file
    Frontend->>API: 2. POST /api/testplan/upload\nFormData{file, replace_existing}
    activate API

    API->>API: 3. Validate file type (.csv)
    API->>API: 4. Read file content (bytes)

    API->>Parser: 5. parse_and_convert()\n(file_content, station_id, project_id)
    activate Parser

    Parser->>Parser: 6. Decode bytes to string
    Parser->>Parser: 7. Create CSV DictReader

    loop For each CSV row
        Parser->>Parser: 8. csv_row_to_testplan_dict()
        Note over Parser: Map PDTool4 columns:\n- ItemKey → item_key\n- LL → lower_limit\n- UL → upper_limit\n- LimitType → limit_type\n- ValueType → value_type\n- ExecuteName → test_type

        Parser->>Parser: 9. Parse limits (float)
        Parser->>Parser: 10. Parse timeout/wait_msec (int)
        Parser->>Parser: 11. Build parameters JSON
    end

    Parser-->>API: 12. Return List[TestPlanDict]
    deactivate Parser

    alt replace_existing = true
        API->>Service: 13. delete_station_testplans()
        activate Service
        Service->>DB: 14. DELETE FROM test_plans\nWHERE station_id = ?
        DB-->>Service: 15. Delete count
        Service-->>API: 16. Confirm deleted
        deactivate Service
    end

    API->>Service: 17. bulk_create_testplans()\n(test_plan_dicts)
    activate Service

    loop For each test_plan_dict
        Service->>Service: 18. validate_unique_id()\n(item_no, station_id)
        Service->>DB: 19. Check existing
        DB-->>Service: 20. Exists or not

        alt Unique ID exists
            Service->>Service: 21a. Skip or update
        else Unique ID available
            Service->>DB: 21b. INSERT INTO test_plans
        end
    end

    Service->>DB: 22. COMMIT transaction
    DB-->>Service: 23. Confirm committed
    Service-->>API: 24. Return created count
    deactivate Service

    API-->>Frontend: 25. Return {created, updated, failed}
    deactivate API

    Frontend-->>User: 26. Display success message

    Note over Frontend,DB: CSV columns expected:\nID, ItemKey, ValueType, LimitType,\nEqLimit, LL, UL, ExecuteName, etc.
```

---

## 3. Test Execution Flow (Normal Mode)

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
    participant Frontend as TestMain.vue
    participant API as Tests API
    participant Engine as TestEngine
    participant MeasureSvc as MeasurementService
    participant Instrument as InstrumentManager
    participant Hardware as Test Instruments
    participant DB as Database
    participant Report as ReportService

    User->>Frontend: 1. Input serial number
    Frontend->>API: 2. POST /api/tests/sessions/start\n{serial_number, station_id, project_id}
    activate API

    API->>DB: 3. INSERT INTO test_sessions\n(status=PENDING)
    activate DB
    DB-->>API: 4. Return session_id
    deactivate DB

    API-->>Frontend: 5. Return {session_id, status}
    deactivate API

    Frontend->>API: 6. POST /api/tests/sessions/{id}/start
    activate API

    API->>Engine: 7. execute_test_session(session_id)
    activate Engine

    Engine->>DB: 8. UPDATE test_sessions\nSET status=RUNNING
    activate DB
    DB-->>Engine: 9. Confirm updated
    deactivate DB

    Engine->>DB: 10. SELECT * FROM test_plans\nWHERE station_id=? ORDER BY sequence_order
    activate DB
    DB-->>Engine: 11. Return test plans
    deactivate DB

    loop For each test point
        Engine->>MeasureSvc: 12. execute_measurement(test_plan)
        activate MeasureSvc

        MeasureSvc->>MeasureSvc: 13. Get measurement class\nfrom registry

        MeasureSvc->>MeasureSvc: 14. measurement.prepare(params)
        Note over MeasureSvc: Configure parameters,\nsetup instrument

        MeasureSvc->>Instrument: 15. Get instrument connection
        activate Instrument
        Instrument-->>MeasureSvc: 16. Return connection
        deactivate Instrument

        MeasureSvc->>Hardware: 17. Execute measurement\nvia instrument driver
        activate Hardware
        Hardware-->>MeasureSvc: 18. Return measured value
        deactivate Hardware

        MeasureSvc->>MeasureSvc: 19. validate_result()\n(PDTool4 logic)

        MeasureSvc->>MeasureSvc: 20. measurement.cleanup()

        MeasureSvc-->>Engine: 21. Return MeasurementResult\n{success, value, error_message}
        deactivate MeasureSvc

        Engine->>DB: 22. INSERT INTO test_results
        activate DB
        DB-->>Engine: 23. Confirm saved
        deactivate DB

        alt Result is FAIL and NOT runAllTest mode
            Engine->>DB: 24. UPDATE test_sessions\nSET status=FAILED
            Engine-->>API: 25. Return FAILED status
            API-->>Frontend: 26. Return with error
            Frontend-->>User: 27. Display failure
        end
    end

    Engine->>DB: 28. UPDATE test_sessions\nSET status=COMPLETED\nSET final_result
    activate DB
    DB-->>Engine: 29. Confirm updated
    deactivate DB

    Engine->>Report: 30. save_session_report(session_id)
    activate Report
    Report->>DB: 31. Query session results
    DB-->>Report: 32. Return results
    Report->>Report: 33. Generate CSV
    Report->>Report: 34. Save to reports/{project}/{station}/{date}/
    Report-->>Engine: 35. Report saved
    deactivate Report

    Engine-->>API: 36. Return COMPLETED with statistics
    deactivate Engine

    API-->>Frontend: 37. Return {status, pass_count, fail_count}
    deactivate API

    Frontend-->>User: 38. Display results summary

    Note over Engine,DB: Normal mode: stops on first failure\nrunAllTest mode: continues (see next diagram)
```

---

## 4. Test Execution Flow (runAllTest Mode)

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
    participant Frontend as TestMain.vue
    participant API as Tests API
    participant Engine as TestEngine
    participant MeasureSvc as MeasurementService
    participant Errors as ErrorCollector
    participant DB as Database

    User->>Frontend: 1. Enable runAllTest toggle
    Frontend->>API: 2. POST /api/tests/sessions/start\n{runAllTest: true}
    activate API

    API->>Engine: 3. execute_test_session(session_id, runAllTest=true)
    activate Engine

    Engine->>DB: 4. UPDATE test_sessions\nSET status=RUNNING
    activate DB
    DB-->>Engine: 5. Confirm updated
    deactivate DB

    Engine->>Errors: 6. Initialize error collector\nerrors = []
    activate Errors
    Errors-->>Engine: 7. Ready
    deactivate Errors

    loop For each test point
        Engine->>MeasureSvc: 8. execute_measurement(test_plan)
        activate MeasureSvc

        MeasureSvc->>MeasureSvc: 9. prepare() → execute() → cleanup()
        MeasureSvc->>MeasureSvc: 10. validate_result()

        MeasureSvc-->>Engine: 11. Return MeasurementResult
        deactivate MeasureSvc

        Engine->>DB: 12. INSERT INTO test_results
        activate DB
        DB-->>Engine: 13. Confirm saved
        deactivate DB

        alt Result is FAIL
            Engine->>Errors: 14. Collect error\n{item_no, error_message}
            activate Errors
            Errors-->>Engine: 15. Added to list
            deactivate Errors

            Note over Engine: runAllTest mode:\nCONTINUE execution
        end
    end

    Engine->>Errors: 16. Get all collected errors
    activate Errors
    Errors-->>Engine: 17. Return error list
    deactivate Errors

    alt Any failures
        Engine->>DB: 18. UPDATE test_sessions\nSET status=FAILED,\nfinal_result=FAIL
    else All passed
        Engine->>DB: 19. UPDATE test_sessions\nSET status=COMPLETED,\nfinal_result=PASS
    end

    Engine-->>API: 20. Return {status, errors}
    deactivate Engine

    API-->>Frontend: 21. Return {status, error_list}
    deactivate API

    Frontend->>Frontend: 22. Display error summary table

    Note over Engine,Errors: PDTool4 compatibility:\nCollect ALL errors, report at end\nDon't stop on first failure
```

---

## 5. Measurement Execution Flow

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
    participant Engine as TestEngine
    participant MeasureSvc as MeasurementService
    participant Registry as MeasurementRegistry
    participant Base as BaseMeasurement
    participant Concrete as ConcreteMeasurement
    participant Instrument as InstrumentManager
    participant Driver as InstrumentDriver
    participant Hardware as Hardware

    Engine->>MeasureSvc: 1. execute_measurement(test_plan)
    activate MeasureSvc

    MeasureSvc->>Registry: 2. get_class(test_type)
    activate Registry
    Registry-->>MeasureSvc: 3. Return measurement class
    deactivate Registry

    MeasureSvc->>Concrete: 4. Instantiate measurement class
    activate Concrete

    Note over Concrete: test_type determines which class:\n- PowerSet → PowerSetMeasurement\n- PowerRead → PowerReadMeasurement\n- CommandTest → CommandTestMeasurement\n- SFCtest → SFCtestMeasurement\n- getSN → GetSNMeasurement\n- OPjudge → OPJudgeMeasurement

    MeasureSvc->>Concrete: 5. async prepare(params)
    Note over Concrete: Phase 1: Setup\n- Parse parameters\n- Configure instrument\n- Validate inputs

    Concrete->>Instrument: 6. Get instrument connection
    activate Instrument
    Instrument->>Driver: 7. Get instrument driver
    activate Driver
    Driver-->>Instrument: 8. Return driver instance
    deactivate Driver
    Instrument-->>Concrete: 9. Return connection
    deactivate Instrument

    Concrete-->>MeasureSvc: 10. Prepare complete
    MeasureSvc->>Concrete: 11. async execute(params)
    Note over Concrete: Phase 2: Execute\n- Send command to hardware\n- Read response\n- Parse value

    Concrete->>Driver: 12. write_command(command)
    activate Driver
    Driver->>Hardware: 13. Send via serial/TCP/IP
    activate Hardware
    Hardware-->>Driver: 14. Confirm sent
    deactivate Hardware
    Driver-->>Concrete: 15. Confirm sent
    deactivate Driver

    Concrete->>Driver: 16. query_command()
    activate Driver
    Driver->>Hardware: 17. Read response
    activate Hardware
    Hardware-->>Driver: 18. Return raw data
    deactivate Hardware
    Driver-->>Concrete: 19. Return parsed value
    deactivate Driver

    Concrete-->>MeasureSvc: 20. Return value
    MeasureSvc->>Concrete: 21. async cleanup()
    Note over Concrete: Phase 3: Cleanup\n- Reset instrument state\n- Release connection

    Concrete->>Instrument: 22. Release connection
    activate Instrument
    Instrument-->>Concrete: 23. Confirm released
    deactivate Instrument

    Concrete-->>MeasureSvc: 24. Cleanup complete
    deactivate Concrete

    MeasureSvc->>MeasureSvc: 25. validate_result()\n(PDTool4 7-limit-type logic)

    alt Instrument error detected
        MeasureSvc->>MeasureSvc: 26a. Set result=ERROR\nSet error_message
    else Validation fails
        MeasureSvc->>MeasureSvc: 26b. Set result=FAIL\nSet error_message
    else Validation passes
        MeasureSvc->>MeasureSvc: 26c. Set result=PASS\nSet measured_value
    end

    MeasureSvc-->>Engine: 27. Return MeasurementResult
    deactivate MeasureSvc

    Note over MeasureSvc: Three-phase execution pattern\nensures proper resource management
```

---

## 6. Instrument Connection Flow

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
    participant MeasureSvc as MeasurementService
    participant Manager as InstrumentManager
    participant Driver as InstrumentDriver
    participant Hardware as Hardware Instrument
    participant DB as Database

    Note over Manager: Singleton pattern ensures\nsingle connection pool

    MeasureSvc->>Manager: 1. get_instrument(instrument_id)
    activate Manager

    alt Connection exists and IDLE
        Manager->>Manager: 2. Check connection pool
        Manager-->>MeasureSvc: 3. Return existing connection
        Manager->>Manager: 4. Set state=BUSY

    else No connection or BUSY
        alt No connection
            Manager->>DB: 5. SELECT * FROM instruments\nWHERE id=?
            activate DB
            DB-->>Manager: 6. Instrument config
            deactivate DB

            Manager->>Driver: 7. Initialize driver\n(instrument_type, config)
            activate Driver

            Driver->>Hardware: 8. Connect\n(serial/TCP/IP)
            activate Hardware
            Hardware-->>Driver: 9. Connection established
            deactivate Hardware

            Driver->>Driver: 10. reset()\nClear buffers, set defaults
            Driver-->>Manager: 11. Driver ready
            deactivate Driver

            Manager->>Manager: 12. Add to pool\nSet state=IDLE
        end

        Manager->>Manager: 13. Set state=BUSY
        Manager-->>MeasureSvc: 14. Return connection
    end

    deactivate Manager

    MeasureSvc->>Driver: 15. Use connection\nwrite/query commands
    activate Driver
    Driver-->>MeasureSvc: 16. Return results
    deactivate Driver

    MeasureSvc->>Manager: 17. release_instrument(instrument_id)
    activate Manager
    Manager->>Manager: 18. Set state=IDLE
    Manager-->>MeasureSvc: 19. Confirm released
    deactivate Manager

    Note over Manager,Hardware: States: IDLE, BUSY, ERROR, OFFLINE\nSingleton prevents multiple connections
```

---

## 7. Results Query Flow

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
    participant Frontend as ResultsView.vue
    participant API as Results API
    participant DB as Database
    participant Calc as StatisticsCalculator

    User->>Frontend: 1. Navigate to results page
    Frontend->>Frontend: 2. Load filters (project, station, date range)

    Frontend->>API: 3. GET /api/results/sessions\n?project_id=&station_id=&start_date=&page=1
    activate API

    API->>DB: 4. SELECT ts.*, p.project_name,\ns.station_name, u.username\nFROM test_sessions ts\nJOIN projects p\nJOIN stations s\nJOIN users u\nWHERE ts.project_id=?\nAND ts.station_id=?\nAND ts.start_time >= ?\nORDER BY ts.start_time DESC\nLIMIT 20 OFFSET 0
    activate DB
    DB-->>API: 5. Return sessions with joins
    deactivate DB

    loop For each session
        API->>DB: 6. SELECT * FROM test_results\nWHERE test_session_id=?\nORDER BY item_no
        activate DB
        DB-->>API: 7. Return test results
        deactivate DB

        API->>Calc: 8. calculate_test_statistics(results)
        activate Calc

        Calc->>Calc: 9. Count total_tests
        Calc->>Calc: 10. Count passed_tests\n(result='PASS')
        Calc->>Calc: 11. Count failed_tests\n(result='FAIL' or 'ERROR')

        Calc-->>API: 12. Return {total, passed, failed, error}
        deactivate Calc

        API->>API: 13. Build TestSessionResponse\nwith statistics
    end

    API->>DB: 14. SELECT COUNT(*) FROM test_sessions\n[with same filters]
    activate DB
    DB-->>API: 15. Return total count
    deactivate DB

    API-->>Frontend: 16. Return {sessions, total, page, page_size}
    deactivate API

    Frontend->>Frontend: 17. Render sessions table\nwith pagination

    User->>Frontend: 18. Click session row
    Frontend->>API: 19. GET /api/results/sessions/{id}
    activate API

    API->>DB: 20. SELECT * FROM test_results\nWHERE test_session_id=?\nORDER BY item_no
    activate DB
    DB-->>API: 21. Return all results
    deactivate DB

    API-->>Frontend: 22. Return session with results
    deactivate API

    Frontend-->>User: 23. Display detailed results
```

---

## 8. CSV Export Flow

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
    participant Frontend as ResultsView.vue
    participant API as Results API
    participant DB as Database
    participant CSV as CSVBuilder

    User->>Frontend: 1. Click "Export CSV" button
    Frontend->>API: 2. GET /api/results/export/csv/{session_id}
    activate API

    API->>DB: 3. SELECT ts.*, tr.*\nFROM test_sessions ts\nJOIN test_results tr\nWHERE ts.id=?
    activate DB
    DB-->>API: 4. Return session with all results
    deactivate DB

    API->>CSV: 5. build_csv_content(session, results)
    activate CSV

    CSV->>CSV: 6. Create CSV writer
    CSV->>CSV: 7. Write header row:\nItemNo, ItemName, MeasuredValue,\nLowerLimit, UpperLimit, Unit,\nResult, ErrorMessage, ExecutionTime

    loop For each test result
        CSV->>CSV: 8. Format values\n- Decimal precision\n- Date/time format\n- Escape special characters
        CSV->>CSV: 9. Write data row
    end

    CSV-->>API: 10. Return CSV content (string)
    deactivate CSV

    API->>API: 11. Set headers:\nContent-Type: text/csv\nContent-Disposition: attachment;\nfilename="session_{id}_{timestamp}.csv"

    API-->>Frontend: 12. Return CSV file
    deactivate API

    Frontend->>Frontend: 13. Trigger browser download\nCreate <a> element with download attribute

    Frontend-->>User: 14. File downloads to Downloads folder

    Note over CSV: CSV format matches PDTool4\nfor compatibility
```

---

## Summary of Request Flows

| Flow | Entry Point | Key Services | Database Tables |
|------|-------------|--------------|-----------------|
| Authentication | POST /api/auth/login | AuthService | users |
| Test Plan Import | POST /api/testplan/upload | TestPlanService, CSVParser | test_plans |
| Test Execution | POST /api/tests/sessions/start | TestEngine, MeasurementService | test_sessions, test_results |
| Measurement | Internal (MeasurementService) | ConcreteMeasurement classes | (via TestResult) |
| Instrument Connection | Internal (InstrumentManager) | InstrumentManager | (instrument config) |
| Results Query | GET /api/results/sessions | StatisticsCalculator | test_sessions, test_results |
| CSV Export | GET /api/results/export/csv | CSVBuilder | test_sessions, test_results |

---

`★ Insight ─────────────────────────────────────`
1. **runAllTest mode** differs from normal mode by continuing execution after failures and collecting all errors in a list for summary reporting
2. **Three-phase measurement execution** (prepare → execute → cleanup) ensures proper resource management even when exceptions occur
3. **Instrument manager singleton** prevents multiple simultaneous connections to the same hardware, which could cause race conditions or communication errors
`─────────────────────────────────────────────────`
