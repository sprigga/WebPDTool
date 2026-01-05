<template>
  <div class="test-main-container">
    <!-- Top Info Bar -->
    <el-card class="info-card" shadow="never">
      <el-row :gutter="20" align="middle">
        <el-col :span="5">
          <div class="info-item">
            <span class="info-label">專案:</span>
            <span class="info-value">{{ currentProject?.project_code || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="info-item">
            <span class="info-label">站別:</span>
            <span class="info-value">{{ currentStation?.station_code || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="info-item">
            <span class="info-label">使用者:</span>
            <span class="info-value">{{ currentUser?.username || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="5">
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
            <el-table-column prop="item_name" label="測試項目" min-width="180" />
            <el-table-column prop="execute_name" label="測試指令" width="140" />
            <el-table-column label="下限" width="100" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.lower_limit) }}
              </template>
            </el-table-column>
            <el-table-column label="上限" width="100" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.upper_limit) }}
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="單位" width="80" align="center" />
            <el-table-column label="狀態" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.status" :type="getStatusTagType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="測量值" width="120" align="right">
              <template #default="{ row }">
                <span v-if="row.measured_value !== null" :class="getValueClass(row)">
                  {{ formatNumber(row.measured_value) }}
                </span>
                <span v-else>-</span>
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
              :disabled="!barcode || testing"
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
import {
  createTestSession,
  startTestExecution,
  stopTestExecution,
  getTestSessionStatus,
  getSessionResults,
  executeSingleMeasurement,
  resetInstrument
} from '@/api/tests'
import { getStationTestPlan, getStationTestPlanNames } from '@/api/testplans'

const router = useRouter()
const authStore = useAuthStore()
const projectStore = useProjectStore()

// Current user and station
const currentUser = computed(() => authStore.user)
const currentProject = computed(() => projectStore.currentProject)
const currentStation = computed(() => projectStore.currentStation)

// Configuration
const sfcEnabled = ref(false)
const runAllTests = ref(false)
const loopCount = ref(0)
const showSFCConfig = ref(false)
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
const formatNumber = (value) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toFixed(3)
}

const formatElapsedTime = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
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
  if (row.status === 'PASS') return 'row-pass'
  if (row.status === 'FAIL') return 'row-fail'
  if (row.status === 'ERROR') return 'row-error'
  return ''
}

