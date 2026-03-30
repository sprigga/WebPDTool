# ModbusStatusIndicator.vue — 程式碼語法詳解

**檔案路徑：** `frontend/src/components/ModbusStatusIndicator.vue`
**元件類型：** 共用 UI 元件（Shared Component）
**用途：** 以彩色圓點顯示 Modbus 連線狀態，並支援點擊展開詳細對話框

---

## 目錄

1. [元件整體結構](#1-元件整體結構)
2. [Template 語法解析](#2-template-語法解析)
3. [Script Setup 語法解析](#3-script-setup-語法解析)
   - [3.1 Import 匯入宣告](#31-import-匯入宣告)
   - [3.2 Props 定義](#32-props-定義)
   - [3.3 響應式狀態（ref）](#33-響應式狀態ref)
   - [3.4 計算屬性（computed）](#34-計算屬性computed)
   - [3.5 工具函數](#35-工具函數)
   - [3.6 方法定義](#36-方法定義)
   - [3.7 defineExpose 公開 API](#37-defineexpose-公開-api)
   - [3.8 生命週期鉤子與 WebSocket 管理](#38-生命週期鉤子與-websocket-管理)
4. [Style 樣式解析](#4-style-樣式解析)
5. [元件資料流圖](#5-元件資料流圖)
6. [WebSocket 訊息協定](#6-websocket-訊息協定)
7. [狀態機邏輯](#7-狀態機邏輯)
8. [使用範例](#8-使用範例)

---

## 1. 元件整體結構

Vue 3 Single File Component（SFC）由三個區塊組成：

```
<template>   ← 定義 HTML 結構與綁定
<script setup>  ← 組合式 API 邏輯（Vue 3 編譯器宏）
<style scoped>  ← 限定作用域的 CSS 樣式
```

`<script setup>` 是 Vue 3.2+ 引入的語法糖，相較於 `setup()` 函數寫法更簡潔。在此區塊中宣告的變數和函數會**自動暴露**給 template 使用，不需要手動 `return`。

---

## 2. Template 語法解析

```html
<template>
  <div class="modbus-status-indicator" @click="showDetail">
```

| 語法 | 說明 |
|------|------|
| `class="modbus-status-indicator"` | 靜態 CSS class，套用 `.modbus-status-indicator` 樣式（`display: inline-block; cursor: pointer`） |
| `@click="showDetail"` | Vue 事件縮寫（等同 `v-on:click`），點擊時呼叫 `showDetail()` 函數，將 `dialogVisible` 設為 `true` |

---

### el-tooltip

```html
<el-tooltip :content="tooltipContent" placement="bottom">
  <div class="status-dot" :class="statusClass"></div>
</el-tooltip>
```

| 語法 | 說明 |
|------|------|
| `el-tooltip` | Element Plus 工具提示元件，滑鼠懸停時顯示說明文字 |
| `:content="tooltipContent"` | 動態綁定（`:` 是 `v-bind:` 的縮寫），內容來自 `computed` 屬性 `tooltipContent` |
| `placement="bottom"` | 靜態 prop，tooltip 出現在下方 |
| `:class="statusClass"` | 動態 class 綁定，依據 `statusClass` computed 值套用不同顏色樣式（`connected`、`connecting`、`disconnected`、`error`、`unknown`） |

`el-tooltip` 的**插槽機制**：內部的 `<div>` 是 tooltip 的觸發元素（trigger），tooltip 文字浮現在觸發元素旁邊。

---

### el-dialog（詳細對話框）

```html
<el-dialog v-model="dialogVisible" title="Modbus Connection Status" width="500px">
```

| 語法 | 說明 |
|------|------|
| `v-model="dialogVisible"` | 雙向綁定，`dialogVisible` 為 `true` 時顯示對話框，對話框關閉時自動設回 `false` |
| `title` | 對話框標題列文字（靜態字串） |
| `width="500px"` | 對話框寬度 |

---

### el-descriptions（說明列表）

```html
<el-descriptions v-if="status" :column="1" border>
```

| 語法 | 說明 |
|------|------|
| `v-if="status"` | 條件渲染，`status` 為 `null`（falsy）時**整個元素不渲染**（從 DOM 移除），與 `v-show` 的差異在於後者只是 `display: none` |
| `:column="1"` | 動態綁定數字 `1`（若寫 `column="1"` 則傳入字串 `"1"`，這裡用 `:` 確保傳入數值） |
| `border` | 布林 prop 的縮寫，等同 `:border="true"` |

---

### el-descriptions-item（個別欄位）

```html
<el-descriptions-item label="Status">
  <el-tag :type="status.running ? 'success' : 'info'">
    {{ status.running ? 'Running' : 'Stopped' }}
  </el-tag>
</el-descriptions-item>
```

| 語法 | 說明 |
|------|------|
| `label="Status"` | 靜態標籤文字，顯示在左側 |
| `:type="status.running ? 'success' : 'info'"` | 三元運算式動態決定 el-tag 的顏色類型（`success`=綠色，`info`=灰色，`danger`=紅色） |
| `{{ status.running ? 'Running' : 'Stopped' }}` | Mustache 插值語法（雙大括號），渲染響應式資料為文字 |

---

### 條件渲染（v-if 的 else 分支）

```html
<el-descriptions-item v-if="status.error_message" label="Error">
  <el-text type="danger">{{ status.error_message }}</el-text>
</el-descriptions-item>
```

只有在 `status.error_message` 存在（truthy）時才渲染此欄位。這利用 JavaScript 的 falsy 判斷——空字串 `""` 和 `null` 都不會觸發渲染。

```html
<el-empty v-else description="No Modbus listener active" />
```

`v-else` 必須緊接在 `v-if` 元素之後，當 `v-if` 條件為假時渲染此空狀態佔位元件。

---

## 3. Script Setup 語法解析

### 3.1 Import 匯入宣告

```js
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { modbusApi } from '@/api/modbus'
```

| 匯入 | 來源 | 說明 |
|------|------|------|
| `ref` | `vue` | 建立基本型別的響應式變數（wraps primitive in `{ value }` 物件） |
| `computed` | `vue` | 建立由其他響應式資料衍生的唯讀快取值 |
| `onMounted` | `vue` | 生命週期鉤子：元件 DOM 掛載後執行 |
| `onBeforeUnmount` | `vue` | 生命週期鉤子：元件從 DOM 移除前執行，用於清理資源 |
| `modbusApi` | `@/api/modbus` | `@` 是 Vite/webpack 設定的路徑別名，指向 `frontend/src/`；`modbusApi` 封裝了 Modbus 相關的 API 呼叫與 WebSocket 連線函數 |

---

### 3.2 Props 定義

```js
const props = defineProps({
  stationId: {
    type: Number,
    required: true
  }
})
```

`defineProps` 是 Vue 3 的**編譯器宏（Compiler Macro）**，不需要 import 即可使用。

| 欄位 | 說明 |
|------|------|
| `type: Number` | 執行期型別驗證，傳入非 Number 時會在 console 發出警告 |
| `required: true` | 若父元件未傳入此 prop，Vue 會發出警告 |
| `props.stationId` | 在 `<script setup>` 中透過 `props.stationId` 存取（template 中可直接用 `stationId`） |

Props 是**單向資料流**：父 → 子。子元件不應直接修改 props（違反 Vue 的設計原則）。

---

### 3.3 響應式狀態（ref）

```js
const status = ref(null)
const dialogVisible = ref(false)
const websocket = ref(null)
```

| 變數 | 初始值 | 用途 |
|------|--------|------|
| `status` | `null` | 儲存從 WebSocket 收到的 Modbus 狀態物件，`null` 表示尚未收到資料 |
| `dialogVisible` | `false` | 控制 `el-dialog` 的顯示/隱藏（透過 `v-model` 雙向綁定） |
| `websocket` | `null` | 儲存 WebSocket 實例，以便在 `onBeforeUnmount` 中呼叫 `.close()` |

**注意：** 在 `<script setup>` 中存取 ref 需加 `.value`（如 `status.value = data`），但在 `<template>` 中 Vue 會自動解包（unwrap），直接寫 `{{ status }}` 即可。

---

### 3.4 計算屬性（computed）

#### statusClass

```js
const statusClass = computed(() => {
  if (!status.value) return 'unknown'
  if (status.value.error_message) return 'error'
  if (status.value.running && status.value.connected) return 'connected'
  if (status.value.running) return 'connecting'
  return 'disconnected'
})
```

`computed` 的特性：
- **快取**：只有當依賴的響應式資料（`status.value`）改變時才重新計算，否則返回快取值
- **唯讀**：預設不可直接賦值（需用 `computed({ get, set })` 才能寫入）
- **自動追蹤**：Vue 的響應式系統自動追蹤函數內存取的響應式資料

優先級邏輯（由高到低）：

```
null status   →  'unknown'    （灰色，尚未連線）
error_message →  'error'      （紅色閃爍）
running+connected → 'connected'  （綠色）
running only  →  'connecting' （橘色脈衝）
其他          →  'disconnected' （深灰色）
```

#### tooltipContent

```js
const tooltipContent = computed(() => {
  if (!status.value) return 'Modbus: Unknown'
  if (status.value.error_message) return `Modbus: Error - ${status.value.error_message}`
  if (status.value.running && status.value.connected) return 'Modbus: Connected'
  if (status.value.running) return 'Modbus: Connecting...'
  return 'Modbus: Disconnected'
})
```

使用 ES6 **模板字面值（Template Literal）**（反引號語法）動態組合錯誤訊息字串，邏輯結構與 `statusClass` 完全對應，確保視覺指示器（顏色）和文字提示（tooltip）始終保持一致。

---

### 3.5 工具函數

```js
const formatUptime = (seconds) => {
  if (!seconds) return 'N/A'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  return `${hours}h ${minutes}m ${secs}s`
}
```

| 語法 | 說明 |
|------|------|
| 箭頭函數 `(seconds) => { }` | ES6 箭頭函數語法，`this` 綁定由外層決定（在此元件中無差異） |
| `Math.floor()` | 無條件捨去小數取整數 |
| `seconds % 3600` | 模除（取餘數）運算，取 3600 秒內的剩餘秒數 |
| `` `${hours}h...` `` | Template Literal 插值，組合最終顯示字串 |

`!seconds` 可同時處理 `null`、`undefined`、`0` 的情況，統一回傳 `'N/A'`。

---

### 3.6 方法定義

```js
const showDetail = () => {
  dialogVisible.value = true
}
```

簡單的箭頭函數，將 `dialogVisible` 設為 `true` 以觸發 `el-dialog` 顯示。對話框的關閉由 `v-model` 雙向綁定自動處理（點擊遮罩或關閉按鈕時 Element Plus 會設回 `false`）。

---

### 3.7 defineExpose 公開 API

```js
defineExpose({ showDetail })
```

`defineExpose` 是另一個**編譯器宏**。

**為何需要這個？** 在 `<script setup>` 中，所有變數預設是**私有的**（父元件無法透過 `ref` 存取）。若父元件需要透過模板引用（template ref）呼叫子元件的方法，必須用 `defineExpose` 明確公開。

使用範例（父元件）：
```html
<ModbusStatusIndicator ref="modbusIndicator" :station-id="1" />
```
```js
modbusIndicator.value.showDetail()  // 可呼叫，因為 showDetail 已被 expose
```

---

### 3.8 生命週期鉤子與 WebSocket 管理

#### onMounted — 建立 WebSocket 連線

```js
onMounted(() => {
  websocket.value = modbusApi.connectWebSocket(props.stationId)
```

元件 DOM 掛載完成後立即執行，呼叫 `modbusApi.connectWebSocket()` 建立 WebSocket 連線並將實例儲存至 `websocket.value`。

---

#### onopen — 連線成功後請求狀態

```js
websocket.value.onopen = () => {
  websocket.value.send(JSON.stringify({ action: 'get_status' }))
}
```

`WebSocket.onopen` 是原生 WebSocket API 的事件處理器，在連線建立後觸發。

| 語法 | 說明 |
|------|------|
| `websocket.value.onopen` | 直接對 WebSocket 實例賦值事件處理函數（非 `addEventListener`） |
| `JSON.stringify(...)` | 將 JavaScript 物件序列化為 JSON 字串後傳送 |
| `{ action: 'get_status' }` | 向後端 WebSocket handler 發送的請求格式 |

---

#### onmessage — 處理即時訊息

```js
websocket.value.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data)
    if (data.type === 'status') {
      // data.data 可能是 null（listener 未啟動）或物件（listener 已啟動）
      status.value = data.data || null
    } else if (data.type === 'connected_change' && status.value) {
      // listener 已啟動後的即時連線狀態更新
      status.value = { ...status.value, connected: data.connected }
    } else if (data.type === 'cycle_update' && status.value) {
      // 即時 cycle_count 更新
      status.value = { ...status.value, cycle_count: data.cycle_count }
    }
  } catch (e) {
    console.warn('Modbus status WS: invalid message', e)
  }
}
```

| 語法 | 說明 |
|------|------|
| `event.data` | WebSocket 訊息事件的原始文字內容（字串） |
| `JSON.parse(event.data)` | 將 JSON 字串反序列化為 JavaScript 物件 |
| `try/catch` | 防禦性程式設計，避免因非 JSON 訊息導致未處理的例外崩潰 |
| `data.data \|\| null` | 短路求值（Short-circuit evaluation）：若 `data.data` 為 `null`/`undefined`/falsy，則設為 `null` |
| `{ ...status.value, connected: data.connected }` | **物件展開語法（Spread Operator）**：建立新物件並覆寫特定欄位，觸發 Vue 響應式系統偵測到資料變更並重新渲染 |

**訊息類型：**

| `data.type` | 觸發條件 | 操作 |
|-------------|---------|------|
| `status` | 初始狀態回應 | 完整替換 `status.value` |
| `connected_change` | 連線狀態改變 | 僅更新 `connected` 欄位（保留其他欄位） |
| `cycle_update` | 新的測試循環完成 | 僅更新 `cycle_count` 欄位 |

使用展開語法（`{ ...status.value, key: newValue }`）而非直接修改 `status.value.connected = data.connected` 的原因：前者建立**新物件引用**，確保 Vue 的響應式系統能偵測到深層變更。

---

#### onerror — 錯誤處理

```js
websocket.value.onerror = () => {
  console.warn('Modbus status WebSocket error')
  status.value = null
}
```

WebSocket 發生錯誤時，將 `status.value` 重設為 `null`，觸發 UI 顯示 `unknown`（灰色）狀態。

---

#### onBeforeUnmount — 清理資源

```js
onBeforeUnmount(() => {
  if (websocket.value) {
    websocket.value.close()
  }
})
```

元件從 DOM 移除前執行。

**為何必須關閉 WebSocket？**
若不關閉，即使元件已銷毀，WebSocket 連線仍在背景保持活躍，持續接收訊息並嘗試更新已不存在的元件狀態，造成**記憶體洩漏（Memory Leak）**和不必要的網路資源消耗。

`if (websocket.value)` 防衛性檢查確保 WebSocket 已成功建立才執行關閉。

---

## 4. Style 樣式解析

```html
<style scoped>
```

`scoped` 屬性讓 CSS 只作用於此元件的元素（Vue 透過編譯期自動加入唯一的 data attribute 實現）。

### 狀態顏色定義

| Class | 顏色 | 動畫 | 語意 |
|-------|------|------|------|
| `.connected` | `#67c23a`（綠色）+ glow | 無 | 已連線且正常 |
| `.connecting` | `#e6a23c`（橘色） | `pulse`（脈衝閃爍） | 正在連線中 |
| `.disconnected` | `#909399`（灰色） | 無 | listener 已停止 |
| `.error` | `#f56c6c`（紅色） | `blink`（快速閃爍） | 發生錯誤 |
| `.unknown` | `#c0c4cc`（淡灰色） | 無 | 尚未收到資料 |

### CSS 動畫

```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
```

| 動畫 | 週期 | 透明度範圍 | 視覺效果 |
|------|------|-----------|---------|
| `pulse` | 1.5s | 1.0 → 0.5 | 柔和的呼吸感，表示「進行中」 |
| `blink` | 1.0s | 1.0 → 0.3 | 較強烈的閃爍，表示「需要注意」 |

顏色系統與 Element Plus 主題色（`--el-color-success`、`--el-color-warning`、`--el-color-danger`、`--el-color-info`）保持一致，確保視覺語言統一。

---

## 5. 元件資料流圖

```
父元件
  │
  │  :station-id="stationId"   (props 單向傳遞)
  ▼
ModbusStatusIndicator
  │
  │  onMounted: modbusApi.connectWebSocket(stationId)
  ▼
WebSocket (WS /api/modbus/ws/{stationId})
  │
  │  onmessage: { type: 'status' | 'connected_change' | 'cycle_update' }
  ▼
status.value (ref)
  │
  ├── statusClass (computed) → <div :class="statusClass">
  └── tooltipContent (computed) → <el-tooltip :content="...">
                                   dialogVisible (ref) → <el-dialog v-model="...">
```

---

## 6. WebSocket 訊息協定

### 發送（Client → Server）

```json
{ "action": "get_status" }
```

### 接收（Server → Client）

**初始狀態回應：**
```json
{
  "type": "status",
  "data": {
    "running": true,
    "connected": true,
    "last_sn": "SN123456",
    "cycle_count": 42,
    "uptime_seconds": 3600,
    "error_message": null
  }
}
```

**連線狀態變更：**
```json
{ "type": "connected_change", "connected": false }
```

**循環計數更新：**
```json
{ "type": "cycle_update", "cycle_count": 43 }
```

---

## 7. 狀態機邏輯

```
         null
          │
     websocket
      onmessage
          │
    type === 'status'
          │
   ┌──────┴──────┐
   │             │
data.data     data.data
  null          ≠ null
   │             │
unknown      ┌───┴───────┐
           error?    running?
            │    no     │
           error   connected?
                   ├──yes──→ connected
                   └──no───→ connecting
                        │
                    running=false
                        │
                   disconnected
```

---

## 8. 使用範例

### 基本使用（在父元件中）

```html
<template>
  <div>
    <!-- 放在導覽列或狀態列中 -->
    <ModbusStatusIndicator :station-id="currentStationId" />
  </div>
</template>

<script setup>
import ModbusStatusIndicator from '@/components/ModbusStatusIndicator.vue'
</script>
```

### 透過 ref 程式化觸發對話框

```html
<template>
  <ModbusStatusIndicator
    ref="modbusIndicator"
    :station-id="1"
  />
  <el-button @click="openModbusDetail">查看 Modbus 詳情</el-button>
</template>

<script setup>
import { ref } from 'vue'
import ModbusStatusIndicator from '@/components/ModbusStatusIndicator.vue'

const modbusIndicator = ref(null)

const openModbusDetail = () => {
  modbusIndicator.value?.showDetail()  // 可選鏈（Optional Chaining）防止 null 錯誤
}
</script>
```

### 在 TestMain.vue 中的實際使用位置

此元件目前整合在 `TestMain.vue` 的頂部導覽列，與 Modbus 設定按鈕相鄰，提供即時的視覺連線狀態反饋。

---

*文件生成日期：2026-03-27*
