# WebPDTool - Web-based Testing System

基於 Vue 3 + FastAPI 的現代化測試系統，從桌面應用程式 PDTool4 重構而來。

## 專案概述

WebPDTool 是一個 Web 化的產品測試系統，用於執行自動化測試、記錄測試結果。系統採用前後端分離架構，提供完整的測試管理、執行和結果查詢功能。

**專案狀態**: 核心架構已完成 (約 75% 完成)
**最新更新**: 2026-01-05 - 完成 PDTool4 測量驗證邏輯與 runAllTest 模式整合

### 主要特色

- ✅ **完整 PDTool4 相容性**: 支援所有 7 種 limit_type 和 3 種 value_type
- ✅ **runAllTest 模式**: 遇到錯誤時繼續執行測試,與 PDTool4 完全一致
- ✅ **測量模組架構**: BaseMeasurement 抽象基礎類別 + MEASUREMENT_REGISTRY 註冊表
- ✅ **測試引擎**: TestEngine 測試編排器 + InstrumentManager 儀器管理器
- ✅ **完整 API 層**: 8 個 API 模組,70+ 端點
- ✅ **現代化前端**: Vue 3 Composition API + Element Plus UI

## 技術堆疊

### 前端
- **框架**: Vue 3 (Composition API)
- **UI 庫**: Element Plus
- **狀態管理**: Pinia
- **路由**: Vue Router
- **HTTP 客戶端**: Axios
- **建置工具**: Vite
- **開發端口**: 9080 (前端服務)

### 後端
- **框架**: FastAPI
- **語言**: Python 3.11+
- **ORM**: SQLAlchemy 2.0
- **資料驗證**: Pydantic v2
- **認證**: JWT (JSON Web Tokens)
- **非同步支援**: asyncio/async-await
- **API 文件**: Swagger UI (/docs)
- **服務端口**: 9100 (後端 API)

### 資料庫
- **主資料庫**: MySQL 8.0+
- **資料庫端口**: 33306 (Docker 容器映射)
- **連線池**: SQLAlchemy async engine

### 部署與容器化
- **容器化**: Docker & Docker Compose
- **反向代理**: Nginx (內建於前端容器)
- **健康檢查**: Docker healthcheck 機制

## 專案結構

