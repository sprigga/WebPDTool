<template>
  <div class="test-history-container">
    <AppNavBar current-page="history" />

    <el-card>
      <template #header>
        <div class="card-header">
          <h2>測試歷史記錄</h2>
          <el-button type="primary" @click="handleRefresh" :loading="loading">
            重新整理
          </el-button>
        </div>
      </template>

      <!-- Date Range Picker -->
      <el-card class="filter-card" shadow="never">
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="開始日期"
              end-placeholder="結束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              @change="handleDateChange"
            />
          </el-col>
          <el-col :span="5">
            <el-select v-model="selectedProject" placeholder="全部專案" clearable style="width: 100%">
              <el-option
                v-for="project in projectStore.projects"
                :key="project.id"
                :label="project.project_name"
                :value="project.id"
              />
            </el-select>
          </el-col>
          <el-col :span="5">
            <el-select
              v-model="selectedStation"
              placeholder="全部站別"
              clearable
              :disabled="!selectedProject"
              style="width: 100%"
            >
              <el-option
                v-for="station in filteredStations"
                :key="station.id"
                :label="station.station_name"
                :value="station.id"
              />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-button type="primary" @click="handleSearch" :loading="loading">
              查詢
            </el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-col>
        </el-row>
      </el-card>

      <!-- Loading State -->
      <el-skeleton v-if="loading && sessions.length === 0" :rows="5" animated />

      <!-- Empty State -->
      <el-empty v-else-if="!loading && sessions.length === 0" description="暫無測試記錄" />

      <!-- Timeline Content -->
      <div v-else class="timeline-content">
        <!-- Statistics Summary -->
        <el-row :gutter="20" class="stats-row">
          <el-col :span="6">
            <el-statistic title="總測試次數" :value="sessions.length" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="通過" :value="passCount">
              <template #prefix>
                <el-text type="success">●</el-text>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="失敗" :value="failCount">
              <template #prefix>
                <el-text type="danger">●</el-text>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="通過率" :value="passRate" suffix="%" />
          </el-col>
        </el-row>

        <!-- Timeline -->
        <el-timeline class="history-timeline">
          <el-timeline-item
            v-for="(daySessions, date) in sessionsByDate"
            :key="date"
            :timestamp="formatDate(date)"
            placement="top"
          >
            <el-card>
              <template #header>
                <div class="day-header">
                  <span>{{ formatDate(date) }}</span>
                  <el-tag size="small">{{ daySessions.length }} 筆記錄</el-tag>
                </div>
              </template>
              <div class="day-stats">
                <el-text type="success">通過: {{ dailyStats[date].pass }}</el-text>
                <el-text type="danger">失敗: {{ dailyStats[date].fail }}</el-text>
                <el-text type="warning">中止: {{ dailyStats[date].abort }}</el-text>
              </div>
              <el-collapse>
                <el-collapse-item v-for="session in daySessions" :key="session.id" :name="session.id">
                  <template #title>
                    <div class="session-title">
                      <el-tag :type="getResultTagType(session.final_result)" size="small">
                        {{ session.final_result || '進行中' }}
                      </el-tag>
                      <span class="session-sn">{{ session.serial_number }}</span>
                      <span class="session-time">{{ formatTime(session.start_time) }}</span>
                    </div>
                  </template>
                  <div class="session-details">
                    <p><strong>站別:</strong> {{ getStationName(session) }}</p>
                    <p><strong>測試計劃:</strong> {{ session.test_plan_name || '-' }}</p>
                    <p><strong>統計:</strong>
                      通過 {{ session.pass_items || 0 }} /
                      失敗 {{ session.fail_items || 0 }} /
                      總計 {{ session.total_items || 0 }}
                    </p>
                    <p v-if="session.test_duration_seconds">
                      <strong>時長:</strong> {{ session.test_duration_seconds.toFixed(2) }} 秒
                    </p>
                    <el-button type="primary" size="small" @click="handleViewResults(session)">
                      查看詳細結果
                    </el-button>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>

    <!-- Results Dialog (reuse from TestResults.vue) -->
    <el-dialog v-model="showResultsDialog" title="測試結果詳情" width="90%" top="5vh">
      <div v-if="selectedSession">
        <el-descriptions :column="2" border style="margin-bottom: 20px">
          <el-descriptions-item label="Session ID">
            {{ selectedSession.id }}
          </el-descriptions-item>
          <el-descriptions-item label="序號">
            {{ selectedSession.serial_number }}
          </el-descriptions-item>
          <el-descriptions-item label="站別">
            {{ getStationName(selectedSession) }}
          </el-descriptions-item>
          <el-descriptions-item label="測試計劃">
            {{ selectedSession.test_plan_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最終結果">
            <el-tag :type="getResultTagType(selectedSession.final_result)">
              {{ selectedSession.final_result || '進行中' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="測試時間">
            {{ formatDateTime(selectedSession.start_time) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- Loading state for results -->
        <el-skeleton v-if="resultsLoading" :rows="5" animated />

        <!-- Empty state for results -->
        <el-empty
          v-else-if="!resultsLoading && sessionResults.length === 0"
          description="此 Session 無測試項目明細"
        />

        <!-- Results table -->
        <el-table
          v-else
          :data="sessionResults"
          stripe
          max-height="500"
        >
          <el-table-column prop="item_no" label="項次" width="80" />
          <el-table-column prop="item_name" label="測試項目" min-width="150" />
          <el-table-column prop="measured_value" label="測量值" min-width="200">
            <template #default="{ row }">
              <span style="white-space: pre-wrap; word-break: break-all;">
                {{ row.measured_value }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="限制值" width="150">
            <template #default="{ row }">
              <span v-if="row.lower_limit !== null || row.upper_limit !== null">
                {{ row.lower_limit ?? '-' }} ~ {{ row.upper_limit ?? '-' }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="unit" label="單位" width="80" />
          <el-table-column label="結果" width="100">
            <template #default="{ row }">
              <el-tag :type="getResultTagType(row.result)">
                {{ row.result }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="執行時間" width="120">
            <template #default="{ row }">
              {{ row.execution_duration_ms != null ? `${(row.execution_duration_ms / 1000).toFixed(3)} s` : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showResultsDialog = false">關閉</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppNavBar from '@/components/AppNavBar.vue'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { queryTestSessions, getSessionWithResults } from '@/api/testResults'
import { useTestHistory } from '@/composables/useTestHistory'
import { normalizeTaipeiDate } from '@/utils/dateHelpers'

// Stores
const projectStore = useProjectStore()
const authStore = useAuthStore()

// Composable
const { sessions, sessionsByDate, dailyStats, loading, fetchSessions } = useTestHistory()

// Filters
const dateRange = ref([])
const selectedProject = ref(null)
const selectedStation = ref(null)

// Computed: Filter stations by selected project (matches TestResults.vue pattern)
const filteredStations = computed(() => {
  if (!selectedProject.value) {
    return projectStore.stations
  }
  return projectStore.stations.filter((station) => station.project_id === selectedProject.value)
})

// Dialog
const showResultsDialog = ref(false)
const selectedSession = ref(null)
const sessionResults = ref([])
const resultsLoading = ref(false)

// Computed statistics
const passCount = computed(() => sessions.value.filter(s => s.final_result === 'PASS').length)
const failCount = computed(() => sessions.value.filter(s => s.final_result === 'FAIL').length)
const passRate = computed(() => {
  if (sessions.value.length === 0) return 0
  return ((passCount.value / sessions.value.length) * 100).toFixed(1)
})

// Build query params
const buildQueryParams = () => {
  const params = {
    limit: 500, // Larger limit for history view
    offset: 0
  }

  if (selectedStation.value) {
    params.station_id = selectedStation.value
  }

  if (selectedProject.value) {
    params.project_id = selectedProject.value
  }

  if (dateRange.value?.length === 2) {
    params.start_date = new Date(`${dateRange.value[0]}T00:00:00`).toISOString()
    params.end_date = new Date(`${dateRange.value[1]}T23:59:59`).toISOString()
  }

  return params
}

// Load sessions
const loadSessions = async () => {
  await fetchSessions(buildQueryParams())
}

// Event handlers
const handleRefresh = () => loadSessions()
const handleDateChange = () => loadSessions()
const handleSearch = () => loadSessions()
const handleReset = () => {
  selectedProject.value = null
  selectedStation.value = null
  dateRange.value = []
  loadSessions()
}

const handleViewResults = async (session) => {
  selectedSession.value = session
  showResultsDialog.value = true
  resultsLoading.value = true

  try {
    const resultData = await getSessionWithResults(session.id)
    sessionResults.value = Array.isArray(resultData) ? resultData : []
  } catch (error) {
    ElMessage.error('載入測試結果失敗')
  } finally {
    resultsLoading.value = false
  }
}

// Helper functions
const getResultTagType = (result) => {
  const types = { PASS: 'success', FAIL: 'danger', ABORT: 'warning' }
  return types[result] || 'info'
}

const getStationName = (session) => {
  const station = projectStore.stations.find(s => s.id === session.station_id)
  return station?.station_name || `站別 ${session.station_id}`
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

const formatTime = (dateStr) => {
  const normalized = normalizeTaipeiDate(dateStr)
  if (!normalized) return '-'
  const date = new Date(normalized)
  return date.toLocaleTimeString('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const normalized = /[Zz]|[+-]\d{2}:?\d{2}$/.test(dateStr) ? dateStr : dateStr + '+08:00'
  const date = new Date(normalized)
  return date.toLocaleString('zh-TW', {
    timeZone: 'Asia/Taipei',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Initialize
onMounted(async () => {
  try {
    await projectStore.fetchProjects()
    await projectStore.fetchAllStations()

    // Set default date range to last 7 days
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 7)
    dateRange.value = [
      start.toISOString().split('T')[0],
      end.toISOString().split('T')[0]
    ]

    await loadSessions()
  } catch (error) {
    ElMessage.error('初始化失敗')
  }
})
</script>

<style scoped>
.test-history-container {
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

.filter-card {
  margin-bottom: 20px;
}

.filter-card :deep(.el-card__body) {
  padding: 15px 20px;
}

.timeline-content {
  margin-top: 20px;
}

.stats-row {
  margin-bottom: 30px;
}

.history-timeline {
  padding-left: 20px;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.day-stats {
  margin-bottom: 10px;
  display: flex;
  gap: 20px;
}

.session-title {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.session-sn {
  font-weight: 500;
  flex: 1;
}

.session-time {
  font-size: 12px;
  color: #909399;
}

.session-details p {
  margin: 5px 0;
}

.session-details .el-button {
  margin-top: 10px;
}

:deep(.el-collapse-item__header) {
  height: auto;
  padding: 10px 15px;
}

:deep(.el-timeline-item__timestamp) {
  color: #909399;
  font-size: 14px;
}

:deep(.el-timeline-item__wrapper) {
  padding-left: 20px;
}

:deep(.el-collapse-item__content) {
  padding-bottom: 10px;
}

/* Mobile responsive design */
@media (max-width: 768px) {
  .test-history-container {
    padding: 10px;
  }

  .stats-row :deep(.el-col) {
    margin-bottom: 10px;
  }

  .history-timeline {
    padding-left: 10px;
  }

  .session-title {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }

  .filter-card :deep(.el-col) {
    margin-bottom: 10px;
  }
}
</style>
