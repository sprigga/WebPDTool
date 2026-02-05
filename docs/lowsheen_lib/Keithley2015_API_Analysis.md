# Keithley 2015 API Analysis

## Overview

Keithley 2015 是 THD 音頻分析儀的驅動程序，提供多功能測量（THD、電壓、電流、電阻等）和信號輸出功能。

**檔案位置**: `src/lowsheen_lib/Keithley2015.py`
**儀器類型**: THD Audio Analyzer / Multimeter
**通訊協議**: SCPI (IEEE 488.2)
**連接介面**: GPIB

---

## Architecture

### Module Dependencies

```
Keithley2015.py
├── pyvisa                                    # VISA 通訊
├── remote_instrument.instrument_iniSetting  # 儀器初始化
├── sys, ast                                  # 參數解析
└── re                                        # 正則表達式 (科學記號處理)
```

### State Machine

```
Initial State
    ├── RST (State='0')        → Reset & IDN Query
    ├── Read Mode (State='1')  → Measurement Execution
    │   ├── Mode Selection (THD/THDN/SINAD)
    │   ├── Type Selection (Voltage/Current/Distortion/etc.)
    │   └── Frequency Setting (Auto/Manual)
    └── Output Mode (State='2') → Signal Generator Control
        ├── Output ON/OFF
        ├── Frequency Setting
        ├── Amplitude Setting
        ├── Impedance Setting (50Ω/600Ω/HIZ)
        └── Shape Selection (Inverted Sine/Pulse)
```

---

## Configuration Class: `conf`

定義儀器參數的映射表，將數字代碼轉換為 SCPI 命令。

### `conf.Mode`
THD 測量模式映射

| Code | SCPI Command | Description |
|------|--------------|-------------|
| '1' | `THD` | Total Harmonic Distortion |
| '2' | `THDN` | THD + Noise |
| '3' | `SINAD` | Signal-to-Noise and Distortion |

### `conf.Type`
測量類型映射

| Code | SCPI Command | Description |
|------|--------------|-------------|
| '1' | `DISTortion` | 失真測量 |
| '2' | `VOLTage:DC` | 直流電壓 |
| '3' | `VOLTage:AC` | 交流電壓 |
| '4' | `CURRent:DC` | 直流電流 |
| '5' | `CURRent:AC` | 交流電流 |
| '6' | `RESistance` | 2 線電阻 |
| '7' | `FRESistance` | 4 線電阻 |
| '8' | `PERiod` | 週期 |
| '9' | `FREQuency` | 頻率 |
| '10' | `TEMPerature` | 溫度 |
| '11' | `DIODe` | 二極體測試 |
| '12' | `CONTinuity` | 導通性測試 |

### `conf.Impd`
輸出阻抗映射

| Code | SCPI Command | Description |
|------|--------------|-------------|
| '1' | `OHM50` | 50 Ω |
| '2' | `OHM600` | 600 Ω |
| '3' | `HIZ` | High Impedance (>10 kΩ) |

### `conf.Shape`
輸出波形形狀映射

| Code | SCPI Command | Description |
|------|--------------|-------------|
| '1' | `ISINE` | Inverted Sine Wave |
| '2' | `PULSE` | Pulse Waveform |

---

## API Reference

### 1. `Parameter(command)`

解析命令列參數並設置全域變數。

**Parameters:**
- `command` (list[str]): 命令參數列表

**Global Variables Set:**
- `RST` (bool): Reset 旗標
- `State` (str): 操作模式 ('0'=RST, '1'=Read, '2'=Output)
- `Read_Mode` (str): THD 測量模式 (僅 State='1')
- `Read_Type` (str): 測量類型 (僅 State='1')
- `Read_Freq` (str): 測量頻率設置 (僅 State='1')
- `Out_Mode` (str): 輸出開關 (僅 State='2')
- `Out_Freq` (str): 輸出頻率 (僅 State='2')
- `Out_Impd` (str): 輸出阻抗 (僅 State='2')
- `Out_AMPL` (str): 輸出振幅 (僅 State='2')
- `Out_Shape` (str): 輸出波形 (僅 State='2', 選用)

