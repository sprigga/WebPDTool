# 報告生成功能快速開始

> 5 分鐘快速了解如何使用自動報告生成功能

---

## 🎯 功能亮點

✅ 測試完成自動生成 CSV 報告
✅ 按項目/站別/日期自動組織文件
✅ 包含完整測試數據(含錯誤訊息、執行時間)
✅ REST API 查詢、下載和管理報告

---

## 🚀 快速開始

### 1. 配置環境變數

編輯 `backend/.env`:

```bash
# 報告生成配置
REPORT_BASE_DIR=reports        # 報告保存目錄
REPORT_AUTO_SAVE=True          # 啟用自動保存
```

### 2. 啟動服務

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. 運行測試

當測試會話完成時,系統會自動:
1. 生成 CSV 報告
2. 保存到 `reports/{project}/{station}/{YYYYMMDD}/`
3. 記錄日誌

**日誌示例**:
```
INFO: Test session 123 finalized: PASSED (10/10 passed)
INFO: Test report saved: reports/MyProject/Station1/20260129/SN001_20260129_143045.csv
```

### 4. 查看報告

#### 方法 A: 直接訪問文件系統

```bash
cd backend/reports
ls -R
```

**目錄結構**:
```
reports/
└── MyProject/
    └── Station1/
        └── 20260129/
            ├── SN001_20260129_143045.csv
            └── SN002_20260129_144530.csv
```

#### 方法 B: 使用 API

```bash
# 列出所有報告
curl -X GET "http://localhost:8000/api/results/reports/list" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 下載特定會話的報告
curl -X GET "http://localhost:8000/api/results/reports/download/123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o report.csv
```

---

## 📊 CSV 報告格式

```csv
Item No, Item Name, Result, Measured Value, Min Limit, Max Limit, Error Message, Execution Time (ms), Test Time
1, Voltage_Test, PASS, 12.5, 10.0, 15.0, , 250, 2026-01-29T14:30:45
2, Current_Test, PASS, 0.85, 0.1, 1.0, , 180, 2026-01-29T14:30:46
3, Resistance_Test, FAIL, 110, 95, 105, Value out of range, 150, 2026-01-29T14:30:47
```

### 欄位說明

| 欄位 | 說明 | 範例 |
|------|------|------|
| Item No | 測試項目編號 | 1 |
| Item Name | 測試項目名稱 | Voltage_Test |
| Result | 測試結果 | PASS/FAIL/ERROR/SKIP |
| Measured Value | 測量值 | 12.5 |
| Min/Max Limit | 上下限 | 10.0, 15.0 |
| Error Message | 錯誤訊息 | Value out of range |
| Execution Time | 執行時間(毫秒) | 250 |
| Test Time | 測試時間(ISO 8601) | 2026-01-29T14:30:45 |

---

## 🔧 API 使用範例

### Python

```python
import requests

# 設定 API 端點和認證
API_BASE = "http://localhost:8000/api/results"
headers = {"Authorization": f"Bearer {token}"}

# 列出報告
response = requests.get(f"{API_BASE}/reports/list", headers=headers)
reports = response.json()
print(f"找到 {len(reports)} 份報告")

# 下載報告
response = requests.get(
    f"{API_BASE}/reports/download/123",
    headers=headers
)
with open("report.csv", "wb") as f:
    f.write(response.content)
```

### JavaScript

```javascript
// 列出報告
async function listReports() {
  const response = await fetch('/api/results/reports/list', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const reports = await response.json();
  console.log(`找到 ${reports.length} 份報告`);
  return reports;
}

// 下載報告
async function downloadReport(sessionId) {
  const response = await fetch(
    `/api/results/reports/download/${sessionId}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  const blob = await response.blob();

  // 觸發下載
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `report_${sessionId}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
}
```

---

## 🎨 前端整合範例

### Vue 3 Component

