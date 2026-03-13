# Async DB Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the FastAPI backend from sync SQLAlchemy (`pymysql` + `Session`) to SQLAlchemy 2.0 async (`asyncmy` + `AsyncSession`) in six incremental waves, each independently testable.

**Architecture:** Add `get_async_db` alongside existing `get_db` in `database.py`. Add async helper functions alongside existing sync helpers in `api_helpers.py`. Migrate routers and their service/repository dependencies one wave at a time. `InstrumentConfigProvider` stays sync and receives a `session_factory` callable instead of a single session. Remove sync engine and `pymysql` only after Wave 6.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, asyncmy, pytest-asyncio, Docker Compose

> **Note on test failures during migration:** Tests using `Base.metadata.create_all(bind=test_engine)` (in `test_instrument_repository.py`, `test_user_management_flow.py`, `test_instruments_api.py`, `test_users.py`) will continue to use the sync engine until the Final Cut-over step. This is expected and intentional — those fixtures are only updated in Chunk 8.

---

## File Structure

| Action | File | What changes |
|--------|------|--------------|
| Modify | `backend/pyproject.toml` | Add `asyncmy`; add `asyncio_mode = "auto"` (final step) |
| Modify | `backend/app/core/database.py` | Add async engine, `AsyncSessionLocal`, `get_async_db` |
| Modify | `backend/app/core/api_helpers.py` | Add async versions of `get_entity_or_404` and `get_entity_by_field_or_404` |
| Modify | `backend/app/services/auth.py` | Wave 1: all functions become `async def` |
| Modify | `backend/app/api/auth.py` | Wave 1: `get_db` → `get_async_db`, use async helpers |
| Modify | `backend/app/api/users.py` | Wave 1: same pattern |
| Modify | `backend/app/api/projects.py` | Wave 2 |
| Modify | `backend/app/api/stations.py` | Wave 2 |
| Modify | `backend/app/repositories/instrument_repository.py` | Wave 3: add `AsyncInstrumentRepository` class |
| Modify | `backend/app/core/instrument_config.py` | Wave 3: `InstrumentConfigProvider` uses `session_factory` callable |
| Modify | `backend/app/api/instruments.py` | Wave 3 |
| Modify | `backend/app/main.py` | Wave 3: update startup provider init |
| Modify | `backend/app/api/testplan/queries.py` | Wave 4 |
| Modify | `backend/app/api/testplan/mutations.py` | Wave 4 |
| Modify | `backend/app/api/testplan/sessions.py` | Wave 4 |
| Modify | `backend/app/api/testplan/validation.py` | Wave 4 |
| Modify | `backend/app/services/test_plan_service.py` | Wave 4 |
| Modify | `backend/app/api/results/sessions.py` | Wave 5 |
| Modify | `backend/app/api/results/measurements.py` | Wave 5 |
| Modify | `backend/app/api/results/summary.py` | Wave 5 |
| Modify | `backend/app/api/results/export.py` | Wave 5 |
| Modify | `backend/app/api/results/cleanup.py` | Wave 5 |
| Modify | `backend/app/api/results/reports.py` | Wave 5 |
| Modify | `backend/app/api/results/analysis.py` | Wave 5 |
| Modify | `backend/app/api/tests.py` | Wave 6 |
| Modify | `backend/app/api/measurements.py` | Wave 6 |
| Modify | `backend/app/services/test_engine.py` | Wave 6: full async rewrite of DB methods |
| Modify | `backend/app/services/measurement_service.py` | Wave 6 |
| Modify | `backend/app/services/report_service.py` | Wave 6 |
| Modify | `backend/tests/test_repositories/test_instrument_repository.py` | Final: async fixtures |
| Modify | `backend/tests/integration/test_user_management_flow.py` | Final: async fixtures |
| Modify | `backend/tests/test_api/test_instruments_api.py` | Final: async fixtures |
| Modify | `backend/tests/test_api/test_users.py` | Final: async fixtures |

---

## Standard Migration Pattern (reference for all waves)

Every router file follows these steps. Refer back to this section for each wave.

### Imports
```python
# Remove these
from sqlalchemy.orm import Session
from app.core.database import get_db

# Add these
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_db
```

### Endpoint signatures
```python
# Before
def endpoint(..., db: Session = Depends(get_db)):

# After
async def endpoint(..., db: AsyncSession = Depends(get_async_db)):
```

### ORM reads — simple
```python
# Before
item = db.query(Model).filter(Model.id == id).first()
items = db.query(Model).filter(Model.field == value).all()

# After
result = await db.execute(select(Model).where(Model.id == id))
item = result.scalar_one_or_none()

result = await db.execute(select(Model).where(Model.field == value))
items = result.scalars().all()
```

