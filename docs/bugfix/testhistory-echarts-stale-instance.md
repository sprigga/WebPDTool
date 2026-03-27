---
title: TestHistory 圖表切換條件後無法顯示
date: 2026-03-26
component: frontend/src/views/TestHistory.vue
composable: frontend/src/composables/useTestTimeline.js
severity: medium
status: fixed
---

# Bug：TestHistory 圖表切換篩選條件後無法顯示

## 問題描述

**重現步驟：**

1. 進入 TestHistory 頁面
2. 選擇 `selectedProject = "demo project 1"`，`selectedStation = "test station 2"`
3. 按下「查詢」→ 查詢結果為 **0 筆**，畫面顯示空白提示（el-empty）
4. 改選 `selectedProject = "demo project 2"`，`selectedStation = "test station 3"`
5. 按下「查詢」→ 查詢結果有資料，但**圖表區塊空白，沒有任何圖表渲染**

**預期行為：** 步驟 5 應正常渲染 ECharts 長條圖。

---

## 根本原因分析（Root Cause）

### Phase 1：追蹤資料流

TestHistory.vue 的模板結構如下：

```html
<!-- sessions.length === 0 → 顯示 el-empty，隱藏 timeline-content -->
<el-empty v-else-if="!loading && sessions.length === 0" ... />

<!-- sessions.length > 0 → 顯示圖表和時間軸 -->
<div v-else class="timeline-content">
  <el-card class="chart-card" shadow="never">
    <div ref="chartRef" class="chart-container"></div>
  </el-card>
  ...
</div>
```

`chartRef` 所指向的 DOM 元素位於 `v-else` 區塊內。

### Phase 2：找到問題核心

**完整的觸發序列：**

| 步驟 | sessions | DOM 狀態 | chartInstance 狀態 |
|------|----------|----------|--------------------|
| 初始化（onMounted） | 有資料 | `timeline-content` 存在，`chartRef` 指向有效 DOM | `initChart()` 建立實例，綁定 DOM |
| 查詢 project1/station2 | **0 筆** | `v-else-if` 顯示，`timeline-content` **被 Vue 銷毀** | `chartInstance` 仍持有舊實例（指向已銷毀的 DOM） |
| sessions watcher 觸發 | 0 筆 | — | 呼叫 `updateChart()` → `chartInstance` 存在，跑完但無作用 |
| 查詢 project2/station3 | 有資料 | Vue 重新建立 `timeline-content`，產生**全新的** `chartRef` DOM | `chartInstance` 仍是舊的，指向舊 DOM |
| sessions watcher 觸發 | 有資料 | — | 呼叫 `updateChart()` → `chartInstance.setOption()` 作用在舊 DOM，**畫面無反應** |

**問題癥結：** ECharts 的 `chartInstance` 在 `initChart()` 時綁定 `chartRef.value`（當下的 DOM 節點）。當 `v-else` 區塊因條件切換被 Vue 銷毀並重建後，`chartRef.value` 指向全新的 DOM 元素，但 `chartInstance` 仍綁定舊節點。此時呼叫 `setOption()` 是無效操作。

---

## 修正方式

**檔案：** `frontend/src/views/TestHistory.vue`

**策略：** 偵測 sessions 從「空」到「有資料」的轉換，在此情況下重新呼叫 `initChartWhenReady()`，而非只呼叫 `updateChart()`。

**修正前（有 bug）：**

```js
// Update chart when sessions change
watch(sessions, () => {
  updateChart()
}, { deep: true })
```

**修正後：**

```js
// Update chart when sessions change.
// When sessions go from empty → non-empty, the timeline-content v-else block is
// re-created in the DOM, destroying the previous chartRef element. In that case
// we must call initChart() (not just updateChart()) to re-bind ECharts to the
// new DOM node. If chartInstance is still alive (DOM was not destroyed), a plain
// updateChart() is enough.
watch(sessions, async (newVal, oldVal) => {
  const wasEmpty = !oldVal || oldVal.length === 0
  const nowHasData = newVal && newVal.length > 0
  if (wasEmpty && nowHasData) {
    // DOM was just re-rendered; wait for Vue to finish then re-init chart
    await initChartWhenReady()
  } else {
    updateChart()
  }
}, { deep: true })
```

