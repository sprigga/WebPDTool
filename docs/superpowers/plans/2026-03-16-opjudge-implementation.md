# OPjudge Service & API Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `_execute_op_judge` method in `MeasurementService` and ensure all pre-existing OPjudge tests pass.

**Architecture:** PDTool4's OPjudge launched blocking Qt dialogs as subprocesses; WebPDTool reimplements this as an async method that (a) calls the external script via `asyncio.create_subprocess_exec` if the script exists, or (b) falls back to `operator_judgment` param when running headless/web. The `OPJudgeMeasurement` class in `implementations.py` delegates to this service method via the test execution engine.

**Tech Stack:** Python asyncio, FastAPI, SQLAlchemy async, pytest + pytest-asyncio

---

## Background & Context

### PDTool4 OPjudge Logic

Two modes, two external Qt scripts:
- **`confirm`** mode → `OPjudge_confirm.py`: Shows image + message + single "confirm" button → prints `"Yes"` (accept) or `"No"` (close)
- **`YorN`** mode → `OPjudge_YorN.py`: Shows image + message + Yes/No buttons → prints `"Yes"` (pass) or `"No"` (fail)

Both scripts accept: `argv[1]=test_uid_str, argv[2]=TestParams_dict_str`

TestParams dict format: `{"ImagePath": "/path/to/img.jpg", "content": "Check LED color"}`

### WebPDTool Current State

| File | Status | Notes |
|------|--------|-------|
| `backend/app/services/measurement_service.py` | **Missing** `_execute_op_judge` | Method referenced in constants but not implemented |
| `backend/app/measurements/implementations.py:1089` | Stub `OPJudgeMeasurement` | Only uses `Type`/`Expected`/`Result` params, ignores subprocess |
| `backend/tests/test_services/test_opjudge_measurement.py` | Pre-existing, **all failing** | 13 tests covering full contract |
| `backend/app/config/instruments.py:150` | `"OPjudge"` template uses `"Type"` required | Legacy fallback in `measurement_service.py:500` already has correct `"TestParams"` rule |

### Pre-Existing Test Contract

The tests define the exact expected behavior:

```python
# Primary path (script exists)
result = await measurement_service._execute_op_judge(
    test_point_id="LED_Color_Check",
    switch_mode="confirm",          # or "YorN"
    test_params={
        "TestParams": ["ImagePath=/images/green_led.jpg", "content=Check LED is green"],
        # optional: "Timeout": 100  (ms, default 60000)
        # optional: "WaitmSec": 2000  (pre-wait, ms)
    },
    run_all_test=False
)
assert result.result == "PASS"        # "FAIL" or "ERROR"
assert result.measured_value == Decimal("1")  # "0" for FAIL, None for ERROR
assert result.error_message is None

# Fallback path (script not found)
# Uses test_params["operator_judgment"] = "PASS"/"FAIL"
# Sets error_message="Script ... not found - fallback to operator_judgment param"
```

Response mapping (subprocess stdout, uppercased):
- `"PASS"` → result=PASS, measured_value=1
- `"YES"` (confirm mode only) → result=PASS, measured_value=1
- `"FAIL"` or `"NO"` → result=FAIL, measured_value=0
- empty or other → result=ERROR, measured_value=None

---

## File Structure

**Files to modify (only):**
- `backend/app/services/measurement_service.py` — Add `_execute_op_judge` method (~100 lines)
- `backend/app/measurements/implementations.py` — Enhance `OPJudgeMeasurement.execute()` to call `_execute_op_judge` (optional quality improvement, ~10 line change)

**Files to verify pass:**
- `backend/tests/test_services/test_opjudge_measurement.py` — 13 pre-existing tests

No new files, no API endpoints, no schema changes, no migrations.

---

## Chunk 1: Implement `_execute_op_judge` in MeasurementService

### Task 1: Verify tests currently fail

