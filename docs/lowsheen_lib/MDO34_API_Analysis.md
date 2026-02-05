# MDO34 API Analysis

## Overview

MDO34 是 Tektronix MDO3000 系列混合域示波器的驅動程序，提供自動設置和多種測量類型（頻率、振幅、週期等）。

**檔案位置**: `src/lowsheen_lib/MDO34.py`
**儀器類型**: Mixed Domain Oscilloscope (混合域示波器)
**製造商**: Tektronix
**通訊協議**: SCPI (Standard Commands for Programmable Instruments)
**連接介面**: USB, Ethernet, GPIB

---

## Architecture

### Module Dependencies

```
MDO34.py
├── pyvisa                                    # VISA 通訊
├── remote_instrument.instrument_iniSetting  # 儀器初始化
├── sys, ast                                  # 參數解析
├── time                                      # 延時控制
└── re                                        # 正則表達式 (未使用)
```

### Execution Flow

```
Main Entry (if __name__ == "__main__")
    ├── Parse arguments (Instrument, Item, Channel, Type)
    ├── Initialize instrument connection
    ├── Sequence detection
    │   ├── --final → initial(instrument)        # 重置
    │   └── normal  → send_cmd_to_instrument()   # 測量
    └── Print result
```

### Measurement Flow

```
send_cmd_to_instrument()
    ├── Map Item code to MeasType (conf.MeasType)
    ├── Measurement()
    │   ├── Query IDN (儀器識別)
    │   ├── Close unused channels
    │   ├── Select target channel (CH1-CH4)
    │   ├── Execute AutoSet
    │   ├── Wait for AutoSet completion (BUSY? polling)
    │   ├── Configure MEAS4 measurement slot
    │   │   ├── Set source channel (CH1-CH4)
    │   │   ├── Set measurement type (AMPlitude, FREQuency, etc.)
    │   │   └── Enable measurement state
    │   ├── Wait for measurement type confirmation
    │   ├── Query measurement value (MEAS4:VALue?)
    │   └── Format and return result
    └── Print result
```

---

## Configuration Class: `conf`

### `conf.MeasType`

測量類型代碼映射表，將數字代碼轉換為 SCPI 測量類型命令。

**Complete Mapping Table:**

| Code | SCPI Command | Description | 典型應用 |
|------|--------------|-------------|----------|
| '1' | `AMPlitude` | 振幅 | 信號幅度測量 |
| '2' | `AREa` | 面積 | 波形積分 |
| '3' | `BURst` | 突發信號 | 脈衝串測量 |
| '4' | `CARea` | 週期面積 | 單週期積分 |
| '5' | `CMEan` | 週期平均值 | 週期內平均電壓 |
| '6' | `CRMs` | 週期 RMS | 週期內有效值 |
| '7' | `DELay` | 延遲 | 通道間時間差 |
| '8' | `FALL` | 下降時間 | 信號邊緣分析 |
| '9' | `FREQuency` | 頻率 | 週期性信號頻率 |
| '10' | `HIGH` | 高電平 | 邏輯高電平值 |
| '11' | `HITS` | 命中數 | 統計測量 |
| '12' | `LOW` | 低電平 | 邏輯低電平值 |
| '13' | `MAXimum` | 最大值 | 波形峰值 |
| '14' | `MEAN` | 平均值 | 全波形平均 |
| '15' | `MEDian` | 中位數 | 統計分析 |
| '16' | `MINImum` | 最小值 | 波形谷值 |
| '17' | `NDUty` | 負佔空比 | 低電平時間比例 |
| '18' | `NEDGECount` | 負邊緣計數 | 下降邊緣數量 |
| '19' | `NOVershoot` | 負過衝 | 下降邊緣過衝 |
| '20' | `NPULSECount` | 負脈衝計數 | 負脈衝數量 |
| '21' | `NWIdth` | 負脈衝寬度 | 低電平持續時間 |
| '22' | `PEAKHits` | 峰值命中 | 峰值統計 |
| '23' | `PDUty` | 正佔空比 | 高電平時間比例 |
| '24' | `PEDGECount` | 正邊緣計數 | 上升邊緣數量 |
| '25' | `PERIod` | 週期 | 信號週期時間 |
| '26' | `PHAse` | 相位 | 通道間相位差 |
| '27' | `PK2Pk` | 峰峰值 | 最大值-最小值 |
| '28' | `POVershoot` | 正過衝 | 上升邊緣過衝 |
| '29' | `PPULSECount` | 正脈衝計數 | 正脈衝數量 |
| '30' | `PWIdth` | 正脈衝寬度 | 高電平持續時間 |
| '31' | `RISe` | 上升時間 | 信號邊緣分析 |
| '32' | `RMS` | 有效值 | 全波形 RMS |
| '33' | `SIGMA1` | 1σ | 統計分布 |
| '34' | `SIGMA2` | 2σ | 統計分布 |
| '35' | `SIGMA3` | 3σ | 統計分布 |
| '36' | `STDdev` | 標準差 | 統計分析 |
| '37' | `TOVershoot` | 總過衝 | 綜合過衝 |
| '38' | `WAVEFORMS` | 波形數量 | 統計測量 |

