# 自動報告生成功能 (Automatic Report Generation)

> **版本**: 1.0
> **建立日期**: 2026-01-29
> **功能狀態**: ✅ 已實現

---

## 📋 功能概述

自動報告生成功能提供測試完成時的即時 CSV 報告保存,滿足生產線追溯和品質管理需求。

### 核心特性

✅ **自動化**: 測試完成時自動生成並保存 CSV 報告
✅ **組織化**: 按項目/站別/日期自動組織報告文件
✅ **可追溯**: 文件名包含序列號和時間戳
✅ **增強格式**: 包含錯誤訊息和執行時間
✅ **API 訪問**: 提供報告查詢、下載和管理接口

---

## 🏗️ 架構設計

### 1. 目錄結構

```
backend/
├── reports/                          # 報告根目錄
│   └── {project_name}/              # 項目目錄
│       └── {station_name}/          # 站別目錄
│           └── YYYYMMDD/            # 日期目錄
│               ├── SN001_20260129_143045.csv
│               ├── SN002_20260129_143215.csv
│               └── SN003_20260129_143530.csv
```

### 2. 組件架構

```
┌─────────────────────────────────────────────────────┐
│                  Test Engine                        │
│  (app/services/test_engine.py)                     │
│                                                     │
│  測試完成 → _finalize_test_session()               │
│                     ↓                               │
└─────────────────────┼───────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│              Report Service                         │
│  (app/services/report_service.py)                  │
│                                                     │
│  • save_session_report()                           │
│  • _get_report_directory()                         │
│  • _generate_filename()                            │
│  • _write_csv_report()                             │
│                     ↓                               │
└─────────────────────┼───────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│           CSV Report File                           │
│  reports/{project}/{station}/{date}/{serial}.csv   │
└─────────────────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│              Reports API                            │
│  (app/api/results/reports.py)                      │
│                                                     │
│  • GET /reports/list          (查詢報告列表)       │
│  • GET /reports/download/{id}  (下載報告)          │
│  • DELETE /reports/cleanup     (清理舊報告)         │
└─────────────────────────────────────────────────────┘
```

---

## 📝 CSV 報告格式

### WebPDTool 增強格式

```csv
Item No, Item Name, Result, Measured Value, Min Limit, Max Limit, Error Message, Execution Time (ms), Test Time
1, Voltage_Test, PASS, 12.5, 10.0, 15.0, , 250, 2026-01-29T14:30:45
2, Current_Test, PASS, 0.85, 0.1, 1.0, , 180, 2026-01-29T14:30:46
3, Resistance_Test, FAIL, 110, 95, 105, Value out of range, 150, 2026-01-29T14:30:47
4, Temperature_Test, PASS, 25.5, -10, 80, , 200, 2026-01-29T14:30:48
```

### 欄位說明

| 欄位 | 類型 | 說明 | 範例 |
|------|------|------|------|
| Item No | Integer | 測試項目編號 | 1 |
| Item Name | String | 測試項目名稱 | Voltage_Test |
| Result | String | 測試結果 | PASS/FAIL/ERROR/SKIP |
| Measured Value | String | 測量值 | 12.5 |
| Min Limit | Float | 下限 | 10.0 |
| Max Limit | Float | 上限 | 15.0 |
| Error Message | String | 錯誤訊息 | Value out of range |
| Execution Time (ms) | Integer | 執行時間(毫秒) | 250 |
| Test Time | ISO 8601 | 測試時間 | 2026-01-29T14:30:45 |

### 與 Polish 格式對比

#### Polish 標準格式
```csv
ItemKey, ID, LL, UL, TestValue, TestDateTime, Result
Power_Test, voltage_1, 10.0, 15.0, 12.5, 26-01-28_14:30:45, P
```

#### WebPDTool 增強點
1. ✅ **更詳細**: 增加錯誤訊息和執行時間
2. ✅ **標準化**: 使用 ISO 8601 時間格式
3. ✅ **完整性**: 保留所有測試項目信息
4. ✅ **可讀性**: 使用完整的 PASS/FAIL 而非 P/F

---

## 🔧 配置說明

### 環境變數 (.env)

```bash
# Report Generation Configuration
REPORT_BASE_DIR=reports                    # 報告根目錄
REPORT_AUTO_SAVE=True                      # 啟用自動保存
REPORT_DATE_FORMAT=%Y%m%d                  # 日期格式
REPORT_TIMESTAMP_FORMAT=%Y%m%d_%H%M%S      # 時間戳格式
REPORT_MAX_AGE_DAYS=0                      # 自動刪除天數(0=不刪除)
REPORT_CSV_ENCODING=utf-8                  # CSV 編碼
```

### 配置文件

位置: `backend/app/core/report_config.py`

```python
from app.core.report_config import report_settings

# 獲取報告目錄
report_dir = report_settings.REPORT_BASE_DIR

# 檢查是否啟用自動保存
if report_settings.REPORT_AUTO_SAVE:
    # 自動保存邏輯
    pass
```

