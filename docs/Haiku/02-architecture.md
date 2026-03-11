# 02 - 架構設計

## 系統整體架構

```
┌──────────────────────────────────────────────────────────────┐
│                    使用者瀏覽器                                 │
├──────────────────────────────────────────────────────────────┤
│  Vue 3 SPA (Vite)                                            │
│  ├─ TestMain (測試執行 UI)                                    │
│  ├─ TestPlanManage (管理)                                    │
│  ├─ ProjectManage, UserManage                                │
│  ├─ ReportAnalysis (報表)                                    │
│  └─ Pinia 狀態管理 + Axios API 用戶端                          │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP/HTTPS (Port 9080)
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                Nginx 反向代理                                 │
│              (Port 9080 → 9100)                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    Frontend              Backend
    (SPA 靜態)            (FastAPI)
                         (Port 9100)

                         ↓

┌──────────────────────────────────────┐
│    MySQL 8.0 Database                │
│    Redis (日誌流)                    │
└──────────────────────────────────────┘
```

## 後端三層架構

```
┌─────────────────────────────────────────────────┐
│         API Layer (app/api/)                    │
│  ┌──────────────────────────────────────────┐  │
│  │ 9 個 FastAPI Router 模組:                   │  │
│  │ • auth.py - JWT 認證                      │  │
│  │ • users.py - 使用者 CRUD                    │  │
│  │ • projects.py - 專案管理                 │  │
│  │ • stations.py - 工站管理                 │  │
│  │ • testplans.py - 測試計劃                 │  │
│  │ • tests.py - 測試執行                    │  │
│  │ • measurements.py - 測量端點             │  │
│  │ • dut_control.py - 裝置控制              │  │
│  │ • results/ (7 個子路由)                   │  │
│  └──────────────────────────────────────────┘  │
└──────────────────┬────────────────────────────┘
                   │ 依賴注入 (async session)
                   ▼
┌─────────────────────────────────────────────────┐
│      Service Layer (app/services/)              │
│  ┌──────────────────────────────────────────┐  │
│  │ 核心業務邏輯：                             │  │
│  │ • TestEngine - 測試編排                  │  │
│  │ • MeasurementService - 測量執行          │  │
│  │ • InstrumentManager - 硬體管理 (單例)    │  │
│  │ • TestPlanService - 計劃操作             │  │
│  │ • ReportService - 報表生成               │  │
│  │ • AuthService - 認證服務                 │  │
│  └──────────────────────────────────────────┘  │
└──────────────────┬────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Measurement Layer (app/measurements/)          │
│  ┌──────────────────────────────────────────┐  │
│  │ BaseMeasurement 抽象基類：                │  │
│  │ • prepare() - 配置階段                   │  │
│  │ • execute() - 執行階段                   │  │
│  │ • cleanup() - 清理階段                   │  │
│  │ • validate_result() - PDTool4 驗證        │  │
│  │                                          │  │
│  │ 20+ 具體實現：                            │  │
│  │ • PowerRead, PowerSet, CommandTest...    │  │
│  │ • SFCMeasurement, GetSNMeasurement...    │  │
│  │ • RF_Tool, CMW100, L6MPU, MDO34...      │  │
│  └──────────────────────────────────────────┘  │
└──────────────────┬────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│      Data Layer (models/ + schemas/)            │
│  ┌──────────────────────────────────────────┐  │
│  │ ORM Models (SQLAlchemy 2.0):             │  │
│  │ • User - 認證和角色                      │  │
│  │ • Project - 專案容器                     │  │
│  │ • Station - 工站定義                     │  │
│  │ • TestPlan - CSV 匯入 的測試規範           │  │
│  │ • TestSession - 執行追蹤                 │  │
│  │ • TestResult - 測試結果                  │  │
│  │ • SFCLog - 製造資料日誌                  │  │
│  │                                          │  │
│  │ Pydantic Schemas (驗證):                │  │
│  │ • UserSchema, ProjectSchema...           │  │
│  └──────────────────────────────────────────┘  │
└──────────────────┬────────────────────────────┘
                   │
                   ▼
        MySQL 8.0 + Redis
```

## 前端元件架構