---

## API Reference

### 1. `Measurement()`

執行示波器測量的核心函數。

**Global Variables Used:**
- `inst` (pyvisa.Resource): 儀器物件
- `Channel` (str): 目標通道 ('1'-'4')
- `MeasType` (str): 測量類型 (SCPI 命令)

**Returns:**
- `float`: 測量值
- `None`: 發生異常時

**Execution Sequence:**

#### Phase 1: Channel Selection
```python
# 1. 查詢儀器識別
IDN = inst.query(':*IDN?')

# 2. 關閉其他通道顯示
closeChannel = ['1', '2', '3', '4']
closeChannel.remove(Channel)
for i in range(len(closeChannel)):
    inst.write('SELECT:CH' + closeChannel[i] + ' OFF')

# 3. 啟用目標通道
inst.write('SELECT:CH' + Channel + ' ON')

# 4. 確認通道選擇
selected_port = inst.query('SELECT:CH' + Channel + '?')
```

#### Phase 2: AutoSet Execution
```python
# 5. 執行自動設置 (自動調整時基和電壓刻度)
inst.write(':AUTOSet EXECute')

# 6. 輪詢等待 AutoSet 完成
while True:
    BUSY = inst.query('BUSY?')
    time.sleep(0.01)  # 10ms 輪詢間隔
    if '0' in BUSY:   # BUSY=0 表示完成
        break
```

#### Phase 3: Measurement Configuration
```python
# 7. 配置測量插槽 MEAS4
inst.write('MEASUrement:MEAS4:SOURCE1 CH' + Channel)  # 設置源通道
inst.write('MEASUrement:MEAS4:STATE ON')              # 啟用測量
inst.write('MEASUrement:MEAS4:TYPE ' + MeasType)      # 設置測量類型

# 8. 等待測量類型設置完成
while True:
    queryType = inst.query('MEASUrement:MEAS4:TYPE?')
    time.sleep(1)  # 1 秒間隔
    if MeasType.upper() in queryType:  # 確認類型已更新
        break
```

#### Phase 4: Result Retrieval
```python
# 9. 查詢測量值
queryValue = inst.query('MEASUrement:MEAS4:VALue?')

# 10. 格式化結果
queryValue = queryValue.replace('\n', '')
queryValue = queryValue.replace('\r', '')
queryValue = queryValue.replace(':MEASUREMENT:MEAS4:VALUE ', '')
queryValue = float(queryValue)  # 轉換為浮點數

return queryValue
```

**Error Handling:**
- 使用 `try-except` 包裹全部邏輯
- 異常時執行 `inst.close()` 並返回 `None`
- **問題**: 未記錄錯誤訊息，難以診斷失敗原因

**Example:**
```python
# 內部執行流程範例 (測量 CH2 頻率)
inst.write('SELECT:CH1 OFF')
inst.write('SELECT:CH3 OFF')
inst.write('SELECT:CH4 OFF')
inst.write('SELECT:CH2 ON')
inst.write(':AUTOSet EXECute')
# ... 等待 BUSY=0 ...
inst.write('MEASUrement:MEAS4:SOURCE1 CH2')
inst.write('MEASUrement:MEAS4:STATE ON')
inst.write('MEASUrement:MEAS4:TYPE FREQuency')
# ... 等待類型確認 ...
result = inst.query('MEASUrement:MEAS4:VALue?')  # 返回: "1.234567E+03"
# 輸出: 1234.567
```

---

