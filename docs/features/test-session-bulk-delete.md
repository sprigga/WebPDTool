# 測試記錄批次刪除功能

## 功能概述

在 `TestResults.vue` 頁面新增批次刪除測試記錄功能，限定 **admin** 角色才能使用。
刪除一筆 Session 同時刪除關聯的 `test_results` 資料，確保資料完整性。

---

## 實作範圍

| 層次 | 檔案 | 變更內容 |
|------|------|---------|
| Backend | `backend/app/api/tests.py` | 新增 `DELETE /api/tests/sessions` 端點 |
| Backend | `backend/app/api/results/cleanup.py` | 修正既有錯誤欄位名稱 |
| Frontend API | `frontend/src/api/testResults.js` | 新增 `deleteTestSessions()` |
| Frontend View | `frontend/src/views/TestResults.vue` | 勾選欄、刪除按鈕、確認對話框 |

---

## 後端實作

### 新端點：`DELETE /api/tests/sessions`

位於 `backend/app/api/tests.py`，router prefix 為 `/api/tests`。

```python
class BulkDeleteSessionsRequest(BaseModel):
    session_ids: List[int]

@router.delete("/sessions")
async def bulk_delete_test_sessions(
    body: BulkDeleteSessionsRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    PermissionChecker.check_admin(current_user, "bulk delete test sessions")
    # 1. 先刪除 test_results（外鍵）
    await db.execute(sa_delete(TestResultModel).where(TestResultModel.session_id.in_(found_ids)))
    # 2. 再刪除 test_sessions
    await db.execute(sa_delete(TestSessionModel).where(TestSessionModel.id.in_(found_ids)))
    await db.commit()
```

**設計決策：**
- 使用 `PermissionChecker.check_admin()` 而非 `check_admin_or_engineer()`，因為批次刪除為破壞性操作。
- 先查詢確認 session 存在再刪除，回傳實際刪除的 ID 清單。
- 外鍵刪除順序：`test_results` → `test_sessions`（雖然 schema 已設 `ondelete="CASCADE"`，明確刪除更安全）。

**新增的 import：**
```python
from sqlalchemy import delete as sa_delete
from pydantic import BaseModel
from app.core.api_helpers import PermissionChecker
```

---

## 前端實作

### API 函式 (`testResults.js`)

```js
export const deleteTestSessions = (sessionIds) => {
  return apiClient.delete('/api/tests/sessions', { data: { session_ids: sessionIds } })
}
```

> **注意：** Axios 的 `delete` 方法傳 body 需用 `{ data: {...} }` 而非第二個位置參數。

### TestResults.vue 變更

**1. 新增 import：**
```js
import { ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { deleteTestSessions } from '@/api/testResults'
```

**2. 響應式狀態：**
```js
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')
const selectedSessions = ref([])
const deleting = ref(false)
```

**3. el-table 勾選欄（僅 admin 顯示）：**
```html
<el-table @selection-change="handleSelectionChange">
  <el-table-column v-if="isAdmin" type="selection" width="50" />
  ...
</el-table>
```

**4. 刪除按鈕（僅 admin 顯示）：**
```html
<el-button
  v-if="isAdmin"
  type="danger"
  :icon="Delete"
  :disabled="selectedSessions.length === 0"
  :loading="deleting"
  @click="handleBulkDelete"
>
  刪除選取 ({{ selectedSessions.length }})
</el-button>
```

**5. 處理函式：**
```js
const handleSelectionChange = (rows) => {
  selectedSessions.value = rows
}

const handleBulkDelete = async () => {
  await ElMessageBox.confirm(
    `確定要刪除選取的 ${selectedSessions.value.length} 筆測試記錄及其所有測試結果？此操作無法復原。`,
    '刪除確認',
    { type: 'warning', confirmButtonText: '確定刪除', cancelButtonText: '取消' }
  )
  const ids = selectedSessions.value.map((s) => s.id)
  await deleteTestSessions(ids)
  await loadSessions()
}
```

---

## 除錯過程

### 症狀

部署後測試，後端回傳 HTTP 500：

```
INFO: 172.18.0.5:53000 - "DELETE /api/tests/sessions HTTP/1.1" 500 Internal Server Error
```

### 排查步驟

**1. 確認日誌無詳細錯誤**

`docker-compose logs backend` 只顯示 HTTP 狀態行，沒有 traceback。FastAPI 預設將 500 錯誤吞掉，只記錄請求行。

**2. 用 curl 直接呼叫端點**

取得有效 token 後，用真實 session ID 測試：

```bash
TOKEN=$(curl -s -X POST http://localhost:9100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X DELETE http://localhost:9100/api/tests/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_ids": [221]}'
```

**回應揭露根本原因：**
```json
{"detail":"Failed to bulk delete sessions: type object 'TestResult' has no attribute 'test_session_id'"}
```

**3. 根本原因**

`TestResult` 模型的欄位是 `session_id`，不是 `test_session_id`：

```python
# backend/app/models/test_result.py
session_id = Column(Integer, ForeignKey("test_sessions.id", ondelete="CASCADE"), ...)
```

程式碼誤寫為 `TestResultModel.test_session_id`，在 SQLAlchemy 存取 Column attribute 時引發 `AttributeError`。

**4. 修正**

```python
# 錯誤（原始）
sa_delete(TestResultModel).where(TestResultModel.test_session_id.in_(found_ids))

# 正確（修正後）
sa_delete(TestResultModel).where(TestResultModel.session_id.in_(found_ids))
```

同時發現 `cleanup.py` 中既有的單筆刪除端點也有相同錯誤，一併修正（共 3 處 `replace_all`）。

**5. 驗證**

重建容器後再次測試：
```json
{"message":"Deleted 1 session(s) and associated results","deleted_session_ids":[221]}
```

---

## 權限控制邏輯

| 角色 | 勾選欄 | 刪除按鈕 | API 端點 |
|------|--------|---------|---------|
| admin | 顯示 | 顯示 | 允許 |
| engineer | 隱藏 | 隱藏 | 403 Forbidden |
| operator | 隱藏 | 隱藏 | 403 Forbidden |

前端以 `authStore.user?.role === 'admin'` 判斷（從 JWT login 回應儲存於 localStorage），後端以 `PermissionChecker.check_admin()` 二次驗證。

---

## 附帶修正

`backend/app/api/results/cleanup.py` 中既有的刪除端點（`DELETE /sessions/{session_id}` 及 `/cleanup`）使用了相同的錯誤欄位名稱 `test_session_id`，在此次修正中一併更正為 `session_id`。這些端點之前若被呼叫到刪除步驟，同樣會 500。
