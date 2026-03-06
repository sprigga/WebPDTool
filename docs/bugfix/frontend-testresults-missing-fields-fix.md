# Frontend TestResults 測試計劃與專案名稱未顯示問題修正

## 問題描述

在 `frontend/src/views/TestResults.vue` 查詢測試記錄時，序號 `AUTO-1772782567361` 的：
- **測試計劃**欄位顯示空白
- **專案**名稱欄位顯示為 `-`

---

## 問題一：測試計劃名稱未顯示

### 根本原因

`test_plan_name` 儲存在 `test_plans` 資料表，而非 `test_sessions` 資料表。整個資料流有三個斷點：

1. `TestSession` schema（`backend/app/schemas/test_session.py`）沒有 `test_plan_name` 欄位
2. `list_test_sessions` 端點（`backend/app/api/tests.py`）回傳的 session 物件不含 `test_plan_name`
3. 前端送出的多個篩選條件（`project_id`、`test_plan_name`、`final_result`、`start_date`、`end_date`）全被後端忽略

### 修正內容

**`backend/app/schemas/test_session.py`**

在 `TestSession` schema 新增 `test_plan_name` 選填欄位：

```python
class TestSession(BaseModel):
    ...
    test_plan_name: Optional[str] = None
```

**`backend/app/api/tests.py`** — `list_test_sessions` 端點

1. 新增所有前端使用的篩選參數：`project_id`、`test_plan_name`、`final_result`、`start_date`、`end_date`
2. 透過 `test_results → test_plans` JOIN 實作 `test_plan_name` 篩選（使用 `EXISTS` 子查詢）
3. 在回傳前，對每個 session 查詢其第一筆 test_result 的 `test_plan_id`，再 JOIN `test_plans` 取得 `test_plan_name`

```python
# 取得每個 session 的 test_plan_name
first_result = db.query(TestResultModel)\
    .filter(TestResultModel.session_id == session.id).first()
if first_result and first_result.test_plan_id:
    plan = db.query(TestPlan).filter(TestPlan.id == first_result.test_plan_id).first()
    plan_name = plan.test_plan_name if plan else None
```

---

## 問題二：專案名稱未顯示

### 根本原因

`getProjectName()` 函數依賴 `projectStore.stations` 來查找 `station_id` 對應的專案，但頁面 `onMounted` 只呼叫 `fetchProjects()`，從未載入任何站別資料，導致 `projectStore.stations` 為空陣列。

此外，原本的 `fetchProjectStations(projectId)` 每次呼叫都用 `stations.value = data` **覆蓋**整個 stations 陣列，只保留單一專案的站別，不適合用於「載入全部站別」的場景。

### 修正內容

**`frontend/src/stores/project.js`**

新增 `fetchAllStations()` 方法，遍歷所有專案逐一載入站別並累積（不覆蓋）：

```javascript
async function fetchAllStations() {
  const allStations = []
  for (const project of projects.value) {
    const data = await getProjectStations(project.id)
    allStations.push(...data)
  }
  stations.value = allStations
  return allStations
}
```

**`frontend/src/views/TestResults.vue`**

在 `onMounted` 中，於 `fetchProjects()` 後立即呼叫 `fetchAllStations()`：

```javascript
onMounted(async () => {
  await projectStore.fetchProjects()
  await projectStore.fetchAllStations()  // 新增
  await loadSessions()
})
```

---

## 修改檔案清單

| 檔案 | 修改內容 |
|------|---------|
| `backend/app/schemas/test_session.py` | 新增 `test_plan_name: Optional[str] = None` |
| `backend/app/api/tests.py` | 新增篩選參數支援；回傳時填充 `test_plan_name` |
| `frontend/src/stores/project.js` | 新增 `fetchAllStations()` 方法並 export |
| `frontend/src/views/TestResults.vue` | `onMounted` 中呼叫 `fetchAllStations()` |

## 部署

```bash
# 後端重啟
docker-compose restart backend

# 前端需重新 build（Nginx serve 靜態檔案，重啟不會重新 build）
docker-compose build frontend && docker-compose up -d frontend
```