```
WebPDTool/
├── backend/                    # FastAPI 後端應用
│   ├── app/
│   │   ├── api/               # RESTful API 路由 (8 模組, 70+ 端點)
│   │   │   ├── auth.py        # 認證 API
│   │   │   ├── projects.py    # 專案管理 API
│   │   │   ├── stations.py    # 站別管理 API
│   │   │   ├── testplans.py   # 測試計劃 API
│   │   │   ├── tests.py       # 測試執行 API
│   │   │   ├── measurements.py           # 測量執行 API
│   │   │   └── measurement_results.py    # 測試結果查詢 API
│   │   ├── models/            # SQLAlchemy 資料模型 (7 模組)
│   │   │   ├── user.py        # 使用者模型
│   │   │   ├── project.py     # 專案模型
│   │   │   ├── station.py     # 站別模型
│   │   │   ├── testplan.py    # 測試計劃模型
│   │   │   ├── test_session.py    # 測試會話模型
│   │   │   ├── test_result.py     # 測試結果模型
│   │   │   └── sfc_log.py         # SFC 日誌模型
│   │   ├── services/          # 業務邏輯層 (5 服務)
│   │   │   ├── auth.py        # 認證服務
│   │   │   ├── measurement_service.py  # 測量服務 (含 runAllTest 模式)
│   │   │   ├── test_engine.py         # 測試引擎
│   │   │   ├── instrument_manager.py  # 儀器管理器
│   │   │   └── sfc_service.py         # SFC 服務
│   │   ├── measurements/      # 測量模組 (3 模組)
│   │   │   ├── base.py        # 測量基礎類別 (BaseMeasurement, 含 PDTool4 驗證邏輯)
│   │   │   ├── implementations.py  # 測量實作 (PowerSet, PowerRead, CommandTest, etc.)
│   │   │   └── registry.py    # 測量類型註冊表
│   │   ├── schemas/           # Pydantic 資料驗證模型
│   │   ├── core/              # 核心功能 (日誌、資料庫)
│   │   ├── utils/             # 工具函數
│   │   ├── config.py          # 應用配置
│   │   ├── dependencies.py    # FastAPI 依賴注入
│   │   └── main.py            # 應用入口點
│   ├── scripts/               # 工具腳本
│   │   ├── import_testplan.py # 測試計劃匯入工具
│   │   ├── batch_import.sh    # 批量匯入腳本
│   │   └── test_refactoring.py # 重構測試套件
│   ├── Dockerfile             # 後端 Docker 映像
│   └── pyproject.toml         # Python 專案配置
├── frontend/                  # Vue 3 前端應用
│   ├── src/
│   │   ├── views/             # 頁面組件 (6 個)
│   │   │   ├── Login.vue      # 登入頁面
│   │   │   ├── SystemConfig.vue      # 系統配置
│   │   │   ├── TestMain.vue          # 測試執行主介面 (含 runAllTest 模式)
│   │   │   ├── TestPlanManage.vue    # 測試計劃管理
│   │   │   ├── TestExecution.vue     # 測試執行監控
│   │   │   └── TestHistory.vue       # 測試歷史查詢
│   │   ├── components/        # 可複用組件
│   │   │   └── ProjectStationSelector.vue  # 專案站別選擇器
│   │   ├── api/               # API 客戶端 (5 模組)
│   │   │   ├── client.js      # Axios 客戶端配置
│   │   │   ├── auth.js        # 認證 API
│   │   │   ├── projects.js    # 專案 API
│   │   │   ├── testplans.js   # 測試計劃 API
│   │   │   └── tests.js       # 測試執行 API
│   │   ├── stores/            # Pinia 狀態管理
│   │   ├── router/            # Vue Router 配置
│   │   ├── utils/             # 工具函數
│   │   ├── App.vue            # 根組件
│   │   └── main.js            # 應用入口點
│   ├── Dockerfile             # 前端 Docker 映像
│   ├── nginx.conf             # Nginx 配置
│   └── package.json           # NPM 專案配置
├── database/                  # 資料庫設計
│   ├── schema.sql             # 資料庫 Schema
│   └── seed_data.sql          # 初始資料
├── docker-compose.yml         # Docker Compose 配置
├── .env.example               # 環境變數範本
├── docs/                      # 技術文檔
│   ├── REFACTORING_SUMMARY.md         # 重構完成報告
│   ├── PDTool4_Measurement_Module_Analysis.md  # PDTool4 分析
│   ├── README_import_testplan.md       # 測試計劃匯入指南
│   ├── architecture_workflow.md        # 架構與工作流程
│   └── ...                    # 其他文檔
└── PDTool4/                   # 舊系統 (供參考，不納入新系統)


## 系統架構

### 後端架構

#### API 層 (backend/app/api/)
- **auth.py**: 認證與授權管理
- **projects.py**: 專案 CRUD 操作
- **stations.py**: 站別管理
- **testplans.py**: 測試計劃管理與 CSV 上傳
- **tests.py**: 測試會話執行與控制
- **measurements.py**: 測量任務執行
- **measurement_results.py**: 測試結果查詢與匯出

#### 資料模型層 (backend/app/models/)
- **user.py**: 使用者模型 (Admin/Engineer/Operator)
- **project.py**: 專案模型
- **station.py**: 測試站別模型
- **testplan.py**: 測試計劃項目模型
- **test_session.py**: 測試會話模型 (狀態追蹤)
- **test_result.py**: 測試結果模型
- **sfc_log.py**: SFC 整合日誌模型

#### 服務層 (backend/app/services/)
- **auth.py**: JWT Token 管理、密碼驗證
- **test_engine.py**: 測試編排引擎 (TestEngine)
  - 非同步測試執行
  - 測試會話狀態管理
  - 測量任務調度
- **instrument_manager.py**: 儀器管理器 (Singleton)
  - 儀器連線池管理
  - 儀器狀態追蹤
  - 連線重置機制
- **measurement_service.py**: 測量服務協調

#### 測量模組層 (backend/app/measurements/)
- **base.py**: BaseMeasurement 抽象基礎類別
  - 定義測量介面規範 (prepare/execute/cleanup)
  - MeasurementResult 資料結構
  - 結果驗證機制 (支援 PDTool4 所有 limit 類型)
  - 值類型轉換 (string/integer/float)
  - **PDTool4 驗證邏輯完整整合** (支援 7 種 limit_type, 3 種 value_type)
  - runAllTest 模式錯誤處理
  - PDTool4 儀器錯誤檢測 ("No instrument found", "Error:")
- **implementations.py**: 測量實作
  - PowerSet (電源供應器控制)
  - PowerRead (電壓/電流讀取)
  - CommandTest (命令執行測試)
  - SFCtest (SFC 整合測試)
  - getSN (序號取得)
  - OPjudge (操作員確認)
  - Other (自定義實作)
- **registry.py**: MEASUREMENT_REGISTRY 測量類型註冊表

### 前端架構

#### 頁面組件 (frontend/src/views/)
- **Login.vue**: 使用者登入介面
- **SystemConfig.vue**: 系統配置頁面 (專案/站別選擇)
- **TestMain.vue**: 測試執行主控台 (495 行，仿 PDTool4 UI)
  - 測試資訊顯示區
  - 配置面板 (專案/站別/測試計劃選擇)
  - 測試計劃表格
  - 控制面板 (條碼輸入、開始/停止)
  - 進度顯示
  - 狀態訊息區
  - SFC 配置對話框
- **TestPlanManage.vue**: 測試計劃管理介面
- **TestExecution.vue**: 測試執行監控
- **TestHistory.vue**: 測試歷史查詢與分析

#### API 客戶端 (frontend/src/api/)
- **client.js**: Axios 實例配置、請求/回應攔截器、錯誤處理
- **auth.js**: 登入、登出、Token 刷新
- **projects.js**: 專案列表、建立、更新、刪除
- **testplans.js**: 測試計劃 CRUD、CSV 上傳、重新排序
- **tests.js**: 測試會話管理、執行控制、結果上傳、儀器狀態

#### 狀態管理 (frontend/src/stores/)
- **auth.js**: 使用者認證狀態 (Pinia)
- **project.js**: 當前專案與站別狀態

### 資料庫架構

#### 核心表格
- **users**: 使用者資料 (username, password_hash, role, is_active)
- **projects**: 專案資料 (project_name, description)
- **stations**: 測試站別 (station_name, project_id, config_json)
- **testplans**: 測試計劃項目 (step_number, item_name, spec, measurement_type...)
- **test_sessions**: 測試會話 (barcode, status, start_time, end_time...)
- **test_results**: 測試結果 (measured_value, result, error_msg...)
- **sfc_logs**: SFC 整合日誌

## API 端點列表

### 認證 API (/api/auth)
- `POST /login` - 使用者登入
- `POST /login-form` - 表單登入 (OAuth2 相容)
- `POST /logout` - 登出
- `GET /me` - 取得當前使用者資訊
- `POST /refresh` - 刷新 Token

### 專案管理 API (/api/projects)
- `GET /` - 取得專案列表
- `GET /{project_id}` - 取得專案詳情 (含站別)
- `POST /` - 建立新專案
- `PUT /{project_id}` - 更新專案
- `DELETE /{project_id}` - 刪除專案

### 站別管理 API (/api)
- `GET /projects/{project_id}/stations` - 取得專案的站別列表
- `GET /stations/{station_id}` - 取得站別詳情
- `POST /stations` - 建立新站別
- `PUT /stations/{station_id}` - 更新站別
- `DELETE /stations/{station_id}` - 刪除站別

### 測試計劃 API (/api)
- `GET /stations/{station_id}/testplan` - 取得站別的測試計劃
- `GET /stations/{station_id}/testplan-names` - 取得測試計劃名稱列表
- `GET /stations/{station_id}/testplan-map` - 取得測試點映射
- `POST /stations/{station_id}/testplan/upload` - 上傳 CSV 測試計劃
- `POST /testplans` - 建立測試項目
- `GET /testplans/{testplan_id}` - 取得測試項目詳情
- `PUT /testplans/{testplan_id}` - 更新測試項目
- `DELETE /testplans/{testplan_id}` - 刪除測試項目
- `POST /testplans/bulk-delete` - 批量刪除測試項目
- `POST /testplans/reorder` - 重新排序測試項目
- `POST /testplans/validate-test-point` - 驗證測試點
- `GET /sessions/{session_id}/test-results` - 取得會話測試結果

### 測試執行 API (/api/tests)
- `POST /sessions` - 建立測試會話
- `POST /sessions/{session_id}/start` - 開始測試執行
- `POST /sessions/{session_id}/stop` - 停止測試執行
- `GET /sessions/{session_id}/status` - 取得測試會話即時狀態
- `GET /sessions/{session_id}/results` - 取得測試會話的所有結果

### 測量執行 API (/api/measurements)
- `POST /execute` - 執行單個測量
- `POST /batch-execute` - 批量執行測量
- `GET /types` - 取得支援的測量類型
- `GET /instruments` - 取得儀器狀態列表
- `GET /instruments/available` - 取得可用儀器列表
- `POST /instruments/{instrument_id}/reset` - 重置儀器
- `GET /session/{session_id}/results` - 取得會話測量結果
- `POST /validate-params` - 驗證測量參數
- `GET /measurement-templates` - 取得測量模板
- `POST /execute-with-dependencies` - 執行具相依性的測量

### 測試結果查詢 API (/api/measurement-results)
- `GET /sessions` - 查詢測試會話 (支援篩選與分頁)
- `GET /sessions/{session_id}` - 取得會話詳細結果
- `GET /results` - 查詢測試結果 (支援多條件篩選)
- `GET /summary` - 取得測試結果統計摘要
- `GET /export/csv/{session_id}` - 匯出測試結果為 CSV
- `DELETE /sessions/{session_id}` - 刪除測試會話與結果
- `POST /cleanup` - 清理舊測試資料
- 測量結果 CRUD 操作

## 開發進度

### ✅ 階段 1: 基礎設施建置 (已完成)
- [x] 專案目錄結構建立
- [x] 後端 FastAPI 專案初始化
- [x] 前端 Vue 3 專案初始化
- [x] 資料庫 Schema 設計
- [x] Docker 容器化配置
- [x] Docker Compose 編排

### ✅ 階段 2: 核心認證系統 (已完成)
- [x] 後端認證模組 (JWT Token)
- [x] 使用者資料模型
- [x] 登入/登出 API
- [x] 前端登入介面
- [x] Token 管理和路由守衛
- [x] 角色權限控制 (Admin/Engineer/Operator)

### ✅ 階段 3: 專案與站別管理 (已完成)
- [x] 專案資料模型和 API
- [x] 站別資料模型和 API
- [x] 前端專案選擇組件
- [x] 前端站別選擇功能
- [x] 專案與站別關聯管理
- [x] 系統配置頁面

### ✅ 階段 4: 測試計劃管理 (已完成)
- [x] CSV 檔案解析功能
- [x] 測試計劃上傳 API
- [x] 測試計劃 CRUD API
- [x] 前端測試計劃管理介面
- [x] 測試項目編輯功能
- [x] 批量刪除和排序功能
- [x] 測試計劃表格顯示與操作
- [x] 測試計劃匯入工具 (scripts/import_testplan.py)

### ✅ 階段 5: 測試執行引擎 (核心架構完成)
- [x] 測試會話資料模型 (TestSession)
- [x] 測試結果資料模型 (TestResult)
- [x] BaseMeasurement 抽象基礎類別
  - [x] **PDTool4 驗證邏輯完整整合** (支援 7 種 limit_type)
  - [x] runAllTest 模式錯誤處理
  - [x] PDTool4 儀器錯誤檢測
- [x] 測量實作模組
  - [x] PowerSet, PowerRead, CommandTest
  - [x] SFCtest, getSN, OPjudge, Other
  - [x] 完整的 limit 類型支援 (lower/upper/both/equality/inequality/partial/none)
  - [x] 值類型轉換 (string/integer/float)
- [x] TestEngine 測試編排引擎
  - [x] 非同步測試執行
  - [x] 測試會話狀態管理
  - [x] 測量任務調度
- [x] InstrumentManager 儀器管理器
  - [x] Singleton 模式實作
  - [x] 儀器連線池管理
  - [x] 儀器狀態追蹤
- [x] 測試執行相關 API (5+ 端點)
- [x] 測量執行相關 API (10 端點)
- [x] 測試會話管理 API
- [x] 測試結果查詢與匯出 API
- [x] 前端測試執行主介面 (TestMain.vue)
  - [x] PDTool4 風格 UI 設計
  - [x] 測試控制面板
  - [x] 條碼掃描輸入
  - [x] 測試計劃表格顯示
  - [x] 進度與狀態顯示
  - [x] **runAllTest 模式整合** (錯誤收集但繼續執行)
- [x] 即時狀態輪詢機制
- [x] 儀器狀態查詢與重置
- [x] MEASUREMENT_REGISTRY 測量類型註冊表
- [x] 測試計劃匯入工具與批量匯入腳本
- [x] 完整的測試覆蓋 (9 個測試類別,100% 通過)
- ⚠️ 實際儀器驅動實作 (目前為 stub/dummy 實作)
- ⏳ WebSocket 即時通訊 (計劃中，目前使用輪詢)
- ⏳ 前端測試歷史查詢介面完整實作
- ⏳ 圖表分析功能
- ⏳ PDF 報表生成


### ⏳ 階段 6: 進階功能 (待實作)
- [ ] 實際儀器驅動實作 (取代 dummy implementations)
- [ ] WebSocket 即時通訊機制
- [ ] Modbus TCP/RTU 通訊模組
- [ ] Modbus 設備配置管理
- [ ] Modbus 讀寫操作 API
- [ ] SFC WebService 客戶端實作
- [ ] SFC 連線測試與錯誤處理
- [ ] 前端測試歷史查詢完整介面
- [ ] 測試結果趨勢分析與圖表
- [ ] PDF 報表生成
- [ ] 儀器校驗管理
- [ ] 系統日誌與審計功能
- [ ] 權限細粒度控制
- [ ] 多語系支援
- [ ] 自動化測試覆蓋


### ⏳ 階段 7: 生產環境優化 (待實作)
- [ ] 安全性強化 (輸入驗證、SQL 注入防護)
- [ ] 效能優化 (資料庫查詢、快取機制)
- [ ] 錯誤處理完善
- [ ] API 速率限制
- [ ] 監控與告警機制
- [ ] 備份與恢復策略

## 快速開始

### 系統需求

- **Docker Engine**: 20.10+
- **Docker Compose**: 2.0+
- **端口需求**: 
  - 9080 (前端服務)
  - 9100 (後端 API)
  - 33306 (MySQL 資料庫)

### 方法 1: 使用 Docker Compose (推薦)

**步驟 1: 配置環境變數**

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，設定必要參數
# 特別注意: SECRET_KEY、MYSQL_ROOT_PASSWORD、MYSQL_PASSWORD
vim .env
```

