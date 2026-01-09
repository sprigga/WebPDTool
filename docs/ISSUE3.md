# ISSUE3: Invalid parameters 錯誤修正報告

## 問題描述

### 錯誤現象
- **錯誤訊息**: `Invalid parameters: []`
- **發生位置**: 前端點擊"開始測試"後,系統執行測試項目時
- **影響範圍**: 所有使用 `case_type` (如 `console`, `comport`, `tcpip`) 的測試項目無法執行
- **具體案例**:
  - `arduino` 測試項目 (case_type='comport'): 執行 `python /app/scripts/hello_world.py` 失敗
  - `123_1` 測試項目 (case_type='console'): 執行 `python ./scripts/test123.py` 失敗

### 執行流程
```
用戶點擊"開始測試"
  ↓
handleStartTest() [TestMain.vue]
  ↓
createTestSession() → POST /api/tests/sessions
  ↓
前端直接執行 executeMeasurements() [TestMain.vue]
  ↓
executeSingleItem() → POST /api/measurements/execute
  ↓
measurement_service.execute_single_measurement()
  ↓
validate_params() → ❌ 返回 "Invalid parameters: []"
```

---

## 根本原因分析

### 問題 1: measurement_type 和 switch_mode 相同時的邏輯錯誤

**位置**: `backend/app/services/measurement_service.py:610-690`

**原因詳解**:
- 前端使用 `case_type` (如 `console`, `comport`) 同時作為 `measurement_type` 和 `switch_mode`
- 當 `measurement_type` == `switch_mode` (例如都是 `'console'`) 時:
  - **錯誤行為**: 後端嘗試執行預設腳本 `ConSoleCommand.py`
  - **正確行為**: 應該直接執行 `command` 參數中的腳本 (如 `python ./scripts/test123.py`)
- 因為預設腳本 `ConSoleCommand.py` 不存在,導致執行失敗

**資料庫資料實例**:
```python
# test_plans 表中的測試項目
{
    "item_no": 3,
    "item_name": "123_1",
    "test_type": "command",
    "case_type": "console",
    "command": "python ./scripts/test123.py",
    "parameters": {
        "command": "python ./scripts/test123.py",
        "timeout": 5000,
        "eq_limit": "123",
        ...
    }
}

# 前端傳遞的 API 參數
{
    "measurement_type": "console",  # 使用 case_type
    "switch_mode": "console",       # 使用 case_type
    "test_params": {
        "command": "python ./scripts/test123.py",
        ...
    }
}
```

**修正方案**:
```python
# 新增判斷邏輯: measurement_type == switch_mode 時,直接執行 command
use_default_script = (
    switch_mode in script_config and
    (measurement_type in ["CommandTest", "command"] or measurement_type != switch_mode)
)

if use_default_script:
    # 使用預設腳本 (如 ComPortCommand.py)
    ...
else:
    # 直接執行 command 參數中的腳本
    ...
```

---

### 問題 2: measurement_dispatch 缺少 case_type 映射

**位置**: `backend/app/services/measurement_service.py:36-60`

**原因詳解**:
- `measurement_dispatch` 字典定義了測量類型到執行函數的映射
- 原本只包含:
  ```python
  {
      "CommandTest": self._execute_command_test,
      "command": self._execute_command_test,
      ...
  }
  ```
- 前端使用 `case_type` (如 `'console'`, `'comport'`) 作為 `measurement_type` 時
- 系統無法找到對應的執行器,返回 "Unknown measurement type"

**修正方案**:
```python
self.measurement_dispatch = {
    ...
    # 新增: 直接支援 case_type 作為 measurement_type
    "comport": self._execute_command_test,
    "console": self._execute_command_test,
    "tcpip": self._execute_command_test,
    "android_adb": self._execute_command_test,
    "PEAK": self._execute_command_test,
    ...
}
```

---

### 問題 3: validation_rules 缺少 case_type 規則