**`initChartWhenReady()` 做了什麼：**

```js
const initChartWhenReady = async () => {
  await nextTick()                         // 等 Vue 完成 DOM 更新
  setTimeout(initChart, CHART_INIT_DELAY_MS)  // 給容器 100ms 確保有尺寸
}
```

`initChart()` 會重新執行 `echarts.init(chartRef.value)`，將新的 DOM 節點綁定到新的 ECharts 實例，然後呼叫 `updateChart()` 渲染資料。

---

## 除錯過程

### 觀察到的現象

- 第一次查詢有資料：圖表正常
- 第一次查詢無資料後，再查詢有資料：圖表空白

### 除錯切入點

1. 先確認 `sessions` 資料是否正確載入 → 是的，API 回傳正確，`sessions.value` 有資料
2. 確認 `chartInstance.value` 是否為 null → 不是 null，代表不是初始化沒跑到的問題
3. 追蹤 `v-else` 條件 → 發現 `chartRef` 所在區塊會在 `sessions.length === 0` 時被 Vue 完整銷毀
4. 關鍵問題：**Vue 的 `v-else` 不是隱藏，而是銷毀並重建 DOM**
5. ECharts 初始化時 `echarts.init()` 對 DOM 元素產生綁定關係，DOM 銷毀後綁定失效

### 關鍵知識點

- `v-show` = `display: none`，DOM 保留，ECharts 實例仍有效
- `v-if` / `v-else` = DOM 完全銷毀重建，任何綁定到舊 DOM 的 JS 物件都失效
- 本案使用 `v-else-if` + `v-else`，屬於 `v-if` 系列，必須考慮 DOM 重建問題

---

## 替代解法（未採用）

| 方案 | 優點 | 缺點 |
|------|------|------|
| 將 `v-else` 改為 `v-show` | 最簡單，DOM 永不銷毀 | 圖表容器在空狀態時仍佔空間，需額外 CSS 處理 |
| 在每次 `updateChart()` 前先 dispose 再 init | 確保每次都是全新實例 | 效能較差，每次查詢都重建實例 |
| **watcher 偵測空→有資料轉換（採用）** | 只在必要時重新初始化，其餘情況直接更新 | 邏輯略複雜，但清楚易懂 |

---

## Playwright 驗證測試（2026-03-26）

### 測試工具
- Playwright MCP（`mcp__plugin_playwright`）
- 測試環境：`http://localhost:9080`

### 測試步驟與結果

| 步驟 | 操作 | 預期結果 | 實際結果 |
|------|------|----------|----------|
| 1 | 進入 `/history` 頁面 | 頁面正常載入 | ✅ 正常 |
| 2 | 選擇 Demo Project 1 / Test Station 2，按「查詢」 | 0 筆，顯示「暫無測試記錄」空狀態 | ✅ 顯示空狀態 |
| 3 | 切換 Demo Project 2 / Test Station 3，按「查詢」 | 圖表正常渲染 | ✅ 圖表正常顯示 |

### 修正後查詢結果（步驟 3）

- 總測試次數：**420**
- 通過：**420**
- 失敗：**0**
- 通過率：**100.0%**
- 圖表：「測試趨勢」長條圖正確渲染，顯示 2026-03-25 的綠色柱狀圖

### 截圖

- 空狀態截圖：`screenshots/bugfix-step1-empty-state.png`
- 修正後圖表截圖：`screenshots/bugfix-step2-chart-after-empty.png`

### 結論

**Bug 已確認修復。** 空狀態 → 有資料的切換流程，`initChartWhenReady()` 成功在 `v-else` DOM 重建後重新綁定 ECharts 實例，圖表正常渲染。
