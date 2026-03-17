# Issue: test_results 與 test_sessions 時間欄位時區錯誤（UTC → Asia/Taipei）

**日期：** 2026-03-16
**影響範圍：** `test_results.test_time`、`test_sessions.start_time`、`test_sessions.end_time`、`test_sessions.created_at`
**嚴重性：** 資料一致性（時間戳與舊資料相差 8 小時，UI 顯示時間不符實際操作時間）
**狀態：** ✅ 已修正

---

## 問題描述

`test_results.test_time`、`test_sessions.start_time`、`test_sessions.end_time` 寫入資料庫的時間戳為 UTC（世界協調時間），與舊有資料（Asia/Taipei，UTC+8）相差 8 小時，導致：

1. 前端 TestResults 對話框顯示的測試時間比實際操作早 8 小時
2. 新資料與舊資料並存時，時間排序混亂（UTC 與 Asia/Taipei 混雜）
3. 查詢時使用日期範圍篩選（`start_date` / `end_date`）會出現偏差

---

## 根本原因分析

### 問題一：Python 端使用 `datetime.utcnow()`

`test_engine.py` 寫入 session 的 `start_time`、`end_time` 時使用 naive UTC datetime：

```python
# test_engine.py（修正前）
test_state.start_time = datetime.utcnow()   # naive UTC，無時區資訊
session.end_time = datetime.utcnow()        # naive UTC
```

SQLAlchemy 收到 naive datetime 時，直接原樣存入 MySQL TIMESTAMP 欄位。MySQL TIMESTAMP 在儲存時會將傳入值視為當前 session 的 `time_zone`（通常為 Asia/Taipei），但 Python 傳入的值已是 UTC，造成兩端不一致。

### 問題二：`MeasurementResult.test_time` 使用 `timezone.utc`

```python
# measurements/base.py（修正前）
self.test_time = datetime.now(timezone.utc)  # UTC aware datetime
```

這個值在 `test_engine.py` 的 `_save_test_result()` 建立 `TestResultModel` 時**沒有被傳入**，導致 DB 改用 `server_default`（`UTC_TIMESTAMP()`），仍為 UTC。

### 問題三：`server_default` 設為 `UTC_TIMESTAMP()`

前一次修正嘗試透過 MySQL `UTC_TIMESTAMP()` 統一時區，但這讓所有欄位都鎖定 UTC，與舊資料（Asia/Taipei）矛盾：

```python
# models/test_session.py（修正前）
start_time = Column(TIMESTAMP, server_default=func.utc_timestamp())

# models/test_result.py（修正前）
test_time = Column(TIMESTAMP, server_default=func.utc_timestamp())
```

```sql
-- database/schema.sql（修正前）
start_time TIMESTAMP DEFAULT (UTC_TIMESTAMP()),
test_time  TIMESTAMP DEFAULT (UTC_TIMESTAMP()),
```

---

## 除錯過程

### Step 1：確認時間欄位的寫入路徑

搜尋所有寫入 `test_time`、`start_time`、`end_time` 的程式碼：

```bash
grep -rn "test_time\|start_time\|end_time\|utcnow" backend/app --include="*.py" | grep -v "\.pyc"
```

發現四個關鍵寫入點：

| 位置 | 欄位 | 原始值 |
|------|------|--------|
| `measurements/base.py:146` | `MeasurementResult.test_time` | `datetime.now(timezone.utc)` |
| `services/test_engine.py:83` | `test_state.start_time` | `datetime.utcnow()` |
| `services/test_engine.py:448` | `session.end_time` | `datetime.utcnow()` |
| `api/tests.py:584` | `session.end_time`（abort 端點） | `datetime.utcnow()` |

### Step 2：確認 `test_time` 是否實際被傳入 ORM

查看 `test_engine.py` 的 `_save_test_result()`：

```python
db_result = TestResultModel(
    session_id=session_id,
    ...
    execution_duration_ms=result.execution_duration_ms
    # ← test_time 沒有出現！改由 server_default 填入
)
```

`MeasurementResult.test_time` 有被設定，但建立 `TestResultModel` 時未傳入，`server_default=func.utc_timestamp()` 接管，值為 UTC。

`api/tests.py` 的單筆和批次建立端點也同樣沒有傳 `test_time`。

### Step 3：確認 `server_default` 的行為

MySQL `UTC_TIMESTAMP()` — 永遠回傳 UTC，不受 `@@time_zone` 設定影響。
MySQL `NOW()` / `CURRENT_TIMESTAMP` — 回傳當前 session 的時區時間（Asia/Taipei = UTC+8）。

結論：前一次修正使 `server_default` 從 `CURRENT_TIMESTAMP`（Asia/Taipei）改為 `UTC_TIMESTAMP()`，解決了 `start_time`（MySQL server 填入）與 `end_time`（Python 填入）不一致的問題，但代價是所有新資料都變成 UTC，與舊資料（Asia/Taipei）不相容。

### Step 4：確認正確修法

決策：**Python 端主導，明確傳入 Asia/Taipei aware datetime**。

- 使用 Python 3.9+ 標準庫 `zoneinfo.ZoneInfo("Asia/Taipei")` 取代 `datetime.utcnow()`
- 所有建立 `TestResultModel` 的地方都明確傳入 `test_time`
- `server_default` 還原為 `func.now()` / `CURRENT_TIMESTAMP`（作為保底，防止繞過 ORM 的直接 SQL INSERT）
- `duration_seconds` 計算使用兩端相同的 aware datetime，差值結果不變

