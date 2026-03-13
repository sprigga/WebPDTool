# Async DB Migration Design

**Date:** 2026-03-13
**Project:** WebPDTool
**Status:** Approved

## Goal

Migrate the FastAPI backend from synchronous SQLAlchemy (`pymysql` + `Session`) to SQLAlchemy 2.0 async (`asyncmy` + `AsyncSession`), eliminating event-loop blocking under load. Migration is incremental — module by module — so each wave is independently testable and deployable.

## Approach

Additive async dependency, module-by-module cut-over:

- Add `get_async_db` alongside existing `get_db` in `database.py`
- Migrate routers and their service/repository dependencies one wave at a time
- Old sync engine and `get_db` remain until the final cut-over step
- `asyncmy` is added to dependencies immediately; `pymysql` removed only at final cut-over

## Section 1: Database Layer (`database.py`)

Add async engine and session factory using SQLAlchemy 2.0 async API.

**Important:** `async_sessionmaker` requires `class_=AsyncSession` explicitly — without it the factory produces sync sessions and `await db.execute(...)` will fail at runtime.

**Important:** `get_async_db` must rollback on exception to avoid leaving open transactions that hold DB locks.

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

ASYNC_DATABASE_URL = f"mysql+asyncmy://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,       # required — do not omit
    expire_on_commit=False,
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

Existing sync `engine`, `SessionLocal`, and `get_db` are left untouched until final cut-over.

## Section 2: Module Migration Order

Six waves. Each wave is fully migrated and verified before moving to the next.

`dut_control.py` uses no DB session — it is excluded from migration entirely.

| Wave | Modules | Service / Repo dependencies |
|------|---------|----------------------------|
| 1 | `api/auth.py`, `api/users.py` | `services/auth.py` |
| 2 | `api/projects.py`, `api/stations.py` | ORM only |
| 3 | `api/instruments.py` | `repositories/instrument_repository.py`, `InstrumentConfigProvider` in `main.py` (see Section 3 special cases) |
| 4 | `api/testplan/` (4 files) | `services/test_plan_service.py` |
| 5 | `api/results/` (7 files) | ORM only |
| 6 | `api/tests.py`, `api/measurements.py` | `services/test_engine.py`, `services/measurement_service.py` |

**Final cut-over (after Wave 6):**
- Remove `get_db`, `SessionLocal`, sync `engine` from `database.py`
- Remove `pymysql` from `pyproject.toml`; keep only `asyncmy`
- Remove `SessionLocal` import from `test_engine.py`
- Update test fixtures (see Section 5)

## Section 3: Per-Module Migration Pattern

Every module follows this 4-step pattern:

### Step 1 — Router dependency
```python
# Before
from app.core.database import get_db
from sqlalchemy.orm import Session
db: Session = Depends(get_db)

# After
from app.core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
db: AsyncSession = Depends(get_async_db)
```

### Step 2 — ORM reads
```python
# Before
items = db.query(Model).filter(Model.field == value).all()
item = db.query(Model).filter(Model.id == id).first()

# After
from sqlalchemy import select
result = await db.execute(select(Model).where(Model.field == value))
items = result.scalars().all()

result = await db.execute(select(Model).where(Model.id == id))
item = result.scalar_one_or_none()
```

Also migrate `db.get(Model, pk)` → `await db.get(Model, pk)` wherever it appears.

### Step 3 — ORM writes
```python
# Before
db.add(obj); db.commit(); db.refresh(obj)

# After
db.add(obj); await db.commit(); await db.refresh(obj)
```

### Step 4 — Service layer
- Method signatures: `db: Session` → `db: AsyncSession`
- All methods that touch DB become `async def`
- Apply same read/write/get patterns above
- **Important:** All intra-class calls to async methods must also be `await`ed. For example, if `update()` calls `self.get_by_id()` internally, that call must become `await self.get_by_id(...)` after both are made async.

### Special cases

**`instrument_repository.py` (Wave 3):**
- Constructor: `def __init__(self, db: AsyncSession)`
- All methods become `async def`
- `self.db.get(Instrument, pk)` → `await self.db.get(Instrument, pk)`
- `update()` calls `get_by_id()` internally — must `await self.get_by_id(...)` after migration
- Queries: `self.db.query(...).filter(...).all()` → `await self.db.execute(select(...).where(...))` + `.scalars().all()`

**`InstrumentConfigProvider` and `main.py` startup (Wave 3):**

`InstrumentConfigProvider` calls `self._repo.list_enabled()`, `list_all()`, and `get_by_instrument_id()` synchronously inside `_refresh_cache`, `_build_all_map`, and `get_instrument`. After the repo becomes async, these are coroutines and cannot be called from plain `def` methods.

**Decision:** Keep `InstrumentConfigProvider` synchronous. Instead of injecting a single session (which has a lifetime problem — the startup session closes but the provider lives forever), inject a `SessionLocal` **factory callable**. Each cache refresh creates its own short-lived session, uses it, and closes it.

