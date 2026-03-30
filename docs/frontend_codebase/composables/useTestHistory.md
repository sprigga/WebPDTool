# useTestHistory.js — 程式碼語法詳解

**檔案位置：** `frontend/src/composables/useTestHistory.js`
**最後更新：** 2026-03-27

---

## 概覽

`useTestHistory` 是一個 **Vue 3 Composable**，負責測試歷史資料的抓取、狀態管理與衍生計算。它被 `TestResults.vue` 的「測試歷史」Tab 使用，提供依日期分組的 session 資料與每日統計。

---

## 完整原始碼

```javascript
// frontend/src/composables/useTestHistory.js
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { queryTestSessions } from '@/api/testResults'
import { formatDateKey } from '@/utils/dateHelpers'

export function useTestHistory() {
  const sessions = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Group sessions by date for timeline view
  const sessionsByDate = computed(() => {
    const grouped = {}
    sessions.value.forEach(session => {
      const dateKey = formatDateKey(session.start_time)
      if (!dateKey) return
      if (!grouped[dateKey]) {
        grouped[dateKey] = []
      }
      grouped[dateKey].push(session)
    })
    return grouped
  })

  // Calculate daily statistics
  const dailyStats = computed(() => {
    const stats = {}
    Object.entries(sessionsByDate.value).forEach(([date, daySessions]) => {
      stats[date] = {
        total: daySessions.length,
        pass: daySessions.filter(s => s.final_result === 'PASS').length,
        fail: daySessions.filter(s => s.final_result === 'FAIL').length,
        abort: daySessions.filter(s => s.final_result === 'ABORT').length
      }
    })
    return stats
  })

  // Fetch sessions with date range and improved error handling
  const fetchSessions = async (params) => {
    loading.value = true
    error.value = null
    try {
      const data = await queryTestSessions(params)
      sessions.value = Array.isArray(data) ? data : []

      // User feedback for empty results (non-blocking)
      if (sessions.value.length === 0) {
        error.value = 'No sessions found for the selected criteria'
      }
    } catch (err) {
      // Extract meaningful error message from response
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load sessions'
      error.value = errorMsg
      sessions.value = []
      ElMessage.error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  return {
    sessions,
    sessionsByDate,
    dailyStats,
    loading,
    error,
    fetchSessions
  }
}
```

---

## 逐行語法解析

### 第 1 行：模組路徑註解

```javascript
// frontend/src/composables/useTestHistory.js
```

純粹的單行 JavaScript 註解（`//`），標示檔案在專案中的相對路徑，方便開發者快速定位來源。

---

### 第 2–5 行：ES Module Imports

```javascript
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { queryTestSessions } from '@/api/testResults'
import { formatDateKey } from '@/utils/dateHelpers'
```

| 語法 | 說明 |
|------|------|
| `import { ... } from '...'` | ES6 **具名匯入（Named Import）**，只引入所需成員，減少打包體積 |
| `from 'vue'` | 從 Vue 3 核心函式庫取得響應式 API |
| `from 'element-plus'` | 從 Element Plus UI 套件取得訊息提示組件 |
| `from '@/api/testResults'` | `@` 是 Vite 設定的路徑別名，指向 `frontend/src/`，等同 `../api/testResults` |
| `from '@/utils/dateHelpers'` | 專案內部工具函式，處理日期格式轉換 |

**引入的成員說明：**

- **`ref`** — 建立**基本型別響應式狀態**（primitive reactive state）
- **`computed`** — 建立**衍生響應式值**（依賴變動時自動重新計算）
- **`ElMessage`** — Element Plus 的全域訊息提示（Toast 通知）
- **`queryTestSessions`** — 呼叫後端 `GET /api/results/sessions` 的 Axios 封裝函式
- **`formatDateKey`** — 將 `ISO datetime` 字串轉為日期鍵值（如 `"2026-03-27"`）

---

### 第 7 行：Composable 函式宣告

```javascript
export function useTestHistory() {
```

