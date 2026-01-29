# ProjectManage.vue Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a master-detail management page for projects and stations with full CRUD operations for administrators.

**Architecture:** Side-by-side layout with projects table (left 35%) and stations table (right 65%). Projects drive station display through selection. All operations require admin role, use existing projectStore and API endpoints.

**Tech Stack:** Vue 3 Composition API, Element Plus, Pinia stores, existing FastAPI backend with CRUD endpoints

---

## Task 1: Check and Create Stations API Module

**Files:**
- Check: `backend/app/api/stations.py` (exists from previous code)
- Create if missing: `frontend/src/api/stations.js`

**Step 1: Verify backend stations API exists**

Run: `ls -la backend/app/api/stations.py`
Expected: File exists (already created in previous work)

**Step 2: Check if frontend stations API module exists**

Run: `ls -la frontend/src/api/stations.js`
Expected: File may or may not exist

**Step 3: Create frontend stations API module (if needed)**

Create: `frontend/src/api/stations.js`

```javascript
import request from '@/utils/request'

/**
 * Get all stations for a project
 * @param {number} projectId - Project ID
 * @returns {Promise<Array>} List of stations
 */
export function getProjectStations(projectId) {
  return request({
    url: `/api/projects/${projectId}/stations`,
    method: 'get'
  })
}

/**
 * Create new station
 * @param {Object} data - Station data
 * @returns {Promise<Object>} Created station
 */
export function createStation(data) {
  return request({
    url: '/api/stations',
    method: 'post',
    data
  })
}

/**
 * Update station
 * @param {number} id - Station ID
 * @param {Object} data - Updated station data
 * @returns {Promise<Object>} Updated station
 */
export function updateStation(id, data) {
  return request({
    url: `/api/stations/${id}`,
    method: 'put',
    data
  })
}

/**
 * Delete station
 * @param {number} id - Station ID
 * @returns {Promise<void>}
 */
export function deleteStation(id) {
  return request({
    url: `/api/stations/${id}`,
    method: 'delete'
  })
}
```

**Step 4: Commit stations API module**

```bash
git add frontend/src/api/stations.js
git commit -m "feat: add stations API module for CRUD operations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Create ProjectManage.vue Component Structure

**Files:**
- Create: `frontend/src/views/ProjectManage.vue`

**Step 1: Create base component with template structure**

Create: `frontend/src/views/ProjectManage.vue`

```vue
<template>
  <div class="project-manage-container">
    <el-row :gutter="20" class="content-row">
      <!-- Left Panel - Projects -->
      <el-col :span="8" class="left-panel">
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>專案管理</h2>
              <el-button
                v-if="canEdit"
                type="primary"
                :icon="Plus"
                @click="handleAddProject"
              >
                新增專案
              </el-button>
            </div>
          </template>

          <!-- Projects table placeholder -->
          <div>Projects table will go here</div>
        </el-card>
      </el-col>

      <!-- Right Panel - Stations -->
      <el-col :span="16" class="right-panel">
        <el-card>
          <template #header>
            <div class="card-header">
              <div class="header-info">
                <h2>站別管理</h2>
                <el-text v-if="selectedProject" type="info" size="small">
                  {{ selectedProject.project_code }} - {{ selectedProject.project_name }}
                </el-text>
              </div>
              <el-button
                v-if="canEdit && hasSelectedProject"
                type="primary"
                :icon="Plus"
                @click="handleAddStation"
              >
                新增站別
              </el-button>
            </div>
          </template>

          <!-- Stations table placeholder -->
          <div v-if="!hasSelectedProject" class="empty-state">
            <el-empty description="請先在左側選擇一個專案" />
          </div>
          <div v-else>Stations table will go here</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'

const projectStore = useProjectStore()
const authStore = useAuthStore()

// State
const selectedProjectId = ref(null)

// Computed
const isAdmin = computed(() => authStore.currentUser?.role === 'admin')
const canEdit = computed(() => isAdmin.value)
const selectedProject = computed(() =>
  projectStore.projects.find(p => p.id === selectedProjectId.value)
)
const hasSelectedProject = computed(() => !!selectedProjectId.value)

