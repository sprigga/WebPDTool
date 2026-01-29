# 測試計劃篩選功能改進

## 概述
在 `TestPlanManage.vue` 中新增「專案」和「站別」選擇器,讓使用者可以篩選查看特定專案和站別的測試計劃。

## 修改內容

### 前端修改 (`frontend/src/views/TestPlanManage.vue`)

#### 1. 新增專案和站別篩選器
- **位置**: 在測試計劃表格上方新增篩選卡片
- **功能**:
  - 專案下拉選單: 顯示所有可用專案
  - 站別下拉選單: 根據選擇的專案動態載入該專案的站別列表
  - 支援清除選擇 (clearable)

#### 2. 狀態管理修改
**原有程式碼**:
```javascript
// 使用 store 的 currentProject 和 currentStation
const currentStation = computed(() => projectStore.currentStation)
```

**修改後**:
```javascript
// 使用本地狀態管理選擇的專案和站別
const selectedProjectId = ref(null)
const selectedStationId = ref(null)

const selectedProject = computed(() => {
  if (!selectedProjectId.value) return null
  return projectStore.projects.find(p => p.id === selectedProjectId.value) || null
})

const selectedStation = computed(() => {
  if (!selectedStationId.value) return null
  return filteredStations.value.find(s => s.id === selectedStationId.value) || null
})
```

**原因**: 不依賴 store 的全局狀態,讓測試計劃管理頁面可以獨立選擇專案和站別,不影響其他頁面。

#### 3. 新增事件處理函式
```javascript
// 處理專案選擇變更
const handleProjectSelect = async (projectId) => {
  selectedStationId.value = null  // 清空站別選擇
  if (projectId) {
    await projectStore.fetchProjectStations(projectId)  // 載入站別列表
  }
  testPlanItems.value = []  // 清空測試計劃列表
}

// 處理站別選擇變更
const handleStationSelect = async (stationId) => {
  await loadTestPlan()  // 載入測試計劃
}
```

#### 4. 修改載入測試計劃邏輯
**原有程式碼**:
```javascript
const loadTestPlan = async () => {
  if (!currentStation.value) {
    ElMessage.warning('請先選擇站別')
    return
  }
  // ...
  testPlanItems.value = await getStationTestPlan(
    currentStation.value.id,
    projectStore.currentProject?.id || currentStation.value.project_id,
    false
  )
}
```

**修改後**:
```javascript
const loadTestPlan = async () => {
  if (!selectedProjectId.value || !selectedStationId.value) {
    testPlanItems.value = []  // 清空測試計劃列表
    return
  }
  // ...
  testPlanItems.value = await getStationTestPlan(
    selectedStationId.value,
    selectedProjectId.value,
    false
  )
}
```

#### 5. 修改新增測試項目邏輯
**原有程式碼**:
```javascript
await createTestPlanItem({
  project_id: projectStore.currentProject?.id || currentStation.value.project_id,
  station_id: currentStation.value.id,
  // ...
})
```

**修改後**:
```javascript
await createTestPlanItem({
  project_id: selectedProjectId.value,
  station_id: selectedStationId.value,
  // ...
})
```

#### 6. 修改初始化邏輯
**原有程式碼**:
```javascript
onMounted(async () => {
  if (projectStore.projects.length === 0) {
    await projectStore.fetchProjects()
  }
  if (projectStore.currentProject) {
    await projectStore.fetchProjectStations(projectStore.currentProject.id)
  }
  loadTestPlan()
})
```

**修改後**:
```javascript
onMounted(async () => {
  if (projectStore.projects.length === 0) {
    await projectStore.fetchProjects()
  }
  // 如果 store 中有當前專案,自動選擇
  if (projectStore.currentProject) {
    selectedProjectId.value = projectStore.currentProject.id
    await projectStore.fetchProjectStations(projectStore.currentProject.id)
    // 如果 store 中有當前站別,自動選擇
    if (projectStore.currentStation) {
      selectedStationId.value = projectStore.currentStation.id
    }
  }
  loadTestPlan()
})
```

**說明**: 保持向後兼容,如果使用者之前在其他頁面選擇了專案和站別,會自動帶入到測試計劃管理頁面。

#### 7. UI 改進
- 新增篩選卡片樣式 (`.filter-card`)
- 更新提示訊息,顯示當前選擇的專案和站別
- 新增項目按鈕的禁用條件改為 `!selectedProject || !selectedStation`

### 後端修改
後端 API 已經支援 `project_id` 和 `station_id` 參數,無需修改。

**API 端點**: `GET /api/stations/{station_id}/testplan`

**參數**:
- `station_id` (路徑參數): 站別 ID
- `project_id` (查詢參數): 專案 ID (必填)
- `enabled_only` (查詢參數): 只傳回已啟用的項目 (預設: true)
- `test_plan_name` (查詢參數): 測試計劃名稱 (選填)

## 使用方式

1. **選擇專案**: 在「選擇專案」下拉選單中選擇要查看的專案
2. **選擇站別**: 在「選擇站別」下拉選單中選擇要查看的站別 (選擇專案後才可選)
3. **查看測試計劃**: 選擇站別後,測試計劃列表會自動載入
4. **新增測試項目**: 選擇專案和站別後,可以新增測試項目
5. **上傳 CSV**: 上傳對話框會預填當前選擇的專案和站別

## 優點

1. **獨立篩選**: 測試計劃管理頁面可以獨立選擇專案和站別,不依賴其他頁面的選擇
2. **清空功能**: 支援清除選擇,方便切換不同專案/站別查看
3. **向後兼容**: 如果 store 中已有當前專案/站別選擇,會自動帶入
4. **User Experience**: 改善使用者體驗,不需要先在其他頁面選擇專案/站別

## 測試建議

1. 測試選擇不同專案時,站別列表是否正確更新
2. 測試選擇站別後,測試計劃是否正確載入
3. 測試清除選擇後,列表是否正確清空
4. 測試新增測試項目時,是否使用正確的專案和站別 ID
5. 測試上傳 CSV 時,預填的專案和站別是否正確
6. 測試頁面重新整理後,是否能保持之前的選擇 (如果 store 中有值)
