# ProjectStationSelector.vue 程式碼說明文件

**檔案路徑：** `frontend/src/components/ProjectStationSelector.vue`
**類型：** 共用 UI 組件（Shared Component）
**最後更新：** 2026-03-27

---

## 1. 組件概述

`ProjectStationSelector` 是一個**專案與站別聯動選擇器**，提供兩個下拉選單：

1. **專案（Project）** 選擇 — 從後端載入所有可用專案
2. **站別（Station）** 選擇 — 根據已選專案動態載入對應站別

此組件負責觸發資料載入與狀態更新，但不自行儲存最終選擇的業務邏輯狀態，而是透過 **Pinia Store** 集中管理，並透過 `emit` 事件通知父組件。

---

## 2. 模板結構（Template）

```html
<template>
  <div class="selector-container">
    <el-form label-width="100px">

      <!-- 專案選單 -->
      <el-form-item label="專案">
        <el-select
          v-model="selectedProjectId"
          placeholder="請選擇專案"
          :loading="loadingProjects"
          @change="handleProjectChange"
          style="width: 100%"
        >
          <el-option v-for="project in projects" :key="project.id"
            :label="project.project_name" :value="project.id">
            <span>{{ project.project_code }} - {{ project.project_name }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 站別選單（依賴專案選擇） -->
      <el-form-item label="站別">
        <el-select
          v-model="selectedStationId"
          placeholder="請選擇站別"
          :disabled="!selectedProjectId || stations.length === 0"
          :loading="loadingStations"
          @change="handleStationChange"
          style="width: 100%"
        >
          <el-option v-for="station in stations" :key="station.id"
            :label="station.station_name" :value="station.id">
            <span>{{ station.station_code }} - {{ station.station_name }}</span>
          </el-option>
        </el-select>
      </el-form-item>

    </el-form>
  </div>
</template>
```

### 2.1 Element Plus 組件說明

| 組件 | 用途 |
|------|------|
| `<el-form>` | 表單容器，`label-width="100px"` 統一標籤寬度 |
| `<el-form-item>` | 表單項目，`label` 屬性顯示欄位名稱 |
| `<el-select>` | 下拉選單，`v-model` 雙向綁定選中值 |
| `<el-option>` | 選單項目，`:key` 用於 Vue diff、`:value` 為提交值、`label` 為顯示文字（此處由 slot 覆蓋） |

### 2.2 站別選單的禁用條件（`:disabled`）

```html
:disabled="!selectedProjectId || stations.length === 0"
```

**邏輯說明：**
- `!selectedProjectId` — 尚未選擇任何專案時禁用
- `stations.length === 0` — 選了專案但該專案下無任何站別時也禁用
- 兩條件以 `||` 連接，任一成立即禁用，避免使用者在無效狀態下操作

### 2.3 自訂選項顯示（Default Slot Override）

```html
<el-option :label="project.project_name" :value="project.id">
  <span>{{ project.project_code }} - {{ project.project_name }}</span>
</el-option>
```

`<el-option>` 有兩種顯示文字：
- **`label` 屬性**：選中後顯示在選單框內的文字（`project_name`）
- **Default Slot 內容**：下拉清單展開時每個選項的顯示格式（`code - name`）

此設計讓選中後的選單框保持簡潔（只顯示名稱），但展開時提供更多識別資訊（代碼 + 名稱）。

---

## 3. 腳本邏輯（Script Setup）

### 3.1 Imports 與依賴

```javascript
import { ref, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'
```

| 引入項目 | 來源 | 用途 |
|---------|------|------|
| `ref` | Vue 3 Composition API | 建立本地響應式狀態 |
| `onMounted` | Vue 3 Composition API | 組件掛載後執行初始化 |
| `useProjectStore` | Pinia Store | 存取共享的專案狀態與 API 方法 |
| `ElMessage` | Element Plus | 顯示錯誤/警告提示訊息 |

### 3.2 事件宣告（defineEmits）

```javascript
const emit = defineEmits(['project-selected', 'station-selected'])
```

| 事件名稱 | 觸發時機 | 攜帶資料 |
|---------|---------|---------|
| `project-selected` | 使用者主動選擇新專案時 | `project` 物件（含 id, project_code, project_name 等） |
| `station-selected` | 使用者主動選擇站別，**或**頁面載入時從 localStorage 恢復已儲存的站別時 | `station` 物件（含 id, station_code, station_name 等） |

`station-selected` 在 `onMounted` 中也會被發出，這是刻意的設計（見 3.3 節說明）。

### 3.3 本地響應式狀態

```javascript
const projects = ref([])              // 所有專案清單
const stations = ref([])              // 當前專案下的站別清單
const selectedProjectId = ref(null)   // 目前選中的專案 ID
const selectedStationId = ref(null)   // 目前選中的站別 ID
const loadingProjects = ref(false)    // 專案選單 loading 狀態
const loadingStations = ref(false)    // 站別選單 loading 狀態
```

