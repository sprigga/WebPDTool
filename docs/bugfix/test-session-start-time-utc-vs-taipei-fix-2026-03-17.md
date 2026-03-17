# test_sessions.start_time 時區錯誤修正（UTC vs Asia/Taipei）

**日期：** 2026-03-17
**影響範圍：**
- `backend/app/api/tests.py` → `create_test_session()`（後端 DB 寫入）
- `frontend/src/views/TestResults.vue` → `formatDateTime()`（前端顯示）

**嚴重性：** 資料一致性 + UI 顯示錯誤（開始/結束時間均多顯示 8 小時）
**狀態：** ✅ 已修正

---

## 問題描述

查詢 `test_sessions` 資料表，session id 219 的時間欄位出現矛盾：

```sql
SELECT id, start_time, end_time FROM test_sessions WHERE id = 219;
```

| id  | start_time          | end_time            |
|-----|---------------------|---------------------|
| 219 | 2026-03-16 08:57:21 | 2026-03-16 16:57:22 |

`start_time` 與 `end_time` 相差剛好 8 小時，即 `start_time` 為 UTC 時間，`end_time` 為 Asia/Taipei（UTC+8）時間。

**問題影響：**
- `test_duration_seconds` 被計算為負數或超過實際測試時間（end - start = 約 8 小時而非幾秒）
- 前端 TestResults 顯示的 Session 開始時間比實際早 8 小時
- 與 `docs/issues/2026-03-16-datetime-timezone-utc-to-taipei.md` 描述的 UTC 問題再次出現，但此次原因不同

---

## 根本原因分析

### 問題源頭：`create_test_session()` 未傳入 `start_time`

`api/tests.py` 的 `create_test_session` endpoint 建立 `TestSessionModel` 時，**沒有傳入 `start_time`**：

```python
# 修正前（api/tests.py:82）
db_session = TestSessionModel(
    serial_number=session_data.serial_number,
    station_id=session_data.station_id,
    user_id=current_user.get("id")
    # ← start_time 未傳入，由 server_default 填入
)
```

`TestSession` 模型定義：

```python
# models/test_session.py
start_time = Column(TIMESTAMP, server_default=func.now())
```

當 Python 未傳入 `start_time` 時，SQLAlchemy INSERT 觸發 MySQL 的 `server_default=func.now()`（即 `CURRENT_TIMESTAMP`）。此函式的回傳值取決於 MySQL **session 級別的 `@@time_zone` 設定**。

若 MySQL 連線時 `@@session.time_zone = 'SYSTEM'` 且系統時區為 UTC（Docker 預設），`CURRENT_TIMESTAMP` 回傳 UTC 時間，存入 `start_time`。

### 為何 `end_time` 正確？

`end_time` 由 `_finalize_test_session()` 從 Python 端**明確傳入**：

```python
# services/test_engine.py:461
# 修改(2026-03-16): 改用 Asia/Taipei
session.end_time = _now  # _now = datetime.now(_TZ_TAIPEI)
```

Python 端的 `datetime.now(ZoneInfo("Asia/Taipei"))` 不依賴 MySQL 時區設定，直接產生 Asia/Taipei aware datetime，SQLAlchemy 將其轉換為正確的時間值存入 DB。

### 時間寫入路徑比對

| 欄位 | 寫入時機 | 寫入方式 | 時區結果 |
|------|----------|----------|----------|
| `start_time` | `POST /sessions` 建立 Session 時 | MySQL `server_default=func.now()` | **UTC ❌** |
| `end_time` | `_finalize_test_session()` 執行完畢時 | Python `datetime.now(_TZ_TAIPEI)` | **Asia/Taipei ✅** |

---

## 除錯過程

### Step 1：確認 DB 資料

直接查詢資料庫確認現象：

```bash
docker-compose exec db mysql -updtool -ppdtool123 webpdtool \
  -e "SELECT id, start_time, end_time, created_at FROM test_sessions WHERE id = 219;"
```

