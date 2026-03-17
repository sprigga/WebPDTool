# Code Simplify Review — 2026-03-17

本文件記錄 `/simplify` 指令對 v0.7.0 變更集的審查結果與修正過程。
涵蓋時區統一、wall_time_ms、批量刪除等功能的後續精簡。

---

## 問題一：`cleanup.py` 存在重複的批量刪除 endpoint

**檔案:** `backend/app/api/results/cleanup.py`
**類型:** 邏輯重複

### 問題描述

`cleanup.py`（掛載於 `/api/measurement-results/sessions`）與 `tests.py`（掛載於 `/api/tests/sessions`）
各自定義了完全相同的批量刪除邏輯與 Pydantic 請求模型：

```python
# cleanup.py (已移除)
class BulkDeleteRequest(BaseModel):
    session_ids: List[int]

@router.delete("/sessions")
async def bulk_delete_test_sessions(body: BulkDeleteRequest, ...):
    # 與 tests.py 完全相同的邏輯
```

前端呼叫的是 `DELETE /api/tests/sessions`（`tests.py` 版本），
`cleanup.py` 的版本從未被呼叫，屬於死碼。

### 修正方式

移除 `cleanup.py` 中的重複 endpoint 及 `BulkDeleteRequest` 類別，
同時移除不再需要的 `from typing import List` 與 `from pydantic import BaseModel` import。

```diff
- from typing import List
- from pydantic import BaseModel
-
- class BulkDeleteRequest(BaseModel):
-     session_ids: List[int]
-
- @router.delete("/sessions")
- async def bulk_delete_test_sessions(...):
-     ...（52 行刪除）
```

---

## 問題二：`cleanup.py` 的 `cleanup_old_results` 使用不存在的欄位 `started_at`

**檔案:** `backend/app/api/results/cleanup.py` line ~166
**類型:** Runtime Bug（AttributeError）

### 問題描述

`cleanup_old_results` 函式在查詢舊 Session 時使用了不存在的欄位名稱：

```python
# 錯誤：TestSession 模型無 started_at 欄位
select(TestSessionModel).where(TestSessionModel.started_at < cutoff_date)

# dry_run 回傳中也使用了 s.started_at
"started_at": s.started_at.isoformat()
```

實際 ORM 欄位為 `start_time`，呼叫此 endpoint 會在 `WHERE` 子句生成時拋出 `AttributeError`。

### 修正方式

```diff
- select(TestSessionModel).where(TestSessionModel.started_at < cutoff_date)
+ select(TestSessionModel).where(TestSessionModel.start_time < cutoff_date)

- "started_at": s.started_at.isoformat()
+ "start_time": s.start_time.isoformat() if s.start_time else None
```

---

## 問題三：`cleanup_old_results` N×1 迴圈刪除效能問題

**檔案:** `backend/app/api/results/cleanup.py` line ~190
**類型:** 效能問題（N+1 DB 查詢）

### 問題描述

原始刪除邏輯對每個 session 發出兩次 DB 操作（共 2×N 次 round-trip）：

```python
# 原始程式碼（N×1）
for session in old_sessions:
    await db.execute(
        sa_delete(TestResultModel).where(TestResultModel.session_id == session.id)
    )
    await db.delete(session)
    deleted_count += 1
await db.commit()
```

若清理 100 個 session，需要 200 次 DB 呼叫。

### 修正方式

使用 `.in_()` 批量刪除，無論清理多少個 session 都只需 2 次 DB 查詢：

```python
# 修改後（固定 2 次查詢）
old_ids = [s.id for s in old_sessions]
if old_ids:
    await db.execute(
        sa_delete(TestResultModel).where(TestResultModel.session_id.in_(old_ids))
    )
    await db.execute(
        sa_delete(TestSessionModel).where(TestSessionModel.id.in_(old_ids))
    )
await db.commit()
```

此模式與同檔案的 `bulk_delete_test_sessions` 一致。

---

## 問題四：`base.py` 每次建立 `MeasurementResult` 都呼叫 `ZoneInfo("Asia/Taipei")`

**檔案:** `backend/app/measurements/base.py` line ~151
**類型:** 熱路徑效能問題

### 問題描述

`MeasurementResult.__init__` 每次初始化都直接呼叫 `ZoneInfo("Asia/Taipei")`：

```python
self.test_time = datetime.now(ZoneInfo("Asia/Taipei"))
```

`ZoneInfo()` 會進行 IANA timezone database 查詢。
測試執行時，每個測試項目建立一個 `MeasurementResult`，此呼叫出現在熱路徑上。

`tests.py` 與 `test_engine.py` 已有模組層級常數 `_TZ_TAIPEI` 的最佳實踐範例。

### 修正方式

在 `base.py` 模組層級加入常數，並在 `__init__` 中引用：

```python
# 新增（模組層級，import 之後）
_TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# 修改（MeasurementResult.__init__）
self.test_time = datetime.now(_TZ_TAIPEI)  # 原: ZoneInfo("Asia/Taipei")
```

---

## 問題五：`test_engine.py` 中 `datetime.now(_TZ_TAIPEI)` 重複呼叫

**檔案:** `backend/app/services/test_engine.py` line ~449
**類型:** 冗餘計算 + 輕微時序偏差

### 問題描述

`_finalize_test_session` 中的 if/else 兩個分支各自呼叫一次 `datetime.now()`：

```python
if test_state.start_time:
    _now = datetime.now(_TZ_TAIPEI)  # 第一次
    duration_seconds = round((_now - test_state.start_time).total_seconds(), 6)
else:
    _now = datetime.now(_TZ_TAIPEI)  # 第二次（兩次呼叫間有時間差）
    duration_seconds = 0

session.end_time = _now
```

