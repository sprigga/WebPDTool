# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WebPDTool is a web-based automated testing system refactored from the desktop application PDTool4. It executes hardware tests on manufactured products, validates results against test plans, and records outcomes using a 3-tier architecture: Vue 3 frontend, FastAPI backend, and MySQL database.

**Key Architecture:** Complete PDTool4 compatibility layer with measurement abstraction, supporting 7 limit types (lower/upper/both/equality/inequality/partial/none) and 3 value types (string/integer/float). The `runAllTest` mode continues executing tests after failures, matching PDTool4 behavior exactly.

## Development Commands

### Docker Environment (Primary)

```bash
docker-compose up -d                   # Start all services
docker-compose logs -f backend         # Backend logs
docker-compose down                    # Stop services
docker-compose build --no-cache && docker-compose up -d  # Rebuild after code changes

# Database initialization (first time only)
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/schema.sql
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_data.sql
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_instruments.sql
```

### Local Development

```bash
# Backend (Python 3.11+) — use uv, not pip directly
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# Frontend (Node.js 16+)
cd frontend
npm install
npm run dev  # Runs on http://localhost:5678 (NOT 5173)
             # /api proxy target: http://localhost:8765
             # ⚠ For local dev, backend must run on port 8765, not 9100:
             # uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8765

# Database access
mysql -h localhost -P 33306 -u pdtool -p webpdtool  # password: pdtool123
```

### Testing

```bash
cd backend

# Preferred: use uv
uv run pytest
uv run pytest tests/test_api/test_auth.py      # Single file
uv run pytest --cov=app tests/                  # Coverage
uv run pytest -m unit                           # Fast unit tests only
uv run pytest -m "not hardware"                 # Skip tests requiring hardware
uv run pytest -k "test_instrument_model2306"    # Filter by name
```

**Available pytest markers:**
- **Speed:** `slow`, `fast`
- **Type:** `unit`, `integration`, `e2e`
- **Hardware:** `hardware`, `simulation`
- **Instruments:** `instrument_34970a`, `instrument_model2306`, `instrument_it6723c`, `instrument_2260b`, `instrument_cmw100`, `instrument_mt8872a`
- **Components:** `measurements`, `instruments`, `api`, `services`

### Test Plan Import

```bash
cd backend
python scripts/import_testplan.py \
  --project "PROJECT_CODE" \
  --station "STATION_CODE" \
  --csv-file "/path/to/testplan.csv"
```

## Architecture Overview

### Service Ports

| Service | Port | Notes |
|---------|------|-------|
| Frontend (Docker) | 9080 | Nginx serving Vue SPA |
| Frontend (dev) | 5678 | Vite dev server |
| Backend | 9100 | uvicorn FastAPI |
| Database | 33306 | MySQL container (internal 3306) |
| API Docs | 9100/docs | Swagger UI |

### Backend Structure (`backend/app/`)

- `main.py` — FastAPI app entry, middleware, router registration
- `api/` — Route handlers: `auth`, `users`, `projects`, `stations`, `instruments`, `tests`, `measurements`, `dut_control`, `modbus`, `modbus_ws`
  - `results/` — 8 sub-routers: sessions, measurements, summary, export, cleanup, reports, analysis (descriptive stats per test item and per session)
  - `testplan/` — 4 sub-routers: queries, mutations, sessions, validation
- `services/` — Business logic: `test_engine.py`, `measurement_service.py` (critical, ~46KB), `instrument_manager.py`, `instrument_connection.py`
  - `instruments/` — Driver registry (`INSTRUMENT_DRIVERS` dict) with 20+ hardware drivers
  - `modbus/` — `modbus_manager.py` (singleton), `modbus_listener.py` (async pymodbus), `modbus_config.py`
- `measurements/` — PDTool4 measurement abstraction layer (see below)
- `models/` — SQLAlchemy ORM: users, projects, stations, test_plans, test_sessions, test_results, sfc_logs, instruments, modbus_config
- `repositories/` — Data access layer (currently: `instrument_repository.py`)
- `core/` — `database.py`, `security.py`, `instrument_config.py`, `logging_v2.py`, `constants.py`
- `config/instruments.py` — `MEASUREMENT_TEMPLATES` and `AVAILABLE_INSTRUMENTS` (see below)
- `schemas/` — Pydantic v2 request/response models

### Frontend Structure (`frontend/src/`)

- `views/` — Vue 3 single-file components: TestMain, TestPlanManage, **TestResults** (3-tab: query/history/analysis), ProjectManage, UserManage, InstrumentManage, SystemConfig, TestExecution, ModbusConfig, Login
- `composables/` — Reusable logic:
  - `useTestTimeline.js` — ECharts timeline chart for test history, handles init/dispose/resize lifecycle
  - `useTestHistory.js` — Test history data fetching and filtering logic
  - `useMeasurementParams.js` — Dynamic parameter form generation from `MEASUREMENT_TEMPLATES` (fetches `GET /api/measurements/types`)
