# TestHistory.vue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the TestHistory.vue stub page as a distinct historical timeline view of test sessions, complementing the existing TestResults.vue query page.

**Architecture:**
- TestHistory.vue focuses on **temporal visualization** with timeline charts and day-by-day aggregation
- TestResults.vue focuses on **query-based filtering** for detailed result inspection
- Both share the same backend API (`GET /api/tests/sessions` and `GET /api/tests/sessions/{id}/results`)
- Reuse existing components: AppNavBar.vue, ProjectStationSelector.vue (optional)

**Tech Stack:**
- Vue 3 Composition API (script setup)
- Element Plus UI components
- ECharts 6.0+ for timeline visualization
- Pinia stores (project, auth)
- Axios API client (testResults.js)

**Scope Note:** This plan implements TestHistory.vue as a separate view with distinct functionality from TestResults.vue. The current router redirects `/history` to `/results` — this will be changed to show the new TestHistory.vue page.

---

## File Structure

```
frontend/src/
├── views/
│   └── TestHistory.vue        # MODIFY: Replace stub with full implementation
├── router/
│   └── index.js               # MODIFY: Remove redirect, add proper route
├── components/
│   └── AppNavBar.vue          # MODIFY: Add history button
├── api/
│   └── testResults.js         # REUSE: Existing API functions
└── composables/
    └── useTestHistory.js      # CREATE: History-specific composable
```

---

## Task 0: Create Date Helper Utility (Prerequisite)

**Files:**
- Create: `frontend/src/utils/dateHelpers.js`
- Test: (manual testing in Task 5)

**Purpose:** Shared date normalization utility to avoid timezone inconsistencies.

- [ ] **Step 1: Create the date helper utility**

```javascript
// frontend/src/utils/dateHelpers.js
/**
 * Normalize date string to Asia/Taipei timezone
 * Handles timestamps with or without timezone information
 */
export function normalizeTaipeiDate(dateStr) {
  if (!dateStr) return null
  // Check if already has timezone suffix (Z, +08:00, etc.)
  if (/[Zz]|[+-]\d{2}:?\d{2}$/.test(dateStr)) {
    return dateStr
  }
  // Assume Asia/Taipei timezone if no timezone info
  return dateStr + '+08:00'
}

/**
 * Format date for display (YYYY-MM-DD format for grouping)
 */
export function formatDateKey(dateStr) {
  const normalized = normalizeTaipeiDate(dateStr)
  if (!normalized) return null
  const date = new Date(normalized)
  return date.toISOString().split('T')[0] // YYYY-MM-DD
}
```

- [ ] **Step 2: Verify file created**

Run: `ls -la frontend/src/utils/dateHelpers.js`
Expected: File exists

- [ ] **Step 3: Commit**

```bash
git add frontend/src/utils/dateHelpers.js
git commit -m "feat: add shared date helper utility for timezone handling"
```

---

## Task 1: Create Test History Composable

**Files:**
- Create: `frontend/src/composables/useTestHistory.js`
- Test: (manual testing in Task 5)

**Purpose:** Encapsulate history-specific data fetching and aggregation logic for reuse.

- [ ] **Step 1: Create the composable file**

```javascript
// frontend/src/composables/useTestHistory.js
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { queryTestSessions } from '@/api/testResults'
import { formatDateKey } from '@/utils/dateHelpers'

export function useTestHistory() {
  const sessions = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Group sessions by date for timeline view
  const sessionsByDate = computed(() => {
    const grouped = {}
    sessions.value.forEach(session => {
      const dateKey = formatDateKey(session.start_time)
      if (!dateKey) return
      if (!grouped[dateKey]) {
        grouped[dateKey] = []
      }
      grouped[dateKey].push(session)
    })
    return grouped
  })

  // Calculate daily statistics
  const dailyStats = computed(() => {
    const stats = {}
    Object.entries(sessionsByDate.value).forEach(([date, daySessions]) => {
      stats[date] = {
        total: daySessions.length,
        pass: daySessions.filter(s => s.final_result === 'PASS').length,
        fail: daySessions.filter(s => s.final_result === 'FAIL').length,
        abort: daySessions.filter(s => s.final_result === 'ABORT').length
      }
    })
    return stats
  })

  // Fetch sessions with date range and improved error handling
  const fetchSessions = async (params) => {
    loading.value = true
    error.value = null
    try {
      const data = await queryTestSessions(params)
      sessions.value = Array.isArray(data) ? data : []

      // User feedback for empty results (non-blocking)
      if (sessions.value.length === 0) {
        error.value = 'No sessions found for the selected criteria'
      }
    } catch (err) {
      // Extract meaningful error message from response
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load sessions'
      error.value = errorMsg
      sessions.value = []
      ElMessage.error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  return {
    sessions,
    sessionsByDate,
    dailyStats,
    loading,
    error,
    fetchSessions
  }
}
```

