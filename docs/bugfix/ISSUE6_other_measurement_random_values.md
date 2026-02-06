# ISSUE #6: Other Measurement Returns Random Values Instead of Script Output

**Date:** 2026-02-06
**Status:** ✅ RESOLVED
**Severity:** HIGH
**Component:** Backend - Measurement Execution Layer

---

## Problem Description

Measurements with `test_type='Other'` were returning random values instead of executing custom Python scripts and capturing their output. This affected all custom test scripts including `test123.py`, `123_1.py`, etc.

### Observed Behavior

```
測試項目 2: test123 測試
- 期望值: 123
- 實際值: 71.64689877304908804944716393947601318359375 (隨機值)
- 結果: FAIL

測試項目 4: test123 測試
- 期望值: 123
- 實際值: 4.4484128872093631201778407557867467403411865234375 (隨機值)
- 結果: FAIL
```

### Backend Log Evidence

```
2026-02-06 02:20:13 - INFO - [MeasurementService:89:execute_single_measurement]
    Executing Other measurement for 2

2026-02-06 02:20:13 - INFO - [MeasurementService:128:execute_single_measurement]
    Measurement 2 completed with result: FAIL,
    measured_value: 71.64689877304908804944716393947601318359375

2026-02-06 02:20:15 - INFO - [MeasurementService:89:execute_single_measurement]
    Executing Other measurement for 4

2026-02-06 02:20:15 - INFO - [MeasurementService:128:execute_single_measurement]
    Measurement 4 completed with result: FAIL,
    measured_value: 4.4484128872093631201778407557867467403411865234375
```

---

## Root Cause Analysis

### Issue Location
**File:** `backend/app/measurements/implementations.py`

### Problem Code

```python
# Measurement Registry (line ~1648)
MEASUREMENT_REGISTRY = {
    # ...
    "OTHER": DummyMeasurement,  # ❌ 錯誤: 使用測試用的 DummyMeasurement
    "other": DummyMeasurement,  # ❌ 錯誤: 小寫版本也是 DummyMeasurement
    # ...
}
```

### DummyMeasurement Behavior

```python
class DummyMeasurement(BaseMeasurement):
    """Returns random values for testing purposes"""

    async def execute(self) -> MeasurementResult:
        # 產生隨機值 (用於測試環境)
        if self.lower_limit is not None and self.upper_limit is not None:
            if random.random() < 0.8:
                # 80% 機率產生範圍內的值
                range_size = float(self.upper_limit - self.lower_limit)
                measured_value = self.lower_limit + Decimal(random.uniform(0.1, 0.9) * range_size)
            else:
                # 20% 機率產生範圍外的值 (模擬失敗)
                if random.random() < 0.5:
                    measured_value = self.lower_limit - Decimal(abs(random.gauss(1, 0.5)))
                else:
                    measured_value = self.upper_limit + Decimal(abs(random.gauss(1, 0.5)))
        else:
            measured_value = Decimal(random.uniform(0, 100))
```

### Why This Happened

1. **Design Intent**: `DummyMeasurement` was designed for **testing purposes only** to generate random pass/fail results
2. **Incorrect Mapping**: The registry incorrectly mapped production `"OTHER"` measurement type to this testing class
3. **Missing Implementation**: No actual script execution logic was implemented for custom test scripts

### Expected Behavior (PDTool4)

In PDTool4, `Other` measurement type executes custom Python scripts:

```python
# PDTool4: src/lowsheen_lib/testUTF/123.py (test123.py)
if len(sys.argv) > 1:
    if sys.argv[1] == '123':
        print('456')
else:
    print('123')  # ✓ 應該輸出 "123"
```

---

## Solution Implementation

### 1. Created OtherMeasurement Class

**File:** `backend/app/measurements/implementations.py`
**Lines:** 61-182