```
Router (Vue Router)
│
├─ Login (未認證)
│
├─ TestMain (核心)
│   ├─ 實時測試監控
│   ├─ runAllTest 模式顯示
│   └─ 錯誤彙總
│
├─ TestPlanManage (工程師)
│   ├─ CRUD 操作
│   └─ CSV 匯入
│
├─ ProjectManage (工程師)
│   └─ 專案和工站管理
│
├─ UserManage (系統管理員)
│   ├─ 使用者 CRUD
│   └─ 角色分配
│
├─ TestResults (所有角色)
│   ├─ 結果查詢
│   └─ 匯出功能
│
├─ TestHistory
├─ ReportAnalysis (ECharts 資料圖)
├─ TestExecution
└─ SystemConfig

    ↓ 所有使用

Pinia Stores (全域性狀態)
├─ auth.js
│  ├─ token (localStorage)
│  ├─ user
│  └─ isAuthenticated
├─ project.js
│  ├─ projects[]
│  ├─ currentProject
│  └─ currentStation
└─ users.js
   ├─ users[]
   └─ {fetchUsers/createUser/updateUser}

    ↓ 使用

Axios API Clients (api/ 目錄)
├─ client.js (全域性配置 + JWT 攔截)
├─ auth.js
├─ users.js
├─ projects.js
├─ tests.js
├─ measurements.js
└─ results.js
```

## 資料流全景

### 1. 測試執行流

```
UI (TestMain.vue)
  │ POST /api/tests/sessions/start
  │ {serial_number, station_id, run_all_test}
  │
  ▼
API (tests.py)
  │ 驗證輸入 → 建立 TestSession
  │
  ▼
TestEngine.start_test_session()
  │ 獲取 TestPlan 專案 → status=RUNNING
  │
  ▼
For each TestPlan item:
  │
  ├─ MeasurementService.execute_measurement()
  │   │
  │   ├─ measurement.prepare(params)
  │   ├─ measurement.execute(params) → MeasurementResult
  │   │   └─ InstrumentManager 傳送命令
  │   ├─ measurement.cleanup()
  │   ├─ validate_result() [PDTool4 邏輯]
  │   ├─ 儲存 TestResult 到資料庫
  │   │
  │   └─ If runAllTest: 繼續 (不中斷)
  │       If normal: 故障則中斷
  │
  ▼
TestEngine.complete_test_session()
  │ status=COMPLETED, final_result=PASS/FAIL
  │
  ▼
API → Frontend
  │ 返回結果總結 + 錯誤列表
  │
  ▼
UI 更新顯示
  └─ 實時進度 + 結果 + 錯誤 details
```

### 2. 測試計劃匯入流

```
CSV 檔案 (PDTool4 格式)
  │
  ▼
UI: POST /api/testplans/import
  │
  ▼
CSV Parser (app/utils/csv_parser.py)
  │ 對映列名 → 資料庫欄位
  │ 驗證必填欄位
  │ 解析 limits 和引數
  │
  ▼
TestPlanService.import_test_plan()
  │ 建立/更新 TestPlan 記錄
  │ 儲存 JSON 引數
  │ 事務執行
  │
  ▼
Database INSERT/UPDATE
  │
  ▼
UI 顯示匯入結果
  └─ 建立/更新數量統計
```

### 3. 認證流

```
使用者輸入憑證
  │ POST /api/auth/login
  │ {username, password}
  │
  ▼
AuthService.authenticate_user()
  │ 查詢 User 從資料庫
  │ 驗證 bcrypt 密碼
  │ 生成 JWT token
  │ 設定過期時間 (8h)
  │
  ▼
Response:
  {access_token, token_type, user}
  │
  ▼
Frontend (auth.js store)
  │ 儲存 token 到 localStorage
  │ 儲存 user 到 Pinia
  │
  ▼
Axios interceptor
  │ 所有請求自動新增:
  │ Authorization: Bearer <token>
  │
  ▼
Backend (get_current_user)
  │ 驗證 token 簽名
  │ 提取 user_id 宣告
  │ 授予/拒絕訪問
  │
  ▼
Token 過期 → POST /api/auth/refresh
  └─ 自動重新整理 token
```

## 關鍵架構模式