---

## 修正方式

### 1. `backend/app/measurements/base.py`

加入 `ZoneInfo` import，`MeasurementResult.test_time` 改用台北時間：

```python
# 修改前
from datetime import datetime, timezone
self.test_time = datetime.now(timezone.utc)

# 修改後
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
self.test_time = datetime.now(ZoneInfo("Asia/Taipei"))
```

### 2. `backend/app/services/test_engine.py`

加入 `ZoneInfo` import 與 `_TZ_TAIPEI` 常數，修改三處 `datetime.utcnow()`，並在 `TestResultModel(...)` 補傳 `test_time`：

```python
# 修改前
from datetime import datetime
test_state.start_time = datetime.utcnow()
duration_seconds = round((datetime.utcnow() - test_state.start_time).total_seconds(), 6)
session.end_time = datetime.utcnow()

# 修改後
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
_TZ_TAIPEI = ZoneInfo("Asia/Taipei")

test_state.start_time = datetime.now(_TZ_TAIPEI)
_now = datetime.now(_TZ_TAIPEI)
duration_seconds = round((_now - test_state.start_time).total_seconds(), 6)
session.end_time = _now
```

`_save_test_result()` 補傳 `test_time`：

```python
db_result = TestResultModel(
    ...
    execution_duration_ms=result.execution_duration_ms,
    # 修改(2026-03-16): 明確傳入 Asia/Taipei 時間，取代 server_default
    test_time=result.test_time,
)
```

### 3. `backend/app/api/tests.py`

加入 `ZoneInfo` import 與 `_TZ_TAIPEI` 常數，修改 abort 端點的 `end_time`，以及兩處 `TestResultModel(...)` 補傳 `test_time`：

```python
# abort 端點
# 修改前: session.end_time = datetime.utcnow()
session.end_time = datetime.now(_TZ_TAIPEI)

# 單筆建立端點（tests.py:444）
db_result = TestResultModel(
    ...
    wall_time_ms=result_data.wall_time_ms,
    test_time=datetime.now(_TZ_TAIPEI),   # 新增
)

# 批次建立端點（tests.py:520）
db_result = TestResultModel(
    ...
    wall_time_ms=result_data.wall_time_ms,
    test_time=datetime.now(_TZ_TAIPEI),   # 新增
)
```

### 4. `backend/app/models/test_session.py`

`server_default` 還原為 `func.now()`（保底，MySQL server 依 Asia/Taipei 填入）：

```python
# 修改前: server_default=func.utc_timestamp()
start_time = Column(TIMESTAMP, server_default=func.now())
created_at = Column(TIMESTAMP, server_default=func.now())
```

### 5. `backend/app/models/test_result.py`

```python
# 修改前: server_default=func.utc_timestamp()
test_time = Column(TIMESTAMP, server_default=func.now(), index=True)
```

### 6. `database/schema.sql`

```sql
-- 修改前
start_time TIMESTAMP DEFAULT (UTC_TIMESTAMP()),
created_at TIMESTAMP DEFAULT (UTC_TIMESTAMP()),
test_time  TIMESTAMP DEFAULT (UTC_TIMESTAMP()),

-- 修改後
start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
test_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
```

---

## 設計原則說明

### Python 端主導、DB 端保底

| 層級 | 機制 | 時區 |
|------|------|------|
| Python（主要） | `datetime.now(ZoneInfo("Asia/Taipei"))` | Asia/Taipei（明確） |
| MySQL server_default（保底） | `CURRENT_TIMESTAMP` / `func.now()` | 跟隨 MySQL `@@global.time_zone`（Asia/Taipei） |

Python 明確傳入 aware datetime 時，`server_default` 不會被觸發。`server_default` 只在直接 SQL INSERT（繞過 ORM）時才生效，兩層都指向 Asia/Taipei，確保一致。

### `zoneinfo` 取代 `pytz`

`zoneinfo` 是 Python 3.9+ 標準庫，無需額外安裝，且正確處理 DST（日光節約時間）轉換規則。台灣（Asia/Taipei）為 UTC+8，無 DST，偏移量永遠固定。

### duration 計算不受影響

`duration_seconds = (end_time - start_time).total_seconds()`

兩端都是 Asia/Taipei aware datetime，相減得到的 `timedelta` 為純粹時間差，與時區選擇無關，數值不會改變。

---

## 修改的檔案清單

| 檔案 | 修改說明 |
|------|---------|
| `backend/app/measurements/base.py` | `test_time` 改用 `ZoneInfo("Asia/Taipei")` |
| `backend/app/services/test_engine.py` | `start_time`、`end_time` 改台北時間；`TestResultModel` 補傳 `test_time` |
| `backend/app/api/tests.py` | abort `end_time` 改台北時間；兩處 `TestResultModel` 補傳 `test_time` |
| `backend/app/models/test_session.py` | `server_default` 還原為 `func.now()` |
| `backend/app/models/test_result.py` | `server_default` 還原為 `func.now()` |
| `database/schema.sql` | `DEFAULT (UTC_TIMESTAMP())` 還原為 `DEFAULT CURRENT_TIMESTAMP` |
