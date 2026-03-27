# Merge Test Views Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate TestResults.vue, TestHistory.vue, and ReportAnalysis.vue into a single unified TestResults.vue using tabs — one page with three focused tab panels.

**Architecture:** Replace the three separate pages/routes with one `/results` page that uses `el-tabs` to switch between: (1) 查詢結果 (table search + session detail dialog — existing TestResults content), (2) 歷史趨勢 (timeline chart + daily collapse groups — existing TestHistory content), and (3) 報表分析 (statistical analysis chart — existing ReportAnalysis content). All composables and API modules are kept unchanged; only the view layer merges.

**Tech Stack:** Vue 3, Element Plus (`el-tabs`, `el-tab-pane`), ECharts (via `echarts` direct import for timeline, via `vue-echarts` for analysis line chart), Pinia project store.

---

## File Map

| File | Action | Notes |
|------|--------|-------|
| `frontend/src/views/TestResults.vue` | **Rewrite** | Unified 3-tab view |
| `frontend/src/views/TestHistory.vue` | **Delete** | Content merged into TestResults |
| `frontend/src/views/ReportAnalysis.vue` | **Delete** | Content merged into TestResults |
| `frontend/src/router/index.js` | **Modify** | Remove `/history` and `/analysis` routes |
| `frontend/src/components/AppNavBar.vue` | **Modify** | Remove 歷史記錄 and 報表分析 buttons |

**Composables / API kept as-is (no changes):**
- `frontend/src/composables/useTestHistory.js`
- `frontend/src/composables/useTestTimeline.js`
- `frontend/src/api/testResults.js`
- `frontend/src/api/analysis.js`
- `frontend/src/api/testplans.js`

---

## Task 1: Rewrite TestResults.vue as a Unified 3-Tab View

**Files:**
- Modify: `frontend/src/views/TestResults.vue`

### Tab 1 — 查詢結果 (existing TestResults content)
Filters: project → station → test plan name → result type → serial number → date range → Search/Reset buttons.
Table: Session ID, serial number, project/station, test plan, result tag, stats, start time. Expand row → descriptions + 查看詳細結果 button. Pagination. Admin delete + export buttons in card header.

### Tab 2 — 歷史趨勢 (existing TestHistory content)
Filters: date range, project select, station select, Search/Reset buttons + Refresh.
Statistics summary row (total, pass, fail, pass rate).
ECharts stacked-bar chart (uses `useTestTimeline` composable).
`el-timeline` grouped by date with collapse items per session.

### Tab 3 — 報表分析 (existing ReportAnalysis content)
Filters: project → station → test plan name → date from → date to → 查詢 button.
Session stats card (mean/median/stdev/MAD in seconds).
Item name filter select.
Item stats table (item_no, item_name, sample count, mean/median/stdev/MAD in ms).
ECharts line chart (uses `vue-echarts` VChart component).

### Tab switching behavior
- Active tab is tracked in `activeTab` ref (default `'query'`).
- When switching TO `'history'` tab: if sessions are empty, trigger `loadHistorySessions()`. If chart DOM just became visible, call `initChartWhenReady()`.
- The ECharts timeline chart requires the DOM container to be visible before `initChart()`. Use `watch(activeTab, async (val) => { if (val === 'history') { await nextTick(); setTimeout(initChart, 100) } })`.

- [ ] **Step 1: Write the new TestResults.vue**

Replace the entire file with the unified 3-tab implementation below. The `<script setup>` combines all imports and state from all three original files. The `<template>` uses `<el-tabs v-model="activeTab">` with three `<el-tab-pane>` children.