前四個 `ref` 僅作為模板綁定用的**本地 UI 狀態**，持久化狀態由 `projectStore` 管理。
`loadingProjects` / `loadingStations` 控制 `el-select` 的 `:loading` prop，在 API 請求期間顯示旋轉指示器。

### 3.4 生命週期鉤子（onMounted）

```javascript
onMounted(async () => {
  loadingProjects.value = true
  try {
    projects.value = await projectStore.fetchProjects()

    // 恢復已儲存的專案選擇
    if (projectStore.currentProject) {
      selectedProjectId.value = projectStore.currentProject.id
      await loadStations(selectedProjectId.value)

      // 恢復已儲存的站別選擇，並主動發出 station-selected 事件
      if (projectStore.currentStation) {
        selectedStationId.value = projectStore.currentStation.id
        emit('station-selected', projectStore.currentStation)
      }
    }
  } catch (error) {
    const status = error.response?.status
    if (status === 401 || status === 403) {
      ElMessage.error('無權限載入專案列表')
    } else if (status >= 500) {
      ElMessage.error('伺服器錯誤，請稍後再試')
    } else if (!error.response) {
      ElMessage.error('網路連線失敗，無法載入專案列表')
    } else {
      ElMessage.error('載入專案列表失敗')
    }
  } finally {
    loadingProjects.value = false
  }
})
```

**執行流程：**

```
組件掛載
  ↓
loadingProjects = true
  ↓
fetchProjects() — 從後端取得所有專案清單
  ↓
检查 projectStore.currentProject（來自 localStorage）
  ├─ 有 → 恢復選中狀態 + loadStations()
  │         ├─ 检查 currentStation
  │         └─ 有 → 恢復選中 + emit('station-selected', ...)  ← 關鍵修正
  └─ 無 → 保持空白選單
  ↓
finally: loadingProjects = false
```

**為何在 onMounted 主動 emit `station-selected`？**

父組件（如 `Login.vue`）使用 `stationSelected` 布林值來控制「進入系統」按鈕是否可點擊。若不在恢復時重新 emit，父組件的 `stationSelected` 會維持 `false`，導致按鈕永遠是 disabled 狀態，儘管 store 中已有選中的站別。

### 3.5 loadStations 方法

```javascript
const loadStations = async (projectId) => {
  loadingStations.value = true
  try {
    stations.value = await projectStore.fetchProjectStations(projectId)
  } catch (error) {
    const status = error.response?.status
    if (status === 404) {
      ElMessage.warning('該專案尚無站別資料')
    } else if (status >= 500) {
      ElMessage.error('伺服器錯誤，無法載入站別列表')
    } else if (!error.response) {
      ElMessage.error('網路連線失敗，無法載入站別列表')
    } else {
      ElMessage.error('載入站別列表失敗')
    }
    stations.value = []  // 失敗時清空，避免顯示過時資料
  } finally {
    loadingStations.value = false
  }
}
```

**設計要點：**
- 接受 `projectId` 參數，與具體的 UI 元素解耦
- 404 使用 `ElMessage.warning`（橙黃色）而非 `error`（紅色）— 專案尚無站別是正常業務狀態，不是程式錯誤
- 錯誤時將 `stations` 重設為空陣列，確保站別選單同步進入禁用狀態（搭配模板中的 `:disabled` 條件）
- `finally` 保證不論成功或失敗，`loadingStations` 都會被清除，避免 UI 卡在 loading 狀態

### 3.6 handleProjectChange 方法

```javascript
const handleProjectChange = async (projectId) => {
  selectedStationId.value = null    // 清除舊站別選擇
  if (projectId) {
    await loadStations(projectId)
    const project = projects.value.find(p => p.id === projectId)
    projectStore.setCurrentProject(project)  // 持久化到 store / localStorage
    emit('project-selected', project)        // 通知父組件
  }
}
```

**執行順序說明：**
1. **先清空站別選擇** — 防止切換專案後舊站別 ID 仍顯示（但該 ID 不屬於新專案）
2. **載入新專案的站別** — 觸發非同步 API 請求
3. **更新 store** — 將選擇持久化（寫入 localStorage）
4. **emit 事件** — 通知父組件，由父組件決定後續行為

### 3.7 handleStationChange 方法

```javascript
const handleStationChange = (stationId) => {
  if (stationId) {
    const station = stations.value.find(s => s.id === stationId)
    if (!station) return   // 防衛性返回，避免 emit undefined
    projectStore.setCurrentStation(station)  // 持久化到 store / localStorage
    emit('station-selected', station)        // 通知父組件
  }
}
```

