# Instrument Config Database Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate instrument configuration from file/env-based storage (`instrument_config.py`) to a MySQL database table, with a full CRUD REST API, so operators can manage instruments at runtime without restarting the server.

**Architecture:** Add an `instruments` table (ORM model + migration SQL), a CRUD service layer, and a new `/api/instruments` router. Replace the `InstrumentSettings` singleton with a DB-backed repository that keeps a short-lived in-memory cache (TTL = 30 s). Existing consumers (`InstrumentExecutor`, `InstrumentConnection`) call the same `get_instrument(id)` interface, so no changes are needed outside the configuration layer.

**Tech Stack:** SQLAlchemy (sync, pymysql), FastAPI, Pydantic v2, MySQL 8.0, pytest

---

## Chunk 1: Database Layer

### Task 1: Add `instruments` table to schema & ORM model

**Files:**
- Modify: `database/schema.sql` (append new table)
- Create: `backend/app/models/instrument.py`
- Modify: `backend/app/models/__init__.py` (export new model)

- [ ] **Step 1: Append table DDL to schema.sql**

Add at the end of `database/schema.sql`:

```sql
-- Instrument Configuration Table
-- Replaces instrument_config.py file/env-based storage
CREATE TABLE IF NOT EXISTS instruments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    instrument_id   VARCHAR(64) NOT NULL UNIQUE COMMENT 'Logical ID, e.g. DAQ973A_1',
    instrument_type VARCHAR(64) NOT NULL COMMENT 'Driver type, e.g. DAQ973A',
    name        VARCHAR(128) NOT NULL,
    conn_type   VARCHAR(32) NOT NULL COMMENT 'VISA | SERIAL | TCPIP_SOCKET | GPIB | LOCAL',
    conn_params JSON NOT NULL COMMENT 'Connection parameters (address, port, baudrate…)',
    enabled     TINYINT(1) NOT NULL DEFAULT 1,
    description TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_instruments_type (instrument_type),
    INDEX idx_instruments_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Instrument connection configurations (DB-backed, runtime editable)';
```

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_models/test_instrument_model.py`:

```python
"""Unit tests for Instrument ORM model."""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from app.models.base import Base
from app.models.instrument import Instrument

@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng

@pytest.fixture
def db(engine):
    with Session(engine) as s:
        yield s

def test_instrument_table_exists(engine):
    assert inspect(engine).has_table("instruments")

def test_instrument_required_columns(engine):
    cols = {c["name"] for c in inspect(engine).get_columns("instruments")}
    assert {"instrument_id", "instrument_type", "name", "conn_type", "conn_params",
            "enabled", "description", "created_at", "updated_at"}.issubset(cols)

