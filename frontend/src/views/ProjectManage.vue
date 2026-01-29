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
import { ref, computed, onMounted, reactive } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'

const projectStore = useProjectStore()
const authStore = useAuthStore()

// State
const selectedProjectId = ref(parseInt(localStorage.getItem('selectedProjectId')) || null)
const loading = reactive({
  projects: false,
  stations: false
})

// Computed
const isAdmin = computed(() => authStore.user?.role === 'admin')
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
</style>