| 語法 | 說明 |
|------|------|
| `export function` | 具名匯出函式，允許其他檔案以 `import { useTestHistory }` 引入 |
| `useTestHistory` | **Composable 命名慣例**：Vue 3 規定 composable 函式名稱必須以 `use` 開頭，表示「使用某功能」 |
| `()` | 無參數。狀態在函式內部初始化，呼叫方透過回傳值存取 |

> **重要：** 每次呼叫 `useTestHistory()` 都會建立**獨立的響應式作用域**（scope），彼此不共享狀態。

---

### 第 8–10 行：響應式狀態宣告

```javascript
const sessions = ref([])
const loading = ref(false)
const error = ref(null)
```

**`ref(initialValue)`** 語法說明：

| 變數 | 初始值 | 型別 | 用途 |
|------|--------|------|------|
| `sessions` | `[]` | `Ref<Array>` | 儲存從後端取得的 session 陣列 |
| `loading` | `false` | `Ref<Boolean>` | 標記 API 請求進行中（控制 loading spinner） |
| `error` | `null` | `Ref<String\|null>` | 儲存錯誤訊息字串，`null` 表示無錯誤 |

**`ref` 的底層機制：**

`ref()` 會將值包裝成一個具有 `.value` 屬性的響應式物件（`Ref` 物件）。在 JavaScript 邏輯中必須用 `.value` 存取，在模板（`<template>`）中 Vue 會自動解包（auto-unwrap）。

```javascript
// JavaScript 中
sessions.value.push(newSession)   // 必須加 .value
loading.value = true

// 模板中（自動解包）
// <div v-if="loading">...</div>  不需要 .value
```

---

### 第 13–24 行：computed — sessionsByDate（依日期分組）

```javascript
const sessionsByDate = computed(() => {
  const grouped = {}
  sessions.value.forEach(session => {
    const dateKey = formatDateKey(session.start_time)
    if (!dateKey) return
    if (!grouped[dateKey]) {
      grouped[dateKey] = []
    }
    grouped[dateKey].push(session)
  })
  return grouped
})
```

#### `computed(() => { ... })` 語法

- 接收一個 **getter 函式**（無副作用的純函式）
- 回傳值是唯讀的 `ComputedRef`
- **自動依賴追蹤**：函式內部存取 `sessions.value` 時，Vue 自動記錄此依賴關係；`sessions` 變動時自動重新執行 getter

#### 邏輯步驟分解

```javascript
const grouped = {}   // 建立空物件作為分組容器
```

`{}` 是 JavaScript 的**物件字面量（Object Literal）**，此處用作動態鍵值對（key-value map），最終結構為：

```javascript
{
  "2026-03-25": [session1, session2],
  "2026-03-26": [session3],
  ...
}
```

```javascript
sessions.value.forEach(session => {
```

- `sessions.value` — 透過 `.value` 解包 ref，取得原始陣列
- `.forEach(callback)` — 陣列迭代，對每個元素執行 callback（無回傳值）
- `session => { ... }` — ES6 **箭頭函式（Arrow Function）**，語法比 `function(session){}` 更簡潔；箭頭函式不綁定自己的 `this`

```javascript
const dateKey = formatDateKey(session.start_time)
if (!dateKey) return
```

- `session.start_time` — 存取 session 物件的 `start_time` 屬性（ISO 格式字串，如 `"2026-03-27T08:30:00"`）
- `formatDateKey(...)` — 轉為日期字串（`"2026-03-27"`）；若輸入無效則回傳 `null`/`undefined`
- `if (!dateKey) return` — **防禦性程式設計（Defensive Programming）**：`!null` 為 `true`，跳過無效資料，避免以 `"null"` 或 `"undefined"` 作為鍵值污染 `grouped`

```javascript
if (!grouped[dateKey]) {
  grouped[dateKey] = []
}
grouped[dateKey].push(session)
```

- `grouped[dateKey]` — **動態屬性存取（Bracket Notation）**，等同 `grouped["2026-03-27"]`
- `if (!grouped[dateKey])` — 若該日期鍵尚不存在（值為 `undefined`，falsy），初始化為空陣列
- `.push(session)` — 將當前 session 加入對應日期的陣列

---

### 第 27–38 行：computed — dailyStats（每日統計）

