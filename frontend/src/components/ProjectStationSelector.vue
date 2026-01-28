<template>
  <div class="selector-container">
    <el-form label-width="100px">
      <el-form-item label="專案">
        <el-select
          v-model="selectedProjectId"
          placeholder="請選擇專案"
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
import { ref, onMounted, watch } from 'vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['project-selected', 'station-selected'])

const projectStore = useProjectStore()
const projects = ref([])
const stations = ref([])
const selectedProjectId = ref(null)
const selectedStationId = ref(null)

onMounted(async () => {
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
    ElMessage.error('載入專案列表失敗')
  }
})

const loadStations = async (projectId) => {
  try {
    stations.value = await projectStore.fetchProjectStations(projectId)
  } catch (error) {
    ElMessage.error('載入站別列表失敗')
    stations.value = []
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

// 原有程式碼: 當選擇站別時，儲存站別資訊並發送事件
// 修正: 加入更詳細的除錯訊息和錯誤處理
const handleStationChange = (stationId) => {
  console.log('Station ID selected:', stationId)
  console.log('Available stations:', stations.value)

  if (stationId) {
    const station = stations.value.find(s => s.id === stationId)
    console.log('Found station:', station)

    if (!station) {
      console.error('Station not found in stations array!')
      return
    }

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
