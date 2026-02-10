# Dynamic Validation Types

## Overview

The dynamic validation types system provides dropdown selection for "數值類型" (Value Type) and "限制類型" (Limit Type) fields in the test plan management interface. These options are dynamically fetched from the backend's validation logic, ensuring frontend UI stays synchronized with backend validation rules.

## Background

### The Problem

**Original Implementation (Before):**
```javascript
// Hardcoded in frontend - TestPlanManage.vue
const valueTypes = ['string', 'integer', 'float']
const limitTypes = ['lower', 'upper', 'both', 'equality', 'inequality', 'partial', 'none']
```

**Issues:**
1. **Duplication**: Same values defined in both frontend and backend (`base.py`)
2. **Synchronization Risk**: Adding a new type requires updating two places
3. **Validation Mismatch**: Frontend could show options not supported by backend
4. **Maintenance Burden**: Changes must be coordinated across codebase

**Backend Configuration:**
```python
# backend/app/measurements/base.py
LIMIT_TYPE_MAP = {
    'lower': LOWER_LIMIT,
    'upper': UPPER_LIMIT,
    'both': BOTH_LIMIT,
    'equality': EQUALITY_LIMIT,
    'partial': PARTIAL_LIMIT,
    'inequality': INEQUALITY_LIMIT,
    'none': NONE_LIMIT,
}

VALUE_TYPE_MAP = {
    'string': StringType,
    'integer': IntegerType,
    'float': FloatType,
}
```

### The Solution

**Implementation Pattern:**
1. Backend API endpoint returns types from `LIMIT_TYPE_MAP` and `VALUE_TYPE_MAP`
2. Frontend fetches options on component mount
3. Dropdowns populated from API response
4. Fallback to hardcoded values if API fails

## Architecture

### Backend API

**Endpoint:** `GET /api/measurements/validation-types`

**Location:** `backend/app/api/measurements.py`

**Implementation:**
```python
from app.measurements.base import LIMIT_TYPE_MAP, VALUE_TYPE_MAP

@router.get("/validation-types")
async def get_validation_types():
    """
    Get available value types and limit types for test plan validation

    Returns the validation types supported by the system,
    based on PDTool4's measurement validation logic in app/measurements/base.py

    This ensures frontend dropdown options stay synchronized with backend validation logic.
    """
    try:
        limit_types = list(LIMIT_TYPE_MAP.keys())
        value_types = list(VALUE_TYPE_MAP.keys())

        return {
            "limit_types": limit_types,
            "value_types": value_types
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation types: {str(e)}"
        )
```

**Response:**
```json
{
  "limit_types": ["lower", "upper", "both", "equality", "inequality", "partial", "none"],
  "value_types": ["string", "integer", "float"]
}
```

### Frontend API Client

**Location:** `frontend/src/api/measurements.js`

```javascript
/**
 * Get validation types (value types and limit types)
 * @returns {Promise<{limit_types: string[], value_types: string[]}>} Validation types
 */
export const getValidationTypes = () => {
  return apiClient.get('/api/measurements/validation-types')
}
```

### Frontend Component

**Location:** `frontend/src/views/TestPlanManage.vue`

**Template:**
```vue
<el-form-item label="數值類型">
  <el-select
    v-model="editingItem.value_type"
    placeholder="請選擇數值類型"
    style="width: 100%"
    filterable
    clearable
  >
    <el-option
      v-for="type in valueTypes"
      :key="type"
      :label="type"
      :value="type"
    />
  </el-select>
</el-form-item>

<el-form-item label="限制類型">
  <el-select
    v-model="editingItem.limit_type"
    placeholder="請選擇限制類型"
    style="width: 100%"
    filterable
    clearable
  >
    <el-option
      v-for="type in limitTypes"
      :key="type"
      :label="type"
      :value="type"
    />
  </el-select>
</el-form-item>
```

