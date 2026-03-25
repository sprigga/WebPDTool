<template>
  <div class="modbus-config-container">
    <AppNavBar current-page="modbus-config" />

    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>Modbus Configuration</span>
          <el-button type="primary" @click="handleCreate">New Configuration</el-button>
        </div>
      </template>

      <el-form :inline="true" class="station-selector">
        <el-form-item label="Project">
          <el-select
            v-model="selectedProjectId"
            placeholder="Select Project"
            @change="handleProjectChange"
            filterable
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.project_name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Station">
          <el-select
            v-model="selectedStationId"
            placeholder="Select Station"
            @change="loadStationConfig"
            filterable
            :disabled="!selectedProjectId"
          >
            <el-option
              v-for="station in stations"
              :key="station.id"
              :label="station.station_name"
              :value="station.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="config" class="config-card">
      <template #header>
        <div class="card-header">
          <span>{{ stationName }} - Modbus Config</span>
          <div>
            <el-button
              :type="listenerRunning ? 'danger' : 'success'"
              @click="toggleListener"
              :disabled="!websocket"
            >
              {{ listenerRunning ? 'Stop Listener' : 'Start Listener' }}
            </el-button>
            <el-button type="primary" @click="handleEdit">Edit</el-button>
            <el-button type="danger" @click="handleDelete">Delete</el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="Server Host">{{ config.server_host }}</el-descriptions-item>
        <el-descriptions-item label="Server Port">{{ config.server_port }}</el-descriptions-item>
        <el-descriptions-item label="Device ID">{{ config.device_id }}</el-descriptions-item>
        <el-descriptions-item label="Enabled">
          <el-tag :type="config.enabled ? 'success' : 'info'">
            {{ config.enabled ? 'Yes' : 'No' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Delay (s)">{{ config.delay_seconds }}</el-descriptions-item>
        <el-descriptions-item label="Simulation Mode">
          <el-tag :type="config.simulation_mode ? 'warning' : 'info'">
            {{ config.simulation_mode ? 'Yes' : 'No' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">Register Addresses</el-divider>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Ready Status">{{ config.ready_status_address }}</el-descriptions-item>
        <el-descriptions-item label="Read SN">{{ config.read_sn_address }}</el-descriptions-item>
        <el-descriptions-item label="Test Status">{{ config.test_status_address }}</el-descriptions-item>
        <el-descriptions-item label="Test Result">{{ config.test_result_address }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">Live Status</el-divider>
      <el-descriptions v-if="listenerStatus" :column="2" border>
        <el-descriptions-item label="Running">
          <el-tag :type="listenerStatus.running ? 'success' : 'info'">
            {{ listenerStatus.running ? 'Running' : 'Stopped' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Connected">
          <el-tag :type="listenerStatus.connected ? 'success' : 'danger'">
            {{ listenerStatus.connected ? 'Yes' : 'No' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Last SN">{{ listenerStatus.last_sn || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="Cycle Count">{{ listenerStatus.cycle_count || 0 }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card v-else-if="selectedStationId" class="no-config-card">
      <el-empty description="No Modbus configuration for this station">
        <el-button type="primary" @click="handleCreate">Create Configuration</el-button>
      </el-empty>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? 'Create Modbus Configuration' : 'Edit Modbus Configuration'"
      width="700px"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="200px">
        <el-divider content-position="left">Connection Settings</el-divider>

        <el-form-item label="Server Host" prop="server_host">
          <el-input v-model="formData.server_host" placeholder="127.0.0.1" />
        </el-form-item>

        <el-form-item label="Server Port" prop="server_port">
          <el-input-number v-model="formData.server_port" :min="1" :max="65535" />
        </el-form-item>

        <el-form-item label="Device ID" prop="device_id">
          <el-input-number v-model="formData.device_id" :min="1" :max="255" />
        </el-form-item>

        <el-form-item label="Enable Listener" prop="enabled">
          <el-switch v-model="formData.enabled" />
        </el-form-item>

        <el-form-item label="Polling Delay (s)" prop="delay_seconds">
          <el-input-number v-model="formData.delay_seconds" :min="0.1" :max="60" :step="0.1" />
        </el-form-item>

        <el-form-item label="Simulation Mode" prop="simulation_mode">
          <el-switch v-model="formData.simulation_mode" />
          <span class="form-tip">Enable for testing without real Modbus device</span>
        </el-form-item>

        <el-divider content-position="left">Register Addresses</el-divider>

        <el-form-item label="Ready Status Address" prop="ready_status_address">
          <el-input v-model="formData.ready_status_address" placeholder="0x0013" />
        </el-form-item>

        <el-form-item label="Read SN Address" prop="read_sn_address">
          <el-input v-model="formData.read_sn_address" placeholder="0x0064" />
        </el-form-item>

        <el-form-item label="Test Status Address" prop="test_status_address">
          <el-input v-model="formData.test_status_address" placeholder="0x0014" />
        </el-form-item>

        <el-form-item label="Test Result Address" prop="test_result_address">
          <el-input v-model="formData.test_result_address" placeholder="0x0015" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="handleSubmit">Submit</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { modbusApi } from '@/api/modbus'
import { useProjectStore } from '@/stores/project'
import AppNavBar from '@/components/AppNavBar.vue'

const projectStore = useProjectStore()

// State
const selectedProjectId = ref(null)
const selectedStationId = ref(null)
const projects = computed(() => projectStore.projects)
const stations = ref([])
const config = ref(null)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const formRef = ref(null)
const websocket = ref(null)
const listenerStatus = ref(null)
const listenerRunning = ref(false)

const stationName = computed(() => {
  const s = stations.value.find(s => s.id === selectedStationId.value)
  return s ? s.station_name : ''
})

const formData = reactive({
  server_host: '127.0.0.1',
  server_port: 502,
  device_id: 1,
  enabled: false,
  delay_seconds: 1.0,
  simulation_mode: false,
  ready_status_address: '0x0013',
  ready_status_length: 1,
  read_sn_address: '0x0064',
  read_sn_length: 11,
  test_status_address: '0x0014',
  test_status_length: 1,
  in_testing_value: '0x00',
  test_finished_value: '0x01',
  test_result_address: '0x0015',
  test_result_length: 1,
  test_no_result: '0x00',
  test_pass_value: '0x01',
  test_fail_value: '0x02'
})

const formRules = {
  server_host: [{ required: true, message: 'Please enter server host', trigger: 'blur' }],
  server_port: [{ required: true, message: 'Please enter server port', trigger: 'blur' }],
  device_id: [{ required: true, message: 'Please enter device ID', trigger: 'blur' }]
}

const handleProjectChange = async () => {
  selectedStationId.value = null
  config.value = null
  disconnectWebSocket()
  if (!selectedProjectId.value) return
  try {
    stations.value = await projectStore.fetchProjectStations(selectedProjectId.value)
  } catch (error) {
    ElMessage.error('Failed to load stations')
  }
}

const loadStationConfig = async () => {
  if (!selectedStationId.value) return

  disconnectWebSocket()

  try {
    config.value = await modbusApi.getStationConfig(selectedStationId.value)
    connectWebSocket()
  } catch (error) {
    if (error?.response?.status === 404) {
      config.value = null
    } else {
      ElMessage.error('Failed to load Modbus configuration')
    }
  }
}

const connectWebSocket = () => {
  websocket.value = modbusApi.connectWebSocket(selectedStationId.value)

  websocket.value.onopen = () => {
    websocket.value.send(JSON.stringify({ action: 'subscribe' }))
    websocket.value.send(JSON.stringify({ action: 'get_status' }))
  }

  websocket.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'status') {
      if (data.data) {
        // Unified status format from get_status / start / stop
        listenerStatus.value = data.data
        listenerRunning.value = data.data.running
      }
    } else if (data.type === 'sn_received') {
      ElMessage.success(`SN received: ${data.sn}`)
      // 即時更新 Last SN 顯示，不需等待下次 get_status
      if (listenerStatus.value) {
        listenerStatus.value.last_sn = data.sn
      }
    } else if (data.type === 'connected_change') {
      // 即時更新 Connected 顯示，TCP 連線狀態改變時觸發
      if (listenerStatus.value) {
        listenerStatus.value.connected = data.connected
      }
    } else if (data.type === 'cycle_update') {
      // 即時更新 Cycle Count，每次輪詢完成後觸發
      if (listenerStatus.value) {
        listenerStatus.value.cycle_count = data.cycle_count
      }
    } else if (data.type === 'error' && data.message) {
      ElMessage.error(data.message)
    }
  }

  websocket.value.onerror = () => {
    console.warn('Modbus WebSocket connection error')
  }
}

const disconnectWebSocket = () => {
  if (websocket.value) {
    websocket.value.close()
    websocket.value = null
  }
}

const toggleListener = () => {
  if (!websocket.value) return
  const action = listenerRunning.value ? 'stop' : 'start'
  websocket.value.send(JSON.stringify({ action }))
}

const handleCreate = () => {
  dialogMode.value = 'create'
  Object.assign(formData, {
    server_host: '127.0.0.1',
    server_port: 502,
    device_id: 1,
    enabled: false,
    delay_seconds: 1.0,
    simulation_mode: false,
    ready_status_address: '0x0013',
    read_sn_address: '0x0064',
    test_status_address: '0x0014',
    test_result_address: '0x0015'
  })
  dialogVisible.value = true
}

const handleEdit = () => {
  dialogMode.value = 'edit'
  Object.assign(formData, config.value)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()

  try {
    if (dialogMode.value === 'create') {
      await modbusApi.createConfig({ ...formData, station_id: selectedStationId.value })
      ElMessage.success('Modbus configuration created')
    } else {
      await modbusApi.updateConfig(config.value.id, formData)
      ElMessage.success('Modbus configuration updated')
    }
    dialogVisible.value = false
    loadStationConfig()
  } catch (error) {
    ElMessage.error('Failed to save configuration')
  }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      'This will delete the Modbus configuration. Continue?',
      'Warning',
      { confirmButtonText: 'OK', cancelButtonText: 'Cancel', type: 'warning' }
    )
    await modbusApi.deleteConfig(config.value.id)
    ElMessage.success('Configuration deleted')
    config.value = null
    disconnectWebSocket()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete configuration')
    }
  }
}

onMounted(() => {
  projectStore.fetchProjects()
})

onBeforeUnmount(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.modbus-config-container {
  padding: 20px;
}

.header-card,
.config-card,
.no-config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