else 分支的 `_now` 與 if 分支的 `_now` 不同時間點建立，
會造成 `end_time` 的輕微偏差（微秒級，但語義不一致）。

### 修正方式

將呼叫提升到 if/else 之前：

```python
_now = datetime.now(_TZ_TAIPEI)  # 單一時間點
if test_state.start_time:
    # 修改(2026-03-16): 改用 Asia/Taipei，兩端需同為 aware datetime 才能相減
    # duration_seconds = round((datetime.utcnow() - test_state.start_time).total_seconds(), 6)
    duration_seconds = round((_now - test_state.start_time).total_seconds(), 6)
else:
    duration_seconds = 0
session.end_time = _now
```

---

## 問題六：`wall_time_ms` 的採樣點說明不正確

**檔案:** `frontend/src/views/TestMain.vue` line ~892
**類型:** 文件錯誤（誤導性注釋）

### 問題描述

`wallTimeMs` 的採樣點在 `createTestResult` 呼叫之前，
因此實際上不包含 DB 寫入時間，但注釋寫：

```javascript
// wall_time 包含: 量測執行 + 網路傳輸 + DB 寫入  ← 錯誤
const wallTimeMs = Date.now() - itemWallStart
item.wall_time_ms = wallTimeMs
try {
  await createTestResult(...)  // DB 寫入在這裡，不在 wallTimeMs 內
```

### 修正方式

更正注釋以反映實際行為：

```diff
- // wall_time 包含: 量測執行 + 網路傳輸 + DB 寫入
+ // wall_time 包含: 量測執行 + 網路傳輸（不含 DB 寫入，DB 寫入在 createTestResult 後）
```

> **補充說明：** 若需要包含 DB 寫入時間，需在 `createTestResult` 的 `await` 解析後再計算 `wallTimeMs`，
> 但這樣就無法將值傳入 `createTestResult` 本身，需要後續 PATCH 操作，屬架構性改動。
> 目前語意為「從測試開始到測量 API 回傳」的時間，足以診斷 backend 效能瓶頸。

---

## 問題七：CSV export 中 `list(results)` 重複呼叫

**檔案:** `backend/app/api/tests.py` line ~265
**類型:** 無謂的記憶體分配

### 問題描述

```python
results = result.scalars().all()  # 已回傳 Python list

if results and list(results)[0].test_plan_id:   # 多餘的 list()
    first_result = list(results)[0]              # 再次多餘的 list()
```

`.all()` 已回傳 `list`，再包一層 `list()` 會建立新的 list 物件，毫無必要。

### 修正方式

```diff
- if results and list(results)[0].test_plan_id:
-     first_result = list(results)[0]
+ if results and results[0].test_plan_id:
+     first_result = results[0]
```

---

## 問題八：`tests.py` import 順序混亂（類別定義插入 import 區塊中間）

**檔案:** `backend/app/api/tests.py` 前 20 行
**類型:** 程式碼可讀性問題

### 問題描述

`BulkDeleteSessionsRequest` 類別被定義在 import 語句之間：

```python
from pydantic import BaseModel

class BulkDeleteSessionsRequest(BaseModel):   # ← 類別插在 import 中間
    session_ids: List[int]
from datetime import datetime                  # ← import 繼續
```

### 修正方式

重排 import 順序，將所有 import 置於上方，類別定義置於 import 區塊之後：

```python
# stdlib imports
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
from typing import List, Optional

# third-party imports
from fastapi import ...
from sqlalchemy import ...
from pydantic import BaseModel

# 模組層級常數
_TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# 專案 imports
from app.core.database import get_async_db
...

# Module-level logger
logger = logging.getLogger(__name__)

# 請求模型（所有 import 完成後才定義）
class BulkDeleteSessionsRequest(BaseModel):
    session_ids: List[int]
```

---

## 修改檔案總覽

| 檔案 | 問題 | 修改類型 |
|------|------|---------|
| `backend/app/api/results/cleanup.py` | 重複 endpoint、不存在欄位 `started_at`、N×1 迴圈 | Bug Fix + 效能優化 |
| `backend/app/measurements/base.py` | 熱路徑 `ZoneInfo()` 呼叫 | 效能優化 |
| `backend/app/services/test_engine.py` | 重複 `datetime.now()` 呼叫 | 冗餘消除 |
| `frontend/src/views/TestMain.vue` | `wall_time_ms` 注釋說明錯誤 | 文件修正 |
| `backend/app/api/tests.py` | `list(results)` 重複、import 順序 | 程式碼品質 |

---

## 除錯過程

1. 執行 `/simplify` 指令，三個 review agent 並行審查：
   - **Agent 1（Code Reuse）**：找到重複的 `DELETE /sessions` endpoint 和 `_TZ_TAIPEI` 常數散落多處
   - **Agent 2（Code Quality）**：找到 `started_at` 不存在欄位（Runtime AttributeError）、`wall_time_ms` 注釋錯誤、`import` 順序問題
   - **Agent 3（Efficiency）**：找到 N×1 迴圈、`ZoneInfo()` 熱路徑呼叫、`list(results)` 重複建立

2. 確認 `frontend` 呼叫的是 `DELETE /api/tests/sessions`（`tests.py` 版本），
   因此 `cleanup.py` 的版本為死碼，安全移除。

3. `started_at` 欄位 bug 屬於重構時的 typo，模型實際欄位為 `start_time`，
   不影響目前使用（`cleanup_old_results` 尚未被呼叫），但會在呼叫時造成 `AttributeError`。

4. N×1 迴圈改用 `bulk .in_()` 後，程式碼模式與同檔案的 `bulk_delete_test_sessions` 一致，
   降低了維護負擔。
