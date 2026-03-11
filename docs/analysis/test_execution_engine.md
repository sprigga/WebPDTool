# Test Execution Engine Analysis

## Overview

The Test Execution Engine orchestrates the complete test session lifecycle from initiation to completion. It integrates async execution, instrument management, and measurement dispatching into a cohesive system that matches PDTool4's behavior.

## Core Components

### 1. TestEngine

**Location:** `backend/app/services/test_engine.py`

**Purpose:** Singleton orchestrator for test session management

**Key Class Structure:**
```python
class TestEngine:
    def __init__(self, db: AsyncSession, measurement_service: MeasurementService):
        self.active_sessions = Dict[int, TestExecutionState]
        self.db = db
        self.measurement_service = measurement_service

class TestExecutionState:
    def __init__(self, session_id: int, run_all_test: bool):
        self.session_id = session_id
        self.run_all_test = run_all_test  # PDTool4 compatibility mode
        self.is_running = False
        self.pause_event = asyncio.Event()
        self.current_item_index = 0
        self.cancel_flag = False
```

### 2. MeasurementService

**Location:** `backend/app/services/measurement_service.py`

**Purpose:** Dispatches measurements to appropriate implementations

**Responsibilities:**
- Retrieve measurement class from registry
- Instantiate measurements with test plan data
- Execute three-phase lifecycle (prepare → execute → cleanup)
- Handle exceptions and error reporting
- Track execution duration

**Key Methods:**
```python
async def execute_single_measurement(
    self,
    test_plan_item: Dict[str, Any],
    session_id: int
) -> MeasurementResult:
    # Get measurement class
    measurement_class = get_measurement_class(test_plan_item['test_type'])

    # Instantiate and execute
    measurement = measurement_class(test_plan_item, self.config)

    # Three-phase execution
    await measurement.prepare(params)
    result = await measurement.execute(params)
    await measurement.cleanup()

    return result

async def execute_batch_measurements(
    self,
    test_plan_items: List[Dict[str, Any]],
    session_id: int,
    run_all_test: bool = False
) -> Dict[str, Any]:
    # Sequential execution with runAllTest logic
    # Return session statistics
```

### 3. InstrumentManager

**Location:** `backend/app/services/instrument_manager.py`

**Purpose:** Singleton connection pool for instrument management

**Design Patterns:**
- Singleton pattern with async context manager
- Connection pooling and reuse
- State tracking (IDLE, BUSY, ERROR, OFFLINE)
- Automatic cleanup and reset

**Key Structure:**
```python
class InstrumentManager:
    _instance = None

    def __init__(self):
        self.connection_pools = {}  # Instrument name → ConnectionPool
        self.instrument_states = {}  # Instrument name → InstrumentState

    async def get_connection(self, instrument_name: str) -> InstrumentConnection:
        # Get or create connection pool
        # Return async context manager
        return self.connection_pools[instrument_name].acquire()

class InstrumentConnection:
    def __init__(self, instrument_config, raw_connection):
        self.config = instrument_config
        self.raw_connection = raw_connection
        self.state = InstrumentState.IDLE

    async def __aenter__(self):
        self.state = InstrumentState.BUSY
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.state = InstrumentState.IDLE
```

## Execution Flow

### Complete Test Session Lifecycle

```
1. Client Request (TestMain.vue)
   POST /api/tests/sessions/start
   {
     "serial_number": "SN123456",
     "station_id": 1,
     "run_all_test": true  // PDTool4 mode
   }

2. API Handler (tests.py)
   - Validate user authentication
   - Check station exists and is active
   - Fetch test plan for station
   - Call TestEngine.start_test_session()

3. TestEngine.start_test_session()
   a. Create TestSession record in database
      - status = PENDING
      - start_time = now
   b. Load test plan items into queue
   c. Create TestExecutionState
   d. Async spawn execution task
   e. Return session_id to client

4. TestEngine.execute_test_session() (async task)
   a. Update session status to RUNNING
   b. For each test_plan_item in sequence:
      - Check pause/resume/cancel signals
      - Create TestResult record
      - Call MeasurementService.execute_single_measurement()
      - Save result to database
      - Update session statistics
      - If run_all_test is false and result is FAIL, break
   c. Update final session status (COMPLETED/FAILED/ABORTED)
   d. Calculate duration and statistics
   e. Trigger WebSocket notification (if implemented)

5. MeasurementService.execute_single_measurement()
   a. Get measurement class from registry
   b. Instantiate measurement with test_plan_item
   c. Call measurement.prepare()
   d. Call measurement.execute()
      - May interact with instruments via InstrumentManager
      - May perform calculations or I/O operations
      - Returns MeasurementResult
   e. Call measurement.cleanup()
   f. Apply PDTool4 validation (inside measurement)
   g. Return result

6. Measurement Implementation (e.g., PowerReadMeasurement)
   a. prepare() - Validate parameters, check instrument availability
   b. execute():
      - Get connection from pool: `async with connection_pool.get_connection()`
      - Get driver: `get_driver_class(connection.config.instrument_type)`
      - Instantiate driver with config
      - Connect: `await driver.connect()`
      - Read value: `value = await driver.read_value()`
      - Validate: `self.validate_result(value, ...)`
      - Return MeasurementResult
   c. cleanup() - Disconnect, release resources

7. Database Persistence
   - TestResult records (one per test item)
   - TestSession statistics update
   - SFC logs if applicable

8. Client Updates
   - Polling: GET /api/tests/sessions/{id}/status
   - Results: GET /api/tests/sessions/{id}/results
   - Real-time feedback if WebSocket implemented
```

