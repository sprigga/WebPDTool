# Issue #9: console/comport/tcpip 測量類型執行鏈修正

**錯誤日期**: 2026-02-24
**錯誤類型**: 多重串聯錯誤（測量分派、儀器設定、參數傳遞、資料庫型別）
**發生位置**: TestMain.vue → MeasurementService → BaseMeasurement → DB

---

## 問題描述

將 `console`/`comport`/`tcpip` 新增為前端測試類型後，執行 `echo_test`（`test_type=console`）時出現連續多個錯誤，導致測試無法執行。

---

## 錯誤 1: "Script not found: /app/./scripts/console.py"

### 根本原因

`frontend/src/views/TestMain.vue` 的 `executeSingleItem()` 中，`specialTypes` 陣列攔截了 `switchMode` 判斷，導致 `measurementType` 被覆寫為 `'Other'`（腳本執行器），而非直接使用 `ConSoleMeasurement`。

```javascript
// 原問題：specialTypes 包含 'console'，導致走 OtherMeasurement 路徑
const specialTypes = ['comport', 'console', 'tcpip', ...]
if (switchMode && specialTypes.includes(switchMode.toLowerCase())) {
  measurementType = 'Other'   // ← 錯誤：應該是 ConSoleMeasurement
}
```

### 修正方案

新增 `directMeasurementTypes` 守衛，當 `test_type` 本身就是直接測量類別時，跳過 `specialTypes` 覆寫：

```javascript
// frontend/src/views/TestMain.vue
const directMeasurementTypes = ['console', 'comport', 'tcpip']
if (switchMode && specialTypes.includes(switchMode.toLowerCase()) &&
    !directMeasurementTypes.includes(item.test_type?.toLowerCase())) {
  measurementType = 'Other'
  finalSwitchMode = switchMode.toLowerCase()
}
```

**修改檔案**: `frontend/src/views/TestMain.vue`（`executeSingleItem()` 函式）

---

## 錯誤 2: "unindent does not match any outer indentation level (smcv100b.py, line 174)"

### 根本原因

`backend/app/services/instruments/smcv100b.py` 第 170-172 行存在預存在的縮排錯誤（`else` 區塊內命令縮排了 20 個空格，應為 16 個）。後端 import 時即發生 `SyntaxError`，導致整個 instruments 模組載入失敗。

### 修正方案

修正 `else` 區塊中 SCPI 命令的縮排（從 20 空格改為 16 空格）：

```python
# 修正前（20 空格縮排，BUG）：
        else:
            # SCPI fallback
                await self.write_command(...)

# 修正後（16 空格縮排，CORRECT）：
        else:
            # SCPI fallback
            await self.write_command(...)
```

**修改檔案**: `backend/app/services/instruments/smcv100b.py`（第 170-172 行）

---

## 錯誤 3: "Missing required parameter: Instrument"

### 根本原因

`BaseMeasurement.__init__` 透過 `test_plan_item.get("parameters", {})` 取得 `self.test_params`。但 `measurement_service.py` 建構 `test_plan_item` 時，只將 `test_params` 展開為頂層 key，**未設定** `"parameters"` 這個 key，導致 `self.test_params = {}`，所有 `required` 參數（Instrument、Command）均查無值。

```python
# 原問題（measurement_service.py）：
test_plan_item = {
    **test_params,        # 展開，但沒有 "parameters" key
    "switch_mode": ...,
}
# BaseMeasurement.__init__：self.test_params = test_plan_item.get("parameters", {}) → {}
```

### 修正方案

在 `test_plan_item` dict 中明確設定 `"parameters"` key：

```python
# backend/app/services/measurement_service.py
test_plan_item = {
    **test_params,
    "parameters": test_params,   # ← 新增，讓 BaseMeasurement 能讀到參數
    "switch_mode": switch_mode,
    "measurement_type": measurement_type,
    "item_no": 0,
    "item_name": test_point_id,
}
```

**修改檔案**: `backend/app/services/measurement_service.py`

---

## 錯誤 4: "Instrument 'console_1' not configured"

### 根本原因

`InstrumentSettings._load_default_config()` 未包含 `console_1`/`comport_1`/`tcpip_1` 虛擬儀器設定，也未在 `INSTRUMENT_DRIVERS` 中登錄對應驅動。

