# OPjudge Frontend Parameter UI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the OPjudge measurement template, both validation paths, backend service param handling, and frontend composable so that `TestPlanManage.vue` correctly renders `ImagePath`, `content`, `WaitmSec`, `Timeout`, and `operator_judgment` fields for OPjudge test items.

**Architecture:** Four targeted changes:
1. Replace the stale `MEASUREMENT_TEMPLATES["OPjudge"]` in `backend/app/config/instruments.py` — from `"default"` mode with `Type/Expected/Result` to `"confirm"`/`"YorN"` modes with flat params (`ImagePath`, `content`, etc.).
2. Update the legacy `validation_rules["OPjudge"]` dict in `backend/app/services/measurement_service.py` for defense-in-depth consistency (this is the rarely-reached fallback; primary path is `validate_params_config` which already picks up change #1 automatically).
3. Refactor `_execute_op_judge` so **flat top-level keys** (`ImagePath`, `content`) are the primary format and `TestParams` key is the **legacy fallback** for backward compatibility with PDTool4 CSV imports. The execution check remains `any(required_arg in parsed_params)` — either `ImagePath` OR `content` is sufficient (image-only and text-only tests are both valid).
4. Update `frontend/src/composables/useMeasurementParams.js` so `WaitmSec`/`Timeout` → number and `operator_judgment` → select PASS/FAIL. `DynamicParamForm.vue` and Pydantic schemas require no changes.

**Key design decision — required params:** `MEASUREMENT_TEMPLATES` marks both `ImagePath` and `content` as `required` for UI purposes (ensures users fill in both). `_execute_op_judge` uses `any()` check (either is sufficient) to handle edge cases. This is intentional and consistent with PDTool4 behavior. `operator_judgment` is `optional` in `YorN` mode only — `confirm` mode doesn't expose it.

**Tech Stack:** Python 3.11 / FastAPI / Vue 3 / Element Plus / pytest

---

## Chunk 1: Backend — Template + Validation Rules

### Task 1: Update `MEASUREMENT_TEMPLATES["OPjudge"]` in `instruments.py`

**Files:**
- Modify: `backend/app/config/instruments.py` (lines 150–158, the `"OPjudge"` block)

- [ ] **Step 1: Run assertion to confirm the current template fails the target shape**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
python3 -c "
from app.config.instruments import MEASUREMENT_TEMPLATES
t = MEASUREMENT_TEMPLATES['OPjudge']
# These should all FAIL before the change
try:
    assert 'confirm' in t, 'confirm mode missing'
    assert 'ImagePath' in t['confirm']['required'], 'ImagePath missing'
    print('UNEXPECTED PASS — template already updated?')
except AssertionError as e:
    print(f'Expected failure confirmed: {e}')
"
```

Expected: `Expected failure confirmed: confirm mode missing`

- [ ] **Step 2: Replace the OPjudge block in `backend/app/config/instruments.py`**

Find the current block (lines 150–158):
```python
    "OPjudge": {
        "default": {
            "required": ["Type"],
            "optional": ["Expected", "Result"],
            "example": {
                "Type": "YorN",
                "Expected": "PASS"
            }
        }
    },
```

Replace with:
```python
    # 原有程式碼: 舊版 stub — 使用 "default" mode 和 Type/Expected/Result 參數
    # "OPjudge": {
    #     "default": {
    #         "required": ["Type"],
    #         "optional": ["Expected", "Result"],
    #         "example": {
    #             "Type": "YorN",
    #             "Expected": "PASS"
    #         }
    #     }
    # },
    # 修正 (Option A): 展開格式 — 前端直接提供 ImagePath/content 為頂層欄位
    # 注意: UI 要求兩個欄位均填寫 (required)，但 _execute_op_judge 執行時接受任一欄位即可 (any())
    # operator_judgment 僅在 YorN 模式下有意義，confirm 模式不需要後備判定
    "OPjudge": {
        "confirm": {
            "required": ["ImagePath", "content"],
            "optional": ["WaitmSec", "Timeout"],
            "example": {
                "ImagePath": "/images/led.jpg",
                "content": "Confirm LED is green",
                "WaitmSec": 0,
                "Timeout": 30000
            }
        },
        "YorN": {
            "required": ["ImagePath", "content"],
            "optional": ["WaitmSec", "Timeout", "operator_judgment"],
            "example": {
                "ImagePath": "/images/display.jpg",
                "content": "Is display correct?",
                "WaitmSec": 0,
                "Timeout": 30000,
                "operator_judgment": "PASS"
            }
        }
    },
```

- [ ] **Step 3: Run assertion to confirm template now passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
python3 -c "
from app.config.instruments import MEASUREMENT_TEMPLATES
t = MEASUREMENT_TEMPLATES['OPjudge']
assert 'confirm' in t, 'confirm mode missing'
assert 'YorN' in t, 'YorN mode missing'
assert 'ImagePath' in t['confirm']['required'], 'ImagePath missing from confirm.required'
assert 'content' in t['confirm']['required'], 'content missing from confirm.required'
assert 'WaitmSec' in t['confirm']['optional'], 'WaitmSec missing from confirm.optional'
assert 'Timeout' in t['confirm']['optional'], 'Timeout missing from confirm.optional'
assert 'operator_judgment' in t['YorN']['optional'], 'operator_judgment missing from YorN.optional'
assert 'operator_judgment' not in t['confirm'].get('optional', []), 'operator_judgment should NOT be in confirm mode'
assert 'default' not in t, 'stale default mode still present'
print('PASS: template shape correct')
"
```

Expected: `PASS: template shape correct`

---

### Task 2: Update `validation_rules["OPjudge"]` in `measurement_service.py`

**Files:**
- Modify: `backend/app/services/measurement_service.py` (lines 722–724)

**Context:** `validate_params()` uses two paths:
- **Primary** (`validate_params_config` from `instruments.py`): Picks up Task 1 changes automatically. For OPjudge with `confirm`/`YorN` modes, this path will now work with flat params.
- **Fallback** (hardcoded `validation_rules` dict in `measurement_service.py`): Triggered only when primary returns "Unsupported combination". OPjudge now has `confirm`/`YorN` in the primary template, so this fallback is rarely reached, but must stay consistent for defense-in-depth.

- [ ] **Step 1: Update `validation_rules["OPjudge"]`**

Find (around line 722–724):
```python
            "OPjudge": {
                "YorN": ["TestParams"],  # Requires TestParams list with ImagePath and content
                "confirm": ["TestParams"],  # Requires TestParams list with ImagePath and content
            },
```

Replace with:
```python
            # 原有程式碼: 要求 TestParams key（舊版 PDTool4 格式）
            # "OPjudge": {
            #     "YorN": ["TestParams"],
            #     "confirm": ["TestParams"],
            # },
            # 修正: 與 MEASUREMENT_TEMPLATES 同步，使用展開格式頂層欄位
            # 此為後備驗證路徑，通常由 validate_params_config (primary path) 先行處理
            "OPjudge": {
                "YorN": ["ImagePath", "content"],
                "confirm": ["ImagePath", "content"],
            },
```

- [ ] **Step 2: Run inline validation check**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
python3 -c "
import asyncio
from app.services.measurement_service import measurement_service

async def check():
    # confirm + flat params → valid
    r = await measurement_service.validate_params('OPjudge', 'confirm', {'ImagePath': '/t.jpg', 'content': 'Check'})
    assert r['valid'] is True, f'confirm flat FAIL: {r}'

    # YorN + flat params + operator_judgment → valid
    r2 = await measurement_service.validate_params('OPjudge', 'YorN', {'ImagePath': '/t.jpg', 'content': 'Check?', 'operator_judgment': 'PASS'})
    assert r2['valid'] is True, f'YorN with operator_judgment FAIL: {r2}'

    # confirm + empty → invalid (missing required params)
    r3 = await measurement_service.validate_params('OPjudge', 'confirm', {})
    assert r3['valid'] is False, f'empty params should be invalid: {r3}'
    missing = r3.get('missing_params', [])
    assert 'ImagePath' in missing or 'content' in missing, f'expected ImagePath or content in missing_params, got: {missing}'

    print('PASS: validate_params consistent')

asyncio.run(check())
"
```

Expected: `PASS: validate_params consistent`

- [ ] **Step 3: Commit both template and validation_rules changes**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/config/instruments.py backend/app/services/measurement_service.py
git commit -m "fix: sync OPjudge MEASUREMENT_TEMPLATES and validation_rules to flat param format"
```

---

## Chunk 2: Backend — Refactor `_execute_op_judge` Param Extraction

### Task 3: Make flat `ImagePath`/`content` the primary format; `TestParams` key as legacy fallback

**Files:**
- Modify: `backend/app/services/measurement_service.py` (around lines 179–217)
- Modify: `backend/tests/test_services/test_opjudge_measurement.py`

After Chunk 1, the frontend sends flat params (`ImagePath`, `content` as top-level keys). The service currently only accepts `TestParams` key. Refactor so:
- **Primary**: scan top-level keys for `ImagePath`/`content` directly
- **Legacy fallback**: if not found at top level, look for `TestParams` key (list or dict PDTool4 CSV format)
- **Guard**: if neither found, return ERROR with descriptive message
- **Execution check**: keep `any()` — either `ImagePath` OR `content` is sufficient (image-only and text-only tests are valid)

- [ ] **Step 1: Write two new TDD tests**

Add to class `TestOPjudgeMeasurement` in `backend/tests/test_services/test_opjudge_measurement.py` (current count: 18 tests):

```python
    @pytest.mark.asyncio
    async def test_opjudge_flat_format_primary(self):
        """Test _execute_op_judge accepts flat ImagePath/content as primary format (Option A)"""

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"PASS\n", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="Flat_Primary_Test",
                    switch_mode="confirm",
                    test_params={
                        "ImagePath": "/images/led.jpg",
                        "content": "Confirm LED is green",
                    },
                    run_all_test=False
                )

        assert result.result == "PASS"
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_opjudge_no_valid_params_returns_error(self):
        """Test _execute_op_judge returns ERROR when neither flat keys nor TestParams present"""

        result = await measurement_service._execute_op_judge(
            test_point_id="No_Params_Test",
            switch_mode="confirm",
            test_params={
                "WaitmSec": 0,
                "Timeout": 5000,
                # No ImagePath, no content, no TestParams
            },
            run_all_test=False
        )

        assert result.result == "ERROR"
        assert "Missing required parameters" in result.error_message
```

- [ ] **Step 2: Run new tests — verify they fail**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
python3 -m pytest tests/test_services/test_opjudge_measurement.py::TestOPjudgeMeasurement::test_opjudge_flat_format_primary tests/test_services/test_opjudge_measurement.py::TestOPjudgeMeasurement::test_opjudge_no_valid_params_returns_error -v
```

Expected: `test_opjudge_flat_format_primary` FAILS (returns ERROR — flat keys not yet recognized as primary). `test_opjudge_no_valid_params_returns_error` likely PASSES already (no params → ERROR).

- [ ] **Step 3: Refactor param extraction block in `_execute_op_judge`**

In `backend/app/services/measurement_service.py`, find the block from roughly line 179 to line 217:

```python
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
                error_message="Missing required parameters: ImagePath or content in TestParams",
            )