**步驟 2: 啟動服務**

```bash
# 建置並啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

**步驟 3: 初始化資料庫**

```bash
# 等待資料庫啟動完成 (約 30 秒)
# 執行資料庫初始化
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/schema.sql
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_data.sql
```

**步驟 4: 存取應用**

- **前端介面**: http://localhost:9080
- **後端 API 文件**: http://localhost:9100/docs
- **預設帳號**:
  - 管理員: `admin` / `admin123`
  - 工程師: `engineer1` / `eng123`
  - 操作員: `operator1` / `op123`

**常用指令**

```bash
# 停止服務
docker-compose stop

# 重新啟動服務
docker-compose restart

# 停止並移除容器
docker-compose down

# 停止並移除容器、資料卷
docker-compose down -v

# 重新建置映像
docker-compose build --no-cache

# 查看後端日誌
docker-compose logs -f backend

# 查看前端日誌
docker-compose logs -f frontend

# 進入後端容器
docker-compose exec backend bash

# 進入資料庫容器
docker-compose exec db mysql -uroot -p
```

### 方法 2: 本機開發模式

**前置需求**:
- Python 3.11+
- Node.js 16+
- MySQL 8.0+

**後端啟動**:

```bash
cd backend

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安裝依賴
pip install -e .

# 配置環境變數
export DATABASE_URL="mysql+asyncmy://user:password@localhost:3306/webpdtool"
export SECRET_KEY="your-secret-key-here"
export PORT=9100