---

## 🚀 使用方法

### 1. 自動報告生成(無需手動操作)

當測試會話完成時,系統會自動:

1. 查詢測試會話和結果
2. 確定報告目錄(`reports/{project}/{station}/{date}/`)
3. 生成文件名(`{serial}_{timestamp}.csv`)
4. 寫入 CSV 報告
5. 記錄日誌

**日誌輸出範例**:
```
INFO: Test session 123 finalized: PASSED (10/10 passed)
INFO: Test report saved: reports/MyProject/Station1/20260129/SN001_20260129_143045.csv
```

### 2. API 查詢報告

#### 列出所有報告

```bash
GET /api/results/reports/list
```

**回應範例**:
```json
[
  {
    "filename": "SN001_20260129_143045.csv",
    "filepath": "reports/MyProject/Station1/20260129/SN001_20260129_143045.csv",
    "project": "MyProject",
    "station": "Station1",
    "date": "20260129",
    "size_bytes": 2048,
    "modified_at": "2026-01-29T14:30:45"
  }
]
```

#### 按條件過濾

```bash
GET /api/results/reports/list?project_name=MyProject&station_name=Station1&date_from=2026-01-01&date_to=2026-01-31&limit=50
```

**參數說明**:
- `project_name`: 項目名稱過濾
- `station_name`: 站別名稱過濾
- `date_from`: 起始日期(YYYY-MM-DD)
- `date_to`: 結束日期(YYYY-MM-DD)
- `limit`: 最多返回數量(1-1000)

#### 下載特定會話的報告

```bash
GET /api/results/reports/download/{session_id}
```

**回應**: CSV 文件下載

#### 按路徑下載報告

```bash
GET /api/results/reports/download-by-path?filepath=reports/MyProject/Station1/20260129/SN001_20260129_143045.csv
```

**安全性**: 自動檢查路徑是否在報告目錄內,防止路徑遍歷攻擊

### 3. 報告清理

#### 預覽要刪除的報告(乾運行)

```bash
DELETE /api/results/reports/cleanup?days_to_keep=90&dry_run=true
```

**回應範例**:
```json
{
  "dry_run": true,
  "cutoff_date": "2025-10-31T00:00:00",
  "days_to_keep": 90,
  "total_old_reports": 150,
  "deleted_count": 0,
  "total_size_bytes": 307200,
  "total_size_mb": 0.3,
  "reports": [
    {
      "filepath": "reports/MyProject/Station1/20251015/SN001.csv",
      "filename": "SN001.csv",
      "modified_at": "2025-10-15T10:30:00",
      "size_bytes": 2048
    }
  ]
}
```

#### 實際刪除舊報告

```bash
DELETE /api/results/reports/cleanup?days_to_keep=90&dry_run=false
```

#### 按項目/站別清理

```bash
DELETE /api/results/reports/cleanup?days_to_keep=30&project_name=MyProject&station_name=Station1&dry_run=false
```

---

## 🔍 程式碼範例

### Python: 使用 ReportService

```python
from app.services.report_service import report_service
from app.core.database import get_db

# 手動保存報告
db = next(get_db())
report_path = report_service.save_session_report(session_id=123, db=db)
print(f"Report saved: {report_path}")

# 查詢報告路徑
report_path = report_service.get_report_path(session_id=123, db=db)
if report_path and report_path.exists():
    print(f"Report exists: {report_path}")

# 列出報告
from datetime import datetime
reports = report_service.list_reports(
    project_name="MyProject",
    station_name="Station1",
    date_from=datetime(2026, 1, 1),
    date_to=datetime(2026, 1, 31)
)
print(f"Found {len(reports)} reports")
```

### JavaScript/TypeScript: API 調用

```typescript
// 列出報告
async function listReports(filters: {
  projectName?: string;
  stationName?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
}) {
  const params = new URLSearchParams();
  if (filters.projectName) params.set('project_name', filters.projectName);
  if (filters.stationName) params.set('station_name', filters.stationName);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.limit) params.set('limit', filters.limit.toString());

  const response = await fetch(`/api/results/reports/list?${params}`);
  return await response.json();
}

// 下載報告
async function downloadReport(sessionId: number) {
  const response = await fetch(`/api/results/reports/download/${sessionId}`);
  const blob = await response.blob();

  // 觸發下載
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `report_${sessionId}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
}