**Files:**
- Test: `backend/tests/test_services/test_opjudge_measurement.py`

- [ ] **Step 1: Run existing tests to confirm they all fail**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_services/test_opjudge_measurement.py -v 2>&1 | head -50
```

Expected: All 13 tests FAIL with `AttributeError: 'MeasurementService' object has no attribute '_execute_op_judge'`

---

### Task 2: Implement `_execute_op_judge` method

**Files:**
- Modify: `backend/app/services/measurement_service.py` (add after `execute_single_measurement` method, ~line 134)

- [ ] **Step 2: Add `_execute_op_judge` to `MeasurementService`**

Insert this method after the closing of `execute_single_measurement` (around line 134) in `measurement_service.py`:

```python
    async def _execute_op_judge(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool = False,
    ) -> MeasurementResult:
        """
        Execute OPjudge measurement - operator visual judgment test.

        Maps to PDTool4's OPjudgeMeasurement with two modes:
        - 'confirm': Single confirm button (operator acknowledges). Script prints "Yes" on confirm.
        - 'YorN': Yes/No buttons (operator judges pass/fail). Script prints "Yes"/"No".

        Primary path: calls external Qt script via asyncio subprocess
        Fallback path: uses 'operator_judgment' param when script not found (headless/web mode)

        Args:
            test_point_id: Test point identifier (e.g. "LED_Color_Check")
            switch_mode: 'confirm' or 'YorN'
            test_params: Must contain 'TestParams' (list or dict) with ImagePath and/or content.
                         Optional: 'Timeout' (ms, default 60000), 'WaitmSec' (pre-wait ms),
                                   'operator_judgment' (fallback: "PASS"/"FAIL")
            run_all_test: Whether to continue on failure (informational only for this method)

        Returns:
            MeasurementResult with result='PASS'/'FAIL'/'ERROR'
        """
        import os

        # --- Validate switch_mode ---
        valid_modes = ["confirm", "YorN"]
        if switch_mode not in valid_modes:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=(
                    f"Invalid OPjudge mode '{switch_mode}'. "
                    f"Expected 'confirm' or 'YorN'"
                ),
            )

        # --- Extract TestParams (case-insensitive key lookup) ---
        raw_test_params = None
        for key in test_params:
            if key.lower() == "testparams":
                raw_test_params = test_params[key]
                break

        if raw_test_params is None:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=(
                    "Missing required parameters: TestParams "
                    "(must contain ImagePath and/or content)"
                ),
            )

        # --- Normalize TestParams to dict ---
        # PDTool4 passes as list ["ImagePath=/path", "content=text"] or dict {"ImagePath": "...", "content": "..."}
        if isinstance(raw_test_params, list):
            parsed_params: Dict[str, Any] = {}
            for item in raw_test_params:
                if isinstance(item, str) and "=" in item:
                    k, v = item.split("=", 1)
                    parsed_params[k.strip()] = v.strip()
        elif isinstance(raw_test_params, dict):
            parsed_params = raw_test_params
        else:
            parsed_params = {}

        required_args = ["ImagePath", "content"]
        if not any(arg in parsed_params for arg in required_args):
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=(
                    f"Missing required parameters: ImagePath or content in TestParams"
                ),
            )

        # --- Extract optional WaitmSec (case-insensitive) ---
        wait_msec = 0
        for key in test_params:
            if key.lower() == "waitmSec".lower():
                try:
                    wait_msec = int(test_params[key])
                except (ValueError, TypeError):
                    wait_msec = 0
                break

        if wait_msec > 0:
            await asyncio.sleep(wait_msec / 1000.0)

        # --- Determine script path (relative to backend working directory) ---
        script_map = {
            "confirm": "./src/lowsheen_lib/OPjudge_confirm.py",
            "YorN": "./src/lowsheen_lib/OPjudge_YorN.py",
        }
        script_path = script_map[switch_mode]

        # --- Extract timeout (case-insensitive, default 60s) ---
        timeout_ms = 60000
        for key in test_params:
            if key.lower() == "timeout":
                try:
                    timeout_ms = int(test_params[key])
                except (ValueError, TypeError):
                    timeout_ms = 60000
                break
        timeout_sec = timeout_ms / 1000.0

        # --- Fallback path: script not found (headless/web mode) ---
        if not os.path.exists(script_path):
            fallback_judgment = None
            for key in test_params:
                if key.lower() == "operator_judgment":
                    fallback_judgment = str(test_params[key]).upper()
                    break

            fallback_msg = f"Script {script_path} not found - fallback to operator_judgment param"
            if fallback_judgment in ("PASS", "1", "YES", "Y"):
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=Decimal("1"),
                    error_message=fallback_msg,
                )
            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="FAIL",
                    measured_value=Decimal("0"),
                    error_message=fallback_msg,
                )

        # --- Primary path: run Qt script via subprocess ---
        try:
            test_uid_str = f"('{test_point_id}',)"
            params_str = str(parsed_params)

            process = await asyncio.create_subprocess_exec(
                "python",
                script_path,
                test_uid_str,
                params_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_sec
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"OPjudge script timeout after {timeout_ms}ms",
                )

            if process.returncode != 0:
                stderr_str = stderr.decode("utf-8", errors="replace").strip()
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=stderr_str or f"Script exited with code {process.returncode}",
                )

            response = stdout.decode("utf-8", errors="replace").strip().upper()

            if not response:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message="Empty response from OPjudge script",
                )

            # PDTool4 OPjudge_confirm prints "Yes" on confirm button click
            # PDTool4 OPjudge_YorN prints "Yes"/"No" on button click
            # Both are normalized to PASS/FAIL
            if response == "PASS" or response == "YES":
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=Decimal("1"),
                )
            elif response in ("FAIL", "NO"):
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="FAIL",
                    measured_value=Decimal("0"),
                )
            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    measured_value=None,
                    error_message=f"Unexpected OPjudge response: {response}",
                )

        except Exception as e:
            self.logger.error(f"OPjudge execution error: {e}", exc_info=True)
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e),
            )
