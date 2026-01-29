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