### 2. `send_cmd_to_instrument(instrument, cmd, channels, type_)`

測量執行的封裝函數。

**Parameters:**
- `instrument` (pyvisa.Resource): PyVISA 儀器物件
- `cmd` (str): 測量類型代碼 ('1'-'38')
- `channels` (str): 通道編號 ('1'-'4')
- `type_` (Any): 保留參數 (未使用)

**Returns:**
- `float`: 測量結果
- `None`: 測量失敗

**Behavior:**
```python
# 1. 映射測量類型
MeasType = conf.MeasType.get(cmd, '')  # 例: cmd='9' → 'FREQuency'

# 2. 設置全域變數
global inst, Channel, MeasType
Channel = channels
inst = instrument

# 3. 執行測量
return Measurement()
```

**Example:**
```python
from MDO34 import send_cmd_to_instrument
from remote_instrument import instrument_iniSetting

inst = instrument_iniSetting("USB0::0x0699::0x052C::C051741::INSTR")
result = send_cmd_to_instrument(inst, '9', '2', None)  # CH2 頻率測量
print(f"Frequency: {result} Hz")
# Output: Frequency: 1234.567 Hz
```

---

### 3. `initial(instrument)`

重置儀器至預設狀態。

**Parameters:**
- `instrument` (pyvisa.Resource): PyVISA 儀器物件

**Returns:**
- `None`

**Behavior:**
```python
instrument.write('*RST\n')  # IEEE 488.2 標準重置命令
```

**Usage:**
- 在 `--final` 序列模式下調用
- 清除所有測量設置和顯示配置

**Example:**
```bash
uv run python MDO34.py --final "{'Instrument': 'USB0::...::INSTR'}"
```

---

### 4. `Close()`

關閉儀器連接。

**Returns:**
- `None`

**Behavior:**
```python
inst.close()  # 關閉 VISA 資源
```

**Note:**
- 在 `Measurement()` 異常處理中被調用
- 主程式執行流程中未明確調用

---

### 5. `help()`

輸出 API 使用說明。

**Output Content:**
```
**********************************************************************************
API Helper
Index 1: <Index> ， Example."USB0::0x0699::0x052C::C051741::INSTR"
Index 2: <Channel> ， 1-4
Index 3: <Type> ， 1:AMPlitude. 2:AREa. 3:BURst. ...
Example: USB0::0x0699::0x052C::C051741::INSTR 2 1
**********************************************************************************
```

**Usage:**
```python
help()  # 顯示使用說明
```

---

## Command Line Interface

### Usage Pattern

```bash
uv run python MDO34.py <sequence> <args_dict>
```

### Parameters

**sequence** (str):
- `--final`: 執行 `initial()` 重置儀器
- 其他值: 執行 `send_cmd_to_instrument()` 測量

**args_dict** (str): Python 字典格式字串，包含以下鍵值：
- `Instrument` (str): 儀器 VISA 地址
  - USB 格式: `"USB0::0x0699::0x052C::C051741::INSTR"`
  - Ethernet 格式: `"TCPIP0::192.168.1.100::INSTR"`
  - GPIB 格式: `"GPIB0::1::INSTR"`
- `Item` (str): 測量類型代碼 ('1'-'38')
- `Channel` (str): 通道編號 ('1'-'4')
- `Type` (Any): 保留參數 (選用)

### Examples

#### Measure Frequency on CH2
```bash
uv run python MDO34.py normal "{'Instrument': 'USB0::0x0699::0x052C::C051741::INSTR', 'Item': '9', 'Channel': '2'}"
# Output: 1234.567
```

#### Measure Amplitude on CH1
```bash
uv run python MDO34.py normal "{'Instrument': 'USB0::0x0699::0x052C::C051741::INSTR', 'Item': '1', 'Channel': '1'}"
# Output: 3.142
```

#### Measure Period on CH3
```bash
uv run python MDO34.py normal "{'Instrument': 'USB0::0x0699::0x052C::C051741::INSTR', 'Item': '25', 'Channel': '3'}"
# Output: 0.001
```

#### Reset Instrument
```bash
uv run python MDO34.py --final "{'Instrument': 'USB0::0x0699::0x052C::C051741::INSTR'}"
# (執行 *RST 重置)
```

---

## SCPI Commands Reference

### Channel Selection Commands