```vue
<template>
  <div class="report-manager">
    <h2>測試報告</h2>

    <!-- 過濾器 -->
    <div class="filters">
      <input v-model="filters.projectName" placeholder="項目名稱" />
      <input v-model="filters.stationName" placeholder="站別名稱" />
      <input v-model="filters.dateFrom" type="date" />
      <input v-model="filters.dateTo" type="date" />
      <button @click="loadReports">搜索</button>
    </div>

    <!-- 報告列表 -->
    <table class="report-table">
      <thead>
        <tr>
          <th>文件名</th>
          <th>項目</th>
          <th>站別</th>
          <th>日期</th>
          <th>大小</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="report in reports" :key="report.filepath">
          <td>{{ report.filename }}</td>
          <td>{{ report.project }}</td>
          <td>{{ report.station }}</td>
          <td>{{ report.date }}</td>
          <td>{{ formatSize(report.size_bytes) }}</td>
          <td>
            <button @click="downloadReport(report.filepath)">
              下載
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const reports = ref([]);
const filters = ref({
  projectName: '',
  stationName: '',
  dateFrom: '',
  dateTo: ''
});

async function loadReports() {
  const params = new URLSearchParams();
  if (filters.value.projectName) {
    params.set('project_name', filters.value.projectName);
  }
  if (filters.value.stationName) {
    params.set('station_name', filters.value.stationName);
  }
  if (filters.value.dateFrom) {
    params.set('date_from', filters.value.dateFrom);
  }
  if (filters.value.dateTo) {
    params.set('date_to', filters.value.dateTo);
  }

  const response = await axios.get(
    `/api/results/reports/list?${params}`
  );
  reports.value = response.data;
}

async function downloadReport(filepath) {
  const response = await axios.get(
    `/api/results/reports/download-by-path`,
    {
      params: { filepath },
      responseType: 'blob'
    }
  );

  const url = window.URL.createObjectURL(response.data);
  const a = document.createElement('a');
  a.href = url;
  a.download = filepath.split('/').pop();
  a.click();
  window.URL.revokeObjectURL(url);
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// 初始加載
loadReports();
</script>
```

---

## 🛠️ 維護操作

### 清理舊報告

```bash
# 預覽要刪除的報告(乾運行)
curl -X DELETE "http://localhost:8000/api/results/reports/cleanup?days_to_keep=90&dry_run=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 實際刪除 90 天前的報告
curl -X DELETE "http://localhost:8000/api/results/reports/cleanup?days_to_keep=90&dry_run=false" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 監控磁碟使用

```bash
# 查看報告目錄大小
du -sh backend/reports

# 按項目查看
du -sh backend/reports/*

# 按日期查看
du -sh backend/reports/*/*/20260129
```

---

## ❓ 常見問題

### Q1: 報告沒有自動生成?

**檢查清單**:
1. ✅ 確認 `.env` 中 `REPORT_AUTO_SAVE=True`
2. ✅ 檢查測試是否成功完成
3. ✅ 查看後端日誌是否有錯誤
4. ✅ 確認 `reports/` 目錄有寫入權限

### Q2: 報告目錄在哪裡?

默認位置: `backend/reports/`

可通過環境變數修改:
```bash
REPORT_BASE_DIR=/var/webpdtool/reports
```

### Q3: 可以自定義 CSV 格式嗎?

目前使用固定格式(9 欄位增強格式)。

如需自定義,修改 `backend/app/services/report_service.py` 中的 `_write_csv_report()` 方法。

### Q4: 如何定期清理舊報告?

**方法 A: 手動 API 調用**
```bash
curl -X DELETE "http://localhost:8000/api/results/reports/cleanup?days_to_keep=90&dry_run=false"
```

**方法 B: Cron Job**
```bash
# 每天凌晨 2 點執行
0 2 * * * curl -X DELETE "http://localhost:8000/api/results/reports/cleanup?days_to_keep=90&dry_run=false" -H "Authorization: Bearer TOKEN"
```

---

## 📚 深入學習

- [完整功能文檔](./automatic-report-generation.md)
- [API 參考文檔](../../backend/app/api/results/reports.py)
- [報告服務源碼](../../backend/app/services/report_service.py)

---

**需要幫助?** 查看完整文檔或聯繫開發團隊
