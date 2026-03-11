# comport 測試類型 - Instrument 欄位運作分析

## 概述

當測試計劃管理頁面（`TestPlanManage.vue`）選擇測試類型 `comport` 時，「測試參數設定」區塊會顯示 `Instrument` 欄位。本文說明此欄位從前端輸入到後端執行的完整運作流程。

---

## 1. 前端：參數渲染

### 測試類型模板

**`backend/app/config/instruments.py`** 定義 comport 所需參數：

```python
"comport": {
    "comport": {
        "required": ["Instrument", "Command"],
        "optional": ["Timeout", "ReslineCount", "ComportWait", "SettlingTime"],
        "example": {
            "Instrument": "comport_1",
            "Command": "AT+VERSION\\n",
        }
    }
}
```

- `Instrument` 是**必填欄位**
- 範例值 `comport_1` 是後端設定檔中的鍵值（Key），非實際 COM port 名稱

### 前端渲染方式

**`frontend/src/components/DynamicParamForm.vue`** 使用 `inferParamType()` 推斷參數類型：

- 含 "volt", "curr", "channel" 等關鍵字 → 數字輸入
- 完全匹配 "baud", "type", "item" → 下拉選單
- `"Instrument"` → **純文字輸入**（預設情況）

> **注意：** Instrument 欄位目前是**純文字輸入**，不是從後端獲取可用儀器列表的下拉選單。

---

## 2. 資料傳遞流程

使用者輸入 `comport_1` 後，執行測試時由 `TestMain.vue` 的 `executeSingleItem()` 打包：

```json
POST /api/measurements/execute
{
  "measurement_type": "comport",
  "switch_mode": "comport",
  "test_params": {
    "Instrument": "comport_1",
    "Command": "AT+VERSION\n",
    "Timeout": 3.0,
    "ReslineCount": 1,
    "ComportWait": 0,
    "SettlingTime": 0.5
  }
}
```

---

## 3. 後端執行流程

### API 端點

**`backend/app/api/measurements.py`**

```python
@router.post("/execute", response_model=MeasurementResponse)
async def execute_measurement(request: MeasurementRequest, ...):
    result = await measurement_service.execute_single_measurement(
        measurement_type=request.measurement_type,   # "comport"
        switch_mode=request.switch_mode,             # "comport"
        test_params=request.test_params,             # {Instrument: "comport_1", ...}
        ...
    )
```

### 測量服務

**`backend/app/services/measurement_service.py`**

```python
async def execute_single_measurement(measurement_type, switch_mode, test_params, ...):
    # 從 Registry 取得 ComPortMeasurement class
    measurement_class = get_measurement_class(measurement_type)

    test_plan_item = {
        **test_params,
        "parameters": test_params,
        "switch_mode": switch_mode,
        "measurement_type": measurement_type,
    }

    measurement = measurement_class(test_plan_item=test_plan_item, config={})
    result = await measurement.execute()
```

### ComPortMeasurement 執行邏輯

**`backend/app/measurements/implementations.py`**

```python
class ComPortMeasurement(BaseMeasurement):
    async def execute(self) -> MeasurementResult:
        # Step 1: 取出 Instrument 參數值
        instrument_name = get_param(self.test_params, "Instrument", "instrument")
        # → "comport_1"

        # Step 2: 查詢儀器設定
        instrument_settings = get_instrument_settings()
        config = instrument_settings.get_instrument(instrument_name)
        if config is None:
            return self.create_result(
                result="ERROR",
                error_message=f"Instrument '{instrument_name}' not configured"
            )
        # → InstrumentConfig(type="comport", connection=SerialAddress(port="COM3", baudrate=115200))

        # Step 3: 取得對應 Driver class
        driver_class = get_driver_class(config.type)
        # → ComPortCommandDriver

        # Step 4: 從連線池取得連線並執行
        async with connection_pool.get_connection(instrument_name) as conn:
            driver = ComPortCommandDriver(conn)
            await driver.initialize()
            response = await driver.send_command(self.test_params)

        # Step 5: 驗證結果
        is_valid, error_msg = self.validate_result(response)
        return self.create_result(
            result="PASS" if is_valid else "FAIL",
            measured_value=response,
            error_message=error_msg if not is_valid else None
        )
```

---

## 4. Instrument 設定查詢

**`backend/app/core/instrument_config.py`** 的 `InstrumentSettings`：