**位置**: `backend/app/services/measurement_service.py:1567-1631`

**原因詳解**:
- `validate_params()` 函數使用 `validation_rules` 來驗證參數
- 原本只定義了 `"CommandTest"` 和 `"command"` 的規則:
  ```python
  validation_rules = {
      "CommandTest": {
          "comport": ["Port", "Baud", "Command"],
          "console": ["Command"],
          ...
      },
      "command": {
          "comport": ["Port", "Baud", "Command"],
          "console": ["Command"],
          ...
      }
  }
  ```
- 當 `measurement_type='console'` 時,找不到對應的驗證規則
- 系統返回 "Unknown measurement type: console"

**修正方案**:
```python
validation_rules = {
    ...
    # 新增: 直接支援 case_type 作為 measurement_type
    "comport": {
        "comport": ["Port", "Baud", "Command"],
        "custom": ["command"],  # 支援自定義腳本
    },
    "console": {
        "console": ["Command"],
        "custom": ["command"],
    },
    "tcpip": {
        "tcpip": ["Host", "Port", "Command"],
        "custom": ["command"],
    },
    ...
}
```

---

### 問題 4: _execute_command_test 需要知道 measurement_type

**位置**: `backend/app/services/measurement_service.py:567-586`

**原因詳解**:
- `_execute_command_test()` 函數需要判斷是否使用預設腳本
- 判斷邏輯需要知道 `measurement_type` 參數
- 但函數原本沒有這個參數:
  ```python
  async def _execute_command_test(
      self,
      test_point_id: str,
      switch_mode: str,
      test_params: Dict[str, Any],
      run_all_test: bool,
      # ❌ 缺少 measurement_type 參數
  )
  ```

**修正方案**:
```python
# 1. 新增參數
async def _execute_command_test(
    self,
    test_point_id: str,
    switch_mode: str,
    test_params: Dict[str, Any],
    run_all_test: bool,
    measurement_type: str = "CommandTest",  # ✅ 新增
)

# 2. 動態傳入參數
import inspect
sig = inspect.signature(executor)
kwargs = {
    "test_point_id": test_point_id,
    "switch_mode": switch_mode,
    "test_params": test_params,
    "run_all_test": run_all_test,
}
if "measurement_type" in sig.parameters:
    kwargs["measurement_type"] = measurement_type
result = await executor(**kwargs)
```

---

## 修正內容

### 1. measurement_dispatch 更新

**檔案**: `backend/app/services/measurement_service.py`
**行數**: 36-60

**修改前**:
```python
self.measurement_dispatch = {
    "PowerSet": self._execute_power_set,
    "PowerRead": self._execute_power_read,
    "CommandTest": self._execute_command_test,
    "command": self._execute_command_test,
    "SFCtest": self._execute_sfc_test,
    "URL": self._execute_sfc_test,
    "webStep1_2": self._execute_sfc_test,
    "getSN": self._execute_get_sn,
    "OPjudge": self._execute_op_judge,
    "wait": self._execute_wait,
    "Wait": self._execute_wait,
    "Other": self._execute_other,
    "Final": self._execute_final,
}
```

**修改後**:
```python
self.measurement_dispatch = {
    "PowerSet": self._execute_power_set,
    "PowerRead": self._execute_power_read,
    "CommandTest": self._execute_command_test,
    "command": self._execute_command_test,
    "SFCtest": self._execute_sfc_test,
    "URL": self._execute_sfc_test,
    "webStep1_2": self._execute_sfc_test,
    # ✅ 新增: 直接支援 case_type 作為 measurement_type
    "comport": self._execute_command_test,
    "console": self._execute_command_test,
    "tcpip": self._execute_command_test,
    "android_adb": self._execute_command_test,
    "PEAK": self._execute_command_test,
    "getSN": self._execute_get_sn,
    "OPjudge": self._execute_op_judge,
    "wait": self._execute_wait,
    "Wait": self._execute_wait,
    "Other": self._execute_other,
    "Final": self._execute_final,
}
```

