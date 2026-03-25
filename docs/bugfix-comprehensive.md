# WebPDTool Bugfix 綜合文檔

## 概述

本文檔整合了 WebPDTool 專案從 2025-12-17 至 2026-03-25 期間的所有 bugfix 記錄。

**統計資訊：**
- 總修正數: 52+
- 時間範圍: 2025-12-17 ~ 2026-03-25
- 最後更新: 2026-03-25

---

## 按嚴重性分類

### 🔴 關鍵問題 (Critical)

影響系統核心功能或導致服務無法使用的問題。

#### Issue #1: 登入 API 返回 500 錯誤（bcrypt 密碼驗證）

**日期**: 2025-12-17 | **狀態**: ✅ 已修正

**症狀**: 使用者登入時 API 返回 500 錯誤

**根本原因**: bcrypt 密碼驗證失敗

**修正**: 修正密碼驗證邏輯

**影響**: `backend/app/api/auth.py`

---

#### Issue #7: 資料庫架構不匹配

**日期**: 2026-02-09 | **狀態**: ✅ 已修正

**症狀**: `test_plans` 表缺少欄位導致查詢失敗

**根本原因**: 資料庫 schema 與程式碼不同步

**修正**: 執行資料庫遷移

**影響**: `database/schema.sql`, `backend/alembic/`

---

#### asyncio.get_event_loop() 棄用（Python 3.10+）

**日期**: 2026-03-13 | **狀態**: ✅ 已修正

**症狀**: Python 3.10+ 環境出現 DeprecationWarning，Python 3.12 可能拋出 RuntimeError

**根本原因**: `asyncio.get_event_loop()` 在 Python 3.10 起被棄用

**修正**: 18 處全部替換為 `asyncio.get_running_loop()`

**影響**:
- `backend/app/services/instrument_connection.py` (9 處)
- `backend/app/services/instruments/comport_command.py` (9 處)

---

#### 無效型別標注 `str or List[str]`

**日期**: 2026-03-13 | **狀態**: ✅ 已修正

**症狀**: IDE 型別檢查器回報錯誤

**根本原因**: `str or List[str]` 是布林運算式，執行期返回 `str`，`List[str]` 被靜默丟棄

**修正**: 改為 `Union[str, List[str]]`

**影響**: `backend/app/services/instruments/console_command.py`

---

### 🟡 重要問題 (High)

影響主要功能但有暫時解決方案的問題。

#### Issue #5: 測量初始化簽章錯誤

**日期**: 2026-02-06 | **狀態**: ✅ 已修正

**症狀**: `BaseMeasurement.__init__()` 收到意外關鍵字參數 `item_no`

**根本原因**: 測量類別初始化簽章不匹配

**影響**: `backend/app/measurements/implementations.py`

---

#### Issue #6: Other 測量返回隨機值

**日期**: 2026-02-06 | **狀態**: ✅ 已修正

**症狀**: Other 測量類型返回隨機值而非執行腳本輸出

**根本原因**: 測量執行邏輯錯誤

**影響**: `backend/app/measurements/implementations.py`

---

#### Issue #8: wait_msec 參數未傳遞

**日期**: 2026-02-10 | **狀態**: ✅ 已修正

**症狀**: 前端設定的 wait_msec 參數後端收不到

**根本原因**: 動態參數表單值無法傳遞到測試執行 API

**修正**: 增加後端型別轉換邏輯（字串 → 數字）

**影響**:
- `frontend/src/views/TestMain.vue`
- `backend/app/measurements/implementations.py`

---

#### Issue #9: console/comport/tcpip 測量執行鏈錯誤

**日期**: 2026-02-24 | **狀態**: ✅ 已修正

**症狀**: 三種測量類型多重串聯錯誤

**根本原因**: 測量分派、儀器設定、參數傳遞、資料庫型別多重問題

**修正**:
- 修正 `executeSingleItem()` specialTypes 覆寫
- 修正 smcv100b.py SyntaxError
- 修正 `measurement_service.py` parameters key
- 新增虛擬儀器至 `_load_default_config()`
- 修正字串型 `measured_value` 丟棄 bug
- 修正前端非數值 `measured_value` DB 500 錯誤

**影響**:
- `frontend/src/views/TestMain.vue`
- `backend/app/services/measurement_service.py`
- `backend/app/measurements/implementations.py`

---

#### ComPortCommand 串列埠不存在

