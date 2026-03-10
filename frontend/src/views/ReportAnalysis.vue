<template>
  <div class="report-analysis-page" style="padding: 20px;">
    <AppNavBar current-page="analysis" />
    <h2>報表分析</h2>

    <!-- 篩選區 -->
    <el-card style="margin-bottom: 16px;">
      <el-form :inline="true" :model="filters" label-width="80px">
        <el-form-item label="專案">
          <el-select
            v-model="filters.project_id"
            placeholder="選擇專案"
            clearable
            @change="onProjectChange"
            style="width: 160px;"
          >
            <el-option
              v-for="p in projects"
              :key="p.id"
              :label="p.project_name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="站別">
          <el-select
            v-model="filters.station_id"
            placeholder="選擇站別"
            clearable
            :disabled="!filters.project_id"
            @change="onStationChange"
            style="width: 160px;"
          >
            <el-option
              v-for="s in stationList"
              :key="s.id"
              :label="s.station_name"
              :value="s.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="測試腳本">
          <el-select
            v-model="filters.test_plan_name"
            placeholder="選擇測試腳本"
            clearable
            :disabled="!filters.station_id"
            :loading="loadingPlans"
            style="width: 200px;"
          >
            <el-option
              v-for="name in testPlanNames"
              :key="name"
              :label="name"
              :value="name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="開始日期">
          <el-date-picker
            v-model="filters.date_from"
            type="date"
            placeholder="From"
            value-format="YYYY-MM-DD"
            style="width: 140px;"
          />
        </el-form-item>

        <el-form-item label="結束日期">
          <el-date-picker
            v-model="filters.date_to"
            type="date"
            placeholder="To"
            value-format="YYYY-MM-DD"
            style="width: 140px;"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            :disabled="!filters.station_id || !filters.test_plan_name"
            @click="fetchAnalysis"
          >
            查詢
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 總執行時間統計 -->
    <el-card v-if="sessionStats && sessionStats.sample_count > 0" style="margin-bottom: 16px;">
      <template #header>
        <span>總執行時間統計（秒）- 樣本數：{{ sessionStats.sample_count }}</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6" v-for="stat in sessionStatItems" :key="stat.label">
          <div class="stat-card">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value">{{ stat.value ?? 'N/A' }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 項目名稱篩選 -->
    <el-card v-if="itemStats.length > 0" style="margin-bottom: 16px;">
      <el-form :inline="true" label-width="80px">
        <el-form-item label="項目名稱">
          <el-select
            v-model="selectedItemNo"
            placeholder="選擇項目（可選，不選則顯示全部）"
            clearable
            style="width: 320px;"
          >
            <el-option
              v-for="opt in itemOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 各測試項目執行時間統計 -->
    <el-card v-if="itemStats.length > 0" style="margin-bottom: 16px;">
      <template #header>
        <span>各測試項目執行時間統計（ms）</span>
      </template>
      <el-table :data="filteredItemStats" stripe border style="width: 100%;">
        <el-table-column prop="item_no" label="項次" width="70" align="center" />
        <el-table-column prop="item_name" label="項目名稱" min-width="200" />
        <el-table-column prop="sample_count" label="樣本數" width="80" align="right" />
        <el-table-column prop="mean_ms" label="平均 (ms)" width="110" align="right">
          <template #default="{ row }">{{ fmt(row.mean_ms) }}</template>
        </el-table-column>
        <el-table-column prop="median_ms" label="中位數 (ms)" width="110" align="right">
          <template #default="{ row }">{{ fmt(row.median_ms) }}</template>
        </el-table-column>
        <el-table-column prop="stdev_ms" label="標準差 (ms)" width="110" align="right">
          <template #default="{ row }">{{ fmt(row.stdev_ms) }}</template>
        </el-table-column>
        <el-table-column prop="mad_ms" label="MAD (ms)" width="110" align="right">
          <template #default="{ row }">{{ fmt(row.mad_ms) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 折線圖 -->
    <el-card v-if="chartOption" style="margin-bottom: 16px;">
      <template #header>
        <span>執行時間趨勢圖</span>
      </template>
      <v-chart :option="chartOption" style="height: 320px;" autoresize />
    </el-card>

    <el-empty v-else-if="queried && itemStats.length === 0" description="此條件無資料" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import AppNavBar from '@/components/AppNavBar.vue'