const getValueClass = (row) => {
  if (row.status === 'PASS') return 'value-pass'
  if (row.status === 'FAIL') return 'value-fail'
  return ''
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
    testPlanItems.value = items.map(item => ({
      ...item,
      status: null,
      measured_value: null
    }))
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
const handleTestPlanChange = () => {
  if (selectedTestPlanName.value && currentStation.value) {
    // 保存到 localStorage
    localStorage.setItem(`lastTestPlanName_station_${currentStation.value.id}`, selectedTestPlanName.value)
    addStatusMessage(`已切換測試計劃: ${selectedTestPlanName.value}`, 'info')
  } else if (currentStation.value) {
    // 清除選擇時移除 localStorage
    localStorage.removeItem(`lastTestPlanName_station_${currentStation.value.id}`)
    addStatusMessage('已清除測試計劃選擇', 'info')
  }
  loadTestPlanItems()
}

// 新增: 執行量測功能 (參考 PDTool4 oneCSV_atlas_2.py)
// 整合 runAllTest 模式 - 遇到錯誤時記錄但繼續執行
const executeMeasurements = async () => {
  try {
    addStatusMessage('開始執行測試項目...', 'info')
    if (runAllTests.value) {
      addStatusMessage('PDTool4 runAllTest 模式: 已啟用 - 將在錯誤時繼續執行', 'info')
    }

    // Reset tracking variables
    testResults.value = {}
    usedInstruments.value = {}

    let passCount = 0
    let failCount = 0
    let errorCount = 0
    const errorItems = [] // PDTool4 runAllTest: 收集錯誤項目

    // Execute each test item sequentially (參考 oneCSV_atlas_2.py:131-191)
    for (let index = 0; index < testPlanItems.value.length; index++) {
      const item = testPlanItems.value[index]

      // Update current item status
      testStatus.value.current_item = index + 1

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

        // Update statistics
        if (result.result === 'PASS') {
          passCount++
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
        if (result.measured_value !== null) {
          testResults.value[item.item_no] = String(result.measured_value)
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
        errorCode.value = `項目 ${item.item_no} 執行錯誤: ${error.message}`

        // PDTool4 runAllTest: 遇到異常也繼續
        if (!runAllTests.value) {
          break
        } else {
          addStatusMessage(`[runAllTest] 項目 ${item.item_no} 異常 - 繼續執行`, 'warning')
        }
      }
    }

    // Cleanup instruments (參考 oneCSV_atlas_2.py:244-265)
    await cleanupInstruments()

    // Update final status - 檢查是否有任何 ERROR 或 FAIL 狀態的項目
    const hasError = testPlanItems.value.some(item => item.status === 'ERROR')
    const hasFail = testPlanItems.value.some(item => item.status === 'FAIL')

    // PDTool4 runAllTest: 顯示錯誤摘要
    if (runAllTests.value && errorItems.length > 0) {
      addStatusMessage(`[runAllTest] 完成，但有 ${errorItems.length} 個錯誤項目:`, 'warning')
      errorItems.slice(0, 5).forEach(err => {
        addStatusMessage(`  - ${err.item_no}: ${err.item_name}: ${err.error}`, 'warning')
      })
      if (errorItems.length > 5) {
        addStatusMessage(`  ... 還有 ${errorItems.length - 5} 個錯誤未顯示`, 'warning')
      }
    }

    // 最終結果判定
    if (hasError || hasFail) {
      testStatus.value.status = 'COMPLETED'
      finalResult.value = 'FAIL'
    } else {
      testStatus.value.status = 'COMPLETED'
      finalResult.value = 'PASS'
    }
    testCompleted.value = true

    addStatusMessage(
      `測試完成: ${finalResult.value} (通過: ${passCount}, 失敗: ${failCount}, 錯誤: ${errorCount})`,
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

    // Extract parameters based on ExecuteName
    const executeName = item.execute_name // ExecuteName 是執行名稱
    const caseMode = item.case || item.switch_mode // Switch/case mode

    // Build test parameters (參考 oneCSV_atlas_2.py:134-155)
    // 這裡需要根據實際的 CSV 欄位來構建參數
    // 簡化版本：將所有額外欄位作為參數傳遞
    Object.keys(item).forEach(key => {
      if (!['item_no', 'item_name', 'execute_name', 'lower_limit', 'upper_limit',
            'unit', 'status', 'measured_value'].includes(key)) {
        if (item[key] && item[key] !== '') {
          testParams[key] = item[key]
        }
      }
    })

    // Handle UseResult dependency (參考 oneCSV_atlas_2.py:146-155)
    if (testParams.UseResult && testResults.value[testParams.UseResult]) {
      const useResultValue = testResults.value[testParams.UseResult]
      if (testParams.Command) {
        testParams.Command = testParams.Command + ' ' + useResultValue
      }
    }

    // Track used instruments
    if (testParams.Instrument) {
      usedInstruments.value[testParams.Instrument] = executeName
    }

    // 新增: 對於 'Other' 類型的測試，確保 command 欄位被正確傳遞
    // command 欄位從資料庫 test_plans 表的 command 欄位讀取
    if (executeName === 'Other' && item.command && !testParams.command) {
      testParams.command = item.command
    }

    // Execute measurement via API
    const measurementData = {
      measurement_type: executeName || 'Other',
      test_point_id: String(item.item_no),
      switch_mode: caseMode || 'default',
      test_params: testParams,
      run_all_test: runAllTests.value
    }

    const response = await executeSingleMeasurement(measurementData)

    // Validate against limits
    let result = response.result
    if (response.measured_value !== null && response.measured_value !== undefined) {
      const measuredValue = Number(response.measured_value)
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
  if (!barcode.value.trim()) {
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

  // Reset test plan items status
  testPlanItems.value.forEach(item => {
    item.status = null
    item.measured_value = null
  })

  try {
    addStatusMessage(`開始測試: ${barcode.value}`, 'info')

    // Create test session
    const session = await createTestSession({
      serial_number: barcode.value.trim(),
      station_id: currentStation.value.id
    })

    currentSession.value = session
    addStatusMessage(`測試會話已創建 (ID: ${session.id})`, 'success')

    // 新增: 直接執行量測 (參考 PDTool4/oneCSV_atlas_2.py 的執行模式)
    // 不使用 startTestExecution API，而是直接在前端執行量測邏輯
    testStatus.value.status = 'RUNNING'

    // Execute measurements sequentially
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

// Watchers
// 當站別改變時，載入測試計劃名稱和測試項目
watch(() => currentStation.value, async (newVal) => {
  if (newVal) {
    await loadTestPlanNames()
    await loadTestPlanItems()
  }
})

// Lifecycle
onMounted(async () => {
  addStatusMessage('系統就緒', 'success')

  // 載入當前站別的測試計劃名稱和測試項目
  if (currentStation.value) {
    await loadTestPlanNames()
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
