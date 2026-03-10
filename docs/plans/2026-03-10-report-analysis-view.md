# ReportAnalysis View Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `ReportAnalysis.vue` 新增「項目名稱」下拉選單，可依選取項目篩選統計表格，並以折線圖顯示每次 Session 的 `execution_duration_ms` 時間趨勢。

**Architecture:** 後端在 `/api/measurement-results/analysis` 回應中新增 `item_series`（各 Session 的時間序列資料）。前端安裝 ECharts + vue-echarts，從 `item_stats` 動態建立項目下拉，選取後過濾表格並渲染折線圖。

**Tech Stack:** Vue 3 (Composition API, `<script setup>`) · Element Plus · ECharts 5 · vue-echarts · FastAPI · SQLAlchemy (sync)

---

## 檔案清單

| 動作 | 路徑 | 說明 |
|------|------|------|
| 修改 | `backend/app/api/results/analysis.py` | 新增 `SessionPoint`、`ItemSeries` 模型，回應加入 `item_series` |
| 修改 | `frontend/package.json` | 安裝 `echarts`、`vue-echarts` |
| 修改 | `frontend/src/views/ReportAnalysis.vue` | 項目下拉、篩選表格、ECharts 折線圖 |

> `frontend/src/api/analysis.js` **不需變更** — `getAnalysis()` 已回傳完整 response，`item_series` 會自動出現在回應中。

---

## Chunk 1: 後端 — 新增 item_series 時間序列

### Task 1: 擴充 `analysis.py` 回應格式

**Files:**
- Modify: `backend/app/api/results/analysis.py`

- [ ] **Step 1: 新增 Pydantic 模型**

在 `SessionStats` 模型之後，加入：

```python
class SessionPoint(BaseModel):
    session_id: int
    start_time: datetime
    duration_ms: Optional[float]

class ItemSeries(BaseModel):
    item_no: int
    item_name: str
    sessions: List[SessionPoint]
```

並將現有 `AnalysisResponse` 改為：

```python
class AnalysisResponse(BaseModel):
    item_stats: List[ItemStats]
    session_stats: SessionStats
    item_series: List[ItemSeries] = []   # 新增欄位，預設空列表保持向後相容
```

- [ ] **Step 2: 在 `get_analysis()` 中建立 item_series**

在現有 per-item stats 迴圈結束後、`return` 之前，加入：

```python
# --- Per-item time-series (session_id, start_time, duration_ms) ---
session_map = {s.id: s.start_time for s in sessions}

item_series_groups: dict = defaultdict(lambda: {"item_name": "", "sessions": {}})
for r in results:
    key = r.item_no
    item_series_groups[key]["item_name"] = r.item_name
    sid = r.session_id
    if sid not in item_series_groups[key]["sessions"]:
        item_series_groups[key]["sessions"][sid] = {
            "session_id": sid,
            "start_time": session_map.get(sid),
            "duration_ms": float(r.execution_duration_ms) if r.execution_duration_ms is not None else None,
        }

item_series = []
for item_no in sorted(item_series_groups.keys()):
    g = item_series_groups[item_no]
    sorted_sessions = sorted(
        g["sessions"].values(),
        key=lambda x: x["start_time"] or datetime.min,
    )
    item_series.append(
        ItemSeries(
            item_no=item_no,
            item_name=g["item_name"],
            sessions=[SessionPoint(**sp) for sp in sorted_sessions],
        )
    )
```

- [ ] **Step 3: 更新所有 `return AnalysisResponse(...)` 呼叫**

共有三處 return：

```python
# 1. 無 sessions 早期回傳
return AnalysisResponse(
    item_stats=[],
    session_stats=SessionStats(sample_count=0, mean_s=None, median_s=None, stdev_s=None, mad_s=None),
    item_series=[],
)

# 2. 無 plan_ids 早期回傳
return AnalysisResponse(item_stats=[], session_stats=session_stats, item_series=[])

# 3. 最終回傳
return AnalysisResponse(item_stats=item_stats, session_stats=session_stats, item_series=item_series)
```