**Script:**
```javascript
import { getValidationTypes } from '@/api/measurements'

// Changed to ref for dynamic loading
const valueTypes = ref([])
const limitTypes = ref([])

onMounted(async () => {
  // Load validation types from API
  try {
    const validationTypes = await getValidationTypes()
    valueTypes.value = validationTypes.value_types
    limitTypes.value = validationTypes.limit_types
  } catch (error) {
    console.error('Failed to load validation types:', error)
    // Fallback to hardcoded values
    valueTypes.value = ['string', 'integer', 'float']
    limitTypes.value = ['lower', 'upper', 'both', 'equality', 'inequality', 'partial', 'none']
  }
})
```

## Validation Type Reference

### Value Types

| Type | Description | Usage Example |
|------|-------------|---------------|
| `string` | Text/string values | Command responses, SN validation |
| `integer` | Whole numbers | Counts, indices, discrete measurements |
| `float` | Decimal numbers | Voltage, current, frequency measurements |

**Type Casting Logic** (`base.py`):
```python
# StringType
value = str(value)

# IntegerType
value = int(str(value), 0) if isinstance(value, str) else int(value)

# FloatType
value = float(value)
```

### Limit Types

| Type | Description | Validation Logic | Example |
|------|-------------|------------------|---------|
| `lower` | Lower limit only | `value >= lower_limit` | Minimum voltage check |
| `upper` | Upper limit only | `value <= upper_limit` | Maximum current check |
| `both` | Range check | `lower <= value <= upper` | Voltage tolerance: 4.75V - 5.25V |
| `equality` | Exact match | `value == eq_limit` | Expected response string |
| `partial` | Substring match | `eq_limit in value` | Check if response contains keyword |
| `inequality` | Not equal | `value != eq_limit` | Ensure value is not a specific value |
| `none` | No limit | Always passes | Information-only measurements |

**Validation Examples:**
```python
# Both limits - voltage must be within range
limit_type='both', lower_limit=4.75, upper_limit=5.25, value_type='float'
# Pass: 5.0V, 4.8V
# Fail: 4.5V, 5.5V

# Equality - exact string match
limit_type='equality', eq_limit='OK', value_type='string'
# Pass: "OK"
# Fail: "ERROR", "OKAY"

# Partial - keyword search
limit_type='partial', eq_limit='VERSION', value_type='string'
# Pass: "VERSION 1.2.3", "FW_VERSION:2.0"
# Fail: "STATUS:OK", "NO VERSION"

# Lower limit only
limit_type='lower', lower_limit=100, value_type='integer'
# Pass: 100, 150, 200
# Fail: 50, 99

# None - always passes
limit_type='none'
# Pass: Any value
```

## Benefits

### 1. Single Source of Truth
- Validation types defined once in `base.py`
- Frontend automatically reflects backend capabilities
- No synchronization issues

### 2. Automatic Updates
- Adding new type in `base.py` automatically available in UI
- No frontend code changes required
- Reduces deployment coordination

### 3. Type Safety
- Frontend dropdown options guaranteed valid
- Backend validates against same types
- Prevents submission of invalid values

### 4. Maintainability
- Clear ownership: `base.py` owns validation type definitions
- Changes tracked in one location
- Easier to understand system behavior

### 5. Error Resilience
- Fallback to hardcoded values if API fails
- Graceful degradation
- System remains functional during API issues

## Usage Guide

### For Test Plan Creators

1. **Open Test Plan Management**
   - Navigate to "測試計劃管理" page
   - Select Project and Station

2. **Create/Edit Test Item**
   - Click "新增項目" or "編輯"

3. **Select Value Type**
   - Choose from dropdown: `string`, `integer`, `float`
   - Select based on measurement data type
   - Leave empty if not applicable

4. **Select Limit Type**
   - Choose from dropdown: `lower`, `upper`, `both`, `equality`, `inequality`, `partial`, `none`
   - Select based on validation requirements
   - Configure corresponding limit values

