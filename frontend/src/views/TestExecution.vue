<template>
  <div class="test-execution-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>測試執行</h2>
        </div>
      </template>

      <!-- Station Info -->
      <el-alert
        v-if="currentStation"
        :title="`當前站別: ${currentStation.station_code} - ${currentStation.station_name}`"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- Serial Number Input -->
      <el-card v-if="!currentSession" class="serial-input-card">
        <el-form :model="testForm" label-width="120px">
          <el-form-item label="產品序號">
            <el-input
              v-model="testForm.serialNumber"
              placeholder="請掃描或輸入產品序號"
              @keyup.enter="handleStartTest"
              :disabled="testing"
            >
              <template #append>
                <el-button
                  type="primary"
                  :loading="testing"
                  @click="handleStartTest"
                >
                  開始測試
                </el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- Test Progress -->
      <el-card v-if="currentSession" class="test-progress-card">
        <div class="progress-header">
          <h3>序號: {{ currentSession.serial_number }}</h3>
          <el-tag :type="statusTagType" size="large">{{ statusText }}</el-tag>
        </div>

        <el-divider />

        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="總項目" :value="testStatus.total_items || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="已完成" :value="testStatus.current_item || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="通過" :value="testStatus.pass_items || 0">
              <template #suffix>
                <span style="color: #67c23a">✓</span>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="失敗" :value="testStatus.fail_items || 0">
              <template #suffix>
                <span style="color: #f56c6c">✗</span>
              </template>
            </el-statistic>
          </el-col>
        </el-row>

        <el-divider />

        <el-progress
          :percentage="progressPercentage"
          :status="progressStatus"
          :stroke-width="20"
        />

        <div class="elapsed-time">
          已用時間: {{ formatElapsedTime(testStatus.elapsed_time_seconds) }}
        </div>
      </el-card>

      <!-- Test Results Table -->
      <el-card v-if="testResults.length > 0" class="results-card">
        <template #header>
          <h3>測試結果</h3>
        </template>

        <el-table
          :data="testResults"
          stripe
          :max-height="400"
          style="width: 100%"
        >
          <el-table-column prop="item_no" label="序號" width="80" />
          <el-table-column prop="item_name" label="測試項目" min-width="200" />
          <el-table-column label="測量值" width="150">
            <template #default="{ row }">
              {{ row.measured_value !== null ? row.measured_value : '-' }}
              {{ row.unit || '' }}
            </template>
          </el-table-column>
          <el-table-column label="限制值" width="180">
            <template #default="{ row }">
              <span v-if="row.lower_limit !== null || row.upper_limit !== null">
                {{ row.lower_limit ?? '-' }} ~ {{ row.upper_limit ?? '-' }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="結果" width="100">
            <template #default="{ row }">
              <el-tag :type="getResultTagType(row.result)">
                {{ row.result }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="execution_duration_ms" label="耗時(ms)" width="100" />
        </el-table>
      </el-card>

      <!-- Action Buttons -->
      <div v-if="currentSession && testStatus.status === 'RUNNING'" class="action-buttons">
        <el-button type="danger" @click="handleAbortTest">
          中止測試
        </el-button>
      </div>

      <div v-if="currentSession && testStatus.status === 'COMPLETED'" class="action-buttons">
        <el-button type="primary" @click="handleNewTest">
          開始新測試
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'
import {
  createTestSession,
  getTestSessionStatus,
  getSessionResults,
  completeTestSession,
  startTestExecution,
  stopTestExecution
} from '@/api/tests'

const projectStore = useProjectStore()
const currentStation = computed(() => projectStore.currentStation)

const testForm = reactive({
  serialNumber: ''
})

const requireBarcode = ref(true) // 控制是否需要輸入產品序號才能開始測試

const currentSession = ref(null)
const testStatus = ref({
  status: 'IDLE',
  current_item: 0,
  total_items: 0,
  pass_items: 0,
  fail_items: 0,
  elapsed_time_seconds: 0
})
const testResults = ref([])
const testing = ref(false)
let statusPollInterval = null

// Status display
const statusText = computed(() => {
  const statusMap = {
    'IDLE': '待機中',
    'RUNNING': '測試中',
    'COMPLETED': '已完成',
    'ABORTED': '已中止'
  }
  return statusMap[testStatus.value.status] || '未知'
})

const statusTagType = computed(() => {
  const typeMap = {
    'IDLE': 'info',
    'RUNNING': 'warning',
    'COMPLETED': 'success',
    'ABORTED': 'danger'
  }
  return typeMap[testStatus.value.status] || 'info'
})

const progressPercentage = computed(() => {
  if (!testStatus.value.total_items) return 0
  return Math.round((testStatus.value.current_item / testStatus.value.total_items) * 100)
})

const progressStatus = computed(() => {
  if (testStatus.value.status === 'COMPLETED') return 'success'
  if (testStatus.value.status === 'ABORTED') return 'exception'
  return undefined
})

// Format elapsed time
const formatElapsedTime = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

// Get result tag type
const getResultTagType = (result) => {
  const typeMap = {
    'PASS': 'success',
    'FAIL': 'danger',
    'SKIP': 'info',
    'ERROR': 'warning'
  }
  return typeMap[result] || 'info'
}

// Start test
const handleStartTest = async () => {
  if (requireBarcode.value && !testForm.serialNumber.trim()) {
    ElMessage.warning('請輸入產品序號')
    return
  }

  if (!currentStation.value) {
    ElMessage.warning('請先選擇站別')
    return
  }

  testing.value = true
  try {
    // Create test session
    const serialNumber = requireBarcode.value ? testForm.serialNumber.trim() : 'AUTO-' + Date.now()
    const session = await createTestSession({
      serial_number: serialNumber,
      station_id: currentStation.value.id
    })

    currentSession.value = session
    
    ElMessage.success('測試會話已創建')

    // Start test execution
    await startTestExecution(session.id)
    
    testStatus.value.status = 'RUNNING'
    ElMessage.success('測試已啟動')

    // Start polling status
    startStatusPolling()

  } catch (error) {
    console.error('Failed to start test:', error)
    ElMessage.error('開始測試失敗: ' + (error.message || '未知錯誤'))
    currentSession.value = null
  } finally {
    testing.value = false
  }
}

// Poll test status
const startStatusPolling = () => {
  if (statusPollInterval) {
    clearInterval(statusPollInterval)
  }

  statusPollInterval = setInterval(async () => {
    if (!currentSession.value) return

    try {
      const status = await getTestSessionStatus(currentSession.value.id)
      testStatus.value = status

      // Update results
      const results = await getSessionResults(currentSession.value.id)
      testResults.value = results

      // Stop polling if completed
      if (status.status === 'COMPLETED' || status.status === 'ABORTED') {
        stopStatusPolling()
      }
    } catch (error) {
      console.error('Failed to poll status:', error)
    }
  }, 1000) // Poll every second
}

const stopStatusPolling = () => {
  if (statusPollInterval) {
    clearInterval(statusPollInterval)
    statusPollInterval = null
  }
}

// Abort test
const handleAbortTest = async () => {
  if (!currentSession.value) return

  try {
    // Call stop API first
    await stopTestExecution(currentSession.value.id)
    
    testStatus.value.status = 'ABORTED'
    stopStatusPolling()
    ElMessage.warning('測試已中止')
  } catch (error) {
    console.error('Failed to abort test:', error)
    ElMessage.error('中止測試失敗: ' + (error.message || '未知錯誤'))
  }
}

// Start new test
const handleNewTest = () => {
  currentSession.value = null
  testStatus.value = {
    status: 'IDLE',
    current_item: 0,
    total_items: 0,
    pass_items: 0,
    fail_items: 0,
    elapsed_time_seconds: 0
  }
  testResults.value = []
  testForm.serialNumber = ''
}

onMounted(() => {
  // Check if there's an active session to resume
})

onUnmounted(() => {
  stopStatusPolling()
})
</script>

<style scoped>
.test-execution-container {
  padding: 20px;
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

.serial-input-card {
  margin-bottom: 20px;
}

.test-progress-card {
  margin-bottom: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-header h3 {
  margin: 0;
}

.elapsed-time {
  margin-top: 16px;
  text-align: center;
  font-size: 16px;
  color: #606266;
}

.results-card {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
}
</style>
