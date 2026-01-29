# PowerReadMeasurement 與 PowerSetMeasurement 程式碼分析

## 概述

這兩個模組是 PDTool4 測試平台的核心元件，負責與各類儀器進行通訊，執行讀取與設定操作。

## PowerReadMeasurement.py

### 核心結構

- **繼承自**: `polish.Measurement` 基類
- **支援儀器**: 6 種
  - `DAQ973A` - Keysight DAQ973A 數據采集系統
  - `34970A` - Keysight 34970A 數據采集/開關單元
  - `APS7050` - APS7050 電源供應器
  - `MDO34` - Tektronix MDO34 混合域示波器
  - `KEITHLEY2015` - Keithley 2015 音頻分析儀
  - `MT8870A_INF` - Anritsu MT8870A 無線通訊測試儀

### 子類別

```python
class MeasureSwitchON(PowerReadMeasurement):
    relay_state = SWITCH_OPEN  # 未使用

class MeasureSwitchOFF(PowerReadMeasurement):
    relay_state = SWITCH_CLOSED  # 未使用
```

### 初始化參數

```python
def __init__(self, meas_assets, test_point, switch, runAllTest, TestParams, test_results, used_instruments)
```

| 參數 | 說明 |
|------|------|
| `meas_assets` | 測試資源配置 |
| `test_point` | 測試點名稱 |
| `switch` | 儀器類型識別碼 |
| `runAllTest` | 是否全部測試旗標 |
| `TestParams` | 測試參數字典 |
| `test_results` | 測試結果字典 |
| `used_instruments` | 已使用儀器追蹤字典 |

### measure() 方法流程

#### 1. DAQ973A 讀取 (第 37-75 行)

```python
if self.switch_select == 'DAQ973A':
    test_uid = self.test_point_uids
    TestParams = self.TestParams
    
    # 設定測試時間
    self.test_points[self.test_point_uids[0]].TestDateTime = datetime.datetime.utcnow().strftime('%Y%m%d_%H:%M:%S')
    
    # 參數驗證
    required_args = ['Instrument', 'Channel', 'Item', 'Type']
    if "Item=volt" in TestParams or "Item=curr" in TestParams:
        required_args.append('Type')
    
    # 執行儀器腳本
    response = subprocess.check_output(['python', './src/lowsheen_lib/DAQ973A_test.py', 
                                         str(test_uid), str(self.TestParams)])
    
    # 處理回應
    response = response.decode('utf-8')
    response = response.replace('\n','')
    response = response.replace('\r','')
    
    # 記錄結果
    self.test_points[self.test_point_uids[0]].execute(response, self.runAllTest)
    self.test_results[self.test_point_uids[0]] = response
```

**必要參數**:
- `Instrument` - 儀器識別碼
- `Channel` - 通道編號
- `Item` - 讀取項目 (volt/curr)
- `Type` - 測量類型 (當 Item=volt 或 Item=curr 時)

**錯誤處理**:
- returncode 10: "No instrument found"
- 其他: "Error, stopping test."

#### 2. 34970A 讀取 (第 77-115 行)

**必要參數**: `Instrument`, `Channel`, `Item`, `Type` (條件)

**儀器腳本**: `./src/lowsheen_lib/34970A.py`

#### 3. APS7050 讀取 (第 117-154 行)

**特點**:
- 無參數驗證邏輯 (已被註釋掉)
- 無換行符處理

**儀器腳本**: `./src/lowsheen_lib/APS7050.py`

#### 4. MDO34 讀取 (第 156-191 行)

**必要參數**: `Instrument`, `Channel`, `Item`

**儀器腳本**: `./src/lowsheen_lib/MDO34.py`

#### 5. KEITHLEY2015 讀取 (第 193-225 行)

**必要參數**: `Instrument`, `Command`

**儀器腳本**: `./src/lowsheen_lib/Keithley2015.py`

#### 6. MT8870A_INF 讀取 (第 227-262 行)

**必要參數**: `Instrument`, `Item`

**儀器腳本**: `./src/lowsheen_lib/RF_tool/MT8872A_INF.py`

### QThread 輔助類別

```python
class MyThread_CW(QThread):
    def run(self):
        subprocess.check_output(['python', './chassis_comms/chassis_fixture_bat.py', 
                                '/dev/ttyACM0', '6', '1'])

class MyThread_CCW(QThread):
    def run(self):
        subprocess.check_output(['python', './chassis_comms/chassis_fixture_bat.py', 
                                '/dev/ttyACM0', '9', '1'])
```

