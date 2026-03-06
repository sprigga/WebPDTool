# Code Review & Simplify — 2026-03-06

**日期**: 2026-03-06
**類型**: 程式碼審查 / 品質修正
**範圍**: backend/app/measurements/implementations.py, backend/app/api/users.py, frontend/src/views/TestMain.vue, frontend/src/views/UserManage.vue

---

## 問題 1: `[DEBUG]` 日誌在 INFO 層級輸出到生產環境

**發生位置**: `backend/app/measurements/implementations.py` 第 121-132、221-222、265-274 行

### 問題描述

`OtherMeasurement.execute()` 內有 8 個 `self.logger.info(f"[DEBUG] ...")` 呼叫，會在每次測試執行時以 INFO 層級輸出詳細的內部資料結構（例如 `test_plan_item` 的所有 key、`use_result` 的原始值與替換值等）。在生產環境中，每執行一個測試項目就會產生多行 INFO 日誌，造成日誌大量累積，並暴露內部資料結構細節。

### 修正方案

將所有 `self.logger.info(f"[DEBUG] ...")` 改為 `self.logger.debug(...)`（移除 `[DEBUG]` 前綴）。`DEBUG` 層級的日誌在生產環境中預設不輸出，可透過設定檔控制。

```python
# 修正前
self.logger.info(f"[DEBUG] test_plan_item keys: {list(self.test_plan_item.keys())}")

# 修正後
self.logger.debug(f"test_plan_item keys: {list(self.test_plan_item.keys())}")
```

---

## 問題 2: `script_path` 變數在 `except FileNotFoundError` 中可能未定義（NameError 風險）

**發生位置**: `backend/app/measurements/implementations.py` 第 285-289 行

### 問題描述

`OtherMeasurement.execute()` 的 `except FileNotFoundError` 例外處理區塊引用了 `script_path` 變數，但該變數僅在 `switch_mode != "script"` 的 `else` 分支中定義。當 `switch_mode == "script"` 路徑發生 `FileNotFoundError` 時，`script_path` 尚未賦值，導致例外處理本身拋出 `NameError`，將原始錯誤資訊覆蓋，造成難以追蹤的連鎖錯誤。

```python
# 修正前（NameError 風險）
except FileNotFoundError:
    return self.create_result(
        result="ERROR",
        error_message=f"Script not found: {script_path}"  # script_path 可能未定義
    )
```

### 修正方案

改用例外物件本身的訊息取代硬編碼的變數引用：

```python
# 修正後
except FileNotFoundError as e:
    return self.create_result(
        result="ERROR",
        error_message=f"Script not found: {e}"
    )
```

---

## 問題 3: `get_password_hash` 在函數內部 import（反模式）

**發生位置**: `backend/app/api/users.py` 第 161 行（原始）

### 問題描述

`change_user_password()` 函數內部有一行 `from app.core.security import get_password_hash`。雖然 Python 會快取已載入的模組，但在函數內 import 是反模式：隱藏了模組依賴關係、靜態分析工具無法在啟動時偵測 import 錯誤，且在每次呼叫時都需要進行 `sys.modules` 查找。

### 修正方案

將 import 移至檔案頂部的 import 區段：

```python
# 修正後（檔案頂部）
from app.core.security import get_password_hash
```

---

## 問題 4: `loading.value` 在 `fetchUsers` 拋出例外時永不重置

**發生位置**: `frontend/src/views/UserManage.vue` 第 537-539 行（原始）

### 問題描述

`handleSaveUser()` 的儲存流程中，`loading.value = true` 設定後直接 `await usersStore.fetchUsers()`，若 fetch 拋出例外，外層 `catch` 會捕捉錯誤，但 `loading.value` 沒有被重置，造成表格永久顯示載入狀態，使用者無法操作。

```javascript
// 修正前（loading 可能永久為 true）
showUserDialog.value = false
loading.value = true
await usersStore.fetchUsers()
loading.value = false
```

### 修正方案

將 fetch 包在獨立的 `try/finally` 中確保 `loading` 一定會被重置：

```javascript
// 修正後
showUserDialog.value = false
loading.value = true
try {
  await usersStore.fetchUsers()
} finally {
  loading.value = false
}
```

---

## 問題 5: `canEdit` 是 `isAdmin` 的無意義別名

**發生位置**: `frontend/src/views/UserManage.vue` 第 309 行（原始）

### 問題描述

`UserManage.vue` 定義了兩個計算屬性，其中 `canEdit` 完全等同於 `isAdmin`，沒有任何附加語意：

```javascript
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const canEdit = computed(() => isAdmin.value)  // 無意義的別名
```

這會誤導開發者認為 `canEdit` 可能有獨立條件（如功能開關或角色擴展），增加維護負擔。

### 修正方案

移除 `canEdit`，將模板中所有 7 處 `canEdit` 引用替換為 `isAdmin`：

```javascript
// 修正後（只保留 isAdmin）
const isAdmin = computed(() => currentUser.value?.role === 'admin')
```

---

## 問題 6: `[DEBUG]` console.log 在測試執行熱路徑大量輸出

**發生位置**: `frontend/src/views/TestMain.vue` 第 1044-1134 行（原始）

### 問題描述

`executeSingleItem()` 函數（測試執行核心迴圈）內有約 30 個 `console.log('[DEBUG] ...')` 呼叫，涵蓋：
- 每個測試項目的欄位清單（`Object.keys(item)`）
- `testParams` 建構過程的中間狀態
- `use_result`/`UseResult` 查找與替換的每一步

每個測試項目執行時輸出約 30 行日誌。若測試計畫有 100 個項目，單次執行即產生 3,000 行瀏覽器控制台輸出；迴圈模式（最多 9,999 次）下更高達數百萬行，嚴重影響瀏覽器效能並使真實錯誤難以找到。

### 修正方案

完全移除所有 `[DEBUG]` console.log 呼叫。邏輯本身（`use_result` 替換、`parameters` 合併）保持不變，僅移除日誌輸出。

---

## 審查中發現但未修正的架構議題

以下問題在審查中被識別，但因涉及架構層面，超出本次 simplify 的範圍，記錄供後續參考：

### A. 資料庫層使用同步 SQLAlchemy（非真正的 async）

CLAUDE.md 描述使用 `AsyncSession`，但實際上 `backend/app/core/database.py` 使用同步 `pymysql` 驅動與同步 `Session`。所有 18 個 API 路由模組（包括 `users.py`）都使用 `db: Session = Depends(get_db)`。雖然這在 `async def` 路由中會阻塞事件迴圈，但因為這是整個專案的既定架構，不在單一模組的修正範圍內。

### B. 導覽列 HTML 在三個視圖中重複

`UserManage.vue`、`ProjectManage.vue`、`TestPlanManage.vue` 都有完全相同的導覽列 HTML 區塊與 `handleLogout`/`navigateTo` 函數。建議提取為 `NavBar.vue` 元件。

### C. 整合測試使用同步 SQLite，無法驗證非同步程式碼路徑

`backend/tests/integration/test_user_management_flow.py` 使用同步 SQLite 引擎，而生產環境為 MySQL。測試無法覆蓋實際的資料庫連線行為。