# 啟動開發伺服器
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100
```

**前端啟動**:

```bash
cd frontend

# 安裝依賴
npm install

# 配置環境變數
# 編輯 .env.development
echo "VITE_API_BASE_URL=http://localhost:9100" > .env.development

# 啟動開發伺服器
npm run dev
```

前端將在 http://localhost:5173 啟動 (Vite 預設端口)

### 開發工具

**API 測試**:
- Swagger UI: http://localhost:9100/docs
- ReDoc: http://localhost:9100/redoc

**資料庫管理**:
```bash
# 連線至資料庫
mysql -h localhost -P 33306 -u webpdtool -p

# 或使用 Docker
docker-compose exec db mysql -uwebpdtool -p webpdtool
```

**日誌查看**:
```bash
# 後端日誌
docker-compose logs -f backend

# 前端 Nginx 日誌
docker-compose logs -f frontend

# 資料庫日誌
docker-compose logs -f db
```

## 測試

### 後端測試

```bash
cd backend

# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_api/test_auth.py

# 執行測試並顯示覆蓋率
pytest --cov=app tests/
```

### 前端測試

```bash
cd frontend

# 執行單元測試
npm run test

# 執行 E2E 測試 (如果已配置)
npm run test:e2e
```

## 部署

### 生產環境部署注意事項

1. **安全性配置**:
   - 修改預設密碼
   - 使用強密碼的 SECRET_KEY
   - 啟用 HTTPS (配置 Nginx SSL)
   - 限制 CORS_ORIGINS

2. **資料庫優化**:
   - 定期備份資料庫
   - 設定資料庫連線池大小
   - 建立適當索引

3. **效能優化**:
   - 啟用 Nginx gzip 壓縮
   - 配置 Redis 快取 (可選)
   - 設定適當的 worker 數量

4. **監控與日誌**:
   - 設定日誌輪轉
   - 整合監控工具 (如 Prometheus)
   - 配置告警機制

### Docker 生產環境部署

```bash
# 使用生產環境配置啟動
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 檢查健康狀態
docker-compose ps
docker-compose exec backend python -c "import app; print('Backend OK')"
```

## 專案配置

### 環境變數說明

| 變數名稱 | 說明 | 預設值 | 必填 |
|---------|------|--------|------|
| `DATABASE_URL` | 資料庫連線字串 | - | ✅ |
| `SECRET_KEY` | JWT 加密金鑰 (最少 32 字元) | - | ✅ |
| `ALGORITHM` | JWT 演算法 | HS256 | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 過期時間 | 30 | ❌ |
| `PORT` | 後端服務端口 | 9100 | ❌ |
| `CORS_ORIGINS` | 允許的前端來源 | http://localhost:9080 | ❌ |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密碼 | - | ✅ |
| `MYSQL_DATABASE` | 資料庫名稱 | webpdtool | ❌ |
| `MYSQL_USER` | 資料庫使用者 | pdtool | ❌ |
| `MYSQL_PASSWORD` | 資料庫密碼 | - | ✅ |
| `VITE_API_BASE_URL` | 前端 API 基礎 URL | http://localhost:9100 | ❌ |
| `DEBUG` | 除錯模式 | false | ❌ |
| `FRONTEND_PORT` | 前端服務端口 | 9080 | ❌ |
| `BACKEND_PORT` | 後端服務端口 | 9100 | ❌ |

### 端口配置

所有端口均可在配置檔案中修改：

- **前端**: `docker-compose.yml` (ports: "9080:80")
- **後端**: `backend/Dockerfile` (EXPOSE 9100), `backend/app/config.py` (PORT)
- **資料庫**: `docker-compose.yml` (ports: "33306:3306")

## 技術特色

### 後端特色
1. **完全非同步**: 使用 async/await 實作所有 I/O 操作
2. **類型安全**: Pydantic v2 資料驗證
3. **依賴注入**: FastAPI 依賴注入系統
4. **測試覆蓋**: 完整的 API 測試套件 (9 個測試類別,100% 通過率)
5. **模組化設計**: 清晰的分層架構 (API/Service/Model/Measurement)
6. **Singleton 模式**: InstrumentManager 確保儀器連線唯一性
7. **抽象基礎類別**: BaseMeasurement 定義測量模組規範
8. **測量註冊表**: MEASUREMENT_REGISTRY 動態載入測量類型
9. **PDTool4 完整相容**:
   - 支援所有 7 種 limit_type (lower, upper, both, equality, inequality, partial, none)
   - 支援所有 3 種 value_type (string, integer, float)
   - runAllTest 模式錯誤處理
   - PDTool4 儀器錯誤檢測機制

### 前端特色
1. **Composition API**: Vue 3 最新語法
2. **TypeScript 友好**: Pinia 完整類型支援
3. **響應式設計**: Element Plus 組件庫
4. **狀態管理**: Pinia 輕量級狀態管理
5. **API 攔截器**: 統一錯誤處理與 Token 管理
6. **PDTool4 風格**: 測試執行介面仿照原桌面應用設計

### 測試引擎特色
1. **BaseMeasurement 抽象類別**:
   - 標準化測量介面 (`prepare()`, `execute()`, `cleanup()`)
   - 內建結果驗證 (`validate_result()`) - 支援 PDTool4 所有 limit 類型
   - 值類型轉換 (string/integer/float)
   - 錯誤處理機制
   - **PDTool4 驗證邏輯完整整合**:
     - 支援 7 種 limit_type: lower, upper, both, equality, inequality, partial, none
     - 支援 3 種 value_type: string, integer, float
     - runAllTest 模式錯誤處理
     - PDTool4 儀器錯誤檢測 ("No instrument found", "Error:")

2. **TestEngine 測試編排器**:
   - 非同步測試執行 (`asyncio`)
   - 測試會話狀態管理
   - 測量任務調度與結果記錄
   - 錯誤恢復機制
   - **runAllTest 模式**:
     - 遇到錯誤時繼續執行測試
     - 收集所有錯誤並在結束時報告
     - 與 PDTool4 行為完全一致

3. **InstrumentManager 儀器管理**:
   - Singleton 模式確保唯一實例
   - 儀器連線池管理
   - 儀器狀態即時追蹤
   - 連線重置與錯誤處理

4. **MEASUREMENT_REGISTRY**:
   - 測量類型動態註冊
   - 支援擴充新測量類型
   - 類型驗證與參數檢查

5. **PDTool4 相容性**:
   - 完整的測試點驗證邏輯遷移
   - 支援所有 limit 類型
   - Run-all-test 功能整合
   - 前後端一致的 runAllTest 模式實現

## 故障排除

### 常見問題

**1. Docker 容器無法啟動**
```bash
# 檢查端口是否被占用
netstat -tuln | grep -E '9080|9100|33306'

