# `useMeasurementParams.js` — Detailed Code Grammar Explanation

> **File path:** `frontend/src/composables/useMeasurementParams.js`
> **Role:** Vue 3 composable that bridges backend `MEASUREMENT_TEMPLATES` config to the dynamic `DynamicParamForm.vue`
> **Pattern:** Composition API composable with cascading computed properties

---

## 1. Imports (Lines 1–3)

```javascript
import { ref, computed, watch } from 'vue'
import { getMeasurementTemplates, validateMeasurementParams } from '@/api/measurements'
import { ElMessage } from 'element-plus'
```

| Import | Source | Purpose |
|--------|--------|---------|
| `ref` | Vue 3 reactivity API | Creates **reactive references** — wrapping a value so Vue tracks changes |
| `computed` | Vue 3 reactivity API | Creates **derived/computed reactive values** that auto-update when dependencies change |
| `watch` | Vue 3 reactivity API | **Side-effect watcher** — runs a callback when a reactive dependency changes |
| `getMeasurementTemplates` | `@/api/measurements` | API call: `GET /api/measurements/templates` → returns `{templates: Object, test_types: string[]}` |
| `validateMeasurementParams` | `@/api/measurements` | API call: `POST /api/measurements/validate-params` → validates user input against backend schema |
| `ElMessage` | `element-plus` | Element Plus toast notification component for showing success/error messages |

**Grammar note:** The `@/` prefix is a Vite/Webpack path alias resolved to `frontend/src/`.

---

## 2. Composable Export Function (Line 9)

```javascript
export function useMeasurementParams() {
```

This is a **Vue 3 Composition API composable** — a function that encapsulates and reuses stateful logic. By convention:

- The function name starts with `use`
- It returns reactive state and methods for components to consume
- It can be called in `setup()` or `<script setup>` blocks

---

## 3. Reactive State — `ref()` (Lines 11–14)

```javascript
const templates = ref({})
const loading = ref(false)
const currentTestType = ref('')
const currentSwitchMode = ref('')
```

`ref()` wraps a plain value in a reactive container. In JavaScript:

| Variable | Initial Value | Type | Purpose |
|----------|--------------|------|---------|
| `templates` | `{}` | `Ref<Object>` | Stores the full `MEASUREMENT_TEMPLATES` dict from backend |
| `loading` | `false` | `Ref<boolean>` | Guards against concurrent API calls |
| `currentTestType` | `''` | `Ref<string>` | Currently selected test type (e.g. `"PowerSet"`, `"PowerRead"`) |
| `currentSwitchMode` | `''` | `Ref<string>` | Currently selected switch mode (e.g. `"DAQ973A"`, `"MODEL2306"`) |

**Grammar note:** To read/write a `ref` in JavaScript, you use `.value`. In Vue templates, `.value` is automatically unwrapped.

---

## 4. Computed Properties (Lines 17–66)

### 4.1 `testTypes` (Lines 17–19)

```javascript
const testTypes = computed(() => {
  return Object.keys(templates.value)
})
```

- `computed()` takes a **getter function** and returns a read-only `Ref`
- `Object.keys(templates.value)` extracts all top-level keys from the templates object → the list of available test types (e.g. `["PowerSet", "PowerRead", "CommandTest", ...]`)
- This auto-updates whenever `templates.value` changes (reactive dependency tracking)

### 4.2 `switchModes` (Lines 22–27)

```javascript
const switchModes = computed(() => {
  if (!currentTestType.value || !templates.value[currentTestType.value]) {
    return []
  }
  return Object.keys(templates.value[currentTestType.value])
})
```

- Guards: returns `[]` if no test type selected, or if the test type doesn't exist in templates
- Otherwise extracts the **second-level keys** — the instrument/switch modes for the selected test type
- Example: `templates.value["PowerSet"]` → `["DAQ973A", "MODEL2306", ...]`

### 4.3 `currentTemplate` (Lines 30–46)

```javascript
const currentTemplate = computed(() => {
  if (!currentTestType.value) return null

  let switchMode = currentSwitchMode.value
  if (!switchMode && switchModes.value.length === 1) {
    switchMode = switchModes.value[0]
  }
  if (!switchMode) return null

  return templates.value[currentTestType.value]?.[switchMode] || null
})
```

Key logic:

1. **Early return `null`** if no test type selected
2. **Auto-select** switch mode when there's exactly one available (UX optimization — skips a manual selection step)
3. **Return the template object** at `templates[testType][switchMode]`, which contains `{ required: [], optional: [], example: {} }`
4. Uses **optional chaining** (`?.`) to safely access nested properties without throwing `TypeError`

### 4.4 `requiredParams`, `optionalParams`, `allParams`, `exampleParams` (Lines 49–66)

```javascript
const requiredParams = computed(() => currentTemplate.value?.required || [])
const optionalParams = computed(() => currentTemplate.value?.optional || [])
const allParams = computed(() => [...requiredParams.value, ...optionalParams.value])
const exampleParams = computed(() => currentTemplate.value?.example || {})
```

- These are **derived computed properties** that depend on `currentTemplate`
- `allParams` uses the **spread operator** (`...`) to flatten two arrays into one
- `||` provides a **fallback default** when `currentTemplate` is `null` (before template is resolved)

**Dependency chain:**

```
templates → testTypes → switchModes → currentTemplate → requiredParams / optionalParams → allParams
```

---

## 5. Methods

### 5.1 `loadTemplates` (Lines 69–84)

```javascript
const loadTemplates = async () => {
  if (loading.value) return  // 避免重複載入

  loading.value = true
  try {
    const response = await getMeasurementTemplates()
    templates.value = response.templates
    return response
  } catch (error) {
    console.error('Failed to load measurement templates:', error)
    ElMessage.error('載入測量參數模板失敗')
    throw error
  } finally {
    loading.value = false
  }
}
```

Grammar breakdown:

- `async/await` — asynchronous function pattern; `await` pauses execution until the Promise resolves
- **Debounce guard**: `if (loading.value) return` prevents duplicate API calls
- `try/catch/finally` — structured error handling:
  - `try`: normal execution path
  - `catch`: error handling with user notification via `ElMessage.error()`
  - `finally`: always runs — resets `loading` flag regardless of success/failure
- `throw error` — re-throws so the caller can also handle the error

### 5.2 `validateParams` (Lines 87–115)

```javascript
const validateParams = async (parameters) => {
  if (!currentTestType.value) {
    return { valid: false, message: '請先選擇測試類型', missing_params: [], invalid_params: [], suggestions: [] }
  }
  try {
    const result = await validateMeasurementParams(currentTestType.value, currentSwitchMode.value, parameters)
    return result
  } catch (error) {
    console.error('Parameter validation failed:', error)
    return { valid: false, message: error.response?.data?.detail || '參數驗證失敗', missing_params: [], invalid_params: [], suggestions: [] }
  }
}
```

- **Client-side early validation**: checks if test type is selected before making the API call
- **Graceful error fallback**: constructs a valid result object even on failure, so callers don't need to handle exceptions
- `error.response?.data?.detail` — Axios error objects store the HTTP response in `error.response`; optional chaining safely navigates the chain

### 5.3 `inferParamType` (Lines 118–159)

```javascript
const inferParamType = (paramName, exampleValue) => {
  const name = paramName.toLowerCase()
  // ... series of if checks ...
  return 'text'  // default
}
```

This is a **pure function** — no reactive dependencies, just input → output:

- Converts param name to lowercase for case-insensitive matching
- Returns one of: `'number'`, `'select'`, `'text'`
- The commented-out code (lines 123–129) shows the original version missing `'waitmsec'`
- The fix (lines 131–136) adds `name.includes('waitmsec')` to the number detection

**Pattern:** keyword-based type inference — uses `String.includes()` to check if parameter names contain known numeric keywords (`volt`, `curr`, `channel`, `timeout`, etc.)

### 5.4 `getParamOptions` (Lines 162–183)

```javascript
const getParamOptions = (paramName) => {
  const name = paramName.toLowerCase()
  if (name === 'baud') return ['9600', '19200', '38400', '57600', '115200']
  if (name === 'type') return ['DC', 'AC', 'RES', 'TEMP']
  if (name === 'item') return ['volt', 'curr', 'res', 'temp', 'freq']
  if (name === 'operator_judgment') return ['PASS', 'FAIL']
  return []
}
```

Another **pure function** — maps parameter names to dropdown option arrays. Returns `[]` (empty array) for parameters that don't have predefined options (they'll render as text/number inputs instead).

### 5.5 `formatParamLabel` (Lines 186–191)

```javascript
const formatParamLabel = (paramName) => {
  return paramName.replace(/([A-Z])/g, ' $1').trim()
}
```