```

Replace with:

```python
        # --- Extract params: primary = flat top-level keys, legacy = TestParams key ---
        # 修正 (Option A): 前端展開格式（ImagePath/content 為頂層欄位）為主要格式
        # PDTool4 CSV 匯入的 TestParams key 格式為向後相容的舊式格式

        parsed_params: Dict[str, Any] = {}

        # 1. 主要格式: 嘗試從頂層欄位直接取 ImagePath / content
        for flat_key in ["ImagePath", "content"]:
            for key in test_params:
                if key.lower() == flat_key.lower():
                    parsed_params[flat_key] = test_params[key]
                    break

        # 2. 舊式格式後備: 若頂層未找到，嘗試 TestParams key（PDTool4 CSV 匯入格式）
        # 原有程式碼: 以 TestParams key 為唯一格式
        # raw_test_params = None
        # for key in test_params:
        #     if key.lower() == "testparams":
        #         raw_test_params = test_params[key]
        #         break
        if not parsed_params:
            raw_test_params = None
            for key in test_params:
                if key.lower() == "testparams":
                    raw_test_params = test_params[key]
                    break

            if raw_test_params is not None:
                # PDTool4 passes list ["ImagePath=/path", "content=text"] or dict
                if isinstance(raw_test_params, list):
                    for item in raw_test_params:
                        if isinstance(item, str) and "=" in item:
                            k, v = item.split("=", 1)
                            parsed_params[k.strip()] = v.strip()
                elif isinstance(raw_test_params, dict):
                    parsed_params = dict(raw_test_params)

        # 3. 若兩種格式均無有效資料，回傳 ERROR
        # 注意: any() — 提供 ImagePath 或 content 任一即可 (image-only 和 text-only 均合法)
        required_args = ["ImagePath", "content"]
        if not any(arg in parsed_params for arg in required_args):
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=(
                    "Missing required parameters: provide 'ImagePath' and/or 'content' as top-level keys, "
                    "or provide a 'TestParams' key (dict or list format) containing ImagePath and/or content."
                ),
            )