```vue
<template>
  <div class="test-results-container">
    <AppNavBar current-page="results" />

    <el-card>
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">

        <!-- ===== Tab 1: 查詢結果 ===== -->
        <el-tab-pane label="查詢結果" name="query">
          <template #label>
            <span>查詢結果</span>
          </template>

          <div class="tab-header-actions">
            <el-button
              v-if="isAdmin"
              type="danger"
              :icon="Delete"
              :disabled="selectedSessions.length === 0"
              :loading="deleting"
              @click="handleBulkDelete"
            >
              刪除選取 ({{ selectedSessions.length }})
            </el-button>
            <el-button
              type="success"
              :icon="Download"
              :disabled="sessions.length === 0"
              @click="handleExport"
            >
              匯出結果
            </el-button>
          </div>

          <!-- Query Filters -->
          <el-card class="filter-card" shadow="never">
            <el-form :model="queryFilters" label-width="100px">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-form-item label="專案">
                    <el-select
                      v-model="queryFilters.project_id"
                      placeholder="選擇專案"
                      clearable filterable style="width: 100%"
                      @change="handleQueryProjectChange"
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
                      v-model="queryFilters.station_id"
                      placeholder="選擇站別"
                      clearable filterable
                      :disabled="!queryFilters.project_id"
                      style="width: 100%"
                      @change="handleQueryStationChange"
                    >
                      <el-option
                        v-for="station in queryFilteredStations"
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
                      v-model="queryFilters.test_plan_name"
                      placeholder="選擇測試計劃"
                      clearable filterable
                      :disabled="!queryFilters.station_id"
                      style="width: 100%"
                    >
                      <el-option v-for="name in queryTestPlanNames" :key="name" :label="name" :value="name" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="測試結果">
                    <el-select v-model="queryFilters.final_result" placeholder="選擇結果" clearable style="width: 100%">
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
                    <el-input v-model="queryFilters.serial_number" placeholder="輸入序號" clearable />
                  </el-form-item>
                </el-col>
                <el-col :span="10">
                  <el-form-item label="日期範圍">
                    <el-date-picker
                      v-model="queryDateRange"
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
                  <el-button type="primary" :loading="queryLoading" @click="handleQuerySearch">查詢</el-button>
                  <el-button @click="handleQueryReset">重置</el-button>
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
            v-loading="queryLoading"
            stripe
            style="width: 100%"
            @selection-change="handleSelectionChange"
          >
            <el-table-column v-if="isAdmin" type="selection" width="50" />
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="expanded-content">
                  <el-descriptions :column="3" border>
                    <el-descriptions-item label="專案">{{ getProjectName(row) }}</el-descriptions-item>
                    <el-descriptions-item label="站別">{{ getStationName(row) }}</el-descriptions-item>
                    <el-descriptions-item label="測試計劃">{{ row.test_plan_name || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="開始時間">{{ formatDateTime(row.start_time) }}</el-descriptions-item>
                    <el-descriptions-item label="結束時間">{{ row.end_time ? formatDateTime(row.end_time) : '進行中' }}</el-descriptions-item>
                    <el-descriptions-item label="測試時長">{{ row.test_duration_seconds ? formatDuration(row.test_duration_seconds) : '-' }}</el-descriptions-item>
                    <el-descriptions-item label="總項目">{{ row.total_items || 0 }}</el-descriptions-item>
                    <el-descriptions-item label="通過"><el-text type="success">{{ row.pass_items || 0 }}</el-text></el-descriptions-item>
                    <el-descriptions-item label="失敗"><el-text type="danger">{{ row.fail_items || 0 }}</el-text></el-descriptions-item>
                  </el-descriptions>
                  <div class="expanded-actions">
                    <el-button type="primary" size="small" @click="handleViewResults(row)">查看詳細結果</el-button>
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
              <template #default="{ row }">{{ row.test_plan_name || '-' }}</template>
            </el-table-column>
            <el-table-column label="結果" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.final_result" :type="getResultTagType(row.final_result)">{{ getResultLabel(row.final_result) }}</el-tag>
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
              <template #default="{ row }">{{ formatDateTime(row.start_time) }}</template>
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
        </el-tab-pane>

        <!-- ===== Tab 2: 歷史趨勢 ===== -->
        <el-tab-pane label="歷史趨勢" name="history">
          <el-card class="filter-card" shadow="never">
            <el-row :gutter="20" align="middle">
              <el-col :span="8">
                <el-date-picker
                  v-model="historyDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="開始日期"
                  end-placeholder="結束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-col>
              <el-col :span="5">
                <el-select v-model="historyProject" placeholder="全部專案" clearable style="width: 100%">
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
                  v-model="historyStation"
                  placeholder="全部站別"
                  clearable
                  :disabled="!historyProject"
                  style="width: 100%"
                >
                  <el-option
                    v-for="station in historyFilteredStations"
                    :key="station.id"
                    :label="station.station_name"
                    :value="station.id"
                  />
                </el-select>
              </el-col>
              <el-col :span="6">
                <el-button type="primary" :loading="historyLoading" @click="handleHistorySearch">查詢</el-button>
                <el-button @click="handleHistoryReset">重置</el-button>
                <el-button @click="handleHistoryRefresh" :loading="historyLoading">重新整理</el-button>
              </el-col>
            </el-row>
          </el-card>

          <el-skeleton v-if="historyLoading && historySessions.length === 0" :rows="5" animated />
          <el-empty v-else-if="!historyLoading && historySessions.length === 0" description="暫無測試記錄" />

          <div v-else class="timeline-content">
            <!-- Statistics Summary -->
            <el-card class="stats-card" shadow="never">
              <el-row :gutter="0" class="stats-row">
                <el-col :span="6" class="stat-col stat-col--total">
                  <el-statistic title="總測試次數" :value="historyPassCount + historyFailCount + historyAbortCount" />
                </el-col>
                <el-col :span="6" class="stat-col stat-col--pass">
                  <el-statistic title="通過" :value="historyPassCount" :value-style="{ color: '#67C23A' }" />
                </el-col>
                <el-col :span="6" class="stat-col stat-col--fail">
                  <el-statistic title="失敗" :value="historyFailCount" :value-style="{ color: '#F56C6C' }" />
                </el-col>
                <el-col :span="6" class="stat-col stat-col--rate">
                  <el-statistic
                    title="通過率"
                    :value="historyPassRate"
                    suffix="%"
                    :value-style="historyPassRateStyle"
                  />
                </el-col>
              </el-row>
            </el-card>

            <!-- Chart -->
            <el-card class="chart-card" shadow="never">
              <div ref="chartRef" class="chart-container"></div>
            </el-card>

            <!-- Timeline -->
            <el-timeline class="history-timeline">
              <el-timeline-item
                v-for="(daySessions, date) in historySessionsByDate"
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
                    <el-text type="success">通過: {{ historyDailyStats[date].pass }}</el-text>
                    <el-text type="danger">失敗: {{ historyDailyStats[date].fail }}</el-text>
                    <el-text type="warning">中止: {{ historyDailyStats[date].abort }}</el-text>
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
                        <p><strong>站別:</strong> {{ getStationNameById(session.station_id) }}</p>
                        <p><strong>測試計劃:</strong> {{ session.test_plan_name || '-' }}</p>
                        <p><strong>統計:</strong>
                          通過 {{ session.pass_items || 0 }} /
                          失敗 {{ session.fail_items || 0 }} /
                          總計 {{ session.total_items || 0 }}
                        </p>
                        <p v-if="session.test_duration_seconds">
                          <strong>時長:</strong> {{ session.test_duration_seconds.toFixed(2) }} 秒
                        </p>
                        <el-button type="primary" size="small" @click="handleViewResults(session)">查看詳細結果</el-button>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>

        <!-- ===== Tab 3: 報表分析 ===== -->
        <el-tab-pane label="報表分析" name="analysis">
          <el-card class="filter-card" shadow="never">
            <el-form :inline="true" :model="analysisFilters" label-width="80px">
              <el-form-item label="專案">
                <el-select
                  v-model="analysisFilters.project_id"
                  placeholder="選擇專案"
                  clearable
                  @change="onAnalysisProjectChange"
                  style="width: 160px"
                >
                  <el-option v-for="p in projectStore.projects" :key="p.id" :label="p.project_name" :value="p.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="站別">
                <el-select
                  v-model="analysisFilters.station_id"
                  placeholder="選擇站別"
                  clearable
                  :disabled="!analysisFilters.project_id"
                  @change="onAnalysisStationChange"
                  style="width: 160px"
                >
                  <el-option v-for="s in analysisStationList" :key="s.id" :label="s.station_name" :value="s.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="測試腳本">
                <el-select
                  v-model="analysisFilters.test_plan_name"
                  placeholder="選擇測試腳本"
                  clearable
                  :disabled="!analysisFilters.station_id"
                  :loading="analysisLoadingPlans"
                  style="width: 200px"
                >
                  <el-option v-for="name in analysisTestPlanNames" :key="name" :label="name" :value="name" />
                </el-select>
              </el-form-item>
              <el-form-item label="開始日期">
                <el-date-picker v-model="analysisFilters.date_from" type="date" placeholder="From" value-format="YYYY-MM-DD" style="width: 140px" />
              </el-form-item>
              <el-form-item label="結束日期">
                <el-date-picker v-model="analysisFilters.date_to" type="date" placeholder="To" value-format="YYYY-MM-DD" style="width: 140px" />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="analysisLoading"
                  :disabled="!analysisFilters.station_id || !analysisFilters.test_plan_name"
                  @click="fetchAnalysis"
                >
                  查詢
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- Session stats -->
          <el-card v-if="sessionStats && sessionStats.sample_count > 0" style="margin-bottom: 16px">
            <template #header><span>總執行時間統計（秒）- 樣本數：{{ sessionStats.sample_count }}</span></template>
            <el-row :gutter="20">
              <el-col :span="6" v-for="stat in sessionStatItems" :key="stat.label">
                <div class="stat-card">
                  <div class="stat-label">{{ stat.label }}</div>
                  <div class="stat-value">{{ stat.value ?? 'N/A' }}</div>
                </div>
              </el-col>
            </el-row>
          </el-card>

          <!-- Item filter -->
          <el-card v-if="itemStats.length > 0" style="margin-bottom: 16px">
            <el-form :inline="true" label-width="80px">
              <el-form-item label="項目名稱">
                <el-select v-model="selectedItemNo" placeholder="選擇項目（可選，不選則顯示全部）" clearable style="width: 320px">
                  <el-option v-for="opt in itemOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- Item stats table -->
          <el-card v-if="itemStats.length > 0" style="margin-bottom: 16px">
            <template #header><span>各測試項目執行時間統計（ms）</span></template>
            <el-table :data="filteredItemStats" stripe border style="width: 100%">
              <el-table-column prop="item_no" label="項次" width="70" align="center" />
              <el-table-column prop="item_name" label="項目名稱" min-width="200" />
              <el-table-column prop="sample_count" label="樣本數" width="80" align="right" />
              <el-table-column prop="mean_ms" label="平均 (ms)" width="110" align="right">
                <template #default="{ row }">{{ fmtNum(row.mean_ms) }}</template>
              </el-table-column>
              <el-table-column prop="median_ms" label="中位數 (ms)" width="110" align="right">
                <template #default="{ row }">{{ fmtNum(row.median_ms) }}</template>
              </el-table-column>
              <el-table-column prop="stdev_ms" label="標準差 (ms)" width="110" align="right">
                <template #default="{ row }">{{ fmtNum(row.stdev_ms) }}</template>
              </el-table-column>
              <el-table-column prop="mad_ms" label="MAD (ms)" width="110" align="right">
                <template #default="{ row }">{{ fmtNum(row.mad_ms) }}</template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- Line chart -->
          <el-card v-if="analysisChartOption" style="margin-bottom: 16px">
            <template #header><span>執行時間趨勢圖</span></template>
            <v-chart :option="analysisChartOption" style="height: 320px" autoresize />
          </el-card>

          <el-empty v-else-if="analysisQueried && itemStats.length === 0" description="此條件無資料" />
        </el-tab-pane>

      </el-tabs>
    </el-card>

    <!-- Session Detail Dialog (shared by all tabs) -->
    <el-dialog v-model="showResultsDialog" title="測試結果詳情" width="90%" top="5vh">
      <div v-if="selectedSession">
        <el-descriptions :column="2" border style="margin-bottom: 20px">
          <el-descriptions-item label="Session ID">{{ selectedSession.id }}</el-descriptions-item>
          <el-descriptions-item label="序號">{{ selectedSession.serial_number }}</el-descriptions-item>
          <el-descriptions-item label="專案">{{ getProjectName(selectedSession) }}</el-descriptions-item>
          <el-descriptions-item label="站別">{{ getStationName(selectedSession) }}</el-descriptions-item>
          <el-descriptions-item label="測試計劃">{{ selectedSession.test_plan_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="最終結果">
            <el-tag v-if="selectedSession.final_result" :type="getResultTagType(selectedSession.final_result)">
              {{ getResultLabel(selectedSession.final_result) }}
            </el-tag>
            <el-text v-else type="info">進行中</el-text>
          </el-descriptions-item>
        </el-descriptions>

        <el-alert
          v-if="!resultsLoading && sessionResults.length === 0"
          title="此 Session 無測試項目明細"
          type="info"
          :closable="false"
          style="margin-bottom: 12px"
        />
        <el-table v-else :data="sessionResults" v-loading="resultsLoading" stripe max-height="500">
          <el-table-column prop="item_no" label="項次" width="80" />
          <el-table-column prop="item_name" label="測試項目" min-width="120" />
          <el-table-column prop="measured_value" label="測量值" min-width="340">
            <template #default="{ row }">
              <span style="white-space: pre-wrap; word-break: break-all;">{{ row.measured_value }}</span>
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
          <el-table-column prop="unit" label="單位" width="80" />
          <el-table-column label="結果" width="100">
            <template #default="{ row }">
              <el-tag :type="getResultTagType(row.result)">{{ row.result }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="執行時間" width="120">
            <template #default="{ row }">
              {{ row.execution_duration_ms != null ? `${(row.execution_duration_ms / 1000).toFixed(3)} s` : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="Wall Time" width="120">
            <template #default="{ row }">
              {{ row.wall_time_ms != null ? `${(row.wall_time_ms / 1000).toFixed(3)} s` : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="Overhead" width="110">
            <template #default="{ row }">
              <span v-if="row.wall_time_ms != null && row.execution_duration_ms != null" style="color: #909399">
                {{ ((row.wall_time_ms - row.execution_duration_ms) / 1000).toFixed(3) }} s
              </span>
              <span v-else>-</span>
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
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import AppNavBar from '@/components/AppNavBar.vue'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { queryTestSessions, getSessionWithResults, exportTestResults, deleteTestSessions } from '@/api/testResults'
import { getStationTestPlanNames } from '@/api/testplans'
import { getAnalysis } from '@/api/analysis'
import apiClient from '@/api/client'
import { useTestHistory } from '@/composables/useTestHistory'
import { useTestTimeline } from '@/composables/useTestTimeline'
import { normalizeTaipeiDate } from '@/utils/dateHelpers'

use([LineChart, GridComponent, TooltipComponent, TitleComponent, LegendComponent, CanvasRenderer])

const CHART_INIT_DELAY_MS = 100

// ── Stores ──────────────────────────────────────────────────────────────────
const projectStore = useProjectStore()
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

// ── Tab state ────────────────────────────────────────────────────────────────
const activeTab = ref('query')

// ── Shared: Session detail dialog ────────────────────────────────────────────
const showResultsDialog = ref(false)
const selectedSession = ref(null)
const sessionResults = ref([])
const resultsLoading = ref(false)

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

// ── Tab 1: Query state ───────────────────────────────────────────────────────
const queryFilters = reactive({
  project_id: null,
  station_id: null,
  test_plan_name: null,
  final_result: null,
  serial_number: null
})
const queryDateRange = ref([])
const queryTestPlanNames = ref([])
const sessions = ref([])
const queryLoading = ref(false)
const totalSessions = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const selectedSessions = ref([])
const deleting = ref(false)

const queryFilteredStations = computed(() => {
  if (!queryFilters.project_id) return []
  return projectStore.stations.filter(s => s.project_id === queryFilters.project_id)
})

const handleQueryProjectChange = async (projectId) => {
  queryFilters.station_id = null
  queryFilters.test_plan_name = null
  queryTestPlanNames.value = []
  if (!projectId) return
  try {
    await projectStore.fetchProjectStations(projectId)
  } catch {
    ElMessage.error('載入站別列表失敗')
  }
}

const handleQueryStationChange = async (stationId) => {
  queryFilters.test_plan_name = null
  queryTestPlanNames.value = []
  if (!stationId || !queryFilters.project_id) return
  try {
    const names = await getStationTestPlanNames(stationId, queryFilters.project_id)
    queryTestPlanNames.value = Array.isArray(names) ? names : []
  } catch {
    ElMessage.error('載入測試計劃列表失敗')
  }
}

const buildQueryParams = () => {
  const params = {
    ...queryFilters,
    limit: pageSize.value,
    offset: (currentPage.value - 1) * pageSize.value
  }
  if (queryDateRange.value?.length === 2) {
    params.start_date = new Date(`${queryDateRange.value[0]}T00:00:00`).toISOString()
    params.end_date = new Date(`${queryDateRange.value[1]}T23:59:59`).toISOString()
  }
  Object.keys(params).forEach(key => {
    if (params[key] === null || params[key] === undefined || params[key] === '') delete params[key]
  })
  return params
}

const loadSessions = async () => {
  queryLoading.value = true
  try {
    const data = await queryTestSessions(buildQueryParams())
    sessions.value = Array.isArray(data) ? data : []
    if (sessions.value.length < pageSize.value) {
      totalSessions.value = (currentPage.value - 1) * pageSize.value + sessions.value.length
    } else {
      totalSessions.value = currentPage.value * pageSize.value + 1
    }
  } catch {
    ElMessage.error('載入測試記錄失敗')
  } finally {
    queryLoading.value = false
  }
}

const handleQuerySearch = async () => { currentPage.value = 1; await loadSessions() }
const handleQueryReset = () => {
  queryFilters.project_id = null
  queryFilters.station_id = null
  queryFilters.test_plan_name = null
  queryFilters.final_result = null
  queryFilters.serial_number = null
  queryDateRange.value = []
  queryTestPlanNames.value = []
  sessions.value = []
  totalSessions.value = 0
  currentPage.value = 1
}
const handlePageChange = async (page) => { currentPage.value = page; await loadSessions() }
const handleSizeChange = async (size) => { pageSize.value = size; currentPage.value = 1; await loadSessions() }
const handleSelectionChange = (rows) => { selectedSessions.value = rows }

const handleBulkDelete = async () => {
  if (selectedSessions.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `確定要刪除選取的 ${selectedSessions.value.length} 筆測試記錄及其所有測試結果？此操作無法復原。`,
      '刪除確認',
      { type: 'warning', confirmButtonText: '確定刪除', cancelButtonText: '取消' }
    )
  } catch { return }
  deleting.value = true
  try {
    const ids = selectedSessions.value.map(s => s.id)
    await deleteTestSessions(ids)
    ElMessage.success(`已刪除 ${ids.length} 筆測試記錄`)
    selectedSessions.value = []
    await loadSessions()
  } catch {
    ElMessage.error('刪除失敗，請稍後再試')
  } finally {
    deleting.value = false
  }
}

const handleExport = async () => {
  try {
    const response = await exportTestResults(buildQueryParams())
    const blob = response instanceof Blob ? response : new Blob([response])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `test-results-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('匯出成功')
  } catch {
    ElMessage.error('匯出失敗，請稍後再試')
  }
}