**日期**: 2026-03-12 | **狀態**: ✅ 已修正

**症狀**: 串列埠無法開啟時導致測試 ERROR

**根本原因**: `ComPortCommandDriver.initialize()` 在串列埠不存在時拋出 ConnectionError

**修正**: 改為進入 simulation mode，新增 `sim_response` 可配置回傳值

**影響**: `backend/app/services/instruments/comport_command.py`

---

#### use_result 機制完整修復

**日期**: 2025-02-10 | **狀態**: ✅ 已修正

**症狀**: `use_result` 機制無法正常工作，測試項目無法使用之前測試項目的結果

**根本原因**: 三層錯誤
1. 後端優先級錯誤（優先使用資料庫值而非前端替換值）
2. 前端大小寫不兼容（只檢查大寫 UseResult，資料庫是小寫 use_result）
3. 字典鍵值不匹配（用 item_no 存儲，用 item_name 查找）

**修正**:
1. 反轉後端優先級
2. 雙重大小寫支持
3. 雙鍵值存儲（同時用 item_no 和 item_name）
4. 整數格式保留（避免 "123" 變成 "123.0"）
5. 前端數值標準化（防禦性編程）

**影響**:
- `backend/app/measurements/implementations.py`
- `frontend/src/views/TestMain.vue`

---

#### lowsheen_lib 遷移 Phase 2 & Phase 3

**日期**: 2026-03-06 | **狀態**: ✅ 已修正

**症狀**: cleanup/reset 路徑未遷移

**根本原因**:
- `_cleanup_used_instruments()` 仍使用 subprocess `--final` 呼叫
- `reset_instrument()` 使用硬編碼 if/elif（僅 2 種儀器）
- fire-and-forget subprocess bug（create_subprocess_exec 結果從未 await）

**修正**:
- 替換為 `InstrumentExecutor.cleanup_instruments()`
- 替換為 `InstrumentExecutor.reset_instrument()`（支援所有 11 種）
- 修正 subprocess await

**影響**: `backend/app/services/lowsheen_lib_wrapper.py`

---

### 🟢 一般問題 (Medium)

影響部分功能但不阻礙主要工作流程的問題。

#### 循環導入問題

**狀態**: ✅ 已修正

**影響**: 模組間導入依賴

---

#### 動態參數表單不顯示

**狀態**: ✅ 已修正

**症狀**: 測試參數表單不顯示

**影響**: `frontend/src/views/TestMain.vue`

---

#### 動態參數表單模板不完整

**狀態**: ✅ 已修正

**症狀**: 部分測試項目的參數欄位缺失

**影響**: `frontend/src/views/TestMain.vue`

---

#### 腳本檔案找不到

**狀態**: ✅ 已修正

**症狀**: 測試腳本路徑解析錯誤

**影響**: `backend/app/measurements/implementations.py`

---

#### 測試時長精度損失

**日期**: 2026-03-06 | **狀態**: ✅ 已修正

**症狀**: 測試時長顯示為整數秒

**修正**: 移除 `Math.round()` 保留浮點秒數

**影響**: `frontend/src/views/TestResults.vue`

---

#### TestMain 導覽列缺少按鈕

**日期**: 2026-03-06 | **狀態**: ✅ 已修正

**症狀**: 測試結果查詢按鈕缺失

**修正**: 在按鈕組補上 `/results` 導覽按鈕

**影響**: `frontend/src/views/TestMain.vue`

---

#### 前端測試結果缺少欄位

**日期**: 2026-03-06 | **狀態**: ✅ 已修正

**影響**: `frontend/src/views/TestResults.vue`

---

#### 導覽列溢出

**日期**: 2026-03-10 | **狀態**: ✅ 已修正

**影響**: `frontend/src/views/TestMain.vue`

---

#### 報表分析視圖修復

**日期**: 2026-03-10 | **狀態**: ✅ 已修正

**影響**: `frontend/src/views/ReportAnalysis.vue`

---

#### OPjudge Web 彈窗修復

**日期**: 2026-03-16 | **狀態**: ✅ 已修正

**影響**: `frontend/src/components/OPjudgeModal.vue`

---

#### TestResults 對話框空 wall_time

**日期**: 2026-03-16 | **狀態**: ✅ 已修正

**影響**: `frontend/src/views/TestResults.vue`

---

#### Modbus Config 前端修復

**日期**: 2026-03-16 | **狀態**: ✅ 已修正

**影響**: `frontend/src/views/ModbusConfig.vue`