- [ ] **Step 2: Verify file created**

Run: `ls -la frontend/src/composables/useTestHistory.js`
Expected: File exists

- [ ] **Step 3: Commit**

```bash
git add frontend/src/composables/useTestHistory.js
git commit -m "feat: add useTestHistory composable for history view"
```

---

## Task 1.5: Verify ECharts Installation

**Files:**
- Check: `frontend/package.json`
- Test: (verification only)

**Purpose:** Ensure ECharts is available for the optional chart visualization (Task 6).

- [ ] **Step 1: Check if ECharts is installed**

```bash
grep -E '"echarts"|"vue-echarts"' frontend/package.json
```

Expected: Output shows `"echarts": "^6.0.0"` or similar

- [ ] **Step 2: Install if missing**

If grep returns nothing:
```bash
cd frontend && npm install echarts@^6.0.0
```

Note: No commit needed for dependency installation (package.json changes committed separately)

---

## Task 2: Implement TestHistory.vue - Basic Structure

**Files:**
- Modify: `frontend/src/views/TestHistory.vue` (replace entire content)
- Test: (manual testing in Task 5)

- [ ] **Step 1: Replace stub content with basic template**

```vue
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
        <!-- Results content will be added in Task 3 -->
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
```

- [ ] **Step 2: Verify file updated**

Run: `cat frontend/src/views/TestHistory.vue | head -20`
Expected: Vue template with `<div class="test-history-container">`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TestHistory.vue
git commit -m "feat: implement TestHistory.vue basic structure with timeline"
```

---

## Task 3: Add Results Dialog to TestHistory.vue

**Files:**
- Modify: `frontend/src/views/TestHistory.vue` (update dialog section)
- Test: (manual testing in Task 5)

- [ ] **Step 1: Update dialog template**

Replace the placeholder dialog content:

```vue
    <!-- Results Dialog -->
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
```

- [ ] **Step 2: Add formatDateTime helper function to script**

Add to the script section (near other helper functions):

```javascript
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
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TestHistory.vue
git commit -m "feat: add results dialog to TestHistory.vue"
```

---

## Task 4: Update Router Configuration

**Files:**
- Modify: `frontend/src/router/index.js`
- Test: (manual testing in Task 5)

- [ ] **Step 1: Remove redirect and add proper route**

Find and replace the redirect entry:
```javascript
// Current code (lines 28-30):
{
  path: '/history',
  redirect: '/results'
},

// Replace with:
{
  path: '/history',
  name: 'TestHistory',
  component: () => import('@/views/TestHistory.vue'),
  meta: { requiresAuth: true }
},
```

- [ ] **Step 2: Verify router update**

Run: `grep -A2 "path: '/history'" frontend/src/router/index.js`
Expected: Shows `name: 'TestHistory'` and component import

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.js
git commit -m "feat: add TestHistory route, remove redirect to TestResults"
```

---

## Task 5: Update Navigation Bar

**Files:**
- Modify: `frontend/src/components/AppNavBar.vue`
- Test: (manual testing below)

- [ ] **Step 1: Add history button to nav-buttons div**

Add this button after "測試結果查詢" (around line 12):
```vue
          <el-button :type="buttonType('history')" size="default" :disabled="isCurrent('history')" @click="navigateTo('/history')">
            測試歷史記錄
          </el-button>
```

- [ ] **Step 2: Verify nav bar updated**

Run: `grep "測試歷史記錄" frontend/src/components/AppNavBar.vue`
Expected: Shows the new button

- [ ] **Step 3: Test navigation**