// ── Tab 2: History state ─────────────────────────────────────────────────────
const { sessions: historySessions, sessionsByDate: historySessionsByDate, dailyStats: historyDailyStats, loading: historyLoading, fetchSessions: fetchHistorySessions } = useTestHistory()
const { chartRef, initChart, updateChart } = useTestTimeline(historySessions)

const historyDateRange = ref([])
const historyProject = ref(null)
const historyStation = ref(null)

const historyFilteredStations = computed(() => {
  if (!historyProject.value) return projectStore.stations
  return projectStore.stations.filter(s => s.project_id === historyProject.value)
})

watch(historyProject, () => { historyStation.value = null })

const historyPassCount = computed(() => historySessions.value.filter(s => s.final_result === 'PASS').length)
const historyFailCount = computed(() => historySessions.value.filter(s => s.final_result === 'FAIL').length)
const historyAbortCount = computed(() => historySessions.value.filter(s => s.final_result === 'ABORT').length)
const historyPassRate = computed(() => {
  const total = historySessions.value.length
  if (total === 0) return 0
  return ((historyPassCount.value / total) * 100).toFixed(1)
})
const historyPassRateStyle = computed(() => {
  const rate = parseFloat(historyPassRate.value)
  if (rate >= 90) return { color: '#67C23A', fontWeight: '600' }
  if (rate >= 70) return { color: '#E6A23C', fontWeight: '600' }
  return { color: '#F56C6C', fontWeight: '600' }
})

