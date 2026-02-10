# Dynamic Parameter Form Not Displaying - Composable Instance Isolation Issue

## Issue Description

**Date:** 2026-02-10
**Component:** `frontend/src/components/DynamicParamForm.vue`
**Severity:** High
**Status:** ✅ Fixed

### Symptom

When editing or creating a test plan item in TestPlanManage.vue:
1. User selects "測試類型" (Test Type) = PowerSet
2. User selects "儀器模式" (Switch Mode) = DAQ973A
3. The "測試參數設定" (Test Parameters) section shows an empty state message:
   > "請先選擇測試類型和儀器模式"

**Expected Behavior:**
The form should display parameter input fields based on the selected test type and switch mode (e.g., Instrument, Channel, Item, Volt, Curr for PowerSet + DAQ973A).

**Actual Behavior:**
No parameter fields are rendered, only the empty state placeholder is shown.

### Affected Files

- `frontend/src/views/TestPlanManage.vue` (lines 368-373, 503-510)
- `frontend/src/components/DynamicParamForm.vue` (entire component)
- `frontend/src/composables/useMeasurementParams.js` (lines 1-202)

## Root Cause Analysis

### Problem: Vue Composable Instance Isolation

The issue stems from how Vue 3 Composition API composables work:

1. **Multiple Independent Instances Created:**
   - `TestPlanManage.vue` calls `useMeasurementParams()` → Instance A
   - `DynamicParamForm.vue` calls `useMeasurementParams()` → Instance B
   - Each call creates a **separate reactive state** with its own `templates` ref

2. **Data Not Shared:**
   - `TestPlanManage.vue` loads templates via `loadTemplates()` into Instance A's `templates.value`
   - `DynamicParamForm.vue` Instance B has `templates.value = {}` (empty)
   - The child component never receives the loaded template data

3. **Reactive Chain Breaks:**
   ```
   TestPlanManage (Instance A)
   ├── templates.value = {...loaded data...}
   └── passes props → testType="PowerSet", switchMode="DAQ973A"

   DynamicParamForm (Instance B)
   ├── templates.value = {} ← EMPTY!
   ├── currentTemplate = computed(() => templates.value[testType][switchMode])
   ├── currentTemplate.value = null ← Lookup fails
   ├── requiredParams.value = [] ← Empty
   ├── allParams.value = [] ← Empty
   └── hasParams.value = false ← Triggers empty state
   ```

### Why This Happens

**Composable Design Pattern:**
- Composables with reactive state (`ref`, `reactive`) create **new instances** per invocation
- Unlike Pinia stores, composables don't share state across components by default
- This is intentional - composables are meant for **reusable logic**, not global state

**Our Misuse:**
- We used `useMeasurementParams()` as if it were a global store
- We expected `templates` loaded in parent to be available in child
- This violates the composable pattern for stateful data

## Solution

### Strategy: Props-Based Data Passing

Instead of relying on shared composable state, we pass the loaded templates from parent to child via props.

### Implementation Steps

#### 1. Export `templates` from Parent Composable

**File:** `frontend/src/views/TestPlanManage.vue`

```javascript
// Before (line 503-510)
const {
  loadTemplates,
  testTypes,
  switchModes,
  currentTestType,
  currentSwitchMode
} = useMeasurementParams()

// After
const {
  loadTemplates,
  testTypes,
  switchModes,
  currentTestType,
  currentSwitchMode,
  templates  // ← NEW: Export templates for child component
} = useMeasurementParams()
```

#### 2. Pass Templates as Prop to Child Component

**File:** `frontend/src/views/TestPlanManage.vue` (line 368-373)

```vue
<!-- Before -->
<DynamicParamForm
  v-model="editingItem.parameters"
  :test-type="editingItem.test_type"
  :switch-mode="editingItem.switch_mode"
  @validation-change="handleParamValidation"
/>

<!-- After -->
<DynamicParamForm
  v-model="editingItem.parameters"
  :test-type="editingItem.test_type"
  :switch-mode="editingItem.switch_mode"
  :templates="templates"
  @validation-change="handleParamValidation"
/>
```

#### 3. Accept Templates Prop in Child Component

**File:** `frontend/src/components/DynamicParamForm.vue`

```javascript
// Add new prop definition
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  testType: {
    type: String,
    default: ''
  },
  switchMode: {
    type: String,
    default: ''
  },
  // NEW: Receive templates from parent to avoid instance isolation
  templates: {
    type: Object,
    default: () => ({})
  }
})
```

#### 4. Refactor Child to Use Prop Data Instead of Composable State

**File:** `frontend/src/components/DynamicParamForm.vue`

