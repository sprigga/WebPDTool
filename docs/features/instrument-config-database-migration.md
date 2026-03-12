# Instrument Config Database Migration

> **Feature Status:** ✅ Completed (2026-03-11) | Alembic Migration Fixed (2026-03-12)
>
> **Implementation Plan:** [docs/superpowers/plans/2026-03-11-instrument-config-database.md](../superpowers/plans/2026-03-11-instrument-config-database.md)
>
> **Latest Fix:** Issue 11.1 - 建立正確的 Alembic migration 取代 raw SQL 方式

## Overview

將儀器配置從檔案/環境變數基礎的儲存方式（`instrument_config.py`）遷移到 MySQL 資料庫表，提供完整的 CRUD REST API，讓操作員可以在執行時期管理儀器而無需重新啟動伺服器。

### 遷移前的問題

**原有架構 (`InstrumentSettings`):**
```python
# 配置來源優先順序
1. INSTRUMENTS_CONFIG_JSON 環境變數（JSON 字串）
2. INSTRUMENTS_CONFIG_FILE 環境變數（JSON 檔案路徑）
3. 硬編碼的預設配置（模擬模式）
```

**問題：**
- ❌ 無法在執行時期新增/修改儀器配置
- ❌ 需要重新啟動伺服器才能更新配置
- ❌ 沒有變更歷史記錄
- ❌ 多實例部署時配置同步困難

### 遷移後的架構

```
MySQL `instruments` 表
    ↓
InstrumentRepository (CRUD 層)
    ↓
InstrumentConfigProvider (TTL 快取層)
    ↓
InstrumentExecutor (消費者)
```

**優勢：**
- ✅ 完整的 CRUD REST API (`/api/instruments`)
- ✅ 執行時期可編輯，無需重啟
- ✅ TTL 快取（30 秒）減少 DB 查詢
- ✅ 向後相容，現有程式碼零修改

---

## 實作內容

### 1. 資料庫層 (Chunk 1)

#### 新增 `instruments` 表

**檔案:** `database/schema.sql`

```sql
CREATE TABLE IF NOT EXISTS instruments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    instrument_id   VARCHAR(64) NOT NULL UNIQUE COMMENT 'Logical ID, e.g. DAQ973A_1',
    instrument_type VARCHAR(64) NOT NULL COMMENT 'Driver type, e.g. DAQ973A',
    name            VARCHAR(128) NOT NULL,
    conn_type       VARCHAR(32) NOT NULL COMMENT 'VISA | SERIAL | TCPIP_SOCKET | GPIB | LOCAL',
    conn_params     JSON NOT NULL COMMENT 'Connection parameters',
    enabled         TINYINT(1) NOT NULL DEFAULT 1,
    description     TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_instruments_type (instrument_type),
    INDEX idx_instruments_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### ORM 模型

**檔案:** `backend/app/models/instrument.py`

```python
from sqlalchemy import TIMESTAMP, Boolean, Integer, String, Text, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    conn_type: Mapped[str] = mapped_column(String(32), nullable=False)
    conn_params: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
```

#### 預設資料

**檔案:** `database/seed_instruments.sql`

包含 5 個預設儀器：
- `DAQ973A_1` - Keysight DAQ973A（VISA）
- `MODEL2303_1` - Keysight 2303 電源（VISA）
- `console_1` - Console 命令（LOCAL）
- `comport_1` - COM 埠命令（LOCAL）
- `tcpip_1` - TCP/IP 命令（LOCAL）

---

### 2. Schema 與 Repository 層 (Chunk 2)

#### Pydantic Schemas

**檔案:** `backend/app/schemas/instrument.py`

```python
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

ConnType = Literal["VISA", "SERIAL", "TCPIP_SOCKET", "GPIB", "LOCAL"]

class InstrumentBase(BaseModel):
    instrument_id: str = Field(..., max_length=64)
    instrument_type: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    conn_type: ConnType
    conn_params: Dict[str, Any] = Field(..., description="Connection parameters JSON")
    enabled: bool = True
    description: Optional[str] = None

class InstrumentCreate(InstrumentBase):
    """POST /api/instruments"""
    pass

class InstrumentUpdate(BaseModel):
    """PATCH /api/instruments/{id} — all fields optional"""
    # instrument_id intentionally excluded — stable logical key
    instrument_type: Optional[str] = Field(None, max_length=64)
    name: Optional[str] = Field(None, max_length=128)
    conn_type: Optional[ConnType] = None
    conn_params: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None