const buildHistoryParams = () => {
  const params = { limit: 500, offset: 0 }
  if (historyStation.value) params.station_id = historyStation.value
  if (historyProject.value) params.project_id = historyProject.value
  if (historyDateRange.value?.length === 2) {
    params.start_date = new Date(`${historyDateRange.value[0]}T00:00:00`).toISOString()
    params.end_date = new Date(`${historyDateRange.value[1]}T23:59:59`).toISOString()
  }
  return params
}

const loadHistorySessions = async () => { await fetchHistorySessions(buildHistoryParams()) }

const handleHistorySearch = () => loadHistorySessions()
const handleHistoryRefresh = () => loadHistorySessions()
const handleHistoryReset = () => {
  historyProject.value = null
  historyStation.value = null
  historyDateRange.value = []
  loadHistorySessions()
}

// Re-init chart when sessions change (DOM may be re-created when going empty → non-empty)
watch(historySessions, async (newVal, oldVal) => {
  const wasEmpty = !oldVal || oldVal.length === 0
  const nowHasData = newVal && newVal.length > 0
  if (wasEmpty && nowHasData) {
    await nextTick()
    setTimeout(initChart, CHART_INIT_DELAY_MS)
  } else {
    updateChart()
  }
}, { deep: true })

// When switching to history tab, init chart if data already exists
const handleTabChange = async (tabName) => {
  if (tabName === 'history' && historySessions.value.length > 0) {
    await nextTick()
    setTimeout(initChart, CHART_INIT_DELAY_MS)
  }
}

