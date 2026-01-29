# OPjudgeMeasurement.py Codebase Analysis

## Overview

`OPjudgeMeasurement.py` 是一個視覺判斷測試模組，負責執行需要視覺確認的測試項目。該模組透過外部 Python 腳本進行影像處理和判斷，並將結果記錄到測試框架中。

## Architecture

### Class Hierarchy

```
polish.Measurement (base class)
    ↓
OPjudgeMeasurement (main class)
    ↓
├── MeasureSwitchON (subclass)
└── MeasureSwitchOFF (subclass)

QThread (PySide2)
    ↓
├── MyThread_CW
└── MyThread_CCW
```

## Class Definitions

### 1. OPjudgeMeasurement (Main Class)

**File**: `OPjudgeMeasurement.py:16`

**Purpose**: 執行視覺判斷測試，透過 subprocess 呼叫外部腳本進行影像確認

**Class Constants**:
```python
SWITCH_OPEN = 0
SWITCH_CLOSED = 1
```

### Constructor `__init__()`

**Location**: `OPjudgeMeasurement.py:21-32`

**Parameters**:
- `meas_assets`: 測試資源物件 (passed to base class)
- `test_point`: 測試點名稱 (字串)
- `switch`: 測試模式選擇 ('confirm' 或 'YorN')
- `runAllTest`: 布林值，決定是否在測試失敗後繼續執行
- `TestParams`: 測試參數列表 (通常為 [ImagePath, content])
- `test_results`: 字典，用於存儲測試結果

**Key Operations**:
1. 保存測試結果字典引用
2. 動態設定 `test_point_uids` 為單一測試點 tuple
3. 保存測試模式、全測試標誌和測試參數

### 2. `measure()` Method

**Location**: `OPjudgeMeasurement.py:34-114`

**Purpose**: 執行測試邏輯，根據 `switch_select` 參數決定執行哪種測試模式

#### 2.1 Confirm Mode (`switch_select == 'confirm'`)

**Location**: `OPjudgeMeasurement.py:35-73`

**Workflow**:
1. 記錄測試時間戳 (`TestDateTime`)
2. 檢查必要參數: `ImagePath`, `content`
3. 呼叫外部腳本: `./src/lowsheen_lib/OPjudge_confirm.py`
4. 執行參數: `test_uid`, `TestParams`
5. 將結果存入 `test_points` 和 `test_results`

**External Script Command**:
```python
subprocess.check_output(['python', './src/lowsheen_lib/OPjudge_confirm.py', 
                        str(test_uid), str(self.TestParams)])
```

**Parameter Validation**:
```python
if not any(arg in TestParams_str for arg in required_args):
    missing_args_str = ', '.join(required_args)
    response = f"Error: Missing one of the required arguments in TestParams [{missing_args_str}]"
```

#### 2.2 YorN Mode (`switch_select == 'YorN'`)

**Location**: `OPjudgeMeasurement.py:75-113`

**Workflow**: 與 confirm 模式類似，但呼叫不同的外部腳本

**External Script Command**:
```python
subprocess.check_output(['python', './src/lowsheen_lib/OPjudge_YorN.py', 
                        str(test_uid), str(self.TestParams)])
```

### 3. `teardown()` Method

**Location**: `OPjudgeMeasurement.py:116-120`

**Purpose**: 測試後清理工作 (目前為空實作，僅 sleep 0.5 秒)

**Note**: 包含註解掉的 subprocess 呼叫，可能是舊版清理邏輯

### 4. Subclasses

#### 4.1 MeasureSwitchON

**Location**: `OPjudgeMeasurement.py:123-125`

**Purpose**: 繼承 OPjudgeMeasurement，定義繼電器開啟狀態

**Class Constant**:
```python
relay_state = SWITCH_OPEN  # 0
```

#### 4.2 MeasureSwitchOFF

**Location**: `OPjudgeMeasurement.py:128-129`

**Purpose**: 繼承 OPjudgeMeasurement，定義繼電器關閉狀態

**Class Constant**:
```python
relay_state = SWITCH_CLOSED  # 1
```

### 5. Thread Classes

#### 5.1 MyThread_CW

**Location**: `OPjudgeMeasurement.py:131-138`

**Purpose**: 執行順時針 (Clockwise) 夾具旋轉

**Implementation**:
```python
def run(self):
    subprocess.check_output(['python', './chassis_comms/chassis_fixture_bat.py',
                            '/dev/ttyACM0', '6', '1'])
```

**Parameters**:
- Serial port: `/dev/ttyACM0`
- Command: `6` (CW direction)
- State: `1` (activate)

#### 5.2 MyThread_CCW

**Location**: `OPjudgeMeasurement.py:140-148`

**Purpose**: 執行逆時針 (Counter-Clockwise) 夾具旋轉