```

- [ ] **Step 4: Run all 20 OPjudge tests**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
python3 -m pytest tests/test_services/test_opjudge_measurement.py -v
```

Expected: All 20 tests PASS (18 original + 2 new). Confirm count at bottom of output shows `20 passed`.

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/services/measurement_service.py
git add backend/tests/test_services/test_opjudge_measurement.py
git commit -m "feat: make flat ImagePath/content primary format in _execute_op_judge; TestParams as legacy fallback"
```

---

## Chunk 3: Frontend — Composable Type Inference

### Task 4: Update `useMeasurementParams.js` for OPjudge field types

**Files:**
- Modify: `frontend/src/composables/useMeasurementParams.js`

The composable's `inferParamType(paramName, exampleValue)` and `getParamOptions(paramName)` drive the input widget rendered by `DynamicParamForm.vue`. The function starts with `const name = paramName.toLowerCase()` before all checks.

**What needs changing:**
- `WaitmSec` → `'WaitmSec'.toLowerCase()` = `'waitmsec'` → add `name.includes('waitmsec')` to number block
- `Timeout` → `'Timeout'.toLowerCase()` = `'timeout'` → already matched by `name.includes('timeout')` → **no change**
- `operator_judgment` → `'operator_judgment'.toLowerCase()` = `'operator_judgment'` → add `name === 'operator_judgment'` → select with `['PASS', 'FAIL']`
- `ImagePath` → `'imagepath'` → no match → defaults to text → **no change**
- `content` → `'content'` → no match → defaults to text → **no change**

- [ ] **Step 1: Verify current behavior before changes**

```bash
cd /home/ubuntu/python_code/WebPDTool/frontend
node -e "
const inferParamType = (paramName, exampleValue) => {
  const name = paramName.toLowerCase()
  if (name.includes('volt') || name.includes('curr') ||
      name.includes('channel') || name.includes('timeout') ||
      name.includes('nplc') || name.includes('range') ||
      name.includes('bandwidth') || name.includes('frequency') ||
      name.includes('delay')) {
    return 'number'
  }
  if (name === 'baud') return 'select'
  if (name === 'type' && typeof exampleValue === 'string') return 'select'
  if (name === 'item' && typeof exampleValue === 'string') return 'select'
  return 'text'
}
const fields = {
  WaitmSec: inferParamType('WaitmSec', 0),
  Timeout: inferParamType('Timeout', 30000),
  operator_judgment: inferParamType('operator_judgment', 'PASS'),
  ImagePath: inferParamType('ImagePath', '/a.jpg'),
  content: inferParamType('content', 'Check LED'),
}
console.log(JSON.stringify(fields, null, 2))
// Expected BEFORE fix: WaitmSec=text (WRONG), Timeout=number (OK), operator_judgment=text (WRONG)
"
```

Expected (shows what needs fixing):
```json
{
  "WaitmSec": "text",
  "Timeout": "number",
  "operator_judgment": "text",
  "ImagePath": "text",
  "content": "text"
}
```

- [ ] **Step 2: Add `waitmsec` to number detection in `inferParamType`**

In `frontend/src/composables/useMeasurementParams.js`, find:

```javascript
    // 數字類型
    if (name.includes('volt') || name.includes('curr') ||
        name.includes('channel') || name.includes('timeout') ||
        name.includes('nplc') || name.includes('range') ||
        name.includes('bandwidth') || name.includes('frequency') ||
        name.includes('delay')) {
      return 'number'
    }