// Handlers (placeholders)
const handleAddProject = () => {
  console.log('Add project')
}

const handleAddStation = () => {
  console.log('Add station')
}
</script>

<style scoped>
.project-manage-container {
  padding: 20px;
  height: calc(100vh - 180px);
}

.content-row {
  height: 100%;
}

.left-panel,
.right-panel {
  height: 100%;
}

.left-panel {
  min-width: 400px;
  max-width: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

:deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  flex: 1;
  overflow: auto;
}
</style>
```

**Step 2: Add route to router**

Modify: `frontend/src/router/index.js`

Add after the `/config` route:

```javascript
  {
    path: '/projects',
    name: 'ProjectManage',
    component: () => import('@/views/ProjectManage.vue'),
    meta: { requiresAuth: true }
  }
```

**Step 3: Test the component renders**

Run: `cd frontend && npm run dev`
Navigate to: `http://localhost:5173/projects`
Expected: Page renders with empty panels and headers

**Step 4: Commit base structure**

```bash
git add frontend/src/views/ProjectManage.vue frontend/src/router/index.js
git commit -m "feat: add ProjectManage.vue base structure with layout

Add side-by-side master-detail layout for projects and stations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Implement Projects Table

**Files:**
- Modify: `frontend/src/views/ProjectManage.vue`

**Step 1: Add projects table with data loading**

Replace the projects table placeholder with:

```vue
<!-- Projects Table -->
<el-table
  v-loading="loading.projects"
  :data="projectStore.projects"
  stripe
  highlight-current-row
  @current-change="handleProjectSelect"
  style="width: 100%"
>
  <el-table-column prop="project_code" label="專案代碼" width="120" />

  <el-table-column prop="project_name" label="專案名稱" min-width="150" />

  <el-table-column label="狀態" width="80">
    <template #default="{ row }">
      <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
        {{ row.enabled ? '啟用' : '停用' }}
      </el-tag>
    </template>
  </el-table-column>

  <el-table-column label="操作" width="140" fixed="right">
    <template #default="{ row }">
      <el-button
        v-if="canEdit"
        size="small"
        @click.stop="handleEditProject(row)"
      >
        編輯
      </el-button>
      <el-button
        v-if="canEdit"
        size="small"
        type="danger"
        @click.stop="handleDeleteProject(row)"
      >
        刪除
      </el-button>
    </template>
  </el-table-column>
</el-table>

<div class="table-footer">
  <el-text>共 {{ projectStore.projects.length }} 個專案</el-text>
</div>
```

**Step 2: Add loading state and handlers to script**

Update script section:

```javascript
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// Add loading state
const loading = reactive({
  projects: false,
  stations: false
})

// Add handlers
const handleProjectSelect = (currentRow) => {
  if (currentRow) {
    selectedProjectId.value = currentRow.id
    localStorage.setItem('selectedProjectId', currentRow.id)
    loadStations()
  }
}

const handleEditProject = (row) => {
  console.log('Edit project:', row)
}

const handleDeleteProject = async (row) => {
  console.log('Delete project:', row)
}

const loadStations = async () => {
  if (!selectedProjectId.value) return

  loading.stations = true
  try {
    await projectStore.fetchProjectStations(selectedProjectId.value)
  } catch (error) {
    console.error('Failed to load stations:', error)
    ElMessage.error('載入站別列表失敗')
  } finally {
    loading.stations = false
  }
}