### 1. 非同步優先 (Async-First)

```python
# 資料庫操作
async def get_test_plans(db: AsyncSession, station_id: int):
    result = await db.execute(
        select(TestPlan).filter_by(station_id=station_id)
    )
    return result.scalars().all()

# 硬體通訊
async def send_measurement_command(instrument_id: str, cmd: str):
    response = await instrument.execute_command_async(cmd)
    return parse_response(response)

# 測試執行
async def execute_test_session(...):
    for test_item in items:
        result = await measurement_service.execute(test_item)
```

### 2. 三相測量生命週期

```
       prepare()          execute()          cleanup()
          ↓                   ↓                   ↓
    ┌──────────┐        ┌──────────┐       ┌──────────┐
    │ 配置階段 │ ---→   │ 執行階段 │  --→ │ 清理階段 │
    └──────────┘        └──────────┘       └──────────┘
    • 硬體配置            • 傳送命令         • 重置狀態
    • 引數解析            • 採集資料         • 釋放資源
    • 資源分配            • 返回結果         • 日誌記錄
```

### 3. Singleton 硬體管理

```python
class InstrumentManager:
    """確保全域性只有一個連線池"""
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
```

**優勢:**
- ✅ 避免重複連線
- ✅ 資源集中管理
- ✅ 易於狀態追蹤

### 4. 測量註冊表 (Registry)

```python
# app/measurements/registry.py
MEASUREMENT_REGISTRY = {
    'PowerRead': PowerReadMeasurement,
    'PowerSet': PowerSetMeasurement,
    'CommandTest': CommandTestMeasurement,
    'SFCtest': SFCMeasurement,
    # ...20+ types
}

# 使用
measurement_class = MEASUREMENT_REGISTRY.get(test_type)
measurement = measurement_class(instrument_manager)
result = await measurement.execute(params)
```

**優勢:**
- ✅ 執行時動態載入
- ✅ 易於擴充新型別
- ✅ 解耦實現

### 5. 依賴注入 (Dependency Injection)

```python
# FastAPI 自動注入
@router.post("/tests/start")
async def start_test(
    request: StartTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """db 和 current_user 由 FastAPI 自動提供"""
    ...
```

**優勢:**
- ✅ 易於測試 (mock 依賴)
- ✅ 鬆耦合
- ✅ 清晰的引數宣告

## 核心設計原則

| 原則 | 實現 | 優勢 |
|------|------|------|
| **關注點分離** | 分層架構 | 易於維護和測試 |
| **單一職責** | Service 類 | 程式碼複用性高 |
| **開閉原則** | 測量抽象 | 易於新增新型別 |
| **依賴反轉** | DI + interfaces | 易於擴充和測試 |
| **非同步優先** | async/await | 高併發效能 |

## 擴充性設計

### 新增新的測量型別
```python
# 1. 繼承 BaseMeasurement
class NewMeasurement(BaseMeasurement):
    async def prepare(self, params):
        # 配置
        pass
    async def execute(self, params):
        # 執行
        return MeasurementResult(...)
    async def cleanup(self):
        # 清理
        pass

# 2. 註冊到表
MEASUREMENT_REGISTRY['NewType'] = NewMeasurement

# 3. 在 CSV 中使用
# test_type = NewType
```

### 新增新的 API 路由
```python
# 1. 建立 router (app/api/new_feature.py)
router = APIRouter(prefix="/api/new")

@router.post("/action")
async def do_action(...):
    return {...}

# 2. 在 main.py 註冊
from app.api import new_feature
app.include_router(new_feature.router)

# 3. 前端呼叫
POST /api/new/action
```

### 新增新的前端頁面
```
1. 建立 View 元件 (frontend/src/views/NewPage.vue)
2. 建立 API 用戶端 (frontend/src/api/newpage.js)
3. 新增路由 (frontend/src/router/index.js)
4. (可選) 建立 Pinia store
5. 佈局和樣式使用 Element Plus
```

## 下一步

- **瞭解後端詳情**: [03-backend-structure.md](03-backend-structure.md)
- **瞭解測試系統**: [07-measurement-system.md](07-measurement-system.md)
- **學習資料庫**: [05-database-schema.md](05-database-schema.md)