class InstrumentResponse(InstrumentBase):
    """API response schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

#### Repository 層

**檔案:** `backend/app/repositories/instrument_repository.py`

```python
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
        return self.db.query(Instrument).filter(
            Instrument.instrument_id == instrument_id
        ).first()

    def list_all(self) -> List[Instrument]:
        return self.db.query(Instrument).order_by(Instrument.instrument_id).all()

    def list_enabled(self) -> List[Instrument]:
        return self.db.query(Instrument).filter(
            Instrument.enabled.is_(True)  # 使用 is_(True) 而非 == True
        ).order_by(Instrument.instrument_id).all()

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

---

### 3. Config Provider 層 (Chunk 3)

**檔案:** `backend/app/core/instrument_config.py` (append)

`InstrumentConfigProvider` 是核心組件，提供 DB 支援的配置存取，具有 TTL 快取機制。

```python
import threading
import time as _time
from typing import Dict, Optional

class InstrumentConfigProvider:
    """
    DB-backed instrument configuration provider with in-memory cache.

    Drop-in replacement for InstrumentSettings.
    cache_ttl: seconds until the full list is refreshed from DB (default 30).
    """

    def __init__(self, repo, cache_ttl: float = 30.0):
        self._repo = repo
        self._cache_ttl = cache_ttl
        self._cache: Optional[Dict[str, InstrumentConfig]] = None
        self._cache_time: float = 0.0
        self._lock = threading.Lock()

    def get_instrument(self, instrument_id: str) -> Optional[InstrumentConfig]:
        """Lookup by logical ID. Uses cache; falls back to direct DB query on miss."""
        cached = self._get_cache()
        if cached is not None and instrument_id in cached:
            return cached[instrument_id]
        # Direct DB lookup for a single instrument (avoids full-list refresh)
        row = self._repo.get_by_instrument_id(instrument_id)
        return self._row_to_config(row) if row else None

    def list_enabled_instruments(self) -> Dict[str, InstrumentConfig]:
        """Return only enabled instruments, using cache."""
        cache = self._get_cache()
        if cache is not None:
            return cache
        return self._refresh_cache()

    def invalidate_cache(self):
        """Force next call to re-fetch from DB. Call after any CRUD mutation."""
        with self._lock:
            self._cache = None
            self._cache_time = 0.0

    # ------------------------------------------------------------------
    # Thread-safe cache with double-checked locking
    # ------------------------------------------------------------------

    def _get_cache(self) -> Optional[Dict[str, InstrumentConfig]]:
        with self._lock:
            if (self._cache is not None and
                    (_time.monotonic() - self._cache_time) < self._cache_ttl):
                return dict(self._cache)  # return copy while holding lock
        return None

    def _refresh_cache(self) -> Dict[str, InstrumentConfig]:
        with self._lock:
            # Double-check: another thread may have refreshed while we waited
            if (self._cache is not None and
                    (_time.monotonic() - self._cache_time) < self._cache_ttl):
                return dict(self._cache)
            # Fetch from DB (holding lock — acceptable for this use case)
            rows = self._repo.list_enabled()
            result = {row.instrument_id: self._row_to_config(row) for row in rows}
            self._cache = result
            self._cache_time = _time.monotonic()
            return dict(result)

    @staticmethod
    def _row_to_config(row) -> InstrumentConfig:
        """Convert ORM row to existing InstrumentConfig Pydantic model."""
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
        elif conn_type == "LOCAL":
            connection = InstrumentAddress(
                type="LOCAL",
                address=params.get("address", "local://unknown"),
                timeout=params.get("timeout", 5000),
            )
        else:  # VISA
            connection = VISAAddress(
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
```

---

### 4. REST API 層 (Chunk 4)

**檔案:** `backend/app/api/instruments.py`

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.instrument import InstrumentCreate, InstrumentResponse, InstrumentUpdate

router = APIRouter()


def _get_repo(db: Session = Depends(get_db)) -> InstrumentRepository:
    return InstrumentRepository(db)


@router.get("", response_model=List[InstrumentResponse])
def list_instruments(
    enabled_only: bool = Query(False, description="Return only enabled instruments"),
    repo: InstrumentRepository = Depends(_get_repo),
):
    rows = repo.list_enabled() if enabled_only else repo.list_all()
    return rows


@router.post("", response_model=InstrumentResponse, status_code=status.HTTP_201_CREATED)
def create_instrument(
    data: InstrumentCreate,
    repo: InstrumentRepository = Depends(_get_repo),
):
    existing = repo.get_by_instrument_id(data.instrument_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Instrument '{data.instrument_id}' already exists.",
        )
    return repo.create(data)


@router.get("/{instrument_id}", response_model=InstrumentResponse)
def get_instrument(instrument_id: str, repo: InstrumentRepository = Depends(_get_repo)):
    inst = repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument '{instrument_id}' not found.",
        )
    return inst


@router.patch("/{instrument_id}", response_model=InstrumentResponse)
def update_instrument(
    instrument_id: str,
    data: InstrumentUpdate,
    repo: InstrumentRepository = Depends(_get_repo),
):
    inst = repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument '{instrument_id}' not found.",
        )
    return repo.update(inst.id, data)


@router.delete("/{instrument_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instrument(
    instrument_id: str,
    repo: InstrumentRepository = Depends(_get_repo),
):
    inst = repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument '{instrument_id}' not found.",
        )
    repo.delete(inst.id)
```

**Router 註冊:** `backend/app/main.py`
```python
from app.api import instruments as instruments_api

app.include_router(instruments_api.router, prefix="/api/instruments", tags=["Instruments"])
```

---

### 5. 消費者整合 (Chunk 5)

**檔案:** `backend/app/services/instrument_executor.py`

```python
# MODIFIED: Accept optional DB-backed InstrumentConfigProvider
def __init__(self, config_provider=None):
    if config_provider is not None:
        self._config_provider = config_provider
    else:
        # Legacy fallback: use file/env-based singleton
        from app.core.instrument_config import get_instrument_settings
        self._config_provider = get_instrument_settings()
    # Keep existing pool setup:
    self.connection_pool = get_connection_pool()
    # For backward compatibility, also store as instrument_settings
    self.instrument_settings = self._config_provider
    self.logger = logging.getLogger(self.__class__.__name__)

def get_instrument_config(self, instrument_id: str):
    """Retrieve InstrumentConfig from the injected provider."""
    return self._config_provider.get_instrument(instrument_id)
```

---

## 除錯與修正過程

### Issue 1: ORM 模型欄位類型不匹配

**問題:**
原始規格使用 `DateTime`，但現有模型使用 `TIMESTAMP`。

**修正:**
```python
# 原本（錯誤）
from sqlalchemy import DateTime
created_at: Mapped[datetime] = mapped_column(DateTime, ...)

# 修正後（與 user.py 一致）
from sqlalchemy import TIMESTAMP
created_at: Mapped[datetime] = mapped_column(TIMESTAMP, ...)
```

**Commit:** `04aeba6` - "fix: improve test isolation and use TIMESTAMP for instrument model"

---

### Issue 2: 測試隔離失敗

**問題:**
`engine` fixture 使用 `scope="module"`，導致測試間狀態洩漏。

**修正:**
```python
# 原本（錯誤）
@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng

# 修正後
@pytest.fixture(scope="function")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
```

---

### Issue 3: Repository 布林值比較

**問題:**
使用 `== True` 比較布林欄位，不符合 SQLAlchemy 慣用語法。

**修正:**
```python
# 原本（警告）
.filter(Instrument.enabled == True)

# 修正後（慣用語法）
.filter(Instrument.enabled.is_(True))
```

**Commit:** `1492221`

---

### Issue 4: InstrumentConfigProvider 執行緒安全性 TOCTOU 競爭

**問題:**
原始實作存在 check-then-act 競爭條件：
```python
# 錯誤：釋放鎖後才檢查 TTL，兩個執行緒可能同時刷新
def _get_cache(self):
    with self._lock:
        if ...:
            return self._cache
    return None  # 鎖已釋放

def _refresh_cache(self):
    rows = self._repo.list_enabled()  # 無鎖保護！
    with self._lock:
        self._cache = ...
```

**修正 - Double-Checked Locking:**
```python
def _refresh_cache(self) -> Dict[str, InstrumentConfig]:
    with self._lock:
        # Double-check: another thread may have refreshed while we waited
        if (self._cache is not None and
                (_time.monotonic() - self._cache_time) < self._cache_ttl):
            return dict(self._cache)
        # We hold the lock - fetch from DB
        rows = self._repo.list_enabled()
        result = {row.instrument_id: self._row_to_config(row) for row in rows}
        self._cache = result
        self._cache_time = _time.monotonic()
        return dict(result)
```

**Commit:** `24f0b31` - "fix: thread-safe cache and full conn_type test coverage"

---

### Issue 5: API 測試的 SQLite 執行緒衝突

**問題:**
FastAPI `TestClient` 在背景執行緒執行請求，使用 `:memory:` SQLite 會導致連線衝突。

**修正:**
使用暫存檔案代替記憶體資料庫：
```python
@pytest.fixture(scope="function")
def db_session():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    test_engine = create_engine(
        f"sqlite:///{db_path}",  # 檔案路徑，不是 :memory:
        connect_args={"check_same_thread": False},
    )
    # ... setup ...
    finally:
        os.unlink(db_path)  # 清理暫存檔
```

---

### Issue 6: 測試環境缺少 `paramiko` 模組

**問題:**
`instrument_executor.py` 匯入 `l6mpu_ssh.py`，該模組需要 `paramiko`，但測試環境未安裝。

**修正:**
在測試檔案中 mock `paramiko`：
```python
import sys
from unittest.mock import MagicMock

sys.modules["paramiko"] = MagicMock()
```

---

### Issue 7: `uv run` 與 `.venv` 權限問題

**問題:**
執行環境的 `.venv` 是損壞的符號連結，`uv run` 無法移除它。

**Workaround:**
直接使用 `python3 -m pytest` 代替 `uv run pytest`：
```bash
python3 -m pytest tests/... -v
```

---

### Issue 9: `docker-compose exec` 無法使用 stdin 重定向

**問題:**
執行資料庫 migration 時，使用 `<` 重定向 SQL 檔案到 `docker-compose exec` 會失敗：

```bash
$ docker-compose exec db mysql -uroot -prootpassword webpdtool < database/migrations/add_instruments_table.sql
the input device is not a TTY
```

**原因:**
`docker-compose exec` 預設會分配 TTY（虛擬終端），而 `<` 重定向需要 stdin 是非 TTY 模式。兩者衝突導致錯誤。

**修正:**
加上 `-T` 旗標停用 TTY 分配，讓 stdin 重定向正常運作：

```bash
docker-compose exec -T db mysql -uroot -prootpassword webpdtool < database/migrations/add_instruments_table.sql
```

執行成功後只會出現以下警告（正常，不影響結果）：
```
mysql: [Warning] Using a password on the command line interface can be insecure.
```

**驗證是否成功:**
```bash
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "SELECT instrument_id, conn_type, enabled FROM instruments;"
```

---

### Issue 10: `docker-compose.yml` 未掛載 `seed_instruments.sql`

**問題:**
`docker-compose.yml` 的 MySQL 服務只掛載了 `schema.sql` 和 `seed_data.sql` 到 `docker-entrypoint-initdb.d`，未包含 `seed_instruments.sql`。
導致新部署時 `instruments` 表雖然會被建立（schema 已含），但不會有預設儀器資料。

```yaml
# 原本（缺少 seed_instruments.sql）
volumes:
  - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
  - ./database/seed_data.sql:/docker-entrypoint-initdb.d/02-seed_data.sql:ro
```

**修正:**
新增第三個掛載項，使用 `03-` 前綴確保執行順序在 schema 之後：

```yaml
# 修正後
volumes:
  - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
  - ./database/seed_data.sql:/docker-entrypoint-initdb.d/02-seed_data.sql:ro
  - ./database/seed_instruments.sql:/docker-entrypoint-initdb.d/03-seed_instruments.sql:ro
```

**注意:** `docker-entrypoint-initdb.d` 腳本只在資料 volume 第一次初始化時執行（volume 為空時）。已存在的部署需手動執行 migration。

---

### Issue 11: 已存在部署缺少 migration 腳本 ✅ RESOLVED

> **Status:** Fixed (2026-03-12) - Proper Alembic migration created

**原本的問題:**
`instruments` 表只有原始 SQL migration (`database/migrations/add_instruments_table.sql`)，沒有對應的 Alembic 版本控制。

**修正:**
建立了正確的 Alembic migration，讓 schema 變更納入版本控制系統：

**檔案:** `backend/alembic/versions/20260312_add_instruments_table.py`

特點：
- 使用 `op.execute()` 執行 MySQL 專用 DDL（JSON 類型、TINYINT(1)）
- 包含 `CREATE TABLE IF NOT EXISTS` 確保冪等性
- 包含 5 個預設儀器的 seed data，使用 `ON DUPLICATE KEY UPDATE`
- 提供完整的 `downgrade()` 函式支援回滾
- 更新了 `backend/alembic/env.py` 加入 `Instrument` model 匯入

**既有部署執行方式:**
```bash
cd /path/to/WebPDTool/backend

# 方式 1: 使用 Alembic（推薦，有版本控制）
uv run alembic upgrade head

# 或使用 python 模組
python3 -m alembic upgrade head

# 方式 2: 直接指定 migration
uv run alembic upgrade 20260312_add_instruments_table

# 方式 3: 在 Docker 環境中
docker-compose exec backend uv run alembic upgrade head
```

**向後相容:**
既有的 raw SQL migration (`database/migrations/add_instruments_table.sql`) 仍然保留，作為備份參考。由於使用了 `IF NOT EXISTS` 和 `ON DUPLICATE KEY UPDATE`，即使部署已經執行過 raw SQL 版本，再執行 Alembic migration 也不會造成問題。

---

### Issue 11.1: Alembic Migration 建立過程與除錯 ✅ RESOLVED

> **Status:** Fixed (2026-03-12) - 完整的問題分析與解決過程記錄

#### 問題發現過程

使用者詢問：「在新增 instruments 資料表時，Alembic tool 沒有發揮任何作用嗎？」

這個問題引發了深入調查，發現了以下架構不一致的問題：

**初始狀態分析:**
```
專案狀態：
├── schema.sql 已包含 instruments 表 ✅
├── seed_instruments.sql 已建立 ✅
├── database/migrations/add_instruments_table.sql (raw SQL) ✅
└── backend/alembic/versions/ (沒有對應的 migration) ❌
```

#### 除錯步驟

**步驟 1: 確認 Alembic 設定狀態**

```bash
# 檢查 Alembic 是否已配置
ls -la backend/alembic/
ls -la backend/alembic/versions/

# 結果：專案已經有 Alembic！
# - alembic.ini ✅
# - alembic/env.py ✅
# - 4 個既有 migrations ✅
```

**步驟 2: 檢查 alembic/env.py 的 model 匯入**

```python
# backend/alembic/env.py (原始狀態)
from app.models.user import User
from app.models.project import Project
from app.models.station import Station
from app.models.testplan import TestPlan
from app.models.test_result import TestResult
from app.models.test_session import TestSession
from app.models.sfc_log import SFCLog
# ❌ Instrument 模型未匯入！
```

**根本原因發現:**
- `Instrument` 模型存在於 `backend/app/models/instrument.py`
- 但 `alembic/env.py` 沒有匯入它
- 導致 `alembic revision --autogenerate` 無法偵測到 `instruments` 表
- 開發者因此建立了 raw SQL migration 作為權宜之計

**步驟 3: 檢查既有 migrations 的 revision chain**

```bash
# 檢查所有 migrations 的依賴關係
grep -E "^(revision|down_revision)" backend/alembic/versions/*.py

# 發現的 migration 鏈:
# 0232af89acc2 (base) → 9dd55b733f64 → 20250109_change_measured_value → a8124fdea538 (latest)
```

#### 解決過程

**修正 1: 更新 alembic/env.py**

```python
# backend/alembic/env.py (修正後)
from app.models.instrument import Instrument  # 新增這行
```

**修正 2: 建立 Alembic migration 檔案**

創建 `backend/alembic/versions/20260312_add_instruments_table.py`:

```python
"""add_instruments_table