```javascript
const dailyStats = computed(() => {
  const stats = {}
  Object.entries(sessionsByDate.value).forEach(([date, daySessions]) => {
    stats[date] = {
      total: daySessions.length,
      pass: daySessions.filter(s => s.final_result === 'PASS').length,
      fail: daySessions.filter(s => s.final_result === 'FAIL').length,
      abort: daySessions.filter(s => s.final_result === 'ABORT').length
    }
  })
  return stats
})
```

#### 依賴鏈（Dependency Chain）

`dailyStats` 依賴 `sessionsByDate`，而 `sessionsByDate` 依賴 `sessions`。因此依賴鏈為：

```
sessions (ref) → sessionsByDate (computed) → dailyStats (computed)
```

`sessions` 更新 → `sessionsByDate` 自動重算 → `dailyStats` 自動重算。

#### `Object.entries(sessionsByDate.value)`

- `sessionsByDate.value` — 解包 computed ref（computed 也是 ref，需 `.value`）
- `Object.entries(obj)` — 回傳 `[[key, value], ...]` 二維陣列

```javascript
// 等同於：
// [["2026-03-25", [s1, s2]], ["2026-03-26", [s3]], ...]
```

#### `.forEach(([date, daySessions]) => { ... })`

`([date, daySessions])` 是 ES6 **解構賦值（Destructuring Assignment）** 應用於函式參數：

```javascript
// 原始形式（不解構）
.forEach((entry) => {
  const date = entry[0]
  const daySessions = entry[1]
})

// 解構後（等同）
.forEach(([date, daySessions]) => { ... })
```

#### 物件字面量與 `.filter().length` 統計

```javascript
stats[date] = {
  total: daySessions.length,
  pass: daySessions.filter(s => s.final_result === 'PASS').length,
  ...
}
```

- `daySessions.length` — 陣列元素總數
- `.filter(s => s.final_result === 'PASS')` — 回傳符合條件的**新陣列**（不修改原陣列）
- `.length` — 立即取得篩選結果的數量，不需另存變數

**最終 `dailyStats` 結構：**

```javascript
{
  "2026-03-25": { total: 5, pass: 3, fail: 1, abort: 1 },
  "2026-03-26": { total: 2, pass: 2, fail: 0, abort: 0 }
}
```

---

### 第 41–61 行：fetchSessions 非同步函式

```javascript
const fetchSessions = async (params) => {
  loading.value = true
  error.value = null
  try {
    const data = await queryTestSessions(params)
    sessions.value = Array.isArray(data) ? data : []

    // User feedback for empty results (non-blocking)
    if (sessions.value.length === 0) {
      error.value = 'No sessions found for the selected criteria'
    }
  } catch (err) {
    // Extract meaningful error message from response
    const errorMsg = err.response?.data?.detail || err.message || 'Failed to load sessions'
    error.value = errorMsg
    sessions.value = []
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}
```

#### `async` / `await` 語法

```javascript
const fetchSessions = async (params) => { ... }
```

- `async` 關鍵字讓函式回傳 `Promise`，並允許函式內部使用 `await`
- `await queryTestSessions(params)` — 暫停執行，等待 Promise 解析（resolve），避免 `.then().catch()` callback 地獄

#### `try / catch / finally` 例外處理

| 區塊 | 執行時機 | 用途 |
|------|---------|------|
| `try` | 一般執行路徑 | 呼叫 API、更新狀態 |
| `catch(err)` | 發生例外時 | 擷取錯誤訊息、清空 sessions、顯示 Toast |
| `finally` | **無論成功或失敗都執行** | 確保 `loading.value = false` 一定被執行 |

`finally` 是關鍵設計：即使 API 成功或失敗，loading 狀態都必須被重置，否則 UI 會永遠顯示 spinner。

#### 防禦性資料驗證

```javascript
sessions.value = Array.isArray(data) ? data : []
```

**三元運算子（Ternary Operator）**：`condition ? valueIfTrue : valueIfFalse`

- `Array.isArray(data)` — 確認後端回傳的是陣列（防止後端回傳非預期格式如 `null`、物件、字串時破壞 `.forEach()` 等陣列方法）
- 若非陣列，回退（fallback）為空陣列

#### 可選鏈（Optional Chaining）與邏輯或運算子