- `components/` — Shared UI: `AppNavBar.vue` (nav with `buttonType()`/`isCurrent()` helpers), `DynamicParamForm.vue` (renders measurement params), `ProjectStationSelector.vue`, `ModbusStatusIndicator.vue`
- `stores/` — Pinia: `auth.js`, `project.js`, `users.js`, `instruments.js`
- `api/` — Axios clients per domain; `client.js` base with auth interceptor that **unwraps `response.data`** (callers receive payload directly, not the full Axios response)
- `router/index.js` — Vue Router with auth guard; unauthenticated → `/login`; active routes: `/main`, `/test`, `/results`, `/testplan`, `/config`, `/projects`, `/users`, `/instruments`, `/modbus-config`

**TestResults.vue tabs:** Tab 1 (查詢結果) — session query/filter/export/delete; Tab 2 (測試歷史) — ECharts timeline chart via `useTestTimeline`; Tab 3 (分析報告) — descriptive statistics (mean/median/std/MAD) from `/api/results/analysis`.

## Critical Architecture Patterns

### Measurement Abstraction Layer

**`backend/app/measurements/base.py`** — `BaseMeasurement` abstract class:
- Three-phase execution: `prepare()` → `execute()` → `cleanup()`
- `validate_result()` replicates PDTool4's exact rules:
  - `none` → always pass
  - `lower` → value ≥ lower_limit
  - `upper` → value ≤ upper_limit
  - `both` → lower_limit ≤ value ≤ upper_limit
  - `equality` → value == eq_limit
  - `inequality` → value != eq_limit
  - `partial` → eq_limit in value (substring)
- Auto-detects instrument errors: strings starting with `"No instrument found"` or `"Error:"`
- `MeasurementResult` dataclass: result (PASS/FAIL/SKIP/ERROR), measured_value, limits, unit, error_message, execution_duration_ms

**`backend/app/measurements/registry.py`** — `MEASUREMENT_REGISTRY` maps test type strings → classes.

**`backend/app/measurements/implementations.py`** (~2300 lines) — Concrete classes: PowerSet, PowerRead, CommandTest, SFCtest, getSN, OPjudge, Other, ConSole, ComPort, TCPIP, Wait. Uses lazy imports to avoid circular dependencies. Parameter extraction via `get_param(params, *keys, default=None)`.

### MEASUREMENT_TEMPLATES (config/instruments.py)

`MEASUREMENT_TEMPLATES` is the authoritative source for per-instrument required/optional parameters per measurement type. It was migrated from hardcoded dicts inside `implementations.py` to improve maintainability and power the `/types` API dynamically. When adding support for a new instrument+measurement combination, update this dict — **do not add hardcoded parameter lists inside implementations**.

```python
MEASUREMENT_TEMPLATES = {
    "PowerSet": {
        "DAQ973A": {"required": ["Instrument", "Channel", "Item"], "optional": [...], "example": {...}},
        "MODEL2306": {...},
        ...
    },
    "PowerRead": {...},
    ...
}
```

### Test Execution Flow

```
TestMain.vue → POST /api/tests/sessions/start
→ TestEngine.execute_test_session() [asyncio background task]
→ MeasurementService.execute_measurement()
→ BaseMeasurement subclass.prepare/execute/cleanup()
→ InstrumentManager (hardware access, singleton connection pool)
→ validate_result() (PDTool4 logic)
→ Save TestResult → DB
→ Poll: GET /api/tests/sessions/{id}/status
```

`runAllTest` mode: continues execution on failures, collects all errors, reports at end. Toggle in `TestMain.vue`, handled in `measurement_service.py`.

### Instrument Driver Registry

**`backend/app/services/instruments/__init__.py`** — `INSTRUMENT_DRIVERS` dict maps type string → driver class.

**Critical naming trap:** The DB stores PDTool4 display names (`ConsoleCommand`, `ComPortCommand`, `TCPIPCommand`) while runtime keys are lowercase (`console`, `comport`, `tcpip`). **Both aliases must be registered:**

```python
"console": ConSoleCommandDriver,
"ConsoleCommand": ConSoleCommandDriver,  # DB-stored name from InstrumentManage.vue
```

Missing an alias → `"No driver for instrument type 'X'"` at runtime.

### InstrumentConfig Provider

`backend/app/core/instrument_config.py` has two providers:
- **`InstrumentSettings`** — legacy hardcoded fallback
- **`InstrumentConfigProvider`** — DB-backed with 30s TTL cache, set at startup via `set_global_instrument_provider()`

`_row_to_config()` maps `instrument.instrument_type` → `config.type` (the driver registry key).

### Database Relationships

```
projects (1) ──→ (N) stations
stations (1) ──→ (N) test_plans     # Each row = one test item (item_no)
stations (1) ──→ (N) test_sessions
users    (1) ──→ (N) test_sessions
test_sessions (1) ──→ (N) test_results
test_plans    (1) ──→ (N) test_results
test_sessions (1) ──→ (N) sfc_logs
```

**`test_plan_name`** groups rows into logical scripts/groups. `item_no` sequences items within a group.

