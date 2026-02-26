# console / comport / tcpip 測試類型執行鏈驗證報告

**驗證日期**: 2026-02-26
**驗證範圍**: `console`、`comport`、`tcpip` 三個測試類型的完整六層執行鏈
**參考文件**: `docs/bugfix/ISSUE9_console_comport_tcpip_measurement_chain.md`

---

## 執行鏈架構

```
TestPlanManage.vue（選單）
  → /api/measurements/types（MEASUREMENT_TEMPLATES）
  → get_measurement_class(test_type)（MEASUREMENT_REGISTRY）
  → BaseMeasurement 子類別.execute()
  → get_driver_class(config.type)（INSTRUMENT_DRIVERS）
  → instrument_config._load_default_config()（虛擬儀器設定）
  → 字串型 measured_value 處理
  → TestMain.vue createTestResult() DB 寫入保護
```

---

## 驗證結果

### comport

| 驗證層 | 位置 | 狀態 |
|--------|------|------|
| `MEASUREMENT_TEMPLATES["comport"]` | `backend/app/config/instruments.py:227` | ✅ |
| `MEASUREMENT_TYPE_DESCRIPTIONS["comport"]` | `backend/app/config/instruments.py:324` | ✅ |
| `MEASUREMENT_REGISTRY["comport"]` | `backend/app/measurements/implementations.py:2061` | ✅ |
| `get_measurement_class("comport")` command_map | `backend/app/measurements/implementations.py:2115` | ✅ |
| `INSTRUMENT_DRIVERS["comport"]` | `backend/app/services/instruments/__init__.py:95` | ✅ |
| `_load_default_config()["comport_1"]` (LOCAL) | `backend/app/core/instrument_config.py:205` | ✅ |
| `ComPortMeasurement` StringType 分路 | `backend/app/measurements/implementations.py:444` | ✅ |
| 前端 DB 寫入保護 | `frontend/src/views/TestMain.vue:createTestResult()` | ✅ |

### console

| 驗證層 | 位置 | 狀態 |
|--------|------|------|
| `MEASUREMENT_TEMPLATES["console"]` | `backend/app/config/instruments.py:243` | ✅ |
| `MEASUREMENT_TYPE_DESCRIPTIONS["console"]` | `backend/app/config/instruments.py:329` | ✅ |
| `MEASUREMENT_REGISTRY["console"]` | `backend/app/measurements/implementations.py:2059` | ✅ |
| `get_measurement_class("console")` command_map | `backend/app/measurements/implementations.py:2114` | ✅ |
| `INSTRUMENT_DRIVERS["console"]` | `backend/app/services/instruments/__init__.py:94` | ✅ |
| `_load_default_config()["console_1"]` (LOCAL) | `backend/app/core/instrument_config.py:197` | ✅ |
| `ConSoleMeasurement` StringType 分路 | `backend/app/measurements/implementations.py:527` | ✅ |
| 前端 DB 寫入保護 | `frontend/src/views/TestMain.vue:createTestResult()` | ✅ |

### tcpip

| 驗證層 | 位置 | 狀態 |
|--------|------|------|
| `MEASUREMENT_TEMPLATES["tcpip"]` | `backend/app/config/instruments.py:258` | ✅ |
| `MEASUREMENT_TYPE_DESCRIPTIONS["tcpip"]` | `backend/app/config/instruments.py:334` | ✅ |
| `MEASUREMENT_REGISTRY["tcpip"]` | `backend/app/measurements/implementations.py:2063` | ✅ |
| `get_measurement_class("tcpip")` command_map | `backend/app/measurements/implementations.py:2116` | ✅ |
| `INSTRUMENT_DRIVERS["tcpip"]` | `backend/app/services/instruments/__init__.py:96` | ✅ |
| `_load_default_config()["tcpip_1"]` (LOCAL) | `backend/app/core/instrument_config.py:213` | ✅ |
| `TCPIPMeasurement` StringType 分路 | `backend/app/measurements/implementations.py:609` | ✅ |
| 前端 DB 寫入保護 | `frontend/src/views/TestMain.vue:createTestResult()` | ✅ |

---

## 關鍵實作細節

### 1. 前端選單動態來源

`TestPlanManage.vue` 的「測試類型」下拉選單透過 `useMeasurementParams` composable 呼叫 `/api/measurements/types`，後端從 `MEASUREMENT_TEMPLATES` 的頂層 key 動態產生清單。三個類型均作為頂層 key 存在，選單會自動顯示。

### 2. switch_mode 自動設定

三個類型的 `MEASUREMENT_TEMPLATES` 各自只有一個 switch_mode（與 test_type 同名，例如 `"comport": {"comport": {...}}`）。`TestPlanManage.vue:handleTestTypeChange()` 在 `switchModes.length === 1` 時會自動選取，使用者無需手動選擇儀器模式。

### 3. 虛擬儀器使用 LOCAL 連線

`comport_1`、`console_1`、`tcpip_1` 皆使用 `InstrumentAddress(type="LOCAL", address="local://...")` 而非 `VISAAddress`，避免 `create_connection()` 嘗試建立 VISA 連線（需要 pyvisa 套件）。

### 4. 字串型測量值處理

三個 Measurement class 的 `execute()` 均以相同模式處理：

```python
if self.value_type is StringType:
    measured_value = response_str          # 字串保留供 UI 顯示
else:
    try:
        measured_value = Decimal(response_str)
    except (ValueError, TypeError):
        measured_value = None

is_valid, error_msg = self.validate_result(response_str)  # 永遠驗證原始字串
```

### 5. DB 寫入保護（前端）

`TestMain.vue:createTestResult()` 在儲存前判斷 `measured_value` 是否為數值，非數值字串傳 `null`，避免 MySQL `DECIMAL(15,6)` 欄位寫入錯誤：

```javascript
const asNum = Number(rawValue)
measuredValueStr = (!isNaN(asNum) && rawValue !== '') ? String(rawValue) : null
```

---

## 結論

三個測試類型的執行鏈六層均驗證完整，無缺漏。ISSUE #9 所描述的全部修正（錯誤 1–7）在 `console`、`comport`、`tcpip` 上均已正確落地。