import { useProjectStore } from '@/stores/project'
import { getAnalysis } from '@/api/analysis'
import apiClient from '@/api/client'

use([LineChart, GridComponent, TooltipComponent, TitleComponent, LegendComponent, CanvasRenderer])

const projectStore = useProjectStore()

// --- State ---
const filters = ref({
  project_id: null,
  station_id: null,
  test_plan_name: null,
  date_from: null,
  date_to: null,
})
const stationList = ref([])
const testPlanNames = ref([])
const loadingPlans = ref(false)
const loading = ref(false)
const queried = ref(false)
const itemStats = ref([])
const sessionStats = ref(null)
const selectedItemNo = ref(null)
const itemSeries = ref([])

// --- Computed ---
const projects = computed(() => projectStore.projects || [])

const sessionStatItems = computed(() => {
  if (!sessionStats.value) return []
  const s = sessionStats.value
  return [
    { label: '平均數', value: s.mean_s },
    { label: '中位數', value: s.median_s },
    { label: '標準差', value: s.stdev_s },
    { label: 'MAD', value: s.mad_s },
  ]
})

const itemOptions = computed(() =>
  (itemStats.value || []).map(i => ({
    label: `${i.item_no}. ${i.item_name}`,
    value: i.item_no,
  }))
)

const filteredItemStats = computed(() => {
  if (selectedItemNo.value === null) return itemStats.value
  return itemStats.value.filter(i => i.item_no === selectedItemNo.value)
})

const chartOption = computed(() => {
  if (selectedItemNo.value === null) return null
  const series = itemSeries.value.find(s => s.item_no === selectedItemNo.value)
  if (!series || !series.sessions.length) return null

  const xData = series.sessions.map(s =>
    s.start_time ? s.start_time.slice(0, 16).replace('T', ' ') : ''
  )
  const yData = series.sessions.map(s => s.duration_ms ?? null)

  return {
    title: {
      text: `${series.item_name} — 每次 Session 執行時間`,
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      formatter: params =>
        `${params[0].axisValue}<br/>執行時間: ${params[0].value ?? 'N/A'} ms`,
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: { type: 'value', name: 'ms', nameTextStyle: { fontSize: 11 } },
    series: [
      {
        type: 'line',
        data: yData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2 },
        itemStyle: { color: '#409EFF' },
      },
    ],
    grid: { left: 60, right: 20, bottom: 60, top: 60 },
  }
})

// --- Methods ---
function fmt(val) {
  return val !== null && val !== undefined ? val : 'N/A'
}

async function onProjectChange() {
  filters.value.station_id = null
  filters.value.test_plan_name = null
  testPlanNames.value = []
  stationList.value = []
  if (!filters.value.project_id) return
  await projectStore.fetchProjectStations(filters.value.project_id)
  stationList.value = projectStore.stations || []
}

async function onStationChange() {
  filters.value.test_plan_name = null
  testPlanNames.value = []
  if (!filters.value.station_id) return

  loadingPlans.value = true
  try {
    // GET /api/stations/{station_id}/testplan-names returns List[str]
    const res = await apiClient.get(`/api/stations/${filters.value.station_id}/testplan-names`)
    testPlanNames.value = Array.isArray(res) ? res : []
  } catch (e) {
    ElMessage.error('載入測試腳本失敗')
  } finally {
    loadingPlans.value = false
  }
}

async function fetchAnalysis() {
  loading.value = true
  queried.value = false
  itemStats.value = []
  sessionStats.value = null
  itemSeries.value = []
  selectedItemNo.value = null

  try {
    const params = {
      station_id: filters.value.station_id,
      test_plan_name: filters.value.test_plan_name,
    }
    if (filters.value.date_from) params.date_from = filters.value.date_from
    if (filters.value.date_to) params.date_to = filters.value.date_to

    const res = await getAnalysis(params)
    itemStats.value = res.item_stats || []
    sessionStats.value = res.session_stats || null
    itemSeries.value = res.item_series || []
    queried.value = true
  } catch (e) {
    ElMessage.error('查詢失敗，請確認篩選條件')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await projectStore.fetchProjects()
})
</script>

<style scoped>
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
</style>