// ── Tab 3: Analysis state ────────────────────────────────────────────────────
const analysisFilters = ref({
  project_id: null,
  station_id: null,
  test_plan_name: null,
  date_from: null,
  date_to: null
})
const analysisStationList = ref([])
const analysisTestPlanNames = ref([])
const analysisLoadingPlans = ref(false)
const analysisLoading = ref(false)
const analysisQueried = ref(false)
const itemStats = ref([])
const sessionStats = ref(null)
const selectedItemNo = ref(null)
const itemSeries = ref([])

const sessionStatItems = computed(() => {
  if (!sessionStats.value) return []
  const s = sessionStats.value
  return [
    { label: '平均數', value: s.mean_s },
    { label: '中位數', value: s.median_s },
    { label: '標準差', value: s.stdev_s },
    { label: 'MAD', value: s.mad_s }
  ]
})

const itemOptions = computed(() =>
  (itemStats.value || []).map(i => ({ label: `${i.item_no}. ${i.item_name}`, value: i.item_no }))
)

const filteredItemStats = computed(() => {
  if (selectedItemNo.value === null) return itemStats.value
  return itemStats.value.filter(i => i.item_no === selectedItemNo.value)
})

const analysisChartOption = computed(() => {
  if (selectedItemNo.value === null) return null
  const series = itemSeries.value.find(s => s.item_no === selectedItemNo.value)
  if (!series || !series.sessions.length) return null
  const xData = series.sessions.map(s => s.start_time ? s.start_time.slice(0, 16).replace('T', ' ') : '')
  const yData = series.sessions.map(s => s.duration_ms ?? null)
  return {
    title: {
      text: `${series.item_name} — 每次 Session 執行時間`,
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: params => `${params[0].axisValue}<br/>執行時間: ${params[0].value ?? 'N/A'} ms`
    },
    xAxis: { type: 'category', data: xData, axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: 'value', name: 'ms', nameTextStyle: { fontSize: 11 } },
    series: [{ type: 'line', data: yData, smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { width: 2 }, itemStyle: { color: '#409EFF' } }],
    grid: { left: 60, right: 20, bottom: 60, top: 60 }
  }
})

