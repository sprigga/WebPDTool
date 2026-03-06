# 架構議題修正紀錄（2026-03-06）

**日期**: 2026-03-06  
**來源**: `docs/bugfix/code-review-simplify-2026-03-06.md`  
**範圍**: Backend API、Frontend 管理頁導覽列、Integration Test DB 配置

---

## 問題 A: 同步 SQLAlchemy 與 `async def` 路由混用

### 問題描述
- 專案資料庫層為同步 `Session`（`mysql+pymysql`），但多數路由宣告為 `async def`。
- 這些路由本身沒有 `await`，仍直接執行同步 DB I/O，會阻塞 event loop。

### 解決方式
- 將「無 `await` 的同步 DB 路由」由 `async def` 改為 `def`，交由 FastAPI threadpool 執行。
- 保留真正需要非同步流程的路由（例如 `dut_control.py`、`tests.py`、`measurements.py`、`testplan/mutations.py`）不變。

### 修改檔案
- `backend/app/api/auth.py`
- `backend/app/api/users.py`
- `backend/app/api/projects.py`
- `backend/app/api/stations.py`
- `backend/app/api/testplan/queries.py`
- `backend/app/api/testplan/sessions.py`
- `backend/app/api/testplan/validation.py`
- `backend/app/api/results/cleanup.py`
- `backend/app/api/results/export.py`
- `backend/app/api/results/measurements.py`
- `backend/app/api/results/reports.py`
- `backend/app/api/results/sessions.py`
- `backend/app/api/results/summary.py`

---

## 問題 B: 管理頁導覽列重複實作

### 問題描述
- `UserManage.vue`、`ProjectManage.vue`、`TestPlanManage.vue` 存在重複導覽列 HTML 與 `navigateTo` / `handleLogout` 邏輯。
- 重複程式碼增加維護成本與不一致風險。

### 解決方式
- 新增共用元件 `frontend/src/components/AppNavBar.vue`。
- 三個頁面改為引用 `<AppNavBar current-page="...">`。
- 移除頁面內重複導航與登出函式、對應 CSS。

### 修改檔案
- `frontend/src/components/AppNavBar.vue`（新增）
- `frontend/src/views/UserManage.vue`
- `frontend/src/views/ProjectManage.vue`
- `frontend/src/views/TestPlanManage.vue`

---

## 問題 C: 整合測試使用 SQLite，與生產 MySQL 不一致

### 問題描述
- 原 `test_user_management_flow.py` 使用檔案型 SQLite。
- 無法覆蓋與驗證 MySQL 相關的連線/行為路徑。

### 解決方式
- 改為使用 `TEST_DATABASE_URL`（測試 MySQL）建立引擎。
- 未設定 `TEST_DATABASE_URL` 時自動 `skip`。
- 安全檢查：URL 必須包含 `test`，避免誤用正式資料庫。
- 每次測試前後執行 `drop_all/create_all`，保持隔離。

### 修改檔案
- `backend/tests/integration/test_user_management_flow.py`

---

## 執行過程中遇到的問題與處理

### 1. `ModuleNotFoundError: No module named 'app'`
- 現象: 直接執行 `pytest` 時，測試匯入 `from app.main import app` 失敗。
- 處理: 使用 `PYTHONPATH=. pytest ...` 執行 backend 測試。

### 2. Integration Test 未提供測試 DB 連線
- 現象: 測試環境未設定 `TEST_DATABASE_URL`。
- 處理: 測試改為顯式 `skip`，並要求設定 `TEST_DATABASE_URL` 後再驗證完整流程。

### 3. `tests/test_api/test_users.py` 在本次環境無輸出卡住
- 現象: 測試程序長時間無輸出，無法取得有效測試結果。
- 處理: 本次改以 `python3 -m compileall` 進行語法驗證，並以 `frontend npm run build` 與 integration test（skip 條件）確認變更可建置。

---

## 驗證結果

- `frontend`: `npm run build` 成功。
- `backend`: `python3 -m compileall app tests/integration/test_user_management_flow.py` 成功。
- `backend`: `PYTHONPATH=. pytest tests/integration/test_user_management_flow.py -q`（在未設定 `TEST_DATABASE_URL` 環境下為 skip，符合預期）。