```

- [ ] **Step 3: Run all 13 tests to confirm they pass**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_services/test_opjudge_measurement.py -v 2>&1 | tail -30
```

Expected: All 13 tests PASS

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/services/measurement_service.py
git commit -m "feat: implement _execute_op_judge in MeasurementService

Adds async OPjudge execution logic with:
- subprocess-based script invocation (primary path)
- operator_judgment fallback param (headless/web mode)
- timeout handling, pre-wait support, case-insensitive params
- PASS/FAIL/ERROR result mapping matching PDTool4 behavior

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: Enhance OPJudgeMeasurement in implementations.py

The current `OPJudgeMeasurement.execute()` stub ignores `switch_mode` and `TestParams` entirely. It should delegate to `_execute_op_judge` to use the actual PDTool4 logic.

### Task 3: Wire `OPJudgeMeasurement` to `_execute_op_judge`

**Files:**
- Modify: `backend/app/measurements/implementations.py:1089-1109`

- [ ] **Step 5: Write a failing test first**

Add this test to `backend/tests/test_services/test_opjudge_measurement.py`:

```python
@pytest.mark.asyncio
async def test_opjudge_implementation_class_uses_service():
    """OPJudgeMeasurement class should produce PASS result for YorN mode via fallback"""
    from app.measurements.implementations import OPJudgeMeasurement

    test_plan_item = {
        "item_no": 1,
        "item_name": "Visual_Check_01",
        "switch_mode": "YorN",
        "measurement_type": "OPjudge",
        "parameters": {
            "TestParams": {"ImagePath": "/test.jpg", "content": "Check LED"},
            "operator_judgment": "PASS",
        }
    }

    with patch('os.path.exists', return_value=False):
        m = OPJudgeMeasurement(test_plan_item=test_plan_item, config={})
        result = await m.execute()

    assert result.result == "PASS"
    assert result.measured_value == Decimal("1")
```