## runAllTest Mode Implementation

### PDTool4 Compatibility

The `run_all_test` parameter (common in PDTool4 test plans) controls whether execution continues after a failure:

**run_all_test = false:**
- Stop immediately on first FAIL result
- Session status = FAILED
- Return to user with partial results

**run_all_test = true:**
- Continue execution regardless of FAIL/ERROR results
- Execute all test items in sequence
- Collect all failures in error summary
- Session status = COMPLETED (even with some fails)
- Final result = PASS if all pass, else FAIL

### Implementation in TestEngine

```python
async def execute_test_session(self, session_id: int):
    state = self.active_sessions[session_id]
    fail_items = 0

    for i, test_plan_item in enumerate(test_plan_items):
        result = await self.measurement_service.execute_single_measurement(
            test_plan_item, session_id
        )

        # Always record result
        await self.save_test_result(session_id, test_plan_item, result)

        # Count failures
        if result.result == ItemResult.FAIL:
            fail_items += 1

        # runAllTest logic
        if not state.run_all_test and result.result == ItemResult.FAIL:
            # Stop on first failure
            break

    # Final status
    if fail_items > 0:
        session.final_result = TestResult.FAIL
    else:
        session.final_result = TestResult.PASS
```

### Implementation in MeasurementService

```python
async def execute_batch_measurements(self, test_plan_items, session_id, run_all_test=False):
    results = []
    errors = []

    for item in test_plan_items:
        try:
            result = await self.execute_single_measurement(item, session_id)
            results.append(result)

            if result.result == ItemResult.ERROR:
                errors.append({
                    'item_no': result.item_no,
                    'item_name': result.item_name,
                    'error_message': result.error_message
                })

            # Stop on ERROR if not run_all_test
            if not run_all_test and result.result == ItemResult.ERROR:
                break

        except Exception as e:
            error_result = self.create_error_result(item, str(e))
            results.append(error_result)
            errors.append({...})
            if not run_all_test:
                break

    return {
        'results': results,
        'errors': errors,
        'total_items': len(test_plan_items),
        'pass_items': sum(1 for r in results if r.result == ItemResult.PASS),
        'fail_items': sum(1 for r in results if r.result == ItemResult.FAIL)
    }
```

## Concurrency and Async Patterns

### Async/Await Throughout

All I/O operations are async:
- Database queries via SQLAlchemy async
- Instrument communication via async drivers
- HTTP requests to external services (SFC, MES)
- File I/O for script execution

### Connection Pooling

InstrumentManager uses connection pooling to reuse instrument connections:
```python
# Connections are acquired and released via async context managers
async with instrument_manager.get_connection('DAQ973A_1') as conn:
    value = await conn.read_value()
# Connection automatically returned to pool
```

### State Synchronization

TestEngine uses thread-safe state tracking:
```python
# asyncio.Lock for state modifications
async with self.state_lock:
    state.current_item_index = i
    state.is_running = True

# asyncio.Event for pause/resume signaling
await state.pause_event.wait()  # Pause here if event cleared
state.pause_event.set()  # Resume execution
```

## Error Handling

### Error Categories

1. **Session Setup Errors** (before test start)
   - Invalid station_id
   - Missing test plan
   - Database connection failure
   - → Return 400/500, no session created

2. **Measurement Errors** (during execution)
   - Instrument connection failure → ERROR result
   - Driver timeout → ERROR result
   - Parameter validation failure → ERROR result
   - → Record ERROR, continue unless not run_all_test

3. **Validation Failures** (after measurement)
   - Value outside limits → FAIL result
   - Type conversion failure → ERROR result
   - → Record FAIL/ERROR, continue if run_all_test

4. **Execution Interruption**
   - User abort → ABORTED status
   - System crash → FAILED status
   - Network timeout → ERROR result with timeout

### Exception Handling Strategy