輸出：

```
id   start_time            end_time              created_at
219  2026-03-16 08:57:21   2026-03-16 16:57:22   2026-03-16 08:57:21
```

`start_time` 與 `created_at` 都是 08:57，`end_time` 是 16:57。兩者差距正好 8 小時 = UTC 偏移量。

### Step 2：確認 `end_time` 的寫入路徑

閱讀 `services/test_engine.py`，確認 `_finalize_test_session()` 中 `end_time` 使用 `datetime.now(_TZ_TAIPEI)`（2026-03-16 已修正）。

### Step 3：追蹤 `start_time` 的寫入路徑

搜尋所有寫入 `start_time` 的程式碼：

```bash
grep -rn "start_time" backend/app --include="*.py" | grep -v ".pyc" | grep -v "test_state"
```

找到兩處：

1. `models/test_session.py` — `server_default=func.now()` （ORM 模型定義）
2. `services/test_engine.py:88` — `test_state.start_time = datetime.now(_TZ_TAIPEI)` （記憶體狀態，非 DB 欄位）

**關鍵發現：** `test_state.start_time` 是 `TestExecutionState`（記憶體中的 Python 物件）的屬性，用於計算 `duration_seconds`，**不是寫入 DB 的路徑**。

DB 的 `test_sessions.start_time` 寫入路徑是：`api/tests.py:82` 的 `TestSessionModel(...)` → INSERT → `server_default=func.now()`。

### Step 4：確認 MySQL 時區設定

```sql
SELECT @@global.time_zone, @@session.time_zone;
-- 結果: SYSTEM / SYSTEM
-- Docker 容器系統時區: UTC
```

因此 `func.now()` = `CURRENT_TIMESTAMP` 在 Docker 環境回傳 UTC。

### Step 5：確認修正方向

與 `docs/issues/2026-03-16-datetime-timezone-utc-to-taipei.md` 描述的設計原則一致：**Python 端主導，DB 端保底**。

修正方式：在 `create_test_session()` 中建立 `TestSessionModel` 時，明確傳入 `start_time=datetime.now(_TZ_TAIPEI)`，取代 `server_default`。

---

## 修正方案

**檔案：** `backend/app/api/tests.py`

```python
# 修正前（第 82-86 行）
db_session = TestSessionModel(
    serial_number=session_data.serial_number,
    station_id=session_data.station_id,
    user_id=current_user.get("id")
)

# 修正後
# 修改(2026-03-16): 明確傳入 Asia/Taipei start_time，避免 server_default 依賴 MySQL 時區設定
# 原有程式碼: 未傳 start_time，改由 server_default=func.now() 填入（若 MySQL session 時區不一致會寫入 UTC）
db_session = TestSessionModel(
    serial_number=session_data.serial_number,
    station_id=session_data.station_id,
    user_id=current_user.get("id"),
    start_time=datetime.now(_TZ_TAIPEI),
)
```

`datetime` 與 `_TZ_TAIPEI` 已在模組頂部定義（2026-03-16 時區修正時已加入）：

```python
# api/tests.py 頂部（已存在，不需額外修改）
from datetime import datetime
from zoneinfo import ZoneInfo
_TZ_TAIPEI = ZoneInfo("Asia/Taipei")
```

---

## 驗證

重啟 backend 服務後，新建 Session 確認：

```bash
docker-compose restart backend
```

預期結果：

```sql
SELECT id, start_time, end_time FROM test_sessions ORDER BY id DESC LIMIT 1;
-- start_time 與 end_time 應在同一小時範圍內（Asia/Taipei 時間，UTC+8）
-- start_time 與 end_time 之差 = 實際測試執行秒數
```

---

## 設計要點

### `server_default` 的風險

MySQL `server_default=func.now()` / `CURRENT_TIMESTAMP` 的回傳值取決於：