```python
# instrument_config.py — updated InstrumentConfigProvider.__init__
class InstrumentConfigProvider:
    def __init__(self, session_factory, cache_ttl: float = 30.0):
        # session_factory: callable that returns a new sync Session (SessionLocal)
        self._session_factory = session_factory
        ...

    def _refresh_cache(self):
        db = self._session_factory()
        try:
            from app.repositories.instrument_repository import InstrumentRepository
            repo = InstrumentRepository(db)
            rows = repo.list_enabled()   # sync — repo stays sync here
            ...
        finally:
            db.close()
```

`InstrumentRepository` therefore needs **two variants**:
- Keep existing sync `InstrumentRepository` (used by `InstrumentConfigProvider`)
- Create `AsyncInstrumentRepository` (used by the instruments API router in Wave 3)

Both can live in `instrument_repository.py` or the async variant in a separate file — either is acceptable.

**`main.py` startup provider update (Wave 3):**

```python
# Before (current state after our earlier bugfix)
from app.core.database import SessionLocal as SyncSessionLocal
db = SyncSessionLocal()
try:
    repo = InstrumentRepository(db)
    provider = InstrumentConfigProvider(repo=repo, cache_ttl=30.0)
    set_global_instrument_provider(provider)
finally:
    db.close()

# After (Wave 3)
from app.core.database import SessionLocal as SyncSessionLocal  # sync factory kept for provider
provider = InstrumentConfigProvider(session_factory=SyncSessionLocal, cache_ttl=30.0)
set_global_instrument_provider(provider)
# No session opened at startup — provider opens its own per-refresh
```

This means `SyncSessionLocal` must remain available even after Wave 3 (it feeds the provider's cache refreshes). It is removed only at final cut-over, when the provider is updated to use the async session factory or the provider's cache-refresh methods are made async.

**`test_engine.py` (Wave 6):**

`test_engine.py` constructs its session directly (`db = SessionLocal()`) rather than using dependency injection. All affected method signatures must be updated explicitly.

Methods that accept or construct a `Session` and must be migrated:
- `start_test_session(self, ..., db: Session)` — `db` parameter removed (no longer passed from API; engine owns its session)
- `_execute_test_session(self, session_id, station_id)` — already fixed to use `SessionLocal()` internally; replace with `async with AsyncSessionLocal() as db:`
- `_execute_measurement(self, ..., db: Session)` — signature changes to `db: AsyncSession`
- `_save_test_result(self, ..., db: Session)` — signature changes to `db: AsyncSession`
- `_finalize_test_session(self, ..., db: Session)` — signature changes to `db: AsyncSession`

All `db.query(...)` → `await db.execute(select(...))`, all `db.commit()` → `await db.commit()`, all `db.refresh()` → `await db.refresh()` throughout.

Import change in `test_engine.py`:
```python
# Before
from app.core.database import SessionLocal

# After
from app.core.database import AsyncSessionLocal
```

## Section 4: Error Handling

No changes to FastAPI error handling or `HTTPException` patterns — they work identically with `AsyncSession`. Unhandled DB exceptions propagate as async exceptions, which FastAPI already handles correctly. The rollback guard in `get_async_db` (Section 1) covers request-scoped sessions.

## Section 5: Test Fixture Updates (Final Cut-over)

Four test files use `Base.metadata.create_all(engine)` with a sync engine:

- `tests/test_repositories/test_instrument_repository.py`
- `tests/integration/test_user_management_flow.py`
- `tests/test_api/test_instruments_api.py`
- `tests/test_api/test_users.py`

After the sync engine is removed, these fixtures must switch to the async pattern:

```python
# Before
Base.metadata.create_all(bind=test_engine)

# After
async with test_async_engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

Each fixture must become an `async` fixture using `pytest-asyncio`.

**Configuration required:** Add the following to `pyproject.toml` (or `pytest.ini`) so `pytest-asyncio` automatically handles async fixtures without requiring `@pytest.mark.asyncio` on every test:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

This is part of the final cut-over step, not individual waves.

## Section 6: Per-Wave Verification

After each wave:

1. Run pytest: `uv run pytest -m "not hardware"` from `backend/`
2. Rebuild and smoke-test:
   ```bash
   docker-compose up -d --build
   docker-compose logs -f backend
   # Manually hit representative endpoints for the migrated wave
   ```

### Final cut-over verification

```bash
uv run pytest                          # Full suite including updated fixtures
curl http://localhost:9100/health
# Hit one endpoint from each wave to confirm no regression
```

Confirm `pymysql` is no longer imported anywhere in the project source (excluding `.venv`):
```bash
grep -r "pymysql" backend/app backend/tests
```

## Dependencies

Add to `backend/pyproject.toml`:
```
asyncmy
pytest-asyncio  # if not already present
```

`pymysql` removed only after Wave 6 + final cut-over.
