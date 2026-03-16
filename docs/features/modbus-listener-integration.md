# Modbus Listener Integration

**實作日期：** 2026-03-16
**相關 Commits：** `4eb94af` → `e2a7a82`（共 8 commits）

## 目標

將 PDTool4 的 Qt-based `ModbusListener.py` 重構為 WebPDTool 的 Vue 3 + FastAPI 架構，實現 Modbus TCP 通訊以支援製造測試自動化。

**替換對應：**

| PDTool4（Qt）| WebPDTool（Web）|
|---|---|
| Qt Signals | WebSocket pub-sub |
| QThread | asyncio + FastAPI BackgroundTask |
| JSON 設定檔 | SQLAlchemy model + MySQL |
| `ModbusListener.py` 單體類 | `ModbusListenerService` + `ModbusManager` 分層 |

---

## 架構總覽

```
Frontend (Vue 3)
├── ModbusConfig.vue          — 每站台 CRUD 設定介面
├── ModbusStatusIndicator.vue — 即時狀態指示器（CSS 動畫點）
└── api/modbus.js             — REST + WebSocket API 客戶端

Backend (FastAPI)
├── api/modbus.py             — REST 端點（CRUD + 狀態）
├── api/modbus_ws.py          — WebSocket 端點（即時事件）
├── services/modbus/
│   ├── modbus_listener.py    — 核心非同步 Modbus 監聽服務
│   ├── modbus_manager.py     — 多站台監聽器管理（singleton）
│   └── modbus_config.py      — PDTool4 相容格式轉換
├── models/modbus_config.py   — SQLAlchemy ORM 模型
└── schemas/modbus.py         — Pydantic v2 資料驗證

Database
└── modbus_configs table      — 每站台一筆設定
```

---

## 實作細節

### 1. 資料庫模型（`backend/app/models/modbus_config.py`）

`modbus_configs` 表與 `stations` 一對一關聯（`station_id UNIQUE`）。暫存器位址以 hex 字串儲存（`"0x0013"`），保留 PDTool4 原始設定格式可讀性。

```python
class ModbusConfig(Base):
    __tablename__ = "modbus_configs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.id"), unique=True, nullable=False)
    server_host = Column(String(255), nullable=False, default="127.0.0.1")
    server_port = Column(Integer, nullable=False, default=502)
    device_id = Column(Integer, nullable=False, default=1)
    enabled = Column(Boolean, nullable=False, default=True)
    delay_seconds = Column(Integer, nullable=False, default=1)
    simulation_mode = Column(Boolean, nullable=False, default=False)
    # 暫存器位址（hex 字串）
    ready_status_address = Column(String(20), nullable=False, default="0x0013")
    read_sn_address = Column(String(20), nullable=False, default="0x0064")
    test_status_address = Column(String(20), nullable=False, default="0x0014")
    test_result_address = Column(String(20), nullable=False, default="0x0015")
    # ... 其餘欄位
    station = relationship("Station", back_populates="modbus_config")
```

**`Station` 模型也需新增關係：**

```python
# backend/app/models/station.py
modbus_config = relationship(
    "ModbusConfig", back_populates="station",
    uselist=False, cascade="all, delete-orphan"
)
```

### 2. Pydantic v2 Schema（`backend/app/schemas/modbus.py`）

hex 位址使用 `@field_validator`（Pydantic v2 語法，**非** `@validator`）：

```python
@field_validator('ready_status_address', 'read_sn_address', 'test_status_address', 'test_result_address', ...)
@classmethod
def validate_hex_string(cls, v: str) -> str:
    if not (v.startswith('0x') or v.startswith('0X')):
        raise ValueError('Hex address must start with 0x or 0X')
    int(v, 16)  # 驗證是合法 hex
    return v
```

### 3. 核心監聽服務（`backend/app/services/modbus/modbus_listener.py`）

#### 關鍵設計決策

**pymodbus 懶惰載入（Lazy Import）：**
```python
async def _run_async(self):
    from pymodbus.client import AsyncModbusTcpClient  # 在此才 import
    ...
```
目的：讓沒有 pymodbus 的測試環境可以 import 並測試其他邏輯，不因缺少硬體依賴而失敗。

**SN 解碼（PDTool4 相容）：**
```python
def _decode_sn(self, registers: list) -> str:
    raw = b''
    for reg in registers:
        raw += struct.pack('>H', reg)
    return raw.decode('ascii', errors='ignore').rstrip('\x00').strip()
```
每個 16-bit 暫存器存放 2 個 ASCII 字元（big-endian），與 PDTool4 `ModbusListener.py` 相同演算法。

**非同步輪詢迴圈：**
```python
async def start(self):
    self.running = True
    self._task = asyncio.create_task(self._run_async())

async def stop(self):
    self.running = False
    if self._task:
        self._task.cancel()
        await asyncio.gather(self._task, return_exceptions=True)
```

### 4. 管理器 Singleton（`backend/app/services/modbus/modbus_manager.py`）

