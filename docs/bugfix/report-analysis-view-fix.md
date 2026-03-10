# ReportAnalysis.vue 功能修正記錄

**日期：** 2026-03-10  
**功能：** 報表分析頁面（`/analysis` → `ReportAnalysis.vue`）

---

## BUG 1：選擇專案後，站別下拉選單無選項

### 原因
`filteredStations` computed 嘗試讀取 `proj.stations`（巢狀屬性），但 `getProjects()` API 回傳的 project 物件中並不包含 `stations` 陣列。站別需要透過 `getProjectStations(projectId)` 單獨取得。

### 修正
- 新增 local `stationList` ref
- `onProjectChange` 改為 async，選擇專案後呼叫 `projectStore.fetchProjectStations(project_id)` 取得站別列表
- 移除不正確的 `filteredStations` computed，template 改用 `stationList`

```javascript
// 修正前（錯誤）
const filteredStations = computed(() => {
  const proj = projects.value.find(p => p.id === filters.value.project_id)
  return proj?.stations || []  // proj.stations 永遠是 undefined
})

// 修正後
const stationList = ref([])
async function onProjectChange() {
  stationList.value = []
  if (!filters.value.project_id) return
  await projectStore.fetchProjectStations(filters.value.project_id)
  stationList.value = projectStore.stations || []
}
```

---

## BUG 2：選擇站別後，測試腳本下拉選單無選項（路徑缺少 /api 前綴）

### 原因
`onStationChange` 呼叫 `/stations/{id}/testplan-names`，缺少 `/api` 前綴。`apiClient` 的 `baseURL` 是空字串，所有路徑都需要手動加上 `/api`。

### 修正
```javascript
// 修正前
const res = await apiClient.get(`/stations/${filters.value.station_id}/testplan-names`)

// 修正後
const res = await apiClient.get(`/api/stations/${filters.value.station_id}/testplan-names`)
```

---

## BUG 3：測試腳本選單無選項（response 解包錯誤）

### 原因
`apiClient` 的 response interceptor 已自動解包 `response.data`，回傳值本身就是陣列。程式碼使用 `res.data` 再次解包，導致取到 `undefined`。

### 修正
```javascript
// 修正前
testPlanNames.value = res.data || []  // res.data 是 undefined

// 修正後
testPlanNames.value = Array.isArray(res) ? res : []
```

---

## BUG 4：按下查詢出現 404 Not Found

### 原因
`analysis.js` 使用 `/api/results/analysis`，但後端 `main.py` 將 results router 掛載在 `/api/measurement-results`，正確路徑應為 `/api/measurement-results/analysis`。

```python
# backend/app/main.py
app.include_router(measurement_results_router, prefix="/api/measurement-results", ...)
```

### 修正
```javascript
// 修正前（frontend/src/api/analysis.js）
return apiClient.get('/results/analysis', { params })

// 修正後
return apiClient.get('/api/measurement-results/analysis', { params })
```

---

## BUG 5：按下查詢出現「查詢失敗，請確認篩選條件」錯誤訊息

### 原因
`fetchAnalysis` 使用 `res.data.item_stats`，但同樣因為 `apiClient` response interceptor 自動解包，`res` 本身就是 `{item_stats: [...], session_stats: {...}}`，`res.data` 是 `undefined`，導致拋出 TypeError 進入 catch。

### 修正
```javascript
// 修正前
itemStats.value = res.data.item_stats || []
sessionStats.value = res.data.session_stats || null

// 修正後
itemStats.value = res.item_stats || []
sessionStats.value = res.session_stats || null
```

---

---

## BUG 6：新增 item_series 後，`analysis.js` API 路徑錯誤導致「此條件無資料」與項目下拉未顯示

**日期：** 2026-03-10（第二次修正，新增 ECharts 折線圖功能後）

### 症狀
- 選擇 Demo Project2 → Test Station 3 → test123 → 查詢，出現「此條件無資料」
- 「項目名稱」下拉未出現

### 原因
`frontend/src/api/analysis.js` 的路徑為 `/results/analysis`，但後端 router 掛載在 `/api/measurement-results`，正確路徑應為 `/api/measurement-results/analysis`。查詢失敗（404）→ catch 捕捉到錯誤 → `itemStats` 維持空陣列 → 「此條件無資料」且項目下拉 `v-if="itemStats.length > 0"` 不顯示。

```javascript
// 修正前（frontend/src/api/analysis.js）
return apiClient.get('/results/analysis', { params })

// 修正後
return apiClient.get('/api/measurement-results/analysis', { params })
```

### 注意：Docker 部署需 rebuild

修改 `analysis.js` 後，Docker 容器內的 Nginx 仍提供舊的 bundle。需要重新 build 並重啟 frontend 容器：

```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

驗證新 bundle 已更新：
```bash
docker-compose exec frontend grep -ro "measurement-results/analysis" /usr/share/nginx/html/assets/
```

---

## 重要規則：apiClient response 解包

`frontend/src/api/client.js` 的 response interceptor：

```javascript
apiClient.interceptors.response.use(
  (response) => {
    return response.data  // 自動解包
  },
  ...
)
```

**結論：** 所有透過 `apiClient` 的呼叫，回傳值已是 response body，**不可再用 `.data` 存取**。正確方式：

```javascript
const res = await apiClient.get('/api/...')
res.someField   // ✅ 正確
res.data        // ❌ 錯誤，是 undefined
```