---

#### Modbus Config 響應驗證錯誤

**日期**: 2026-03-18 | **狀態**: ✅ 已修正

**症狀**: Modbus 配置 API 響應驗證失敗

**影響**:
- `backend/app/api/modbus.py`
- `frontend/src/views/ModbusConfig.vue`

---

#### Modbus Start/Stop 按鈕狀態

**日期**: 2026-03-25 | **狀態**: ✅ 已修正

**症狀**: Modbus Listener 啟動/停止按鈕狀態不正確

**影響**: `frontend/src/views/ModbusConfig.vue`

---

#### Modbus Auto-Trigger 地址和 testing flag

**日期**: 2026-03-25 | **狀態**: ✅ 已修正

**症狀**:
1. `_str2hex()` 地址轉換錯誤（400022 → 400034）
2. `_testing` flag 永久卡住導致 Auto-Trigger 停止

**根本原因**:
1. `_str2hex()` 將所有輸入用 `int(hex_str, 16)` 解析，但 DB 中地址是十進制格式
2. 前端 `write_result` 未送出（條件過嚴），後端無逾時保護

**修正**:
1. `_str2hex()` 改為判斷 `0x` 前綴，有前綴用十六進制，否則用十進制
2. 前端 `sn_received` 時設定 `modbusAutoMode=true`，放寬 `write_result` 條件
3. 後端新增 `_testing` 逾時自動清除（5 分鐘）

**影響**:
- `backend/app/services/modbus/modbus_listener.py`
- `frontend/src/views/TestMain.vue`

---

#### Modbus 即時 Connected 和 Cycle Count

**日期**: 2026-03-25 | **狀態**: ✅ 已修正

**症狀**: Live Status 區塊的 Connected 和 Cycle Count 欄位無法即時更新

**根本原因**: 後端無回調觸發點，前端無對應訊息處理器

**修正**:
1. 新增 `on_connected` 和 `on_cycle` callback
2. `connected` 改用邊緣觸發
3. 前端新增 `connected_change` 和 `cycle_update` 訊息處理器

**影響**:
- `backend/app/services/modbus/modbus_listener.py`
- `backend/app/services/modbus/modbus_manager.py`
- `backend/app/api/modbus_ws.py`
- `frontend/src/views/ModbusConfig.vue`

---

#### Test Session 時區錯誤（UTC vs Taipei）

**日期**: 2026-03-17 | **狀態**: ✅ 已修正

**症狀**: `start_time` 為 UTC 時間，`end_time` 為 Taipei 時間，相差 8 小時

**根本原因**: `create_test_session()` 未傳入 `start_time`，由 server_default 填入 UTC

**修正**: 傳入 `start_time=datetime.now(timezone.utc)` 確保一致性

**影響**:
- `backend/app/api/tests.py`
- `frontend/src/views/TestResults.vue`

---

#### 條碼序號未寫入資料庫

**日期**: 2026-03-11 | **狀態**: ✅ 已修正

**症狀**: 條碼掃描的序號未正確儲存

**影響**: `backend/app/api/tests.py`

---

#### 測量值字串類型

**日期**: 2026-03-11 | **狀態**: ✅ 已修正

**症狀**: 字串測量值觸發 DB DECIMAL 欄位 500 錯誤

**影響**:
- `backend/app/measurements/implementations.py`
- `frontend/src/views/TestMain.vue`

---

#### DB-backed Instrument Provider 未使用

**日期**: 2026-03-12 | **狀態**: ✅ 已修正

**症狀**: 儀器設定提供者未使用資料庫配置

**影響**: `backend/app/core/instrument_config.py`

---

#### Console Shell 元字元自動偵測

**狀態**: ✅ 已修正

**影響**: `backend/app/services/instruments/console_command.py`

---

### ⚙️ 環境配置問題

與開發環境或部署環境相關的問題。

#### Docker Desktop WSL2 資料庫連線

**狀態**: ✅ 已修正

**症狀**: Docker Desktop WSL2 環境無法連接資料庫

**影響**: `docker-compose.yml`

---

#### 資料庫遷移問題

**日期**: 2026-02-09 | **狀態**: ✅ 已修正

**影響**: `backend/alembic/`

---

#### Alembic 可用性驗證

**日期**: 2026-03-06 | **狀態**: ✅ 已修正

**症狀**: `alembic current/check` 在特定環境失敗