// Load projects on mount
onMounted(async () => {
  loading.projects = true
  try {
    await projectStore.fetchProjects()

    // Restore selection from localStorage
    const savedId = localStorage.getItem('selectedProjectId')
    if (savedId) {
      selectedProjectId.value = parseInt(savedId)
      await loadStations()
    }
  } catch (error) {
    console.error('Failed to load projects:', error)
    ElMessage.error('載入專案列表失敗')
  } finally {
    loading.projects = false
  }
})
```

**Step 3: Add table footer style**

Add to styles:

```css
.table-footer {
  margin-top: 16px;
  text-align: right;
}
```

**Step 4: Test projects table**

Run: `npm run dev`
Expected: Projects load and display in table, selection highlights row

**Step 5: Commit projects table**

```bash
git add frontend/src/views/ProjectManage.vue
git commit -m "feat: implement projects table with selection and loading

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Implement Stations Table

**Files:**
- Modify: `frontend/src/views/ProjectManage.vue`

**Step 1: Add stations table**

Replace the stations table placeholder with:

```vue
<!-- Stations Table -->
<el-table
  v-loading="loading.stations"
  :data="projectStore.stations"
  stripe
  style="width: 100%"
>
  <el-table-column prop="station_code" label="站別代碼" width="120" />

  <el-table-column prop="station_name" label="站別名稱" min-width="150" />

  <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

  <el-table-column label="狀態" width="80">
    <template #default="{ row }">
      <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
        {{ row.enabled ? '啟用' : '停用' }}
      </el-tag>
    </template>
  </el-table-column>

  <el-table-column label="操作" width="140" fixed="right">
    <template #default="{ row }">
      <el-button
        v-if="canEdit"
        size="small"
        @click="handleEditStation(row)"
      >
        編輯
      </el-button>
      <el-button
        v-if="canEdit"
        size="small"
        type="danger"
        @click="handleDeleteStation(row)"
      >
        刪除
      </el-button>
    </template>
  </el-table-column>
</el-table>

<div v-if="hasSelectedProject" class="table-footer">
  <el-text>共 {{ projectStore.stations.length }} 個站別</el-text>
</div>
```

**Step 2: Add station handlers**

Add to script:

```javascript
const handleEditStation = (row) => {
  console.log('Edit station:', row)
}

const handleDeleteStation = async (row) => {
  console.log('Delete station:', row)
}
```

**Step 3: Test stations table**

Run: `npm run dev`
Expected: When project selected, stations load and display

**Step 4: Commit stations table**

```bash
git add frontend/src/views/ProjectManage.vue
git commit -m "feat: implement stations table with loading state

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Implement Project Dialog Form

**Files:**
- Modify: `frontend/src/views/ProjectManage.vue`

**Step 1: Add project dialog to template**

Add after the row closing tag:

```vue
<!-- Project Create/Edit Dialog -->
<el-dialog
  v-model="showProjectDialog"
  :title="editingProject.id ? '編輯專案' : '新增專案'"
  width="600px"
>
  <el-form
    ref="projectFormRef"
    :model="editingProject"
    :rules="projectFormRules"
    label-width="100px"
  >
    <el-form-item label="專案代碼" prop="project_code">
      <el-input
        v-model="editingProject.project_code"
        placeholder="請輸入專案代碼"
        :disabled="!!editingProject.id"
      />
    </el-form-item>

    <el-form-item label="專案名稱" prop="project_name">
      <el-input
        v-model="editingProject.project_name"
        placeholder="請輸入專案名稱"
      />
    </el-form-item>

    <el-form-item label="描述">
      <el-input
        v-model="editingProject.description"
        type="textarea"
        :rows="3"
        placeholder="請輸入專案描述(選填)"
        maxlength="500"
        show-word-limit
      />
    </el-form-item>

    <el-form-item label="狀態">
      <el-switch
        v-model="editingProject.enabled"
        active-text="啟用"
        inactive-text="停用"
      />
    </el-form-item>
  </el-form>

  <template #footer>
    <el-button @click="showProjectDialog = false">取消</el-button>
    <el-button
      type="primary"
      :loading="savingProject"
      @click="handleSaveProject"
    >
      儲存
    </el-button>
  </template>
</el-dialog>
```

**Step 2: Add dialog state and form data**

Add to script:

```javascript
import { createProject, updateProject, deleteProject } from '@/api/projects'