### teardown() 方法

目前為空實作，僅有 `sleep(0.5)`

---

## PowerSetMeasurement.py

### 核心結構

- **繼承自**: `polish.Measurement`
- **支援儀器**: 9 種
  - `DAQ973A` - Keysight DAQ973A
  - `MODEL2303` - Keysight 2303 雙通道直流電源
  - `MODEL2306` - Keysight 2306 雙通道直流電源
  - `34970A` - Keysight 34970A
  - `DAQ6510` - Keithley DAQ6510
  - `2260B` - Keithley 2260B 直流電源
  - `IT6723C` - ITECH IT6723C 直流電源
  - `PSW3072` - GW Instek PSW3072 可編程直流電源
  - `KEITHLEY2015` - Keithley 2015 音頻分析儀

### 子類別

```python
class MeasureSwitchON(PowerSetMeasurement):
    relay_state = SWITCH_OPEN  # 未使用

class MeasureSwitchOFF(PowerSetMeasurement):
    relay_state = SWITCH_CLOSED  # 未使用
```

### measure() 方法流程

#### 1. DAQ973A 設定 (第 36-77 行)

**必要參數**: `Instrument`, `Channel`, `Item`

**儀器腳本**: `./src/lowsheen_lib/DAQ973A_test.py`

**回應處理**:
```python
if '1' in response:
    response = '1'
else:
    response = '0'
```

#### 2. MODEL2303 設定 (第 79-110 行)

**必要參數**: `Instrument`, `SetVolt`, `SetCurr`

**儀器腳本**: `./src/lowsheen_lib/2303_test.py`

#### 3. MODEL2306 設定 (第 112-143 行)

**必要參數**: `Instrument`, `Channel`, `SetVolt`, `SetCurr`

**儀器腳本**: `./src/lowsheen_lib/2306_test.py`

#### 4. 34970A 設定 (第 145-177 行)

**必要參數**: `Instrument`, `Channel`, `Item`

**儀器腳本**: `./src/lowsheen_lib/34970A.py`

#### 5. DAQ6510 設定 (第 179-210 行)

**必要參數**: `Instrument`, `Channel`, `Item`

**儀器腳本**: `./src/lowsheen_lib/DAQ6510.py`

#### 6. 2260B 設定 (第 212-243 行)

**必要參數**: `Instrument`, `SetVolt`, `SetCurr`

**儀器腳本**: `./src/lowsheen_lib/2260B.py`

#### 7. IT6723C 設定 (第 245-275 行)

**必要參數**: `Instrument`, `SetVolt`, `SetCurr`

**儀器腳本**: `./src/lowsheen_lib/IT6723C.py`

#### 8. PSW3072 設定 (第 277-308 行)

**必要參數**: `Instrument`, `SetVolt`, `SetCurr`

**儀器腳本**: `./src/lowsheen_lib/PSW3072.py`

#### 9. KEITHLEY2015 設定 (第 310-343 行)

**必要參數**: `Instrument`, `Command`

**儀器腳本**: `./src/lowsheen_lib/Keithley2015.py`

---

## 共同架構模式

### 儀器註冊機制

```python
# 追蹤已使用的儀器
if TestParams['Instrument'] not in self.used_instruments:
    self.used_instruments[TestParams['Instrument']] = 'script.py'
```

- 目的: 避免重複初始化儀器
- 格式: `{儀器識別碼: 儀器腳本名稱}`
- 範例: `{'daq973a_1': 'DAQ973A_test.py', 'COM5': 'ComPortCommand.py'}`

### subprocess 執行模式

```python
# 標準調用格式
response = subprocess.check_output([
    'python', 
    './src/lowsheen_lib/script.py', 
    str(test_uid), 
    str(self.TestParams)
])

# 解碼與清理
response = response.decode('utf-8')
response = response.replace('\n', '')
response = response.replace('\r', '')
```

### 結果記錄模式

```python
# 記錄到測試點
self.test_points[self.test_point_uids[0]].execute(response, self.runAllTest)

# 記錄到結果字典
self.test_results[self.test_point_uids[0]] = response
```

### 錯誤處理模式