**根本原因**: 固定綁定 `host.docker.internal`

**修正**: 支援 `ALEMBIC_DATABASE_URL` / `DATABASE_URL` 覆寫

**影響**: `backend/alembic/env.py`

---

#### Alembic Migration Bind Parameter

**日期**: 2026-03-12 | **狀態**: ✅ 已修正

**影響**: `backend/alembic/versions/`

---

### 📝 資料驗證問題

與參數驗證或資料格式相關的問題。

#### 無效參數錯誤

**狀態**: ✅ 已修正

**症狀**: 測試執行時報錯 "Invalid parameters: []"

**影響**: `backend/app/api/tests.py`

---

#### 測試參數重複欄位

**狀態**: ✅ 已修正

**影響**: `backend/app/api/tests.py`

---

#### 測試值資料庫錯誤

**狀態**: ✅ 已修正

**影響**: `backend/app/models/test_results.py`

---

#### Script 模式執行

**狀態**: ✅ 已修正

**影響**: `backend/app/services/test_engine.py`

---

#### Switch 模式資料庫架構

**狀態**: ✅ 已修正

**影響**: `backend/app/models/`

---

#### use_result 參數優先級

**日期**: 2025-02-10 | **狀態**: ✅ 已修正

**症狀**: use_result 機制優先級錯誤

**影響**: `backend/app/measurements/implementations.py`

---

### 🔧 程式碼品質問題

#### 程式碼品質精簡（/simplify 審查）

**日期**: 2026-03-13 | **狀態**: ✅ 已修正

**問題**:
1. `asyncio.get_event_loop()` → `asyncio.get_running_loop()`（18 處）
2. 無效型別標注 `str or List[str]` → `Union[str, List[str]]`
3. 函式內部 `import os/sys` 移至模組頂層
4. 裸 `except:` → `except Exception:`
5. `_refresh_cache` DB 查詢移至 Lock 外部
6. Pinia Store 死碼移除

**影響**:
- `backend/app/services/instrument_connection.py`
- `backend/app/services/instruments/comport_command.py`
- `backend/app/services/instruments/console_command.py`
- `backend/app/core/instrument_config.py`
- `frontend/src/stores/instruments.js`

---

#### 架構議題修正

**日期**: 2026-03-06 | **狀態**: ✅ 已修正

**問題**:
1. 同步 SQLAlchemy + `async def` 路由混用
2. 管理頁導覽列重複
3. 整合測試 DB 不一致

**修正**:
1. 將無 `await` 路由改為同步 `def`
2. 抽取共用元件 `AppNavBar.vue`
3. 測試改用 `TEST_DATABASE_URL`

**影響**:
- `backend/app/api/`
- `frontend/src/views/`
- `tests/integration/`

---

#### 程式碼精簡

**日期**: 2026-03-17 | **狀態**: ✅ 已修正

**影響**: 多個前端和後端檔案

---

#### Code Review Simplify

**日期**: 2026-03-06 | **狀態**: ✅ 已修正

**影響**: 多個檔案

---

#### Bug 分析

**日期**: 2026-03-11 | **狀態**: ✅ 已修正

**影響**: 系統性問題分析

---

---

## 按時間軸查看

### 2026-03

| 日期 | 問題 | 嚴重性 |
|------|------|--------|
| 03-25 | Modbus Auto-Trigger 地址和 testing flag | 高 |
| 03-25 | Modbus 即時 Connected 和 Cycle Count | 一般 |
| 03-25 | Modbus Start/Stop 按鈕狀態 | 一般 |
| 03-18 | Modbus Config 響應驗證錯誤 | 一般 |
| 03-17 | Test Session 時區錯誤 | 一般 |
| 03-17 | 程式碼精簡 | 一般 |
| 03-16 | Modbus Config 前端修復 | 一般 |
| 03-16 | OPjudge Web 彈窗 | 一般 |
| 03-16 | TestResults 對話框空 wall_time | 一般 |
| 03-13 | 程式碼品質精簡 | 關鍵 |
| 03-12 | Alembic Migration Bind Parameter | 環境 |
| 03-12 | ComPortCommand 串列埠不存在 | 高 |
| 03-12 | DB-backed Instrument Provider 未使用 | 一般 |
| 03-11 | 條碼序號未寫入資料庫 | 一般 |
| 03-11 | 測量值字串類型 | 一般 |
| 03-11 | Bug 分析 | 一般 |
| 03-10 | 報表分析視圖修復 | 一般 |
| 03-10 | 導覽列溢出 | 一般 |
| 03-06 | lowsheen_lib 遷移 Phase 2 & Phase 3 | 高 |
| 03-06 | Alembic 可用性驗證 | 環境 |
| 03-06 | 測試時長精度損失 | 一般 |
| 03-06 | TestMain 導覽列缺少按鈕 | 一般 |
| 03-06 | 前端測試結果缺少欄位 | 一般 |
| 03-06 | 架構議題修正 | 一般 |
| 03-06 | Code Review Simplify | 一般 |