Run to confirm it fails:
```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_services/test_opjudge_measurement.py::TestOPjudgeMeasurement::test_opjudge_implementation_class_uses_service -v
```

Expected: FAIL (OPJudgeMeasurement stub ignores TestParams)

- [ ] **Step 6: Update `OPJudgeMeasurement.execute()` in `implementations.py`**

Replace the existing `OPJudgeMeasurement.execute()` method (lines 1092–1108) with:

```python
    async def execute(self) -> MeasurementResult:
        """
        Operator judgment measurement.
        Delegates to MeasurementService._execute_op_judge() for full PDTool4 behavior.
        Falls back to legacy Type/Expected/Result param logic if service unavailable.
        """
        try:
            # 原有程式碼: 僅使用 Type/Expected/Result 參數，不呼叫外部腳本
            # 修改: 委派給 MeasurementService._execute_op_judge() 實作完整 PDTool4 邏輯
            from app.services.measurement_service import measurement_service

            switch_mode = get_param(self.test_params, "switch_mode") or \
                          self.test_plan_item.get("switch_mode", "YorN")
            test_point_id = self.test_plan_item.get("item_name", "unknown")

            result = await measurement_service._execute_op_judge(
                test_point_id=test_point_id,
                switch_mode=switch_mode,
                test_params=self.test_params,
                run_all_test=False,
            )
            return result

        except Exception as e:
            self.logger.error(f"Operator judgment error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))
```

- [ ] **Step 7: Run all tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_services/test_opjudge_measurement.py -v 2>&1 | tail -20
```

Expected: All tests PASS (including the new one from Step 5)

- [ ] **Step 8: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/measurements/implementations.py
git add backend/tests/test_services/test_opjudge_measurement.py
git commit -m "feat: wire OPJudgeMeasurement to _execute_op_judge service method

Replaces stub implementation that ignored subprocess/TestParams with
delegation to measurement_service._execute_op_judge(), ensuring
OPjudge test plan items use full PDTool4-compatible execution logic.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Final Verification

- [ ] **Run full backend test suite**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest -v --tb=short 2>&1 | tail -40
```

Expected: All pre-existing tests still pass; no regressions.

---

## Design Notes

### Why No New API Endpoints?

OPjudge is already wired into the test execution flow:
1. `test_engine.py` calls `measurement_service.execute_single_measurement()`
2. Which calls `OPJudgeMeasurement.execute()`
3. Which (after this plan) calls `_execute_op_judge()`

The web-based interactive judgment (showing image/dialog to browser user during a live test) is a future enhancement requiring WebSocket or SSE. The current implementation supports:
- **Production hardware stations**: External Qt script runs on the test machine
- **Web/headless mode**: `operator_judgment` param preset in test_params (e.g. set by TestPlan CSV)

### TestParams Format

PDTool4 passes as list strings: `["ImagePath=/path/img.jpg", "content=Check LED color"]`

The implementation normalizes both list and dict formats:
```python
# List format (PDTool4 CSV import)
"TestParams": ["ImagePath=/path/img.jpg", "content=Check LED color"]

# Dict format (direct API call)
"TestParams": {"ImagePath": "/path/img.jpg", "content": "Check LED color"}
```

### Response Normalization

| Script output | Mode | Normalized | Result |
|--------------|------|------------|--------|
| `"Yes"` | confirm | `"YES"` | PASS |
| `"Yes"` | YorN | `"YES"` | PASS |
| `"No"` | confirm | `"NO"` | FAIL |
| `"No"` | YorN | `"NO"` | FAIL |
| `"PASS"` | any | `"PASS"` | PASS |
| `"FAIL"` | any | `"FAIL"` | FAIL |
| other | any | — | ERROR |
