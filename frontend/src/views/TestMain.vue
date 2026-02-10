<template>
  <div class="test-main-container">
    <!-- Top Info Bar -->
    <el-card class="info-card" shadow="never">
      <el-row :gutter="20" align="middle">
        <!-- 原有程式碼: 只顯示專案和站別的資訊 -->
        <!-- 修改: 增加專案和站別選擇器,允許使用者切換不同的專案和站別 -->
        <el-col :span="6">
          <el-form-item label="專案:" label-width="60px" style="margin-bottom: 0">
            <el-select
              v-model="selectedProjectId"
              placeholder="選擇專案"
              style="width: 160px"
              filterable
              clearable
              size="small"
              @change="handleProjectChange"
            >
              <el-option
                v-for="project in projectStore.projects"
                :key="project.id"
                :label="`${project.project_code} - ${project.project_name}`"
                :value="project.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="站別:" label-width="60px" style="margin-bottom: 0">
            <el-select
              v-model="selectedStationId"
              placeholder="選擇站別"
              style="width: 160px"
              filterable
              clearable
              size="small"
              :disabled="!selectedProjectId"
              @change="handleStationChange"
            >
              <el-option
                v-for="station in filteredStations"
                :key="station.id"
                :label="`${station.station_code} - ${station.station_name}`"
                :value="station.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="4">
          <div class="info-item">
            <span class="info-label">使用者:</span>
            <span class="info-value">{{ currentUser?.username || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="info-item">
            <span class="info-label">版本:</span>
            <span class="info-value">v1.0.0</span>
          </div>
        </el-col>
        <el-col :span="4" style="text-align: right">
          <el-button type="danger" @click="handleLogout">
            登出
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Configuration Panel -->
    <el-card class="config-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <el-button 
            type="primary" 
            size="large"
            @click="showSFCConfig = true"
            style="width: 100%"
          >
            SFC 設定
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-checkbox 
            v-model="sfcEnabled" 
            size="large"
            @change="handleSFCToggle"
          >
            啟用 SFC
          </el-checkbox>
          <el-checkbox 
            v-model="runAllTests" 
            size="large"
            style="margin-left: 20px"
          >
            全測模式
          </el-checkbox>
        </el-col>
        <el-col :span="4">
          <div class="loop-counter">
            <span class="loop-label">Loop:</span>
            <div class="loop-display">{{ loopCount }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <!-- 新增: 測試計劃名稱選擇器 -->
          <el-select
            v-model="selectedTestPlanName"
            placeholder="選擇測試計劃"
            size="large"
            style="width: 100%"
            clearable
            @change="handleTestPlanChange"
          >
            <el-option
              v-for="planName in testPlanNames"
              :key="planName"
              :label="planName"
              :value="planName"
            />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- Main Content -->
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- Left Panel: Test Plan Table -->
      <el-col :span="16">
        <el-card class="test-plan-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>測試計劃</h3>
              <el-tag v-if="testPlanItems.length > 0" type="info">
                共 {{ testPlanItems.length }} 項
              </el-tag>
            </div>
          </template>
          
          <el-table
            :data="testPlanItems"
            :height="400"
            stripe
            highlight-current-row
            :row-class-name="getRowClassName"
          >
            <el-table-column prop="item_no" label="序號" width="70" align="center" />
            <el-table-column prop="item_name" label="測試項目" min-width="150" />
            <!-- 新增: 項目鍵值欄位 - 顯示測試計劃中的唯一識別碼 -->
            <el-table-column prop="item_key" label="項目鍵值" width="100" align="center" />
            <!-- 新增: 限制類型欄位 - 顯示驗證邏輯 (lower/upper/both/equality/inequality/partial/none) -->
            <el-table-column prop="limit_type" label="限制類型" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.limit_type" size="small" type="info">
                  {{ row.limit_type }}
                </el-tag>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <!-- 新增: 限制值欄位 - 顯示上下限值的組合 -->
            <el-table-column label="限制值" width="150" align="center">
              <template #default="{ row }">
                <span v-if="row.lower_limit !== null || row.upper_limit !== null">
                  <span v-if="row.lower_limit !== null">{{ formatNumber(row.lower_limit) }}</span>
                  <span v-if="row.lower_limit !== null && row.upper_limit !== null"> ~ </span>
                  <span v-if="row.upper_limit !== null">{{ formatNumber(row.upper_limit) }}</span>
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <!-- 原有程式碼: 顯示 execute_name 作為測試指令 -->
            <!-- 說明: execute_name 在測試執行時被轉換為 measurement_type,保留顯示以便使用者了解測試類型 -->
            <el-table-column prop="execute_name" label="測試指令" width="120" show-overflow-tooltip />
            <el-table-column label="下限" width="90" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.lower_limit) }}
              </template>
            </el-table-column>
            <el-table-column label="上限" width="90" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.upper_limit) }}
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="單位" width="70" align="center" />

            <!-- 新增: 執行狀態欄位 -->
            <el-table-column label="執行" width="60" align="center">
              <template #default="{ row }">
                <el-icon v-if="row.executed" color="#67C23A" :size="18">
                  <CircleCheck />
                </el-icon>
                <el-icon v-else color="#DCDFE6" :size="18">
                  <CircleClose />
                </el-icon>
              </template>
            </el-table-column>

            <!-- 修改: 測試結果欄位（使用 passed 狀態） -->
            <el-table-column label="結果" width="80" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.passed === true" type="success" size="small">PASS</el-tag>
                <el-tag v-else-if="row.passed === false" type="danger" size="small">FAIL</el-tag>
                <el-tag v-else-if="row.status" :type="getStatusTagType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>

            <!-- 修改: 測量值欄位（顯示 value，並根據 passed 狀態標色） -->
            <el-table-column label="測量值" width="110" align="right">
              <template #default="{ row }">
                <span
                  v-if="row.value !== null && row.value !== undefined"
                  :class="getTestPointValueClass(row)"
                  :style="getTestPointValueStyle(row)"
                >
                  {{ formatNumber(row.value) }}
                </span>
                <span v-else-if="row.measured_value !== null" :class="getValueClass(row)">
                  {{ formatNumber(row.measured_value) }}
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- Right Panel: Control & Status -->
      <el-col :span="8">
        <!-- Barcode Input & Control -->
        <el-card class="control-card" shadow="hover">
          <template #header>
            <h3>測試控制</h3>
          </template>
          
          <div class="barcode-section">
            <el-input
              v-model="barcode"
              placeholder="請掃描或輸入產品序號"
              size="large"
              :disabled="testing"
              @keyup.enter="handleStartTest"
              clearable
            >
              <template #prepend>
                <el-icon><Document /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="control-buttons">
            <el-button
              type="success"
              size="large"
              :loading="testing"
              :disabled="(requireBarcode && !barcode) || testing"
              @click="handleStartTest"
              style="width: 100%"
            >
              <el-icon v-if="!testing"><VideoPlay /></el-icon>
              {{ testing ? '測試進行中...' : '開始測試' }}
            </el-button>
            
            <el-button
              v-if="testing"
              type="danger"
              size="large"
              @click="handleStopTest"
              style="width: 100%; margin-top: 10px"
            >
              <el-icon><VideoPause /></el-icon>
              停止測試
            </el-button>
          </div>

          <!-- Test Progress -->
          <div v-if="currentSession" class="progress-section">
            <el-divider />
            <div class="progress-info">
              <div class="progress-item">
                <span class="progress-label">進度:</span>
                <span class="progress-value">
                  {{ testStatus.current_item || 0 }} / {{ testStatus.total_items || 0 }}
                </span>
              </div>
              <div class="progress-item">
                <span class="progress-label">通過:</span>
                <span class="progress-value success">{{ testStatus.pass_items || 0 }}</span>
              </div>
              <div class="progress-item">
                <span class="progress-label">失敗:</span>
                <span class="progress-value fail">{{ testStatus.fail_items || 0 }}</span>
              </div>
              <div class="progress-item">
                <span class="progress-label">時間:</span>
                <span class="progress-value">{{ formatElapsedTime(testStatus.elapsed_time_seconds) }}</span>
              </div>
            </div>
            <el-progress
              :percentage="progressPercentage"
              :status="progressStatus"
              :stroke-width="15"
              style="margin-top: 10px"
            />
          </div>

          <!-- Test Result Display -->
          <div v-if="testCompleted" class="result-display">
            <el-divider />
            <div :class="['result-banner', finalResult.toLowerCase()]">
              <el-icon v-if="finalResult === 'PASS'" class="result-icon"><CircleCheck /></el-icon>
              <el-icon v-else class="result-icon"><CircleClose /></el-icon>
              <span class="result-text">{{ finalResult }}</span>
            </div>
          </div>
        </el-card>

        <!-- Status Display -->
        <el-card class="status-card" shadow="hover" style="margin-top: 20px">
          <template #header>
            <h3>系統狀態</h3>
          </template>
          
          <div class="status-content">
            <el-scrollbar height="200px">
              <div
                v-for="(msg, index) in statusMessages"
                :key="index"
                :class="['status-message', msg.type]"
              >
                <span class="status-time">{{ msg.time }}</span>
                <span class="status-text">{{ msg.text }}</span>
              </div>
            </el-scrollbar>
          </div>
        </el-card>

        <!-- Error Display -->
        <el-card v-if="errorCode" class="error-card" shadow="hover" style="margin-top: 20px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <h3>錯誤訊息</h3>
              <el-button size="small" @click="errorCode = ''">清除</el-button>
            </div>
          </template>
          <div class="error-content">
            {{ errorCode }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- SFC Configuration Dialog -->
    <el-dialog
      v-model="showSFCConfig"
      title="SFC 配置"
      width="600px"
    >
      <el-form :model="sfcConfig" label-width="120px">
        <el-form-item label="SFC 路徑">
          <el-input v-model="sfcConfig.path" />
        </el-form-item>
        <el-form-item label="站點 ID">
          <el-input v-model="sfcConfig.stationID" />
        </el-form-item>
        <el-form-item label="線路名稱">
          <el-input v-model="sfcConfig.lineName" />
        </el-form-item>
        <el-form-item label="治具 ID">
          <el-input v-model="sfcConfig.fixtureID" />
        </el-form-item>
        <el-form-item label="資料庫">
          <el-input v-model="sfcConfig.database" />
        </el-form-item>
        <el-form-item label="日誌路徑">
          <el-input v-model="sfcConfig.logPath" />
        </el-form-item>
        <el-form-item label="Loop 測試">
          <el-switch v-model="sfcConfig.loopEnabled" />
          <el-input-number
            v-if="sfcConfig.loopEnabled"
            v-model="sfcConfig.loopCount"
            :min="1"
            :max="9999"
            style="margin-left: 10px"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSFCConfig = false">取消</el-button>
        <el-button type="primary" @click="saveSFCConfig">儲存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, 
  VideoPlay, 
  VideoPause, 
  CircleCheck, 
  CircleClose 
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
// 原有程式碼: 導入測試相關 API
// 修改: 新增 createTestResult 和 completeTestSession API，用於保存測試結果到資料庫
import {
  createTestSession,
  startTestExecution,
  stopTestExecution,
  getTestSessionStatus,
  getSessionResults,
  executeSingleMeasurement,
  resetInstrument,
  createTestResult,
  completeTestSession
} from '@/api/tests'
import { getStationTestPlan, getStationTestPlanNames, getStationTestPlanMap } from '@/api/testplans'

const router = useRouter()
const authStore = useAuthStore()
const projectStore = useProjectStore()

// 原有程式碼: 使用 store 中的 currentProject 和 currentStation
// 修改: 使用本地狀態管理選擇的專案和站別,允許動態切換
const selectedProjectId = ref(null)
const selectedStationId = ref(null)

const currentUser = computed(() => authStore.user)
const currentProject = computed(() => {
  if (!selectedProjectId.value) return null
  return projectStore.projects.find(p => p.id === selectedProjectId.value) || null
})
const currentStation = computed(() => {
  if (!selectedStationId.value) return null
  return filteredStations.value.find(s => s.id === selectedStationId.value) || null
})

// 根據選擇的專案過濾站別
const filteredStations = computed(() => {
  if (!selectedProjectId.value) return []
  return projectStore.stations.filter(station => station.project_id === selectedProjectId.value)
})

// Configuration
const sfcEnabled = ref(false)
const runAllTests = ref(true)
const loopCount = ref(0)
const showSFCConfig = ref(false)
const requireBarcode = ref(false) // 控制是否需要輸入產品序號才能開始測試
const sfcConfig = reactive({
  path: '',
  stationID: '',
  lineName: '',
  fixtureID: '',
  database: '',
  logPath: '',
  loopEnabled: false,
  loopCount: 1
})

// Test plan
// 移除測試計劃列表相關變數，因為系統架構中沒有獨立的測試計劃實體
// const testPlans = ref([])
// const selectedTestPlan = ref(null)
// 新增: 測試計劃名稱列表和選擇的測試計劃名稱
const testPlanNames = ref([])
const selectedTestPlanName = ref(null)
const testPlanItems = ref([])

// 新增: 測試點映射表（TestPointMap）- 對應 PDTool4 test_point_map.py
const testPointMap = ref(null) // TestPlanMap 完整資料
const testPointsById = ref({})  // 快速查找用：{ unique_id: testPoint }

// Test control
const barcode = ref('')
const testing = ref(false)
const testCompleted = ref(false)
const currentSession = ref(null)
const testStatus = ref({
  status: 'IDLE',
  current_item: 0,
  total_items: 0,
  pass_items: 0,
  fail_items: 0,
  elapsed_time_seconds: 0
})
const finalResult = ref('')

// Status messages
const statusMessages = ref([])
const errorCode = ref('')

// Measurement execution tracking (PDTool4 style)
const testResults = ref({}) // 蒐集各測項測量值 {'ID':'value','ID2':'value2',....}
const usedInstruments = ref({}) // 蒐集有使用的儀器 {'儀器位置':'儀器類型'}

// Polling
let statusPollInterval = null

// Computed
const progressPercentage = computed(() => {
  if (!testStatus.value.total_items) return 0
  return Math.round((testStatus.value.current_item / testStatus.value.total_items) * 100)
})

const progressStatus = computed(() => {
  if (testStatus.value.status === 'COMPLETED') {
    return finalResult.value === 'PASS' ? 'success' : 'exception'
  }
  if (testStatus.value.status === 'ABORTED') return 'exception'
  return undefined
})

// Methods
// 原有程式碼: formatNumber 直接使用 Number(value).toFixed(3)
// 修改: 支援字串類型的測量值 (例如: "Hello World!")
const formatNumber = (value) => {
  if (value === null || value === undefined) return '-'

  // 如果是字串類型，直接返回
  if (typeof value === 'string') {
    return value
  }

  // 如果是數字類型，格式化為3位小數
  const num = Number(value)
  if (!isNaN(num)) {
    return num.toFixed(3)
  }

  // 其他情況返回原始值
  return value
}

// 原有程式碼: formatElapsedTime 只顯示整數秒
// 修改: 支援小數點第3位顯示，格式為 MM:SS.sss
const formatElapsedTime = (seconds) => {
  if (!seconds && seconds !== 0) return '00:00.000'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  // 秒數顯示到小數點第3位
  const secsFormatted = typeof secs === 'number' ? secs.toFixed(3) : '0.000'
  return `${String(mins).padStart(2, '0')}:${String(parseFloat(secsFormatted)).padStart(6, '0')}`
}

const getStatusTagType = (status) => {
  const typeMap = {
    'PASS': 'success',
    'FAIL': 'danger',
    'SKIP': 'info',
    'ERROR': 'warning'
  }
  return typeMap[status] || 'info'
}

const getRowClassName = ({ row }) => {
  // 優先使用測試點狀態（passed）
  if (row.passed === true) return 'row-pass'
  if (row.passed === false) return 'row-fail'

  // 回退到原有 status 欄位
  if (row.status === 'PASS') return 'row-pass'
  if (row.status === 'FAIL') return 'row-fail'
  if (row.status === 'ERROR') return 'row-error'

  // 執行中的項目（executed 但尚未完成）
  if (row.executed && row.passed === null) return 'row-executing'

  return ''
}

const getValueClass = (row) => {
  if (row.status === 'PASS') return 'value-pass'
  if (row.status === 'FAIL') return 'value-fail'
  return ''
}

// 新增: 測試點測量值樣式（基於 passed 狀態）
const getTestPointValueClass = (row) => {
  if (row.passed === true) return 'test-point-value-pass'
  if (row.passed === false) return 'test-point-value-fail'
  return ''
}

// 新增: 測試點測量值內聯樣式
const getTestPointValueStyle = (row) => {
  if (row.passed === true) {
    return { color: '#67C23A', fontWeight: '600' }
  }
  if (row.passed === false) {
    return { color: '#F56C6C', fontWeight: '600' }
  }
  return {}
}

const addStatusMessage = (text, type = 'info') => {
  const time = new Date().toLocaleTimeString()
  statusMessages.value.unshift({ time, text, type })
  if (statusMessages.value.length > 100) {
    statusMessages.value.pop()
  }
}

// 新增: 載入測試計劃名稱列表
const loadTestPlanNames = async () => {
  if (!currentStation.value) {
    return
  }

  try {
    // 原有程式碼缺少 project_id 參數,導致後端 API 報錯,需傳遞 currentProject.value.id
    const names = await getStationTestPlanNames(currentStation.value.id, currentProject.value.id)
    testPlanNames.value = names

    // 從 localStorage 讀取上次選擇的測試計劃名稱
    const lastSelectedPlanName = localStorage.getItem(`lastTestPlanName_station_${currentStation.value.id}`)
    if (lastSelectedPlanName && names.includes(lastSelectedPlanName)) {
      selectedTestPlanName.value = lastSelectedPlanName
    } else if (names.length === 1) {
      // 如果只有一個測試計劃，自動選擇
      selectedTestPlanName.value = names[0]
    }
  } catch (error) {
    console.error('Failed to load test plan names:', error)
    addStatusMessage('載入測試計劃名稱失敗: ' + error.message, 'error')
  }
}

// 新增: 載入 TestPlanMap（包含測試點狀態資訊）
const loadTestPlanMap = async () => {
  if (!currentStation.value || !currentProject.value) {
    addStatusMessage('請先選擇專案和站別', 'warning')
    return
  }

  try {
    addStatusMessage('載入測試點映射表...', 'info')
    const response = await getStationTestPlanMap(
      currentStation.value.id,
      currentProject.value.id,
      true,
      selectedTestPlanName.value
    )

    testPointMap.value = response

    // 建立快速查找索引
    testPointsById.value = {}
    response.test_points.forEach(tp => {
      testPointsById.value[tp.unique_id] = tp
    })

    if (selectedTestPlanName.value) {
      addStatusMessage(`已載入測試點映射表「${selectedTestPlanName.value}」: ${response.total_test_points} 個測試點`, 'success')
    } else {
      addStatusMessage(`已載入 ${response.total_test_points} 個測試點`, 'success')
    }
  } catch (error) {
    console.error('Failed to load test plan map:', error)
    addStatusMessage('載入測試點映射表失敗: ' + error.message, 'error')
  }
}

// 直接載入當前站別的測試項目
const loadTestPlanItems = async () => {
  if (!currentStation.value) {
    addStatusMessage('請先選擇站別', 'warning')
    return
  }

  try {
    addStatusMessage('載入測試計劃...', 'info')
    // 原有程式碼缺少 project_id 參數,導致後端 API 報錯,需傳遞 currentProject.value.id
    // 新增: 傳遞選擇的測試計劃名稱
    const items = await getStationTestPlan(currentStation.value.id, currentProject.value.id, true, selectedTestPlanName.value)

    // 新增: 合併測試點狀態資訊到測試計劃項目
    testPlanItems.value = items.map(item => {
      const testPoint = testPointsById.value[item.item_name]
      return {
        ...item,
        // 原有欄位
        status: null,
        measured_value: null,
        // 新增: 測試點狀態欄位
        unique_id: item.item_name,
        executed: testPoint?.executed || false,
        passed: testPoint?.passed || null,
        value: testPoint?.value || null,
        // 修改: 優先使用後端返回的 limit_type 和 item_key，若無則使用測試點映射表
        limit_type: item.limit_type || testPoint?.limit_type || null,
        value_type: item.value_type || testPoint?.value_type || null,
        item_key: item.item_key || null
      }
    })
    testStatus.value.total_items = items.length

    if (selectedTestPlanName.value) {
      addStatusMessage(`已載入測試計劃「${selectedTestPlanName.value}」: ${items.length} 個測試項目`, 'success')
    } else {
      addStatusMessage(`已載入 ${items.length} 個測試項目`, 'success')
    }
  } catch (error) {
    console.error('Failed to load test plan:', error)
    addStatusMessage('載入測試計劃失敗: ' + error.message, 'error')
    ElMessage.error('載入測試計劃失敗')
  }
}

// 新增: 當測試計劃改變時，保存選擇並重新載入
const handleTestPlanChange = async () => {
  if (selectedTestPlanName.value && currentStation.value) {
    // 保存到 localStorage
    localStorage.setItem(`lastTestPlanName_station_${currentStation.value.id}`, selectedTestPlanName.value)
    addStatusMessage(`已切換測試計劃: ${selectedTestPlanName.value}`, 'info')
  } else if (currentStation.value) {
    // 清除選擇時移除 localStorage
    localStorage.removeItem(`lastTestPlanName_station_${currentStation.value.id}`)
    addStatusMessage('已清除測試計劃選擇', 'info')
  }

  // 先載入 TestPlanMap，再載入測試計劃項目
  await loadTestPlanMap()
  await loadTestPlanItems()
}

// 新增: 執行量測功能 (參考 PDTool4 oneCSV_atlas_2.py)
// 整合 runAllTest 模式 - 遇到錯誤時記錄但繼續執行
// 整合 Loop 測試模式 - 根據 loopCount 循環執行測試
const executeMeasurements = async () => {
  // 原有程式碼: 測試完成後沒有計算經過時間
  // 修改: 記錄測試開始時間，用於計算經過時間
  const startTime = Date.now()

  // 原有程式碼: 沒有實現 Loop 測試功能
  // 修改: 根據 sfcConfig.loopEnabled 和 sfcConfig.loopCount 來執行循環測試
  const loopEnabled = sfcConfig.loopEnabled
  const totalLoops = loopEnabled ? sfcConfig.loopCount : 1

  try {
    addStatusMessage('開始執行測試項目...', 'info')
    if (runAllTests.value) {
      addStatusMessage('PDTool4 runAllTest 模式: 已啟用 - 將在錯誤時繼續執行', 'info')
    }
    if (loopEnabled) {
      addStatusMessage(`Loop 測試模式: 已啟用 - 將執行 ${totalLoops} 次循環`, 'info')
    }

    // 原有程式碼: passCount, failCount, errorCount, errorItems 在循環內部定義
    // 修改: 將這些變數移到循環外部,以便在循環結束後仍能存取
    let passCount = 0
    let failCount = 0
    let errorCount = 0
    const errorItems = [] // PDTool4 runAllTest: 收集錯誤項目

    // 外層循環: 處理 Loop 測試
    for (let currentLoop = 0; currentLoop < totalLoops; currentLoop++) {
      // 如果是循環測試,顯示當前循環次數
      if (loopEnabled) {
        addStatusMessage(`========== Loop ${currentLoop + 1}/${totalLoops} ==========`, 'info')
        loopCount.value = currentLoop + 1
      }

      // Reset tracking variables for each loop
      testResults.value = {}
      usedInstruments.value = {}

      // 原有程式碼: 每次循環都重新定義 passCount, failCount, errorCount, errorItems
      // 修改: 每次循環重置這些變數的值,而不是重新定義
      passCount = 0
      failCount = 0
      errorCount = 0
      errorItems.length = 0 // 清空陣列

      // Reset test plan items status for each loop
      testPlanItems.value.forEach(item => {
        item.status = null
        item.measured_value = null
      })

      // Execute each test item sequentially (參考 oneCSV_atlas_2.py:131-191)
      for (let index = 0; index < testPlanItems.value.length; index++) {
        const item = testPlanItems.value[index]

        // Update current item status
        testStatus.value.current_item = index + 1

        // 原有程式碼: 時間只在最後計算一次，測試過程中沒有更新
        // 修改: 每次執行測項時更新經過時間（精確到毫秒），讓時間即時顯示
        testStatus.value.elapsed_time_seconds = (Date.now() - startTime) / 1000

        // Check if should stop
        if (!testing.value) {
          addStatusMessage('測試已中止', 'warning')
          break
        }

        try {
          // Execute single measurement
          const result = await executeSingleItem(item, index)

          // Update item with result
          item.status = result.result
          item.measured_value = result.measured_value

          // 新增: 更新測試點狀態（對應 PDTool4 TestPoint.execute()）
          item.executed = true
          item.value = result.measured_value
          if (result.result === 'PASS') {
            item.passed = true
          } else if (result.result === 'FAIL') {
            item.passed = false
          } else {
            item.passed = null // ERROR 狀態視為未通過但不標記為失敗
          }

          // 原有程式碼: errorCode 只在測試開始時清除,導致之前的錯誤訊息一直顯示
          // 修改: 如果當前項目執行成功,且 errorCode 包含當前項目的錯誤,則清除 errorCode
          // 這樣可以確保只有最新的錯誤會顯示,且成功的項目不會保留錯誤狀態
          if (result.result === 'PASS') {
            passCount++
            // 清除當前項目的錯誤訊息 (如果存在)
            if (errorCode.value && errorCode.value.includes(item.item_name)) {
              errorCode.value = ''
            }
          } else if (result.result === 'FAIL') {
            failCount++

            // PDTool4 runAllTest: 記錄失敗但繼續
            if (!runAllTests.value) {
              addStatusMessage(`測試失敗於項目 ${item.item_name}，停止執行`, 'error')
              break
            } else {
              addStatusMessage(`[runAllTest] 項目 ${item.item_name} 失敗 - 繼續執行`, 'warning')
            }
          } else if (result.result === 'ERROR') {
            errorCount++
            errorItems.push({
              item_no: item.item_no,
              item_name: item.item_name,
              error: result.error_message
            })

            // PDTool4 runAllTest: 記錄錯誤但繼續
            if (!runAllTests.value) {
              addStatusMessage(`測試錯誤於項目 ${item.item_name}，停止執行`, 'error')
              break
            } else {
              addStatusMessage(`[runAllTest] 項目 ${item.item_name} 錯誤 - 繼續執行`, 'warning')
            }
          }

          // Update test status
          testStatus.value.pass_items = passCount
          testStatus.value.fail_items = failCount

          // Store result for dependency usage (UseResult機制)
          // 原有程式碼: 只用 item_no 作為 key
          // 修正: 同時用 item_no 和 item_name 作為 key，因為 use_result 欄位可能使用任一種
          // 例如: use_result="123_1" (item_name) 或 use_result="2" (item_no)
          if (result.measured_value !== null) {
            const measuredValueStr = String(result.measured_value)
            testResults.value[item.item_no] = measuredValueStr        // 用序號作為 key
            testResults.value[item.item_name] = measuredValueStr      // 用名稱作為 key
          }

          addStatusMessage(`項目 ${item.item_no}: ${item.item_name} - ${result.result}`,
                          result.result === 'PASS' ? 'success' : 'error')

        } catch (error) {
          console.error(`Failed to execute item ${item.item_no}:`, error)
          item.status = 'ERROR'
          item.measured_value = null
          errorCount++
          errorItems.push({
            item_no: item.item_no,
            item_name: item.item_name,
            error: error.message
          })

          testStatus.value.fail_items = failCount + errorCount

          addStatusMessage(`項目 ${item.item_no} 執行錯誤: ${error.message}`, 'error')

          // 原有程式碼: errorCode 直接被覆蓋,導致只顯示最後一個錯誤
          // 修改: 使用格式化的錯誤訊息,包含項目名稱,方便識別錯誤來源
          errorCode.value = `[${item.item_no}] ${item.item_name}: ${error.message}`

          // PDTool4 runAllTest: 遇到異常也繼續
          if (!runAllTests.value) {
            break
          } else {
            addStatusMessage(`[runAllTest] 項目 ${item.item_no} 異常 - 繼續執行`, 'warning')
          }
        }
      }

      // 如果測試被中止,跳出循環
      if (!testing.value) {
        break
      }

      // 如果不是循環模式,完成一次後就跳出
      if (!loopEnabled) {
        break
      }

      // PDTool4 runAllTest: 顯示當前循環的錯誤摘要
      if (runAllTests.value && errorItems.length > 0) {
        addStatusMessage(`[Loop ${currentLoop + 1}] 完成，但有 ${errorItems.length} 個錯誤項目`, 'warning')
      }

      // 循環測試模式: 在每次循環結束後顯示結果
      if (currentLoop < totalLoops - 1) {
        addStatusMessage(`Loop ${currentLoop + 1} 完成，準備進行下一次循環...`, 'info')
        // 可選: 在循環之間添加延遲
        // await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }

    // Cleanup instruments (參考 oneCSV_atlas_2.py:244-265)
    await cleanupInstruments()

    // Update final status - 檢查是否有任何 ERROR 或 FAIL 狀態的項目
    // 注意: 這裡檢查的是最後一次循環的結果
    const hasError = testPlanItems.value.some(item => item.status === 'ERROR')
    const hasFail = testPlanItems.value.some(item => item.status === 'FAIL')

    // 原有程式碼: PDTool4 runAllTest: 顯示錯誤摘要 (只在非循環模式下顯示)
    // 修改: 支援循環測試模式,顯示最終一次循環的錯誤摘要
    // 注意: errorItems 現在定義在循環外部,包含最後一次循環的錯誤
    if (runAllTests.value && errorItems.length > 0) {
      const loopInfo = loopEnabled ? ` (最後一次循環)` : ''
      addStatusMessage(`測試完成${loopInfo}，有 ${errorItems.length} 個錯誤項目:`, 'warning')
      errorItems.slice(0, 5).forEach(err => {
        addStatusMessage(`  - ${err.item_no}: ${err.item_name}: ${err.error}`, 'warning')
      })
      if (errorItems.length > 5) {
        addStatusMessage(`  ... 還有 ${errorItems.length - 5} 個錯誤未顯示`, 'warning')
      }
    }

    // 最終結果判定
    // 原有程式碼: 測試完成後沒有更新 elapsed_time_seconds
    // 修改: 計算並更新經過時間（精確到毫秒）
    const elapsedSeconds = (Date.now() - startTime) / 1000
    testStatus.value.elapsed_time_seconds = elapsedSeconds

    if (hasError || hasFail) {
      testStatus.value.status = 'COMPLETED'
      finalResult.value = 'FAIL'
    } else {
      testStatus.value.status = 'COMPLETED'
      finalResult.value = 'PASS'
    }

    // 新增: 方案 A - 完成測試 session
    // 調用 completeTestSession API，更新 session 的結束時間、最終結果和統計數據
    if (currentSession.value) {
      try {
        await completeTestSession(currentSession.value.id, {
          final_result: finalResult.value,
          total_items: testPlanItems.value.length,
          pass_items: passCount,
          fail_items: failCount + errorCount,  // 錯誤視為失敗
          test_duration_seconds: Math.round(elapsedSeconds)
        })
        addStatusMessage('測試 session 已完成並保存', 'success')
      } catch (completeError) {
        console.error('Failed to complete test session:', completeError)
        addStatusMessage(`完成 session 失敗: ${completeError.message}`, 'warning')
        // 不影響測試流程，只記錄錯誤
      }
    }

    testCompleted.value = true

    // 原有程式碼: 只顯示一次測試的結果
    // 修改: 支援循環測試模式,顯示循環次數
    // 注意: passCount, failCount, errorCount 現在定義在循環外部,包含最後一次循環的統計
    const loopText = loopEnabled ? ` (共 ${totalLoops} 次循環)` : ''
    addStatusMessage(
      `測試完成: ${finalResult.value}${loopText} (通過: ${passCount}, 失敗: ${failCount}, 錯誤: ${errorCount})`,
      finalResult.value === 'PASS' ? 'success' : 'error'
    )

  } catch (error) {
    console.error('Failed to execute measurements:', error)
    addStatusMessage('執行測試時發生錯誤: ' + error.message, 'error')
    errorCode.value = '執行測試時發生錯誤: ' + error.message
    testStatus.value.status = 'ERROR'
  } finally {
    testing.value = false
    stopStatusPolling()
  }
}

// 新增: 執行單一測試項目 (參考 oneCSV_atlas_2.py 的量測分發邏輯)
const executeSingleItem = async (item, index) => {
  try {
    // Parse test parameters from CSV columns
    const testParams = {}

    // 原有程式碼: 優先使用 case_type
    // 修正方案 A: 優先使用 switch_mode,向後相容 case_type
    const switchMode = item.switch_mode || item.case_type || item.case || item.item_name

    // Extract parameters based on ExecuteName
    const executeName = item.execute_name // ExecuteName 是測量類型 (measurement_type)

    // Build test parameters (參考 oneCSV_atlas_2.py:134-155)
    // 這裡需要根據實際的 CSV 欄位來構建參數
    // 簡化版本：將所有額外欄位作為參數傳遞
    // 重要: 排除不應該傳給 backend 的欄位，其他欄位都傳遞
    Object.keys(item).forEach(key => {
      if (!['item_no', 'item_name', 'execute_name', 'lower_limit', 'upper_limit',
            'unit', 'status', 'measured_value', 'id', 'project_id', 'station_id',
            'test_plan_name', 'item_key', 'sequence_order', 'enabled', 'pass_or_fail',
            'measure_value', 'created_at', 'updated_at', 'parameters'].includes(key)) {
        if (item[key] && item[key] !== '') {
          testParams[key] = item[key]
        }
      }
    })

    // 新增: 日誌輸出 item 欄位和 testParams 內容
    console.log('[DEBUG] ============================================')
    console.log('[DEBUG] 項目:', item.item_name)
    console.log('[DEBUG] item 欄位:', Object.keys(item))
    console.log('[DEBUG] item.use_result:', item.use_result)
    console.log('[DEBUG] item.UseResult:', item.UseResult)
    console.log('[DEBUG] item.parameters:', item.parameters)
    console.log('[DEBUG] 建構後的 testParams:', testParams)

    // 修正: 合併 parameters 欄位到 testParams（優先級最高）
    // parameters 欄位包含從動態參數表單設定的值，應覆蓋資料庫欄位的值
    if (item.parameters && typeof item.parameters === 'object') {
      Object.entries(item.parameters).forEach(([key, value]) => {
        // 只合併非空值
        if (value !== null && value !== undefined && value !== '') {
          testParams[key] = value
        }
      })
      console.log('[DEBUG] 合併 parameters 後的 testParams:', testParams)
    }
    console.log('[DEBUG] testParams.use_result:', testParams.use_result)
    console.log('[DEBUG] testParams.UseResult:', testParams.UseResult)

    // Handle UseResult dependency (參考 oneCSV_atlas_2.py:146-155)
    // 原有程式碼: 只檢查大寫的 UseResult，但資料庫欄位是小寫的 use_result
    // 修正: 同時檢查大小寫，並將 use_result 的值替換為實際的測量結果
    // 這樣後端就會收到實際的測量值 (例如 "123") 而不是項目名稱 (例如 "123_1")

    // 新增: 詳細日誌追蹤 use_result 處理
    console.log('[DEBUG] ============================================')
    console.log('[DEBUG] UseResult 處理開始')
    console.log('[DEBUG] 項目:', item.item_name)
    console.log('[DEBUG] testParams.use_result (原始):', testParams.use_result)
    console.log('[DEBUG] testParams.UseResult (原始):', testParams.UseResult)
    console.log('[DEBUG] testResults.value:', testResults.value)
    console.log('[DEBUG] testResults keys:', Object.keys(testResults.value))

    // 處理小寫 use_result (資料庫欄位名稱)
    if (testParams.use_result) {
      console.log('[DEBUG] 找到小寫 use_result:', testParams.use_result)
      const useResultValue = testResults.value[testParams.use_result]
      console.log('[DEBUG] 從 testResults 查找:', testParams.use_result, '→', useResultValue)
      if (useResultValue !== undefined) {
        // 修正: 標準化數值格式，去除 ".0" 後綴以匹配腳本期望
        // 例如: "123.0" → "123", "456.0" → "456"
        let normalizedValue = useResultValue
        if (typeof useResultValue === 'string' && /^\d+\.0$/.test(useResultValue)) {
          normalizedValue = useResultValue.replace(/\.0$/, '')
          console.log('[DEBUG] 標準化數值:', useResultValue, '→', normalizedValue)
        }

        // 將 use_result 的值替換為實際的測量結果
        testParams.use_result = normalizedValue
        console.log('[DEBUG] 替換後 use_result:', testParams.use_result)

        // 如果有 Command 欄位，也附加結果值 (PDTool4 兼容)
        if (testParams.Command) {
          testParams.Command = testParams.Command + ' ' + normalizedValue
        }
      } else {
        console.log('[DEBUG] ⚠️ 未找到對應的測試結果:', testParams.use_result)
      }
    }

    // 處理大寫 UseResult (向後兼容舊的命名)
    if (testParams.UseResult) {
      console.log('[DEBUG] 找到大寫 UseResult:', testParams.UseResult)
      const useResultValue = testResults.value[testParams.UseResult]
      console.log('[DEBUG] 從 testResults 查找:', testParams.UseResult, '→', useResultValue)
      if (useResultValue !== undefined) {
        // 修正: 標準化數值格式，去除 ".0" 後綴
        let normalizedValue = useResultValue
        if (typeof useResultValue === 'string' && /^\d+\.0$/.test(useResultValue)) {
          normalizedValue = useResultValue.replace(/\.0$/, '')
          console.log('[DEBUG] 標準化數值:', useResultValue, '→', normalizedValue)
        }

        testParams.UseResult = normalizedValue
        console.log('[DEBUG] 替換後 UseResult:', testParams.UseResult)

        if (testParams.Command) {
          testParams.Command = testParams.Command + ' ' + normalizedValue
        }
      } else {
        console.log('[DEBUG] ⚠️ 未找到對應的測試結果:', testParams.UseResult)
      }
    }

    console.log('[DEBUG] 最終 testParams.use_result:', testParams.use_result)
    console.log('[DEBUG] 最終 testParams.UseResult:', testParams.UseResult)
    console.log('[DEBUG] ============================================')

    // Track used instruments
    if (testParams.Instrument) {
      usedInstruments.value[testParams.Instrument] = executeName
    }

    // 原有程式碼: 只對於 'Other' 類型的測試，確保 command 欄位被正確傳遞
    // 修改: 對於 'Other' 和 'CommandTest' 類型的測試，都要確保 command 欄位被正確傳遞
    // command 欄位從資料庫 test_plans 表的 command 欄位讀取
    if ((executeName === 'Other' || executeName === 'CommandTest') && item.command && !testParams.command) {
      testParams.command = item.command
    }

    // 修正方案 A: 正確區分 measurement_type 和 switch_mode 的角色
    // - measurement_type: 從 execute_name 或 test_type 獲取 (測量類型: PowerSet, PowerRead, CommandTest, Other, Wait 等)
    // - switch_mode: 從 switch_mode 欄位獲取 (儀器/腳本/特殊類型: DAQ973A, wait, relay, console, comport, test123 等)
    let measurementType = executeName || item.test_type || 'Other'  // 預設為 'Other' 表示自定義腳本
    let finalSwitchMode = switchMode || item.item_name || 'script'  // 預設使用 'script' 作為通用腳本模式

    // 特殊處理: 如果 switch_mode 是特殊測試類型 (wait, relay 等)
    // 將 measurement_type 設為 'Other' (這些特殊類型都屬於 Other 測量類別)
    const specialTypes = ['wait', 'relay', 'chassis_rotation', 'console', 'comport', 'tcpip']
    if (switchMode && specialTypes.includes(switchMode.toLowerCase())) {
      measurementType = 'Other'  // 使用 Other 測量類別處理特殊類型
      finalSwitchMode = switchMode.toLowerCase()
    }

    // Execute measurement via API
    const measurementData = {
      measurement_type: measurementType,
      test_point_id: String(item.item_no),
      switch_mode: finalSwitchMode,  // 修正方案 A: 使用處理後的 switch_mode
      test_params: testParams,
      run_all_test: runAllTests.value
    }

    const response = await executeSingleMeasurement(measurementData)

    // Validate against limits
    // 原有程式碼: const measuredValue = Number(response.measured_value)
    // 修改: 支援字串類型的測量值,只有數值類型才進行限制值檢查
    let result = response.result
    if (response.measured_value !== null && response.measured_value !== undefined) {
      // 檢查是否為數值類型
      const measuredValue = Number(response.measured_value)
      const isNumeric = !isNaN(measuredValue) && typeof response.measured_value !== 'string'

      // 只有數值類型才進行限制值檢查
      if (isNumeric) {
        const lowerLimit = item.lower_limit !== null ? Number(item.lower_limit) : null
        const upperLimit = item.upper_limit !== null ? Number(item.upper_limit) : null

        if (lowerLimit !== null && measuredValue < lowerLimit) {
          result = 'FAIL'
        } else if (upperLimit !== null && measuredValue > upperLimit) {
          result = 'FAIL'
        } else if (lowerLimit !== null || upperLimit !== null) {
          result = 'PASS'
        }
      }
      // 字串類型保持原有的 result 結果,不進行限制值檢查
    }

    // 新增: 方案 A - 保存測試結果到資料庫
    // 在每個測項執行完畢後，立即保存結果到 test_results 表
    if (currentSession.value && item.id) {
      try {
        // 修正: 將 measured_value 轉換為字串，避免類型不匹配導致後端 500 錯誤
        // 資料庫 measured_value 欄位是 String(100)，但 response.measured_value 可能是數字類型
        const measuredValueStr = response.measured_value !== null && response.measured_value !== undefined
          ? String(response.measured_value)
          : null

        await createTestResult(currentSession.value.id, {
          session_id: currentSession.value.id,
          test_plan_id: item.id,
          item_no: item.item_no,
          item_name: item.item_name,
          measured_value: measuredValueStr,
          lower_limit: item.lower_limit,
          upper_limit: item.upper_limit,
          unit: item.unit,
          result: result,
          error_message: response.error_message,
          execution_duration_ms: response.execution_duration_ms
        })
      } catch (saveError) {
        // 保存失敗不影響測試流程，只記錄錯誤
        console.error('Failed to save test result:', saveError)
        addStatusMessage(`保存測試結果失敗: ${saveError.message}`, 'warning')
      }
    }

    return {
      result: result,
      measured_value: response.measured_value,
      error_message: response.error_message
    }

  } catch (error) {
    throw new Error(`量測執行失敗: ${error.response?.data?.detail || error.message}`)
  }
}

// 新增: 清理儀器 (參考 oneCSV_atlas_2.py:244-265)
const cleanupInstruments = async () => {
  if (Object.keys(usedInstruments.value).length === 0) {
    return
  }

  addStatusMessage('開始儀器初始化...', 'info')

  for (const [instrumentLocation, instrumentType] of Object.entries(usedInstruments.value)) {
    try {
      await resetInstrument(instrumentLocation)
      addStatusMessage(`儀器 ${instrumentLocation} 已重置`, 'success')
    } catch (error) {
      console.error(`Failed to reset instrument ${instrumentLocation}:`, error)
      addStatusMessage(`儀器 ${instrumentLocation} 重置失敗: ${error.message}`, 'warning')
    }
  }

  addStatusMessage('儀器初始化完成', 'success')
  usedInstruments.value = {}
}

// 移除測試計劃列表相關函數，因為系統架構中沒有獨立的測試計劃實體
/*
// 新增: 載入測試計劃列表並恢復上次選擇
const loadTestPlanList = async () => {
  if (!currentStation.value) return

  try {
    // TODO: 這裡應該調用 API 獲取該站別的所有測試計劃列表
    // 暫時使用空陣列，因為後端可能還沒有對應的 API
    testPlans.value = []

    // 從 localStorage 讀取上次選擇的測試計劃 ID
    const lastSelectedPlan = localStorage.getItem(`lastTestPlan_station_${currentStation.value.id}`)

    if (lastSelectedPlan && testPlans.value.length > 0) {
      const planId = parseInt(lastSelectedPlan)
      const plan = testPlans.value.find(p => p.id === planId)
      if (plan) {
        selectedTestPlan.value = planId
        addStatusMessage(`已恢復上次選擇的測試計劃: ${plan.plan_name}`, 'info')
      }
    }

    // 載入測試項目
    await loadTestPlanItems()
  } catch (error) {
    console.error('Failed to load test plan list:', error)
  }
}

// 修改: 當測試計劃改變時，保存選擇並重新載入
const handleTestPlanChange = () => {
  if (selectedTestPlan.value && currentStation.value) {
    // 保存到 localStorage
    localStorage.setItem(`lastTestPlan_station_${currentStation.value.id}`, selectedTestPlan.value.toString())
    addStatusMessage(`已切換測試計劃`, 'info')
  }
  loadTestPlanItems()
}
*/

const handleSFCToggle = () => {
  if (sfcEnabled.value) {
    addStatusMessage('SFC 已啟用', 'success')
  } else {
    addStatusMessage('SFC 已停用', 'info')
  }
}

const saveSFCConfig = () => {
  ElMessage.success('SFC 配置已儲存')
  showSFCConfig.value = false
  addStatusMessage('SFC 配置已更新', 'success')
}

const handleStartTest = async () => {
  if (requireBarcode.value && !barcode.value.trim()) {
    ElMessage.warning('請輸入產品序號')
    return
  }

  if (!currentStation.value) {
    ElMessage.warning('請先選擇站別')
    return
  }

  if (testPlanItems.value.length === 0) {
    ElMessage.warning('請先載入測試計劃')
    return
  }

  testing.value = true
  testCompleted.value = false
  errorCode.value = ''

  // 原有程式碼: 沒有重置 loopCount
  // 修改: 重置 loopCount 為 0，表示準備開始新的循環測試
  loopCount.value = 0

  // Reset test plan items status
  testPlanItems.value.forEach(item => {
    item.status = null
    item.measured_value = null
  })

  try {
    const serialNumber = requireBarcode.value ? barcode.value.trim() : 'AUTO-' + Date.now()
    addStatusMessage(`開始測試: ${serialNumber}`, 'info')

    // Create test session
    const session = await createTestSession({
      serial_number: serialNumber,
      station_id: currentStation.value.id
    })

    currentSession.value = session
    addStatusMessage(`測試會話已創建 (ID: ${session.id})`, 'success')

    // 新增: 直接執行量測 (參考 PDTool4/oneCSV_atlas_2.py 的執行模式)
    // 不使用 startTestExecution API，而是直接在前端執行量測邏輯
    testStatus.value.status = 'RUNNING'

    // Execute measurements sequentially (包含 Loop 測試邏輯)
    await executeMeasurements()

    // Note: executeMeasurements 會在完成時自動設定 finalResult 和 testCompleted
    // 不再需要輪詢機制

  } catch (error) {
    console.error('Failed to start test:', error)
    const errorMsg = error.response?.data?.detail || error.message || '未知錯誤'
    addStatusMessage(`開始測試失敗: ${errorMsg}`, 'error')
    errorCode.value = `啟動失敗: ${errorMsg}`
    ElMessage.error('開始測試失敗')
    testing.value = false
    currentSession.value = null
  }
}

const handleStopTest = async () => {
  if (!currentSession.value) return

  try {
    await ElMessageBox.confirm('確定要停止測試嗎？', '確認', {
      confirmButtonText: '確定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    // 新增: 直接設定 testing 為 false，executeMeasurements 會檢查這個標誌
    testing.value = false
    addStatusMessage('測試已停止', 'warning')
    testStatus.value.status = 'ABORTED'
    finalResult.value = 'ABORT'

    // 仍然呼叫 API 停止後端會話（如果有的話）
    try {
      await stopTestExecution(currentSession.value.id)
    } catch (apiError) {
      // 忽略 API 錯誤，因為可能前端執行模式下後端沒有在運行
      console.log('Backend stop API call failed (expected in frontend-only execution mode):', apiError)
    }

  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to stop test:', error)
      addStatusMessage('停止測試失敗: ' + error.message, 'error')
      ElMessage.error('停止測試失敗')
    }
  }
}

const startStatusPolling = () => {
  if (statusPollInterval) {
    clearInterval(statusPollInterval)
  }

  statusPollInterval = setInterval(async () => {
    if (!currentSession.value) return

    try {
      // Get status
      const status = await getTestSessionStatus(currentSession.value.id)
      testStatus.value = status

      // Get results
      const results = await getSessionResults(currentSession.value.id)
      
      // Update test plan items with results
      results.forEach(result => {
        const item = testPlanItems.value.find(i => i.item_no === result.item_no)
        if (item) {
          item.status = result.result
          item.measured_value = result.measured_value
        }
      })

      // Check if completed
      if (status.status === 'COMPLETED' || status.status === 'ABORTED') {
        stopStatusPolling()
        testing.value = false
        testCompleted.value = true
        
        // Determine final result
        if (status.status === 'ABORTED') {
          finalResult.value = 'ABORT'
          addStatusMessage('測試已中止', 'warning')
        } else if (status.fail_items > 0) {
          finalResult.value = 'FAIL'
          addStatusMessage(`測試完成: FAIL (${status.pass_items}/${status.total_items} 通過)`, 'error')
          errorCode.value = `測試失敗: ${status.fail_items} 項未通過`
        } else {
          finalResult.value = 'PASS'
          addStatusMessage(`測試完成: PASS (${status.pass_items}/${status.total_items} 通過)`, 'success')
        }

        // Increment loop counter
        if (sfcConfig.loopEnabled) {
          loopCount.value++
        }

        // Clear barcode after test
        setTimeout(() => {
          barcode.value = ''
        }, 2000)
      }

    } catch (error) {
      console.error('Failed to poll status:', error)
      // Don't stop polling on error, just log it
    }
  }, 1000) // Poll every second
}

const stopStatusPolling = () => {
  if (statusPollInterval) {
    clearInterval(statusPollInterval)
    statusPollInterval = null
  }
}

// 修正: 移除確認對話框,直接執行登出,避免需要點擊兩次的問題
// 修正: 先執行登出再清除專案選擇,確保一次點擊就能完成登出
// 修正: 確保 logout 完成後再進行路由跳轉,避免路由守衛阻擋
const handleLogout = async () => {
  try {
    // 先執行登出並清除認證狀態 (await 確保完成)
    await authStore.logout()

    // 清除專案和站別選擇
    projectStore.clearCurrentSelection()

    // 跳轉到登入頁面
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    // 即使失敗也要清除本地狀態並跳轉
    projectStore.clearCurrentSelection()
    router.push('/login')
  }
}

// 新增: 處理專案變更
const handleProjectChange = async () => {
  // 清除站別選擇
  selectedStationId.value = null
  selectedTestPlanName.value = null
  testPlanNames.value = []
  testPlanItems.value = []

  if (selectedProjectId.value) {
    const project = projectStore.projects.find(p => p.id === selectedProjectId.value)
    addStatusMessage(`已選擇專案: ${project?.project_code} - ${project?.project_name}`, 'info')

    // 原有程式碼: 沒有載入該專案的站別列表
    // 修改: 當選擇專案時，載入該專案的站別列表
    try {
      await projectStore.fetchProjectStations(selectedProjectId.value)
    } catch (error) {
      console.error('Failed to load stations:', error)
      addStatusMessage('載入站別列表失敗: ' + error.message, 'error')
    }
  }

  // 清除站別相關的 localStorage
  if (currentStation.value) {
    localStorage.removeItem(`lastTestPlanName_station_${currentStation.value.id}`)
  }
}

// 新增: 處理站別變更
const handleStationChange = async () => {
  selectedTestPlanName.value = null
  testPlanNames.value = []
  testPlanItems.value = []
  // 新增: 清除測試點映射表
  testPointMap.value = null
  testPointsById.value = {}

  if (currentStation.value) {
    addStatusMessage(`已選擇站別: ${currentStation.value.station_code} - ${currentStation.value.station_name}`, 'info')
    await loadTestPlanNames()
    // 新增: 先載入 TestPlanMap，再載入測試計劃項目
    await loadTestPlanMap()
    await loadTestPlanItems()
  }
}

// Watchers
// 原有程式碼: 當站別改變時，載入測試計劃名稱和測試項目
// 修改: 移除這個 watcher,因為我們改用 handleStationChange 手動處理
// watch(() => currentStation.value, async (newVal) => {
//   if (newVal) {
//     await loadTestPlanNames()
//     await loadTestPlanItems()
//   }
// })

// Lifecycle
onMounted(async () => {
  addStatusMessage('系統就緒', 'success')

  // 原有程式碼: 沒有載入專案列表
  // 修改: 載入所有專案列表 (參考 TestPlanManage.vue:848-854)
  if (projectStore.projects.length === 0) {
    try {
      await projectStore.fetchProjects()
    } catch (error) {
      console.error('Failed to load projects:', error)
      addStatusMessage('載入專案列表失敗: ' + error.message, 'error')
    }
  }

  // 原有程式碼: 使用 store 中的 currentProject 和 currentStation
  // 修改: 初始化時,如果 store 中有選擇的專案和站別,則設為預設選擇
  if (projectStore.currentProject) {
    selectedProjectId.value = projectStore.currentProject.id
    // 原有程式碼: 沒有載入該專案的站別列表
    // 修改: 載入該專案的站別列表 (參考 TestPlanManage.vue:857-869)
    try {
      await projectStore.fetchProjectStations(projectStore.currentProject.id)
    } catch (error) {
      console.error('Failed to load stations:', error)
      addStatusMessage('載入站別列表失敗: ' + error.message, 'error')
    }
  }
  if (projectStore.currentStation && projectStore.currentStation.project_id === selectedProjectId.value) {
    selectedStationId.value = projectStore.currentStation.id
  }

  // 如果有選擇站別,載入測試計劃名稱、測試點映射表和測試項目
  if (currentStation.value) {
    await loadTestPlanNames()
    await loadTestPlanMap()
    await loadTestPlanItems()
  }

  // Load SFC config from localStorage
  const savedConfig = localStorage.getItem('sfcConfig')
  if (savedConfig) {
    Object.assign(sfcConfig, JSON.parse(savedConfig))
  }
})

onUnmounted(() => {
  stopStatusPolling()
  
  // Save SFC config to localStorage
  localStorage.setItem('sfcConfig', JSON.stringify(sfcConfig))
})
</script>

<style scoped>
.test-main-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

/* Info Card */
.info-card {
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  font-size: 15px;
}

.info-label {
  font-weight: bold;
  color: #606266;
  margin-right: 8px;
}

.info-value {
  color: #409eff;
  font-weight: 500;
}

/* Config Card */
.config-card {
  margin-bottom: 20px;
}

.config-card :deep(.el-form-item) {
  margin-bottom: 0;
}

.loop-counter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.loop-label {
  font-size: 16px;
  font-weight: bold;
  color: #606266;
}

.loop-display {
  background: linear-gradient(to bottom, #1e3c72, #2a5298);
  color: #00ff00;
  font-family: 'Courier New', monospace;
  font-size: 28px;
  font-weight: bold;
  padding: 5px 20px;
  border-radius: 4px;
  border: 2px solid #333;
  min-width: 80px;
  text-align: center;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);
}

/* Card Headers */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

/* Test Plan Table */
.test-plan-card :deep(.el-table) {
  font-size: 13px;
}

.test-plan-card :deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: bold;
}

.test-plan-card :deep(.row-pass) {
  background-color: #f0f9ff;
}

.test-plan-card :deep(.row-fail) {
  background-color: #fef0f0;
}

.test-plan-card :deep(.row-error) {
  background-color: #fdf6ec;
}

/* 新增: 執行中的行背景色 */
.test-plan-card :deep(.row-executing) {
  background-color: #fffbf0;
}

/* 新增: 測試點測量值樣式 */
.test-point-value-pass {
  color: #67C23A;
  font-weight: 600;
}

.test-point-value-fail {
  color: #F56C6C;
  font-weight: 600;
}

/* 新增: 淡化未執行的值 */
.text-muted {
  color: #C0C4CC;
}

.value-pass {
  color: #67c23a;
  font-weight: bold;
}

.value-fail {
  color: #f56c6c;
  font-weight: bold;
}

/* Control Card */
.control-card {
  height: fit-content;
}

.barcode-section {
  margin-bottom: 20px;
}

.control-buttons {
  margin-bottom: 10px;
}

/* Progress Section */
.progress-section {
  margin-top: 10px;
}

.progress-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 15px;
}

.progress-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.progress-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.progress-value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.progress-value.success {
  color: #67c23a;
}

.progress-value.fail {
  color: #f56c6c;
}

/* Result Display */
.result-display {
  margin-top: 10px;
}

.result-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border-radius: 8px;
  font-size: 28px;
  font-weight: bold;
  text-transform: uppercase;
}

.result-banner.pass {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.result-banner.fail {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
}

.result-banner.abort {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  color: #333;
}

.result-icon {
  font-size: 36px;
  margin-right: 12px;
}

.result-text {
  letter-spacing: 2px;
}

/* Status Card */
.status-card {
  height: fit-content;
}

.status-content {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.status-message {
  padding: 4px 8px;
  margin-bottom: 4px;
  border-radius: 3px;
  display: flex;
  gap: 10px;
}

.status-message.info {
  background-color: #f0f9ff;
  color: #0284c7;
}

.status-message.success {
  background-color: #f0fdf4;
  color: #15803d;
}

.status-message.warning {
  background-color: #fffbeb;
  color: #b45309;
}

.status-message.error {
  background-color: #fef2f2;
  color: #dc2626;
}

.status-time {
  font-weight: bold;
  min-width: 70px;
}

.status-text {
  flex: 1;
}

/* Error Card */
.error-card {
  border: 2px solid #f56c6c;
}

.error-content {
  background-color: #fef0f0;
  color: #f56c6c;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Responsive */
@media (max-width: 1200px) {
  .info-item {
    font-size: 13px;
  }
  
  .loop-display {
    font-size: 24px;
    min-width: 60px;
  }
}
</style>