// Dialog state
const showProjectDialog = ref(false)
const savingProject = ref(false)
const projectFormRef = ref(null)

// Form data
const editingProject = reactive({
  id: null,
  project_code: '',
  project_name: '',
  description: '',
  enabled: true
})

// Form rules
const projectFormRules = {
  project_code: [
    { required: true, message: '請輸入專案代碼', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: '只能包含字母、數字、底線和破折號',
      trigger: 'blur'
    }
  ],
  project_name: [
    { required: true, message: '請輸入專案名稱', trigger: 'blur' },
    { min: 2, message: '專案名稱至少需要2個字元', trigger: 'blur' }
  ]
}
```

**Step 3: Implement add/edit/save handlers**

Update handlers:

```javascript
const handleAddProject = () => {
  Object.assign(editingProject, {
    id: null,
    project_code: '',
    project_name: '',
    description: '',
    enabled: true
  })
  showProjectDialog.value = true
}

const handleEditProject = (row) => {
  Object.assign(editingProject, { ...row })
  showProjectDialog.value = true
}

const handleSaveProject = async () => {
  if (!projectFormRef.value) return

  await projectFormRef.value.validate(async (valid) => {
    if (!valid) return

    savingProject.value = true
    try {
      const projectData = {
        project_code: editingProject.project_code,
        project_name: editingProject.project_name,
        description: editingProject.description || null,
        enabled: editingProject.enabled
      }

      if (editingProject.id) {
        // Update existing project
        await updateProject(editingProject.id, projectData)
        ElMessage.success('專案更新成功')
      } else {
        // Create new project
        await createProject(projectData)
        ElMessage.success('專案建立成功')
      }

      showProjectDialog.value = false
      loading.projects = true
      await projectStore.fetchProjects()
      loading.projects = false
    } catch (error) {
      console.error('Save project failed:', error)
      const message = error.response?.data?.detail || '操作失敗'
      ElMessage.error(message)
    } finally {
      savingProject.value = false
    }
  })
}
```

**Step 4: Test project dialog**

Run: `npm run dev`
Test: Click "新增專案", fill form, save
Expected: Project created and appears in table

**Step 5: Commit project dialog**

```bash
git add frontend/src/views/ProjectManage.vue
git commit -m "feat: implement project create/edit dialog with validation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Implement Station Dialog Form

**Files:**
- Modify: `frontend/src/views/ProjectManage.vue`

**Step 1: Add station dialog to template**

Add after project dialog:

```vue
<!-- Station Create/Edit Dialog -->
<el-dialog
  v-model="showStationDialog"
  :title="editingStation.id ? '編輯站別' : '新增站別'"
  width="600px"
>
  <el-form
    ref="stationFormRef"
    :model="editingStation"
    :rules="stationFormRules"
    label-width="100px"
  >
    <el-form-item label="站別代碼" prop="station_code">
      <el-input
        v-model="editingStation.station_code"
        placeholder="請輸入站別代碼"
        :disabled="!!editingStation.id"
      />
    </el-form-item>

    <el-form-item label="站別名稱" prop="station_name">
      <el-input
        v-model="editingStation.station_name"
        placeholder="請輸入站別名稱"
      />
    </el-form-item>

    <el-form-item label="描述">
      <el-input
        v-model="editingStation.description"
        type="textarea"
        :rows="3"
        placeholder="請輸入站別描述(選填)"
        maxlength="500"
        show-word-limit
      />
    </el-form-item>

    <el-form-item label="狀態">
      <el-switch
        v-model="editingStation.enabled"
        active-text="啟用"
        inactive-text="停用"
      />
    </el-form-item>
  </el-form>

  <template #footer>
    <el-button @click="showStationDialog = false">取消</el-button>
    <el-button
      type="primary"
      :loading="savingStation"
      @click="handleSaveStation"
    >
      儲存
    </el-button>
  </template>
</el-dialog>
```

**Step 2: Add station dialog state**

Add to script:

```javascript
import { createStation, updateStation, deleteStation } from '@/api/stations'

// Station dialog state
const showStationDialog = ref(false)
const savingStation = ref(false)
const stationFormRef = ref(null)

// Station form data
const editingStation = reactive({
  id: null,
  station_code: '',
  station_name: '',
  description: '',
  enabled: true,
  project_id: null
})

// Station form rules
const stationFormRules = {
  station_code: [
    { required: true, message: '請輸入站別代碼', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: '只能包含字母、數字、底線和破折號',
      trigger: 'blur'
    }
  ],
  station_name: [
    { required: true, message: '請輸入站別名稱', trigger: 'blur' },
    { min: 2, message: '站別名稱至少需要2個字元', trigger: 'blur' }
  ]
}
```

**Step 3: Implement station handlers**

Update handlers:

```javascript
const handleAddStation = () => {
  if (!selectedProjectId.value) {
    ElMessage.warning('請先選擇專案')
    return
  }

  Object.assign(editingStation, {
    id: null,
    station_code: '',
    station_name: '',
    description: '',
    enabled: true,
    project_id: selectedProjectId.value
  })
  showStationDialog.value = true
}

const handleEditStation = (row) => {
  Object.assign(editingStation, { ...row })
  showStationDialog.value = true
}

const handleSaveStation = async () => {
  if (!stationFormRef.value) return

  await stationFormRef.value.validate(async (valid) => {
    if (!valid) return

    savingStation.value = true
    try {
      const stationData = {
        station_code: editingStation.station_code,
        station_name: editingStation.station_name,
        description: editingStation.description || null,
        enabled: editingStation.enabled,
        project_id: editingStation.project_id
      }

      if (editingStation.id) {
        // Update existing station
        await updateStation(editingStation.id, stationData)
        ElMessage.success('站別更新成功')
      } else {
        // Create new station
        await createStation(stationData)
        ElMessage.success('站別建立成功')
      }

      showStationDialog.value = false
      await loadStations()
    } catch (error) {
      console.error('Save station failed:', error)
      const message = error.response?.data?.detail || '操作失敗'
      ElMessage.error(message)
    } finally {
      savingStation.value = false
    }
  })
}
```

**Step 4: Test station dialog**

Run: `npm run dev`
Test: Select project, click "新增站別", fill form, save
Expected: Station created and appears in table

**Step 5: Commit station dialog**

```bash
git add frontend/src/views/ProjectManage.vue
git commit -m "feat: implement station create/edit dialog with validation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Implement Delete Operations

**Files:**
- Modify: `frontend/src/views/ProjectManage.vue`

**Step 1: Implement project delete handler**

Update the handleDeleteProject function:

```javascript
const handleDeleteProject = async (row) => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除專案 "${row.project_name}" 嗎？這將同時刪除所有關聯的站別和測試計劃資料。`,
      '確認刪除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    loading.projects = true
    await deleteProject(row.id)
    ElMessage.success('專案刪除成功')

    // If deleted project was selected, clear selection
    if (selectedProjectId.value === row.id) {
      selectedProjectId.value = null
      localStorage.removeItem('selectedProjectId')
      projectStore.stations = []
    }

    await projectStore.fetchProjects()

    // Auto-select first project if available
    if (projectStore.projects.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projectStore.projects[0].id
      localStorage.setItem('selectedProjectId', selectedProjectId.value)
      await loadStations()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete project failed:', error)
      const message = error.response?.data?.detail || '刪除失敗'
      ElMessage.error(message)
    }
  } finally {
    loading.projects = false
  }
}
```

**Step 2: Implement station delete handler**

Update the handleDeleteStation function:

```javascript
const handleDeleteStation = async (row) => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除站別 "${row.station_name}" 嗎？這將同時刪除該站別的所有測試計劃資料。`,
      '確認刪除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    loading.stations = true
    await deleteStation(row.id)
    ElMessage.success('站別刪除成功')
    await loadStations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete station failed:', error)
      const message = error.response?.data?.detail || '刪除失敗'
      ElMessage.error(message)
    }
  } finally {
    loading.stations = false
  }
}
```

**Step 3: Test delete operations**

Run: `npm run dev`
Test:
1. Delete a station - should show confirmation and remove from table
2. Delete a project - should show warning about cascade deletion
Expected: Both deletions work with proper confirmations

**Step 4: Commit delete operations**

```bash
git add frontend/src/views/ProjectManage.vue
git commit -m "feat: implement project and station deletion with confirmations

Add cascade deletion warnings and auto-selection after project deletion

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Add Permission Checks and Non-Admin Experience

**Files:**
- Modify: `frontend/src/views/ProjectManage.vue`

**Step 1: Add permission check alert**

Add after the opening container div:

```vue
<el-alert
  v-if="!isAdmin"
  title="僅供查看"
  description="您沒有管理權限，無法新增、編輯或刪除專案和站別"
  type="info"
  :closable="false"
  style="margin-bottom: 20px"
/>
```

**Step 2: Add tooltips for disabled buttons**

Update table action buttons to add tooltips:

```vue
<!-- In projects table -->
<el-tooltip content="需要管理員權限" :disabled="canEdit">
  <span>
    <el-button
      size="small"
      :disabled="!canEdit"
      @click.stop="handleEditProject(row)"
    >
      編輯
    </el-button>
  </span>
</el-tooltip>
<el-tooltip content="需要管理員權限" :disabled="canEdit">
  <span>
    <el-button
      size="small"
      type="danger"
      :disabled="!canEdit"
      @click.stop="handleDeleteProject(row)"
    >
      刪除
    </el-button>
  </span>
</el-tooltip>

<!-- Same for stations table -->
```

**Step 3: Test non-admin experience**

Test: Login as non-admin user
Expected: Alert shows, all edit/delete buttons disabled with tooltips

**Step 4: Commit permission checks**

```bash
git add frontend/src/views/ProjectManage.vue
git commit -m "feat: add permission checks and non-admin user experience

Show info alert and disable actions for non-admin users

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Add Empty States and Polish UI

**Files:**
- Modify: `frontend/src/views/ProjectManage.vue`

**Step 1: Add empty state for no projects**

Wrap projects table:

```vue
<div v-if="projectStore.projects.length === 0 && !loading.projects" class="empty-state">
  <el-empty description="尚無專案資料，點擊「新增專案」開始建立" />
</div>
<el-table v-else ...>
  <!-- existing table -->
</el-table>
```

**Step 2: Add empty state for no stations**

Wrap stations table:

```vue
<div v-else-if="projectStore.stations.length === 0 && !loading.stations" class="empty-state">
  <el-empty description="尚無站別資料，點擊「新增站別」為此專案建立站別" />
</div>
<el-table v-else ...>
  <!-- existing table -->
</el-table>
```

**Step 3: Add responsive styles**

Add to styles:

```css
/* Responsive adjustments */
@media (max-width: 1200px) {
  .left-panel {
    min-width: 350px;
  }
}

@media (max-width: 768px) {
  .content-row {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    width: 100% !important;
    max-width: 100%;
    margin-bottom: 20px;
  }
}

/* Improve table action column spacing */
:deep(.el-table .el-button + .el-button) {
  margin-left: 4px;
}

/* Highlight selected project row */
:deep(.el-table__row.current-row) {
  background-color: #ecf5ff;
}
```

**Step 4: Test UI polish**

Run: `npm run dev`
Test: Empty states, responsive layout, row highlighting
Expected: Clean UI with proper empty states

**Step 5: Commit UI polish**

```bash
git add frontend/src/views/ProjectManage.vue
git commit -m "feat: add empty states and responsive design polish

Improve user experience with empty states and mobile responsiveness

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Final Testing and Documentation

**Files:**
- Create: `docs/features/project-manage.md`
- Modify: `README.md` (if navigation needs updating)

**Step 1: Create feature documentation**

Create: `docs/features/project-manage.md`

