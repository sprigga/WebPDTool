# TestPlanManage.vue 元件整合指南

## 概述

本文件說明如何在 `TestPlanManage.vue` 中整合 `frontend/src/components/` 目錄下的可重用元件。

## 已整合的元件

### 1. DynamicParamForm.vue (測試參數動態表單)

**用途:** 根據選擇的測試類型和儀器模式,動態生成參數輸入表單

**整合位置:** 編輯對話框的「測試參數設定」區塊 (第359-364行)

**使用方式:**
```vue
<DynamicParamForm
  v-model="editingItem.parameters"
  :test-type="editingItem.test_type"
  :switch-mode="editingItem.switch_mode"
  @validation-change="handleParamValidation"
/>
```

**資料流:**
1. 使用者選擇測試類型 → 觸發 `handleTestTypeChange`
2. 使用者選擇儀器模式 → 觸發 `handleSwitchModeChange`
3. DynamicParamForm 根據類型和模式載入對應的參數模板
4. 使用者填寫參數 → 透過 `v-model` 雙向綁定到 `editingItem.parameters`
5. 表單驗證結果 → 透過 `@validation-change` 事件傳回

**相關程式碼:**
```javascript
// composables/useMeasurementParams.js
const { loadTemplates, testTypes, switchModes } = useMeasurementParams()

// 處理測試類型變更
const handleTestTypeChange = (testType) => {
  currentTestType.value = testType
  editingItem.switch_mode = ''
  editingItem.parameters = {}
}

// 處理儀器模式變更
const handleSwitchModeChange = (switchMode) => {
  currentSwitchMode.value = switchMode
  editingItem.parameters = {}
}

// 處理參數驗證
const handleParamValidation = (isValid) => {
  paramValidation.value = isValid
}
```

### 2. ProjectStationSelector.vue (專案站別選擇器)

**用途:** 提供統一的專案和站別選擇介面,自動處理資料載入和狀態同步

**整合位置:** 主頁面的篩選卡片區塊 (第36-78行)

**使用方式:**
```vue
<el-card class="filter-card" shadow="never">
  <ProjectStationSelector
    @project-selected="handleProjectSelected"
    @station-selected="handleStationSelected"
  />
</el-card>
```

**資料流:**
1. 元件掛載時自動載入專案列表
2. 如果有儲存的當前專案/站別,自動選擇並發送事件
3. 使用者選擇專案 → 觸發 `@project-selected` 事件
4. 使用者選擇站別 → 觸發 `@station-selected` 事件
5. 父元件接收事件,更新本地狀態並載入測試計劃

**事件處理器:**
```javascript
// 處理專案選擇
const handleProjectSelected = (project) => {
  selectedProjectId.value = project.id
  selectedStationId.value = null
  testPlanItems.value = []
}

// 處理站別選擇
const handleStationSelected = async (station) => {
  selectedStationId.value = station.id
  selectedProjectId.value = station.project_id
  await loadTestPlan()
}
```

**元件內部邏輯:**
- 自動與 Pinia projectStore 同步
- 專案變更時自動清空站別選擇
- 專案變更時自動載入該專案的站別列表
- 從 localStorage 恢復上次選擇的專案/站別

## 整合的優點

### 1. 程式碼可重用性
- DynamicParamForm 可在任何需要測試參數輸入的地方使用
- ProjectStationSelector 可在 TestPlanManage、TestMain 等多個頁面使用

### 2. 邏輯封裝
- 參數模板載入邏輯封裝在 useMeasurementParams composable
- 專案站別載入邏輯封裝在 ProjectStationSelector 元件

### 3. 降低維護成本
- 修改選擇器邏輯只需要改一個元件
- 參數驗證規則統一管理

### 4. 一致性
- 所有使用這些元件的頁面有相同的 UI 和行為
- 減少重複程式碼

## 整合檢查清單

使用元件時請確認:

- [ ] 已引入元件: `import ProjectStationSelector from '@/components/ProjectStationSelector.vue'`
- [ ] 已註冊元件 (使用 `<script setup>` 時自動註冊)
- [ ] 已綁定必要的事件處理器
- [ ] 已建立本地狀態變數 (如 `selectedProjectId`, `selectedStationId`)
- [ ] 已處理 computed 屬性 (如 `selectedProject`, `selectedStation`)
- [ ] 已在 onMounted 中處理初始化邏輯

## 常見問題

### Q1: 為什麼需要同時維護本地狀態和 store 狀態?

**A:**
- `projectStore.currentProject/currentStation` - 全域當前選擇,用於跨頁面共享
- `selectedProjectId/selectedStationId` - 頁面本地選擇,允許暫時選擇不同的專案/站別而不影響其他頁面

### Q2: ProjectStationSelector 如何處理初始值?

**A:** 元件在 `onMounted` 時會:
1. 載入專案列表
2. 檢查 `projectStore.currentProject` 是否存在
3. 如果存在,自動選擇並載入站別
4. 檢查 `projectStore.currentStation` 是否存在
5. 如果存在,自動選擇並發送 `station-selected` 事件

### Q3: 如何在上傳對話框中使用選擇器?

**A:** 上傳對話框目前保持獨立的選擇器,因為它需要:
- 獨立的表單狀態 (`uploadForm.projectId/stationId`)
- 不同的預設值邏輯
- 與主頁面選擇器互不干擾

如果需要統一,可以考慮為 ProjectStationSelector 添加 props:
```vue
<ProjectStationSelector
  :initial-project-id="uploadForm.projectId"
  :initial-station-id="uploadForm.stationId"
  @project-selected="handleUploadProjectChange"
  @station-selected="handleUploadStationChange"
/>
```

## 下一步建議

1. **統一上傳對話框的選擇器**
   - 修改 ProjectStationSelector 支援外部控制初始值
   - 在上傳對話框中也使用相同元件

2. **擴展 DynamicParamForm**
   - 添加更多測試類型的參數模板
   - 支援參數驗證規則自定義

3. **添加單元測試**
   - 測試元件的事件發送
   - 測試資料綁定邏輯
   - 測試錯誤處理

4. **效能優化**
   - 考慮使用 `v-memo` 優化大列表渲染
   - 使用 `shallowRef` 優化不需要深度響應的資料
