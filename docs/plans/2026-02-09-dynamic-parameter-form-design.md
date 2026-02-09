# Dynamic Parameter Form Design Document

**Date:** 2026-02-09
**Feature:** Dynamic Test Parameter Form for TestPlan Management
**Status:** Approved - Ready for Implementation

## Overview

Implement a dynamic form system that allows users to input and edit test parameters based on `test_type` and `switch_mode` selections. This eliminates the need for manual JSON editing and provides intelligent, type-aware input controls.

## Business Requirements

### Current Problem
- The `TestPlan.parameters` JSON field exists in the database but has no UI implementation
- Users cannot view or edit test parameters through the frontend
- Parameters are hardcoded as empty objects `{}` during test plan creation
- Manual JSON editing would be error-prone for operators

### Solution Goals
1. **Phase 1:** Implement dynamic parameter form in TestPlanManage.vue edit dialog
2. **Phase 2:** Add parameter preview/editing during CSV upload (future)
3. Provide intelligent input controls based on parameter types
4. Validate parameters against backend templates
5. Maintain backward compatibility with existing test plans

## Technical Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────┐
│  Frontend UI Layer                      │
│  - DynamicParamForm.vue (智慧表單元件)   │
│  - TestPlanManage.vue (整合)             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Frontend Service Layer                 │
│  - useMeasurementParams (composable)    │
│  - api/measurements.js (API client)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Backend API Layer                      │
│  - GET /api/measurements/templates      │
│  - POST /api/measurements/validate-params│
│  - MEASUREMENT_TEMPLATES (single source)│
└─────────────────────────────────────────┘
```

## Data Flow

```
User selects test_type + switch_mode
         ↓
Frontend requests MEASUREMENT_TEMPLATES
         ↓
Backend returns parameter definitions (required, optional, example)
         ↓
DynamicParamForm renders input controls dynamically
         ↓
User fills in parameter values
         ↓
Real-time validation (frontend basic check)
         ↓
Save triggers backend validation (validate-params API)
         ↓
Parameters saved to TestPlan.parameters JSON field
```

## Component Design

### 1. Backend API Endpoints

#### GET /api/measurements/templates
```python
@router.get("/templates")
async def get_measurement_templates():
    """Get all measurement type parameter templates"""
    return {
        "templates": MEASUREMENT_TEMPLATES,
        "test_types": list(MEASUREMENT_TEMPLATES.keys())
    }
```

**Response Example:**
```json
{
  "templates": {
    "PowerRead": {
      "DAQ973A": {
        "required": ["Instrument", "Channel", "Item", "Type"],
        "optional": ["Range", "NPLC"],
        "example": {
          "Instrument": "daq973a_1",
          "Channel": "101",
          "Item": "volt",
          "Type": "DC"
        }
      }
    }
  },
  "test_types": ["PowerRead", "PowerSet", "CommandTest", ...]
}
```

#### POST /api/measurements/validate-params
```python
class ParamValidationRequest(BaseModel):
    test_type: str
    switch_mode: Optional[str] = None
    parameters: Dict[str, Any]

@router.post("/validate-params")
async def validate_measurement_params(request: ParamValidationRequest):
    """Validate measurement parameters against template"""
    return {
        "valid": bool,
        "missing_params": List[str],
        "invalid_params": List[str],
        "suggestions": List[str]
    }
```

### 2. Frontend Composable: useMeasurementParams

**File:** `frontend/src/composables/useMeasurementParams.js`

**Key Features:**
- Load and cache MEASUREMENT_TEMPLATES
- Reactive template selection based on test_type/switch_mode
- Infer parameter input types from names and examples
- Provide parameter options for select dropdowns
- Integrate validation API

**Key Functions:**
```javascript
export function useMeasurementParams() {
  return {
    // State
    templates,
    loading,
    currentTestType,
    currentSwitchMode,

    // Computed
    testTypes,          // Available test types
    switchModes,        // Available switch modes for current test type
    requiredParams,     // Required parameter names
    optionalParams,     // Optional parameter names
    exampleParams,      // Example values

    // Methods
    loadTemplates(),           // Load from backend
    validateParams(params),    // Validate against backend
    inferParamType(name, val), // Infer UI control type
    getParamOptions(name)      // Get dropdown options
  }
}
```

**Parameter Type Inference Logic:**
```javascript
inferParamType(paramName, exampleValue) {
  const name = paramName.toLowerCase()

  // Number inputs
  if (name.includes('volt') || name.includes('curr') ||
      name.includes('channel') || name.includes('timeout'))
    return 'number'

  // Select dropdowns
  if (name === 'baud' || name === 'type')
    return 'select'

  // Default: text input
  return 'text'
}
```

### 3. DynamicParamForm Component

**File:** `frontend/src/components/DynamicParamForm.vue`

**Props:**
- `modelValue`: Object - Parameters (v-model)
- `testType`: String - Test type name
- `switchMode`: String - Switch mode name

**Events:**
- `update:modelValue` - Parameter changes
- `validation-change` - Validation status (boolean)

**Features:**
1. **Dynamic Rendering:** Automatically render appropriate input controls
2. **Real-time Validation:** Check required fields on input
3. **Visual Feedback:** Required markers, example hints, error alerts
4. **Responsive Layout:** Two-column grid using Element Plus

**Input Control Mapping:**
```
Parameter Type → UI Control
─────────────────────────────
number         → el-input-number
select         → el-select with predefined options
text (default) → el-input
```

### 4. TestPlanManage.vue Integration

**Modifications Required:**

1. **Import Dependencies:**
```javascript
import DynamicParamForm from '@/components/DynamicParamForm.vue'
import { useMeasurementParams } from '@/composables/useMeasurementParams'
```

2. **Update Data Model:**
```javascript
const editingItem = reactive({
  // ... existing fields ...
  switch_mode: '',    // NEW: Instrument mode
  parameters: {},     // CHANGED: From hardcoded {} to actual usage
})
```

3. **Add Form Section in Edit Dialog:**
```vue
<!-- After basic info section -->
<el-divider content-position="left">測試類型與儀器模式</el-divider>