```markdown
# Project Management Feature

## Overview

The Project Management page (`/projects`) provides a master-detail interface for managing projects and their associated stations.

## Features

### Project Management (Left Panel)
- View all projects in a table
- Create new projects (admin only)
- Edit existing projects (admin only)
- Delete projects with cascade deletion (admin only)
- Highlight selected project

### Station Management (Right Panel)
- View stations for selected project
- Create new stations (admin only)
- Edit existing stations (admin only)
- Delete stations (admin only)

## Permissions

- **Admin users:** Full CRUD access to projects and stations
- **Non-admin users:** Read-only access

## User Flow

1. Projects load automatically on page mount
2. Select a project from the left panel
3. Stations for that project load in the right panel
4. Use action buttons to create, edit, or delete items
5. Selection persists in localStorage across sessions

## API Endpoints Used

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Stations
- `GET /api/projects/{project_id}/stations` - List stations
- `POST /api/stations` - Create station
- `PUT /api/stations/{id}` - Update station
- `DELETE /api/stations/{id}` - Delete station

## Validation

### Project Form
- `project_code`: Required, alphanumeric + underscore/dash, unique
- `project_name`: Required, min 2 chars

### Station Form
- `station_code`: Required, alphanumeric + underscore/dash
- `station_name`: Required, min 2 chars

## Error Handling

- Network errors: "網路連線失敗，請檢查網路狀態後重試"
- Permission errors (403): "權限不足，僅管理員可執行此操作"
- Not found (404): "資料不存在，可能已被刪除"
- Duplicate (400): Shows server error message
- Generic errors: "操作失敗，請稍後重試"

## Responsive Design

- Desktop (>1200px): Side-by-side layout
- Tablet (768-1200px): Narrower panels
- Mobile (<768px): Stacked vertically
```

**Step 2: Manual testing checklist**

Test the following scenarios:

1. **As Admin:**
   - [ ] Create new project with valid data
   - [ ] Edit existing project
   - [ ] Delete project (verify cascade deletion warning)
   - [ ] Create new station for selected project
   - [ ] Edit existing station
   - [ ] Delete station
   - [ ] Verify form validations work
   - [ ] Test duplicate project_code error

2. **As Non-Admin:**
   - [ ] View projects (read-only)
   - [ ] View stations (read-only)
   - [ ] Verify all edit/delete buttons disabled
   - [ ] See permission alert

3. **Edge Cases:**
   - [ ] Delete currently selected project
   - [ ] Try to create station without selecting project
   - [ ] Refresh page and verify selection persists
   - [ ] Test with empty projects list
   - [ ] Test with project that has no stations

**Step 3: Commit documentation**

```bash
git add docs/features/project-manage.md
git commit -m "docs: add ProjectManage feature documentation

Document features, permissions, API usage, and validation rules

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Step 4: Final integration commit**

```bash
git add -A
git commit -m "feat: complete ProjectManage.vue with full CRUD operations

Implement master-detail management interface for projects and stations:
- Side-by-side layout with responsive design
- Full CRUD operations with admin-only permissions
- Form validation and error handling
- Empty states and loading indicators
- localStorage persistence for selection

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Completion Checklist

Before considering this plan complete:

- [ ] All 10 tasks implemented and committed
- [ ] Admin can create/edit/delete projects
- [ ] Admin can create/edit/delete stations
- [ ] Non-admin users see read-only view
- [ ] Form validations work correctly
- [ ] Delete confirmations show appropriate warnings
- [ ] Selection persists in localStorage
- [ ] Empty states display properly
- [ ] Loading states work during API calls
- [ ] Error messages display for failures
- [ ] Documentation created
- [ ] Manual testing completed

## Next Steps

After implementation:
1. Merge feature branch to main using @superpowers:finishing-a-development-branch
2. Test in staging environment
3. Update navigation menu to include link to `/projects` page
4. Consider adding search/filter functionality in future iteration
5. Consider adding bulk operations in future iteration