// 清理舊報告
async function cleanupOldReports(daysToKeep: number, dryRun: boolean = true) {
  const response = await fetch(
    `/api/results/reports/cleanup?days_to_keep=${daysToKeep}&dry_run=${dryRun}`,
    { method: 'DELETE' }
  );
  return await response.json();
}
```

---

## 📊 與 Polish 框架對比

| 功能 | Polish | WebPDTool | 狀態 |
|------|--------|-----------|------|
| **CSV 報告生成** | ✅ default_report.py | ✅ report_service.py | ✅ 完成 |
| **自動保存** | ✅ 測試完成時 | ✅ 測試完成時 | ✅ 完成 |
| **目錄組織** | ❌ 單一目錄 | ✅ 按項目/站別/日期 | ✅ 增強 |
| **文件命名** | ✅ {serial}_{time}.csv | ✅ {serial}_{timestamp}.csv | ✅ 完成 |
| **報告格式** | 基礎(7欄) | 增強(9欄) | ✅ 增強 |
| **錯誤訊息** | ❌ 無 | ✅ 有 | ✅ 增強 |
| **執行時間** | ❌ 無 | ✅ 有 | ✅ 增強 |
| **收據打印** | ✅ print_receipt.py | ❌ 無 | ⚠️ 未實現 |
| **熱敏打印機** | ✅ thermal_printer.py | ❌ 無 | ⚠️ 未實現 |
| **API 訪問** | ❌ 無 | ✅ REST API | ✅ 增強 |
| **報告查詢** | ❌ 無 | ✅ 有 | ✅ 增強 |
| **自動清理** | ❌ 無 | ✅ 有 | ✅ 增強 |

### 總結

✅ **核心功能**: WebPDTool 完整實現 Polish 的 CSV 報告生成功能
✅ **增強功能**: 增加了錯誤訊息、執行時間、API 訪問等現代化特性
⚠️ **缺失功能**: 收據打印和熱敏打印機驅動(適用於 Web 架構不需要)

---

## 🔐 安全考量

### 1. 路徑遍歷防護

```python
# 檢查文件路徑是否在報告目錄內
report_base = report_service.base_report_dir.resolve()
try:
    report_path = report_path.resolve()
    report_path.relative_to(report_base)
except ValueError:
    raise HTTPException(status_code=403, detail="Access denied")
```

### 2. 權限控制

所有報告 API 端點都需要身份驗證:
```python
current_user: dict = Depends(get_current_active_user)
```

### 3. 文件命名安全

```python
# 清理序列號中的特殊字符
safe_serial = serial_number.replace(" ", "_").replace("/", "_")
```

---

## 📈 性能考量

### 1. 報告生成

- **異步處理**: 報告生成不會阻塞測試流程
- **錯誤容忍**: 報告生成失敗不影響測試會話完成

```python
try:
    report_path = report_service.save_session_report(session_id, db)
except Exception as report_error:
    # 記錄錯誤但不影響測試
    logger.error(f"Error generating test report: {report_error}")
```

### 2. 文件 I/O

- **目錄緩存**: 目錄結構在首次訪問時創建
- **批量查詢**: 使用 `glob` 高效搜索文件

### 3. 磁碟空間管理

- **自動清理**: 提供 API 定期清理舊報告
- **大小監控**: API 返回文件大小信息

---

## 🧪 測試

### 單元測試

```python
# tests/services/test_report_service.py

def test_save_session_report(db_session, test_session):
    """測試報告保存"""
    report_path = report_service.save_session_report(
        session_id=test_session.id,
        db=db_session
    )
    assert report_path is not None
    assert report_path.exists()
    assert report_path.suffix == '.csv'

def test_report_directory_structure(db_session, test_session):
    """測試目錄結構"""
    report_path = report_service.save_session_report(
        session_id=test_session.id,
        db=db_session
    )
    parts = report_path.parts
    assert parts[-4] == test_session.project.name
    assert parts[-3] == test_session.station.name
    # YYYYMMDD 格式
    assert len(parts[-2]) == 8
    assert parts[-2].isdigit()
```

### 集成測試

```python
# tests/api/test_reports_api.py

def test_list_reports(client, auth_headers):
    """測試報告列表 API"""
    response = client.get(
        "/api/results/reports/list",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_download_report(client, auth_headers, test_session):
    """測試報告下載 API"""
    response = client.get(
        f"/api/results/reports/download/{test_session.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/csv'
```

---

## 📚 相關文檔

- [Polish 框架分析](../Polish/Polish_Analysis.md)
- [Polish 報告模組分析](../Polish/Polish_Report_Analysis.md)
- [測試引擎服務](../../backend/app/services/test_engine.py)
- [報告服務](../../backend/app/services/report_service.py)
- [Reports API](../../backend/app/api/results/reports.py)

---

## 🔄 未來改進

### 短期 (1-2 週)
- [ ] 添加報告格式驗證
- [ ] 實現報告壓縮歸檔
- [ ] 添加報告統計儀表板

### 中期 (1-2 月)
- [ ] 支持多種報告格式 (JSON, XML)
- [ ] 實現報告模板自定義
- [ ] 添加報告電子郵件發送

### 長期 (3-6 月)
- [ ] 收據格式化輸出 (可選)
- [ ] 網絡打印機支持 (可選)
- [ ] 報告數據分析工具

---

**文檔版本**: 1.0
**最後更新**: 2026-01-29
**維護者**: Development Team