### ORM reads — query-builder pattern (conditional filters)
Some endpoints build up a query object across multiple `if` branches before executing. Translate like this:
```python
# Before
query = db.query(Model)
if condition_a:
    query = query.filter(Model.field_a == value_a)
if condition_b:
    query = query.filter(Model.field_b == value_b)
items = query.offset(skip).limit(limit).all()

# After
stmt = select(Model)
if condition_a:
    stmt = stmt.where(Model.field_a == value_a)
if condition_b:
    stmt = stmt.where(Model.field_b == value_b)
result = await db.execute(stmt.offset(skip).limit(limit))
items = result.scalars().all()
```

### ORM reads — count
```python
# Before
count = db.query(Model).filter(...).count()

# After
from sqlalchemy import func
result = await db.execute(select(func.count()).select_from(Model).where(...))
count = result.scalar()
```

### ORM reads — db.get()
```python
# Before
obj = db.get(Model, pk)

# After
obj = await db.get(Model, pk)
```

### ORM writes
```python
# Before
db.add(obj); db.commit(); db.refresh(obj)

# After
db.add(obj); await db.commit(); await db.refresh(obj)
```

### ORM deletes
```python
# Before
db.delete(obj); db.commit()

# After
await db.delete(obj); await db.commit()
```

### Async helper calls
Replace calls to sync `get_entity_or_404` and `get_entity_by_field_or_404` with their async versions (added in Chunk 1):
```python
# Before
entity = get_entity_or_404(db, Model, entity_id)
entity = get_entity_by_field_or_404(db, Model, "field", value)

# After
entity = await async_get_entity_or_404(db, Model, entity_id)
entity = await async_get_entity_by_field_or_404(db, Model, "field", value)
```

---

## Chunk 1: Foundation — database.py + api_helpers.py + asyncmy

### Task 1: Add asyncmy and async DB infrastructure

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/database.py`
- Modify: `backend/app/core/api_helpers.py`

- [ ] **Step 1: Add asyncmy to pyproject.toml**

In `backend/pyproject.toml`, add `asyncmy>=0.2.7` to the `dependencies` list after the `pymysql` line:

```toml
    "pymysql>=1.1.0",
    "asyncmy>=0.2.7",
```

- [ ] **Step 2: Install asyncmy**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv add asyncmy
```

Expected: `asyncmy` added to lock file, no errors.

- [ ] **Step 3: Add async engine and session factory to database.py**

In `backend/app/core/database.py`, add the following imports at the top of the file alongside the existing imports:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
```

Then add the following after the existing `SessionLocal` and `Base` definitions:

```python
# Async engine and session factory (SQLAlchemy 2.0)
# Uses same DB settings as sync engine (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
ASYNC_DATABASE_URL = f"mysql+asyncmy://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,       # required — omitting this produces sync sessions
    expire_on_commit=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an AsyncSession, rolls back on exception."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 4: Add async helper functions to api_helpers.py**

In `backend/app/core/api_helpers.py`, add these imports at the top alongside the existing ones:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
```

Then add the following two async functions after the existing sync `get_entity_by_field_or_404` function:

```python
async def async_get_entity_or_404(
    db: AsyncSession,
    model: Type[T],
    entity_id: int,
    detail: Optional[str] = None
) -> T:
    """Async version of get_entity_or_404 for use with AsyncSession."""
    entity = await db.get(model, entity_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or f"{model.__name__} not found"
        )
    return entity


async def async_get_entity_by_field_or_404(
    db: AsyncSession,
    model: Type[T],
    field_name: str,
    field_value: Any,
    detail: Optional[str] = None
) -> T:
    """Async version of get_entity_by_field_or_404 for use with AsyncSession."""
    stmt = select(model).filter_by(**{field_name: field_value})
    result = await db.execute(stmt)
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or f"{model.__name__} with {field_name}='{field_value}' not found"
        )
    return entity
```

- [ ] **Step 5: Verify imports work**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run python -c "
from app.core.database import AsyncSessionLocal, get_async_db
from app.core.api_helpers import async_get_entity_or_404, async_get_entity_by_field_or_404
print('OK')
"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/app/core/database.py backend/app/core/api_helpers.py
git commit -m "feat: add asyncmy, async SQLAlchemy session factory, and async API helpers"
```

---

## Chunk 2: Wave 1 — auth + users

### Task 2: Migrate services/auth.py to async

**Files:**
- Modify: `backend/app/services/auth.py`

- [ ] **Step 1: Replace entire content of auth.py with async version**

```python
"""Authentication service"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import verify_password, get_password_hash


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Create new user"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
        full_name=user.full_name,
        email=user.email,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(db: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
    """Update user information"""
    user = await get_user_by_id(db, user_id)   # await intra-function call
    if not user:
        return None
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user
```

- [ ] **Step 2: Run tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -m "not hardware" -v 2>&1 | tail -20
```

Expected: No new failures vs before this change.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/auth.py
git commit -m "feat(wave1): migrate auth service to AsyncSession"
```

### Task 3: Migrate api/auth.py to async

**Files:**
- Modify: `backend/app/api/auth.py`

- [ ] **Step 1: Update imports**