<el-row :gutter="20">
  <el-col :span="12">
    <el-form-item label="測試類型" prop="test_type">
      <el-select v-model="editingItem.test_type" @change="handleTestTypeChange">
        <el-option v-for="type in testTypes" :key="type" :label="type" :value="type"/>
      </el-select>
    </el-form-item>
  </el-col>
  <el-col :span="12">
    <el-form-item label="儀器模式">
      <el-select v-model="editingItem.switch_mode" :disabled="!editingItem.test_type">
        <el-option v-for="mode in switchModes" :key="mode" :label="mode" :value="mode"/>
      </el-select>
    </el-form-item>
  </el-col>
</el-row>

<el-divider content-position="left">測試參數設定</el-divider>

<DynamicParamForm
  v-model="editingItem.parameters"
  :test-type="editingItem.test_type"
  :switch-mode="editingItem.switch_mode"
  @validation-change="handleParamValidation"
/>
```

4. **Update Save Logic:**
```javascript
const handleSaveItem = async () => {
  // ... validation ...

  // Check parameter validation
  if (!paramValidation.value && editingItem.switch_mode) {
    ElMessage.warning('請完整填寫測試參數')
    return
  }

  const itemData = {
    // ... other fields ...
    switch_mode: editingItem.switch_mode,  // NEW
    parameters: editingItem.parameters,     // CHANGED: Send actual params
  }

  // Save via API...
}
```

5. **Initialize in onMounted:**
```javascript
onMounted(async () => {
  // ... existing initialization ...

  // NEW: Load measurement templates
  await loadTemplates()
})
```

## User Workflow

### Creating New Test Item
1. Click "新增項目" button
2. Fill in basic info (item_name, sequence_order, etc.)
3. Select **測試類型** (test_type) → Available switch modes load
4. Select **儀器模式** (switch_mode) → Parameter form appears
5. Fill in required parameters (marked with *)
6. Optional: Fill in optional parameters
7. Real-time validation shows errors
8. Click "儲存" → Backend validates → Save to database

### Editing Existing Test Item
1. Click "編輯" button on table row
2. Dialog loads with existing values
3. If test_type/switch_mode exist, parameter form displays with current values
4. Modify parameters as needed
5. Validation checks completeness
6. Save updates TestPlan.parameters

## Backward Compatibility

### For Existing Test Plans
- Test plans without `switch_mode` or `parameters` remain editable
- All existing fields (command, timeout, etc.) coexist with parameters
- No breaking changes to database schema
- No migration required

### Validation Rules
- If `test_type` not in MEASUREMENT_TEMPLATES, no dynamic form shown
- If `switch_mode` empty, parameter section shows "Please select instrument mode"
- Legacy test plans can be gradually migrated by editing and adding parameters

## Implementation Plan

### Phase 1: Edit Dialog Implementation (Current)

**Backend Tasks:**
1. Add `/api/measurements/templates` endpoint
2. Add `/api/measurements/validate-params` endpoint
3. Implement `validate_params()` function in `instruments.py`
4. Update API router registration

**Frontend Tasks:**
1. Create `api/measurements.js` API client
2. Create `composables/useMeasurementParams.js` composable
3. Create `components/DynamicParamForm.vue` component
4. Integrate into `TestPlanManage.vue` edit dialog
5. Update save/edit logic to handle parameters

**Testing:**
- Unit tests for parameter validation logic
- Component tests for DynamicParamForm
- Integration tests for TestPlanManage edit flow
- Manual testing with different test types

### Phase 2: CSV Upload Preview (Future)
- Add parameter preview table after CSV upload
- Allow editing parameters before saving
- Batch validation for all imported items
- Detailed error reporting for each row

## Success Criteria

1. ✅ Users can view/edit parameters through UI (no manual JSON editing)
2. ✅ Parameter form adapts to selected test_type and switch_mode
3. ✅ Real-time validation prevents incomplete submissions
4. ✅ Backend validation ensures data integrity
5. ✅ Existing test plans remain functional
6. ✅ No breaking changes to API or database

## Technical Considerations

### Performance
- Template data cached after first load
- Validation throttled to avoid excessive API calls
- Component uses v-if to avoid unnecessary rendering

### Error Handling
- Network errors show user-friendly messages
- Validation errors displayed inline with suggestions
- Fallback to text input if type inference fails

### Extensibility
- Adding new test types only requires updating MEASUREMENT_TEMPLATES
- Parameter type inference can be extended with more rules
- Custom validation rules can be added per parameter

## Related Documentation

- [TestPlan Parameters Architecture](../features/testplan-parameters-architecture.md)
- [Measurement Implementation Guide](../features/measurement-implementations.md)
- [CLAUDE.md Project Overview](../../CLAUDE.md)

## Approval

**Design Approved:** 2026-02-09
**Ready for Implementation:** Yes
**Estimated Effort:** 1-2 days for Phase 1