```python
class ModbusManager:
    def __init__(self):
        self.active_listeners: Dict[int, ModbusListenerService] = {}
        self._lock = asyncio.Lock()

    async def start_listener(self, config: ModbusConfigCreate) -> ModbusListenerService:
        async with self._lock:
            # 若已有同 station_id 的 listener 先停止
            if config.station_id in self.active_listeners:
                await self.stop_listener(config.station_id)
            listener = ModbusListenerService(config)
            await listener.start()
            self.active_listeners[config.station_id] = listener
            return listener

    async def write_test_result(self, station_id: int, passed: bool) -> bool:
        listener = self.active_listeners.get(station_id)
        if not listener:
            return False
        return await listener.write_test_result(passed)

# 模組層級 singleton（整個程序共用）
modbus_manager = ModbusManager()
```

### 5. TestEngine 整合（`backend/app/services/test_engine.py`）

測試完成後靜默寫入 Modbus 結果（不影響測試流程）：

```python
async def _write_modbus_result(self, station_id: int, passed: bool) -> None:
    try:
        await modbus_manager.write_test_result(station_id=station_id, passed=passed)
    except Exception as e:
        logger.warning(f"Modbus write skipped: {e}")
        # 故意吞掉錯誤 — Modbus 失敗不能導致測試 session 失敗
```

### 6. WebSocket 即時事件（`backend/app/api/modbus_ws.py`）

```
WS /api/modbus/ws/{station_id}

Client → {"action": "subscribe"}
Client → {"action": "start", "config": {...}}
Client → {"action": "stop"}
Client → {"action": "get_status"}
Server → {"event": "sn_received", "sn": "...", "station_id": 1}
Server → {"event": "error", "message": "...", "station_id": 1}
Server → {"event": "status", "running": true, "connected": true, ...}
```

### 7. 前端 ModbusStatusIndicator

```vue
<!-- 使用 CSS 動畫點顯示連線狀態 -->
<div :class="['status-dot', statusClass]" @click="showDetail" />
```

狀態對應：`connected` → 綠色閃爍、`connecting` → 黃色閃爍、`disconnected`/`error` → 紅色、`unknown` → 灰色。

整合至 `TestMain.vue`：
```vue
<ModbusStatusIndicator v-if="currentStation" :station-id="currentStation.id" />
```

---

## 除錯過程與修正記錄

### Bug 1：`Station` 模型欄位名稱錯誤

**問題：** 計畫文件中使用 `name=`, `code=`，但實際模型欄位是 `station_name=`, `station_code=`（同理 `Project` 使用 `project_name=`, `project_code=`）。

**症狀：** 測試建立 `Station` 物件時 `TypeError: unexpected keyword argument 'name'`。

**修正：** 讀取 `backend/app/models/station.py` 確認實際欄位名稱後，將所有測試中的欄位名稱對應更新。

**教訓：** 寫測試前先確認實際 ORM 模型欄位，不要依賴計畫文件中的假設欄位名。

---

### Bug 2：`get_db` import 路徑錯誤

**問題：** 計畫文件使用 `from app.core.database import get_db`，但此專案的 async db 依賴函數名稱是 `get_async_db`。

**症狀：** `ImportError: cannot import name 'get_db' from 'app.core.database'`。

**修正：**
```python
# 錯誤
from app.core.database import get_db

# 正確
from app.core.database import get_async_db as get_db
```

---

### Bug 3：`get_current_user` 位置不正確

**問題：** 計畫文件假設 `get_current_user` 在 `app.core.security`，實際上在 `app.dependencies`。

**修正：**
```python
# 錯誤
from app.core.security import get_current_user

# 正確
from app.dependencies import get_current_user
```

---

### Bug 4：Manager 測試中 `running is True` 失敗

**問題：** 測試對 `ModbusListenerService.start()` 整個 mock 掉，導致 `running = True` 這行也被跳過，斷言 `listener.running is True` 失敗。

**症狀：**
```python
with patch.object(listener, 'start', new_callable=AsyncMock):
    await manager.start_listener(config)
assert listener.running is True  # FAIL：running 仍是 False
```

**修正：** 改為 mock `_run_async`（背景 polling 迴圈），讓 `start()` 正常執行並設定 `running = True`：
```python
with patch.object(listener, '_run_async', new_callable=AsyncMock):
    await listener.start()
assert listener.running is True  # PASS
```

**原理：** `start()` 只做兩件事：`self.running = True` + `asyncio.create_task(_run_async())`。Mock `_run_async` 讓 task 立即返回，但 `running` 狀態正確設定。

---

### Bug 5：Pydantic v1 `@validator` vs v2 `@field_validator`

**問題：** 計畫文件使用 Pydantic v1 的 `@validator` 語法，但專案使用 Pydantic v2。

**症狀：** `PydanticUserError: The 'validator' decorator is deprecated`。

**修正：**
```python
# Pydantic v1（錯誤）
@validator('ready_status_address')
def validate_hex(cls, v):
    ...

# Pydantic v2（正確）
@field_validator('ready_status_address', ...)
@classmethod
def validate_hex_string(cls, v: str) -> str:
    ...
```