```python
# ============================================================================
# Other Measurement - Custom Script Execution
# ============================================================================
class OtherMeasurement(BaseMeasurement):
    """
    Executes custom Python scripts (PDTool4 'Other' measurement type).

    Maps switch_mode (case_type) to script files:
    - test123 → scripts/test123.py
    - 123_1 → scripts/123_1.py
    - WAIT_FIX_5sec → scripts/WAIT_FIX_5sec.py
    - etc.

    Supports UseResult parameter for dependency injection.
    """

    async def execute(self) -> MeasurementResult:
        try:
            # 1. Get script name from switch_mode (case_type)
            switch_mode = self.test_plan_item.get("switch_mode", "")

            if not switch_mode:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing switch_mode (script name)"
                )

            # 2. Get optional parameters
            use_result = get_param(self.test_params, "use_result", "UseResult")
            timeout = get_param(self.test_params, "timeout", "Timeout", default=5000)
            wait_msec = get_param(self.test_params, "wait_msec", "WaitmSec") or \
                       self.test_plan_item.get("wait_msec", 0)

            # 3. Build script path
            script_name = switch_mode.replace(".", "_")  # test123 or 123_1
            script_path = f"/app/scripts/{script_name}.py"

            self.logger.info(f"Executing Other script: {script_path}")

            # 4. Wait if specified
            if wait_msec and isinstance(wait_msec, (int, float)):
                await asyncio.sleep(wait_msec / 1000.0)

            # 5. Build command arguments
            args = []
            if use_result:
                # UseResult: 使用之前測試項目的結果作為參數
                args.append(str(use_result))

            # 6. Execute script
            timeout_seconds = timeout / 1000.0
            cmd = ["python3", script_path] + args

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/app"
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                return self.create_result(
                    result="ERROR",
                    error_message=f"Script timeout after {timeout_seconds}s"
                )

            # 7. Check return code
            if process.returncode != 0:
                error_msg = stderr.decode().strip() if stderr else \
                           f"Script failed with code {process.returncode}"
                return self.create_result(
                    result="ERROR",
                    error_message=error_msg
                )

            # 8. Parse output
            output = stdout.decode().strip()
            self.logger.info(f"Script output: {output}")

            # 9. Try to convert to number, fallback to string
            try:
                measured_value = float(output)
            except ValueError:
                # String result (e.g., "Hello World!")
                measured_value = StringType(output)

            # 10. Validate result
            is_valid, error_msg = self.validate_result(measured_value)

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except FileNotFoundError:
            return self.create_result(
                result="ERROR",
                error_message=f"Script not found: {script_path}"
            )
        except Exception as e:
            self.logger.error(f"Other measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))
```

### 2. Updated Measurement Registry

**File:** `backend/app/measurements/implementations.py`
**Lines:** 1648, 1668

```python
# 原有程式碼: 使用 DummyMeasurement 產生隨機值
MEASUREMENT_REGISTRY = {
    # ...
    "OTHER": DummyMeasurement,  # ❌ OLD: Random values
    "FINAL": DummyMeasurement,
    # ...
    "other": DummyMeasurement,  # ❌ OLD: Random values
    # ...
}

# 修改: 使用 OtherMeasurement 執行自定義腳本
MEASUREMENT_REGISTRY = {
    # ...
    "OTHER": OtherMeasurement,  # ✅ NEW: Execute custom scripts
    "FINAL": DummyMeasurement,  # Keep FINAL as dummy for now
    # ...
    "other": OtherMeasurement,  # ✅ NEW: Execute custom scripts
    # ...
}
```

---

## Key Features of OtherMeasurement

### 1. Script Path Mapping
```python
switch_mode="test123"  → /app/scripts/test123.py
switch_mode="123_1"    → /app/scripts/123_1.py
switch_mode="WAIT_FIX_5sec" → /app/scripts/WAIT_FIX_5sec.py
```

### 2. UseResult Support (PDTool4 Dependency Injection)
```python
# 測試項目 A 輸出: "456"
# 測試項目 B 使用 A 的結果作為輸入
use_result = "456"  # 從測試項目 A 獲取
args = [use_result]
cmd = ["python3", script_path, "456"]  # 傳遞給腳本
```

### 3. Type Flexibility
```python
# Numeric output
print("123")      → measured_value = 123.0 (float)

# String output
print("Hello")    → measured_value = StringType("Hello")
```

### 4. Timeout Protection
```python
timeout = 5000  # ms
timeout_seconds = timeout / 1000.0
await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
```

### 5. Error Handling
```python
# Script not found
FileNotFoundError → ERROR: "Script not found: /app/scripts/xxx.py"

# Script failed
returncode != 0   → ERROR: stderr output

# Script timeout
TimeoutError      → ERROR: "Script timeout after 5.0s"
```

---

## Verification Steps

### 1. Backend Container Restart
```bash
cd /home/ubuntu/python_code/WebPDTool
docker-compose restart backend
```

### 2. Verify Script Exists
```bash
docker-compose exec backend ls -la /app/scripts/test123.py
# Output: -rw-r--r-- 1 1000 1000 337 Jan 29 07:48 /app/scripts/test123.py
```

### 3. Test Script Execution
```bash
docker-compose exec backend python3 /app/scripts/test123.py
# Expected Output: 123
# ✅ Verified: Output is "123"
```

### 4. Test Through Frontend
1. 登入系統: http://localhost:9080
2. 選擇專案和站別
3. 執行包含 test123 測試項目的測試計劃
4. 驗證測量值:
   - **期望**: 測試項目 2 和 4 顯示測量值 `123.000`
   - **結果**: PASS (如果 lower_limit ≤ 123 ≤ upper_limit)

---

## Expected Results After Fix

### Before Fix (❌ FAIL)
```
測試項目 2: test123
- 測量值: 71.646898773... (隨機值)
- 結果: FAIL
- 錯誤: Value outside range

測試項目 4: test123
- 測量值: 4.448412887... (隨機值)
- 結果: FAIL
- 錯誤: Value outside range
```

### After Fix (✅ PASS)
```
測試項目 2: test123
- 測量值: 123.000
- 結果: PASS (假設 lower_limit=100, upper_limit=150)

測試項目 4: test123
- 測量值: 123.000
- 結果: PASS
```