1. MySQL `@@global.time_zone`
2. 每個連線的 `@@session.time_zone`
3. 作業系統時區（當設定為 `SYSTEM` 時）

在 Docker 環境中，容器的作業系統時區預設為 UTC，除非在 MySQL 啟動時明確設定 `--default-time-zone=Asia/Taipei`。使用 `server_default` 作為時區敏感欄位的預設值，會因部署環境不同而產生不可預期的結果。

### Python 端主導原則

| 層級 | 機制 | 時區 |
|------|------|------|
| Python（主要） | `datetime.now(ZoneInfo("Asia/Taipei"))` | Asia/Taipei（明確，不受環境影響） |
| MySQL `server_default`（保底） | `CURRENT_TIMESTAMP` / `func.now()` | 跟隨 MySQL `@@time_zone`（環境相依） |

結論：**所有時區敏感的時間欄位都應由 Python 端明確傳入，不依賴 `server_default`。**

### 此問題與 2026-03-16 時區修正的關係

2026-03-16 的修正（`docs/issues/2026-03-16-datetime-timezone-utc-to-taipei.md`）已修正：
- `test_engine.py` 的 `end_time`、`test_state.start_time`
- `measurements/base.py` 的 `test_time`
- `TestResultModel` 的 `test_time` 補傳

**遺漏：** `api/tests.py` `create_test_session()` 建立 `TestSessionModel` 時的 `start_time` 未補傳，導致此次問題。

---

## 修改的檔案清單（後端）

| 檔案 | 修改說明 |
|------|----------|
| `backend/app/api/tests.py` | `create_test_session()` 建立 `TestSessionModel` 時補傳 `start_time=datetime.now(_TZ_TAIPEI)` |

---

## 問題二：前端 TestResults 開始/結束時間多顯示 8 小時

### 問題描述

後端 DB 修正後，前端 TestResults 頁面的「開始時間」與「結束時間」欄位仍顯示錯誤時間，比實際 DB 值多 8 小時：

```
DB 儲存值:  2026-03-17 08:40:27   （Asia/Taipei 正確時間）
UI 顯示值:  2026/03/17 下午 04:40:27 = 16:40:27   （多了 8 小時）
```

### 根本原因：`formatDateTime` 的雙重時區轉換

`TestResults.vue` 的 `formatDateTime()` 函式：

```javascript
// 修正前（TestResults.vue:571）
const normalized = /[Zz]|[+-]\d{2}:?\d{2}$/.test(dateStr) ? dateStr : dateStr + 'Z'
const date = new Date(normalized)
return date.toLocaleString('zh-TW', { timeZone: 'Asia/Taipei', ... })
```

**轉換流程（修正前）：**

```
DB 回傳: "2026-03-17 08:40:27"（無時區後綴）
→ 補 'Z': "2026-03-17 08:40:27Z"（被解讀為 UTC）
→ new Date(): UTC 08:40:27
→ toLocaleString(Taipei): UTC+8 → 16:40:27  ← 錯誤！
```

**此邏輯的歷史背景：**

在 `docs/issues/2026-03-16-datetime-timezone-utc-to-taipei.md` 修正之前，DB 儲存的是 UTC 時間（`08:40:27` = UTC）。補 `'Z'` 後 `toLocaleString(Taipei)` 加 8 小時顯示 `16:40:27` 是正確的。

現在 DB 改為儲存 Asia/Taipei（`08:40:27` = 台北時間），但前端仍以舊邏輯（補 `'Z'`）處理，造成**二次 +8 小時**：

| 階段 | DB 儲存 UTC 時代 | DB 儲存 Taipei 時代 |
|------|------------------|---------------------|
| DB 值 | `08:40:27`（UTC） | `08:40:27`（Taipei） |
| 補 `'Z'` 後解讀 | UTC `08:40:27` ✅ | UTC `08:40:27`（錯誤解讀） |
| `toLocaleString(Taipei)` | `16:40:27` Taipei ✅ | `16:40:27` Taipei ❌（多 8 小時） |