const onAnalysisProjectChange = async () => {
  analysisFilters.value.station_id = null
  analysisFilters.value.test_plan_name = null
  analysisTestPlanNames.value = []
  analysisStationList.value = []
  if (!analysisFilters.value.project_id) return
  await projectStore.fetchProjectStations(analysisFilters.value.project_id)
  analysisStationList.value = projectStore.stations || []
}

const onAnalysisStationChange = async () => {
  analysisFilters.value.test_plan_name = null
  analysisTestPlanNames.value = []
  if (!analysisFilters.value.station_id) return
  analysisLoadingPlans.value = true
  try {
    const res = await apiClient.get(`/api/stations/${analysisFilters.value.station_id}/testplan-names`)
    analysisTestPlanNames.value = Array.isArray(res) ? res : []
  } catch {
    ElMessage.error('載入測試腳本失敗')
  } finally {
    analysisLoadingPlans.value = false
  }
}

const fetchAnalysis = async () => {
  analysisLoading.value = true
  analysisQueried.value = false
  itemStats.value = []
  sessionStats.value = null
  itemSeries.value = []
  selectedItemNo.value = null
  try {
    const params = {
      station_id: analysisFilters.value.station_id,
      test_plan_name: analysisFilters.value.test_plan_name
    }
    if (analysisFilters.value.date_from) params.date_from = analysisFilters.value.date_from
    if (analysisFilters.value.date_to) params.date_to = analysisFilters.value.date_to
    const res = await getAnalysis(params)
    itemStats.value = res.item_stats || []
    sessionStats.value = res.session_stats || null
    itemSeries.value = res.item_series || []
    analysisQueried.value = true
  } catch {
    ElMessage.error('查詢失敗，請確認篩選條件')
  } finally {
    analysisLoading.value = false
  }
}

