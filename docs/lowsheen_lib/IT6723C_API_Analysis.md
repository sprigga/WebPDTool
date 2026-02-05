# IT6723C API Analysis

## Overview

IT6723C 是 ITECH 電源供應器的驅動程序，提供電壓/電流設置、輸出控制和測量驗證功能。

**檔案位置**: `src/lowsheen_lib/IT6723C.py`
**儀器類型**: Programmable DC Power Supply
**通訊協議**: SCPI (Standard Commands for Programmable Instruments)

---

## Architecture

### Module Dependencies

```
IT6723C.py
├── remote_instrument.instrument_iniSetting  # 儀器初始化
├── sys                                       # 命令列參數處理
└── ast                                       # 參數解析
```

### Execution Flow

```
Main Entry (if __name__ == "__main__")
    ├── Parse command line arguments (sys.argv)
    ├── Initialize instrument connection
    │   └── instrument_iniSetting(Instrument_value)
    ├── Sequence detection
    │   ├── --final → initial(instrument)      # 輸出關閉
    │   └── normal  → send_cmd_to_instrument() # 設置並驗證
    └── Print response
```

---

## API Reference

### 1. `get_cmd_string(SetVolt, SetCurr)`

產生 SCPI 命令字串用於電壓/電流設置與查詢。

**Parameters:**
- `SetVolt` (str): 設置電壓值 (例如: "5", "12.5")
- `SetCurr` (str): 設置電流值 (例如: "1.5", "3.0")

**Returns:**
- `tuple`: (remote_Voltcmd, remote_Currcmd, check_Voltcmd, check_Currcmd)
  - `remote_Voltcmd` (str): 電壓設置命令 `"VOLT {value}"`
  - `remote_Currcmd` (str): 電流設置命令 `"CURR {value}"`
  - `check_Voltcmd` (str): 電壓查詢命令 `"MEAS:VOLT:DC?"`
  - `check_Currcmd` (str): 電流查詢命令 `"MEAS:CURR:DC?"`

**Example:**
```python
remote_Voltcmd, remote_Currcmd, check_Voltcmd, check_Currcmd = get_cmd_string("5", "1.5")
# Returns:
# ("VOLT 5", "CURR 1.5", "MEAS:VOLT:DC?", "MEAS:CURR:DC?")
```

---

### 2. `send_cmd_to_instrument(instrument, SetVolt, SetCurr)`

設置電源供應器的電壓和電流，並驗證設置是否成功。

**Parameters:**
- `instrument` (pyvisa.Resource): PyVISA 儀器物件
- `SetVolt` (str): 目標電壓值
- `SetCurr` (str): 目標電流值

**Returns:**
- `int`: `1` - 設置成功
- `str`: 錯誤訊息
  - `"Error : remote command is wrong"` - 命令生成失敗
  - `"IT6723C set volt fail"` - 電壓設置失敗
  - `"IT6723C set curr fail"` - 電流設置失敗
  - `"IT6723C set volt and curr fail"` - 兩者皆失敗

**Behavior:**
1. 產生 SCPI 命令字串
2. 寫入電壓設置命令 (`VOLT {value}`)
3. 寫入電流設置命令 (`CURR {value}`)
4. 啟用輸出 (`OUTP ON`)
5. 讀取實際電壓/電流值並驗證
6. 四捨五入至小數點後 2 位進行比較

**Validation Logic:**
```python
response_Volt = round(float(instrument.query("MEAS:VOLT:DC?")), 2)
response_Curr = round(float(instrument.query("MEAS:CURR:DC?")), 2)

if response_Volt != float(SetVolt):  # 驗證失敗
    errors.append('volt')
if response_Curr != float(SetCurr):  # 驗證失敗
    errors.append('curr')
```

**Example:**
```python
result = send_cmd_to_instrument(inst, "5", "1.5")
# Success: result = 1
# Failure: result = "IT6723C set volt fail"
```

---

### 3. `initial(instrument)`

關閉電源供應器輸出，用於測試結束時的清理操作。

**Parameters:**
- `instrument` (pyvisa.Resource): PyVISA 儀器物件

**Returns:**
- `None`

**Behavior:**
- 執行命令: `"OUTP OFF\n"` - 關閉輸出

**Usage:**
- 在 `--final` 序列模式下被調用
- 確保測試結束後設備處於安全狀態

**Example:**
```python
initial(instrument)  # 關閉電源輸出
```

---

## Command Line Interface

### Usage Pattern

```bash
uv run python IT6723C.py <sequence> <args_dict>
```

### Parameters

**sequence** (str):
- `--final`: 執行清理操作 (關閉輸出)
- 其他值: 執行正常設置與驗證