Replace:
```python
from sqlalchemy.orm import Session
from app.core.database import get_db
```
With:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.api_helpers import async_get_entity_by_field_or_404
```

- [ ] **Step 2: Update all endpoint signatures**

Change all `db: Session = Depends(get_db)` → `db: AsyncSession = Depends(get_async_db)`.
Make all endpoints `async def`.

- [ ] **Step 3: Update service calls to await**

All calls to `authenticate_user`, `get_user_by_username`, `get_user_by_id` are now async:
```python
user = await authenticate_user(db, ...)
user = await get_user_by_username(db, ...)
user = await get_user_by_id(db, ...)
```

- [ ] **Step 4: Replace sync helper call**

The `GET /me` endpoint calls `get_entity_by_field_or_404(db, UserModel, "username", ...)`. Replace with:
```python
user = await async_get_entity_by_field_or_404(db, UserModel, "username", username)
```
Also update the import — remove `get_entity_by_field_or_404` from api_helpers import if it's no longer used in auth.py.

- [ ] **Step 5: Run tests**

```bash
uv run pytest -m "not hardware" -k "auth" -v 2>&1 | tail -20
```

- [ ] **Step 6: Docker smoke test**

```bash
cd /home/ubuntu/python_code/WebPDTool
docker-compose up -d --build
curl -s -X POST http://localhost:9100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -m json.tool
```

Expected: Returns JSON with `access_token`.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/auth.py
git commit -m "feat(wave1): migrate auth API to AsyncSession"
```

### Task 4: Migrate api/users.py to async

**Files:**
- Modify: `backend/app/api/users.py`

- [ ] **Step 1: Update imports**

Replace:
```python
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.api_helpers import PermissionChecker, get_entity_or_404
```
With:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_async_db
from app.core.api_helpers import PermissionChecker, async_get_entity_or_404
```

- [ ] **Step 2: Update all endpoint signatures**

Change `db: Session = Depends(get_db)` → `db: AsyncSession = Depends(get_async_db)`.
Make all endpoints `async def`.

- [ ] **Step 3: Replace all get_entity_or_404 calls (4 locations)**

All four endpoints (`get_user`, `update_user`, `change_user_password`, `delete_user`) call `get_entity_or_404`. Replace each:
```python
# Before
db_user = get_entity_or_404(db, UserModel, user_id, ErrorMessages.USER_NOT_FOUND)

# After
db_user = await async_get_entity_or_404(db, UserModel, user_id, ErrorMessages.USER_NOT_FOUND)
```
Also update the import line — replace `get_entity_or_404` with `async_get_entity_or_404` in the `from app.core.api_helpers import ...` line.

- [ ] **Step 4: Replace query-builder pattern in get_users endpoint**

The actual `get_users` endpoint uses `or_()` across 3 columns for search, plus `order_by`. Translate:

```python
# After
stmt = select(UserModel)

if search:
    search_pattern = f"%{search}%"
    stmt = stmt.where(
        or_(
            UserModel.username.like(search_pattern),
            UserModel.full_name.like(search_pattern),
            UserModel.email.like(search_pattern)
        )
    )
if role is not None:
    stmt = stmt.where(UserModel.role == role)
if is_active is not None:
    stmt = stmt.where(UserModel.is_active == is_active)

stmt = stmt.order_by(UserModel.username.asc())
result = await db.execute(stmt.offset(offset).limit(limit))
users = result.scalars().all()
return users
```

Keep `from sqlalchemy import or_` in the imports (already present in original file).

- [ ] **Step 5: Migrate create_user endpoint inline query**

The `create_user` endpoint checks for duplicate username with a direct `db.query`. Migrate it:

```python
# Before
existing_user = db.query(UserModel).filter(UserModel.username == user.username).first()