**Command Structure:**

**Reset Mode (State='0'):**
```python
command = ['0']
# RST = True
```

**Read Mode (State='1'):**
```python
command = [State, Mode, Type, Frequency]
# Example: ['1', '1', '1', '1000']  # THD, Distortion, 1000Hz
# Example: ['1', '2', '3', '0']     # THDN, AC Voltage, Auto Frequency
```

**Output Mode (State='2'):**
```python
command = [State, Output, Freq, Ampl, Impd, Shape(optional)]
# Example: ['2', '1', '1000', '1', '1', '1']  # ON, 1000Hz, 1V, 50Ω, Inverted Sine
# Example: ['2', '0']                         # OFF
```

---

### 2. `Measment()`

執行測量操作並格式化結果輸出。

**Returns:**
- `None` (結果透過 `print()` 輸出)

**Output Format:**
- 格式化的測量值字串 (移除換行符號)
- 使用 `format_scientific_notation()` 進行格式化

**Execution Flow:**
```python
1. inst.write(":DIST:TYPE " + Read_Mode)      # 設置 THD 模式
2. inst.write("func '" + Read_Type + "'")     # 設置測量類型
3. inst.write(":DIST:FREQ" + Read_Freq)       # 設置頻率 (或 AUTO)
4. inst.write('INIT')                         # 觸發測量
5. thd_result = inst.query('READ?')           # 讀取結果
6. print(formatted_str, end='')               # 輸出格式化結果
```

**Example:**
```python
# 內部執行流程
inst.write(":DIST:TYPE THD")
inst.write("func 'DISTortion'")
inst.write(":DIST:FREQ:AUTO ON")
inst.write('INIT')
result = inst.query('READ?')  # 返回: "+1.234567E-02\n"
# 輸出: "0.01235" (格式化後)
```

---

### 3. `Output()`

控制信號輸出功能。

**Returns:**
- `None` (結果透過 `print()` 輸出)

**Output:**
- 輸出模式狀態訊息: `"Output Mode:On"` 或 `"Output Mode:Off"`
- 固定返回值: `1` (透過 `print(1, end='')`)

**Execution Flow:**
```python
1. inst.write("OUTP " + Out_Mode)             # ON/OFF
2. if ON:
   - inst.write("OUTP:FREQ " + Out_Freq)      # 設置頻率
   - inst.write("OUTP:IMP " + Out_Impd)       # 設置阻抗
   - inst.write("OUTP:AMPL " + Out_AMPL)      # 設置振幅
   - inst.write("OUTP:CHANnel2 " + Out_Shape) # 設置波形
3. thd_result = inst.query('OUTP?')           # 查詢狀態
4. print("Output Mode:On/Off")                # 輸出狀態
5. print(1, end='')                           # 返回成功標誌
```

**Example:**
```python
# 啟用輸出: 1kHz, 1V, 50Ω, Inverted Sine
inst.write("OUTP 1")
inst.write("OUTP:FREQ 1000")
inst.write("OUTP:IMP OHM50")
inst.write("OUTP:AMPL 1")
inst.write("OUTP:CHANnel2 ISINE")
# Output: "Output Mode:On\n1"
```

---

### 4. `Reset()`

重置儀器並查詢識別資訊。

**Returns:**
- `None` (透過 `print()` 輸出 IDN 字串)

**Execution:**
```python
IDN_string = inst.query('*IDN?')  # 例: "KEITHLEY INSTRUMENTS INC.,MODEL 2015,..."
print(IDN_string, end='')
inst.write('*RST')                # 重置儀器至預設狀態
```

---

### 5. `send_cmd_to_instrument(instrument, command)`

主要執行函數，根據命令狀態路由到對應功能。

**Parameters:**
- `instrument` (pyvisa.Resource): PyVISA 儀器物件
- `command` (list[str]): 命令參數列表

**Returns:**
- `None` (結果透過各子函數輸出)

