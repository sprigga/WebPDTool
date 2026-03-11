# 07 - 測量系統

## 測量系統概覽

WebPDTool 的核心創新是**測量抽象層**，它實現了從 PDTool4 遷移過來的完整測量和驗證邏輯。

```
┌─────────────────────────────────┐
│  TestEngine (測試編排)           │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  MeasurementService (執行協調)   │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ BaseMeasurement (抽象基類)       │
├─ prepare()  配置硬體            │
├─ execute()  執行測量            │
├─ cleanup()  清理狀態            │
└─ validate_result() PDTool4 邏輯  │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ 20+ 具體實現 (PowerRead、...)    │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  InstrumentManager (硬體管理)    │
│  └─ 與實際硬體通訊               │
└─────────────────────────────────┘
```

## 三相測量生命週期

每個測量執行都遵循相同的三個階段：

```python
class BaseMeasurement(ABC):
    async def prepare(self, params: Dict[str, Any]) -> None:
        """
        階段 1: 準備 (配置)
        - 解析引數
        - 配置硬體
        - 分配資源

        示例:
            channel = params['channel']     # 通道號
            range_val = params['range']     # 量程
            await instrument.set_channel(channel)
            await instrument.set_range(range_val)
        """
        raise NotImplementedError

    async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
        """
        階段 2: 執行 (測量)
        - 傳送命令到硬體
        - 等待響應
        - 採集資料
        - 返回 MeasurementResult

        示例:
            try:
                reading = await instrument.read_value()
                return MeasurementResult(
                    value=reading,
                    unit='V',
                    success=True
                )
            except Exception as e:
                return MeasurementResult(
                    value=None,
                    success=False,
                    error=str(e)
                )
        """
        raise NotImplementedError

    async def cleanup(self) -> None:
        """
        階段 3: 清理 (重置)
        - 重置到安全狀態
        - 釋放資源
        - 記錄日誌

        示例:
            await instrument.reset()
            await instrument.disable_output()
        """
        raise NotImplementedError
```

## PDTool4 驗證邏輯

WebPDTool 的驗證核心是 7 種 limit_type 與 3 種 value_type 的組合，完全複製 PDTool4 的行為：

### 7 種限制型別 (limit_type)

```python
def validate_result(
    self,
    measured_value: Any,
    lower_limit: Optional[Any],
    upper_limit: Optional[Any],
    limit_type: str = 'both',
    value_type: str = 'float'
) -> Tuple[bool, str]:
    """
    驗證測量值是否符合規範
    """

    # 1. LOWER - 只檢查下限
    if limit_type == 'lower':
        if float(measured_value) >= float(lower_limit):
            return True, f"符合下限 ≥ {lower_limit}"
        return False, f"低於下限 {lower_limit}"

    # 2. UPPER - 只檢查上限
    elif limit_type == 'upper':
        if float(measured_value) <= float(upper_limit):
            return True, f"符合上限 ≤ {upper_limit}"
        return False, f"高於上限 {upper_limit}"

    # 3. BOTH - 檢查範圍 [最常用]
    elif limit_type == 'both':
        val = float(measured_value)
        lower = float(lower_limit)
        upper = float(upper_limit)
        if lower <= val <= upper:
            return True, f"在範圍 {lower}-{upper} 內"
        return False, f"超出範圍 {lower}-{upper}"

    # 4. EQUALITY - 精確匹配 [字串]
    elif limit_type == 'equality':
        expected = str(expected_value)
        actual = str(measured_value)
        if actual == expected:
            return True, f"匹配期望值 {expected}"
        return False, f"不匹配期望值 {expected}"

    # 5. INEQUALITY - 不等於 [字串]
    elif limit_type == 'inequality':
        if str(measured_value) != str(expected_value):
            return True, f"不等於 {expected_value}"
        return False, f"值不應該是 {expected_value}"

    # 6. PARTIAL - 子字串包含 [字串]
    elif limit_type == 'partial':
        if str(expected_value) in str(measured_value):
            return True, f"包含期望子串 {expected_value}"
        return False, f"不包含 {expected_value}"

    # 7. NONE - 無驗證，總是通過
    elif limit_type == 'none':
        return True, "無驗證規則，自動通過"
```

### 3 種值型別 (value_type)

```python
# value_type 決定如何轉換和比較值

'string'  → str(measured_value) vs str(expected_value)
    # 示例："OK" == "OK"

'integer' → int(measured_value) vs int(expected_value)
    # 示例：42 == 42

'float'   → float(measured_value) vs float(expected_value)
    # 示例：5.15 vs 5.5 (with tolerance)
    #  浮點數比較有容差，避免精度問題
```

