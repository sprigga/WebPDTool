# Bug: DB-Backed Instrument Provider 未被 Measurement 層使用

**日期：** 2026-03-12
**嚴重程度：** High（新增 instruments 表記錄後，測試仍回傳 ERROR）
**影響範圍：** ConSoleMeasurement、ComPortMeasurement、TCPIPMeasurement、InstrumentConnectionPool

---

## 問題描述

在 `instruments` 表新增 `instrument_id="console_2"` 後，透過 `TestMain.vue` 執行對應測試項目，仍然收到：

```json
{
  "result": "ERROR",
  "error_message": "Instrument 'console_2' not configured"
}
```

後來回應訊息改為：

```json
{
  "result": "ERROR",
  "error_message": "Instrument console_2 not found in configuration"
}
```

---

## 根本原因分析

### 系統有兩套 Instrument Config 來源

| 來源 | 函數 | 資料來自 |
|------|------|---------|
| Hardcoded Singleton | `get_instrument_settings()` | `InstrumentSettings._load_default_config()`（只含 `console_1`、`DAQ973A_1` 等預設值） |
| DB-Backed Provider | `InstrumentConfigProvider` | `instruments` 資料表（動態配置） |

### 問題：兩個查找點都使用 Hardcoded Singleton

**查找點 1：** `implementations.py` — `ConSoleMeasurement.execute()` 的 lazy import

```python
# 原有程式碼（有問題）
from app.core.instrument_config import get_instrument_settings as _gis
instrument_settings = _gis()               # ← hardcoded singleton
config = instrument_settings.get_instrument(instrument_name)
```

**查找點 2：** `instrument_connection.py` — `InstrumentConnectionPool.get_connection()`

```python
# 原有程式碼（有問題）
settings = get_instrument_settings()       # ← hardcoded singleton
config = settings.get_instrument(instrument_id)
```

即使 DB-Backed Provider 已在之前的 commit 建立，卻沒有人在測量執行路徑中呼叫它。

---

## 除錯過程

### Step 1：確認資料庫記錄存在

```sql
SELECT instrument_id, instrument_type, name, enabled FROM instruments;
-- 確認 console_2 已存在
```

### Step 2：直接 API 呼叫重現問題

```bash
TOKEN=$(curl -s -X POST http://localhost:9100/api/auth/login \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "...")

curl -s -X POST http://localhost:9100/api/measurements/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "measurement_type": "console",
    "test_params": {"Instrument": "console_2", "Command": "echo hello"}
  }'
# → ERROR: "Instrument 'console_2' not configured"
```

### Step 3：追蹤錯誤訊息來源

```python
# 錯誤訊息 "not configured" → implementations.py:505
# 錯誤訊息 "not found in configuration" → instrument_connection.py:440
```

兩個不同訊息揭示了**兩個獨立的查找點**都需要修正。

### Step 4：確認 main.py startup 沒有初始化全域 DB provider

```bash
docker-compose logs backend | grep "InstrumentConfig"
# → 無任何相關日誌，確認 DB provider 從未被初始化
```

### Step 5：加入全域 DB provider 並驗證

修正後重啟，確認日誌出現：

```
Global DB-backed InstrumentConfigProvider initialized
```

再次呼叫 API → `result: "PASS"`。

---

## 修正方案

### 1. `instrument_config.py`：新增全域 DB provider 的 getter/setter

```python
# 新增（在 get_instrument_settings() 之後）
_global_instrument_provider = None

def set_global_instrument_provider(provider: "InstrumentConfigProvider") -> None:
    """Set the global DB-backed instrument provider (called at app startup)."""
    global _global_instrument_provider
    _global_instrument_provider = provider

def get_global_instrument_provider() -> Optional["InstrumentConfigProvider"]:
    """Return the global DB-backed provider if set, else None."""
    return _global_instrument_provider
```

### 2. `main.py`：startup 時初始化全域 DB provider