```python
# In TestEngine
try:
    result = await measurement_service.execute_single_measurement(item, session_id)
except MeasurementError as e:
    # Known measurement error
    result = MeasurementResult(ERROR, error_message=str(e))
except asyncio.TimeoutError:
    result = MeasurementResult(ERROR, error_message="Measurement timeout")
except Exception as e:
    # Unexpected error
    logger.exception("Unexpected error in measurement")
    result = MeasurementResult(ERROR, error_message=f"Unexpected: {str(e)}")

# In MeasurementService
async def execute_single_measurement(self, item, session_id):
    try:
        # Normal execution path
        ...
    except Exception as e:
        # Ensure result always returned
        return self.create_error_result(item, str(e))
```

## Performance Considerations

### Sequential Execution

Tests execute sequentially (not parallel) to ensure:
1. Instrument availability (single device per test)
2. predictable test order
3. PDTool4 compatibility (same execution order)
4. Simplified error handling

### Database Transactions

- Each test result written in separate transaction
- Session statistics updated incrementally
- Commit frequency minimal to maintain performance

### Instrument Connection Reuse

- Connections pooled and reused across tests
- Connection timeout and cleanup policies
- Configurable pool size (currently 1 per instrument)

## Monitoring and Observability

### Logging Strategy

**TestEngine Logging:**
- Session start/end at INFO level
- Each test item execution at DEBUG level
- Failures at WARN level
- Errors at ERROR level

**MeasurementService Logging:**
- Measurement class and parameters at DEBUG
- Instrument I/O at DEBUG
- Validation results at INFO
- Performance metrics (duration) at INFO

**InstrumentManager Logging:**
- Connection establishment at INFO
- State transitions at DEBUG
- Connection errors at ERROR

### Request Context

FastAPI provides request context via middleware:
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Add user_id to context
    user_id = get_user_from_token(request)
    request.state.user_id = user_id

    response = await call_next(request)
    return response
```

Request ID propagation enables correlation in logs.

## Testing Strategies

### Unit Tests

**TestEngine:**
- Mock MeasurementService and database
- Test session creation, progression, cancellation
- Verify run_all_test logic
- Test state management and synchronization

**MeasurementService:**
- Mock registry and instrument manager
- Test each measurement type
- Verify exception handling
- Test duration tracking

**InstrumentManager:**
- Test connection pooling
- Verify state transitions
- Test timeout and cleanup

### Integration Tests

**End-to-End Test Session:**
1. Create session → verify TestSession record
2. Start test execution → verify TestResult records created
3. Poll status → verify progression through items
4. Complete execution → verify final statistics
5. Query results → verify data accuracy

**Instrument Integration:**
- Use simulated instruments (virtual drivers)
- Test real instrument communication
- Verify connection handling and recovery

**runAllTest Mode:**
- Test both modes with mix of PASS/FAIL results
- Verify correct session final_result
- Verify error collection and reporting

### Performance Tests

- Test with large test plan (100+ items)
- Measure execution time with and without connection pooling
- Test concurrent session execution (should be isolated)
- Verify memory usage over long-running sessions

## Known Limitations

1. **Sequential Execution:** No parallel test execution
2. **No WebSocket Support:** Client uses polling for progress updates
3. **Single Instrument per Type:** Cannot parallelize same-instrument tests
4. **Memory Growth:** Session state retained until completion
5. **No Checkpoint/Restart:** Failed session must restart from beginning

## Future Enhancements

1. **Parallel Execution:** Execute independent tests concurrently
2. **Checkpointing:** Save progress for restart after failures
3. **WebSocket Support:** Real-time progress streaming
4. **Session Pause/Resume:** Proper pause implementation (currently stop only)
5. **Test Plan Optimization:** Dependency-based scheduling
6. **Distributed Execution:** Spread tests across multiple engine instances
7. **Advanced Error Recovery:** Retry logic for transient instrument failures
8. **Resource Quotas:** Limit concurrent sessions per station

## API Endpoints

### Test Session Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tests/sessions/start` | POST | Start new test session |
| `/api/tests/sessions/{id}/status` | GET | Get session status |
| `/api/tests/sessions/{id}/results` | GET | Get test results |
| `/api/tests/sessions/{id}/abort` | POST | Abort running session |
| `/api/tests/sessions` | GET | List all sessions |

### Instrument Control

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/measurements/instruments` | GET | List all instruments |
| `/api/measurements/instruments/{name}/reset` | POST | Reset instrument |

## Configuration

TestEngine configuration via `backend/app/config.py`:

```python
class Settings(BaseSettings):
    # Test execution
    TEST_ENGINE_TIMEOUT: int = 3600  # 1 hour max per session
    MAX_CONCURRENT_SESSIONS: int = 10
    INSTRUMENT_TIMEOUT: float = 30.0

    # Database
    DATABASE_URL: str
```

## Conclusion

The Test Execution Engine provides robust, PDTool4-compatible test orchestration with clear separation of concerns, comprehensive error handling, and extensible architecture. The async design ensures efficient resource utilization while maintaining the sequential execution model required for hardware testing.