```bash
# Start frontend dev server
cd frontend
npm run dev

# In browser:
# 1. Login to the application
# 2. Click "測試歷史記錄" button
# 3. Verify URL changes to /history
# 4. Verify TestHistory page loads with timeline
# 5. Verify date range picker works
# 6. Verify station filter works
# 7. Click expand on a session to see details
# 8. Click "查看詳細結果" to open results dialog
```

Expected: Page loads without errors, navigation works correctly

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/AppNavBar.vue
git commit -m "feat: add TestHistory navigation button to AppNavBar"
```

---

## Task 6: Add ECharts Timeline Visualization (Optional Enhancement)

**Files:**
- Modify: `frontend/src/views/TestHistory.vue`
- Create: `frontend/src/composables/useTestTimeline.js` (optional)

- [ ] **Step 1: Create timeline chart composable**

```javascript
// frontend/src/composables/useTestTimeline.js
import { ref, computed, onUnmounted, onBeforeMount } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import * as echarts from 'echarts'

export function useTestTimeline(sessions) {
  const chartRef = ref(null)
  const chartInstance = ref(null)

  const chartData = computed(() => {
    // Group by date for chart
    const grouped = {}
    sessions.value.forEach(session => {
      const date = new Date(session.start_time).toISOString().split('T')[0]
      if (!grouped[date]) {
        grouped[date] = { pass: 0, fail: 0, abort: 0 }
      }
      if (session.final_result === 'PASS') grouped[date].pass++
      else if (session.final_result === 'FAIL') grouped[date].fail++
      else if (session.final_result === 'ABORT') grouped[date].abort++
    })

    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, counts]) => ({
        date,
        ...counts,
        total: counts.pass + counts.fail + counts.abort
      }))
  })

  const initChart = () => {
    if (!chartRef.value) return

    chartInstance.value = echarts.init(chartRef.value)
    updateChart()

    // Add window resize handler
    window.addEventListener('resize', handleResize)
  }

  const handleResize = () => {
    if (chartInstance.value) {
      chartInstance.value.resize()
    }
  }

  const updateChart = () => {
    if (!chartInstance.value) return

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      legend: {
        data: ['通過', '失敗', '中止']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: chartData.value.map(d => d.date)
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '通過',
          type: 'bar',
          stack: 'total',
          data: chartData.value.map(d => d.pass),
          itemStyle: { color: '#67C23A' }
        },
        {
          name: '失敗',
          type: 'bar',
          stack: 'total',
          data: chartData.value.map(d => d.fail),
          itemStyle: { color: '#F56C6C' }
        },
        {
          name: '中止',
          type: 'bar',
          stack: 'total',
          data: chartData.value.map(d => d.abort),
          itemStyle: { color: '#E6A23C' }
        }
      ]
    }

    chartInstance.value.setOption(option)
  }

  const disposeChart = () => {
    window.removeEventListener('resize', handleResize)
    if (chartInstance.value) {
      chartInstance.value.dispose()
      chartInstance.value = null
    }
  }

  // Cleanup on route leave (Vue Router navigation guard)
  onBeforeRouteLeave(() => {
    disposeChart()
  })

  // Cleanup on component unmount
  onUnmounted(() => {
    disposeChart()
  })

  return {
    chartRef,
    chartData,
    initChart,
    updateChart,
    disposeChart
  }
}
```

- [ ] **Step 2: Add chart to TestHistory.vue template**

Add after stats-row:
```vue
        <!-- Chart Section -->
        <el-card class="chart-card" shadow="never">
          <div ref="chartRef" style="width: 100%; height: 300px"></div>
        </el-card>
```

- [ ] **Step 3: Import and use chart composable**

Add to script setup (after existing imports):
```javascript
import { useTestTimeline } from '@/composables/useTestTimeline'
import { watch, nextTick } from 'vue'

const { chartRef, initChart, updateChart } = useTestTimeline(sessions)

// Update chart when sessions change
watch(sessions, () => {
  updateChart()
}, { deep: true })