---

### 2. validation_rules 更新

**檔案**: `backend/app/services/measurement_service.py`
**行數**: 1567-1631

**新增內容**:
```python
validation_rules = {
    "CommandTest": { ... },
    "command": { ... },
    # ✅ 新增: 直接支援 case_type 作為 measurement_type
    "comport": {
        "comport": ["Port", "Baud", "Command"],
        "custom": ["command"],  # 支援自定義腳本
    },
    "console": {
        "console": ["Command"],
        "custom": ["command"],
    },
    "tcpip": {
        "tcpip": ["Host", "Port", "Command"],
        "custom": ["command"],
    },
    "android_adb": {
        "android_adb": ["Command"],
        "custom": ["command"],
    },
    "PEAK": {
        "PEAK": ["Command"],
        "custom": ["command"],
    },
    "SFCtest": { ... },
    ...
}
```

---

### 3. use_default_script 判斷邏輯

**檔案**: `backend/app/services/measurement_service.py`
**行數**: 610-690

**新增邏輯**:
```python
# ✅ 新增: 當 measurement_type == switch_mode 時,視為「直接執行 command」模式
use_default_script = (
    switch_mode in script_config and
    # 如果 measurement_type 不是 CommandTest/command,則使用預設腳本
    # 例如: measurement_type='CommandTest', switch_mode='comport' -> 使用 ComPortCommand.py
    # 但: measurement_type='console', switch_mode='console' -> 直接執行 command
    (measurement_type in ["CommandTest", "command"] or measurement_type != switch_mode)
)

if use_default_script:
    # 執行預設腳本 (如 ComPortCommand.py, ConSoleCommand.py)
    ...
else:
    # 直接執行 command 參數中的腳本
    ...
```

---

### 4. _execute_command_test 函數簽名更新

**檔案**: `backend/app/services/measurement_service.py`
**行數**: 567-586

**修改前**:
```python
async def _execute_command_test(
    self,
    test_point_id: str,
    switch_mode: str,
    test_params: Dict[str, Any],
    run_all_test: bool,
) -> MeasurementResult:
```

**修改後**:
```python
async def _execute_command_test(
    self,
    test_point_id: str,
    switch_mode: str,
    test_params: Dict[str, Any],
    run_all_test: bool,
    measurement_type: str = "CommandTest",  # ✅ 新增: 用於判斷是否使用預設腳本
) -> MeasurementResult:
```

---

### 5. 動態傳入 measurement_type 參數

**檔案**: `backend/app/services/measurement_service.py`
**行數**: 117-148

**新增程式碼**:
```python
# Execute measurement
executor = self.measurement_dispatch[measurement_type]

# ✅ 新增: 動態判斷是否需要傳入 measurement_type
import inspect
sig = inspect.signature(executor)
kwargs = {
    "test_point_id": test_point_id,
    "switch_mode": switch_mode,
    "test_params": test_params,
    "run_all_test": run_all_test,
}

# 如果 executor 接受 measurement_type 參數,則傳入
if "measurement_type" in sig.parameters:
    kwargs["measurement_type"] = measurement_type

result = await executor(**kwargs)
```

---

### 6. validate_params 更新

**檔案**: `backend/app/services/measurement_service.py`
**行數**: 1603-1760

**修改內容**:
```python
# ✅ 擴展支援的測量類型
command_test_types = ["CommandTest", "command", "comport", "console", "tcpip", "android_adb", "PEAK"]

# ✅ 對於自定義 switch_mode,支援 case-insensitive 參數檢查
if measurement_type in command_test_types:
    if not has_parameter("command") and not has_parameter("script_path"):
        return { "valid": False, ... }
    else:
        return { "valid": True, ... }
```

---

## 驗證結果

### 測試案例 1: arduino (comport)

