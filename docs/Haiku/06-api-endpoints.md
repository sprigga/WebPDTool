# 06 - API 端點

## API 總體架構

```
/api/
├─ /auth              # 認證 (3 個端點)
├─ /users             # 使用者管理 (6 個端點)
├─ /projects          # 專案管理 (4 個端點)
├─ /stations          # 工站管理 (4 個端點)
├─ /testplans         # 測試計劃 (5 個端點)
├─ /tests             # 測試執行 (5 個端點)
├─ /tests/results     # 結果分析 (10+ 個端點)
├─ /measurements      # 測量控制 (3 個端點)
└─ /dut               # 裝置控制 (3 個端點)
```

## 認證端點 (/api/auth)

### POST /api/auth/login
**描述**: 使用者登入，獲取 JWT token

**請求體:**
```json
{
  "username": "engineer1",
  "password": "password123"
}
```

**響應 (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "username": "engineer1",
    "full_name": "工程師一",
    "email": "eng1@company.com",
    "role": "ENGINEER"
  }
}
```

**錯誤 (401):**
```json
{
  "detail": "使用者名稱或密碼錯誤"
}
```

### POST /api/auth/logout
**描述**: 使用者登出（可選，主要是前端清理 token）

**認證**: 需要有效 JWT token

**響應 (200):**
```json
{
  "message": "登出成功"
}
```

### POST /api/auth/refresh
**描述**: 重新整理過期的 token

**認證**: 需要有效 JWT token

**響應 (200):**
```json
{
  "access_token": "新的 token...",
  "token_type": "bearer"
}
```

---

## 使用者管理端點 (/api/users)

### GET /api/users
**描述**: 獲取使用者列表（分頁，可過濾）

**查詢引數:**
```
?offset=0&limit=20&search=engineer&role=ENGINEER&is_active=true
```

**響應:**
```json
{
  "total": 45,
  "items": [
    {
      "id": 2,
      "username": "engineer1",
      "full_name": "工程師一",
      "email": "eng1@company.com",
      "role": "ENGINEER",
      "is_active": true,
      "created_at": "2026-02-01T10:00:00Z"
    }
  ]
}
```

**權限**: 登入使用者可查看，僅 ADMIN 可看全部

### GET /api/users/{id}
**描述**: 獲取特定使用者詳情

**響應:**
```json
{
  "id": 2,
  "username": "engineer1",
  "full_name": "工程師一",
  "email": "eng1@company.com",
  "role": "ENGINEER",
  "is_active": true,
  "created_at": "2026-02-01T10:00:00Z"
}
```

### POST /api/users
**描述**: 建立新使用者（僅 ADMIN）

**請求體:**
```json
{
  "username": "newuser",
  "password": "initial_password_123",
  "full_name": "新使用者",
  "email": "newuser@company.com",
  "role": "ENGINEER"
}
```

**響應 (201):**
```json
{
  "id": 50,
  "username": "newuser",
  "full_name": "新使用者",
  "email": "newuser@company.com",
  "role": "ENGINEER",
  "is_active": true
}
```

### PUT /api/users/{id}
**描述**: 更新使用者資訊（僅 ADMIN 或本人）

**請求體:**
```json
{
  "full_name": "更新的名字",
  "email": "newemail@company.com",
  "is_active": true
}
```

**響應 (200):** 更新後的使用者物件

### PUT /api/users/{id}/password
**描述**: 修改使用者密碼（ADMIN 或本人）

**請求體:**
```json
{
  "old_password": "current_password",  // 非 admin 使用者需要
  "new_password": "new_password_123"
}
```

**響應 (200):**
```json
{
  "message": "密碼已更新"
}
```

### DELETE /api/users/{id}
**描述**: 刪除使用者（僅 ADMIN，不能刪除自己）

**響應 (204):** 無內容

---

## 專案管理端點 (/api/projects)

### GET /api/projects
**描述**: 獲取所有專案列表

**查詢引數:**
```
?is_active=true
```

**響應:**
```json
[
  {
    "id": 1,
    "project_code": "PROJ001",
    "project_name": "產品 A 測試",
    "description": "2026 年 Q1 測試",
    "is_active": true,
    "created_at": "2026-01-15T00:00:00Z"
  }
]
```

### GET /api/projects/{id}/stations
**描述**: 獲取專案下的所有工站

**響應:**
```json
[
  {
    "id": 1,
    "station_code": "STATION_A",
    "station_name": "功能測試工站 A",
    "project_id": 1,
    "is_active": true
  }
]
```

### POST /api/projects
**描述**: 建立新專案

**請求體:**
```json
{
  "project_code": "PROJ002",
  "project_name": "產品 B 測試",
  "description": "新產品測試計劃"
}
```

**響應 (201):** 新建專案物件

### PUT /api/projects/{id}
**描述**: 更新專案資訊

**請求體:**
```json
{
  "project_name": "更新的名稱",
  "description": "更新的描述",
  "is_active": true
}
```

**響應 (200):** 更新後的專案物件

---

## 工站管理端點 (/api/stations)

### GET /api/stations
**描述**: 獲取工站列表（可按 project_id 過濾）

**查詢引數:**
```
?project_id=1
```

### POST /api/stations
**描述**: 建立新工站

**請求體:**
```json
{
  "station_code": "STATION_B",
  "station_name": "功能測試工站 B",
  "project_id": 1,
  "test_plan_path": "/path/to/testplan.csv"
}
```

### GET /api/stations/{id}/testplans
**描述**: 獲取工站的所有測試計劃

**響應:**
```json
[
  {
    "id": 1,
    "item_no": 1,
    "item_name": "電源輸入",
    "test_type": "PowerRead",
    "upper_limit": 5.5,
    "lower_limit": 4.5,
    "limit_type": "both",
    "value_type": "float"
  }
]
```

### PUT /api/stations/{id}
**描述**: 更新工站

---

## 測試計劃端點 (/api/testplans)

### GET /api/testplans
**描述**: 獲取測試計劃列表

**查詢引數:**
```
?station_id=1&project_id=1
```

### POST /api/testplans
**描述**: 建立單個測試計劃

### POST /api/testplans/import
**描述**: 從 CSV 檔案匯入測試計劃

**請求體 (multipart/form-data):**
```
file: <CSV 檔案>
project_id: 1
station_id: 1
```

**CSV 格式 (PDTool4 相容):**
```
項次，品名規格，上限值，下限值，期望值，測試類型，限制類型，值類型，引數
1，電源輸入電壓，5.5,4.5,,PowerRead,both,float,"{""channel"":1}"
2，功率消耗，10.0,,, PowerRead,upper,float,"{""channel"":2}"
```

**響應 (200):**
```json
{
  "created_count": 25,
  "updated_count": 0,
  "failed_count": 0,
  "message": "成功匯入 25 個測試項"
}
```

### GET /api/testplans/{id}
**描述**: 獲取單個測試計劃詳情

### PUT /api/testplans/{id}
**描述**: 更新測試計劃

---

## 測試執行端點 (/api/tests)

### POST /api/tests/sessions/start
**描述**: 啟動新的測試 session

**請求體:**
```json
{
  "serial_number": "SN20260311001",
  "station_id": 1,
  "run_all_test": false
}
```

**響應 (201):**
```json
{
  "session_id": 123,
  "status": "RUNNING",
  "serial_number": "SN20260311001",
  "station_id": 1,
  "start_time": "2026-03-11T10:00:00Z"
}
```

### GET /api/tests/sessions/{id}/status
**描述**: 獲取測試 session 的當前狀態

**響應:**
```json
{
  "session_id": 123,
  "status": "RUNNING",
  "current_item_index": 5,
  "total_items": 25,
  "progress_percent": 20,
  "elapsed_seconds": 45
}
```

### GET /api/tests/sessions/{id}/results
**描述**: 獲取 session 的所有測試結果

**響應:**
```json
{
  "session_id": 123,
  "final_result": "PASS",
  "total_count": 25,
  "pass_count": 24,
  "fail_count": 1,
  "error_count": 0,
  "items": [
    {
      "item_no": 1,
      "item_name": "電源輸入",
      "measured_value": "5.15",
      "validation_result": "PASS",
      "execution_time_ms": 850
    }
  ]
}
```

### POST /api/tests/sessions/{id}/pause
**描述**: 暫停測試執行

**響應 (200):**
```json
{
  "message": "測試已暫停"
}
```

### POST /api/tests/sessions/{id}/abort
**描述**: 中止測試執行

**響應 (200):**
```json
{
  "message": "測試已中止"
}
```

---

## 結果分析端點 (/api/tests/results)

### GET /api/tests/results
**描述**: 查詢測試結果（支援複雜過濾）

**查詢引數:**
```
?project_id=1&station_id=1&start_date=2026-03-01&end_date=2026-03-11
&result=PASS&offset=0&limit=50
```

**響應:**
```json
{
  "total": 1240,
  "items": [
    {
      "id": 5001,
      "session_id": 123,
      "item_no": 1,
      "item_name": "電源輸入",
      "measured_value": "5.15",
      "validation_result": "PASS",
      "execution_time_ms": 850,
      "created_at": "2026-03-11T10:05:30Z"
    }
  ]
}
```

### GET /api/tests/results/export
**描述**: 匯出結果為 CSV 或 PDF

**查詢引數:**
```
?format=csv&project_id=1&start_date=2026-03-01&end_date=2026-03-11
```

**響應:** 檔案下載

### GET /api/tests/sessions/{id}/summary
**描述**: 獲取 session 的摘要統計

**響應:**
```json
{
  "session_id": 123,
  "final_result": "PASS",
  "total_time_seconds": 330,
  "statistics": {
    "total_items": 25,
    "pass_count": 24,
    "fail_count": 1,
    "error_count": 0,
    "pass_rate": 96.0
  },
  "failed_items": [
    {
      "item_no": 15,
      "item_name": "記憶體讀寫",
      "measured_value": "FAIL",
      "error": "記憶體檢測失敗"
    }
  ]
}
```

### GET /api/tests/reports/analysis
**描述**: 獲取趨勢和統計分析資料

**查詢引數:**
```
?project_id=1&days=30
```

**響應:**
```json
{
  "date_range": "2026-02-10 ~ 2026-03-11",
  "summary": {
    "total_sessions": 485,
    "pass_sessions": 468,
    "fail_sessions": 17,
    "overall_pass_rate": 96.5
  },
  "daily_statistics": [
    {
      "date": "2026-03-11",
      "sessions": 12,
      "pass_count": 11,
      "fail_count": 1,
      "pass_rate": 91.7
    }
  ],
  "top_failed_items": [
    {
      "item_no": 15,
      "item_name": "記憶體讀寫",
      "fail_count": 8,
      "fail_rate": 3.2
    }
  ]
}
```

---

## 測量控制端點 (/api/measurements)

### GET /api/measurements/instruments
**描述**: 獲取所有硬體狀態

**響應:**
```json
[
  {
    "instrument_id": "PSU1",
    "instrument_name": "電源裝置 1",
    "status": "IDLE",
    "connection_status": "CONNECTED",
    "last_used": "2026-03-11T09:50:00Z"
  }
]
```

### POST /api/measurements/reset
**描述**: 重置所有硬體狀態

**響應 (200):**
```json
{
  "message": "所有硬體已重置"
}
```

### GET /api/measurements/health
**描述**: 檢查硬體健康狀態

**響應:**
```json
{
  "overall_status": "HEALTHY",
  "instruments": {
    "PSU1": "OK",
    "SCOPE1": "OK",
    "DMM1": "WARNING - 需要校準"
  }
}
```

---

## 裝置控制端點 (/api/dut)

### POST /api/dut/reset
**描述**: 重置被測裝置（DUT）

**請求體:**
```json
{
  "reset_type": "hard"
}
```

**響應:**
```json
{
  "message": "裝置已重置"
}
```

### POST /api/dut/power
**描述**: 控制被測裝置的電源

**請求體:**
```json
{
  "action": "on",
  "power_level": 100
}
```

### GET /api/dut/status
**描述**: 獲取被測裝置狀態

**響應:**
```json
{
  "power_status": "ON",
  "temperature": 45.2,
  "last_reset": "2026-03-11T10:00:00Z"
}
```

---

## 通用錯誤處理

### 錯誤響應格式

```json
{
  "detail": "錯誤描述資訊"
}
```

### 常見 HTTP 狀態碼

| 狀態碼 | 含義 |
|--------|------|
| 200 | 成功 |
| 201 | 資源已建立 |
| 204 | 無內容 |
| 400 | 請求引數無效 |
| 401 | 未認證或 token 過期 |
| 403 | 權限不足 |
| 404 | 資源不存在 |
| 409 | 衝突 (如 duplicate key) |
| 500 | 伺服器錯誤 |

### 認證錯誤

```json
{
  "detail": "無效的 token"
}
```

### 權限錯誤

```json
{
  "detail": "您沒有權限訪問此資源"
}
```

---

## 速率限制

```
- 普通使用者：100 requests/minute
- 管理員：500 requests/minute
- 測試執行：不限制
```

## API 文件工具

**自動生成的 API 文件:**
- Swagger UI: `http://localhost:9100/docs`
- ReDoc: `http://localhost:9100/redoc`
- OpenAPI schema: `http://localhost:9100/openapi.json`

## 下一步

- **瞭解測試系統**: [07-measurement-system.md](07-measurement-system.md)
- **學習資料庫**: [05-database-schema.md](05-database-schema.md)
- **開發指南**: [10-development-guide.md](10-development-guide.md)