```javascript
// Before - Creates new composable instance with empty templates
const {
  currentTestType,
  currentSwitchMode,
  requiredParams,
  optionalParams,
  exampleParams,
  inferParamType,
  getParamOptions,
  formatParamLabel
} = useMeasurementParams()

// After - Only import utility functions, manage state locally
const {
  inferParamType,      // ← Utility function (stateless)
  getParamOptions,     // ← Utility function (stateless)
  formatParamLabel     // ← Utility function (stateless)
} = useMeasurementParams()

// Local state management
const currentTestType = ref(props.testType)
const currentSwitchMode = ref(props.switchMode)

// Sync props to local state
watch(() => props.testType, (val) => {
  currentTestType.value = val
}, { immediate: true })

watch(() => props.switchMode, (val) => {
  currentSwitchMode.value = val
}, { immediate: true })

// Compute template from props.templates (not composable)
const currentTemplate = computed(() => {
  if (!currentTestType.value || !props.templates || Object.keys(props.templates).length === 0) {
    return null
  }

  const switchMode = currentSwitchMode.value
  if (!switchMode) {
    return null
  }

  return props.templates[currentTestType.value]?.[switchMode] || null
})

// Compute parameters from local currentTemplate
const requiredParams = computed(() => {
  return currentTemplate.value?.required || []
})

const optionalParams = computed(() => {
  return currentTemplate.value?.optional || []
})

const exampleParams = computed(() => {
  return currentTemplate.value?.example || {}
})
```

## Verification

### Test Steps

1. Clear browser cache (Ctrl+Shift+R / Cmd+Shift+R)
2. Navigate to "測試計劃管理" (Test Plan Management)
3. Click "新增項目" (Add Item)
4. Select "測試類型" = PowerSet
5. Select "儀器模式" = DAQ973A
6. **Expected Result:** Parameter fields should appear:
   - Instrument (required)
   - Channel (required)
   - Item (required)
   - Volt (optional)
   - Curr (optional)
   - Sense (optional)
   - Range (optional)

### API Validation

Check that backend returns correct template structure:

```bash
curl -s http://localhost:9100/api/measurements/templates | grep -A 20 '"PowerSet"'
```

Expected JSON structure:
```json
{
  "templates": {
    "PowerSet": {
      "DAQ973A": {
        "required": ["Instrument", "Channel", "Item"],
        "optional": ["Volt", "Curr", "Sense", "Range"],
        "example": {
          "Instrument": "daq973a_1",
          "Channel": "101",
          "Item": "volt",
          "Volt": "5.0",
          "Curr": "1.0"
        }
      }
    }
  }
}
```

## Key Learnings

### Composable Best Practices

1. **Stateless Utility Functions:**
   - ✅ Safe to call multiple times: `formatParamLabel()`, `inferParamType()`
   - No shared state, pure functions

2. **Stateful Data Management:**
   - ❌ Don't use composables for global state that needs to be shared
   - ✅ Use Pinia stores for cross-component reactive state
   - ✅ Use props for parent-to-child data flow

3. **When to Use Each Pattern:**

   | Use Case | Pattern | Example |
   |----------|---------|---------|
   | Reusable logic (no state) | Composable | `useValidation()`, `useFormatter()` |
   | Global state (cross-component) | Pinia Store | `useAuthStore()`, `useProjectStore()` |
   | Parent-child data | Props + Emit | `templates` prop in this fix |
   | Component-local state | `ref`, `reactive` | Form inputs, UI toggles |

### Architecture Insights

**The Rule of Thumb:**
> If you expect data loaded in Component A to automatically appear in Component B, you need **global state** (Pinia), not a **composable**.

**Composables are for:**
- Extracting reusable logic
- Avoiding code duplication
- Organizing component code

**Pinia Stores are for:**
- Cross-component shared state
- Persistent data (localStorage sync)
- Application-wide state management

## Alternative Solution (Not Implemented)

### Option: Convert to Pinia Store

If we needed templates in many components, we could create a dedicated store:

```javascript
// stores/measurement.js
import { defineStore } from 'pinia'
import { getMeasurementTemplates } from '@/api/measurements'

export const useMeasurementStore = defineStore('measurement', {
  state: () => ({
    templates: {},
    loading: false
  }),

  getters: {
    testTypes: (state) => Object.keys(state.templates),

    getSwitchModes: (state) => (testType) => {
      return Object.keys(state.templates[testType] || {})
    },

    getTemplate: (state) => (testType, switchMode) => {
      return state.templates[testType]?.[switchMode] || null
    }
  },

  actions: {
    async loadTemplates() {
      if (this.loading) return
      this.loading = true
      try {
        const response = await getMeasurementTemplates()
        this.templates = response.templates
      } finally {
        this.loading = false
      }
    }
  }
})
```

**Why we didn't use this:**
- Templates are only needed in TestPlanManage.vue and its child DynamicParamForm.vue
- Props-based solution is simpler for this limited scope
- Avoids adding another store to the application

## Related Issues

- None (first occurrence of this pattern)

## Future Considerations

If we add more components that need measurement templates:
1. Consider migrating to Pinia store approach
2. Document the decision in CLAUDE.md
3. Create `useMeasurementStore()` following the alternative solution above

## References

- Vue 3 Composables: https://vuejs.org/guide/reusability/composables.html
- Pinia vs Composables: https://pinia.vuejs.org/introduction.html#comparison-with-vue-3-composition-api
- Props Documentation: https://vuejs.org/guide/components/props.html