### 驗證矩陣 (7 × 3 = 21 種組合)

| limit_type | string | integer | float |
|------------|--------|---------|-------|
| lower | 字串 ≥ | 整數 ≥ | 浮點 ≥ |
| upper | 字串 ≤ | 整數 ≤ | 浮點 ≤ |
| both | N/A | 範圍檢查 | 範圍檢查 |
| equality | 完全匹配 | 完全匹配 | 完全匹配 |
| inequality | 不相等 | 不相等 | 不相等 |
| partial | 包含檢查 | N/A | N/A |
| none | 總是通過 | 總是通過 | 總是通過 |

### 實際例子

#### 例子 1: 電壓測量 (PowerRead)
```json
{
  "test_type": "PowerRead",
  "item_name": "電源輸入電壓",
  "measured_value": "5.15",
  "lower_limit": 4.5,
  "upper_limit": 5.5,
  "limit_type": "both",
  "value_type": "float"
}
```

驗證：4.5 ≤ 5.15 ≤ 5.5 → **PASS**

#### 例子 2: 序列號獲取 (GetSN)
```json
{
  "test_type": "getSN",
  "item_name": "裝置序列號",
  "measured_value": "SN20260311001",
  "expected_value": "SN",
  "limit_type": "partial",
  "value_type": "string"
}
```

驗證："SN" in "SN20260311001" → **PASS**

#### 例子 3: 跳線配置 (OPjudge)
```json
{
  "test_type": "OPjudge",
  "item_name": "跳線配置",
  "measured_value": "J1_ON",
  "expected_value": "J1_ON",
  "limit_type": "equality",
  "value_type": "string"
}
```

驗證："J1_ON" == "J1_ON" → **PASS**

## 20+ 測量型別實現

### 通訊類

#### ComPortMeasurement (串口通訊)
```python
class ComPortMeasurement(BaseMeasurement):
    """通過 RS-232/RS-485 串口通訊的測量"""

    async def prepare(self, params):
        self.port = params['port']      # COM1, /dev/ttyUSB0
        self.baudrate = params.get('baudrate', 9600)
        # 開啟串口
        self.serial = await open_serial_port(self.port, self.baudrate)

    async def execute(self, params):
        command = params['command']     # 要傳送的 AT 命令
        await self.serial.write(command)
        response = await self.serial.read_until_timeout(timeout=2)
        return MeasurementResult(value=response.decode())

    async def cleanup(self):
        await self.serial.close()
```

#### TCPIPMeasurement (網路通訊)
```python
class TCPIPMeasurement(BaseMeasurement):
    """通過 TCP/IP 網路通訊的測量"""

    async def prepare(self, params):
        self.ip = params['ip']
        self.port = params['port']
        self.socket = await connect_socket(self.ip, self.port)

    async def execute(self, params):
        command = params['command']
        await self.socket.send(command)
        response = await self.socket.recv(1024)
        return MeasurementResult(value=response.decode())
```

### 電源類

#### PowerReadMeasurement (讀取功率)
```python
class PowerReadMeasurement(BaseMeasurement):
    """從功率計讀取功率值"""

    async def prepare(self, params):
        channel = params.get('channel', 1)
        range_val = params.get('range', 'AUTO')
        await self.instrument.select_channel(channel)
        await self.instrument.set_range(range_val)

    async def execute(self, params):
        reading = await self.instrument.read_power()
        return MeasurementResult(
            value=reading,
            unit='W',
            timestamp=datetime.now(timezone.utc)
        )

    async def cleanup(self):
        await self.instrument.reset()
```

#### PowerSetMeasurement (設定電源)
```python
class PowerSetMeasurement(BaseMeasurement):
    """設定電源輸出值"""

    async def execute(self, params):
        voltage = float(params['voltage'])
        current = float(params.get('current_limit', 10.0))

        await self.instrument.set_voltage(voltage)
        await self.instrument.set_current_limit(current)
        await self.instrument.enable_output()

        return MeasurementResult(
            value=voltage,
            success=True
        )
```

### 資料採集類

#### GetSNMeasurement (獲取序列號)
```python
class GetSNMeasurement(BaseMeasurement):
    """獲取裝置序列號"""

    async def execute(self, params):
        # 通過 UART 或串口傳送查詢命令
        command = params.get('command', 'AT+GSN\r\n')
        response = await self.send_command(command)

        # 提取 SN
        sn = parse_sn_from_response(response)
        return MeasurementResult(value=sn)
```