5. **Configure Limits**
   - For `lower`: Set "下限值"
   - For `upper`: Set "上限值"
   - For `both`: Set both limits
   - For `equality`/`partial`/`inequality`: Set "等於限制"

### For Developers

#### Adding a New Validation Type

1. **Update Backend** (`backend/app/measurements/base.py`)

```python
# Add new limit type class
class CUSTOM_LIMIT(LimitType):
    """Custom limit constraint"""
    pass

# Update map
LIMIT_TYPE_MAP = {
    # ... existing types
    'custom': CUSTOM_LIMIT,
}

# Add validation logic in validate_result()
if self.limit_type is CUSTOM_LIMIT:
    # Your validation logic here
    pass
```

2. **Frontend Updates Automatically**
   - No code changes needed
   - New option appears in dropdown on next page load
   - Existing forms continue to work

## Troubleshooting

### Dropdown Shows No Options

**Symptom:** Value type or limit type dropdown is empty

**Causes:**
1. API endpoint not responding
2. Network connectivity issue
3. Backend service not running

**Solutions:**
1. Check browser console for API errors
2. Verify backend is running: `docker-compose ps`
3. Check backend logs: `docker-compose logs -f backend`
4. Fallback values should load automatically

### "Invalid limit_type" Error on Save

**Symptom:** Saving test item fails with validation error

**Causes:**
1. Frontend has stale options
2. Backend code changed without redeployment

**Solutions:**
1. Refresh browser page to reload options
2. Clear browser cache
3. Verify backend and frontend are in sync

### Type Validation Not Working

**Symptom:** Test passes when it should fail

**Causes:**
1. Wrong value type selected
2. Limit type doesn't match limit values provided

**Solutions:**
1. Verify value type matches measurement data
2. Check limit type matches your validation intent
3. Review validation logic reference table above

## Technical Details

### Data Flow

```
User opens TestPlanManage.vue
    ↓
onMounted() calls getValidationTypes()
    ↓
GET /api/measurements/validation-types
    ↓
Backend reads LIMIT_TYPE_MAP and VALUE_TYPE_MAP
    ↓
Returns {limit_types: [...], value_types: [...]}
    ↓
Frontend populates valueTypes and limitTypes refs
    ↓
Dropdown options rendered via v-for
    ↓
User selects and saves
    ↓
Backend validates against same MAP definitions
```

### Related Files

**Backend:**
- `backend/app/measurements/base.py` - Validation logic and type definitions
- `backend/app/api/measurements.py` - API endpoint

**Frontend:**
- `frontend/src/api/measurements.js` - API client
- `frontend/src/views/TestPlanManage.vue` - UI component

### Performance Considerations

1. **API Caching**: Options fetched once on component mount
2. **Minimal Payload**: Response is small (~100 bytes)
3. **No Polling**: Static options don't need real-time updates
4. **Fallback**: Hardcoded values prevent UI blocking

## Migration Notes

### Existing Test Plans
- No migration required
- Existing `value_type` and `limit_type` values remain valid
- Dropdowns pre-select existing values on edit

### Compatibility
- Fully backward compatible
- CSV import/export unaffected
- Test execution logic unchanged

## Future Enhancements

1. **Localized Labels**: Display Chinese names for types (下拉值、上限、範圍, etc.)
2. **Type Descriptions**: Show help text explaining each type
3. **Validation Preview**: Show expected validation behavior in UI
4. **Custom Types**: Allow user-defined validation types via admin panel
5. **Type Templates**: Pre-configured type combinations for common scenarios

## Related Documentation

- [Measurement Base Module](../../backend/app/measurements/base.py) - Validation implementation
- [Dynamic Parameter Form Usage](./dynamic-parameter-form-usage.md) - Parameter input system
- [TestPlan Parameters Architecture](./testplan-parameters-architecture.md) - Parameter storage
- [PDTool4 Compatibility](../CLAUDE.md) - System architecture overview