```javascript
const errorMsg = err.response?.data?.detail || err.message || 'Failed to load sessions'
```

| 語法 | 說明 |
|------|------|
| `err.response?.data?.detail` | **可選鏈（`?.`）**：若 `err.response` 或 `err.response.data` 為 `null`/`undefined`，不拋出 TypeError，直接回傳 `undefined` |
| `\|\|` | **邏輯或（Short-circuit evaluation）**：取第一個 truthy 值 |

**錯誤訊息優先級：**
1. FastAPI 的 `HTTPException.detail`（最具體）
2. JavaScript Error 的 `.message`（次選）
3. 固定字串 fallback（最後保底）

#### `ElMessage.error(errorMsg)`

呼叫 Element Plus 的全域 Toast 通知 API，顯示紅色錯誤訊息。這是**阻斷式（blocking）使用者通知**，相對於 `error.value` 的非阻斷式（讓模板決定是否顯示）。

---

### 第 63–70 行：回傳公開介面

```javascript
return {
  sessions,
  sessionsByDate,
  dailyStats,
  loading,
  error,
  fetchSessions
}
```

**Composable 的公開介面（Public API）**，呼叫方透過物件解構使用：

```javascript
// TestResults.vue 中
const { sessions, loading, error, fetchSessions, dailyStats } = useTestHistory()
```

| 回傳成員 | 型別 | 讀寫 | 說明 |
|---------|------|------|------|
| `sessions` | `Ref<Array>` | 讀（可寫但不建議） | 原始 session 陣列 |
| `sessionsByDate` | `ComputedRef<Object>` | 唯讀 | 依日期分組後的結果 |
| `dailyStats` | `ComputedRef<Object>` | 唯讀 | 每日統計摘要 |
| `loading` | `Ref<Boolean>` | 讀 | API 請求進行中標記 |
| `error` | `Ref<String\|null>` | 讀 | 錯誤訊息 |
| `fetchSessions` | `Function` | — | 觸發 API 呼叫的函式 |

> **注意：** `sessionsByDate` 和 `dailyStats` 為 `computed`，是唯讀的衍生值，不應從外部直接賦值。

---

## 資料流示意圖

```
呼叫 fetchSessions(params)
        │
        ▼
  loading = true
  error = null
        │
        ▼
  queryTestSessions(params)    ← GET /api/results/sessions
  (Axios 呼叫後端 API)
        │
   ┌────┴────┐
   │ 成功    │ 失敗
   ▼         ▼
sessions   error = errorMsg
= data[]   sessions = []
           ElMessage.error()
   │
   ▼
 sessions 更新
   │
   ├──► sessionsByDate (computed 自動重算)
   │         │
   └──► dailyStats (computed 自動重算)
              │
              ▼
  loading = false (finally)
```

---

## 與其他模組的關係

| 模組 | 關係 |
|------|------|
| `frontend/src/api/testResults.js` | 提供 `queryTestSessions` — 呼叫 `GET /api/results/sessions` |
| `frontend/src/utils/dateHelpers.js` | 提供 `formatDateKey` — 轉換日期格式 |
| `frontend/src/composables/useTestTimeline.js` | 平行 composable，負責 ECharts 圖表，消費 `sessionsByDate`/`dailyStats` 資料 |
| `frontend/src/views/TestResults.vue` | 主要消費者，在「測試歷史」Tab 中呼叫此 composable |
| `element-plus` | 提供 `ElMessage` 全域 Toast 通知 |

---

## 設計模式說明

### 關注點分離（Separation of Concerns）

```
useTestHistory.js
├── 資料抓取層：fetchSessions (副作用)
├── 資料轉換層：sessionsByDate (純計算)
└── 統計計算層：dailyStats (純計算)
```

- **副作用（side effects）**集中在 `fetchSessions`
- **純計算（pure computation）**使用 `computed`，可測試、可快取、無副作用

### 響應式資料管道（Reactive Data Pipeline）

Vue 3 的 `computed` 形成天然的**響應式資料管道**，類似 RxJS Observable chain，但語法更簡潔。更新 `sessions` 後，所有衍生值自動傳播更新，UI 無需手動刷新。
