# AppNavBar.vue — 元件語法詳解

> 檔案路徑：`frontend/src/components/AppNavBar.vue`
> 元件用途：應用程式全域導覽列，提供各頁面的快速切換與使用者登出功能

---

## 目錄

1. [模板區 (Template)](#1-模板區-template)
2. [腳本區 (Script Setup)](#2-腳本區-script-setup)
3. [樣式區 (Scoped Style)](#3-樣式區-scoped-style)
4. [資料流與生命週期](#4-資料流與生命週期)
5. [使用的 Vue / Element Plus API 一覽](#5-使用的-vue--element-plus-api-一覽)

---

## 1. 模板區 (Template)

```html
<template>
  <el-card class="nav-card" shadow="never">
    <el-row :gutter="10" align="middle" justify="space-between">
      <el-col :span="18">
        <div class="nav-buttons">
          <!-- 7 個導覽按鈕 -->
        </div>
      </el-col>
      <el-col :span="6" style="text-align: right">
        <!-- 使用者資訊 + 登出按鈕 -->
      </el-col>
    </el-row>
  </el-card>
</template>
```

### 1.1 `<el-card>` — Element Plus 卡片容器

```html
<el-card class="nav-card" shadow="never">
```

| 屬性 | 值 | 說明 |
|------|-----|------|
| `class` | `"nav-card"` | 自定義 CSS class，用於外部樣式控制 |
| `shadow` | `"never"` | 取消卡片陰影，使其看起來像一個扁平的導覽列 |

`shadow` 可選值：`"always"` / `"hover"` / `"never"`。此處選 `never` 是因為導覽列通常不需要立體陰影效果。

### 1.2 `<el-row>` / `<el-col>` — Element Plus 柵格佈局系統

```html
<el-row :gutter="10" align="middle" justify="space-between">
  <el-col :span="18">...</el-col>
  <el-col :span="6">...</el-col>
</el-row>
```

**`<el-row>` 屬性：**

| 屬性 | 值 | 說明 |
|------|-----|------|
| `:gutter` | `10` | 欄間距（px）。使用 `v-bind`（`:`）因為是數值型別，若寫成字串 `"10"` 也能運作但語義上不精確 |
| `align` | `"middle"` | 垂直對齊方式，值對應 CSS `align-items: middle` |
| `justify` | `"space-between"` | 水平排列方式，對應 CSS `justify-content: space-between`，將兩個 `<el-col>` 推向兩端 |

**`<el-col>` 的 `:span` 屬性：**

| 欄位 | 值 | 佔比 |
|------|-----|------|
| 左欄（導覽按鈕） | `18` | 18/24 = 75% |
| 右欄（使用者資訊） | `6` | 6/24 = 25% |

Element Plus 柵格系統基於 24 欄制，`:span` 的值即為佔用的欄數。`18 + 6 = 24` 剛好填滿一整行。

### 1.3 導覽按鈕 — 重複模式

每個導覽按鈕遵循相同的模式：

```html
<el-button
  :type="buttonType('main')"
  size="default"
  :disabled="isCurrent('main')"
  @click="navigateTo('/main')"
>
  測試主畫面
</el-button>
```

**逐屬性解析：**

| 屬性/事件 | 值 | 說明 |
|-----------|-----|------|
| `:type` | `buttonType('main')` | 動態綁定按鈕型態，當前頁面為 `"primary"`（實心藍色），否則 `"default"`（白色描邊）。使用 `v-bind`（`:`）因為是 JS 表達式 |
| `size` | `"default"` | 字串值，可直接寫不用 `v-bind`。可選值：`"large"` / `"default"` / `"small"` |
| `:disabled` | `isCurrent('main')` | 當前頁面的按鈕設為禁用，防止重複導覽。使用 `v-bind` 因為是 JS 函數呼叫 |
| `@click` | `navigateTo('/main')` | 事件綁定語法糖，等同 `v-on:click="navigateTo('/main')"` |

**所有按鈕一覽：**

| label | page key | route path |
|-------|----------|------------|
| 測試主畫面 | `main` | `/main` |
| 測試計劃管理 | `testplan` | `/testplan` |
| 測試結果查詢 | `results` | `/results` |
| 專案管理 | `projects` | `/projects` |
| 使用者管理 | `users` | `/users` |
| 儀器管理 | `instruments` | `/instruments` |
| Modbus 設定 | `modbus-config` | `/modbus-config` |

### 1.4 使用者資訊與登出

```html
<el-text type="info">{{ authStore.user?.username || '-' }}</el-text>
<el-button type="danger" size="small" @click="handleLogout" style="margin-left: 10px">
  登出
</el-button>
```

| 語法 | 說明 |
|------|------|
| `{{ authStore.user?.username \|\| '-' }}` | Vue 模板插值語法。`?.` 是 optional chaining，避免 `authStore.user` 為 `null`/`undefined` 時報錯。`\|\|` 是 nullish coalescing，fallback 為 `'-'` |
| `<el-text type="info">` | Element Plus 文字元件，`type="info"` 呈現灰色文字 |
| `style="margin-left: 10px"` | 內聯樣式，直接設定 CSS。這裡用內聯而非 class 是因為只需要一處的簡單樣式 |
| `type="danger"` | Element Plus 按鈕的危險色（紅色），適合用於登出等破壞性操作 |

---

## 2. 腳本區 (Script Setup)

```html
<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({...})
const router = useRouter()
const authStore = useAuthStore()

const isCurrent = (page) => ...
const buttonType = (page) => ...
const navigateTo = (path) => ...
const handleLogout = async () => ...
</script>
```

### 2.1 `<script setup>` 語法

`<script setup>` 是 Vue 3.2+ 引入的 **編譯期語法糖**，等價於：

```js
export default {
  setup() {
    // 所有頂層宣告都會自動暴露給模板
    return { /* 所有變數、函數、import */ }
  }
}
```

特點：
- 所有頂層變數、函數、import 自動暴露給 `<template>`，無需手動 `return`
- 更少的樣板程式碼（boilerplate）
- 更好的 TypeScript 支援（雖然此檔案未使用 TS）
- 編譯後效能與普通 `<script>` + `setup()` 相同

### 2.2 Imports

```js
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
```

| Import | 來源 | 說明 |
|--------|------|------|
| `useRouter` | `vue-router` | Vue Router 的 composable，提供 `router.push()`、`router.replace()` 等導覽方法 |
| `useAuthStore` | `@/stores/auth` | Pinia store composable。`@/` 是 Vite/Webpack 別名，對應 `src/` 目錄 |

### 2.3 `defineProps()` — 元件屬性宣告

```js
const props = defineProps({
  currentPage: {
    type: String,
    required: true
  }
})
```

**語法解析：**

| 部分 | 說明 |
|------|------|
| `defineProps({...})` | Vue 3 編譯期巨集（macro），無需 import，編譯時會被轉換。在 `<script setup>` 中宣告父元件傳入的 props |
| `const props =` | 將 props 物件存入變數，使得在 JS 中可以透過 `props.currentPage` 存取。在模板中則可直接用 `currentPage` |
| `type: String` | Prop 型別驗證，Vue 會在開發模式下發出警告如果傳入非字串值 |
| `required: true` | 標記為必填 prop。若父元件未傳入，Vue 會在 console 發出警告 |

**`defineProps` 的編譯期特性：**

`defineProps` 不是一個普通函數，而是一個 **編譯器巨集**（compiler macro）。它不需要從 Vue 匯入，在編譯時會被靜態分析並轉換為標準的 options API `props` 宣告。這就是為什麼你可以在 `<script setup>` 中直接使用它而沒有 `import` 語句。

### 2.4 `useRouter()` — Router 實例

```js
const router = useRouter()
```

| 方法 | 說明 |
|------|------|
| `router.push(path)` | 導覽到指定路徑，會在 history 中新增一筆記錄（使用者可以用瀏覽器返回） |
| `router.replace(path)` | 導覽但**不新增** history 記錄 |
| `router.back()` | 等同於瀏覽器的「上一頁」 |

在 Vue 3 + Vue Router 4 中，`useRouter()` 必須在 `setup()` 函數或 `<script setup>` 的頂層呼叫（即不能在條件語句或迴圈中呼叫），因為它依賴元件的 injection context。

### 2.5 `useAuthStore()` — Pinia Store

```js
const authStore = useAuthStore()
```

Pinia store composable 回傳一個 **reactive 物件**，這意味著：
- `authStore.user` 是響應式的，當 store 中的 `user` 變更時，模板會自動更新
- `authStore.logout()` 是一個 action（可能是 async）
- 無需 `.value`（不像 `ref()`），因為 store 本身就是一個 reactive 物件

### 2.6 輔助函數

```js
const isCurrent = (page) => props.currentPage === page
const buttonType = (page) => (isCurrent(page) ? 'primary' : 'default')
```

| 函數 | 參數 | 回傳值 | 說明 |
|------|------|--------|------|
| `isCurrent` | `page` (String) | `Boolean` | 判斷傳入的頁面 key 是否為當前頁面 |
| `buttonType` | `page` (String) | `String` | 當前頁面回傳 `'primary'`，其餘回傳 `'default'` |

這兩個函數使用 **箭頭函數**（arrow function）語法，並透過 `props.currentPage` 存取 prop 值。在模板中呼叫時可以省略括號內的引數嗎？不行，因為它們需要參數，所以模板中必須寫 `isCurrent('main')` 而非 `isCurrent`。

`buttonType` 內部呼叫了 `isCurrent`，形成了一個簡單的函數組合模式。這避免了在模板中寫冗長的三元運算子。

### 2.7 `navigateTo()` — 頁面導覽

```js
const navigateTo = (path) => {
  router.push(path)
}
```

封裝 `router.push()` 為獨立函數，好處：
1. 模板中只需寫 `@click="navigateTo('/main')"` 而非 `@click="() => router.push('/main')"`
2. 未來如需加入導覽前的邏輯（如確認對話框），只需修改此處

### 2.8 `handleLogout()` — 非同步登出處理

```js
const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    router.push('/login')
  }
}
```

**語法逐行解析：**

| 行 | 語法 | 說明 |
|----|------|------|
| `async () => {` | async arrow function | 標記此函數為非同步，內部可以使用 `await` |
| `await authStore.logout()` | await | 等待 Pinia action 完成（可能是 API 呼叫清除 server-side session） |
| `router.push('/login')` | — | 登出成功後導向登入頁 |
| `catch (error)` | try/catch | 捕捉 `logout()` 拋出的任何錯誤 |
| `console.error(...)` | — | 開發環境的錯誤日誌輸出 |
| `router.push('/login')` | — | 即使登出失敗仍導向登入頁（fail-safe 設計） |

**設計亮點：** 無論登出成功或失敗都會導向登入頁，這是一種 fail-safe 模式 — 使用者看到登入頁代表已登出（或至少無法繼續操作），避免卡在中間狀態。

---

## 3. 樣式區 (Scoped Style)

```html
<style scoped>
.nav-card {
  margin-bottom: 20px;
}

.nav-buttons {
  display: flex;
  gap: 8px;
}

.nav-buttons .el-button {
  margin: 0;
}
</style>
```

### 3.1 `scoped` 屬性

`<style scoped>` 讓 CSS 只作用於**當前元件**的元素。Vue 在編譯時會：
1. 為元件的每個 DOM 元素加上一個唯一屬性（如 `data-v-f3f3eg9`）
2. 將 CSS 選擇器改寫為 `.nav-card[data-v-f3f3eg9]`

這避免了全域樣式汙染 — 即使其他元件也有 `.nav-card` class，也不會互相影響。

### 3.2 樣式規則解析

| 規則 | 說明 |
|------|------|
| `.nav-card { margin-bottom: 20px; }` | 導覽列底部留 20px 間距，與下方內容區分 |
| `.nav-buttons { display: flex; gap: 8px; }` | 使用 Flexbox 水平排列按鈕，`gap: 8px` 設定按鈕間的統一間距。這比傳統的 `margin-left` 方案更簡潔，且不會有第一個按鈕多餘邊距的問題 |
| `.nav-buttons .el-button { margin: 0; }` | **覆蓋 Element Plus 預設樣式。** Element Plus 的 `<el-button>` 預設有 `margin-left: 12px`（用於按鈕群組間距），使用 Flex `gap` 後需將其清除以避免雙重間距。`scoped` 不影響子元件的根元素，但此處 `.nav-buttons .el-button` 的層級足夠深，能穿透到 Element Plus 按鈕 |

> **注意：** Vue 的 scoped style 對**子元件的根元素**有效，但對子元件**內部元素**無效。然而 `.nav-buttons .el-button` 能生效，是因為它匹配的是子元件（`<el-button>`）的根元素（本身就是 button），而非其內部 span。

---

## 4. 資料流與生命週期

### 4.1 Props 資料流

```
父元件（如 TestMain.vue）
    │
    │  <AppNavBar currentPage="main" />
    │
    ▼
AppNavBar.vue
    │
    ├── props.currentPage = "main"
    │       │
    │       ├── isCurrent('main') → true
    │       └── buttonType('main') → 'primary'
    │
    └── 模板渲染：對應按鈕高亮 + disabled
```

### 4.2 事件流

```
使用者點擊按鈕
    │
    ▼
@click="navigateTo('/testplan')"
    │
    ▼
router.push('/testplan')
    │
    ▼
Vue Router 匹配路由 → 切換元件
    │
    ▼
新元件的 <AppNavBar currentPage="testplan" />
    │
    ▼
AppNavBar 重新渲染，testplan 按鈕高亮
```

### 4.3 元件生命週期

此元件沒有使用任何生命週期鉤子（`onMounted`、`onUnmounted` 等），這是合理的因為：
- 它是一個純展示型元件（presentational component）
- 所有邏輯都由 props 和事件驅動
- 沒有需要清理的副作用（side effects）

---

## 5. 使用的 Vue / Element Plus API 一覽

### Vue 3 核心

| API | 類型 | 用途 |
|-----|------|------|
| `<script setup>` | 編譯期巨集 | Composition API 語法糖 |
| `defineProps()` | 編譯期巨集 | 宣告元件屬性 |
| `{{ }}` | 模板語法 | 插值渲染 |
| `:` (v-bind) | 指令 | 動態屬性綁定 |
| `@` (v-on) | 指令 | 事件監聽 |
| `?.` (optional chaining) | JS 運算子 | 安全存取巢狀屬性 |
| `\|\|` (nullish coalescing) | JS 運算子 | 預設值 fallback |
| `async/await` | JS 語法 | 非同步流程控制 |
| `try/catch` | JS 語法 | 錯誤處理 |
| `<style scoped>` | SFC 功能 | 限定 CSS 作用域 |

### Vue Router

| API | 類型 | 用途 |
|-----|------|------|
| `useRouter()` | Composable | 取得 router 實例 |
| `router.push(path)` | 方法 | 程式化導覽 |

### Pinia

| API | 類型 | 用途 |
|-----|------|------|
| `useAuthStore()` | Composable | 取得 auth store 實例 |
| `authStore.user` | State | 讀取當前使用者 |
| `authStore.logout()` | Action | 執行登出 |

### Element Plus

| 元件 | 屬性/事件 | 值 | 說明 |
|------|-----------|-----|------|
| `<el-card>` | `shadow` | `"never"` | 無陰影卡片 |
| `<el-row>` | `:gutter` | `10` | 欄間距 |
| `<el-row>` | `align` | `"middle"` | 垂直置中 |
| `<el-row>` | `justify` | `"space-between"` | 兩端對齊 |
| `<el-col>` | `:span` | `18` / `6` | 柵格佔比 |
| `<el-button>` | `:type` | `"primary"` / `"default"` / `"danger"` | 按鈕樣式 |
| `<el-button>` | `size` | `"default"` / `"small"` | 按鈕尺寸 |
| `<el-button>` | `:disabled` | `Boolean` | 禁用狀態 |
| `<el-button>` | `@click` | Function | 點擊事件 |
| `<el-text>` | `type` | `"info"` | 文字色彩 |