| SCPI Command | Description | Parameter |
|--------------|-------------|-----------|
| `SELECT:CH{n} {state}` | 通道顯示控制 | n: 1-4, state: ON/OFF |
| `SELECT:CH{n}?` | 查詢通道顯示狀態 | n: 1-4 |

### AutoSet Command

| SCPI Command | Description | Notes |
|--------------|-------------|-------|
| `:AUTOSet EXECute` | 執行自動設置 | 自動調整時基、垂直刻度、觸發 |
| `BUSY?` | 查詢忙碌狀態 | 返回 1 (忙碌) 或 0 (空閒) |

### Measurement Configuration Commands

| SCPI Command | Description | Parameter |
|--------------|-------------|-----------|
| `MEASUrement:MEAS4:SOURCE1 CH{n}` | 設置測量源通道 | n: 1-4 |
| `MEASUrement:MEAS4:STATE {state}` | 啟用/禁用測量 | ON/OFF |
| `MEASUrement:MEAS4:TYPE {type}` | 設置測量類型 | 見 conf.MeasType 表 |
| `MEASUrement:MEAS4:TYPE?` | 查詢測量類型 | 返回當前類型 |
| `MEASUrement:MEAS4:VALue?` | 查詢測量值 | 返回科學記號格式 |

**Note**: MDO3000 系列支援多個測量插槽 (MEAS1-MEAS8)，此驅動固定使用 MEAS4。

### Standard Commands

| SCPI Command | Description |
|--------------|-------------|
| `:*IDN?` | 查詢儀器識別資訊 |
| `*RST` | 重置儀器至預設狀態 |

---

## Measurement Slot Usage

### Why MEAS4?

程式固定使用 **MEAS4** 測量插槽：

```python
inst.write('MEASUrement:MEAS4:SOURCE1 CH' + Channel)
inst.write('MEASUrement:MEAS4:STATE ON')
inst.write('MEASUrement:MEAS4:TYPE ' + MeasType)
queryValue = inst.query('MEASUrement:MEAS4:VALue?')
```

**Potential Issues:**
1. **覆蓋現有測量**: 若 MEAS4 已被使用，會被覆蓋
2. **單一測量限制**: 無法同時執行多個測量
3. **測量槽衝突**: 多程序同時運行可能互相干擾

**Improvement Suggestion:**
```python
# 動態選擇空閒測量槽
for slot in range(1, 9):  # MEAS1-MEAS8
    state = inst.query(f'MEASUrement:MEAS{slot}:STATE?')
    if '0' in state:  # 找到空閒槽
        break
```

---

## Timing Considerations

### AutoSet Polling Interval

```python
while True:
    BUSY = inst.query('BUSY?')
    time.sleep(0.01)  # 10ms 間隔
    if '0' in BUSY:
        break
```

**Trade-offs:**
- **10ms 間隔**: 快速響應，但高 CPU 使用率
- **建議**: 使用指數退避策略 (exponential backoff)

```python
delay = 0.01
while True:
    BUSY = inst.query('BUSY?')
    if '0' in BUSY:
        break
    time.sleep(delay)
    delay = min(delay * 1.5, 0.5)  # 最大 500ms
```

### Measurement Type Confirmation Wait

```python
while True:
    queryType = inst.query('MEASUrement:MEAS4:TYPE?')
    time.sleep(1)  # 1 秒間隔
    if MeasType.upper() in queryType:
        break
```

**Issue:**
- **固定 1 秒過長**: 大多數情況下測量類型立即更新
- **建議**: 減少至 100ms 或使用事件驅動機制

---

## Error Handling

### Current Implementation

```python
try:
    # ... 全部測量邏輯 ...
    return queryValue
except:
    inst.close()
```

**Problems:**
1. **裸 except**: 捕獲所有異常包含 KeyboardInterrupt
2. **無錯誤訊息**: 調用者無法得知失敗原因
3. **返回 None**: 與合法的 0 值無法區分

### Improvement Suggestion

```python
import pyvisa

try:
    # ... 測量邏輯 ...
    return queryValue
except pyvisa.VisaIOError as e:
    print(f"VISA Error: {e}", file=sys.stderr)
    return None
except ValueError as e:
    print(f"Value Error: {e}", file=sys.stderr)
    return None
except Exception as e:
    print(f"Unexpected Error: {e}", file=sys.stderr)
    return None
finally:
    inst.close()
```