---

### Bug 6：方法名稱不一致（`_byteoffset` vs `_byte_offset`）

**問題：** 計畫文件中方法名稱為 `_byteoffset`，但測試呼叫 `_byte_offset`（有底線分隔）。

**修正：** 以測試檔為準，實作方法命名為 `_byte_offset`。

**原則：** 當計畫和測試衝突時，以測試為準（測試是可執行的規格）。

---

### Bug 7：Commit 訊息含署名

**問題：** 使用者要求 commit 訊息不得包含 `Co-Authored-By` 署名行。

**修正（事後批次清除）：**
```bash
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
  --msg-filter 'sed "/^Co-Authored-By:/d"' \
  HEAD~8..HEAD
```

**注意：** 此操作會重寫 commit SHA，只能在尚未推送到遠端時使用。

---

### Bug 8：`.venv` 權限問題（Worktree 合併後）

**問題：** Worktree 在 `backend/.venv`（由 Docker 以 root 建立）嘗試重建時，`uv sync` 失敗：
```
error: failed to remove directory `backend/.venv/bin`: Permission denied (os error 13)
```

**根因：** 主分支的 `backend/.venv` 是由 Docker container 以 `root` 建立，worktree 的 `.venv` 由 `ubuntu` 使用者建立。合併後 `uv` 嘗試重建 root-owned `.venv` 時沒有權限。

**解決方案：** 指定 `UV_PROJECT_ENVIRONMENT` 指向 worktree 的 ubuntu-owned `.venv`：
```bash
UV_PROJECT_ENVIRONMENT=/path/to/.worktrees/modbus-listener/backend/.venv \
  uv run pytest ...
```
這讓測試可在合併後的 main 分支程式碼上正常執行，不需要重建 `.venv`。

**根本解法：** 長期應使用 `docker-compose exec backend uv sync` 在容器內重建，或使用 `sudo rm -rf backend/.venv` 後重新 `uv sync`。

---

## 測試覆蓋

| 測試檔 | 測試數 | 說明 |
|--------|--------|------|
| `test_models/test_modbus_config_model.py` | 4 | SQLite in-memory，模型 CRUD |
| `test_schemas/test_modbus_schemas.py` | 5 | Hex 驗證、欄位預設值 |
| `test_services/test_modbus_listener_service.py` | 6 | Listener 生命週期、SN 解碼 |
| `test_services/test_modbus_manager.py` | 5 | Manager singleton、多站台 |
| `test_services/test_modbus_ws.py` | 5 | WebSocket pub-sub |
| `test_services/test_modbus_integration.py` | 4 | TestEngine 整合 |
| `test_services/test_modbus_e2e.py` | 3（2 標記 `e2e`）| 需硬體模擬器 |
| **合計** | **32** | |

### 執行方式

```bash
# 一般測試（不需硬體）
cd backend
uv run pytest tests/test_models/test_modbus_config_model.py \
               tests/test_schemas/test_modbus_schemas.py \
               tests/test_services/test_modbus_listener_service.py \
               tests/test_services/test_modbus_manager.py \
               tests/test_services/test_modbus_ws.py \
               tests/test_services/test_modbus_integration.py -v

# E2E 測試（需先啟動模擬器）
python scripts/modbus_simulator.py --port 5020
uv run pytest -m e2e tests/test_services/test_modbus_e2e.py -v
```

### Modbus TCP 模擬器

```bash
# scripts/modbus_simulator.py
# 預載 SN "TEST12345678" 於暫存器 0x0064-0x006E
python scripts/modbus_simulator.py --host 127.0.0.1 --port 5020
```

模擬器行為：
- `ready_status` (0x0013) 預設 `0x00`（未就緒），手動設為 `0x01` 觸發 SN 讀取
- SN 資料 (0x0064-0x006E)：`"TEST12345678"`
- 接受 `test_status` (0x0014) 和 `test_result` (0x0015) 寫入

---

## API 端點

### REST (`/api/modbus/`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/configs` | 列出所有 Modbus 設定 |
| GET | `/configs/{id}` | 取得特定設定 |
| GET | `/stations/{station_id}/config` | 取得站台設定 |
| POST | `/configs` | 新增設定（admin） |
| PUT | `/configs/{id}` | 更新設定（admin） |
| DELETE | `/configs/{id}` | 刪除設定（admin） |
| GET | `/status` | 所有站台監聽器狀態 |
| GET | `/status/{station_id}` | 特定站台狀態 |

### WebSocket (`/api/modbus/ws/{station_id}`)

客戶端傳送 JSON action，伺服器廣播事件給同站台所有訂閱者。

---

## 資料庫遷移

```bash
cd backend
# 遷移已產生於：alembic/versions/d31e415c57a9_add_modbus_config_table.py
alembic upgrade head
```

downgrade：
```bash
alembic downgrade d31e415c57a9-1
```