### 修正方案

#### 4a. 新增虛擬儀器設定

```python
# backend/app/core/instrument_config.py → _load_default_config()
"console_1": InstrumentConfig(
    id="console_1", type="console", name="Console Command (default)",
    connection=InstrumentAddress(type="LOCAL", address="local://console"),
    enabled=True,
    description="Virtual instrument for OS subprocess command execution"
),
"comport_1": InstrumentConfig(
    id="comport_1", type="comport", name="COM Port Command (default)",
    connection=InstrumentAddress(type="LOCAL", address="local://comport"),
    enabled=True,
    description="Virtual instrument for serial port command execution"
),
"tcpip_1": InstrumentConfig(
    id="tcpip_1", type="tcpip", name="TCP/IP Command (default)",
    connection=InstrumentAddress(type="LOCAL", address="local://tcpip"),
    enabled=True,
    description="Virtual instrument for TCP/IP socket command execution"
),
```

#### 4b. 登錄驅動至 INSTRUMENT_DRIVERS

```python
# backend/app/services/instruments/__init__.py
from app.services.instruments.console_command import ConSoleCommandDriver
from app.services.instruments.comport_command import ComPortCommandDriver
from app.services.instruments.tcpip_command import TCPIPCommandDriver

INSTRUMENT_DRIVERS = {
    ...
    "console": ConSoleCommandDriver,
    "comport": ComPortCommandDriver,
    "tcpip": TCPIPCommandDriver,
}
```

**修改檔案**:
- `backend/app/core/instrument_config.py`
- `backend/app/services/instruments/__init__.py`

---

## 錯誤 5: "pyvisa not installed"

### 根本原因

前一步驟的虛擬儀器 `console_1` 使用 `VISAAddress`，`create_connection()` 工廠函式會嘗試建立 VISA 連線 → 需要 `pyvisa` 套件。虛擬儀器不需要實體連線。

### 修正方案

改用 `InstrumentAddress(type="LOCAL", ...)` — `create_connection()` 的 `else` 分支會回傳 `SimulationInstrumentConnection`（no-op），不需要任何套件：

```python
# 修正前（嘗試建立 VISA 連線）：
connection=VISAAddress(address="TCPIP0::...")

# 修正後（使用本地虛擬連線）：
connection=InstrumentAddress(type="LOCAL", address="local://console")
```

**修改檔案**: `backend/app/core/instrument_config.py`

---

## 錯誤 6: ConSoleMeasurement 丟棄字串型 measured_value

### 根本原因

`ConSoleMeasurement`（以及 `ComPortMeasurement`、`TCPIPMeasurement`）將 `response_str` 賦值給 `measured_value` 後，又透過以下判斷將其設為 `None`：

```python
# 原問題（implementations.py）：
measured_value = response_str
if self.value_type is not StringType:
    try: measured_value = Decimal(response_str)
    except: measured_value = None
if isinstance(measured_value, str):
    measured_value = None   # ← 強制丟棄字串
```

結果字串類型的測量值永遠為 `None`，validate_result 收到 `None` 而非實際回應。

### 修正方案

依 `value_type` 分路處理；validate 永遠傳入原始字串 `response_str`：

```python
# 修正後（三個 Measurement 類別都相同）：
if self.value_type is StringType:
    measured_value = response_str          # 保留字串供 UI 顯示
else:
    try:
        measured_value = Decimal(response_str.strip())
    except Exception:
        measured_value = None

is_valid, error_msg = self.validate_result(response_str)  # 永遠驗證原始字串
```

**修改檔案**: `backend/app/measurements/implementations.py`（`ConSoleMeasurement`、`ComPortMeasurement`、`TCPIPMeasurement`）

---

## 錯誤 7: "保存測試結果失敗 - HTTP 500 / Incorrect decimal value"

### 根本原因

資料庫 `test_results.measured_value` 欄位型別為 `DECIMAL(15,6)`，無法儲存字串（如 `'hello'`）。前端 `createTestResult()` 原本將所有 `measured_value` 都轉為字串後傳送，導致 MySQL 拒絕非數值字串。

### 修正方案

在前端判斷 `measured_value` 是否為數值，非數值字串則傳 `null`：