// Initialize chart after DOM is ready
const initChartWhenReady = async () => {
  await nextTick()
  setTimeout(initChart, 100) // Small delay to ensure container has size
}
```

Then modify the onMounted function to call chart initialization:
```javascript
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

    // Initialize chart after data loads
    await initChartWhenReady()
  } catch (error) {
    ElMessage.error('初始化失敗')
  }
})
```

- [ ] **Step 4: Add chart styles**

```css
.chart-card {
  margin-bottom: 20px;
}
```

- [ ] **Step 5: Test chart visualization**

```bash
# In browser:
# 1. Navigate to TestHistory page
# 2. Verify bar chart appears with test data
# 3. Hover over bars to see tooltip
# 4. Change date range and verify chart updates
```

Expected: Chart renders correctly with stacked bars showing pass/fail/abort counts

- [ ] **Step 6: Commit**

```bash
git add frontend/src/composables/useTestTimeline.js frontend/src/views/TestHistory.vue
git commit -m "feat: add ECharts timeline visualization to TestHistory"
```

---

## Task 7: Backend Verification (No Changes Required)

**Files:**
- Test: `backend/app/api/tests.py` (existing endpoints)

- [ ] **Step 1: Verify backend endpoints exist**

```bash
# Check if backend is running
curl http://localhost:9100/health

# Test the sessions endpoint (with auth token)
export TOKEN=<your_jwt_token>
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9100/api/tests/sessions?limit=5"
```

Expected: Returns JSON array of test sessions

- [ ] **Step 2: Note existing endpoints**

The following endpoints already exist and are used by TestHistory.vue:
- `GET /api/tests/sessions` - List sessions with filtering
- `GET /api/tests/sessions/{id}/results` - Get detailed results

No backend changes are required for this feature.

- [ ] **Step 3: (Optional) Generate test data**

If the database is empty, generate some test sessions for manual testing:

```bash
# Create a test session (replace TOKEN and station_id)
export TOKEN=<your_jwt_token>
curl -X POST http://localhost:9100/api/tests/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"serial_number": "HISTORY001", "station_id": 1}'

# Start the test session
SESSION_ID=<returned_session_id>
curl -X POST http://localhost:9100/api/tests/sessions/$SESSION_ID/start \
  -H "Authorization: Bearer $TOKEN"
```

---

## Task 8: Documentation Update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update TestHistory.vue status in README**

Find the "前端視圖結構" table and update:
```markdown
| `/history` | TestHistory.vue | 測試歷史記錄（時間軸視圖） | ✅ 完整 |
```

- [ ] **Step 2: Update API 端點列表 section (if needed)**

The existing documentation for `/api/tests/sessions` already covers this feature.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update TestHistory.vue status to complete"
```

---

## Testing Checklist

After completing all tasks, verify the following:

- [ ] Frontend builds without errors: `cd frontend && npm run build`
- [ ] Navigation from AppNavBar works
- [ ] Page loads at `/history` route
- [ ] Date range picker filters sessions correctly
- [ ] Station filter works
- [ ] Timeline displays sessions grouped by date
- [ ] Statistics summary shows correct counts
- [ ] Session details expand on click
- [ ] "查看詳細結果" opens results dialog
- [ ] Results dialog shows all test items
- [ ] Chart visualizes data correctly (if Task 6 completed)
- [ ] No console errors in browser DevTools
- [ ] Responsive design works on mobile viewport

---

## Rollback Instructions

If issues arise, rollback commits in reverse order:

```bash
# Rollback all changes
git reset --hard HEAD~8  # Adjust number based on commits made

# Or rollback specific commits
git revert <commit-hash>
```

---

## Notes for Implementation

1. **Difference from TestResults.vue:**
   - TestResults: Query-focused with filters, pagination, and detailed table view
   - TestHistory: Timeline-focused with date grouping, statistics, and visual summary

2. **Pagination Strategy:**
   - This implementation uses a 500-session limit without pagination controls
   - This is intentional for the "timeline" experience - users see all sessions in the date range
   - If performance issues arise with large datasets, consider:
     a) Adding pagination (similar to TestResults.vue), OR
     b) Reducing the default limit and adding a "Load More" button, OR
     c) Implementing virtual scrolling for the timeline

3. **API Reuse:**
   - Both pages use the same backend endpoints
   - Consider adding request caching if performance issues arise

4. **Timezone Handling:**
   - Uses the shared `normalizeTaipeiDate()` utility for consistency
   - Backend stores timestamps in Asia/Taipei timezone
   - Frontend assumes +08:00 offset for timestamps without timezone info

5. **Future Enhancements:**
   - Add WebSocket for real-time updates
   - Add export to PDF feature
   - Add trend analysis charts
   - Add search by serial number with autocomplete

---

**Plan End**
