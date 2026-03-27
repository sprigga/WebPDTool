---
title: measurement-results/sessions 端點 500 錯誤（ORM 欄位名稱不符）
date: 2026-03-27
component: backend/app/api/results/sessions.py
severity: medium
status: fixed
---

# Bug：`GET /api/measurement-results/sessions` 回傳 500 錯誤

## 問題描述

**重現步驟：**

1. 以有效 JWT Token 呼叫 `GET /api/measurement-results/sessions`
2. 後端回傳 HTTP 500，body 為：

```json
{
  "detail": "Failed to retrieve test sessions: type object 'TestSession' has no attribute 'started_at'"
}
```

**預期行為：** 回傳最近的測試 Session 列表（JSON 陣列）。

---

## 發現過程（Chrome DevTools MCP 驗證）

本次透過 Chrome DevTools MCP + Playwright MCP 對整個專案進行功能驗證，過程中直接在瀏覽器以 `fetch()` 呼叫後端 API，發現：

```
/api/results/sessions    → 404 Not Found
/api/results/analysis   → 404 Not Found
/api/projects           → 401 Unauthorized（正常，缺 token）
/api/auth/me            → 401 Unauthorized（正常，缺 token）
```

進一步確認路由後，發現 `sessions` 實際掛在 `/api/measurement-results/sessions`（非 `/api/results/sessions`）。以帶 token 的 curl 呼叫：

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9100/api/measurement-results/sessions?limit=2"
```

回傳 500，錯誤訊息指向 `TestSession.started_at` 不存在。

---

## 根本原因分析

`backend/app/api/results/sessions.py` 是一個舊版寫法，其中所有欄位名稱和關聯路徑都與實際 ORM Model 不符。以下為完整對照表：

### 欄位名稱不符

| sessions.py 使用的名稱 | 實際 ORM Model 欄位 | 說明 |
|---|---|---|
| `TestSessionModel.started_at` | `TestSessionModel.start_time` | `test_sessions` 表欄位 |
| `TestSessionModel.completed_at` | `TestSessionModel.end_time` | `test_sessions` 表欄位 |
| `TestSessionModel.status` | `TestSessionModel.final_result` | Enum: PASS/FAIL/ABORT |
| `TestSessionModel.project_id` | 不存在（透過 `StationModel.project_id`） | TestSession 無直接 project FK |
| `session.project.name` | `session.station.project.project_name` | 需先過 station 再到 project |
| `session.station.name` | `session.station.station_name` | 欄位名是 station_name |
| `session.operator_id` | `session.user_id`（int） | 無 operator_id 欄位 |
| `session.status` | `session.final_result.value` | Enum 需 .value 取字串 |
| `session.started_at` | `session.start_time` | — |
| `session.completed_at` | `session.end_time` | — |
| `TestResultModel.test_session_id` | `TestResultModel.session_id` | FK 欄位命名不同 |
| `r.min_limit` | `r.lower_limit` | TestResult 表欄位名稱 |
| `r.max_limit` | `r.upper_limit` | TestResult 表欄位名稱 |
| `r.created_at` | `r.test_time` | TestResult 無 created_at |
| `r.measured_value` 型別 `float` | 實際是 `str`（Text 欄位） | 允許多行文字輸出 |

### JOIN 順序錯誤

原始程式碼：
```python
stmt = select(TestSessionModel).join(ProjectModel).join(StationModel)
```

`TestSession` 沒有直接連到 `Project` 的 FK，正確的 FK 鏈是：
```
TestSession.station_id → Station.id
Station.project_id    → Project.id
```

修正後：
```python
stmt = select(TestSessionModel).join(StationModel).join(ProjectModel)
```

### 非同步懶加載問題（MissingGreenlet）

第一次修正後，呼叫端仍回傳 500：

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
can't call await_only() here.
```

**原因：** SQLAlchemy async 模式下，ORM 關聯屬性（`session.station`、`session.station.project`）預設為懶加載（lazy load）。在 `await db.execute()` 之後存取這些關聯時，已離開非同步 IO 上下文，會觸發 `MissingGreenlet` 錯誤。

**解法：** 在查詢時加上 `selectinload` 預先載入所需關聯：

```python
from sqlalchemy.orm import selectinload

stmt = (
    select(TestSessionModel)
    .join(StationModel)
    .join(ProjectModel)
    .options(
        selectinload(TestSessionModel.station)
        .selectinload(StationModel.project)
    )
)
```

---

## 修正內容（backend/app/api/results/sessions.py）

### 1. 加入必要 import

```python
from sqlalchemy.orm import selectinload
```

### 2. 修正 JOIN 順序 + 加入 selectinload

