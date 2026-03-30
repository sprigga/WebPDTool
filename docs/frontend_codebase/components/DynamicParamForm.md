# DynamicParamForm.vue 程式碼語法詳解

**檔案路徑：** `frontend/src/components/DynamicParamForm.vue`

**用途：** 根據測試類型（testType）與儀器模式（switchMode）動態渲染量測參數表單欄位，並提供即時參數驗證。

---

## 目錄

1. [組件概觀](#1-組件概觀)
2. [Template 語法解析](#2-template-語法解析)
3. [Script 語法解析](#3-script-語法解析)
   - [Props 定義](#31-props-定義)
   - [Emits 定義](#32-emits-定義)
   - [Composable 使用策略](#33-composable-使用策略)
   - [響應式狀態](#34-響應式狀態)
   - [Watch 監聽器](#35-watch-監聽器)
   - [計算屬性](#36-計算屬性)
   - [工具函式](#37-工具函式)
   - [事件處理](#38-事件處理)
4. [Style 作用域樣式](#4-style-作用域樣式)
5. [資料流向圖](#5-資料流向圖)
6. [設計決策說明](#6-設計決策說明)

---

## 1. 組件概觀

`DynamicParamForm` 是一個「**資料驅動式表單（Data-Driven Form）**」組件。

- **不硬編碼欄位**：欄位結構完全由父組件傳入的 `templates` prop 決定
- **三種輸入類型**：自動推斷每個參數應使用數字輸入、下拉選單或文字輸入
- **v-model 雙向綁定**：父組件可透過 `v-model` 直接存取表單值
- **即時驗證**：必填欄位未填時發出 `validation-change` 事件通知父組件

---

## 2. Template 語法解析

### 2.1 根容器

```html
<div class="dynamic-param-form">
```

最外層 `div` 提供 CSS 作用域的掛載點，`scoped` 樣式將以此為邊界。

---

### 2.2 條件渲染：`v-if` / `v-else`

```html
<div v-if="hasParams" class="param-fields">
  ...
</div>

<el-empty
  v-else
  description="請先選擇測試類型和儀器模式"
  :image-size="100"
/>
```

- **`v-if="hasParams"`**：`hasParams` 是計算屬性，當 `allParams` 陣列長度 > 0 時為 `true`
- **`v-else`**：當沒有參數可顯示時，渲染 Element Plus 的空狀態組件 `<el-empty>`
- **`:image-size="100"`**：用 `:` (v-bind 縮寫) 將數字 `100` 綁定（不加 `:` 會傳入字串 `"100"`）

---

### 2.3 佈局：`el-row` / `el-col`

```html
<el-row :gutter="20">
  <el-col
    v-for="param in allParams"
    :key="param.name"
    :span="12"
  >
```

| 屬性 | 說明 |
|------|------|
| `:gutter="20"` | 欄位間距 20px（Element Plus Grid System） |
| `v-for="param in allParams"` | 遍歷計算屬性 `allParams`，每個元素命名為 `param` |
| `:key="param.name"` | Vue 的 diff 算法需要唯一 key，避免重複渲染問題 |
| `:span="12"` | 24欄制佈局，span=12 表示每欄佔一半寬度（2欄並排） |

---

### 2.4 表單項目：`el-form-item`

```html
<el-form-item
  :label="formatParamLabel(param.name)"
  :required="param.required"
>
```

- **`:label`**：呼叫 `formatParamLabel()` 函式將參數名（如 `channelA`）轉為顯示標籤（如 `Channel A`）
- **`:required`**：傳入布林值，Element Plus 會自動顯示紅色星號標記

---

### 2.5 三種輸入組件（條件渲染鏈）

#### 數字輸入：`v-if`

```html
<el-input-number
  v-if="param.type === 'number'"
  v-model="localParams[param.name]"
  :placeholder="param.example"
  :precision="getNumberPrecision(param.name)"
  :controls="false"
  style="width: 100%"
  @change="handleChange"
/>
```

| 屬性/事件 | 說明 |
|-----------|------|
| `v-if="param.type === 'number'"` | 當推斷類型為數字時顯示 |
| `v-model="localParams[param.name]"` | 雙向綁定到本地狀態物件的對應 key |
| `:precision="getNumberPrecision(param.name)"` | 依參數名決定小數位數（0~3位） |
| `:controls="false"` | 隱藏 ±1 按鈕，提供更簡潔的外觀 |
| `@change="handleChange"` | 值改變後觸發（數字輸入用 `change`，非 `input`） |

#### 下拉選單：`v-else-if`

```html
<el-select
  v-else-if="param.type === 'select'"
  v-model="localParams[param.name]"
  :placeholder="param.example"
  style="width: 100%"
  clearable
  @change="handleChange"
>
  <el-option
    v-for="option in param.options"
    :key="option"
    :label="option"
    :value="option"
  />
</el-select>
```

- **`clearable`**：布林 prop，直接寫屬性名等同 `:clearable="true"`，允許清空選擇
- **`v-for="option in param.options"`**：渲染 `getParamOptions()` 返回的選項陣列
- **`:label="option"` 與 `:value="option"`**：此處 label（顯示文字）和 value（實際值）相同

#### 文字輸入：`v-else`（預設）

```html
<el-input
  v-else
  v-model="localParams[param.name]"
  :placeholder="param.example"
  clearable
  @input="handleChange"
/>
```

- **`@input`**：文字輸入用 `input` 事件（每次按鍵即觸發），而非 `change`（失焦才觸發）
- 這是預設情況，覆蓋所有非 `number` / `select` 類型

> **事件差異說明：**
> - `@input`：文字輸入框每次字元變動就觸發 → 即時驗證
> - `@change`：數字/選單組件值確定後觸發 → 避免中間狀態誤觸

---

### 2.6 參數提示區塊

```html
<div v-if="param.required" class="param-hint">
  <el-text size="small" type="info">
    必填 · 範例: {{ param.example }}
  </el-text>
</div>
<div v-else class="param-hint">
  <el-text size="small" type="info">
    選填 · 範例: {{ param.example }}
  </el-text>
</div>
```

- **`{{ param.example }}`**：Mustache 插值語法，渲染 `exampleParams` 中對應的範例值
- 依 `param.required` 顯示「必填」或「選填」文字前綴

---

### 2.7 驗證錯誤提示

```html
<el-alert
  v-if="validationErrors.length > 0"
  type="warning"
  :closable="false"
  style="margin-top: 10px"
>
  <template #title>
    參數驗證錯誤
  </template>
  <ul style="margin: 5px 0; padding-left: 20px">
    <li v-for="(error, index) in validationErrors" :key="index">
      {{ error }}
    </li>
  </ul>
</el-alert>
```

- **`v-if="validationErrors.length > 0"`**：只有存在錯誤時才渲染，避免空白警告框
- **`<template #title>`**：具名插槽（Named Slot）語法，`#title` 是 `v-slot:title` 的縮寫
- **`v-for="(error, index) in validationErrors"`**：解構賦值取得值和索引，`index` 用作 key

---

## 3. Script 語法解析

### 3.1 Props 定義

```javascript
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
  templates: {
    type: Object,
    default: () => ({})
  }
})
```

| Prop | 類型 | 說明 |
|------|------|------|
| `modelValue` | `Object` | v-model 的值（當前表單參數物件），遵循 Vue 3 v-model 慣例 |
| `testType` | `String` | 測試類型（如 `"PowerSet"`），用於查找對應模板 |
| `switchMode` | `String` | 儀器型號（如 `"DAQ973A"`），與 testType 共同確定模板 |
| `templates` | `Object` | 從父組件傳入的完整模板資料（`MEASUREMENT_TEMPLATES`），避免重複 API 呼叫 |

> **注意：** 物件/陣列類型的 `default` 必須使用函式形式 `() => ({})` 而非直接 `{}`，
> 否則所有組件實例會共享同一個物件參考，造成狀態污染。

---

### 3.2 Emits 定義

```javascript
const emit = defineEmits(['update:modelValue', 'validation-change'])
```

| Event | 說明 |
|-------|------|
| `update:modelValue` | v-model 的標準更新事件，父組件透過 `v-model` 接收更新後的參數 |
| `validation-change` | 傳遞布林值 `true`（驗證通過）或 `false`（有錯誤），通知父組件是否可提交 |

---

### 3.3 Composable 使用策略

```javascript
// 原有程式碼: 創建新的 composable 實例導致模板數據不同步
// const {
//   currentTestType,
//   currentSwitchMode,
//   requiredParams,
//   optionalParams,
//   exampleParams,
//   inferParamType,
//   getParamOptions,
//   formatParamLabel
// } = useMeasurementParams()

// 修正: 只使用工具函數，模板數據從 props 接收
const {
  inferParamType,
  getParamOptions,
  formatParamLabel
} = useMeasurementParams()
```

這段保留的注解記錄了**重要設計決策**：

- **問題**：若在此組件內部獨立呼叫 `useMeasurementParams()`，會建立一個新的 composable 實例，其內部狀態（`requiredParams` 等）與父組件的實例不同步
- **解法**：只從 composable 取出**純函式工具**（`inferParamType`, `getParamOptions`, `formatParamLabel`），而把**狀態資料**（`templates`）改由 props 傳入
- **模式名稱**：這是「**狀態提升（Lifting State Up）**」模式 — 狀態統一由父組件管理

---

### 3.4 響應式狀態

```javascript
const currentTestType = ref(props.testType)
const currentSwitchMode = ref(props.switchMode)
const validationErrors = ref([])
const localParams = ref({ ...props.modelValue })
```

| 變數 | 說明 |
|------|------|
| `currentTestType` | 本地鏡像 `props.testType`，供 computed 使用（Vue 3 不能直接在 computed 中寫 props） |
| `currentSwitchMode` | 本地鏡像 `props.switchMode` |
| `validationErrors` | 驗證錯誤字串陣列 `ref<string[]>` |
| `localParams` | **淺拷貝** `props.modelValue`（`{ ...props.modelValue }`），避免直接 mutate prop |

> **`ref` vs `reactive`：**
> - `ref` 包裹任意值，存取需 `.value`，適合單一值或需整體替換的物件
> - `reactive` 只包裹物件，存取不需 `.value`，但不能整體替換（`localParams = {}` 會失去響應性）
> - 此處用 `ref` 是因為 watch 的替換賦值 `localParams.value = { ...val }` 語意更清晰

---

### 3.5 Watch 監聽器

#### 同步 props 到本地狀態

```javascript
watch(() => props.testType, (val) => {
  currentTestType.value = val
}, { immediate: true })

watch(() => props.switchMode, (val) => {
  currentSwitchMode.value = val
}, { immediate: true })
```

- **`() => props.testType`**：getter 函式形式，用於監聽 prop 的變化（不能直接寫 `props.testType`，那是取值而非監聽）
- **`{ immediate: true }`**：組件掛載時立即執行一次，確保初始值同步

#### 同步 modelValue

```javascript
watch(() => props.modelValue, (val) => {
  localParams.value = { ...val }
}, { deep: true })
```

- **`{ deep: true }`**：深度監聽物件內部屬性變化，即使物件參考未改變也能偵測

#### 觸發即時驗證

```javascript
watch(() => localParams.value, validateParams, { deep: true, immediate: true })
```

- 監聽 `localParams` 的深層變化，每次變動都重新驗證
- `immediate: true` 確保初始渲染時就進行一次驗證

#### 清空驗證錯誤（模板切換時）

```javascript
watch([currentTestType, currentSwitchMode], () => {
  validationErrors.value = []
})
```

- **陣列語法**：同時監聽多個響應式來源，任一變化都觸發
- 當使用者切換測試類型或儀器模式時，清空舊的驗證錯誤（因為新模板的必填欄位不同）

---

### 3.6 計算屬性

#### currentTemplate

```javascript
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
```

- 從 `props.templates` 取出 `templates[testType][switchMode]` 的模板物件
- **`?.`（可選鏈）**：若 `props.templates[currentTestType.value]` 不存在，回傳 `undefined` 而非拋出錯誤
- **`|| null`**：若結果為 `undefined`，統一回傳 `null`

#### requiredParams / optionalParams / exampleParams

```javascript
const requiredParams = computed(() => currentTemplate.value?.required || [])
const optionalParams = computed(() => currentTemplate.value?.optional || [])
const exampleParams  = computed(() => currentTemplate.value?.example  || {})
```

- 三個計算屬性都依賴 `currentTemplate`，形成**計算屬性鏈**
- 使用 `|| []` / `|| {}` 提供安全的預設值，避免後續遍歷時出錯

#### allParams（核心）

```javascript
const allParams = computed(() => {
  const params = []

  requiredParams.value.forEach(name => {
    params.push({
      name,
      required: true,
      type: inferParamType(name, exampleParams.value[name]),
      options: getParamOptions(name),
      example: String(exampleParams.value[name] || '')
    })
  })

  optionalParams.value.forEach(name => {
    params.push({
      name,
      required: false,
      type: inferParamType(name, exampleParams.value[name]),
      options: getParamOptions(name),
      example: String(exampleParams.value[name] || '')
    })
  })

  return params
})
```

- 將必填/選填參數名稱清單轉換為表單需要的**富物件陣列**
- `inferParamType(name, exampleValue)` — 根據參數名和範例值推斷 `'number'`/`'select'`/`'string'`
- `getParamOptions(name)` — 若為 `select` 類型，返回選項陣列；否則返回空陣列
- **`String(...)`**：確保 `example` 永遠是字串，避免 placeholder 顯示為 `undefined`
- **必填優先排序**：必填參數先加入陣列，表單中顯示在上方

---

### 3.7 工具函式

#### getNumberPrecision

```javascript
const getNumberPrecision = (paramName) => {
  const name = paramName.toLowerCase()
  if (name.includes('channel'))   return 0  // 通道號為整數
  if (name.includes('volt') || name.includes('curr')) return 2  // 電壓/電流 2 位
  if (name.includes('frequency') || name.includes('bandwidth')) return 3  // 頻率 3 位
  return 2  // 預設 2 位
}
```

- 依參數名稱中的**關鍵字**決定小數精度
- `toLowerCase()` 確保大小寫不敏感比對

---

### 3.8 事件處理

#### handleChange

```javascript
const handleChange = () => {
  emit('update:modelValue', { ...localParams.value })
  validateParams()
}
```

- **淺拷貝 `{ ...localParams.value }`**：傳出新物件而非原始參考，確保父組件能偵測到變化
- 每次值變更都同時驗證

#### validateParams

```javascript
const validateParams = () => {
  const errors = []
  requiredParams.value.forEach(paramName => {
    const value = localParams.value[paramName]
    if (value === undefined || value === null || value === '') {
      errors.push(`參數 "${formatParamLabel(paramName)}" 為必填`)
    }
  })
  validationErrors.value = errors
  emit('validation-change', errors.length === 0)
}
```

- 遍歷必填參數，檢查三種「空值」情況：`undefined`（未設定）、`null`（明確清空）、`''`（空字串）
- `emit('validation-change', errors.length === 0)`：傳出布林值，`true` 表示驗證通過

---

## 4. Style 作用域樣式

```css
<style scoped>
.dynamic-param-form {
  padding: 10px 0;
}

.param-fields {
  min-height: 100px;
}

.param-hint {
  margin-top: 4px;
  line-height: 1.2;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-empty) {
  padding: 30px 0;
}
</style>
```

| 選擇器 | 說明 |
|--------|------|
| `scoped` | Vue 的 CSS 作用域，自動為選擇器加上唯一 hash，不影響其他組件 |
| `.param-fields { min-height: 100px }` | 設定最小高度，防止無參數時版面高度塌縮 |
| `:deep(...)` | **穿透作用域**語法（舊版 `::v-deep`），修改 Element Plus 內部組件的樣式 |
| `:deep(.el-form-item__label)` | 加粗表單標籤，提升可讀性 |

---

## 5. 資料流向圖

```
父組件
  │
  ├─ props.templates (MEASUREMENT_TEMPLATES 全量資料)
  ├─ props.testType  (當前選擇的測試類型)
  ├─ props.switchMode (當前選擇的儀器型號)
  └─ props.modelValue (當前表單值物件)
         │
         ▼
DynamicParamForm.vue
  │
  ├─ currentTemplate (computed) ──→ 取出 templates[testType][switchMode]
  │
  ├─ requiredParams  (computed) ──→ 必填參數名稱陣列
  ├─ optionalParams  (computed) ──→ 選填參數名稱陣列
  ├─ exampleParams   (computed) ──→ 範例值物件
  │
  ├─ allParams       (computed) ──→ 富物件陣列 (name, required, type, options, example)
  │         │
  │         ▼
  │    v-for 渲染 el-input-number / el-select / el-input
  │         │
  │         ▼
  └─ localParams (ref) ←── v-model 雙向綁定
         │
         ▼
  handleChange() ──→ emit('update:modelValue', { ...localParams })
                └──→ validateParams() ──→ emit('validation-change', boolean)
         │
         ▼
      父組件
```

---

## 6. 設計決策說明

### 6.1 為何不在組件內部建立完整的 composable 實例？

`useMeasurementParams()` 會在首次呼叫時從 API 取得模板資料並儲存在內部 `ref` 中。若在此組件內重新呼叫，會：

1. 觸發額外的 API 請求（重複浪費）
2. 建立獨立的響應式狀態，與父組件的資料**不同步**

**解法：** 父組件負責呼叫 composable 並管理 `templates` 狀態，透過 prop 傳入子組件。子組件只使用 composable 的**工具函式**部分（`inferParamType`, `getParamOptions`, `formatParamLabel`）。

### 6.2 為何使用 localParams 而非直接操作 modelValue？

Vue 3 的 `props` 是**只讀**的（Single Source of Truth 原則）。直接修改 `props.modelValue` 會：

- 在開發模式下出現警告
- 破壞父子組件的數據流方向性

透過 `localParams` 作為中間層，遵循「**先本地更新，再 emit 通知父組件**」的雙向綁定慣例。

### 6.3 計算屬性鏈設計

```
currentTemplate → requiredParams → allParams → 表單渲染
               ↘ optionalParams ↗
               ↘ exampleParams ↗
```

這種**單向依賴**設計確保當 `testType` 或 `switchMode` 改變時，整條鏈自動重新計算，Vue 的響應式系統會精確追蹤依賴關係，只更新必要部分。