def test_instrument_create_and_read(db):
    inst = Instrument(
        instrument_id="DAQ973A_1",
        instrument_type="DAQ973A",
        name="Keysight DAQ973A #1",
        conn_type="VISA",
        conn_params={"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000},
        enabled=True,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    assert inst.id is not None
    assert inst.instrument_id == "DAQ973A_1"

def test_instrument_unique_constraint(db):
    from sqlalchemy.exc import IntegrityError
    db.add(Instrument(
        instrument_id="DAQ973A_1",
        instrument_type="DAQ973A",
        name="Duplicate",
        conn_type="VISA",
        conn_params={},
    ))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_models/test_instrument_model.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` (model doesn't exist yet)

- [ ] **Step 4: Create ORM model**

Create `backend/app/models/instrument.py`:

```python
"""
Instrument ORM Model
Stores instrument connection configurations in the database,
replacing the file/env-based InstrumentSettings singleton.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Instrument(Base):
    """Database model for instrument connection configuration."""
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False,
                                               comment="Logical ID, e.g. DAQ973A_1")
    instrument_type: Mapped[str] = mapped_column(String(64), nullable=False,
                                                  comment="Driver type, e.g. DAQ973A")
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    conn_type: Mapped[str] = mapped_column(String(32), nullable=False,
                                           comment="VISA | SERIAL | TCPIP_SOCKET | GPIB | LOCAL")
    conn_params: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False,
                                                         comment="Connection parameters")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                  server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                  server_default=func.now(),
                                                  onupdate=func.now())
```

- [ ] **Step 5: Export from models `__init__.py`**

Open `backend/app/models/__init__.py` and add:
```python
from app.models.instrument import Instrument
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_models/test_instrument_model.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 7: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add database/schema.sql backend/app/models/instrument.py backend/app/models/__init__.py backend/tests/test_models/test_instrument_model.py
git commit -m "feat: add instruments table ORM model for DB-backed config"
```

---

### Task 2: Seed data migration script

**Files:**
- Create: `database/seed_instruments.sql`

- [ ] **Step 1: Create seed file**

Create `database/seed_instruments.sql`:

```sql
-- Seed: Default instruments (mirrors instrument_config.py defaults)
-- Run after schema.sql: mysql -u... webpdtool < database/seed_instruments.sql
INSERT INTO instruments (instrument_id, instrument_type, name, conn_type, conn_params, enabled, description)
VALUES
  ('DAQ973A_1', 'DAQ973A', 'Keysight DAQ973A #1',
   'VISA', '{"address":"TCPIP0::192.168.1.10::inst0::INSTR","timeout":5000}',
   0, 'Keysight DAQ973A data acquisition system'),

  ('MODEL2303_1', 'MODEL2303', 'Keysight 2303 Power Supply #1',
   'VISA', '{"address":"TCPIP0::192.168.1.11::inst0::INSTR","timeout":5000}',
   0, 'Keysight 2303 power supply'),

  ('console_1', 'console', 'Console Command (default)',
   'LOCAL', '{"address":"local://console"}',
   1, 'Virtual instrument for OS subprocess command execution'),

  ('comport_1', 'comport', 'COM Port Command (default)',
   'LOCAL', '{"address":"local://comport"}',
   1, 'Virtual instrument for serial port command execution'),

  ('tcpip_1', 'tcpip', 'TCP/IP Command (default)',
   'LOCAL', '{"address":"local://tcpip"}',
   1, 'Virtual instrument for TCP/IP socket command execution')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  conn_type = VALUES(conn_type),
  conn_params = VALUES(conn_params),
  description = VALUES(description);
```

- [ ] **Step 2: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add database/seed_instruments.sql
git commit -m "feat: add instruments seed data matching legacy defaults"
```

---

## Chunk 2: Repository & Pydantic Schemas

### Task 3: Pydantic schemas for Instrument CRUD

**Files:**
- Create: `backend/app/schemas/instrument.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_schemas/test_instrument_schema.py`:

```python
"""Unit tests for Instrument Pydantic schemas."""
import pytest
from pydantic import ValidationError
from app.schemas.instrument import InstrumentCreate, InstrumentUpdate, InstrumentResponse

def test_instrument_create_visa():
    data = InstrumentCreate(
        instrument_id="DAQ973A_1",
        instrument_type="DAQ973A",
        name="Keysight DAQ973A",
        conn_type="VISA",
        conn_params={"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000},
        enabled=True,
    )
    assert data.conn_type == "VISA"

def test_instrument_create_invalid_conn_type():
    with pytest.raises(ValidationError):
        InstrumentCreate(
            instrument_id="X",
            instrument_type="X",
            name="X",
            conn_type="INVALID_TYPE",   # must be one of allowed values
            conn_params={},
        )

def test_instrument_update_partial():
    upd = InstrumentUpdate(enabled=False)
    assert upd.enabled is False
    assert upd.name is None  # All fields optional in Update

def test_instrument_response_from_orm():
    """Simulate ORM object -> response schema conversion."""
    from datetime import datetime
    class FakeOrm:
        id = 1
        instrument_id = "DAQ973A_1"
        instrument_type = "DAQ973A"
        name = "Test"
        conn_type = "VISA"
        conn_params = {"address": "TCPIP0::..."}
        enabled = True
        description = None
        created_at = datetime.now()
        updated_at = datetime.now()

    resp = InstrumentResponse.model_validate(FakeOrm())
    assert resp.instrument_id == "DAQ973A_1"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_schemas/test_instrument_schema.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create schemas**

Create `backend/app/schemas/instrument.py`:

```python
"""
Pydantic schemas for Instrument CRUD API.
"""
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

# Allowed connection types (mirrors InstrumentAddress.type values)
ConnType = Literal["VISA", "SERIAL", "TCPIP_SOCKET", "GPIB", "LOCAL"]


class InstrumentBase(BaseModel):
    instrument_id: str = Field(..., max_length=64, description="Logical ID, e.g. DAQ973A_1")
    instrument_type: str = Field(..., max_length=64, description="Driver type, e.g. DAQ973A")
    name: str = Field(..., max_length=128)
    conn_type: ConnType
    conn_params: Dict[str, Any] = Field(..., description="Connection parameters JSON")
    enabled: bool = True
    description: Optional[str] = None


class InstrumentCreate(InstrumentBase):
    """Schema for POST /api/instruments"""
    pass


class InstrumentUpdate(BaseModel):
    """Schema for PATCH /api/instruments/{id} — all fields optional"""
    instrument_type: Optional[str] = Field(None, max_length=64)
    name: Optional[str] = Field(None, max_length=128)
    conn_type: Optional[ConnType] = None
    conn_params: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class InstrumentResponse(InstrumentBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_schemas/test_instrument_schema.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/schemas/instrument.py backend/tests/test_schemas/test_instrument_schema.py
git commit -m "feat: add Instrument Pydantic schemas for CRUD API"
```

---

### Task 4: Instrument repository (data access layer)

**Files:**
- Create: `backend/app/repositories/instrument_repository.py`
- Create: `backend/app/repositories/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_repositories/test_instrument_repository.py`:

```python
"""Integration tests for InstrumentRepository."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.base import Base
from app.models.instrument import Instrument
from app.repositories.instrument_repository import InstrumentRepository

@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng

@pytest.fixture
def db(engine):
    with Session(engine) as s:
        yield s
        s.rollback()

@pytest.fixture
def repo(db):
    return InstrumentRepository(db)

@pytest.fixture(autouse=True)
def seed(db):
    """Seed a known instrument before each test."""
    db.add(Instrument(
        instrument_id="test_inst_1",
        instrument_type="DAQ973A",
        name="Test Instrument",
        conn_type="VISA",
        conn_params={"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000},
        enabled=True,
    ))
    db.commit()
    yield
    db.query(Instrument).delete()
    db.commit()

def test_get_by_instrument_id(repo):
    inst = repo.get_by_instrument_id("test_inst_1")
    assert inst is not None
    assert inst.instrument_type == "DAQ973A"

def test_get_by_instrument_id_not_found(repo):
    assert repo.get_by_instrument_id("nonexistent") is None

def test_list_all(repo):
    result = repo.list_all()
    assert len(result) >= 1

def test_list_enabled(repo):
    result = repo.list_enabled()
    assert all(i.enabled for i in result)

def test_create(repo, db):
    from app.schemas.instrument import InstrumentCreate
    data = InstrumentCreate(
        instrument_id="new_inst",
        instrument_type="MODEL2303",
        name="New Instrument",
        conn_type="SERIAL",
        conn_params={"port": "COM3", "baudrate": 115200},
    )
    inst = repo.create(data)
    assert inst.id is not None
    assert inst.instrument_id == "new_inst"

def test_update(repo):
    inst = repo.get_by_instrument_id("test_inst_1")
    from app.schemas.instrument import InstrumentUpdate
    updated = repo.update(inst.id, InstrumentUpdate(enabled=False, name="Updated"))
    assert updated.enabled is False
    assert updated.name == "Updated"

def test_delete(repo, db):
    inst = repo.get_by_instrument_id("test_inst_1")
    result = repo.delete(inst.id)
    assert result is True
    assert repo.get_by_instrument_id("test_inst_1") is None

def test_delete_not_found(repo):
    assert repo.delete(99999) is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_repositories/test_instrument_repository.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create repository**

Create `backend/app/repositories/__init__.py` (empty file).

Create `backend/app/repositories/instrument_repository.py`:

```python
"""
Instrument Repository — data access layer for the instruments table.
Provides CRUD operations. All callers pass a SQLAlchemy Session.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.instrument import Instrument
from app.schemas.instrument import InstrumentCreate, InstrumentUpdate


class InstrumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, instrument_pk: int) -> Optional[Instrument]:
        return self.db.get(Instrument, instrument_pk)

    def get_by_instrument_id(self, instrument_id: str) -> Optional[Instrument]:
        return (
            self.db.query(Instrument)
            .filter(Instrument.instrument_id == instrument_id)
            .first()
        )

    def list_all(self) -> List[Instrument]:
        return self.db.query(Instrument).order_by(Instrument.instrument_id).all()

    def list_enabled(self) -> List[Instrument]:
        return (
            self.db.query(Instrument)
            .filter(Instrument.enabled == True)
            .order_by(Instrument.instrument_id)
            .all()
        )

    def create(self, data: InstrumentCreate) -> Instrument:
        inst = Instrument(**data.model_dump())
        self.db.add(inst)
        self.db.commit()
        self.db.refresh(inst)
        return inst

    def update(self, instrument_pk: int, data: InstrumentUpdate) -> Optional[Instrument]:
        inst = self.get_by_id(instrument_pk)
        if inst is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(inst, field, value)
        self.db.commit()
        self.db.refresh(inst)
        return inst

    def delete(self, instrument_pk: int) -> bool:
        inst = self.get_by_id(instrument_pk)
        if inst is None:
            return False
        self.db.delete(inst)
        self.db.commit()
        return True
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_repositories/test_instrument_repository.py -v
```

Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/repositories/ backend/tests/test_repositories/test_instrument_repository.py
git commit -m "feat: add InstrumentRepository for DB-backed instrument CRUD"
```

---

## Chunk 3: DB-Backed Config Provider & Cache

### Task 5: DB-backed InstrumentConfig provider (replaces singleton)

The goal is to keep the **same public interface** that `InstrumentExecutor` and `InstrumentConnection` already call:
- `get_instrument(instrument_id: str) -> Optional[InstrumentConfig]`
- `list_enabled_instruments() -> Dict[str, InstrumentConfig]`

We add a thin cache (30 s TTL) so the DB is not hit on every measurement.

**Files:**
- Modify: `backend/app/core/instrument_config.py` (add `InstrumentConfigProvider` class and new `get_instrument_provider()` factory; keep old classes for backward compatibility)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_core/test_instrument_config_provider.py`:

```python
"""Tests for DB-backed InstrumentConfigProvider."""
import time
import pytest
from unittest.mock import MagicMock, patch
from app.core.instrument_config import InstrumentConfigProvider, InstrumentConfig, VISAAddress

def _make_db_row(instrument_id="DAQ973A_1", conn_type="VISA",
                 conn_params=None, enabled=True):
    """Build a mock ORM Instrument row."""
    row = MagicMock()
    row.instrument_id = instrument_id
    row.instrument_type = "DAQ973A"
    row.name = "Test Instrument"
    row.conn_type = conn_type
    row.conn_params = conn_params or {"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000}
    row.enabled = enabled
    row.description = "A test instrument"
    return row

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.list_all.return_value = [_make_db_row()]
    repo.list_enabled.return_value = [_make_db_row()]
    repo.get_by_instrument_id.return_value = _make_db_row()
    return repo

def test_get_instrument_returns_instrument_config(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=30)
    config = provider.get_instrument("DAQ973A_1")
    assert isinstance(config, InstrumentConfig)
    assert config.id == "DAQ973A_1"
    assert config.type == "DAQ973A"

def test_get_instrument_not_found(mock_repo):
    mock_repo.get_by_instrument_id.return_value = None
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=30)
    assert provider.get_instrument("nonexistent") is None

def test_list_enabled_instruments(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=30)
    enabled = provider.list_enabled_instruments()
    assert "DAQ973A_1" in enabled
    assert isinstance(enabled["DAQ973A_1"], InstrumentConfig)

def test_cache_prevents_repeated_db_calls(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=60)
    provider.list_enabled_instruments()
    provider.list_enabled_instruments()
    # Should only hit DB once despite two calls
    assert mock_repo.list_enabled.call_count == 1

def test_cache_expires_after_ttl(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=0.01)  # 10ms TTL
    provider.list_enabled_instruments()
    time.sleep(0.02)
    provider.list_enabled_instruments()
    assert mock_repo.list_enabled.call_count == 2

def test_invalidate_cache(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=60)
    provider.list_enabled_instruments()
    provider.invalidate_cache()
    provider.list_enabled_instruments()
    assert mock_repo.list_enabled.call_count == 2

def test_orm_row_to_instrument_config_visa(mock_repo):
    """Verify correct InstrumentAddress subtype is built."""
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=30)
    config = provider.get_instrument("DAQ973A_1")
    assert isinstance(config.connection, VISAAddress)
    assert "TCPIP0" in config.connection.address

def test_orm_row_to_instrument_config_serial():
    row = _make_db_row(
        instrument_id="MODEL2303_1",
        conn_type="SERIAL",
        conn_params={"port": "COM3", "baudrate": 115200, "stopbits": 1, "parity": "N", "bytesize": 8},
    )
    from app.core.instrument_config import InstrumentConfigProvider, SerialAddress
    repo = MagicMock()
    repo.get_by_instrument_id.return_value = row
    provider = InstrumentConfigProvider(repo=repo, cache_ttl=30)
    config = provider.get_instrument("MODEL2303_1")
    assert isinstance(config.connection, SerialAddress)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_core/test_instrument_config_provider.py -v
```

Expected: `ImportError` (InstrumentConfigProvider not yet defined)

- [ ] **Step 3: Add `InstrumentConfigProvider` to `instrument_config.py`**

Append **after** the existing `get_instrument_settings()` function in `backend/app/core/instrument_config.py`:

```python
# ============================================================================
# DB-Backed Instrument Config Provider
# Replaces InstrumentSettings singleton for production use.
# Keeps the same interface: get_instrument(), list_enabled_instruments()
# ============================================================================

import threading
import time as _time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.repositories.instrument_repository import InstrumentRepository


class InstrumentConfigProvider:
    """
    DB-backed instrument configuration provider with in-memory cache.

    Drop-in replacement for InstrumentSettings.  Consumers call:
        provider.get_instrument(instrument_id)
        provider.list_enabled_instruments()
        provider.list_instruments()
        provider.invalidate_cache()   # call after CRUD mutations

    cache_ttl: seconds until the full list is refreshed from DB (default 30).
    """

    def __init__(self, repo: "InstrumentRepository", cache_ttl: float = 30.0):
        self._repo = repo
        self._cache_ttl = cache_ttl
        self._cache: Optional[Dict[str, InstrumentConfig]] = None
        self._cache_time: float = 0.0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface (same as InstrumentSettings)
    # ------------------------------------------------------------------

    def get_instrument(self, instrument_id: str) -> Optional[InstrumentConfig]:
        """Lookup by logical ID.  Uses cache; falls back to direct DB query on miss."""
        cached = self._get_cache()
        if cached is not None and instrument_id in cached:
            return cached[instrument_id]
        # Direct DB lookup for a single instrument (avoids full-list refresh)
        row = self._repo.get_by_instrument_id(instrument_id)
        return self._row_to_config(row) if row else None

    def list_instruments(self) -> Dict[str, InstrumentConfig]:
        """Return all instruments (enabled + disabled)."""
        return self._build_all_map()

    def list_enabled_instruments(self) -> Dict[str, InstrumentConfig]:
        """Return only enabled instruments, using cache."""
        cache = self._get_cache()
        if cache is not None:
            return cache
        return self._refresh_cache()

    def invalidate_cache(self):
        """Force next call to re-fetch from DB.  Call after any CRUD mutation."""
        with self._lock:
            self._cache = None
            self._cache_time = 0.0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_cache(self) -> Optional[Dict[str, InstrumentConfig]]:
        with self._lock:
            if self._cache is not None and (_time.monotonic() - self._cache_time) < self._cache_ttl:
                return self._cache
        return None

    def _refresh_cache(self) -> Dict[str, InstrumentConfig]:
        rows = self._repo.list_enabled()
        result = {row.instrument_id: self._row_to_config(row) for row in rows}
        with self._lock:
            self._cache = result
            self._cache_time = _time.monotonic()
        return result

    def _build_all_map(self) -> Dict[str, InstrumentConfig]:
        rows = self._repo.list_all()
        return {row.instrument_id: self._row_to_config(row) for row in rows}

    @staticmethod
    def _row_to_config(row) -> InstrumentConfig:
        """Convert an ORM Instrument row to the existing InstrumentConfig Pydantic model."""
        params = row.conn_params or {}
        conn_type = row.conn_type

        if conn_type == "SERIAL":
            connection = SerialAddress(
                port=params.get("port", "COM1"),
                baudrate=params.get("baudrate", 115200),
                stopbits=params.get("stopbits", 1),
                parity=params.get("parity", "N"),
                bytesize=params.get("bytesize", 8),
                timeout=params.get("timeout", 5000),
            )
        elif conn_type == "TCPIP_SOCKET":
            connection = TCPIPSocketAddress(
                host=params.get("host", "localhost"),
                port=params.get("port", 2268),
                timeout=params.get("timeout", 5000),
            )
        elif conn_type == "GPIB":
            connection = GPIBAddress(
                board=params.get("board", 0),
                address=params.get("address", 0),
                timeout=params.get("timeout", 5000),
            )
        else:
            # VISA or LOCAL — address field required
            connection = InstrumentAddress(
                type=conn_type,
                address=params.get("address", ""),
                timeout=params.get("timeout", 5000),
            ) if conn_type == "LOCAL" else VISAAddress(
                address=params.get("address", ""),
                timeout=params.get("timeout", 5000),
            )

        return InstrumentConfig(
            id=row.instrument_id,
            type=row.instrument_type,
            name=row.name,
            connection=connection,
            enabled=row.enabled,
            description=row.description,
        )


# ============================================================================
# Factory: get_instrument_provider(db_session)
# Use this in FastAPI endpoints and services instead of get_instrument_settings()
# ============================================================================

def get_instrument_provider(db) -> "InstrumentConfigProvider":
    """
    Create an InstrumentConfigProvider backed by the given DB session.
    Intended to be called from FastAPI dependency injection.

    Usage in endpoint:
        from app.core.database import get_db
        from app.core.instrument_config import get_instrument_provider
        from app.repositories.instrument_repository import InstrumentRepository

        @router.get("/{id}")
        def get_instrument(instrument_id: str, db: Session = Depends(get_db)):
            repo = InstrumentRepository(db)
            provider = get_instrument_provider(db)   # short-lived, per-request
            return provider.get_instrument(instrument_id)

    For long-lived services (InstrumentExecutor), use a module-level provider
    that is refreshed with invalidate_cache() after mutations.
    """
    from app.repositories.instrument_repository import InstrumentRepository
    repo = InstrumentRepository(db)
    return InstrumentConfigProvider(repo=repo, cache_ttl=30.0)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_core/test_instrument_config_provider.py -v
```

Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/core/instrument_config.py backend/tests/test_core/test_instrument_config_provider.py
git commit -m "feat: add DB-backed InstrumentConfigProvider with TTL cache"
```

---

## Chunk 4: REST API

### Task 6: `/api/instruments` CRUD router

**Files:**
- Create: `backend/app/api/instruments.py`
- Modify: `backend/app/main.py` (register router)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_api/test_instruments_api.py`:

```python
"""API integration tests for /api/instruments endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.models.base import Base

@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return eng

@pytest.fixture
def db(engine):
    with Session(engine) as s:
        yield s

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# --- Auth header helper -------------------------------------------------
AUTH = {"Authorization": "Bearer test-token"}  # mocked below

@pytest.fixture(autouse=True)
def mock_auth(monkeypatch):
    """Bypass JWT validation for API tests."""
    from app import dependencies
    monkeypatch.setattr(
        dependencies, "get_current_active_user",
        lambda *a, **kw: type("U", (), {"role": "admin", "id": 1, "is_active": True})()
    )

# --- Tests --------------------------------------------------------------

def test_list_instruments_empty(client):
    resp = client.get("/api/instruments", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == []

def test_create_instrument(client):
    payload = {
        "instrument_id": "DAQ973A_1",
        "instrument_type": "DAQ973A",
        "name": "Keysight DAQ973A",
        "conn_type": "VISA",
        "conn_params": {"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000},
        "enabled": True,
    }
    resp = client.post("/api/instruments", json=payload, headers=AUTH)
    assert resp.status_code == 201
    body = resp.json()
    assert body["instrument_id"] == "DAQ973A_1"
    assert "id" in body

def test_create_instrument_duplicate(client):
    # second POST with same instrument_id should fail
    payload = {
        "instrument_id": "DAQ973A_1",
        "instrument_type": "DAQ973A",
        "name": "Duplicate",
        "conn_type": "VISA",
        "conn_params": {},
        "enabled": True,
    }
    resp = client.post("/api/instruments", json=payload, headers=AUTH)
    assert resp.status_code == 409

def test_get_instrument(client):
    resp = client.get("/api/instruments/DAQ973A_1", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["instrument_type"] == "DAQ973A"

def test_get_instrument_not_found(client):
    resp = client.get("/api/instruments/NONEXISTENT", headers=AUTH)
    assert resp.status_code == 404

def test_update_instrument(client):
    resp = client.patch("/api/instruments/DAQ973A_1",
                        json={"enabled": False, "name": "Updated Name"},
                        headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False

def test_delete_instrument(client):
    resp = client.delete("/api/instruments/DAQ973A_1", headers=AUTH)
    assert resp.status_code == 204

def test_delete_instrument_not_found(client):
    resp = client.delete("/api/instruments/DAQ973A_1", headers=AUTH)
    assert resp.status_code == 404

def test_list_enabled_instruments(client):
    # Create two: one enabled, one disabled
    for inst_id, enabled in [("inst_a", True), ("inst_b", False)]:
        client.post("/api/instruments", json={
            "instrument_id": inst_id, "instrument_type": "TEST",
            "name": inst_id, "conn_type": "LOCAL",
            "conn_params": {"address": "local://test"}, "enabled": enabled,
        }, headers=AUTH)
    resp = client.get("/api/instruments?enabled_only=true", headers=AUTH)
    assert resp.status_code == 200
    ids = [i["instrument_id"] for i in resp.json()]
    assert "inst_a" in ids
    assert "inst_b" not in ids
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_api/test_instruments_api.py -v
```

Expected: 404 from TestClient (router not registered)

- [ ] **Step 3: Create router**

Create `backend/app/api/instruments.py`:

```python
"""
REST API for instrument configuration management.
Provides CRUD endpoints for the instruments table.
Replaces the read-only InstrumentSettings singleton with full runtime editability.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.instrument_config import InstrumentConfigProvider
from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.instrument import InstrumentCreate, InstrumentResponse, InstrumentUpdate

router = APIRouter()


def _repo(db: Session = Depends(get_db)) -> InstrumentRepository:
    return InstrumentRepository(db)


@router.get("", response_model=List[InstrumentResponse])
def list_instruments(
    enabled_only: bool = Query(False, description="Return only enabled instruments"),
    repo: InstrumentRepository = Depends(_repo),
):
    """List all instruments (or only enabled ones)."""
    rows = repo.list_enabled() if enabled_only else repo.list_all()
    return rows


@router.post("", response_model=InstrumentResponse, status_code=status.HTTP_201_CREATED)
def create_instrument(
    data: InstrumentCreate,
    repo: InstrumentRepository = Depends(_repo),
):
    """Create a new instrument configuration."""
    existing = repo.get_by_instrument_id(data.instrument_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Instrument '{data.instrument_id}' already exists.",
        )
    try:
        return repo.create(data)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Instrument ID conflict.",
        )


@router.get("/{instrument_id}", response_model=InstrumentResponse)
def get_instrument(instrument_id: str, repo: InstrumentRepository = Depends(_repo)):
    """Get instrument by logical ID (e.g. 'DAQ973A_1')."""
    inst = repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Instrument '{instrument_id}' not found.")
    return inst


@router.patch("/{instrument_id}", response_model=InstrumentResponse)
def update_instrument(
    instrument_id: str,
    data: InstrumentUpdate,
    repo: InstrumentRepository = Depends(_repo),
):
    """Partially update an instrument configuration."""
    inst = repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Instrument '{instrument_id}' not found.")
    updated = repo.update(inst.id, data)
    return updated


@router.delete("/{instrument_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instrument(instrument_id: str, repo: InstrumentRepository = Depends(_repo)):
    """Delete an instrument configuration."""
    inst = repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Instrument '{instrument_id}' not found.")
    repo.delete(inst.id)
```

- [ ] **Step 4: Register router in `main.py`**

In `backend/app/main.py`, add after existing router imports:

```python
from app.api import instruments as instruments_api
```

And in the router registration section:

```python
app.include_router(instruments_api.router, prefix="/api/instruments", tags=["Instruments"])
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_api/test_instruments_api.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/api/instruments.py backend/app/main.py backend/tests/test_api/test_instruments_api.py
git commit -m "feat: add /api/instruments CRUD REST API"
```

---

## Chunk 5: Wire Up Consumers & Integration

### Task 7: Update `InstrumentExecutor` to use DB provider

**Files:**
- Modify: `backend/app/services/instrument_executor.py`

The key change: instead of calling `get_instrument_settings()` (file-based singleton), `InstrumentExecutor` now accepts an `InstrumentConfigProvider` (injected).  For backwards compatibility the constructor falls back to the file-based settings if no provider is given.

- [ ] **Step 1: Read current `instrument_executor.py`**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
cat -n app/services/instrument_executor.py
```

Identify the lines that call `get_instrument_settings()` and `self.instrument_settings.get_instrument(...)`.

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_services/test_instrument_executor_db.py`:

```python
"""Test InstrumentExecutor uses DB-backed provider when injected."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.core.instrument_config import InstrumentConfig, VISAAddress, InstrumentConfigProvider
from app.services.instrument_executor import InstrumentExecutor

def _make_visa_config(inst_id="DAQ973A_1"):
    return InstrumentConfig(
        id=inst_id,
        type="DAQ973A",
        name="Test",
        connection=VISAAddress(address="TCPIP0::192.168.1.10::inst0::INSTR"),
        enabled=True,
    )

@pytest.fixture
def mock_provider():
    provider = MagicMock(spec=InstrumentConfigProvider)
    provider.get_instrument.return_value = _make_visa_config()
    return provider

@pytest.mark.asyncio
async def test_executor_uses_injected_provider(mock_provider):
    """Executor should call provider.get_instrument, not get_instrument_settings."""
    executor = InstrumentExecutor(config_provider=mock_provider)
    # Simulate a lookup (we don't actually connect hardware in this test)
    config = executor.get_instrument_config("DAQ973A_1")
    mock_provider.get_instrument.assert_called_once_with("DAQ973A_1")
    assert config is not None

@pytest.mark.asyncio
async def test_executor_falls_back_to_legacy_when_no_provider():
    """Without injection, executor falls back to get_instrument_settings()."""
    with patch("app.services.instrument_executor.get_instrument_settings") as mock_settings:
        mock_settings.return_value.get_instrument.return_value = _make_visa_config()
        executor = InstrumentExecutor()  # no provider injected
        config = executor.get_instrument_config("DAQ973A_1")
        assert config is not None
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_services/test_instrument_executor_db.py -v
```

Expected: `TypeError` (unexpected keyword argument `config_provider`)

- [ ] **Step 4: Modify `InstrumentExecutor`**

In `backend/app/services/instrument_executor.py`, comment out the old `__init__` body and add:

```python
# MODIFIED: Accept optional DB-backed InstrumentConfigProvider
# Old code used get_instrument_settings() singleton directly.
# New code accepts an injected provider; falls back to legacy singleton if not given.
def __init__(self, config_provider=None):
    if config_provider is not None:
        self._config_provider = config_provider
    else:
        # Legacy fallback: use file/env-based singleton
        from app.core.instrument_config import get_instrument_settings
        self._config_provider = get_instrument_settings()
    # Keep existing pool setup:
    self.connection_pool = get_connection_pool()

def get_instrument_config(self, instrument_id: str):
    """Retrieve InstrumentConfig from the injected provider."""
    return self._config_provider.get_instrument(instrument_id)
```

Also replace existing calls like `self.instrument_settings.get_instrument(...)` with `self._config_provider.get_instrument(...)`.

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_services/test_instrument_executor_db.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/services/instrument_executor.py backend/tests/test_services/test_instrument_executor_db.py
git commit -m "refactor: InstrumentExecutor accepts DB-backed provider with legacy fallback"
```

---

### Task 8: Full test suite regression check

- [ ] **Step 1: Run all tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -x -q
```

Expected: All existing tests still PASS.  Fix any failures before committing.

- [ ] **Step 2: Run with coverage**

```bash
uv run pytest --cov=app tests/ -q
```

- [ ] **Step 3: Commit if all green**

```bash
git add -A
git commit -m "test: verify full test suite after instrument DB migration"
```

---

### Task 9: Docker Compose integration (apply schema migration)

**Files:**
- Modify: `docker-compose.yml` (ensure seed_instruments.sql is executed on init)

- [ ] **Step 1: Check current DB init in docker-compose.yml**

Look for the MySQL service `volumes` — typically there is a `./database:/docker-entrypoint-initdb.d` mount or similar.

- [ ] **Step 2: Add seed file to init**

If using `docker-entrypoint-initdb.d`, copy `seed_instruments.sql` into the database init directory or ensure it's mounted. If the project uses manual init scripts, document the command:

```bash
# First-time setup (after schema.sql):
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  < database/seed_instruments.sql
```

- [ ] **Step 3: Update CLAUDE.md Database Setup section**

In project CLAUDE.md, add:
```markdown
# Database initialization (first time only)
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/schema.sql
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_data.sql
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_instruments.sql  # NEW
```

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add CLAUDE.md docker-compose.yml
git commit -m "docs: add seed_instruments.sql to DB init instructions"
```

---

## Summary

| Chunk | Deliverables | Tests |
|-------|-------------|-------|
| 1 | `instruments` table DDL + ORM model + seed SQL | 4 model tests |
| 2 | Pydantic schemas + Repository | 4 schema tests + 8 repo tests |
| 3 | `InstrumentConfigProvider` with TTL cache | 8 provider tests |
| 4 | `/api/instruments` CRUD REST API | 9 API tests |
| 5 | Wire up consumers, regression, Docker docs | Service + full suite |

**Total new tests:** ~33 across 5 test files.

**Consumer impact:** `InstrumentExecutor` and `InstrumentConnection` continue to call the same `.get_instrument(id)` interface — no changes needed in measurement implementations or test plans.