// ── Shared helper functions ──────────────────────────────────────────────────
const fmtNum = (val) => (val !== null && val !== undefined ? val : 'N/A')

const getResultTagType = (result) => {
  const types = { PASS: 'success', FAIL: 'danger', ABORT: 'warning', ERROR: 'danger', SKIP: 'info' }
  return types[result] || 'info'
}

const getResultLabel = (result) => {
  const labels = { PASS: '通過', FAIL: '失敗', ABORT: '中止', ERROR: '錯誤', SKIP: '略過' }
  return labels[result] || result || '-'
}

const getStationById = (stationId) => projectStore.stations.find(s => s.id === stationId)

const getProjectName = (row) => {
  const station = getStationById(row.station_id)
  if (!station) return row.station?.project?.project_name || '-'
  const project = projectStore.projects.find(p => p.id === station.project_id)
  return project?.project_name || row.station?.project?.project_name || '-'
}

const getStationName = (row) => {
  const station = getStationById(row.station_id)
  return station?.station_name || row.station?.station_name || `站別 ID: ${row.station_id}`
}

const getStationNameById = (stationId) => {
  const station = getStationById(stationId)
  return station?.station_name || `站別 ${stationId}`
}

const formatDuration = (seconds) => `${seconds.toFixed(6)} 秒`

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const normalized = /[Zz]|[+-]\d{2}:?\d{2}$/.test(dateStr) ? dateStr : dateStr + '+08:00'
  const date = new Date(normalized)
  return date.toLocaleString('zh-TW', {
    timeZone: 'Asia/Taipei',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
}

const formatTime = (dateStr) => {
  const normalized = normalizeTaipeiDate(dateStr)
  if (!normalized) return '-'
  const date = new Date(normalized)
  return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// ── Initialize ───────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    await projectStore.fetchProjects()
    await projectStore.fetchAllStations()

    // Tab 1: load first page
    await loadSessions()

    // Tab 2: set default date range (last 7 days) and load history
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 7)
    historyDateRange.value = [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
    await loadHistorySessions()
  } catch {
    ElMessage.error('初始化失敗')
  }
})
</script>

<style scoped>
.test-results-container {
  padding: 20px;
}

.tab-header-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
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

/* History tab */
.timeline-content {
  margin-top: 20px;
}

.stats-card {
  margin-bottom: 20px;
  background: #fafafa;
}

.stats-card :deep(.el-card__body) {
  padding: 20px 0;
}

.stat-col {
  padding: 8px 24px;
  text-align: center;
}

.stat-col--pass,
.stat-col--fail,
.stat-col--rate {
  border-left: 1px solid #e4e7ed;
}

.stats-card :deep(.el-statistic__number) {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.3;
}