Revision ID: 20260312_add_instruments_table
Revises: a8124fdea538  # 連接到最新的 migration
Create Date: 2026-03-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260312_add_instruments_table'
down_revision: Union[str, Sequence[str], None] = 'a8124fdea538'

def upgrade() -> None:
    """使用 raw SQL 以支援 MySQL 特定功能"""
    op.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            instrument_id   VARCHAR(64) NOT NULL UNIQUE COMMENT 'Logical ID',
            instrument_type VARCHAR(64) NOT NULL COMMENT 'Driver type',
            name            VARCHAR(128) NOT NULL,
            conn_type       VARCHAR(32) NOT NULL COMMENT 'Connection type',
            conn_params     JSON NOT NULL COMMENT 'Connection parameters',
            enabled         TINYINT(1) NOT NULL DEFAULT 1,
            description     TEXT,
            created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_instruments_type (instrument_type),
            INDEX idx_instruments_enabled (enabled)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # Idempotent seed data
    op.execute("""
        INSERT INTO instruments (instrument_id, instrument_type, name, conn_type, conn_params, enabled, description)
        VALUES
          ('DAQ973A_1', 'DAQ973A', 'Keysight DAQ973A #1',
           'VISA', '{"address":"TCPIP0::192.168.1.10::inst0::INSTR","timeout":5000}',
           0, 'Keysight DAQ973A data acquisition system'),
          -- ... 其他 4 個預設儀器
        ON DUPLICATE KEY UPDATE
          name        = VALUES(name),
          conn_type   = VALUES(conn_type),
          conn_params = VALUES(conn_params),
          description = VALUES(description);
    """)