---

## Integration Example

### Test Plan CSV Format

```csv
項次,品名規格,上限值,下限值,單位,儀器位置,測試類型,參數
1,Signal Frequency,1100,900,Hz,USB0::0x0699::0x052C::C051741::INSTR,CommandTest,"{'Item': '9', 'Channel': '2'}"
2,Signal Amplitude,3.5,2.5,V,USB0::0x0699::0x052C::C051741::INSTR,CommandTest,"{'Item': '1', 'Channel': '2'}"
3,Rise Time,0.001,0,s,USB0::0x0699::0x052C::C051741::INSTR,CommandTest,"{'Item': '31', 'Channel': '1'}"
```

### Python Integration

```python
from MDO34 import send_cmd_to_instrument, initial
from remote_instrument import instrument_iniSetting

# Initialize
inst_addr = "USB0::0x0699::0x052C::C051741::INSTR"
inst = instrument_iniSetting(inst_addr)

if inst is None:
    print("Instrument initialization failed")
    sys.exit(10)

# Measure frequency on CH2
freq = send_cmd_to_instrument(inst, '9', '2', None)
print(f"Frequency: {freq} Hz")

# Measure amplitude on CH2
ampl = send_cmd_to_instrument(inst, '1', '2', None)
print(f"Amplitude: {ampl} V")

# Cleanup
initial(inst)
inst.close()
```

---

## Performance Characteristics

### Typical Execution Times

| Operation | Duration | Notes |
|-----------|----------|-------|
| Channel Selection | ~100ms | 切換 4 個通道 |
| AutoSet Execution | 2-5s | 視信號複雜度 |
| Measurement Configuration | ~200ms | 設置 MEAS4 |
| Value Query | ~50ms | 查詢測量值 |
| **Total** | **3-6s** | 單次完整測量 |

### Optimization Opportunities

1. **跳過 AutoSet**:
   - 若信號參數已知，手動設置時基和電壓刻度
   - 可節省 2-5 秒

2. **預配置測量**:
   - 在測試計劃開始時配置所有測量類型
   - 執行時僅查詢值

3. **批次測量**:
   - 使用多個測量槽 (MEAS1-MEAS8) 同時測量
   - 單次 AutoSet 後執行多項測量

---

## Supported Instrument Models

### MDO3000 Series

| Model | Bandwidth | Channels | Spectrum Analyzer |
|-------|-----------|----------|-------------------|
| MDO3012 | 100 MHz | 2 | Optional |
| MDO3014 | 100 MHz | 4 | Optional |
| MDO3022 | 200 MHz | 2 | Optional |
| MDO3024 | 200 MHz | 4 | Optional |
| MDO3032 | 350 MHz | 2 | Optional |
| MDO3034 | 350 MHz | 4 | Optional |
| MDO3052 | 500 MHz | 2 | Optional |
| MDO3054 | 500 MHz | 4 | Optional |
| MDO3102 | 1 GHz | 2 | Optional |
| MDO3104 | 1 GHz | 4 | Optional |

**Compatibility:**
- 此驅動適用於所有 MDO3000 系列型號
- 測量功能依儀器選配不同可能有限制

---

## Implementation Notes

### Global Variable Usage

```python
global inst, Channel, MeasType
```

**Issues:**
- 非執行緒安全
- 在多執行緒環境下可能引發競爭條件
- 難以追蹤變數狀態

**Recommendation:**
- 使用類別封裝
- 將參數作為函數參數傳遞

### Unused Imports

```python
import re  # 未使用
```

### Type Parameter Unused

```python
def send_cmd_to_instrument(instrument, cmd, channels, type_=None):
    # type_ 參數未被使用
```

---

## Related Documentation

- **Instrument Manual**: Tektronix MDO3000 Series Programmer Manual
- **SCPI Standard**: IEEE 488.2
- **PyVISA**: https://pyvisa.readthedocs.io/
- **Related Modules**:
  - `remote_instrument.py` - 儀器連接管理
  - `CommandTestMeasurement.py` - 上層測量封裝

---

## Keywords

`Tektronix`, `MDO3000`, `Oscilloscope`, `Mixed Domain`, `SCPI`, `AutoSet`, `Waveform Measurement`, `PyVISA`, `USB Instrument`, `Frequency Measurement`
