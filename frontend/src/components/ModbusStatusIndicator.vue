<template>
  <div class="modbus-status-indicator" @click="showDetail">
    <el-tooltip :content="tooltipContent" placement="bottom">
      <div class="status-dot" :class="statusClass"></div>
    </el-tooltip>

    <el-dialog v-model="dialogVisible" title="Modbus Connection Status" width="500px">
      <el-descriptions v-if="status" :column="1" border>
        <el-descriptions-item label="Status">
          <el-tag :type="status.running ? 'success' : 'info'">
            {{ status.running ? 'Running' : 'Stopped' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Connected">
          <el-tag :type="status.connected ? 'success' : 'danger'">
            {{ status.connected ? 'Yes' : 'No' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Last SN">{{ status.last_sn || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="Cycle Count">{{ status.cycle_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="Uptime">{{ formatUptime(status.uptime_seconds) }}</el-descriptions-item>
        <el-descriptions-item v-if="status.error_message" label="Error">
          <el-text type="danger">{{ status.error_message }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
      <el-empty v-else description="No Modbus listener active" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { modbusApi } from '@/api/modbus'

const props = defineProps({
  stationId: {
    type: Number,
    required: true
  }
})

const status = ref(null)
const dialogVisible = ref(false)
const websocket = ref(null)

const statusClass = computed(() => {
  if (!status.value) return 'unknown'
  if (status.value.error_message) return 'error'
  if (status.value.running && status.value.connected) return 'connected'
  if (status.value.running) return 'connecting'
  return 'disconnected'
})

const tooltipContent = computed(() => {
  if (!status.value) return 'Modbus: Unknown'
  if (status.value.error_message) return `Modbus: Error - ${status.value.error_message}`
  if (status.value.running && status.value.connected) return 'Modbus: Connected'
  if (status.value.running) return 'Modbus: Connecting...'
  return 'Modbus: Disconnected'
})

const formatUptime = (seconds) => {
  if (!seconds) return 'N/A'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  return `${hours}h ${minutes}m ${secs}s`
}

const showDetail = () => {
  dialogVisible.value = true
}

defineExpose({ showDetail })

onMounted(() => {
  websocket.value = modbusApi.connectWebSocket(props.stationId)

  websocket.value.onopen = () => {
    websocket.value.send(JSON.stringify({ action: 'get_status' }))
  }

  websocket.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'status' && data.data) {
      status.value = data.data
    }
  }

  websocket.value.onerror = () => {
    console.warn('Modbus status WebSocket error')
  }
})

onBeforeUnmount(() => {
  if (websocket.value) {
    websocket.value.close()
  }
})
</script>

<style scoped>
.modbus-status-indicator {
  display: inline-block;
  cursor: pointer;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.status-dot.connected {
  background-color: #67c23a;
  box-shadow: 0 0 8px #67c23a;
}

.status-dot.connecting {
  background-color: #e6a23c;
  animation: pulse 1.5s infinite;
}

.status-dot.disconnected {
  background-color: #909399;
}

.status-dot.error {
  background-color: #f56c6c;
  animation: blink 1s infinite;
}

.status-dot.unknown {
  background-color: #c0c4cc;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>
