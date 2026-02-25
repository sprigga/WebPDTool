<template>
  <div class="project-manage-container">
    <!-- 新增: 導航列 - 提供快速存取各個管理頁面 -->
    <el-card class="nav-card" shadow="never">
      <el-row :gutter="10" align="middle" justify="space-between">
        <el-col :span="18">
          <div class="nav-buttons">
            <el-button size="default" @click="navigateTo('/main')">
              測試主畫面
            </el-button>
            <el-button size="default" @click="navigateTo('/testplan')">
              測試計劃管理
            </el-button>
            <el-button type="primary" size="default" disabled>
              專案管理
            </el-button>
            <el-button size="default" @click="navigateTo('/users')">
              使用者管理
            </el-button>
          </div>
        </el-col>
        <el-col :span="6" style="text-align: right">
          <el-text type="info">{{ authStore.user?.username || '-' }}</el-text>
          <el-button type="danger" size="small" @click="handleLogout" style="margin-left: 10px">
            登出
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-alert
      v-if="!isAdmin"
      title="僅供查看"
      description="您沒有管理權限，無法新增、編輯或刪除專案和站別"
      type="info"
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-row :gutter="20" class="content-row">
      <!-- Left Panel - Projects -->
      <el-col :span="12" class="left-panel">
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

          <!-- Projects Table -->
          <div v-if="projectStore.projects.length === 0 && !loading.projects" class="empty-state">
            <el-empty description="尚無專案資料，點擊「新增專案」開始建立" />
          </div>
          <el-table
            v-else
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
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <el-text>共 {{ projectStore.projects.length }} 個專案</el-text>
          </div>
        </el-card>
      </el-col>

      <!-- Right Panel - Stations -->
      <el-col :span="12" class="right-panel">
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
          <div v-else-if="projectStore.stations.length === 0 && !loading.stations" class="empty-state">
            <el-empty description="尚無站別資料，點擊「新增站別」為此專案建立站別" />
          </div>
          <div v-else>
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
                  <el-tooltip content="需要管理員權限" :disabled="canEdit">
                    <span>
                      <el-button
                        size="small"
                        :disabled="!canEdit"
                        @click="handleEditStation(row)"
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
                        @click="handleDeleteStation(row)"
                      >
                        刪除
                      </el-button>
                    </span>
                  </el-tooltip>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="hasSelectedProject" class="table-footer">
              <el-text>共 {{ projectStore.stations.length }} 個站別</el-text>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { createProject, updateProject, deleteProject, createStation, updateStation, deleteStation } from '@/api/projects'

// 新增: Router 用於導航
const router = useRouter()
const projectStore = useProjectStore()
const authStore = useAuthStore()

const projectStore = useProjectStore()
const authStore = useAuthStore()

// 新增: 導航函數
const navigateTo = (path) => {
  router.push(path)
}

// 新增: 登出函數
const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    router.push('/login')
  }
}

// State
const selectedProjectId = ref(parseInt(localStorage.getItem('selectedProjectId')) || null)
const loading = reactive({
  projects: false,
  stations: false
})

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

// Computed
const isAdmin = computed(() => authStore.user?.role === 'admin')
const canEdit = computed(() => isAdmin.value)
const selectedProject = computed(() =>
  projectStore.projects.find(p => p.id === selectedProjectId.value)
)
const hasSelectedProject = computed(() => !!selectedProjectId.value)

// Handlers
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

const handleProjectSelect = (currentRow) => {
  if (currentRow) {
    selectedProjectId.value = currentRow.id
    localStorage.setItem('selectedProjectId', currentRow.id)
    loadStations()
  }
}

const handleEditProject = (row) => {
  Object.assign(editingProject, { ...row })
  showProjectDialog.value = true
}

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

const handleEditStation = (row) => {
  Object.assign(editingStation, { ...row })
  showStationDialog.value = true
}

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

onMounted(async () => {
  loading.projects = true
  try {
    await projectStore.fetchProjects()

    // Auto-select from localStorage or first project
    if (selectedProjectId.value) {
      await loadStations()
    } else if (projectStore.projects.length > 0) {
      selectedProjectId.value = projectStore.projects[0].id
      localStorage.setItem('selectedProjectId', selectedProjectId.value)
      await loadStations()
    }
  } catch (error) {
    console.error('Failed to load projects:', error)
    ElMessage.error('載入專案列表失敗')
  } finally {
    loading.projects = false
  }
})
</script>

<style scoped>
.project-manage-container {
  padding: 20px;
  height: calc(100vh - 180px);
}

/* 新增: 導航列樣式 */
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

.content-row {
  height: 100%;
}

.left-panel,
.right-panel {
  height: 100%;
}

.left-panel {
  min-width: 400px;
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

.table-footer {
  margin-top: 16px;
  text-align: right;
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
</style>