#### CommandTestMeasurement (傳送命令)
```python
class CommandTestMeasurement(BaseMeasurement):
    """傳送並驗證命令響應"""

    async def execute(self, params):
        command = params['command']
        expected = params['expected_response']

        response = await self.send_command(command)

        # 驗證響應中是否包含期望值
        if expected in response:
            return MeasurementResult(value=response, success=True)
        return MeasurementResult(value=response, success=False,
                               error=f"期望 {expected}")
```

### 製造整合類

#### SFCMeasurement (SFC 系統互動)
```python
class SFCMeasurement(BaseMeasurement):
    """與 SFC (生產系統) 互動"""

    async def execute(self, params):
        # 查詢 SFC 系統中的產品資訊
        product_id = params['product_id']
        sfc_data = await self.sfc_service.query_product(product_id)

        return MeasurementResult(value=str(sfc_data))
```

#### OPJudgeMeasurement (工程決策/跳線配置)
```python
class OPJudgeMeasurement(BaseMeasurement):
    """工程判定 - 讀取跳線配置或工程開關狀態"""

    async def execute(self, params):
        gpio_pin = params['gpio_pin']

        # 讀取 GPIO 狀態
        state = await self.instrument.read_gpio(gpio_pin)

        return MeasurementResult(
            value=f"J{gpio_pin}_{'ON' if state else 'OFF'}"
        )
```

### RF 測試類

#### RF_Tool_LTE_TX_Measurement (LTE 發射)
```python
class RF_Tool_LTE_TX_Measurement(BaseMeasurement):
    """LTE 射頻發射測試"""

    async def execute(self, params):
        band = params['band']
        channel = params['channel']
        power = params['tx_power']

        # 通過 RF 測試儀控制 DUT 發射
        result = await self.rf_tool.measure_tx_power(
            band=band, channel=channel
        )

        return MeasurementResult(value=result['power_dbm'])
```

#### CMW100_BLE_Measurement (BLE 測試)
```python
class CMW100_BLE_Measurement(BaseMeasurement):
    """使用 CMW100 進行 BLE 測試"""

    async def execute(self, params):
        frequency = params.get('frequency', 2402)  # MHz

        result = await self.cmw100.measure_ble_power(frequency)

        return MeasurementResult(value=result['power_dbm'])
```

### 硬體控制類

#### RelayMeasurement (繼電器控制)
```python
class RelayMeasurement(BaseMeasurement):
    """控制繼電器開關"""

    async def execute(self, params):
        relay_id = params['relay_id']
        action = params.get('action', 'ON')  # ON/OFF

        if action == 'ON':
            await self.instrument.relay_close(relay_id)
        else:
            await self.instrument.relay_open(relay_id)

        return MeasurementResult(value=action, success=True)
```

#### WaitMeasurement (等待計時)
```python
class WaitMeasurement(BaseMeasurement):
    """等待指定時間 (用於提交延遲操作)"""

    async def execute(self, params):
        duration_ms = params['duration_ms']

        await asyncio.sleep(duration_ms / 1000)

        return MeasurementResult(
            value=duration_ms,
            success=True
        )
```

#### ChassisRotationMeasurement (旋轉測試框)
```python
class ChassisRotationMeasurement(BaseMeasurement):
    """旋轉測試框 (用於多產品並行測試)"""

    async def execute(self, params):
        rotation_count = params['rotation_count']

        await self.instrument.rotate_chassis(rotation_count)

        return MeasurementResult(
            value=rotation_count,
            success=True
        )
```

### 其他類

#### OtherMeasurement (通用)
```python
class OtherMeasurement(BaseMeasurement):
    """自定義/其他測量型別"""

    async def execute(self, params):
        # 由 JSON 引數完全定義
        operation = params['operation']

        # 執行自定義邏輯
        result = await self.execute_custom_operation(operation)

        return MeasurementResult(value=result)
```

#### DummyMeasurement (測試佔位符)
```python
class DummyMeasurement(BaseMeasurement):
    """用於測試的虛擬測量"""

    async def execute(self, params):
        # 返回固定值，用於 UI 測試
        return MeasurementResult(value="DUMMY_PASS")
```

## MeasurementResult 資料類