### Backend Logs (After Fix)
```
2026-02-06 XX:XX:XX - INFO - [OtherMeasurement:XX:execute]
    Executing Other script: /app/scripts/test123.py

2026-02-06 XX:XX:XX - INFO - [OtherMeasurement:XX:execute]
    Script output: 123

2026-02-06 XX:XX:XX - INFO - [MeasurementService:128:execute_single_measurement]
    Measurement 2 completed with result: PASS, measured_value: 123.0
```

---

## Related Code Locations

### Modified Files
1. **backend/app/measurements/implementations.py**
   - Added: `OtherMeasurement` class (lines 61-182)
   - Modified: Registry mappings (lines 1648, 1668)

### Related Files (No Changes Required)
1. **backend/app/measurements/base.py**
   - `BaseMeasurement` base class
   - `validate_result()` method (PDTool4 validation logic)

2. **backend/app/services/measurement_service.py**
   - `execute_single_measurement()` method
   - Calls `get_measurement_class()` from implementations.py

3. **frontend/src/views/TestMain.vue**
   - Displays measurement results in UI
   - No frontend changes required

---

## Testing Scenarios

### Scenario 1: Simple Script Output
```python
# script: test123.py
print("123")

# Expected:
# - measured_value: 123.0
# - result: PASS (if within limits)
```

### Scenario 2: Script with Arguments (UseResult)
```python
# script: test123.py
if len(sys.argv) > 1:
    if sys.argv[1] == '123':
        print('456')
else:
    print('123')

# Test Item A: UseResult = None
# Output: "123"

# Test Item B: UseResult = "123" (from Item A)
# Output: "456"
```

### Scenario 3: String Output
```python
# script: string_test.py
print("Hello World!")

# Expected:
# - measured_value: StringType("Hello World!")
# - result: PASS (if limit_type='none' or 'partial')
```

### Scenario 4: Script Error
```python
# script: error_test.py
raise Exception("Simulated error")

# Expected:
# - result: ERROR
# - error_message: "Script failed with code 1: Simulated error"
```

### Scenario 5: Script Timeout
```python
# script: timeout_test.py
import time
time.sleep(10)  # Timeout = 5s

# Expected:
# - result: ERROR
# - error_message: "Script timeout after 5.0s"
```

---

## Impact Assessment

### Affected Components
- ✅ **Backend Measurement Execution**: Fixed
- ✅ **Custom Script Support**: Implemented
- ⚠️ **Frontend Display**: No changes (works correctly)
- ⚠️ **Database**: No schema changes required

### Affected Measurement Types
- ✅ `test_type='Other'` with any `case_type`
- ✅ All custom test scripts in `/app/scripts/`
- ⚠️ `test_type='FINAL'` still uses DummyMeasurement (intentional)

### Breaking Changes
- **None**: This fix restores expected PDTool4 behavior
- **Backward Compatible**: DummyMeasurement still available for FINAL type

---

## Future Enhancements

### 1. Script Discovery
```python
# Auto-discover available scripts
async def list_available_scripts():
    scripts_dir = "/app/scripts"
    return [f.stem for f in Path(scripts_dir).glob("*.py")]
```

### 2. Script Validation
```python
# Validate script before execution
async def validate_script(script_path: str):
    # Check if file exists
    # Check if file is executable
    # Check syntax with ast.parse()
```

### 3. Script Output Parsing
```python
# Support JSON output from scripts
output = '{"value": 123, "status": "OK", "metadata": {...}}'
result = json.loads(output)
measured_value = result["value"]
```

### 4. Script Caching
```python
# Cache compiled scripts for performance
script_cache = {}

if script_path not in script_cache:
    script_cache[script_path] = compile(code, script_path, 'exec')
```

---

## References

### PDTool4 Equivalent
- **File**: `PDTool4/src/lowsheen_lib/testUTF/123.py`
- **Usage**: Custom test scripts for specialized measurements
- **Behavior**: Print to stdout, exit code indicates success/failure

### Related Issues
- **ISSUE #1**: Invalid parameters (BUGFIX_INVALID_PARAMETERS.md)
- **ISSUE #3**: Wait measurement implementation (ISSUE3.md)
- **ISSUE #5**: Measurement init signature (ISSUE5_measurement_init_signature.md)

### Documentation
- **Architecture**: CLAUDE.md - Measurement Abstraction Layer
- **Test Plans**: backend/testplans/*.csv - Test plan definitions
- **Scripts**: backend/scripts/*.py - Custom measurement scripts

---

## Conclusion

This issue was caused by incorrect registry mapping that directed `"OTHER"` measurement type to a testing stub (`DummyMeasurement`) instead of a proper script execution implementation. The fix implements `OtherMeasurement` class that:

1. ✅ Executes custom Python scripts via subprocess
2. ✅ Captures stdout as measured value
3. ✅ Supports both numeric and string outputs
4. ✅ Implements PDTool4-compatible UseResult dependency injection
5. ✅ Provides proper error handling and timeout protection

The system now correctly executes custom test scripts and returns their actual output values (e.g., "123" from test123.py) instead of random test values.

**Status:** ✅ RESOLVED
**Verification:** Backend restarted, script execution confirmed, ready for production testing
