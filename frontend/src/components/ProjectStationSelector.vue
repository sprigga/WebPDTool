<template>
  <div class="selector-container">
    <el-form label-width="100px">
      <el-form-item label="專案">
        <el-select
          v-model="selectedProjectId"
          placeholder="請選擇專案"
          :loading="loadingProjects"
          @change="handleProjectChange"
          style="width: 100%"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.project_name"
            :value="project.id"
          >
            <span>{{ project.project_code }} - {{ project.project_name }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="站別">
        <el-select
          v-model="selectedStationId"
          placeholder="請選擇站別"
          :disabled="!selectedProjectId || stations.length === 0"
          :loading="loadingStations"
          @change="handleStationChange"
          style="width: 100%"
        >
          <el-option
            v-for="station in stations"
            :key="station.id"
            :label="station.station_name"
            :value="station.id"
          >
            <span>{{ station.station_code }} - {{ station.station_name }}</span>
          </el-option>
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['project-selected', 'station-selected'])

const projectStore = useProjectStore()
const projects = ref([])
const stations = ref([])
const selectedProjectId = ref(null)
const selectedStationId = ref(null)
const loadingProjects = ref(false)
const loadingStations = ref(false)

onMounted(async () => {
  loadingProjects.value = true
  try {
    projects.value = await projectStore.fetchProjects()

    // Load saved selections
    if (projectStore.currentProject) {
      selectedProjectId.value = projectStore.currentProject.id
      await loadStations(selectedProjectId.value)

      if (projectStore.currentStation) {
        selectedStationId.value = projectStore.currentStation.id
        // 修正: 當從localStorage載入已儲存的站別時,主動發出事件通知父元件
        // 這樣可以避免"進入系統"按鈕因為stationSelected為false而保持disabled狀態
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
    stations.value = []
  } finally {
    loadingStations.value = false
  }
}

const handleProjectChange = async (projectId) => {
  selectedStationId.value = null
  if (projectId) {
    await loadStations(projectId)
    const project = projects.value.find(p => p.id === projectId)
    projectStore.setCurrentProject(project)
    emit('project-selected', project)
  }
}

const handleStationChange = (stationId) => {
  if (stationId) {
    const station = stations.value.find(s => s.id === stationId)
    if (!station) return
    projectStore.setCurrentStation(station)
    emit('station-selected', station)
  }
}
</script>

<style scoped>
.selector-container {
  padding: 10px 0;
}
</style>