def downgrade() -> None:
    """回滾 migration"""
    op.execute("DROP TABLE IF EXISTS instruments;")
```

**設計決策說明:**

| 決策 | 原因 |
|------|------|
| 使用 `op.execute()` 而非 `op.create_table()` | MySQL 特定功能：JSON 類型、TINYINT(1)、ON DUPLICATE KEY UPDATE |
| `CREATE TABLE IF NOT EXISTS` | 幂等性：可重複執行，即使已存在 raw SQL 建立的表 |
| `ON DUPLICATE KEY UPDATE` | Seed data 幂等性：避免重複插入時失敗 |
| `down_revision = 'a8124fdea538'` | 連接到正確的 migration chain 頂端 |
| 提供 `downgrade()` 函式 | 支援完整的 rollback 能力 |

**修正 3: 驗證 migration chain**

```bash
# 驗證 revision 鏈是否正確連接
grep -E "^(revision|down_revision)" backend/alembic/versions/*.py | sort

# 正確的鏈應該是:
# 0232af89acc2 → 9dd55b733f64 → 20250109 → a8124fdea538 → 20260312_add_instruments_table ✅
```

#### 除錯過程中發現的問題

**問題 1: Revision chain 不一致**

```python
# 初始版本 (錯誤)
down_revision: Union[str, Sequence[str], None] = '9dd55b733f64'  # 太舊！

# 檢查所有 migrations 後發現
a8124fdea538_add_project_id_to_test_plans.py:
  down_revision = '20250109_change_measured_value'

# 修正後
down_revision: Union[str, Sequence[str], None] = 'a8124fdea538'  # 最新！
```

**問題 2: 為何不用 autogenerate？**

```bash
# 嘗試 autogenerate 會失敗，因為:
# 1. Instrument 模型未在 env.py 匯入 (已修正)
# 2. MySQL 的 JSON 類型在 autogenerate 中可能產生不兼容的 SQL
# 3. Seed data 無法通過 autogenerate 自動產生
```

#### 執行與驗證

```bash
# 查看當前 migration 版本
uv run alembic current

# 執行 upgrade
uv run alembic upgrade head

# 驗證表已建立
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "DESCRIBE instruments;"

# 驗證 seed data
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "SELECT instrument_id, name, enabled FROM instruments;"

# 查看 migration 歷史
uv run alembic history

# 測試 rollback
uv run alembic downgrade -1
uv run alembic upgrade 20260312_add_instruments_table
```

#### 經驗總結

**學到的教訓:**

1. **Alembic env.py 必須匯入所有模型** - 否則 autogenerate 無法偵測
2. **MySQL 特定功能需要 raw SQL** - JSON、TINYINT(1) 等
3. **Idempotent migration 設計** - `IF NOT EXISTS` + `ON DUPLICATE KEY UPDATE`
4. **正確的 revision chain** - 必須連接到最新的 migration
5. **文件同步更新** - 解決問題後立即更新文件

**最佳實踐:**

```python
# 新增表時的標準流程:
# 1. 建立 ORM model (backend/app/models/instrument.py)
# 2. 更新 alembic/env.py 匯入新模型
# 3. 建立 migration (alembic revision -m "description")
# 4. 或使用 autogenerate (alembic revision --autogenerate -m "description")
# 5. 撰寫 upgrade/downgrade 邏輯
# 6. 測試 upgrade 和 downgrade
# 7. 更新文件
```

---

## Docker 自動化 Migration (Issue 11.2) ✅ NEW

> **Status:** Added (2026-03-12) - 容器啟動時自動執行 Alembic migrations

### 概述

為了簡化部署流程，Docker 容器現在會在啟動應用程式之前自動執行 Alembic migrations。這確保了資料庫 schema 始終與應用程式版本同步，無需手動執行 migration 指令。

### 實作架構

```
Docker Container Start
    ↓
docker-entrypoint.sh 執行
    ↓
等待資料庫就緒 (wait_for_db)
    ↓
執行 Alembic migrations (alembic upgrade head)
    ↓
啟動 FastAPI 應用程式
```

### 檔案變更

#### 1. 新增 `backend/docker-entrypoint.sh`

Entrypoint 腳本負責：
- 等待資料庫連線（可配置超時時間）
- 執行 `alembic upgrade head`
- Migration 失敗時仍允許應用程式啟動（優雅降級）
- 提供詳細的日誌輸出

#### 2. 更新 `backend/Dockerfile`

```dockerfile
# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Use entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9100"]
```

#### 3. 更新 `docker-compose.yml`

新增環境變數控制 migration 行為：

```yaml
environment:
  # 設為 "true" 跳過自動 migration
  SKIP_MIGRATIONS: ${SKIP_MIGRATIONS:-false}
  # 資料庫連線等待時間（秒）
  MIGRATION_TIMEOUT: ${MIGRATION_TIMEOUT:-60}
  # 傳遞給 alembic 的額外參數
  ALEMBIC_ARGS: ${ALEMBIC_ARGS:-}
```

### 使用方式

#### 正常啟動（自動執行 migrations）

```bash
docker-compose up -d backend

# 查看日誌確認 migrations 已執行
docker-compose logs backend | grep -i migration
```

預期輸出：
```
[INFO] Waiting for database at db:3306 to be ready...
[INFO] Database is ready!
[INFO] Starting Alembic database migrations...
[INFO] Running 'alembic upgrade head'...
[INFO] ✅ Migrations completed successfully!
[INFO] Starting FastAPI application...
```

#### 跳過 Migrations（開發/除錯用）

```bash
# 方式 1: 透過 .env 檔案
echo "SKIP_MIGRATIONS=true" >> .env
docker-compose up -d backend

# 方式 2: 透過命令列參數
docker-compose run -e SKIP_MIGRATIONS=true backend

# 方式 3: 直接執行命令（繞過 entrypoint）
docker-compose exec backend uv run uvicorn app.main:app
```

#### 手動執行 Migrations

```bash
# 進入容器執行
docker-compose exec backend uv run alembic upgrade head

# 查看當前版本
docker-compose exec backend uv run alembic current

# 查看歷史
docker-compose exec backend uv run alembic history

# 回滾一個版本
docker-compose exec backend uv run alembic downgrade -1
```

### 環境變數說明

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `SKIP_MIGRATIONS` | `false` | 設為 `true` 跳過自動 migration |
| `MIGRATION_TIMEOUT` | `60` | 等待資料庫的最大秒數 |
| `ALEMBIC_ARGS` | `""` | 傳遞給 `alembic upgrade` 的額外參數 |

### 故障排除

#### Migration 失敗但應用程式仍啟動

Entrypoint 設計為**優雅降級**：即使 migration 失敗，應用程式仍會嘗試啟動。這允許在 migration 問題修復後手動重試。

日誌範例：
```
[ERROR] ❌ Migration failed!
[ERROR] The application will still start, but database schema may be incomplete.
[ERROR] You can also run migrations manually later:
[ERROR]   docker-compose exec backend uv run alembic upgrade head
```

#### 資料庫連線超時

如果看到 `Database connection timeout` 錯誤：

1. 檢查資料庫容器是否健康：`docker-compose ps db`
2. 增加超時時間：`MIGRATION_TIMEOUT=120`（120 秒）
3. 手動檢查連線：`docker-compose exec backend python -c "import pymysql; pymysql.connect(host='db', user='pdtool', password='pdtool123', database='webpdtool')"`

#### 查看詳細 Migration 日誌

```bash
# 查看完整容器日誌
docker-compose logs backend

# 只看 migration 相關
docker-compose logs backend | grep -E "(Migration|alembic|Database)"

# 即時跟蹤日誌
docker-compose logs -f backend
```

### 最佳實踐

1. **生產環境**: 保留自動 migration（預設行為），確保部署時 schema 同步
2. **開發環境**: 可使用 `SKIP_MIGRATIONS=true` 加速啟動，手動控制 migration 時機
3. **CI/CD**: 建議保留自動 migration，但先在測試環境驗證
4. **Rollback**: 使用 `alembic downgrade -1` 回滾後，重啟容器不會重新執行已回滾的 migration

### 相關檔案

| 檔案 | 說明 |
|------|------|
| `backend/docker-entrypoint.sh` | **新增** - 容器啟動腳本 |
| `backend/Dockerfile` | **已修改** - 新增 ENTRYPOINT 指令 |
| `docker-compose.yml` | **已修改** - 新增 migration 環境變數 |

---

### Issue 8: Async 測試需要 `pytest-asyncio`

**問題:**
測試使用 `@pytest.mark.asyncio`，但環境未安裝 `pytest-asyncio`。

**修正:**
將非同步測試改為同步測試（因為測試的是建構函式行為，非非同步方法）：
```python
# 原本（需要 pytest-asyncio）
@pytest.mark.asyncio
async def test_executor_uses_injected_provider(mock_provider):
    ...

# 修正後（同步測試）
def test_executor_uses_injected_provider(mock_provider):
    ...
```

---

## 測試覆蓋

| 測試檔案 | 測試數量 | 覆蓋內容 |
|---------|---------|---------|
| `test_instrument_model.py` | 4 | ORM 模型驗證 |
| `test_instrument_schema.py` | 4 | Pydantic 驗證 |
| `test_instrument_repository.py` | 8 | Repository CRUD |
| `test_instrument_config_provider.py` | 11 | TTL 快取、conn_type 轉換 |
| `test_instruments_api.py` | 9 | REST API 端點 |
| `test_instrument_executor_db.py` | 2 | 依賴注入 |
| **總計** | **38** | **完整覆蓋** |

---

## API 使用範例

### 列出所有儀器
```bash
curl http://localhost:9100/api/instruments
```

### 只列出已啟用的儀器
```bash
curl http://localhost:9100/api/instruments?enabled_only=true
```

### 建立新儀器
```bash
curl -X POST http://localhost:9100/api/instruments \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "DAQ973A_2",
    "instrument_type": "DAQ973A",
    "name": "Keysight DAQ973A #2",
    "conn_type": "VISA",
    "conn_params": {"address": "TCPIP0::192.168.1.11::inst0::INSTR", "timeout": 5000},
    "enabled": true
  }'
```

### 更新儀器
```bash
curl -X PATCH http://localhost:9100/api/instruments/DAQ973A_2 \
  -H "Content-Type: application/json" \
  -d '{"enabled": false, "name": "Updated Name"}'
```

### 刪除儀器
```bash
curl -X DELETE http://localhost:9100/api/instruments/DAQ973A_2
```

---

## 資料庫初始化

首次部署時執行：

```bash
# 1. 建立 schema
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/schema.sql

# 2. 匯入預設資料
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_data.sql

# 3. 匯入儀器配置（新增）
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_instruments.sql
```

---

## 向後相容性

現有使用 `get_instrument_settings()` 的程式碼無需修改：

```python
# 舊方式（仍然有效）
from app.core.instrument_config import get_instrument_settings
settings = get_instrument_settings()
config = settings.get_instrument("DAQ973A_1")

# 新方式（DB 支援）
from app.core.instrument_config import get_instrument_provider
from app.core.database import get_db

provider = get_instrument_provider(db)  # 或使用 InstrumentRepository
config = provider.get_instrument("DAQ973A_1")
```

`InstrumentExecutor` 自動支援兩種方式：
```python
# 使用 DB provider
executor = InstrumentExecutor(config_provider=provider)

# 或回退到舊方式
executor = InstrumentExecutor()  # 使用 get_instrument_settings()
```

---

## 效能考量

- **TTL 快取**: 30 秒快取減少 DB 查詢
- **快取失效**: CRUD 操作後呼叫 `invalidate_cache()`
- **執行緒安全**: 使用 `threading.Lock` 和 double-checked locking
- **查詢優化**: 單一儀器查詢直接走 DB（不刷新整個快取）

---

## 未來改進方向

1. **WebSocket 推送**: 儀器配置變更時推送到前端
2. **變更歷史**: 記錄儀器配置的修改歷史
3. **批次操作**: 支援批次啟用/停用儀器
4. **配置驗證**: 建立前測試連線是否可用
5. **權限控制**: 新增認證要求（目前無認證）

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `database/schema.sql` | 資料庫 DDL (包含 instruments 表) |
| `database/seed_instruments.sql` | 預設儀器資料 |
| `database/migrations/add_instruments_table.sql` | **備用** - Raw SQL migration (已被 Alembic 取代) |
| `backend/alembic/env.py` | **已修正** - 新增 Instrument 模型匯入 |
| `backend/alembic/versions/20260312_add_instruments_table.py` | **新增** - Alembic migration (Issue 11.1) |
| `backend/docker-entrypoint.sh` | **新增** - Docker 容器啟動腳本，自動執行 migrations (Issue 11.2) |
| `backend/Dockerfile` | **已修改** - 新增 ENTRYPOINT 指令 |
| `docker-compose.yml` | **已修改** - 新增 migration 環境變數 |
| `backend/app/models/instrument.py` | SQLAlchemy ORM 模型 |
| `backend/app/schemas/instrument.py` | Pydantic 驗證 schemas |
| `backend/app/repositories/instrument_repository.py` | CRUD repository |
| `backend/app/core/instrument_config.py` | Config provider（附錄在檔案末尾） |
| `backend/app/api/instruments.py` | REST API 路由 |
| `backend/app/services/instrument_executor.py` | 消費者整合 |