- [ ] **Step 4: 確認 import 完整**

確認 `analysis.py` 頂端有：

```python
from datetime import date, datetime
from collections import defaultdict
from typing import List, Optional
```

- [ ] **Step 5: 手動驗證 API**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
python3 -c "
import ast, sys
with open('app/api/results/analysis.py') as f:
    src = f.read()
ast.parse(src)
print('Syntax OK')
"
```

預期：`Syntax OK`

- [ ] **Step 6: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/api/results/analysis.py
git commit -m "feat: add item_series time-series data to analysis endpoint"
```

---

## Chunk 2: 前端 — 安裝 ECharts

### Task 2: 安裝圖表套件

**Files:**
- Modify: `frontend/package.json`（透過 npm install）

- [ ] **Step 1: 安裝套件**

```bash
cd /home/ubuntu/python_code/WebPDTool/frontend
npm install echarts vue-echarts
```

- [ ] **Step 2: 驗證安裝**

```bash
node -e "require('echarts'); require('vue-echarts'); console.log('OK')"
```

預期：`OK`

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add echarts and vue-echarts dependencies"
```

---

## Chunk 3: 前端 — ReportAnalysis.vue 更新

### Task 3: 新增項目下拉、篩選表格、折線圖

**Files:**
- Modify: `frontend/src/views/ReportAnalysis.vue`

#### 變更摘要

1. 在 `<script setup>` 頂端加入 ECharts tree-shaking import 及 `VChart`
2. 新增 reactive 狀態：`selectedItemNo`、`itemSeries`
3. `fetchAnalysis()` 存入 `item_series`，並重置 `selectedItemNo`
4. 新增 computed：`itemOptions`（下拉選項）、`filteredItemStats`（篩選後表格資料）、`chartOption`（ECharts 設定）
5. Template：在 session stats 卡片後新增「項目名稱」下拉卡片；`el-table` 資料改用 `filteredItemStats`；統計表格卡片後新增折線圖卡片

---

- [ ] **Step 1: 更新 `<script setup>` — import**

在現有 import 區塊底端加入：

```javascript
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

use([LineChart, GridComponent, TooltipComponent, TitleComponent, LegendComponent, CanvasRenderer])
```

> **Note:** 在 Vue 3 `<script setup>` 中，import 的元件會自動在 template 中可用，無需 `defineOptions({ components: { VChart } })`。

- [ ] **Step 2: 新增 reactive 狀態**

在現有 `const sessionStats = ref(null)` 之後加入：

```javascript
const selectedItemNo = ref(null)
const itemSeries = ref([])
```

- [ ] **Step 3: 更新 `fetchAnalysis()`**

在 try 區塊的 `sessionStats.value = res.session_stats || null` 之後加入：

```javascript
itemSeries.value = res.item_series || []
selectedItemNo.value = null
```

- [ ] **Step 4: 新增 computed**

在現有 `sessionStatItems` computed 之後加入：

```javascript
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
```

- [ ] **Step 5: 更新 template**

**5a. 在「總執行時間統計」`</el-card>` 後，「各測試項目執行時間統計」`<el-card>` 前，插入項目下拉卡片：**

```html
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
```

**5b. 將 `el-table` 的 `:data` 改為 `filteredItemStats`：**

```html
<!-- 將 :data="itemStats" 改為 -->
<el-table :data="filteredItemStats" stripe border style="width: 100%;">
```

**5c. 在「各測試項目執行時間統計」`</el-card>` 後新增折線圖卡片：**

```html
<!-- 折線圖 -->
<el-card v-if="chartOption" style="margin-top: 16px;">
  <template #header>
    <span>執行時間趨勢圖</span>
  </template>
  <v-chart :option="chartOption" style="height: 320px;" autoresize />