**Execution Flow:**
```python
1. Parameter(command)       # 解析命令
2. if RST == True:
       Reset()              # 重置模式
   elif State == '1':
       Measment()           # 測量模式
   elif State == '2':
       Output()             # 輸出模式
3. Close()                  # 關閉連接
```

---

### 6. `initial(instrument)`

清理函數，執行儀器重置。

**Parameters:**
- `instrument` (pyvisa.Resource): PyVISA 儀器物件

**Returns:**
- `None`

**Behavior:**
```python
instrument.write('*RST')  # IEEE 488.2 標準重置命令
```

---

## Utility Functions

### 7. `format_scientific_notation(scientific_str)`

格式化科學記號為易讀的十進制格式。

**Parameters:**
- `scientific_str` (str): 科學記號字串 (例: `"+1.234567E-02"`)

**Returns:**
- `str`: 格式化後的字串 (例: `"0.01235"`)

**Formatting Rules:**
- 負指數 (`e-`): 使用動態小數位數 (指數值 + 2)
- 正指數或無指數: 固定 3 位小數
- 自動調用 `extract_exponent()` 提取指數值

**Example:**
```python
format_scientific_notation("+1.234567E-02")  # → "0.01235"
format_scientific_notation("+1.234567E+01")  # → "12.346"
format_scientific_notation("0.123456")       # → "0.123"
```

---

### 8. `extract_exponent(scientific_str)`

從科學記號字串中提取指數值。

**Parameters:**
- `scientific_str` (str): 科學記號或浮點數字串

**Returns:**
- `int`: 指數值 (負數表示小數，正數表示整數倍)

**Extraction Logic:**
1. 使用正則表達式匹配 `e-` 或 `E-`
2. 若無科學記號，計算小數點後前導零數量

**Example:**
```python
extract_exponent("1.234E-03")  # → -3
extract_exponent("0.000123")   # → 4 (4個前導零)
extract_exponent("123.45")     # → 0
```

---

## Command Line Interface

### Usage Pattern

```bash
uv run python Keithley2015.py <sequence> <args_dict>
```

### Parameters

**sequence** (str):
- `--final`: 執行 `initial()` 重置
- 其他值: 執行 `send_cmd_to_instrument()`

**args_dict** (str): Python 字典格式字串
- `Instrument` (str): 儀器 GPIB 地址 (例: `"GPIB0::16::INSTR"`)
- `Command` (str): 空格分隔的命令參數 (例: `"1 1 1 1000"`)

### Examples

#### Reset Mode
```bash
uv run python Keithley2015.py normal "{'Instrument': 'GPIB0::16::INSTR', 'Command': '0'}"
# Output: KEITHLEY INSTRUMENTS INC.,MODEL 2015,...
```

#### THD Measurement (1kHz, Auto)
```bash
uv run python Keithley2015.py normal "{'Instrument': 'GPIB0::16::INSTR', 'Command': '1 1 1 0'}"
# Output: 0.01234 (formatted THD value)
```

#### AC Voltage Measurement (1kHz)
```bash
uv run python Keithley2015.py normal "{'Instrument': 'GPIB0::16::INSTR', 'Command': '1 2 3 1000'}"
# Output: 1.234 (formatted voltage)
```

#### Enable Output (1kHz, 1V, 50Ω)
```bash
uv run python Keithley2015.py normal "{'Instrument': 'GPIB0::16::INSTR', 'Command': '2 1 1000 1 1 1'}"
# Output: Output Mode:On
#         1
```

#### Disable Output
```bash
uv run python Keithley2015.py normal "{'Instrument': 'GPIB0::16::INSTR', 'Command': '2 0'}"
# Output: Output Mode:Off
#         1
```

#### Final Cleanup
```bash
uv run python Keithley2015.py --final "{'Instrument': 'GPIB0::16::INSTR'}"
# (執行 *RST 重置)
```

---

## SCPI Commands Reference

### Measurement Commands