```python
# 修正前
stmt = select(TestSessionModel).join(ProjectModel).join(StationModel)

# 修正後
stmt = (
    select(TestSessionModel)
    .join(StationModel)
    .join(ProjectModel)
    .options(selectinload(TestSessionModel.station).selectinload(StationModel.project))
)
```

### 3. 修正 project_id 篩選條件

```python
# 修正前
stmt = stmt.where(TestSessionModel.project_id == project_id)

# 修正後（透過 Station）
stmt = stmt.where(StationModel.project_id == project_id)
```

### 4. 修正日期篩選和排序欄位

```python
# 修正前
stmt = stmt.where(TestSessionModel.started_at >= date_from)
stmt = stmt.where(TestSessionModel.started_at <= date_to)
stmt.order_by(desc(TestSessionModel.started_at))

# 修正後
stmt = stmt.where(TestSessionModel.start_time >= date_from)
stmt = stmt.where(TestSessionModel.start_time <= date_to)
stmt.order_by(desc(TestSessionModel.start_time))
```

### 5. 修正 status 篩選

```python
# 修正前
stmt = stmt.where(TestSessionModel.status == status)

# 修正後
stmt = stmt.where(TestSessionModel.final_result == status)
```

### 6. 修正 Response 建構（兩個端點）

```python
# 修正前
TestSessionResponse(
    project_name=session.project.name,
    station_name=session.station.name,
    operator_id=session.operator_id,
    status=session.status,
    started_at=session.started_at,
    completed_at=session.completed_at,
    ...
)

# 修正後
TestSessionResponse(
    project_name=session.station.project.project_name,
    station_name=session.station.station_name,
    operator_id=str(session.user_id) if session.user_id else None,
    status=str(session.final_result.value) if session.final_result else "UNKNOWN",
    started_at=session.start_time,
    completed_at=session.end_time,
    ...
)
```

### 7. 修正 TestResult 轉換

```python
# 修正前
MeasurementResultResponse(
    test_session_id=r.test_session_id,
    measured_value=r.measured_value,   # float
    min_limit=r.min_limit,
    max_limit=r.max_limit,
    created_at=r.created_at,
    ...
)

# 修正後
MeasurementResultResponse(
    test_session_id=r.session_id,
    measured_value=r.measured_value,   # str（Text 欄位）
    min_limit=r.lower_limit,
    max_limit=r.upper_limit,
    created_at=r.test_time,
    ...
)
```

### 8. 修正 TestResult 查詢篩選條件

```python
# 修正前（兩處）
TestResultModel.test_session_id == session.id
TestResultModel.test_session_id == session_id

# 修正後
TestResultModel.session_id == session.id
TestResultModel.session_id == session_id
```

### 9. 修正 Pydantic Response Model 中 measured_value 型別

```python
# 修正前
measured_value: float | None = None

# 修正後
measured_value: str | None = None
```

---

## 除錯流程

```
1. Chrome DevTools MCP 驗證發現 /api/results/sessions → 404
   ↓
2. 確認路由實際路徑為 /api/measurement-results/sessions（查 main.py）
   ↓
3. 用帶 token 的 curl 呼叫 → 500: "TestSession has no attribute 'started_at'"
   ↓
4. 閱讀 sessions.py，對照 test_session.py ORM Model → 欄位名稱全不符
   ↓
5. 第一輪修正（欄位名稱 + JOIN 順序）→ 重啟 backend → 500: MissingGreenlet
   ↓
6. 確認 SQLAlchemy async 懶加載限制 → 加入 selectinload → 修正
   ↓
7. curl 驗證：回傳正確 JSON，project/station 名稱正確，results 完整
   ↓
8. 驗證篩選條件：project_id=2 → 僅回傳 Demo Project 2 的 sessions ✅
```

---

## 驗證結果

```bash
# 測試 sessions 列表
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9100/api/measurement-results/sessions?limit=2"
# → HTTP 200，2 筆 session，project/station/status 欄位正確

# 測試單一 session
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9100/api/measurement-results/sessions/656"
# → HTTP 200，id=656, project=Demo Project 1, status=PASS, 5 筆 results

# 測試 project_id 篩選
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9100/api/measurement-results/sessions?project_id=2&limit=3"
# → HTTP 200，3 筆，全部 project_name=Demo Project 2 ✅
```

---

## 影響範圍說明

此端點（`/api/measurement-results/sessions`）目前**不被前端使用**。前端 TestResults.vue 的 Tab 1 使用的是 `/api/tests/sessions`（位於 `backend/app/api/tests.py`），該端點運作正常。

因此此 bug 不影響現有使用者介面，但修正後可確保 `measurement-results` 路由群組的完整性。