</el-card>
```

- [ ] **Step 6: 前端 build 驗證**

```bash
cd /home/ubuntu/python_code/WebPDTool/frontend
npm run build 2>&1 | tail -10
```

預期：最後幾行出現 `✓ built in` 且無 ERROR。

- [ ] **Step 7: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add frontend/src/views/ReportAnalysis.vue
git commit -m "feat: add item name dropdown and execution time trend chart to ReportAnalysis"
```

---

## Chunk 4: 整合手動驗證

### Task 4: 瀏覽器端對端確認

- [ ] **Step 1: 啟動服務**

```bash
docker-compose up -d
```

- [ ] **Step 2: 執行測試流程**

1. 開啟 `http://localhost:9080/analysis`
2. 選擇 專案 → 站別 → 測試腳本 → 點擊「查詢」
3. 確認「項目名稱」下拉出現，選項包含測試項目清單
4. 選取一個項目 → 確認統計表格只顯示該項目
5. 確認折線圖出現，X 軸為 session 時間，Y 軸為 duration（ms）
6. 清除選取 → 確認表格顯示全部項目、折線圖消失

- [ ] **Step 3: 清除臨時測試檔（若有）**

```bash
# 若有任何臨時 .py 測試腳本，在此刪除
```

---

## Chunk 5: Bugfix — API 路徑錯誤（2026-03-10 實際執行後發現）

### 問題

執行後，選擇測試腳本查詢時出現「此條件無資料」且「項目名稱」下拉未顯示。

### 根本原因

`frontend/src/api/analysis.js` 的路徑 `/results/analysis` 不正確。後端 `main.py` 將 results router 掛載在 `prefix="/api/measurement-results"`，正確路徑應為 `/api/measurement-results/analysis`。

查詢呼叫回傳 404 → catch 攔截錯誤 → `itemStats` 維持空陣列 → 「此條件無資料」且 `v-if="itemStats.length > 0"` 的項目下拉不顯示。

### 修正

- [ ] **Step 1: 修正 `analysis.js`**

```javascript
// frontend/src/api/analysis.js
// 修正前
return apiClient.get('/results/analysis', { params })

// 修正後
return apiClient.get('/api/measurement-results/analysis', { params })
```

- [ ] **Step 2: 驗證後端路由掛載前綴**

```bash
grep "measurement-results" backend/app/main.py
# 預期輸出：prefix="/api/measurement-results"
```

- [ ] **Step 3: Rebuild Docker frontend 容器**

> **重要：** 修改 JS 原始碼後，Docker Nginx 仍提供舊 bundle，必須 rebuild。

```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend

# 驗證新 bundle 包含正確路徑
docker-compose exec frontend grep -ro "measurement-results/analysis" /usr/share/nginx/html/assets/
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/analysis.js
git commit -m "fix: correct analysis API path to /api/measurement-results/analysis"
```

> **詳細記錄：** `docs/bugfix/report-analysis-view-fix.md` BUG 6

---

## 注意事項

1. **`item_series` 每個 session 只取第一筆 result**：若同一 session 對同一 item_no 有多筆 TestResult（重測），只保留第一筆。如需平均，可於後端調整 grouping 邏輯。

2. **ECharts tree-shaking**：使用 `use([...])` 按需引入元件，避免打包整個 ECharts（~1MB+）。

3. **`autoresize` 屬性**：vue-echarts 的 `autoresize` 讓圖表自動跟隨容器寬度調整，無需手動監聽 resize 事件。

4. **向後相容**：`AnalysisResponse` 的 `item_series` 欄位設有預設值 `= []`，舊呼叫端不受影響。

5. **apiClient 已自動解包 response.data**：`client.js` response interceptor 回傳 `response.data`，所有 API 呼叫回傳值直接是 body，不可再用 `.data` 存取（`res.item_stats` ✅，`res.data.item_stats` ❌）。

6. **Docker 前端修改後必須 rebuild**：本地修改 JS/Vue 檔案不會自動反映到 Docker Nginx 容器，每次前端異動都需執行 `docker-compose build --no-cache frontend && docker-compose up -d frontend`。
