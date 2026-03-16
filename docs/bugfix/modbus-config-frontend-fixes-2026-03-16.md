# ModbusConfig 前端三個問題修正 (2026-03-16)

## 問題一：GET /api/stations 回傳 405 Method Not Allowed

### 症狀

```
INFO: "GET /api/stations HTTP/1.1" 405 Method Not Allowed
```

`ModbusConfig.vue` 的 `loadStations()` 直接呼叫 `/api/stations`，每 5 秒重試一次。

### 根本原因

後端 `backend/app/api/stations.py` 只有：
- `POST /api/stations` → 建立站別
- `GET /api/projects/{project_id}/stations` → 列出某專案的站別

沒有 `GET /api/stations` 端點。FastAPI 對同一路徑但方法不符時回傳 **405**（非 404）。

### 除錯過程

1. 查看 `backend/app/api/stations.py` 確認路由定義
2. 發現只有 `POST /api/stations`，沒有 `GET /api/stations`
3. 參考 `TestMain.vue` 和 `ProjectManage.vue` 的站別載入方式：
   - 使用 `projectStore.fetchProjectStations(projectId)`
   - 對應 API：`GET /api/projects/{project_id}/stations`

### 修正

**`frontend/src/views/ModbusConfig.vue`**

新增 Project 下拉選單作為前置條件，改為兩段式選擇（先選專案，再選站別）：

```js
// 修改前：直接呼叫不存在的端點
const loadStations = async () => {
  const response = await apiClient.get('/api/stations')  // 405!
  stations.value = response || []
}

// 修改後：改用 projectStore，對應正確的 API
import { useProjectStore } from '@/stores/project'
const projectStore = useProjectStore()
const projects = computed(() => projectStore.projects)

const handleProjectChange = async () => {
  selectedStationId.value = null
  config.value = null
  disconnectWebSocket()
  if (!selectedProjectId.value) return
  stations.value = await projectStore.fetchProjectStations(selectedProjectId.value)
}

onMounted(() => {
  projectStore.fetchProjects()  // 載入專案清單
})
```

Template 新增 Project 選單：

```html
<el-form-item label="Project">
  <el-select v-model="selectedProjectId" @change="handleProjectChange" filterable>
    <el-option v-for="project in projects" :key="project.id"
      :label="project.project_name" :value="project.id" />
  </el-select>
</el-form-item>
```

---

## 問題二：GET /api/modbus/stations/1/config 回傳 404 卻顯示錯誤訊息

### 症狀

```
INFO: "GET /api/modbus/stations/1/config HTTP/1.1" 404 Not Found
```

選擇一個尚未建立 Modbus 設定的站別時，應顯示「No Modbus configuration」空白狀態，
但實際卻顯示錯誤訊息 `'請求的資源不存在'` 和 `'Failed to load Modbus configuration'`。

### 根本原因（兩個 bug 疊加）

**Bug A：`error?.status` 永遠是 `undefined`**

Axios 將 HTTP 錯誤包裝在 `error.response` 物件內，
所以 `error.status` 不存在，應使用 `error.response?.status`：

```js
// 修改前：永遠判斷失敗
if (error?.status === 404) { ... }

// 修改後：正確存取 Axios 錯誤結構
if (error?.response?.status === 404) { ... }
```

**Bug B：全域攔截器對所有 404 自動彈出錯誤訊息**

`frontend/src/api/client.js` 的 response interceptor：

```js
case 404:
  ElMessage.error('請求的資源不存在')  // 所有 404 都彈出！
  break
```

Modbus config 的 404 是正常業務邏輯（站別尚未設定），
不應視為錯誤彈出。

### 除錯過程

1. 確認後端路由 `/api/modbus/stations/{station_id}/config` 存在且正確
2. 確認後端在找不到設定時回傳 `HTTP_404_NOT_FOUND`（正確行為）
3. 閱讀 `client.js` interceptor，發現 case 404 全域彈出 toast
4. 閱讀 `ModbusConfig.vue` 的 catch 區塊，發現 `error?.status` 路徑錯誤
5. 確認 Axios 錯誤物件結構：`error.response.status`（非 `error.status`）

### 修正

**`frontend/src/api/client.js`** — 移除全域 404 toast（各呼叫端自行處理）：

```js
// 修改前：所有 404 都彈出錯誤
case 404:
  ElMessage.error('請求的資源不存在')
  break

// 修改後：改為註解，由各呼叫端自行決定如何處理
// case 404: callers handle "not found" themselves (e.g. no config yet)
// case 404:
//   ElMessage.error('請求的資源不存在')
//   break
```

**`frontend/src/views/ModbusConfig.vue`** — 修正 Axios 錯誤存取路徑：

```js
// 修改前：error.status 永遠 undefined
if (error?.status === 404) {

// 修改後：正確路徑
if (error?.response?.status === 404) {
```

---

## 問題三：ModbusConfig 頁面缺少導航選單

### 症狀

進入 `/modbus-config` 頁面後，頁面頂端沒有導航選單，無法切換到其他頁面。
反之，從其他頁面（如 TestMain）也沒有進入 Modbus 設定的入口。

### 根本原因

`ModbusConfig.vue` 未引入 `AppNavBar` 元件。
`TestMain.vue` 有自己的 inline 導航按鈕，但缺少 Modbus 設定的按鈕。

### 除錯過程

1. 比對所有 views，找出已使用 `AppNavBar` 的清單：
   - `TestPlanManage`, `TestResults`, `InstrumentManage`, `ReportAnalysis`, `ProjectManage`, `UserManage` ✓
   - `ModbusConfig`, `TestMain`, `TestExecution` ✗
2. 確認 `AppNavBar` 已有 Modbus 設定按鈕（route: `modbus-config`）
3. 確認 `router/index.js` 已有 `/modbus-config` 路由定義

### 修正

**`frontend/src/views/ModbusConfig.vue`** — 引入並使用 AppNavBar：

```html
<!-- template 頂部新增 -->
<AppNavBar current-page="modbus-config" />
```

```js
// script 新增 import
import AppNavBar from '@/components/AppNavBar.vue'
```

**`frontend/src/views/TestMain.vue`** — 在 inline 導航加入 Modbus 設定按鈕：

```html
<!-- 修改前 -->
<el-button size="default" @click="navigateTo('/analysis')">報表分析</el-button>
<el-button type="danger" size="default" @click="handleLogout">登出</el-button>

<!-- 修改後：在登出前插入 -->
<el-button size="default" @click="navigateTo('/analysis')">報表分析</el-button>
<el-button size="default" @click="navigateTo('/modbus-config')">Modbus 設定</el-button>
<el-button type="danger" size="default" @click="handleLogout">登出</el-button>
```

---

## 重點教訓

| 問題 | 教訓 |
|------|------|
| 405 vs 404 | FastAPI 對路徑存在但方法不符回傳 405，路徑不存在才是 404 |
| Axios 錯誤結構 | HTTP 狀態碼在 `error.response.status`，不是 `error.status` |
| 全域 interceptor | 業務邏輯上的「找不到」（404）不應視為錯誤，不宜全域彈出 |
| 新頁面導航 | 新增頁面時須同步更新：AppNavBar + 所有有 inline nav 的頁面 |

## 修改檔案清單

| 檔案 | 修改內容 |
|------|---------|
| `frontend/src/views/ModbusConfig.vue` | 新增 Project 選單、修正 API 路徑、修正 404 判斷、引入 AppNavBar |
| `frontend/src/api/client.js` | 移除全域 404 toast |
| `frontend/src/views/TestMain.vue` | 新增 Modbus 設定導航按鈕 |