**Implementation**:
```python
def run(self):
    subprocess.check_output(['python', './chassis_comms/chassis_fixture_bat.py',
                            '/dev/ttyACM0', '9', '1'])
```

**Parameters**:
- Serial port: `/dev/ttyACM0`
- Command: `9` (CCW direction)
- State: `1` (activate)

## External Dependencies

### Python Libraries

1. **polish**: 測試框架基礎類別
   ```python
   from polish import Measurement
   from polish.util_funcs import make_list
   ```

2. **PySide2**: Qt GUI 框架 (QThread for threading)
   ```python
   from PySide2 import QtWidgets, QtGui, QtCore
   from PySide2.QtCore import *
   from PySide2.QtWidgets import *
   ```

3. **subprocess**: 執行外部腳本
   ```python
   import subprocess
   ```

4. **datetime**: 記錄測試時間戳
   ```python
   import datetime
   ```

5. **time**: 延遲控制
   ```python
   from time import sleep
   ```

### External Scripts

1. **OPjudge_confirm.py** (`src/lowsheen_lib/`)
   - 用途: 執行確認模式的視覺判斷
   - 輸入: test_uid, TestParams
   - 輸出: 判斷結果 (UTF-8 字串)

2. **OPjudge_YorN.py** (`src/lowsheen_lib/`)
   - 用途: 執行 Yes/No 模式的視覺判斷
   - 輸入: test_uid, TestParams
   - 輸出: 判斷結果 (UTF-8 字串)

3. **chassis_fixture_bat.py** (`chassis_comms/`)
   - 用途: 控制測試夾具旋轉
   - 串口: `/dev/ttyACM0`
   - 命令參數:
     - `6`: 順時針 (CW)
     - `9`: 逆時針 (CCW)
     - `1`: 啟動狀態

## Data Flow

### Test Execution Flow

```
Test Init (oneCSV_atlas_2.py)
    ↓
OPjudgeMeasurement.__init__()
    ↓
measure() method
    ↓
Parameter Validation (ImagePath, content)
    ↓
subprocess.check_output() → External Script
    ↓
Response Decoding (UTF-8)
    ↓
test_points.execute(response, runAllTest)
    ↓
test_results[test_point] = response
    ↓
teardown() → Cleanup
```

### Error Handling Flow

```
Exception in subprocess
    ↓
try-except block catches exception
    ↓
Print error message to console
    ↓
response = "Error, stopping test."
    ↓
Execute result with error message
    ↓
Continue based on runAllTest flag
```

## Key Design Patterns

### 1. Dynamic test_point_uids

**Implementation**:
```python
def __init__(self, meas_assets, test_point, switch, runAllTest, TestParams, test_results):
    self.test_point_uids = (test_point, )  # Dynamic single test point
```

**Purpose**: 允許在執行時動態設定測試點，而非在類別定義時固定

### 2. Subprocess Delegation

**Pattern**: 將複雜的影像處理邏輯委派給獨立 Python 腳本

**Benefits**:
- 模組化: 影像處理邏輯與測試框架分離
- 可維護性: 獨立腳本可單獨測試和更新
- 隔離性: 外部腳本錯誤不會直接影響主程式

**Implementation**:
```python
response = subprocess.check_output(['python', './src/lowsheen_lib/OPjudge_confirm.py', 
                                    str(test_uid), str(self.TestParams)])
response = response.decode('utf-8').strip()
```

### 3. Dual Result Storage

**Pattern**: 測試結果同時存儲在兩個位置

1. `test_points[uid].execute(response, runAllTest)` - Framework integration
2. `test_results[uid] = response` - Result dictionary for reporting

**Purpose**: 同時滿足測試框架需求和報告生成需求

### 4. Thread-Based Fixture Control

**Pattern**: 使用 QThread 實作非同步夾具控制

**Benefits**:
- 非阻塞: GUI 保持響應
- 並行: 可同時執行多個旋轉操作
- 獨立: 夾具控制與測試邏輯分離

## Configuration Requirements

### Test Params

External scripts expect TestParams to contain:
- `ImagePath`: 圖片檔案路徑
- `content`: 測試內容/描述

### Test Modes

Two operational modes supported:
1. **'confirm'**: 確認模式 - 執行詳細視覺判斷
2. **'YorN'**: Yes/No 模式 - 執行二元判斷

## Usage Examples

### Creating OPjudgeMeasurement Instance

```python
from OPjudgeMeasurement import OPjudgeMeasurement

test_point = "VisualCheck_01"
switch_mode = "confirm"
run_all_test = True
test_params = ["ImagePath=/path/to/image.jpg", "content=Check for defects"]
test_results = {}

measurement = OPjudgeMeasurement(
    meas_assets=assets,
    test_point=test_point,
    switch=switch_mode,
    runAllTest=run_all_test,
    TestParams=test_params,
    test_results=test_results
)

measurement.measure()
result = test_results[test_point]
print(f"Test result: {result}")
```