```javascript
// frontend/src/views/TestMain.vue → createTestResult()
// 修正前：
const measuredValueStr = response.measured_value !== null
  ? String(response.measured_value) : null

// 修正後：
const rawValue = response.measured_value
let measuredValueStr = null
if (rawValue !== null && rawValue !== undefined) {
  const asNum = Number(rawValue)
  measuredValueStr = (!isNaN(asNum) && rawValue !== '') ? String(rawValue) : null
}
```

**說明**: 字串型測量結果（如指令回應文字）不儲存至 `measured_value`（DB 欄位），UI 顯示仍透過 API 回傳的 `response_text` 欄位處理。

**修改檔案**: `frontend/src/views/TestMain.vue`（`createTestResult()` 函式）

---

## 同步新增：前端測試類型選單

作為此次修正的前提，在 `backend/app/config/instruments.py` 的 `MEASUREMENT_TEMPLATES` 中新增 `comport`/`console`/`tcpip` 三個頂層測試類型，讓 `TestPlanManage.vue` 的「測試類型」下拉選單自動顯示新選項：

```python
"comport": {
    "comport": {
        "required": ["Instrument", "Command"],
        "optional": ["Timeout", "ReslineCount", "ComportWait", "SettlingTime"],
        "example": {"Instrument": "comport_1", "Command": "AT+VERSION\\n", ...}
    }
},
"console": {
    "console": {
        "required": ["Instrument", "Command"],
        "optional": ["Timeout", "Shell", "WorkingDir"],
        "example": {"Instrument": "console_1", "Command": "echo hello", ...}
    }
},
"tcpip": {
    "tcpip": {
        "required": ["Instrument", "Command"],
        "optional": ["Timeout", "UseCRC32", "BufferSize"],
        "example": {"Instrument": "tcpip_1", "Command": "31;01;f0;00;00", ...}
    }
},
```

---

## 修改的檔案彙整

| 檔案 | 修改內容 |
|------|---------|
| `frontend/src/views/TestMain.vue` | 新增 `directMeasurementTypes` 守衛；修正非數值 `measured_value` 存 DB |
| `backend/app/config/instruments.py` | 新增 `comport`/`console`/`tcpip` 至 `MEASUREMENT_TEMPLATES` |
| `backend/app/core/instrument_config.py` | 新增 `console_1`/`comport_1`/`tcpip_1` 至 `_load_default_config()`（使用 `type="LOCAL"`）|
| `backend/app/services/instruments/__init__.py` | import 並登錄三個 Command 驅動至 `INSTRUMENT_DRIVERS` |
| `backend/app/services/measurement_service.py` | 新增 `"parameters": test_params` 至 `test_plan_item` dict |
| `backend/app/measurements/implementations.py` | 修正三個 Measurement 類別的 `measured_value` 型別處理及 `validate_result` 傳參 |
| `backend/app/services/instruments/smcv100b.py` | 修正預存在的縮排錯誤（第 170-172 行）|

---

## 測試驗證

1. 在 TestPlanManage.vue 確認「測試類型」下拉選單出現 `console`、`comport`、`tcpip` 選項
2. 執行 `echo_test`（`test_type=console`, `Command=echo hello`, `eq_limit=hello`, `limit_type=partial`）
3. 預期結果：
   - 後端執行 `echo hello` → 回傳 `'hello'`
   - `validate_result('hello')` 對 `partial` match `'hello'` → **PASS**
   - `measured_value=null` 儲存至 DB（字串不存數值欄位）
   - 前端顯示 PASS，無 500 錯誤

---

## 影響範圍

- `console` / `comport` / `tcpip` 三種新測量類型的完整執行鏈
- `DECIMAL` 型態的 `measured_value` DB 欄位寫入保護（適用所有字串型測量）
- `BaseMeasurement.self.test_params` 的讀取正確性（影響所有 Measurement 類別）

---

## 相關文件

- `docs/features/command-measurement-migration.md` — 遷移設計文件
- `docs/plans/2026-02-24-command-measurement-migration.md` — 實作計畫
- `backend/app/measurements/implementations.py` — 各 Measurement 實作
- `backend/app/services/measurement_service.py` — 測量服務橋接層

---

**最後更新**: 2026-02-24