| SCPI Command | Description | Parameter |
|--------------|-------------|-----------|
| `:DIST:TYPE {mode}` | 設置失真測量模式 | THD, THDN, SINAD |
| `func '{type}'` | 設置測量功能 | DISTortion, VOLTage:DC, etc. |
| `:DIST:FREQ {freq}` | 設置測量頻率 | 數值 (Hz) |
| `:DIST:FREQ:AUTO ON` | 自動頻率偵測 | - |
| `INIT` | 觸發測量 | - |
| `READ?` | 讀取測量結果 | 返回科學記號格式 |

### Output Commands

| SCPI Command | Description | Parameter |
|--------------|-------------|-----------|
| `OUTP {state}` | 輸出控制 | 1 (ON), 0 (OFF) |
| `OUTP:FREQ {freq}` | 輸出頻率 | 10-20000 Hz |
| `OUTP:IMP {impd}` | 輸出阻抗 | OHM50, OHM600, HIZ |
| `OUTP:AMPL {ampl}` | 輸出振幅 | 0-4V (HIZ), 0-2V (50Ω/600Ω) |
| `OUTP:CHANnel2 {shape}` | 波形形狀 | ISINE, PULSE |
| `OUTP?` | 查詢輸出狀態 | 返回 1 或 0 |

### Standard Commands

| SCPI Command | Description |
|--------------|-------------|
| `*IDN?` | 查詢儀器識別資訊 |
| `*RST` | 重置儀器至預設狀態 |

---

## Help System

### `help()`

輸出完整的 API 使用說明。

**Output Content:**
1. 參數索引說明 (Index, Address, State)
2. Read Mode 參數詳細說明
3. Output Mode 參數詳細說明
4. 使用範例

**Usage:**
```python
help()
# 輸出多行使用說明
```

---

## Error Handling

### Exit Codes
- `sys.exit(10)`: 儀器初始化失敗

### Potential Issues
1. **No Error Checking in Measurement**
   - `Measment()` 使用 `try-except` 但僅關閉連接
   - 未返回錯誤訊息給調用者

2. **Output Mode Always Returns 1**
   - 即使設置失敗也會輸出成功標誌
   - 僅檢查最終狀態但未驗證參數設置

3. **Frequency Auto Detection**
   - `Read_Freq == '0'` 觸發自動模式
   - 未處理非數值輸入錯誤

---

## Integration Example

### Test Plan CSV Format

```csv
項次,品名規格,上限值,下限值,單位,儀器位置,測試類型,參數
1,THD Measurement,0.05,0,%, GPIB0::16::INSTR,CommandTest,"{'Command': '1 1 1 1000'}"
2,AC Voltage,5.5,4.5,V,GPIB0::16::INSTR,CommandTest,"{'Command': '1 2 3 0'}"
```

### Python Integration

```python
from Keithley2015 import send_cmd_to_instrument, initial
from remote_instrument import instrument_iniSetting

# Initialize
inst = instrument_iniSetting("GPIB0::16::INSTR")

# Measurement
command = ['1', '1', '1', '1000']  # THD, Distortion, 1kHz
send_cmd_to_instrument(inst, command)
# Output: 0.01234

# Cleanup
initial(inst)
inst.close()
```

---

## Implementation Notes

### Global Variables
- 使用全域變數儲存解析後的參數
- 在多執行緒環境下可能引發競爭條件
- 建議改用類別封裝或返回值傳遞

### Output Handling
- 使用 `print(..., end='')` 避免額外換行
- 結果透過標準輸出傳遞給父程序
- 調用者需解析字串輸出

### Format Precision
- 動態調整小數位數根據科學記號指數
- 可能過度格式化導致精度損失
- 建議保留原始科學記號供後續處理

---

## Related Documentation

- **Instrument Manual**: Keithley 2015 User Manual
- **SCPI Standard**: IEEE 488.2
- **PyVISA**: https://pyvisa.readthedocs.io/
- **Related Modules**:
  - `remote_instrument.py` - 儀器連接管理
  - `CommandTestMeasurement.py` - 上層測量封裝

---

## Keywords

`Keithley 2015`, `THD Analyzer`, `Audio Measurement`, `SCPI`, `GPIB`, `Distortion`, `Signal Generator`, `PyVISA`, `Multimeter`
