<template>
  <div class="test-results-container">
    <AppNavBar current-page="results" />

    <el-card>
      <template #header>
        <div class="card-header">
          <h2>測試結果查詢</h2>
          <div class="header-actions">
            <el-button
              type="success"
              :icon="Download"
              :disabled="sessions.length === 0"
              @click="handleExport"
            >
              匯出結果
            </el-button>
          </div>
        </div>
      </template>

      <el-card class="filter-card" shadow="never">
        <el-form :model="filters" label-width="100px">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-form-item label="專案">
                <el-select
                  v-model="filters.project_id"
                  placeholder="選擇專案"
                  clearable
                  filterable
                  style="width: 100%"
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
              <el-form-item label="站別">
                <el-select
                  v-model="filters.station_id"
                  placeholder="選擇站別"
                  clearable
                  filterable
                  :disabled="!filters.project_id"
                  style="width: 100%"
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

            <el-col :span="6">
              <el-form-item label="測試計劃">
                <el-select
                  v-model="filters.test_plan_name"
                  placeholder="選擇測試計劃"
                  clearable
                  filterable
                  :disabled="!filters.station_id"
                  style="width: 100%"
                >
                  <el-option
                    v-for="planName in testPlanNames"
                    :key="planName"
                    :label="planName"
                    :value="planName"
                  />
                </el-select>
              </el-form-item>
            </el-col>

            <el-col :span="6">
              <el-form-item label="測試結果">
                <el-select
                  v-model="filters.final_result"
                  placeholder="選擇結果"
                  clearable
                  style="width: 100%"
                >
                  <el-option label="通過" value="PASS" />
                  <el-option label="失敗" value="FAIL" />
                  <el-option label="中止" value="ABORT" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="序號">
                <el-input
                  v-model="filters.serial_number"
                  placeholder="輸入序號"
                  clearable
                />
              </el-form-item>
            </el-col>

            <el-col :span="10">
              <el-form-item label="日期範圍">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="開始日期"
                  end-placeholder="結束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>

            <el-col :span="6" class="search-actions">
              <el-button type="primary" :loading="loading" @click="handleSearch">
                查詢
              </el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <el-alert
        v-if="sessions.length > 0"
        :title="`找到 ${totalSessions} 筆測試記錄，顯示第 ${currentPage} 頁`"
        type="success"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-table
        :data="sessions"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expanded-content">
              <el-descriptions :column="3" border>
                <el-descriptions-item label="專案">
                  {{ getProjectName(row) }}
                </el-descriptions-item>
                <el-descriptions-item label="站別">
                  {{ getStationName(row) }}
                </el-descriptions-item>
                <el-descriptions-item label="測試計劃">
                  {{ row.test_plan_name || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="開始時間">
                  {{ formatDateTime(row.start_time) }}
                </el-descriptions-item>
                <el-descriptions-item label="結束時間">
                  {{ row.end_time ? formatDateTime(row.end_time) : '進行中' }}
                </el-descriptions-item>
                <el-descriptions-item label="測試時長">
                  {{ row.test_duration_seconds ? formatDuration(row.test_duration_seconds) : '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="總項目">
                  {{ row.total_items || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="通過">
                  <el-text type="success">{{ row.pass_items || 0 }}</el-text>
                </el-descriptions-item>
                <el-descriptions-item label="失敗">
                  <el-text type="danger">{{ row.fail_items || 0 }}</el-text>
                </el-descriptions-item>
              </el-descriptions>

              <div class="expanded-actions">
                <el-button type="primary" size="small" @click="handleViewResults(row)">
                  查看詳細結果
                </el-button>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="id" label="Session ID" width="100" />

        <el-table-column prop="serial_number" label="序號" width="180" />

        <el-table-column label="專案/站別" min-width="220">
          <template #default="{ row }">
            <div>
              <div>{{ getProjectName(row) }}</div>
              <el-text type="info" size="small">{{ getStationName(row) }}</el-text>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="test_plan_name" label="測試計劃" width="180">
          <template #default="{ row }">
            {{ row.test_plan_name || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="結果" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.final_result" :type="getResultTagType(row.final_result)">
              {{ getResultLabel(row.final_result) }}
            </el-tag>
            <el-text v-else type="info">進行中</el-text>
          </template>
        </el-table-column>

        <el-table-column label="統計" min-width="200">
          <template #default="{ row }">
            <span v-if="row.total_items">
              通過: <el-text type="success">{{ row.pass_items || 0 }}</el-text>
              / 失敗: <el-text type="danger">{{ row.fail_items || 0 }}</el-text>
              / 總計: {{ row.total_items }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="start_time" label="測試時間" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="totalSessions"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="showResultsDialog"
      title="測試結果詳情"
      width="90%"
      top="5vh"
    >
      <div v-if="selectedSession">
        <el-descriptions :column="2" border style="margin-bottom: 20px">
          <el-descriptions-item label="Session ID">
            {{ selectedSession.id }}
          </el-descriptions-item>
          <el-descriptions-item label="序號">
            {{ selectedSession.serial_number }}
          </el-descriptions-item>
          <el-descriptions-item label="專案">
            {{ getProjectName(selectedSession) }}
          </el-descriptions-item>
          <el-descriptions-item label="站別">
            {{ getStationName(selectedSession) }}
          </el-descriptions-item>
          <el-descriptions-item label="測試計劃">
            {{ selectedSession.test_plan_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最終結果">
            <el-tag v-if="selectedSession.final_result" :type="getResultTagType(selectedSession.final_result)">
              {{ getResultLabel(selectedSession.final_result) }}
            </el-tag>
            <el-text v-else type="info">進行中</el-text>
          </el-descriptions-item>
        </el-descriptions>

        <el-table
          :data="sessionResults"
          v-loading="resultsLoading"
          stripe
          max-height="500"
        >
          <el-table-column prop="item_no" label="項次" width="80" />
          <el-table-column prop="item_name" label="測試項目" min-width="220" />
          <el-table-column prop="measured_value" label="測量值" width="120" />
          <el-table-column label="限制值" width="180">
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
          <el-table-column prop="error_message" label="錯誤訊息" min-width="220" show-overflow-tooltip />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="showResultsDialog = false">關閉</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import AppNavBar from '@/components/AppNavBar.vue'
import { useProjectStore } from '@/stores/project'
import { queryTestSessions, getSessionWithResults, exportTestResults } from '@/api/testResults'
import { getStationTestPlanNames } from '@/api/testplans'

const projectStore = useProjectStore()

const filters = reactive({
  project_id: null,
  station_id: null,
  test_plan_name: null,
  final_result: null,
  serial_number: null
})

const dateRange = ref([])
const testPlanNames = ref([])
const sessions = ref([])
const loading = ref(false)
const totalSessions = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const showResultsDialog = ref(false)
const selectedSession = ref(null)
const sessionResults = ref([])
const resultsLoading = ref(false)

const filteredStations = computed(() => {
  if (!filters.project_id) {
    return []
  }
  return projectStore.stations.filter((station) => station.project_id === filters.project_id)
})

const handleProjectChange = async (projectId) => {
  filters.station_id = null
  filters.test_plan_name = null
  testPlanNames.value = []

  if (!projectId) {
    return
  }

  try {
    await projectStore.fetchProjectStations(projectId)
  } catch (error) {
    ElMessage.error('載入站別列表失敗')
  }
}

const handleStationChange = async (stationId) => {
  filters.test_plan_name = null
  testPlanNames.value = []

  if (!stationId || !filters.project_id) {
    return
  }

  try {
    const names = await getStationTestPlanNames(stationId, filters.project_id)
    testPlanNames.value = Array.isArray(names) ? names : []
  } catch (error) {
    ElMessage.error('載入測試計劃列表失敗')
  }
}

const buildQueryParams = () => {
  const params = {
    ...filters,
    limit: pageSize.value,
    offset: (currentPage.value - 1) * pageSize.value
  }

  if (dateRange.value?.length === 2) {
    params.start_date = new Date(`${dateRange.value[0]}T00:00:00`).toISOString()
    params.end_date = new Date(`${dateRange.value[1]}T23:59:59`).toISOString()
  }

  Object.keys(params).forEach((key) => {
    if (params[key] === null || params[key] === undefined || params[key] === '') {
      delete params[key]
    }
  })

  return params
}

const loadSessions = async () => {
  loading.value = true
  try {
    const sessionData = await queryTestSessions(buildQueryParams())
    sessions.value = Array.isArray(sessionData) ? sessionData : []

    if (sessions.value.length < pageSize.value) {
      totalSessions.value = (currentPage.value - 1) * pageSize.value + sessions.value.length
    } else {
      totalSessions.value = currentPage.value * pageSize.value + 1
    }
  } catch (error) {
    ElMessage.error('載入測試記錄失敗')
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  currentPage.value = 1
  await loadSessions()
}

const handleReset = () => {
  filters.project_id = null
  filters.station_id = null
  filters.test_plan_name = null
  filters.final_result = null
  filters.serial_number = null
  dateRange.value = []
  testPlanNames.value = []
  sessions.value = []
  totalSessions.value = 0
  currentPage.value = 1
}

const handlePageChange = async (page) => {
  currentPage.value = page
  await loadSessions()
}

const handleSizeChange = async (size) => {
  pageSize.value = size
  currentPage.value = 1
  await loadSessions()
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

const handleExport = async () => {
  try {
    const blob = await exportTestResults(buildQueryParams())
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `test-results-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.info('匯出功能尚未啟用')
  }
}

const getResultTagType = (result) => {
  const types = {
    PASS: 'success',
    FAIL: 'danger',
    ABORT: 'warning',
    ERROR: 'danger',
    SKIP: 'info'
  }
  return types[result] || 'info'
}

const getResultLabel = (result) => {
  const labels = {
    PASS: '通過',
    FAIL: '失敗',
    ABORT: '中止',
    ERROR: '錯誤',
    SKIP: '略過'
  }
  return labels[result] || result || '-'
}

const getStationById = (stationId) => {
  return projectStore.stations.find((station) => station.id === stationId)
}

const getProjectName = (row) => {
  const station = getStationById(row.station_id)
  if (!station) {
    return row.station?.project?.project_name || '-'
  }
  const project = projectStore.projects.find((item) => item.id === station.project_id)
  return project?.project_name || row.station?.project?.project_name || '-'
}

const getStationName = (row) => {
  const station = getStationById(row.station_id)
  return station?.station_name || row.station?.station_name || `站別 ID: ${row.station_id}`
}

const formatDuration = (seconds) => {
  return `${seconds.toFixed(6)} 秒`
}

const formatDateTime = (dateStr) => {
  if (!dateStr) {
    return '-'
  }
  const date = new Date(dateStr)
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(async () => {
  try {
    await projectStore.fetchProjects()
    await projectStore.fetchAllStations()
    await loadSessions()
  } catch (error) {
    ElMessage.error('初始化資料失敗')
  }
})
</script>

<style scoped>
.test-results-container {
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

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-card :deep(.el-card__body) {
  padding: 15px 20px;
}

.search-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.expanded-content {
  padding: 20px;
}

.expanded-actions {
  margin-top: 15px;
  text-align: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

:deep(.el-table) {
  font-size: 14px;
}

@media (max-width: 992px) {
  .search-actions {
    margin-top: 10px;
  }
}
</style>
