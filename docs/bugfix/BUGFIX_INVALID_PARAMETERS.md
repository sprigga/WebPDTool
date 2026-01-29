# Bug Fix: "Invalid parameters: []" Error for Custom Test Scripts

## Problem Description

When loading test plan "test123" with custom test scripts (like "123_1", "123_2", "WAIT_FIX_5sec"), the system displayed error messages:
```
下午3:33:38 - 4: 123_2: Invalid parameters: []
下午3:33:38 - 3: WAIT_FIX_5sec: Invalid parameters: []
下午3:33:38 - 2: 123_1: Invalid parameters: []
```

## Root Cause

### 1. Backend Validation Issue
The validation logic in `measurement_service.py` was too restrictive:
- When `measurement_type` was not in the predefined validation rules, it rejected the test
- Custom test scripts (like "123_1.py") use `measurement_type="Other"` with the script name as `switch_mode`
- The validation returned `valid: False` with empty `missing_params: []`, causing the confusing error message

### 2. Frontend Logic Confusion
The frontend code in `TestMain.vue` incorrectly mapped CSV data to API parameters:
- Lines 1006-1009 incorrectly used `case_type` as BOTH `measurement_type` AND `switch_mode`
- This violated PDTool4's architecture where:
  - `execute_name` (ExecuteName in CSV) → `measurement_type` (PowerSet, PowerRead, Other, wait, etc.)
  - `case_type` (case in CSV) → `switch_mode` (instrument/script name: DAQ973A, 123_1, WAIT_FIX_5sec, etc.)

## Solution

### Backend Fix (measurement_service.py)

**File**: `backend/app/services/measurement_service.py`

**Change 1**: Allow unknown switch_modes for "Other" and "wait" measurement types (lines 1740-1750)

```python
# Added after line 1730
elif measurement_type in ["Other", "wait", "Wait"]:
    # Other and wait types allow any switch_mode (custom script names)
    # No required parameters
    return {
        "valid": True,
        "missing_params": [],
        "invalid_params": [],
        "suggestions": [],
    }
```

**Rationale**:
- "Other" measurement type is designed for custom test scripts
- Script names like "123_1", "123_2", "WAIT_FIX_5sec" become the `switch_mode`
- These scripts don't need predefined validation rules

**Change 2**: Improved error messages (lines 112-125)

```python
if not validation_result["valid"]:
    # Provide detailed error messages including suggestions
    error_details = []
    if validation_result.get('missing_params'):
        error_details.append(f"Missing: {validation_result['missing_params']}")
    if validation_result.get('suggestions'):
        error_details.append(f"Hint: {validation_result['suggestions'][0]}")

    error_message = f"Invalid parameters for {measurement_type}/{switch_mode}: " + "; ".join(error_details) if error_details else f"Invalid configuration: {measurement_type}/{switch_mode}"

    return MeasurementResult(
        item_no=0,
        item_name=test_point_id,
        result="ERROR",
        error_message=error_message,
    )
```

**Rationale**: Show actual measurement_type/switch_mode and helpful suggestions instead of just "Invalid parameters: []"

### Frontend Fix (TestMain.vue)

**File**: `frontend/src/views/TestMain.vue`

**Change**: Correct parameter mapping (lines 998-1013)

**Before (Incorrect)**:
```javascript
let measurementType = executeName || 'Other'
let switchMode = caseMode || 'default'

// WRONG: Overrides measurement_type with case_type
if (item.case_type && item.case_type !== '') {
  measurementType = item.case_type  // ❌ Incorrect
  switchMode = item.case_type
}
```

**After (Correct)**:
```javascript
// measurement_type: from execute_name (test type)
// switch_mode: from case_type (instrument/script name)
let measurementType = executeName || 'Other'
let switchMode = caseMode || item.item_name || 'default'

// Special case: wait tests need both set to 'wait'
if (item.case_type && (item.case_type.toLowerCase() === 'wait')) {
  measurementType = 'wait'
  switchMode = 'wait'
}
```

**Rationale**:
- Correctly separate concerns between measurement type and switch mode
- Maintain PDTool4's original architecture
- Only override for special case of "wait" tests

## Data Flow Architecture

### CSV → Database → API Parameters

```
CSV Column        → Database Column  → Frontend Use        → API Parameter
-------------------------------------------------------------------------------
ExecuteName       → execute_name     → executeName         → measurement_type
case              → case_type        → caseMode            → switch_mode
ID                → item_name        → item.item_name      → test_point_id
Port              → parameters.port  → testParams.Port     → test_params.Port
Baud              → parameters.baud  → testParams.Baud     → test_params.Baud
Command           → command          → testParams.command  → test_params.command
```

### Example: Custom Test Script

**CSV Data**:
```csv
ID,ExecuteName,case,Command
123_1,Other,123_1,python scripts/123_1.py
```

**API Call**:
```json
{
  "measurement_type": "Other",
  "switch_mode": "123_1",
  "test_point_id": "1",
  "test_params": {
    "command": "python scripts/123_1.py"
  }
}
```

**Execution Flow**:
1. Backend receives `measurement_type="Other"`, `switch_mode="123_1"`
2. Validation accepts because "Other" allows any switch_mode
3. `_execute_other()` method runs the script specified in `command` parameter
4. Script output becomes the measured value

## Testing

### Validation Tests
```bash
cd backend
python3 -c "
from app.services.measurement_service import MeasurementService
import asyncio

async def test():
    service = MeasurementService()
    result1 = await service.validate_params('Other', '123_1', {})
    result2 = await service.validate_params('Other', 'WAIT_FIX_5sec', {})
    result3 = await service.validate_params('wait', 'wait', {})
    assert result1['valid'] == True
    assert result2['valid'] == True
    assert result3['valid'] == True
    print('✓ All validation tests passed')

asyncio.run(test())
"
```

### Frontend Build Test
```bash
cd frontend
npm run build -- --mode development
# Should complete without errors
```

## Impact

### Fixed Issues
✅ Custom test scripts (123_1, 123_2, WAIT_FIX_5sec) no longer show "Invalid parameters: []"
✅ Validation correctly accepts "Other" measurement type with any script name
✅ Error messages now show helpful information instead of empty arrays
✅ Frontend correctly maps execute_name → measurement_type and case_type → switch_mode

### No Breaking Changes
✅ Existing test plans with standard measurement types still work
✅ Backward compatible with both old and new parameter naming
✅ All standard instruments (DAQ973A, MODEL2303, etc.) continue to work

## Files Modified

1. `backend/app/services/measurement_service.py`
   - Lines 1740-1750: Added "Other"/"wait" validation rule
   - Lines 112-125: Improved error messages

2. `frontend/src/views/TestMain.vue`
   - Lines 998-1013: Fixed parameter mapping logic

## Related Documentation

- PDTool4 Architecture: Custom test scripts use `ExecuteName="Other"` with script name in `case` column
- Validation Rules: `backend/app/services/measurement_service.py` lines 1609-1688
- Measurement Dispatch: `backend/app/services/measurement_service.py` lines 36-60

## Prevention

To prevent similar issues in the future:
1. Always use `execute_name` for measurement type, `case_type` for switch mode
2. Add validation tests when introducing new measurement types
3. Document the CSV → API parameter mapping clearly
4. Consider adding a test plan validation tool to catch configuration errors early