```python
try:
    response = subprocess.check_output([...])
    # 處理回應
except subprocess.CalledProcessError as e:
    if e.returncode == 10:
        response = "No instrument found"
    else:
        print("subprocess.CalledProcessError:", e)
        response = "Error, stopping test."
    
    self.test_points[self.test_point_uids[0]].execute(response, self.runAllTest)
    self.test_results[self.test_point_uids[0]] = response
```

**標準錯誤代碼**:
- `returncode 10`: 儀器未找到
- 其他: 執行錯誤

---

## 比較差異

| 項目 | PowerReadMeasurement | PowerSetMeasurement |
|------|---------------------|---------------------|
| 儀器數量 | 6 種 | 9 種 |
| 回應處理 | 直接返回原始值 (或去除換行符) | 統一轉換為 '1' 或 '0' |
| 共同儀器 | DAQ973A, 34970A, KEITHLEY2015 | DAQ973A, 34970A, KEITHLEY2015 |
| 電源類儀器 | APS7050 (讀取) | MODEL2303, MODEL2306, 2260B, IT6723C, PSW3072 |
| 類比儀器 | MDO34, MT8870A_INF | DAQ6510 |
| 參數驗證 | 完整 | 完整 |

---

## 儀器腳本位置

| 儀器 | PowerRead | PowerSet |
|------|-----------|----------|
| DAQ973A | `src/lowsheen_lib/DAQ973A_test.py` | `src/lowsheen_lib/DAQ973A_test.py` |
| 34970A | `src/lowsheen_lib/34970A.py` | `src/lowsheen_lib/34970A.py` |
| APS7050 | `src/lowsheen_lib/APS7050.py` | - |
| MDO34 | `src/lowsheen_lib/MDO34.py` | - |
| KEITHLEY2015 | `src/lowsheen_lib/Keithley2015.py` | `src/lowsheen_lib/Keithley2015.py` |
| MT8870A_INF | `src/lowsheen_lib/RF_tool/MT8872A_INF.py` | - |
| MODEL2303 | - | `src/lowsheen_lib/2303_test.py` |
| MODEL2306 | - | `src/lowsheen_lib/2306_test.py` |
| DAQ6510 | - | `src/lowsheen_lib/DAQ6510.py` |
| 2260B | - | `src/lowsheen_lib/2260B.py` |
| IT6723C | - | `src/lowsheen_lib/IT6723C.py` |
| PSW3072 | - | `src/lowsheen_lib/PSW3072.py` |

---

## 測試參數範例

### 電源設定參數
```python
{
    'Instrument': 'MODEL2303',
    'SetVolt': '12.0',
    'SetCurr': '2.5'
}
```

### 讀取參數
```python
{
    'Instrument': 'DAQ973A',
    'Channel': '101',
    'Item': 'volt',
    'Type': 'DCV'
}
```

### 命令參數
```python
{
    'Instrument': 'KEITHLEY2015',
    'Command': '*RST'
}
```

---

## Chassis 通訊

### Fixture 控制腳本
```bash
python ./chassis_comms/chassis_fixture_bat.py <串口> <命令> <參數>
```

**QThread 類別用途**:
- `MyThread_CW`: 順時針控制 (`/dev/ttyACM0`, '6', '1')
- `MyThread_CCW`: 逆時針控制 (`/dev/ttyACM0`, '9', '1')

---

## 注意事項

1. **時間戳記**: 使用 UTC 時間格式 `YYYYMMDD_HH:MM:SS`
2. **子進程調用**: 使用 `subprocess.check_output()` 確保腳本執行成功
3. **錯誤處理**: 必須處理 `CalledProcessError` 並區分 returncode
4. **儀器初始化**: 僅在首次使用時註冊到 `used_instruments`
5. **回應格式**: 
   - PowerRead: 原始測量值 (字串)
   - PowerSet: '1' (成功) 或 '0' (失敗)
6. **參數驗證**: 缺少必要參數時立即返回錯誤信息
7. **測試點**: 使用動態 `test_point_uids` 單一測點模式

---

## 代碼改進建議

1. **APS7050 參數驗證**: 恢復被註釋的參數驗證邏輯
2. **回應處理統一**: PowerRead 可考慮統一回應格式
3. **錯誤處理**: 可增加更詳細的錯誤日誌
4. **teardown 實作**: 補充實際清理邏輯
5. **QThread 用途**: MyThread_CW/CCW 應添加文檔說明使用場景
6. **Magic Numbers**: 錯誤代碼 10 應定義為常量