```python
@app.on_event("startup")
async def startup_event():
    # ...
    try:
        from app.core.database import SessionLocal as SyncSessionLocal
        from app.repositories.instrument_repository import InstrumentRepository
        from app.core.instrument_config import InstrumentConfigProvider, set_global_instrument_provider
        db = SyncSessionLocal()
        repo = InstrumentRepository(db)
        provider = InstrumentConfigProvider(repo=repo, cache_ttl=30.0)
        set_global_instrument_provider(provider)
        logger.info("Global DB-backed InstrumentConfigProvider initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize DB instrument provider (fallback to hardcoded): {e}")
```

### 3. `implementations.py`：ConSole/ComPort/TCPIP 改用 DB provider（replace_all）

```python
# 原有程式碼（已保留為註解）:
# instrument_settings = _gis()
# config = instrument_settings.get_instrument(instrument_name)

# 修改：優先使用全域 DB-backed provider
from app.core.instrument_config import get_global_instrument_provider
_db_provider = get_global_instrument_provider()
if _db_provider is not None:
    config = _db_provider.get_instrument(instrument_name)
else:
    instrument_settings = _gis()
    config = instrument_settings.get_instrument(instrument_name)
```

此修改套用到三個 Measurement 類別（`replace_all=true`）。

### 4. `instrument_connection.py`：ConnectionPool 建立連線時改用 DB provider

```python
# 原有程式碼（已保留為註解）:
# settings = get_instrument_settings()
# config = settings.get_instrument(instrument_id)

# 修改：優先使用全域 DB-backed provider
from app.core.instrument_config import get_global_instrument_provider
_db_provider = get_global_instrument_provider()
if _db_provider is not None:
    config = _db_provider.get_instrument(instrument_id)
else:
    settings = get_instrument_settings()
    config = settings.get_instrument(instrument_id)
```

---

## 驗證

修正並重啟後，API 回傳：

```json
{
  "result": "PASS",
  "measured_value": "hello_from_console_2",
  "error_message": null,
  "execution_duration_ms": 148
}
```

---

## 新增的測試資料

### instruments 表

```sql
INSERT INTO instruments (instrument_id, instrument_type, name, conn_type, conn_params, enabled, description)
VALUES (
  'console_2', 'console', 'Console Command #2',
  'LOCAL', '{"address":"local://console"}',
  1, 'Second virtual instrument for OS subprocess command execution'
);
```

### test_plans 表（PROJ001 / STA001）

```sql
INSERT INTO test_plans (
  project_id, station_id, item_no, item_name, item_key,
  test_type, switch_mode, parameters,
  limit_type, value_type,
  sequence_order, enabled, test_plan_name
) VALUES (
  1, 1, 999, 'console_2 測試項目', 'console2_test',
  'console', 'console_2',
  '{"Instrument": "console_2", "Command": "echo hello_from_console_2"}',
  'none', 'string',
  999, 1, 'console_2_demo'
);
```

---

## 關鍵架構說明

```
測試執行路徑：
  ConSoleMeasurement.execute()
    ├── get_global_instrument_provider()   ← 查 DB（修正後）
    │     └── InstrumentConfigProvider.get_instrument("console_2")
    │           └── InstrumentRepository → instruments 表
    └── connection_pool.get_connection("console_2")
          ├── get_global_instrument_provider()  ← 查 DB（修正後）
          └── create_instrument_connection(config)
                └── ConSoleCommandDriver → subprocess 執行命令
```

### 查找優先級（修正後）

1. **全域 DB-backed provider**（`_global_instrument_provider`）— 讀 `instruments` 表，TTL 快取 30s
2. **Hardcoded singleton**（`get_instrument_settings()`）— 回退，只含預設值

---

## 涉及檔案

| 檔案 | 修改類型 |
|------|---------|
| `backend/app/core/instrument_config.py` | 新增 `set_global_instrument_provider` / `get_global_instrument_provider` |
| `backend/app/main.py` | startup 初始化全域 DB provider |
| `backend/app/measurements/implementations.py` | 3 個 Measurement 類別改用 DB provider |
| `backend/app/services/instrument_connection.py` | ConnectionPool 改用 DB provider |