- Instrument 字串（如 `comport_1`）是設定檔的 **Key**
- 設定來源（優先順序）：
  1. 環境變數 `INSTRUMENTS_CONFIG_JSON`（JSON 字串）
  2. 環境變數 `INSTRUMENTS_CONFIG_FILE`（JSON 檔案路徑）
  3. 預設設定（`_load_default_config()`）

設定結構範例：
```json
{
  "comport_1": {
    "type": "comport",
    "connection": {
      "port": "COM3",
      "baudrate": 115200,
      "timeout": 5000
    }
  }
}
```

---

## 5. Driver 解析與執行

**`backend/app/services/instruments/__init__.py`** 的 Driver Registry：

```python
INSTRUMENT_DRIVERS = {
    "comport": ComPortCommandDriver,
    "tcpip":   TCPIPCommandDriver,
    "console": ConSoleCommandDriver,
    "DAQ973A": DAQ973ADriver,
    ...
}
```

**`backend/app/services/instruments/comport_command.py`** 的 `ComPortCommandDriver`：

```python
class ComPortCommandDriver(BaseInstrumentDriver):
    async def initialize(self):
        """依設定開啟序列埠"""
        port = self.connection.config.connection.port       # e.g., "COM3"
        baudrate = self.connection.config.connection.baudrate  # e.g., 115200
        self.serial_port = serial.Serial(port=port, baudrate=baudrate, ...)

    async def send_command(self, test_params):
        """發送命令並讀取回應"""
        command = get_param(test_params, "Command", "command")
        timeout = get_param(test_params, "Timeout", "timeout", default=3.0)
        await self._write_command(command)
        return await self._read_response(timeout=timeout)
```

---

## 6. 完整資料流程圖

```
使用者輸入 Instrument = "comport_1"
    ↓
TestPlanManage.vue → 儲存到 test_plan_item.parameters
    ↓
TestMain.vue executeSingleItem()
    ↓
POST /api/measurements/execute
  { test_params: { Instrument: "comport_1", Command: "...", ... } }
    ↓
measurement_service.execute_single_measurement()
    ↓
ComPortMeasurement(test_plan_item)
    ↓
ComPortMeasurement.execute():
  1. get_param(test_params, "Instrument") → "comport_1"
  2. instrument_settings.get_instrument("comport_1") → InstrumentConfig
  3. get_driver_class("comport") → ComPortCommandDriver
  4. connection_pool.get_connection("comport_1")
  5. driver.send_command(test_params)
    ↓
ComPortCommandDriver:
  - 開啟 COM3 序列埠（baudrate=115200）
  - 發送 Command 字串
  - 讀取回應
    ↓
validate_result() → PASS / FAIL
    ↓
回傳 measured_value 到前端顯示
```

---

## 7. 相關檔案索引

| 元件 | 檔案 | 說明 |
|------|------|------|
| 參數模板 | `backend/app/config/instruments.py` | `MEASUREMENT_TEMPLATES["comport"]`，定義必填/選填參數 |
| 前端表單 | `frontend/src/components/DynamicParamForm.vue` | 渲染參數輸入欄位 |
| 參數收集 | `frontend/src/views/TestMain.vue` | `executeSingleItem()` |
| API 端點 | `backend/app/api/measurements.py` | `POST /api/measurements/execute` |
| 測量服務 | `backend/app/services/measurement_service.py` | `execute_single_measurement()` |
| 測量實作 | `backend/app/measurements/implementations.py` | `ComPortMeasurement.execute()` |
| 儀器設定 | `backend/app/core/instrument_config.py` | `InstrumentSettings.get_instrument()` |
| Driver Registry | `backend/app/services/instruments/__init__.py` | `INSTRUMENT_DRIVERS` 字典 |
| Driver 實作 | `backend/app/services/instruments/comport_command.py` | `ComPortCommandDriver` |

---

## 8. 錯誤情境

| 情境 | 錯誤訊息 | 原因 |
|------|----------|------|
| Instrument 欄位空白 | `Missing required parameter: Instrument` | 未填寫 Instrument 值 |
| Instrument 值找不到 | `Instrument 'xxx' not configured` | 設定檔中無此 Key |
| Driver 類型不支援 | `No driver for instrument type 'xxx'` | INSTRUMENT_DRIVERS 無對應 |
| 序列埠無法開啟 | 序列埠相關 exception | 實體 COM port 不存在或已被占用 |