```python
@dataclass
class MeasurementResult:
    """測量結果的標準格式"""

    value: Optional[Union[str, int, float]]
    # 測量得到的實際值

    unit: Optional[str] = None
    # 單位 ("V", "A", "W", "dBm" 等)

    success: bool = True
    # 測量過程是否成功 (False = 硬體錯誤)

    error: Optional[str] = None
    # 錯誤資訊 (如果 success=False)

    timestamp: datetime = field(default_factory=datetime.now)
    # 測量時間戳
```

## 測量註冊表與發現

**檔案:** `app/measurements/registry.py`

```python
MEASUREMENT_REGISTRY = {
    'PowerRead': PowerReadMeasurement,
    'PowerSet': PowerSetMeasurement,
    'CommandTest': CommandTestMeasurement,
    'SFCtest': SFCMeasurement,
    'getSN': GetSNMeasurement,
    'OPjudge': OPJudgeMeasurement,
    'Other': OtherMeasurement,
    'ComPort': ComPortMeasurement,
    'Console': ConSoleMeasurement,
    'TCPIP': TCPIPMeasurement,
    'Relay': RelayMeasurement,
    'ChassisRotation': ChassisRotationMeasurement,
    'Wait': WaitMeasurement,
    'RF_Tool_LTE_TX': RF_Tool_LTE_TX_Measurement,
    'RF_Tool_LTE_RX': RF_Tool_LTE_RX_Measurement,
    'CMW100_BLE': CMW100_BLE_Measurement,
    'CMW100_WiFi': CMW100_WiFi_Measurement,
    'L6MPU_LTE_Check': L6MPU_LTE_Check_Measurement,
    'L6MPU_PLC_Test': L6MPU_PLC_Test_Measurement,
    'MDO34': MDO34Measurement,
    # ... 更多型別
}

def get_measurement_class(test_type: str) -> Type[BaseMeasurement]:
    """執行時獲取測量類"""
    return MEASUREMENT_REGISTRY.get(test_type, OtherMeasurement)
```

## 測量引數 JSON 示例

```json
{
  "PowerRead": {
    "channel": 1,
    "range": "AUTO",
    "timeout_ms": 5000
  },

  "ComPort": {
    "port": "COM1",
    "baudrate": 9600,
    "command": "AT+GSN\r\n"
  },

  "RF_Tool_LTE_TX": {
    "band": 1,
    "channel": 100,
    "tx_power": 20,
    "modulation": "QPSK"
  },

  "CommandTest": {
    "command": "AT+CSQ\r\n",
    "expected_response": "OK"
  }
}
```

## runAllTest 模式 (故障繼續)

在 MeasurementService 中實現：

```python
async def execute_measurement(test_plan, params, run_all_test):
    errors = []

    for item in test_plan.items:
        try:
            measurement = get_measurement_class(item.test_type)

            result = await measurement.prepare(item.parameters)
            result = await measurement.execute(item.parameters)
            await measurement.cleanup()

            is_valid, message = measurement.validate_result(result, ...)

            if not is_valid and not run_all_test:
                # 正常模式：故障則停止
                raise ValidationError(message)

            if not is_valid:
                # runAllTest 模式：繼續，收集錯誤
                errors.append({
                    'item_no': item.item_no,
                    'error': message
                })

        except Exception as e:
            if not run_all_test:
                raise
            errors.append({
                'item_no': item.item_no,
                'error': str(e)
            })

    # 返回錯誤彙總
    return {
        'status': 'COMPLETED',
        'final_result': 'PASS' if not errors else 'FAIL',
        'error_summary': errors
    }
```

## 新增新的測量型別

### 步驟 1: 建立類

在 `app/measurements/implementations.py`:

```python
class MyCustomMeasurement(BaseMeasurement):

    async def prepare(self, params):
        # 配置硬體
        pass

    async def execute(self, params):
        # 執行測量
        value = await self.get_value()
        return MeasurementResult(value=value)

    async def cleanup(self):
        # 清理
        pass
```

### 步驟 2: 註冊

在 `app/measurements/registry.py`:

```python
MEASUREMENT_REGISTRY['MyCustom'] = MyCustomMeasurement
```

### 步驟 3: CSV 中使用

```
test_type = MyCustom
limit_type = both
value_type = float
parameters = {...}
```

## 下一步

- **瞭解 API**: [06-api-endpoints.md](06-api-endpoints.md)
- **學習後端**: [03-backend-structure.md](03-backend-structure.md)
- **開發指南**: [10-development-guide.md](10-development-guide.md)