**資料庫資料**:
```python
{
    "item_no": 1,
    "item_name": "arduino",
    "test_type": "command",
    "case_type": "comport",
    "command": "python /app/scripts/hello_world.py",
    "limit_type": "partial",
    "eq_limit": "Hello World!"
}
```

**API 請求**:
```python
{
    "measurement_type": "comport",
    "switch_mode": "comport",
    "test_params": {
        "command": "python /app/scripts/hello_world.py",
        ...
    }
}
```

**執行結果**:
```
✅ PASS
```

**實際執行**:
```bash
python /app/scripts/hello_world.py
```

---

### 測試案例 2: 123_1 (console)

**資料庫資料**:
```python
{
    "item_no": 3,
    "item_name": "123_1",
    "test_type": "command",
    "case_type": "console",
    "command": "python ./scripts/test123.py",
    "timeout": 5000,
    "limit_type": "partial",
    "eq_limit": "123"
}
```

**API 請求**:
```python
{
    "measurement_type": "console",
    "switch_mode": "console",
    "test_params": {
        "command": "python ./scripts/test123.py",
        "timeout": 5000,
        ...
    }
}
```

**執行結果**:
```
✅ PASS
```

**實際執行**:
```bash
python ./scripts/test123.py
```

---

## 預期效果

修正後,當用戶點擊"開始測試"時:

1. ✅ **不再出現 "Invalid parameters: []" 錯誤**
   - 參數驗證支援 `comport`, `console`, `tcpip` 等 case_type

2. ✅ **正確執行測試腳本**
   - `arduino` 測試項目能正確執行 `python /app/scripts/hello_world.py`
   - `123_1` 測試項目能正確執行 `python ./scripts/test123.py`

3. ✅ **測試結果正確驗證**
   - 根據 `eq_limit` 驗證輸出
   - 返回正確的 PASS/FAIL 結果

4. ✅ **支援多種測試模式**
   - case_type 直接作為 measurement_type 的模式
   - CommandTest + switch_mode 的傳統模式
   - 自定義腳本模式 (custom switch_mode)

5. ✅ **Log 輸出正確**
   - Backend log 顯示測試執行狀態
   - 不再出現 "ConSoleCommand.py not found" 錯誤

---

## 相關檔案

### 修改的檔案
1. `backend/app/services/measurement_service.py`
   - measurement_dispatch 更新 (36-60)
   - validation_rules 更新 (1567-1631)
   - _execute_command_test 函數簽名更新 (567-586)
   - use_default_script 邏輯新增 (610-690)
   - 動態參數傳入 (117-148)
   - validate_params 更新 (1603-1760)

### 相關檔案 (未修改但相關)
2. `backend/app/services/test_engine.py`
   - 參數提取邏輯已在之前修正
   - 支援 case_type 優先於 test_type

3. `backend/app/measurements/implementations.py`
   - CommandTestMeasurement 和 WaitMeasurement 已在之前修正
   - 支援完整的參數讀取

4. `frontend/src/views/TestMain.vue`
   - executeSingleItem 函數構建 API 請求
   - 使用 case_type 作為 measurement_type 和 switch_mode

---

## 總結

本次修正解決了前端使用 `case_type` 作為 `measurement_type` 時的參數驗證和執行問題:

1. **根本原因**: 系統原本設計為使用 `CommandTest` 作為 measurement_type,搭配 switch_mode 指定通信方式
2. **實際情況**: 前端直接使用 `case_type` (如 `console`, `comport`) 作為 measurement_type
3. **修正方向**: 擴展系統以支援 case_type 直接作為 measurement_type 的模式
4. **關鍵改進**:
   - 新增 case_type 到 measurement_dispatch 和 validation_rules
   - 修正 _execute_command_test 的執行邏輯判斷
   - 支援 case-insensitive 參數查找

修正後系統完全相容前端的實現方式,所有測試項目都能正確執行。