### 2026-02

| 日期 | 問題 | 嚴重性 |
|------|------|--------|
| 02-24 | Issue #9: console/comport/tcpip 測量執行鏈 | 高 |
| 02-10 | Issue #8: wait_msec 參數未傳遞 | 高 |
| 02-10 | 無效參數錯誤 | 驗證 |
| 02-10 | 測試參數重複欄位 | 驗證 |
| 02-10 | 測試值資料庫錯誤 | 驗證 |
| 02-10 | Script 模式執行 | 驗證 |
| 02-10 | Switch 模式資料庫架構 | 驗證 |
| 02-10 | use_result 參數優先級 | 驗證 |
| 02-09 | 資料庫遷移問題 | 環境 |
| 02-09 | Issue #7: 資料庫架構不匹配 | 關鍵 |
| 02-06 | Issue #5: 測量初始化簽章錯誤 | 高 |
| 02-06 | Issue #6: Other 測量返回隨機值 | 高 |

### 2025-12

| 日期 | 問題 | 嚴重性 |
|------|------|--------|
| 12-17 | Issue #1: 登入 API 500 錯誤 | 關鍵 |

---

## 按模組分類

### Backend

#### 測量層 (`measurements/`)
- Issue #5: 測量初始化簽章錯誤
- Issue #6: Other 測量返回隨機值
- Issue #8: wait_msec 參數未傳遞
- Issue #9: console/comport/tcpip 測量執行鏈
- use_result 機制完整修復
- 測量值字串類型
- Script 模式執行

#### Modbus (`services/modbus/`)
- Modbus Auto-Trigger 地址和 testing flag
- Modbus 即時 Connected 和 Cycle Count
- Modbus Start/Stop 按鈕狀態
- Modbus Config 前端修復
- Modbus Config 響應驗證錯誤

#### API (`api/`)
- Issue #1: 登入 API 500 錯誤
- 無效參數錯誤
- 測試參數重複欄位
- 測試值資料庫錯誤

#### 資料庫 (`models/`, `alembic/`)
- Issue #7: 資料庫架構不匹配
- 資料庫遷移問題
- Alembic 可用性驗證
- Alembic Migration Bind Parameter
- Switch 模式資料庫架構
- Test Session 時區錯誤

#### 儀器服務 (`services/instruments/`)
- ComPortCommand 串列埠不存在
- lowsheen_lib 遷移 Phase 2 & Phase 3
- DB-backed Instrument Provider 未使用
- asyncio.get_event_loop() 棄用（18 處）
- 無效型別標注
- Console Shell 元字元自動偵測

#### 核心服務 (`core/`)
- 程式碼品質精簡（Lock 內 DB 查詢）

#### 測試引擎 (`services/test_engine.py`)
- 架構議題修正

### Frontend

#### 測試執行 (`TestMain.vue`)
- Issue #8: wait_msec 參數未傳遞
- Issue #9: console/comport/tcpip 測量執行鏈
- use_result 機制完整修復
- 動態參數表單不顯示
- 動態參數表單模板不完整
- Modbus Auto-Trigger testing flag
- TestMain 導覽列缺少按鈕
- 導覽列溢出

#### 測試結果 (`TestResults.vue`)
- 前端測試結果缺少欄位
- Test Session 時區錯誤
- TestResults 對話框空 wall_time

#### Modbus 配置 (`ModbusConfig.vue`)
- Modbus Config 前端修復
- Modbus Start/Stop 按鈕狀態
- Modbus 即時 Connected 和 Cycle Count

#### 報表分析 (`ReportAnalysis.vue`)
- 報表分析視圖修復

#### 其他元件
- OPjudge Web 彈窗修復 (`OPjudgeModal.vue`)
- AppNavBar 抽取（架構議題修正）
- Pinia Store 死碼移除 (`instruments.js`)

### DevOps