# After
result = await db.execute(select(UserModel).where(UserModel.username == user.username))
existing_user = result.scalar_one_or_none()
```

Then update the service call — `auth_service.create_user` is now async:
```python
db_user = await auth_service.create_user(db, user)
```

- [ ] **Step 6: Migrate update_user, change_user_password, delete_user write operations**

`update_user` applies the `USER_UPDATE_WHITELIST` guard inline (does NOT call `auth_service.update_user`). Just migrate the commit/refresh:
```python
await db.commit(); await db.refresh(db_user)
```

`change_user_password`:
```python
await db.commit(); await db.refresh(db_user)
```

`delete_user`:
```python
await db.delete(db_user); await db.commit()
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest -m "not hardware" -k "user" -v 2>&1 | tail -20
```

- [ ] **Step 7: Docker smoke test**

```bash
TOKEN=$(curl -s -X POST http://localhost:9100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:9100/api/users -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Returns user list JSON.

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/users.py
git commit -m "feat(wave1): migrate users API to AsyncSession"
```

---

## Chunk 3: Wave 2 — projects + stations

### Task 5: Migrate api/projects.py and api/stations.py to async

**Files:**
- Modify: `backend/app/api/projects.py`
- Modify: `backend/app/api/stations.py`

Apply the Standard Migration Pattern to both files. Neither file uses `api_helpers` sync helpers — only direct `db.query(...)` calls.

- [ ] **Step 1: Migrate projects.py**

1. Update imports (Standard Pattern)
2. All endpoints `async def`
3. All `db.query(...)` → `await db.execute(select(...))` + `.scalar_one_or_none()` or `.scalars().all()`
4. All `db.commit()` → `await db.commit()`, `db.refresh()` → `await db.refresh()`
5. All `db.delete(obj)` → `await db.delete(obj)`

- [ ] **Step 2: Migrate stations.py** (same steps)

- [ ] **Step 3: Run tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -m "not hardware" -v 2>&1 | tail -30
```

- [ ] **Step 4: Docker smoke test**

```bash
curl -s http://localhost:9100/api/projects -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Returns projects list.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/projects.py backend/app/api/stations.py
git commit -m "feat(wave2): migrate projects and stations API to AsyncSession"
```

---

## Chunk 4: Wave 3 — instruments + InstrumentConfigProvider

### Task 6: Add AsyncInstrumentRepository

**Files:**
- Modify: `backend/app/repositories/instrument_repository.py`

- [ ] **Step 1: Add AsyncInstrumentRepository class at the bottom of the file**

The existing sync `InstrumentRepository` class stays unchanged. Add after it:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select


class AsyncInstrumentRepository:
    """Async variant used by API routers with AsyncSession.
    The sync InstrumentRepository is kept for InstrumentConfigProvider's cache refreshes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, instrument_pk: int) -> Optional[Instrument]:
        return await self.db.get(Instrument, instrument_pk)

    async def get_by_instrument_id(self, instrument_id: str) -> Optional[Instrument]:
        result = await self.db.execute(
            sa_select(Instrument).where(Instrument.instrument_id == instrument_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Instrument]:
        result = await self.db.execute(
            sa_select(Instrument).order_by(Instrument.instrument_id)
        )
        return result.scalars().all()

    async def list_enabled(self) -> List[Instrument]:
        result = await self.db.execute(
            sa_select(Instrument)
            .where(Instrument.enabled.is_(True))
            .order_by(Instrument.instrument_id)
        )
        return result.scalars().all()

    async def create(self, data: InstrumentCreate) -> Instrument:
        inst = Instrument(**data.model_dump())
        self.db.add(inst)
        await self.db.commit()
        await self.db.refresh(inst)
        return inst

    async def update(self, instrument_pk: int, data: InstrumentUpdate) -> Optional[Instrument]:
        inst = await self.get_by_id(instrument_pk)   # await intra-class call
        if inst is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(inst, field, value)
        await self.db.commit()
        await self.db.refresh(inst)
        return inst

    async def delete(self, instrument_pk: int) -> bool:
        inst = await self.get_by_id(instrument_pk)   # await intra-class call
        if inst is None:
            return False
        await self.db.delete(inst)
        await self.db.commit()
        return True
```

Note: `Optional`, `List`, `Instrument`, `InstrumentCreate`, `InstrumentUpdate` are already imported at the top of the file — the new class relies on those existing imports.

- [ ] **Step 2: Verify import**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run python -c "from app.repositories.instrument_repository import AsyncInstrumentRepository; print('OK')"
```

Expected: `OK`

### Task 7: Refactor InstrumentConfigProvider to use session_factory

**Files:**
- Modify: `backend/app/core/instrument_config.py`

The `InstrumentConfigProvider` currently stores a `self._repo` instance and calls `self._repo.list_enabled()` etc. synchronously. After the repo is migrated to async, these calls break. The fix: accept a `session_factory` callable and create a fresh `InstrumentRepository` per refresh.

Only three internal methods change (`__init__`, `_refresh_cache`, `_build_all_map`, `get_instrument`). All other methods (`_get_cache`, `list_instruments`, `list_enabled_instruments`, `invalidate_cache`, `_row_to_config`) remain unchanged.

- [ ] **Step 1: Update __init__ signature**

```python
# Before
def __init__(self, repo, cache_ttl: float = 30.0):
    self._repo = repo
    ...

# After
def __init__(self, session_factory, cache_ttl: float = 30.0):
    # session_factory: callable returning a new sync Session (e.g. SessionLocal)
    self._session_factory = session_factory
    self._cache_ttl = cache_ttl
    self._cache: Optional[Dict[str, InstrumentConfig]] = None
    self._cache_time: float = 0.0
    self._lock = threading.Lock()
```

- [ ] **Step 2: Update _refresh_cache**

```python
def _refresh_cache(self) -> Dict[str, InstrumentConfig]:
    """Fetch enabled instruments from DB, populate cache."""
    with self._lock:
        if (self._cache is not None and
                (_time.monotonic() - self._cache_time) < self._cache_ttl):
            return dict(self._cache)
    # Open a short-lived session for this refresh (outside lock to avoid blocking other threads during I/O)
    db = self._session_factory()
    try:
        from app.repositories.instrument_repository import InstrumentRepository
        rows = InstrumentRepository(db).list_enabled()
        result = {row.instrument_id: self._row_to_config(row) for row in rows}
    finally:
        db.close()
    # Two threads may race here if both passed the TTL check above — last writer wins (harmless)
    with self._lock:
        self._cache = result
        self._cache_time = _time.monotonic()
        return dict(result)
```

- [ ] **Step 3: Update _build_all_map**

```python
def _build_all_map(self) -> Dict[str, InstrumentConfig]:
    db = self._session_factory()
    try:
        from app.repositories.instrument_repository import InstrumentRepository
        rows = InstrumentRepository(db).list_all()
        return {row.instrument_id: self._row_to_config(row) for row in rows}
    finally:
        db.close()
```

- [ ] **Step 4: Update get_instrument**

```python
def get_instrument(self, instrument_id: str) -> Optional[InstrumentConfig]:
    """Lookup by logical ID. Uses cache; falls back to direct DB query on miss."""
    cached = self._get_cache()
    if cached is not None and instrument_id in cached:
        return cached[instrument_id]
    db = self._session_factory()
    try:
        from app.repositories.instrument_repository import InstrumentRepository
        row = InstrumentRepository(db).get_by_instrument_id(instrument_id)
        return self._row_to_config(row) if row else None
    finally:
        db.close()
```

- [ ] **Step 5: Delete get_instrument_provider function**

The `get_instrument_provider(db)` function at the bottom of `instrument_config.py` has no callers outside its own docstring. Verify this first:

```bash
grep -rn "get_instrument_provider" /home/ubuntu/python_code/WebPDTool/backend/app /home/ubuntu/python_code/WebPDTool/backend/tests --include="*.py"
```

Expected output: Only the function definition itself and its internal docstring reference. If that's the case, delete the entire `get_instrument_provider` function.

### Task 8: Update main.py startup and migrate instruments API

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/instruments.py`

- [ ] **Step 1: Update main.py startup provider block**

In `backend/app/main.py`, replace the startup provider initialization block:

```python
# Before
try:
    from app.core.database import SessionLocal as SyncSessionLocal
    from app.repositories.instrument_repository import InstrumentRepository
    from app.core.instrument_config import InstrumentConfigProvider, set_global_instrument_provider
    # Fix: close the startup session after provider is initialized to prevent session leak
    db = SyncSessionLocal()
    try:
        repo = InstrumentRepository(db)
        provider = InstrumentConfigProvider(repo=repo, cache_ttl=30.0)
        set_global_instrument_provider(provider)
        logger.info("Global DB-backed InstrumentConfigProvider initialized")
    finally:
        db.close()
except Exception as e:
    logger.warning(f"Failed to initialize DB instrument provider (fallback to hardcoded): {e}")

# After
try:
    from app.core.database import SessionLocal as SyncSessionLocal
    from app.core.instrument_config import InstrumentConfigProvider, set_global_instrument_provider
    # Pass session_factory so provider creates its own session per cache refresh
    provider = InstrumentConfigProvider(session_factory=SyncSessionLocal, cache_ttl=30.0)
    set_global_instrument_provider(provider)
    logger.info("Global DB-backed InstrumentConfigProvider initialized")
except Exception as e:
    logger.warning(f"Failed to initialize DB instrument provider (fallback to hardcoded): {e}")
```

Note: `InstrumentRepository` import is no longer needed here — remove it if it appears.

- [ ] **Step 2: Migrate api/instruments.py**

In `backend/app/api/instruments.py`:

1. Replace imports:
```python
# Remove
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.instrument_repository import InstrumentRepository

# Add
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.repositories.instrument_repository import AsyncInstrumentRepository
```

2. Update `_get_repo` dependency function:
```python
async def _get_repo(db: AsyncSession = Depends(get_async_db)) -> AsyncInstrumentRepository:
    return AsyncInstrumentRepository(db)
```

3. Make all endpoints `async def` and `await` all repo method calls. The `list_instruments` endpoint uses `enabled_only` query param to choose between `list_enabled` and `list_all` — preserve this logic:
```python
# Before
def list_instruments(enabled_only: bool = Query(False, ...), repo: InstrumentRepository = Depends(_get_repo)):
    rows = repo.list_enabled() if enabled_only else repo.list_all()
    return rows

# After
async def list_instruments(enabled_only: bool = Query(False, ...), repo: AsyncInstrumentRepository = Depends(_get_repo)):
    rows = await repo.list_enabled() if enabled_only else await repo.list_all()
    return rows
```

For `create_instrument`, `get_instrument`, `update_instrument`, `delete_instrument`: all `repo.*` calls get `await`. The `update_instrument` endpoint calls `repo.get_by_instrument_id(instrument_id)` first then `repo.update(inst.id, data)` — both need `await`. The `delete_instrument` endpoint does the same — `await repo.get_by_instrument_id(...)` then `await repo.delete(inst.id)`.

- [ ] **Step 3: Run tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -m "not hardware" -v 2>&1 | tail -30
```

- [ ] **Step 4: Docker smoke test**

```bash
docker-compose up -d --build
curl -s http://localhost:9100/api/instruments -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Returns instruments list.

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/instrument_repository.py \
        backend/app/core/instrument_config.py \
        backend/app/api/instruments.py \
        backend/app/main.py
git commit -m "feat(wave3): migrate instruments to AsyncSession; provider uses session_factory"
```

---

## Chunk 5: Wave 4 — testplan

### Task 9: Migrate testplan routers and test_plan_service.py

**Files:**
- Modify: `backend/app/api/testplan/queries.py`
- Modify: `backend/app/api/testplan/mutations.py`
- Modify: `backend/app/api/testplan/sessions.py`
- Modify: `backend/app/api/testplan/validation.py`
- Modify: `backend/app/services/test_plan_service.py`

Apply the Standard Migration Pattern to all five files. Check each for:
- sync helper calls (`get_entity_or_404` → `async_get_entity_or_404`)
- query-builder pattern (see Standard Pattern section)
- service method calls from routers that are now async (need `await`)

- [ ] **Step 1: Migrate queries.py** (Standard Pattern)
- [ ] **Step 2: Migrate mutations.py** (Standard Pattern)
- [ ] **Step 3: Migrate sessions.py** (Standard Pattern)
- [ ] **Step 4: Migrate validation.py** (Standard Pattern)
- [ ] **Step 5: Migrate test_plan_service.py** (Standard Pattern — service functions become `async def`)

- [ ] **Step 6: Run tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -m "not hardware" -v 2>&1 | tail -30
```

- [ ] **Step 7: Docker smoke test**

```bash
curl -s "http://localhost:9100/api/stations/1/testplan" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Returns test plan list (may be empty array `[]`).

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/testplan/ backend/app/services/test_plan_service.py
git commit -m "feat(wave4): migrate testplan routers and service to AsyncSession"
```

---

## Chunk 6: Wave 5 — results

### Task 10: Migrate all results routers to async

**Files:**
- Modify: `backend/app/api/results/sessions.py`
- Modify: `backend/app/api/results/measurements.py`
- Modify: `backend/app/api/results/summary.py`
- Modify: `backend/app/api/results/export.py`
- Modify: `backend/app/api/results/cleanup.py`
- Modify: `backend/app/api/results/reports.py`
- Modify: `backend/app/api/results/analysis.py`

Apply Standard Migration Pattern to all seven files.

Special attention for complex files:
- **`export.py`**: likely has multi-join queries and `StreamingResponse`. Translate each `db.query(...).join(...).filter(...).all()` to `select(...).join(...).where(...).all()` (see Standard Pattern query-builder section). `StreamingResponse` is unaffected.
- **`analysis.py`**: uses aggregation queries. Translate `db.query(func.avg(...))` to `await db.execute(select(func.avg(...)))` + `.scalar()`.
- **`sessions.py`**: has the query-builder pattern for conditional filters — apply the `stmt = select(Model)` + conditional `.where(...)` chaining approach.

- [ ] **Step 1: Migrate sessions.py**
- [ ] **Step 2: Migrate measurements.py**
- [ ] **Step 3: Migrate summary.py**
- [ ] **Step 4: Migrate export.py**
- [ ] **Step 5: Migrate cleanup.py**
- [ ] **Step 6: Migrate reports.py**
- [ ] **Step 7: Migrate analysis.py**

- [ ] **Step 8: Run tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -m "not hardware" -v 2>&1 | tail -30
```

- [ ] **Step 9: Docker smoke test**

```bash
curl -s "http://localhost:9100/api/measurement-results/sessions" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Returns sessions list (may be empty array).

- [ ] **Step 10: Commit**

```bash
git add backend/app/api/results/
git commit -m "feat(wave5): migrate results routers to AsyncSession"
```

---

## Chunk 7: Wave 6 — test engine + execution APIs

### Task 11: Migrate report_service.py to async

**Files:**
- Modify: `backend/app/services/report_service.py`

- [ ] **Step 1: Identify all DB calls in report_service.py**

```bash
grep -n "db\.\|Session\|get_db" /home/ubuntu/python_code/WebPDTool/backend/app/services/report_service.py
```

- [ ] **Step 2: Migrate report_service.py**

Apply Standard Migration Pattern:
- All functions accepting `db: Session` become `async def` with `db: AsyncSession`
- All `db.query(...)` → `await db.execute(select(...))`
- All `db.commit()` / `db.refresh()` → `await db.commit()` / `await db.refresh()`

### Task 12: Migrate test_engine.py to async

**Files:**
- Modify: `backend/app/services/test_engine.py`

This file constructs its session directly (not via dependency injection) and has 4 DB-touching methods. Migrate each carefully.

- [ ] **Step 1: Update imports**

```python
# Remove
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

# Add
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
```

- [ ] **Step 2: Update _execute_test_session to own an AsyncSession**

```python
async def _execute_test_session(
    self,
    session_id: int,
    station_id: int,
):
    """Execute test session in background. Creates its own AsyncSession."""
    test_state = self.active_tests[session_id]
    try:
        async with AsyncSessionLocal() as db:
            # Get test plan items
            result = await db.execute(
                select(TestPlan)
                .where(TestPlan.station_id == station_id)
                .order_by(TestPlan.sequence_order)
            )
            test_plan_items = result.scalars().all()

            if not test_plan_items:
                raise ValueError(f"No test plan found for station {station_id}")

            self.logger.info(f"Starting test session {session_id} with {len(test_plan_items)} items")

            # Get station configuration
            result = await db.execute(select(Station).where(Station.id == station_id))
            station = result.scalar_one_or_none()
            config = self._load_configuration(station)

            # Execute each test item
            for idx, test_plan_item in enumerate(test_plan_items):
                if test_state.should_stop:
                    test_state.status = "ABORTED"
                    self.logger.warning(f"Test session {session_id} aborted by user")
                    break

                test_state.current_item_index = idx

                result_item = await self._execute_measurement(session_id, test_plan_item, config, db)
                test_state.results.append(result_item)
                await self._save_test_result(session_id, test_plan_item.id, result_item, db)

                if result_item.result == "FAIL" and config.get("stop_on_fail", False):
                    test_state.status = "ABORTED"
                    self.logger.warning(f"Test session {session_id} aborted due to failure on {result_item.item_name}")
                    break

            if test_state.status != "ABORTED":
                test_state.status = "COMPLETED"

            await self._finalize_test_session(session_id, test_state, db)

    except Exception as e:
        self.logger.error(f"Error executing test session {session_id}: {e}", exc_info=True)
        test_state.status = "ERROR"
        test_state.error = str(e)
        # Try to finalize with error state — open a new session since we may be outside the async with
        try:
            async with AsyncSessionLocal() as db:
                await self._finalize_test_session(session_id, test_state, db)
        except Exception as finalize_error:
            self.logger.error(f"Error finalizing failed session: {finalize_error}")

    finally:
        async with self._lock:
            if session_id in self.active_tests:
                del self.active_tests[session_id]
```

- [ ] **Step 3: Update _execute_measurement signature**

```python
async def _execute_measurement(
    self,
    session_id: int,
    test_plan_item: TestPlan,
    config: Dict[str, Any],
    db: AsyncSession          # was: db: Session
) -> MeasurementResult:
```

The body only reads attributes from `test_plan_item` (already loaded into memory) — no `db` calls needed inside this method. Confirm there are no `db.query(...)` calls in its body.

- [ ] **Step 4: Update _save_test_result**

```python
async def _save_test_result(
    self,
    session_id: int,
    test_plan_id: int,
    result: MeasurementResult,
    db: AsyncSession
):
    try:
        db_result = TestResultModel(
            session_id=session_id,
            test_plan_id=test_plan_id,
            item_no=result.item_no,
            item_name=result.item_name,
            measured_value=result.measured_value,
            lower_limit=result.lower_limit,
            upper_limit=result.upper_limit,
            unit=result.unit,
            result=ItemResult(result.result),
            error_message=result.error_message,
            execution_duration_ms=result.execution_duration_ms
        )
        db.add(db_result)
        await db.commit()
    except Exception as e:
        self.logger.error(f"Error saving test result: {e}", exc_info=True)
        await db.rollback()
```

- [ ] **Step 5: Update _finalize_test_session**

```python
async def _finalize_test_session(
    self,
    session_id: int,
    test_state: TestExecutionState,
    db: AsyncSession
):
    try:
        result = await db.execute(
            select(TestSessionModel).where(TestSessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            self.logger.error(f"Session {session_id} not found in database")
            return

        # ... all attribute assignments stay unchanged ...

        await db.commit()

        # report_service.save_session_report is now async
        try:
            report_path = await report_service.save_session_report(session_id, db)
            if report_path:
                self.logger.info(f"Test report saved: {report_path}")
        except Exception as report_error:
            self.logger.error(f"Error generating report: {report_error}")

    except Exception as e:
        self.logger.error(f"Error finalizing session {session_id}: {e}", exc_info=True)
```

- [ ] **Step 6: Remove db parameter from start_test_session**

```python
async def start_test_session(
    self,
    session_id: int,
    serial_number: str,
    station_id: int,
    # db: Session  <-- remove this parameter; engine owns its session
) -> Dict[str, Any]:
    ...
    asyncio.create_task(
        self._execute_test_session(session_id, station_id)   # no db passed
    )
```

### Task 13: Migrate api/tests.py and api/measurements.py

**Files:**
- Modify: `backend/app/api/tests.py`
- Modify: `backend/app/api/measurements.py`

- [ ] **Step 1: Migrate api/tests.py**

Apply Standard Migration Pattern. For the `start_test_session` endpoint, remove `db=db` from the engine call (since `start_test_session` no longer accepts `db`):

```python
# Before
result = await test_engine.start_test_session(
    session_id=session_id,
    serial_number=session.serial_number,
    station_id=session.station_id,
    db=db
)

# After
result = await test_engine.start_test_session(
    session_id=session_id,
    serial_number=session.serial_number,
    station_id=session.station_id,
)
```

Keep `db: AsyncSession = Depends(get_async_db)` in the endpoint — it is still used for direct session/plan queries in the same endpoint.

- [ ] **Step 2: Migrate api/measurements.py** (Standard Pattern)

- [ ] **Step 3: Run tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -m "not hardware" -v 2>&1 | tail -30
```

- [ ] **Step 4: Docker smoke test**

```bash
docker-compose up -d --build
docker-compose logs backend 2>&1 | grep -E "ERROR|WARNING" | head -20
curl -s -X POST "http://localhost:9100/api/tests/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"station_id":1,"serial_number":"TEST001"}' | python3 -m json.tool
```

Expected: New session created with `"id": <n>`.

- [ ] **Step 5: Commit Wave 6**

```bash
git add backend/app/services/test_engine.py \
        backend/app/services/report_service.py \
        backend/app/services/measurement_service.py \
        backend/app/api/tests.py \
        backend/app/api/measurements.py
git commit -m "feat(wave6): migrate test engine and execution APIs to AsyncSession"
```

---

## Chunk 8: Final Cut-over

### Task 14: Remove sync engine and update test fixtures

**Files:**
- Modify: `backend/app/core/database.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/tests/test_repositories/test_instrument_repository.py`
- Modify: `backend/tests/integration/test_user_management_flow.py`
- Modify: `backend/tests/test_api/test_instruments_api.py`
- Modify: `backend/tests/test_api/test_users.py`

- [ ] **Step 1: Verify no remaining get_db or sync Session usage in app/**

```bash
grep -rn "get_db\|from sqlalchemy.orm import Session" \
  /home/ubuntu/python_code/WebPDTool/backend/app --include="*.py"
```

Expected: Only `SyncSessionLocal` used in `instrument_config.py` (for the provider's session factory). Fix any remaining hits before proceeding.

- [ ] **Step 2: Keep SyncSessionLocal for InstrumentConfigProvider, remove get_db**

In `backend/app/core/database.py`:
- Remove `get_db` function
- Keep `engine`, `SessionLocal` (renamed or labelled as sync, used by `InstrumentConfigProvider`)
- Keep all async objects

Add a comment to clarify:
```python
# Sync engine kept for InstrumentConfigProvider's cache refreshes (sync by design).
# All API routers use get_async_db instead.
```

- [ ] **Step 3: Add asyncio_mode = "auto" to pyproject.toml**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 4: Add aiosqlite to dev dependencies**

`pyproject.toml` has TWO dev dependency sections — update both:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
    "aiosqlite>=0.19.0",   # add this
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
    "aiosqlite>=0.19.0",   # add this
]
```

Then install:
```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv sync
```

- [ ] **Step 5: Update test fixtures to async**

For each of the four test files, replace the sync engine + `create_all` fixture with this pattern:

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base

@pytest.fixture
async def async_test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(async_test_engine):
    """Provide an AsyncSession for each test, rolling back after."""
    AsyncTestSession = async_sessionmaker(async_test_engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncTestSession() as session:
        yield session
```

Update all test functions in those files:
- Change `def test_*` to `async def test_*`
- Replace sync `db` fixture with `db_session` (the async fixture above)
- Replace `db.query(...)` with `await db.execute(select(...))` in test body assertions
- Replace `db.commit()` with `await db.commit()`, etc.

For tests using `TestClient` (HTTP-level tests), replace with `httpx.AsyncClient` + `ASGITransport`:
```python
import httpx
from app.main import app

@pytest.fixture
async def client(db_session):
    # Override get_async_db dependency to use test session
    async def override_get_async_db():
        yield db_session
    app.dependency_overrides[get_async_db] = override_get_async_db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 6: Run full test suite**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -v 2>&1 | tail -40
```

Expected: All tests pass.

- [ ] **Step 7: Final Docker smoke test**

```bash
docker-compose up -d --build
docker-compose logs backend 2>&1 | grep -E "ERROR|WARNING|Starting" | head -20
curl -s http://localhost:9100/health
```

Expected: `{"status":"healthy"}`

- [ ] **Step 8: Confirm sync DB URL is clearly labelled in database.py**

Since `SyncSessionLocal` is kept for `InstrumentConfigProvider`, `database.py` still contains `DATABASE_URL = f"mysql+pymysql://..."`. This is intentional. Verify it has a clear comment:

```python
# Sync engine — kept for InstrumentConfigProvider's cache refreshes (sync by design).
# All API routers use get_async_db / AsyncSessionLocal instead.
DATABASE_URL = f"mysql+pymysql://..."
```

`pymysql` therefore stays in `pyproject.toml` and `database.py` — this is expected. Do NOT attempt to remove it until `InstrumentConfigProvider` is also migrated to async (future work).

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: complete async DB migration — remove get_db, update test fixtures"
```