```

Replace with:

```javascript
    // 數字類型
    // 原有程式碼: 未包含 waitmsec（'WaitmSec'.toLowerCase() 的結果）
    // if (name.includes('volt') || name.includes('curr') ||
    //     name.includes('channel') || name.includes('timeout') ||
    //     name.includes('nplc') || name.includes('range') ||
    //     name.includes('bandwidth') || name.includes('frequency') ||
    //     name.includes('delay')) {
    //   return 'number'
    // }
    // 修正: 加入 'waitmsec'（'WaitmSec'.toLowerCase() = 'waitmsec'）
    if (name.includes('volt') || name.includes('curr') ||
        name.includes('channel') || name.includes('timeout') ||
        name.includes('nplc') || name.includes('range') ||
        name.includes('bandwidth') || name.includes('frequency') ||
        name.includes('delay') || name.includes('waitmsec')) {
      return 'number'
    }
```

- [ ] **Step 3: Add `operator_judgment` select detection in `inferParamType`**

In the same file, find:

```javascript
    if (name === 'item' && typeof exampleValue === 'string') {
      return 'select'
    }

    // 預設文字輸入
    return 'text'
```

Replace with:

```javascript
    if (name === 'item' && typeof exampleValue === 'string') {
      return 'select'
    }

    // 新增: operator_judgment → select (OPjudge YorN 模式的後備判定，僅 YorN 模式模板中有此欄位)
    if (name === 'operator_judgment') {
      return 'select'
    }

    // 預設文字輸入
    return 'text'