**args_dict** (str): Python 字典格式字串，包含以下鍵值：
- `Instrument` (str): 儀器識別碼 (例如: `"IT6723C_1"`)
- `SetVolt` (str): 目標電壓值
- `SetCurr` (str): 目標電流值

### Examples

#### Normal Operation
```bash
uv run python IT6723C.py normal "{'Instrument': 'IT6723C_1', 'SetVolt': '5', 'SetCurr': '1.5'}"
# Output: 1 (成功) 或錯誤訊息
```

#### Final Cleanup
```bash
uv run python IT6723C.py --final "{'Instrument': 'IT6723C_1'}"
# Output: (無輸出，執行關閉操作)
```

---

## SCPI Commands Reference

### Output Control Commands

| Command | Description | Parameter Range |
|---------|-------------|-----------------|
| `VOLT {value}` | 設置輸出電壓 | 依儀器規格 (IT6723C: 0-30V) |
| `CURR {value}` | 設置輸出電流 | 依儀器規格 (IT6723C: 0-3A) |
| `OUTP ON` | 啟用輸出 | - |
| `OUTP OFF` | 關閉輸出 | - |

### Measurement Query Commands

| Command | Description | Response Format |
|---------|-------------|-----------------|
| `MEAS:VOLT:DC?` | 查詢輸出電壓 | 浮點數 (例如: `5.01`) |
| `MEAS:CURR:DC?` | 查詢輸出電流 | 浮點數 (例如: `1.49`) |

---

## Error Handling

### Exit Codes

- `sys.exit(10)`: 儀器初始化失敗 (`instrument is None`)

### Error Messages

1. **Command Generation Error**
   ```
   "Error : remote command is wrong"
   ```
   - 原因: `get_cmd_string()` 返回 `None`
   - 處理: 檢查輸入參數格式

2. **Voltage Setting Error**
   ```
   "IT6723C set volt fail"
   ```
   - 原因: 設置後測量值與目標值不符
   - 可能原因: 儀器連接問題、超出範圍、儀器故障

3. **Current Setting Error**
   ```
   "IT6723C set curr fail"
   ```
   - 原因: 設置後測量值與目標值不符
   - 可能原因: 負載過大、儀器限制

4. **Combined Error**
   ```
   "IT6723C set volt and curr fail"
   ```
   - 原因: 電壓和電流設置皆失敗

---

## Implementation Notes

### Validation Precision
- 測量值四捨五入至小數點後 2 位
- 比較時使用浮點數相等比較
- 可能受儀器精度和穩定時間影響

**Potential Issue:**
```python
response_Volt = round(float(instrument.query("MEAS:VOLT:DC?")), 2)
if response_Volt != float(SetVolt):  # 直接相等比較可能太嚴格
```

**Improvement Suggestion:**
```python
# 使用容差比較
tolerance = 0.05  # 5% 或固定值
if abs(response_Volt - float(SetVolt)) > tolerance:
    errors.append('volt')
```

### No Settling Time
- 設置後立即測量，未等待穩定時間
- 可能導致瞬態測量誤差
- 建議加入 `time.sleep(0.1)` 在測量前

### No Output State Check
- 未驗證 `OUTP ON` 命令是否成功執行
- 建議加入 `instrument.query("OUTP?")`

---

## Integration Example

### Test Plan CSV Format

```csv
項次,品名規格,上限值,下限值,單位,儀器位置,測試類型,參數
1,Power Set 5V 1.5A,,,V,IT6723C_1,PowerSet,"{'SetVolt': '5', 'SetCurr': '1.5'}"
```

### Measurement Module Call Pattern

```python
from IT6723C import send_cmd_to_instrument, initial
from remote_instrument import instrument_iniSetting

# Initialize
instrument = instrument_iniSetting("IT6723C_1")

# Test execution
result = send_cmd_to_instrument(instrument, "5", "1.5")
if result == 1:
    print("PASS")
else:
    print(f"FAIL: {result}")

# Cleanup
initial(instrument)
instrument.close()
```

---

## Related Documentation

- **Instrument Manual**: IT6723C User Manual (ITECH)
- **SCPI Standard**: IEEE 488.2
- **PyVISA Documentation**: https://pyvisa.readthedocs.io/
- **Related Modules**:
  - `remote_instrument.py` - 儀器連接管理
  - `PowerSetMeasurement.py` - 上層測量封裝

---

## Revision History

| Version | Date | Description |
|---------|------|-------------|
| Initial | 2024-XX-XX | 原始實現 |

---

## Keywords

`IT6723C`, `Power Supply`, `SCPI`, `Voltage Control`, `Current Control`, `ITECH`, `PyVISA`, `Instrument Driver`