.stats-card :deep(.el-statistic__head) {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 380px;
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

/* Analysis tab */
.stat-card {
  text-align: center;
  padding: 16px 8px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 22px;
  font-weight: bold;
  color: #303133;
}

:deep(.el-table) {
  font-size: 14px;
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

@media (max-width: 992px) {
  .search-actions {
    margin-top: 10px;
  }
}

@media (max-width: 768px) {
  .test-results-container {
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

- [ ] **Step 2: Verify the file saved correctly**

```bash
wc -l frontend/src/views/TestResults.vue
```
Expected: ~500+ lines (well over original 704 due to merged content).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TestResults.vue
git commit -m "feat: merge TestHistory and ReportAnalysis into TestResults as tabs"
```

---

## Task 2: Remove Obsolete Routes and Nav Buttons

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/AppNavBar.vue`
- Delete: `frontend/src/views/TestHistory.vue`
- Delete: `frontend/src/views/ReportAnalysis.vue`

- [ ] **Step 1: Remove /history and /analysis routes from router/index.js**

In `frontend/src/router/index.js`, remove these two route objects:

```js
// REMOVE these two objects:
  {
    path: '/history',
    name: 'TestHistory',
    component: () => import('@/views/TestHistory.vue'),
    meta: { requiresAuth: true }
  },
  // ...and...
  {
    path: '/analysis',
    name: 'ReportAnalysis',
    component: () => import('@/views/ReportAnalysis.vue'),
    meta: { requiresAuth: true }
  },
```

After removal the routes array should have entries for: login, main, test, results, testplan, config, projects, users, instruments, modbus-config.

- [ ] **Step 2: Remove 歷史記錄 and 報表分析 buttons from AppNavBar.vue**

In `frontend/src/components/AppNavBar.vue`, remove these two `<el-button>` elements:

```html
<!-- REMOVE: -->
<el-button :type="buttonType('history')" size="default" :disabled="isCurrent('history')" @click="navigateTo('/history')">
  測試歷史記錄
</el-button>
<!-- REMOVE: -->
<el-button :type="buttonType('analysis')" size="default" :disabled="isCurrent('analysis')" @click="navigateTo('/analysis')">
  報表分析
</el-button>
```

- [ ] **Step 3: Delete the now-unused view files**

```bash
rm frontend/src/views/TestHistory.vue
rm frontend/src/views/ReportAnalysis.vue
```

- [ ] **Step 4: Delete the now-unused composables (if no other consumers)**

Check whether `useTestHistory` and `useTestTimeline` are still imported anywhere other than the new TestResults.vue:

```bash
grep -r "useTestHistory\|useTestTimeline" frontend/src --include="*.vue" --include="*.js" -l
```

Expected output: only `frontend/src/views/TestResults.vue` and `frontend/src/composables/useTestTimeline.js` (the composable files themselves). The composables are still used by TestResults.vue — **do NOT delete them**.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/router/index.js frontend/src/components/AppNavBar.vue
git commit -m "feat: remove obsolete TestHistory and ReportAnalysis routes and nav buttons"
```

---

## Task 3: Smoke Test in Browser

**Prerequisites:** Docker services running (`docker-compose up -d`) or local dev server (`npm run dev`).

- [ ] **Step 1: Open the app and navigate to 測試結果查詢**

Open `http://localhost:9080` (Docker) or `http://localhost:5678` (dev).

Verify:
- NavBar no longer shows 測試歷史記錄 or 報表分析 buttons.
- Navigating to `/history` or `/analysis` should redirect (no route match → likely 404 or redirect to `/login` if not caught — acceptable; no broken links in nav).

- [ ] **Step 2: Test Tab 1 — 查詢結果**

1. Click 查詢結果 tab (active by default).
2. Click 查詢 without filters → table loads.
3. Expand a row → descriptions appear, 查看詳細結果 button opens dialog.
4. Admin: select rows, 刪除選取 button becomes enabled.
5. 匯出結果 button downloads CSV when sessions exist.

- [ ] **Step 3: Test Tab 2 — 歷史趨勢**

1. Click 歷史趨勢 tab.
2. Chart should appear with last-7-days data (loaded on mount).
3. Statistics row shows total/pass/fail/rate.
4. Timeline groups sessions by date; expand a collapse item, click 查看詳細結果 → dialog opens.
5. Change date range, click 查詢 → chart and timeline update.

- [ ] **Step 4: Test Tab 3 — 報表分析**

1. Click 報表分析 tab.
2. Select project → station list populates.
3. Select station → 測試腳本 list populates.
4. Select test script → click 查詢.
5. Session stats card appears; item stats table appears.
6. Select an item in the filter → line chart renders.

- [ ] **Step 5: Commit (if any fixes were made)**

```bash
git add -p
git commit -m "fix: smoke test corrections for merged TestResults tabs"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Task |
|-------------|------|
| Merge TestResults query table | Task 1 (Tab 1) |
| Merge TestHistory timeline + chart | Task 1 (Tab 2) |
| Merge ReportAnalysis stats + line chart | Task 1 (Tab 3) |
| Remove /history and /analysis routes | Task 2 |
| Remove nav buttons for removed routes | Task 2 |
| Delete obsolete view files | Task 2 |
| Shared session detail dialog | Task 1 (shared dialog section) |
| ECharts chart re-init on tab switch | Task 1 (`handleTabChange`) |
| ECharts chart re-init on data change | Task 1 (`watch(historySessions)`) |

**Placeholder scan:** No TBD, TODO, or vague steps found.

**Type consistency:**
- `historySessions` / `historySessionsByDate` / `historyDailyStats` — correctly prefixed to avoid collision with query-tab `sessions`.
- `getStationName(row)` — used in query/dialog (takes row object). `getStationNameById(stationId)` — used in history timeline (takes bare id). Both defined.
- `fmtNum` (analysis) vs no rename needed — `fmt` was renamed to `fmtNum` to avoid any future collision.
- `analysisChartOption` (computed) vs `chartOption` in old ReportAnalysis — renamed correctly.
- `useTestTimeline(historySessions)` — passes the correct `Ref<Session[]>` from `useTestHistory`, same as original.