- Uses a **regular expression** with a capture group and replacement
- `/([A-Z])/g` — matches every uppercase letter (global flag `g`)
- `' $1'` — replaces each match with a space followed by the captured letter
- `.trim()` — removes leading/trailing whitespace
- Example: `"SetVolt"` → `"Set Volt"`, `"WaitmSec"` → `"Waitm Sec"`

---

## 6. Watcher (Lines 194–196)

```javascript
watch(currentTestType, () => {
  currentSwitchMode.value = ''
})
```

- `watch(source, callback)` — runs the callback whenever `currentTestType` changes
- **Cascading reset pattern**: when the user changes the test type, the switch mode is cleared because the previous switch mode may not exist in the new test type's templates
- This prevents stale/invalid state in the cascading selection chain

---

## 7. Return Object (Lines 198–221)

```javascript
return {
  // 狀態
  templates, loading, currentTestType, currentSwitchMode,
  // 計算屬性
  testTypes, switchModes, currentTemplate,
  requiredParams, optionalParams, allParams, exampleParams,
  // 方法
  loadTemplates, validateParams,
  inferParamType, getParamOptions, formatParamLabel
}
```

The composable **exposes a public API** — only the returned properties are accessible to consuming components. Everything else is private closure scope.

---

## 8. Data Flow Diagram

```
Backend MEASUREMENT_TEMPLATES
        │
        ▼ GET /api/measurements/templates
  loadTemplates()
        │
        ▼
   templates (ref<Object>)
        │
        ├──► testTypes (computed) → ["PowerSet", "PowerRead", ...]
        │
        ▼ (user selects testType)
  currentTestType (ref<string>)
        │
        ├──► switchModes (computed) → ["DAQ973A", "MODEL2306", ...]
        │
        ▼ (user selects switchMode, or auto-selected)
  currentSwitchMode (ref<string>)
        │
        ├──► currentTemplate (computed) → { required, optional, example }
        │         │
        │         ├──► requiredParams / optionalParams / allParams
        │         └──► exampleParams
        │
        ▼
  DynamicParamForm.vue renders form fields
        │
        │   inferParamType()  → input type (text/number/select)
        │   getParamOptions() → dropdown options for select inputs
        │   formatParamLabel() → display labels (camelCase → spaced)
        │
        ▼
  validateParams() → POST /api/measurements/validate-params
```

---

## 9. JavaScript Grammar Summary

| Syntax | Example in File | Explanation |
|--------|----------------|-------------|
| `ref()` | `ref({})` | Creates a reactive wrapper; access value via `.value` |
| `computed()` | `computed(() => ...)` | Creates a cached derived value; auto-invalidates when dependencies change |
| `watch()` | `watch(currentTestType, ...)` | Runs callback when source ref changes |
| Arrow function | `() => {}` | Concise function expression; inherits outer `this` |
| Optional chaining | `?.[switchMode]` | Safely accesses nested properties; returns `undefined` instead of throwing |
| Nullish coalescing | `\|\| []` | Provides fallback when left side is `null`/`undefined` |
| Spread operator | `[...a, ...b]` | Expands iterables into individual elements |
| `async/await` | `async () => { await ... }` | Syntactic sugar for Promises; `await` pauses until resolution |
| `try/catch/finally` | Standard JS | Structured error handling; `finally` always executes |
| Regex with groups | `/([A-Z])/g` | Global match of uppercase letters; `$1` references captured group |
| `String.includes()` | `name.includes('volt')` | Case-sensitive substring check |
| `String.toLowerCase()` | `paramName.toLowerCase()` | Converts to lowercase for case-insensitive matching |
| `String.replace()` | `.replace(/([A-Z])/g, ' $1')` | Regex-based string replacement |
| `Object.keys()` | `Object.keys(obj)` | Returns array of own enumerable property names |
| Destructuring (implicit) | `{ valid: false, ... }` | Object literal shorthand (property name = variable name) |

---

## 10. Usage Example in a Component

```vue
<script setup>
import { useMeasurementParams } from '@/composables/useMeasurementParams'

const {
  loading,
  testTypes,
  switchModes,
  currentTestType,
  currentSwitchMode,
  requiredParams,
  optionalParams,
  exampleParams,
  loadTemplates,
  validateParams,
  inferParamType,
  getParamOptions,
  formatParamLabel
} = useMeasurementParams()

// Load templates on mount
onMounted(() => loadTemplates())
</script>
```