**Key model fields:**
```
TestSession: id, serial_number, station_id, user_id, start_time, end_time,
             final_result (PASS/FAIL/ABORT), total_items, pass_items, fail_items,
             test_duration_seconds

TestResult:  id, session_id, test_plan_id, item_no, item_name, measured_value,
             lower_limit, upper_limit, unit, result, error_message,
             test_time, execution_duration_ms
```

### User Roles

- `admin` — Full access including user/instrument management
- `engineer` — Test plan management and execution
- `operator` — Test execution only

## Important Implementation Details

### Alembic Migrations and asyncmy

FastAPI runtime uses `asyncmy`; Alembic requires synchronous `pymysql`. `alembic/env.py` auto-converts `mysql+asyncmy://` → `mysql+pymysql://` via `_resolve_alembic_database_url()`. The database module exports `ASYNC_DATABASE_URL` (not `DATABASE_URL`).

### All DB Operations are Async

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_test_plan(db: AsyncSession, station_id: int):
    result = await db.execute(select(TestPlan).filter_by(station_id=station_id))
    return result.scalars().all()
```

### Frontend CRUD Pattern

Follow `UserManage.vue` / `InstrumentManage.vue`: `el-table` + `el-dialog` + reactive form + `ElMessageBox.confirm` for delete. When adding a new management page: add route to `router/index.js`, button to `AppNavBar.vue` using `buttonType()`/`isCurrent()` helpers, and link to `TestMain.vue` top nav bar.

### MEASUREMENT_TEMPLATES → Frontend Flow

When adding a new instrument+measurement combination, the data flows:
1. Add entry to `MEASUREMENT_TEMPLATES` in `backend/app/config/instruments.py`
2. Automatically exposed via `GET /api/measurements/types` (no code change needed there)
3. Frontend `useMeasurementParams.js` fetches this endpoint and passes schema to `DynamicParamForm.vue`

### DUT Communications (`backend/app/services/dut_comms/`)

Custom hardware protocol implementations (not related to instrument drivers):
- `chassis_controller.py`, `relay_controller.py` — top-level DUT control API
- `ltl_chassis_fixt_comms/` — CRC16 Kermit framing, struct-based messages
- `ls_comms/` — LS protocol messages
- `vcu_ether_comms/` — Ethernet/TCP-based VCU protocol

### CSV Import Field Mapping

`backend/app/utils/csv_parser.py` maps PDTool4 CSV columns:
- `項次` → `item_no`, `品名規格` → `item_name`
- `上限值` → `upper_limit`, `下限值` → `lower_limit`
- `limit_type`, `value_type`, `eq_limit` → PDTool4 validation parameters

### Error Handling

- Backend: FastAPI `HTTPException` with appropriate status codes
- Frontend: Axios response interceptor unwraps `response.data`; 401 → auto-logout + redirect
- Measurement results distinguish: validation failures (FAIL) vs execution errors (ERROR)

## Environment Configuration

```bash
# Backend (backend/.env)
DATABASE_URL=mysql+asyncmy://pdtool:pdtool123@db:3306/webpdtool
SECRET_KEY=<min 32 chars>
ACCESS_TOKEN_EXPIRE_MINUTES=480
DEBUG=false
REDIS_ENABLED=true          # Optional distributed logging
REDIS_URL=redis://redis:6379/0

# Docker ports
FRONTEND_PORT=9080
BACKEND_PORT=9100
MYSQL_PORT=33306
```

## Modbus Integration

`ModbusListenerService` polls a Modbus TCP device for coil/register values. `ModbusManager` is a singleton that manages one active listener per station.

**WebSocket flow:** `TestMain.vue` connects to `WS /api/modbus/ws/{station_id}`. The backend broadcasts `sn_received` events when a serial number register changes; the frontend auto-triggers a test run on receipt.

**Stale socket guard:** The frontend tracks a `modbusWsRef` counter — each new `WebSocket` increments it, and the `onopen`/`onmessage` handlers check the counter at call time to drop messages from closed sockets.

**Key routes:**
- `GET/POST /api/modbus/configs` — CRUD for `ModbusConfig` (station_id, host, port, register addresses)
- `POST /api/modbus/start/{station_id}`, `POST /api/modbus/stop/{station_id}` — listener lifecycle
- `WS /api/modbus/ws/{station_id}` — real-time events (`listener_started`, `listener_stopped`, `sn_received`, `result_written`)

## Known Limitations

1. **Instrument Drivers:** Most implementations are stubs. Real hardware drivers need implementation in `backend/app/services/instruments/`.
2. **Real-time Updates:** Modbus uses WebSocket. Test execution status still uses polling (GET `/api/tests/sessions/{id}/status`).
3. **Modbus:** WebSocket and REST are implemented; requires actual Modbus TCP device for production use.

## Port Mapping Summary

| Context | Backend port | Frontend port | Notes |
|---------|-------------|---------------|-------|
| Docker | 9100 (internal) | 9080 | Nginx proxies `/api` to backend |
| Local dev | **8765** | 5678 | Vite proxy in `vite.config.js` targets 8765 |

For local dev the backend **must** run on 8765 (`--port 8765`), not 9100, because `vite.config.js` hardcodes the proxy target as `http://localhost:8765`.