```

- [ ] **Step 4: Add `operator_judgment` options in `getParamOptions`**

In the same file, find:

```javascript
    if (name === 'item') {
      return ['volt', 'curr', 'res', 'temp', 'freq']
    }

    return []
```

Replace with:

```javascript
    if (name === 'item') {
      return ['volt', 'curr', 'res', 'temp', 'freq']
    }

    // 新增: operator_judgment 選項（OPjudge YorN 後備判定值）
    if (name === 'operator_judgment') {
      return ['PASS', 'FAIL']
    }

    return []
```

- [ ] **Step 5: Verify all OPjudge fields infer correctly after changes**

```bash
cd /home/ubuntu/python_code/WebPDTool/frontend
node -e "
const inferParamType = (paramName, exampleValue) => {
  const name = paramName.toLowerCase()
  if (name.includes('volt') || name.includes('curr') ||
      name.includes('channel') || name.includes('timeout') ||
      name.includes('nplc') || name.includes('range') ||
      name.includes('bandwidth') || name.includes('frequency') ||
      name.includes('delay') || name.includes('waitmsec')) {
    return 'number'
  }
  if (name === 'baud') return 'select'
  if (name === 'type' && typeof exampleValue === 'string') return 'select'
  if (name === 'item' && typeof exampleValue === 'string') return 'select'
  if (name === 'operator_judgment') return 'select'
  return 'text'
}
const results = {
  WaitmSec: inferParamType('WaitmSec', 0),
  Timeout: inferParamType('Timeout', 30000),
  operator_judgment: inferParamType('operator_judgment', 'PASS'),
  ImagePath: inferParamType('ImagePath', '/a.jpg'),
  content: inferParamType('content', 'Check LED'),
}
console.log(JSON.stringify(results, null, 2))
const expected = {WaitmSec:'number', Timeout:'number', operator_judgment:'select', ImagePath:'text', content:'text'}
let allOk = true
Object.entries(expected).forEach(([k, v]) => {
  if (results[k] !== v) { console.error('FAIL:', k, 'expected', v, 'got', results[k]); allOk = false }
})
if (allOk) console.log('PASS: all field types correct')
"
```

Expected:
```json
{
  "WaitmSec": "number",
  "Timeout": "number",
  "operator_judgment": "select",
  "ImagePath": "text",
  "content": "text"
}
PASS: all field types correct
```

- [ ] **Step 6: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add frontend/src/composables/useMeasurementParams.js
git commit -m "feat: add WaitmSec number and operator_judgment select type inference for OPjudge"
```

---

## Chunk 4: Final Verification

### Task 5: Full test suite + push

- [ ] **Step 1: Run the full backend test suite**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
python3 -m pytest --tb=short -q
```

Expected: No new failures vs pre-change baseline. Pre-existing failures in relay/power/comport/RF instrument tests are acceptable (hardware-dependent stubs). OPjudge tests should show 20 passed.

- [ ] **Step 2: Push to remote**

```bash
cd /home/ubuntu/python_code/WebPDTool
git push origin main
```

Expected: Push succeeds.