#### Docker
- Docker Desktop WSL2 資料庫連線

#### 測試
- 架構議題修正（整合測試 DB）

---

## 快速查找索引

### A
- **asyncio.get_event_loop()**: 見「程式碼品質精簡」
- **Alembic**: 見「環境配置問題」

### B
- **bcrypt**: Issue #1
- **bugfix**: use_result 機制

### C
- **ComPortCommand**: 串列埠不存在
- **console**: 測量執行鏈、Shell 元字元
- **cycle_count**: Modbus 即時更新

### D
- **資料庫**: Issue #7、遷移問題、時區錯誤

### F
- **浮點數精度**: 測試時長、整數格式保留

### I
- **Issue #1-#9**: 見各 Issue 條目
- **import**: 函式內部 import

### L
- **lowsheen_lib**: Phase 2 & Phase 3 遷移

### M
- **Modbus**: Auto-Trigger、Connected、Cycle Count、Config、Start/Stop
- **measurement**: 初始化簽章、Other 測量、字串類型

### P
- **parameter**: wait_msec、use_result、無效參數、重複欄位
- **Pinia**: 死碼移除

### S
- **switch**: 模式資料庫架構
- **script**: 模式執行、檔案找不到

### T
- **test**: session 時區、results 欄位、duration 精度、dialog wall_time
- **timezone**: UTC vs Taipei
- **type**: 型別標注、字串/整數格式

### U
- **use_result**: 完整修復、優先級、大小寫、雙鍵存儲

### V
- **validation**: 參數驗證、Modbus Config 響應

### W
- **wait_msec**: Issue #8
- **WebSocket**: Modbus 即時更新
- **write_result**: Modbus Auto-Trigger

---

## 常見問題類型

### 1. 參數傳遞問題

**典型症狀:**
- 前端設定的參數後端收不到
- 參數驗證失敗但值看起來正確
- 測試執行時報錯 "Missing required parameter"

**相關問題:**
- Issue #8: wait_msec 參數未傳遞
- use_result 機制完整修復
- 無效參數錯誤
- 測試參數重複欄位

---

### 2. 測量執行問題

**典型症狀:**
- 測量類型返回錯誤結果
- 腳本無法執行
- 儀器初始化失敗

**相關問題:**
- Issue #5: 測量初始化簽章錯誤
- Issue #6: Other 測量返回隨機值
- Issue #9: console/comport/tcpip 測量執行鏈
- ComPortCommand 串列埠不存在
- 測量值字串類型

---

### 3. UI 元件問題

**典型症狀:**
- 表單不顯示
- 參數欄位缺失
- 選項清單為空
- 導覽按鈕缺失
- 按鈕狀態不正確

**相關問題:**
- 動態參數表單不顯示
- 動態參數表單模板不完整
- TestMain 導覽列缺少按鈕
- 導覽列溢出
- Modbus Start/Stop 按鈕狀態
- 前端測試結果缺少欄位

---

### 4. 環境配置問題

**典型症狀:**
- Docker 容器無法啟動
- 資料庫連線失敗
- 依賴套件衝突
- Alembic 操作失敗

**相關問題:**
- Docker Desktop WSL2 資料庫連線
- 資料庫遷移問題
- Alembic 可用性驗證
- Alembic Migration Bind Parameter

---

### 5. Modbus 相關問題

**典型症狀:**
- Auto-Trigger 無法持續運作
- 即時狀態未更新
- 按鈕狀態不同步
- 配置驗證失敗

**相關問題:**
- Modbus Auto-Trigger 地址和 testing flag
- Modbus 即時 Connected 和 Cycle Count
- Modbus Start/Stop 按鈕狀態
- Modbus Config 前端修復
- Modbus Config 響應驗證錯誤

---

## 文檔使用指南

### 遇到問題時

1. **搜尋關鍵字**: 使用錯誤訊息或症狀在本頁面搜尋
2. **查看分類**: 根據問題類型（嚴重性/模組/時間）找到相關分類
3. **追蹤關聯問題**: 許多問題有相關性，一併檢查可完整解決

### 記錄新問題時

建議在 git commit 中記錄，然後定期更新本文檔：

1. 添加到對應的嚴重性分類
2. 添加到時間軸
3. 添加到模組分類
4. 更新統計資訊
5. 更新快速查找索引

---

**最後更新**: 2026-03-25

**原始文檔目錄**: `docs/bugfix/` (已刪除，整合至此文件)