### 除錯過程

#### Step 1：確認 UI 顯示值與 DB 值的差距

截圖顯示 Session 220 的開始時間為 `2026/03/17 下午 04:40:27`（16:40:27）。

查詢 DB：

```bash
docker-compose exec db mysql -updtool -ppdtool123 webpdtool \
  -e "SELECT id, start_time, end_time FROM test_sessions WHERE id = 220;"
```

DB 儲存：`start_time = 2026-03-17 08:40:27`、`end_time = 2026-03-17 08:40:28`。

UI 顯示比 DB 值多 8 小時 → 確認是前端轉換邏輯問題。

#### Step 2：定位 `formatDateTime` 邏輯

閱讀 `TestResults.vue:565-582`，找到 `dateStr + 'Z'` — 這是讓瀏覽器將無後綴 datetime 字串解讀為 UTC 的慣用做法，但現在 DB 已改存 Taipei 時間，此邏輯不再適用。

#### Step 3：確認修正方向

DB 回傳的 datetime 字串無時區後綴（MySQL TIMESTAMP 欄位輸出格式為 `"YYYY-MM-DD HH:MM:SS"`）。

正確處理：補 `'+08:00'` 讓 `new Date()` 將其解讀為 Taipei 時間，後續 `toLocaleString(Taipei)` 即為 no-op（+8 顯示 +8 = 正確值）。

### 修正方案

**檔案：** `frontend/src/views/TestResults.vue`

```javascript
// 修正前（第 569-571 行）
// Append 'Z' if no timezone info, so the browser treats it as UTC
// then display in Asia/Taipei timezone
const normalized = /[Zz]|[+-]\d{2}:?\d{2}$/.test(dateStr) ? dateStr : dateStr + 'Z'

// 修正後
// 修改(2026-03-17): DB 已統一儲存 Asia/Taipei 時間，補上 +08:00 而非 'Z'
// 原有程式碼: dateStr + 'Z'（當 DB 儲存 UTC 時正確，現在會多加 8 小時）
const normalized = /[Zz]|[+-]\d{2}:?\d{2}$/.test(dateStr) ? dateStr : dateStr + '+08:00'
```

**轉換流程（修正後）：**

```
DB 回傳: "2026-03-17 08:40:27"（無時區後綴）
→ 補 '+08:00': "2026-03-17 08:40:27+08:00"（被解讀為 Taipei）
→ new Date(): Taipei 08:40:27
→ toLocaleString(Taipei): 08:40:27  ← 正確！
```

### 驗證

重新建置前端 Docker 映像：

```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

預期結果：TestResults 頁面的開始時間與結束時間與 DB 實際儲存值一致（Asia/Taipei）。

---

## 修改的檔案清單（完整）

| 檔案 | 修改說明 |
|------|----------|
| `backend/app/api/tests.py` | `create_test_session()` 建立 `TestSessionModel` 時補傳 `start_time=datetime.now(_TZ_TAIPEI)` |
| `frontend/src/views/TestResults.vue` | `formatDateTime()` 中 `dateStr + 'Z'` 改為 `dateStr + '+08:00'` |

## 問題關聯圖

```
2026-03-16 時區修正（issues/2026-03-16-datetime-timezone-utc-to-taipei.md）
    ├── ✅ test_engine.py: end_time → datetime.now(_TZ_TAIPEI)
    ├── ✅ measurements/base.py: test_time → datetime.now(_TZ_TAIPEI)
    ├── ✅ TestResultModel: test_time 補傳
    ├── ❌ 遺漏: api/tests.py create_test_session() start_time 未補傳
    │       └── → 2026-03-17 修正（本文件，後端部分）
    └── ❌ 前端 formatDateTime 仍補 'Z'（假設 DB 存 UTC）
            └── → 2026-03-17 修正（本文件，前端部分）
```