# 停止占用端口的服務或修改配置檔案中的端口
```

**2. 資料庫連線失敗**
```bash
# 檢查資料庫容器狀態
docker-compose ps db

# 查看資料庫日誌
docker-compose logs db

# 手動測試連線
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD}
```

**3. 前端無法連接後端 API**
```bash
# 檢查後端服務狀態
docker-compose logs backend

# 驗證 API 是否正常
curl http://localhost:9100/docs

# 檢查前端環境變數
cat frontend/.env.development
```

**4. Token 過期或無效**
```bash
# 清除瀏覽器 localStorage
# 或在瀏覽器開發者工具中執行:
localStorage.clear()
location.reload()
```

**5. 測試執行卡住或失敗**
```bash
# 檢查測試引擎狀態
curl http://localhost:9100/api/tests/instruments/status

# 重置儀器連線
curl -X POST http://localhost:9100/api/tests/instruments/{instrument_id}/reset

# 查看後端日誌尋找錯誤
docker-compose logs -f backend | grep ERROR
```

## 貢獻指南

歡迎貢獻！請遵循以下步驟：

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送至分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 編碼規範

**Python (後端)**:
- 遵循 PEP 8
- 使用 Black 格式化
- 類型提示 (Type Hints)
- Docstrings 說明

**JavaScript/Vue (前端)**:
- ESLint 規則
- Prettier 格式化
- Composition API 優先
- 註解清晰

## 授權

[請在此添加授權資訊]

## 聯絡方式

[請在此添加聯絡資訊]

## 參考文檔

- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [Vue 3 官方文檔](https://vuejs.org/)
- [Element Plus 文檔](https://element-plus.org/)
- [SQLAlchemy 2.0 文檔](https://docs.sqlalchemy.org/)
- [Pydantic 文檔](https://docs.pydantic.dev/)

## 專案文檔

詳細技術文檔請參閱 `docs/` 目錄：

### 核心文檔
- [重構計劃](docs/Refactoring.md) - 完整的重構階段規劃
- [架構與工作流程](docs/architecture_workflow.md) - 系統架構說明
- [測量模組分析](docs/measurement_modules.md) - 測量模組設計

### PDTool4 分析與整合
- **[重構完成報告](docs/REFACTORING_SUMMARY.md)** - PDTool4 整合完成總結
- **[PDTool4 測量模組分析](docs/PDTool4_Measurement_Module_Analysis.md)** - PDTool4 架構深入分析
- **[測試計劃匯入指南](docs/README_import_testplan.md)** - CSV 匯入工具使用說明

### 整合方案
- [Modbus 通訊](docs/modbus_communication.md) - Modbus 整合方案
- [SFC 整合](docs/sfc_integration.md) - SFC 系統整合

## 專案狀態與待辦事項

### 目前狀態
- **完成度**: 約 75%
- **核心架構**: ✅ 已完成
- **API 層**: ✅ 已完成 (70+ 端點)
- **PDTool4 相容性**: ✅ 已完成 (完整驗證邏輯與 runAllTest 模式)
- **前端介面**: ⚠️ 部分完成 (核心功能完成,部分待優化)
- **儀器驅動**: ⚠️ Stub 實作，需實際驅動
- **生產就緒**: ❌ 需要更多測試與優化

### 已知限制
1. **儀器驅動**: 目前使用 dummy 實作，需要實際儀器驅動
2. **即時通訊**: 使用輪詢機制，WebSocket 待實作
3. **前端功能**: 測試歷史查詢介面待完善
4. **錯誤處理**: 部分 API 需要更完善的錯誤處理
5. **安全性**: 預設密碼需要修改，輸入驗證需要加強

### 優先待辦事項
1. **高優先級**:
   - 實作實際儀器驅動 (Power Supply, DMM, Serial 通訊)
   - 完善錯誤處理機制
   - 修改預設密碼和安全性設定

2. **中優先級**:
   - WebSocket 即時通訊實作
   - 前端測試歷史查詢完整介面
   - 圖表與趨勢分析功能
   - PDF 報表生成

3. **低優先級**:
   - Modbus 整合
   - SFC 實際連線實作
   - 多語系支援
   - 系統監控與告警

## 更新日誌

### v0.6.0 (最新) - 2026-01-05
- ✅ **PDTool4 完整相容性整合**
  - 整合 PDTool4 測量驗證邏輯到 BaseMeasurement
  - 支援所有 7 種 limit_type (lower, upper, both, equality, inequality, partial, none)
  - 支援所有 3 種 value_type (string, integer, float)
- ✅ **runAllTest 模式實現**
  - Backend: measurement_service.py 支援錯誤收集但繼續執行
  - Frontend: TestMain.vue 整合 runAllTest UI 與錯誤顯示
  - 與 PDTool4 行為完全一致
- ✅ **PDTool4 儀器錯誤檢測**
  - 檢測 "No instrument found" 和 "Error:" 訊息
  - 完整的錯誤處理機制
- ✅ **測試計劃匯入工具**
  - scripts/import_testplan.py 完整匯入工具
  - scripts/batch_import.sh 批量匯入腳本
  - docs/README_import_testplan.md 使用指南
- ✅ **前端 Bug 修復**
  - ProjectStationSelector.vue 站別選擇修復
  - TestPlanManage.vue API 參數修復
- ✅ **完整測試覆蓋**
  - 9 個測試類別,100% 通過率
  - scripts/test_refactoring.py 測試套件

### v0.5.0 - 2024
- ✅ 完成測試執行引擎核心架構
- ✅ 實作 BaseMeasurement 抽象基礎類別
- ✅ 實作 TestEngine 測試編排器
- ✅ 實作 InstrumentManager 儀器管理器
- ✅ 完成 TestMain.vue 主測試介面 (PDTool4 風格)
- ✅ 擴展測試執行 API (5+ 端點)
- ✅ 擴展測量執行 API (10 端點)
- ✅ 測試會話狀態管理與輪詢機制
- ✅ 儀器狀態查詢與重置功能
- ✅ 測試結果查詢與 CSV 匯出 API
- ✅ 新增測試計劃名稱與映射 API
- ✅ Docker 端口配置優化 (9080/9100/33306)
- ✅ 新增 SFC 服務模組

### v0.4.0 - 測試計劃管理
- ✅ CSV 測試計劃上傳功能
- ✅ 測試計劃 CRUD 操作
- ✅ 測試項目重新排序
- ✅ 批量刪除功能

### v0.3.0 - 專案與站別管理
- ✅ 專案管理 API 與介面
- ✅ 站別管理 API 與介面
- ✅ 專案與站別關聯

### v0.2.0 - 認證系統
- ✅ JWT Token 認證
- ✅ 使用者角色權限
- ✅ 登入介面與路由守衛

### v0.1.0 - 專案初始化
- ✅ 專案結構建立
- ✅ Docker 容器化
- ✅ 資料庫 Schema 設計

---

**Last Updated**: 2026-01-05
**Status**: Phase 1-5 Core Complete (~75%), Phase 6-7 Pending
**Latest Version**: v0.6.0 - PDTool4 Complete Integration