### Using Thread Classes

```python
from OPjudgeMeasurement import MyThread_CW, MyThread_CCW

# Create thread instances
cw_thread = MyThread_CW()
ccw_thread = MyThread_CCW()

# Start clockwise rotation
cw_thread.start()

# Wait for completion
cw_thread.wait()

# Start counter-clockwise rotation
ccw_thread.start()
```

## Error Handling

### Parameter Validation

```python
required_args = ['ImagePath', 'content']
if not any(arg in TestParams_str for arg in required_args):
    missing_args_str = ', '.join(required_args)
    response = f"Error: Missing one of the required arguments in TestParams [{missing_args_str}]"
    self.test_points[self.test_point_uids[0]].execute(response, self.runAllTest)
    self.test_results[self.test_point_uids[0]] = response
```

### Subprocess Exception Handling

```python
try:
    response = subprocess.check_output(['python', './src/lowsheen_lib/OPjudge_confirm.py', 
                                        str(test_uid), str(self.TestParams)])
    response = response.decode('utf-8').strip()
except Exception as e:
    print('confirm except 66')
    print("Exception: ", e)
    response = "Error, stopping test."
```

## Best Practices

### 1. Always Validate TestParams

External scripts expect specific parameters. Always validate before execution to prevent cryptic errors.

### 2. Handle Subprocess Failures Gracefully

Subprocess calls can fail for many reasons (missing files, permission issues, script errors). Use try-except blocks to capture errors.

### 3. Use runAllTest Flag Appropriately

- `runAllTest=True`: Continue testing even if this test fails
- `runAllTest=False`: Stop immediately on failure

### 4. Decode Responses Properly

External scripts return bytes. Always decode to UTF-8 and strip whitespace:
```python
response = response.decode('utf-8').strip()
```

## Testing Considerations

### Unit Testing

- Mock subprocess.check_output() to test measure() method without external scripts
- Test parameter validation logic independently
- Test both 'confirm' and 'YorN' modes

### Integration Testing

- Test with actual external scripts
- Verify test_points.execute() is called correctly
- Verify test_results dictionary is populated
- Test error handling with invalid parameters

### Fixture Control Testing

- Test MyThread_CW and MyThread_CCW independently
- Verify serial communication to `/dev/ttyACM0`
- Test thread lifecycle (start, wait, completion)

## Maintenance Notes

### Adding New Test Modes

1. Add new mode check in `measure()` method
2. Create corresponding external script in `src/lowsheen_lib/`
3. Update required_args validation if needed
4. Document the new mode in this file

### Modifying External Scripts

- External scripts should accept `test_uid` and `TestParams` as arguments
- Output should be UTF-8 encoded string
- Script should handle errors and return appropriate error messages

### Thread Safety

- QThread instances are independent and thread-safe
- No shared state between MyThread_CW and MyThread_CCW
- Subprocess calls are blocking within each thread

## Future Improvements

### Potential Enhancements

1. **Async Subprocess**: Use `asyncio.subprocess` for non-blocking external script execution
2. **Timeout Handling**: Add timeout to subprocess calls to prevent hanging
3. **Logging**: Replace print statements with proper logging framework
4. **Config File**: Move serial port and command parameters to config file
5. **Error Codes**: Use structured error codes instead of error strings
6. **Result Validation**: Validate response format from external scripts
7. **Thread Pool**: Use thread pool for multiple fixture operations
8. **Retry Logic**: Add retry mechanism for transient failures

### Code Cleanup

- Remove commented-out code (lines 1-5, 39-64, 77-103, 117, 119)
- Consolidate duplicate code between 'confirm' and 'YorN' modes
- Extract common validation logic into separate method
- Add docstrings to all methods and classes
- Use constants for magic strings ('confirm', 'YorN', 'Error, stopping test.')

## Related Files

- `src/lowsheen_lib/OPjudge_confirm.py`: Confirm mode visual judgment script
- `src/lowsheen_lib/OPjudge_YorN.py`: Yes/No mode visual judgment script
- `chassis_comms/chassis_fixture_bat.py`: Fixture control script
- `polish/Measurement.py`: Base measurement class
- `oneCSV_atlas_2.py`: Test execution engine that calls OPjudgeMeasurement

## Summary

OPjudgeMeasurement.py provides a flexible framework for visual judgment testing in manufacturing environments. It supports two operational modes (confirm and YorN), validates required parameters, delegates complex image processing to external scripts, and provides thread-based fixture control. The module follows key design patterns including dynamic test point assignment, subprocess delegation, dual result storage, and thread-based async operations.

**Key Strengths**:
- Modular design with external script delegation
- Flexible test modes
- Thread-based fixture control
- Comprehensive error handling
- Integration with polish testing framework

**Key Weaknesses**:
- Code duplication between modes
- Lacks proper logging
- No timeout handling
- Commented-out code needs cleanup
- Limited documentation in code