**與 handleProjectChange 的差異：**
- `handleStationChange` 是同步函式（無 `async`），因為不需要等待 API 請求
- 加入了防衛性檢查（`if (!station)`），避免在邊緣情況下 emit `undefined` 造成父組件錯誤

---

## 4. 樣式（Style Scoped）

```css
<style scoped>
.selector-container {
  padding: 10px 0;
}
</style>
```

- `scoped` 屬性確保樣式只作用於此組件的 DOM，不會污染全局
- 僅設定上下 padding，其餘排版由 Element Plus 的 `el-form` 自動處理

---

## 5. 資料流架構圖

```
後端 API
  ↑↓
projectStore (Pinia)
  ├── fetchProjects()          ← 取得所有專案
  ├── fetchProjectStations()   ← 取得特定專案的站別
  ├── setCurrentProject()      ← 持久化選中專案（寫 localStorage）
  ├── setCurrentStation()      ← 持久化選中站別（寫 localStorage）
  ├── currentProject           ← 讀取已儲存的專案
  └── currentStation           ← 讀取已儲存的站別
        ↑↓
ProjectStationSelector.vue（本組件）
  ├── 本地 UI 狀態（ref）      ← 驅動模板渲染
  └── emit events              ← 向上通知父組件
        ↓
父組件（如 Login.vue）
  └── 監聽事件，控制「進入系統」按鈕狀態
```

---

## 6. 組件使用方式

```html
<!-- 在父組件中使用 -->
<ProjectStationSelector
  @project-selected="onProjectSelected"
  @station-selected="onStationSelected"
/>

<script setup>
import ProjectStationSelector from '@/components/ProjectStationSelector.vue'

const stationSelected = ref(false)

const onProjectSelected = (project) => {
  console.log('選擇了專案:', project.project_name)
  stationSelected.value = false  // 切換專案時重置站別狀態
}

const onStationSelected = (station) => {
  console.log('選擇了站別:', station.station_name)
  stationSelected.value = true   // 啟用「進入系統」按鈕
}
</script>
```

---

## 7. 關鍵設計決策

### 7.1 為何使用 Pinia Store 而非 Props？

此組件被用於多個進入點（Login 頁、TestMain 頁等），選擇的專案/站別需要在整個應用程式生命週期中持久保存。若使用 Props 傳遞，每個父組件都需要自行管理狀態，造成重複邏輯。Pinia Store + localStorage 提供了單一來源的真相（Single Source of Truth）。

### 7.2 為何在 onMounted 重播 station-selected 事件？

這是一個**恢復使用者上次工作狀態**的 UX 設計。當使用者重新載入頁面後，store 已從 localStorage 恢復狀態，但父組件的 UI 狀態（如按鈕啟用/禁用）需要被重新觸發，否則即使 store 有資料，父組件也不知道要啟用「進入系統」按鈕。

### 7.3 聯動選單的清空策略

選擇新專案時立即清空 `selectedStationId`（設為 `null`），是防止 UI 顯示「已選站別」但該站別不屬於新專案的不一致狀態。這個清空操作在 API 請求完成前就執行，確保 UX 的即時反饋。

### 7.4 錯誤訊息分類策略

錯誤處理依 `error.response?.status` 分類：

| HTTP 狀態碼 | 情境 | 訊息類型 | 訊息內容 |
|------------|------|---------|---------|
| 401 / 403 | 權限不足 | `error` | 無權限載入...列表 |
| 404（站別） | 專案尚無站別 | `warning` | 該專案尚無站別資料 |
| 5xx | 伺服器問題 | `error` | 伺服器錯誤，請稍後再試 |
| 無 `response` | 網路中斷 | `error` | 網路連線失敗，無法載入... |
| 其他 | 未預期狀況 | `error` | 載入...失敗（fallback） |

> **注意：** `error.response` 只在 HTTP 請求送達但伺服器回傳錯誤時存在；網路中斷時 `error.response` 為 `undefined`，需以 `!error.response` 判斷。

---

## 8. 修改歷程

### 2026-03-27 — 修正已知問題

依文件原「已知問題與改進建議」章節，完成以下修正：

| 問題 | 修正方式 |
|------|---------|
| `watch` 未使用 | 從 `import { ref, onMounted, watch }` 移除 `watch` |
| `console.log` 殘留 | 移除 `handleStationChange` 中所有 `console.log` / `console.error` 輸出 |
| 無 loading 狀態 | 新增 `loadingProjects` / `loadingStations` ref，綁定至兩個 `el-select` 的 `:loading` prop；使用 `try/finally` 確保 loading 旗標被清除 |
| 錯誤處理不分類 | 依 HTTP 狀態碼分類顯示不同訊息（見 7.4 節），站別 404 改用 `ElMessage.warning` |
