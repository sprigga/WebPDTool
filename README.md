# WebPDTool - Web-based Testing System

> 基於 Vue 3 + FastAPI 的現代化測試系統，從桌面應用程式 PDTool4 重構而來。

---

## 📋 目錄

- [專案概述](#專案概述)
- [技術堆疊](#技術堆疊)
- [系統架構](#系統架構)
- [專案結構](#專案結構)
- [快速開始](#快速開始)
- [API 端點](#api-端點列表)
- [開發進度](#開發進度)
- [技術特色](#技術特色)
- [測試](#測試)
- [部署](#部署)
- [故障排除](#故障排除)
- [更新日誌](#更新日誌)

---

## 📖 專案概述

WebPDTool 是一個 Web 化的產品測試系統，用於執行自動化測試、記錄測試結果。系統採用前後端分離架構，提供完整的測試管理、執行和結果查詢功能。

### 專案狀態

| 項目 | 內容 |
|------|------|
| **版本** | v0.6.0 |
| **完成度** | ~80% (核心架構完成) |
| **最新更新** | 2026-01-05 - PDTool4 完整相容性整合 |
| **狀態** | 核心架構完成，生產環境待優化 |

### ✨ 主要特色

- ✅ **完整 PDTool4 相容性** - 支援所有 7 種 limit_type 和 3 種 value_type
- ✅ **runAllTest 模式** - 遇到錯誤時繼續執行測試，與 PDTool4 完全一致
- ✅ **測量模組架構** - BaseMeasurement 抽象基礎類別 + MEASUREMENT_REGISTRY 註冊表
- ✅ **測試引擎** - TestEngine 測試編排器 + InstrumentManager 儀器管理器
- ✅ **完整 API 層** - 8 個 API 模組，70+ 端點
- ✅ **現代化前端** - Vue 3 Composition API + Element Plus UI

---

## 🛠️ 技術堆疊

### 前端技術

| 技術 | 版本/工具 | 用途 |
|------|-----------|------|
| **框架** | Vue 3 (Composition API) | 核心前端框架 |
| **UI 庫** | Element Plus | UI 組件庫 |
| **狀態管理** | Pinia | 應用狀態管理 |
| **路由** | Vue Router | 頁面路由 |
| **HTTP 客戶端** | Axios | API 請求 |
| **建置工具** | Vite | 開發與建置工具 |
| **開發端口** | 9080 | 前端服務端口 |

### 後端技術

| 技術 | 版本/工具 | 用途 |
|------|-----------|------|
| **框架** | FastAPI | 核心後端框架 |
| **語言** | Python 3.11+ | 程式語言 |
| **ORM** | SQLAlchemy 2.0 | 資料庫 ORM |
| **資料驗證** | Pydantic v2 | 資料驗證 |
| **認證** | JWT | 身份認證 |
| **非同步支援** | asyncio/async-await | 非同步處理 |
| **API 文件** | Swagger UI | API 文檔 (/docs) |
| **服務端口** | 9100 | 後端 API 端口 |

### 資料庫

| 項目 | 版本/配置 |
|------|----------|
| **主資料庫** | MySQL 8.0+ |
| **資料庫端口** | 33306 (Docker 容器映射) |
| **連線池** | SQLAlchemy async engine |

### 部署與容器化

| 項目 | 技術 |
|------|------|
| **容器化** | Docker & Docker Compose |
| **反向代理** | Nginx (內建於前端容器) |
| **健康檢查** | Docker healthcheck 機制 |

---

## 🏗️ 系統架構

### 整體系統架構圖

```plantuml
@startuml
!theme plain
skinparam componentStyle rectangle

package "客戶端 Client" #e1f5ff {
    [瀏覽器\nBrowser] as Browser
}

package "Docker 容器環境" #fff4e6 {
    package "前端容器 (Port 9080)" #e8f5e9 {
        [Nginx\n反向代理] as Nginx
        [Vue 3 應用\nElement Plus UI\nPinia Store\nVue Router] as Vue
    }
    
    package "後端容器 (Port 9100)" #f3e5f5 {
        [FastAPI\nPython 3.11+] as FastAPI
        
        package "API 層" {
            [Auth API\n認證] as AuthAPI
            [Projects API\n專案管理] as ProjectsAPI
            [Stations API\n站別管理] as StationsAPI
            [Test Plans API\n測試計劃] as TestPlansAPI
            [Tests API\n測試執行] as TestsAPI
            [Measurements API\n測量執行] as MeasurementsAPI
            [Results API\n測試結果] as ResultsAPI
        }
        
        package "服務層 Services" {
            [TestEngine\n測試引擎] as TestEngine
            [InstrumentManager\n儀器管理器] as InstrumentMgr
            [MeasurementService\n測量服務] as MeasurementSvc
            [SFC Service\nSFC整合] as SFCSvc
        }
        
        package "測量模組 Measurements" {
            [BaseMeasurement\n抽象基礎類別] as BaseMeasure
            [PowerSet] as PowerSet
            [PowerRead] as PowerRead
            [CommandTest] as CommandTest
            [其他測量模組] as OtherMeasure
        }
        
        package "資料模型 Models\nSQLAlchemy ORM" {
            [User] as UserModel
            [Project] as ProjectModel
            [Station] as StationModel
            [TestPlan] as TestPlanModel
            [TestSession] as TestSessionModel
            [TestResult] as TestResultModel
            [SFCLog] as SFCLogModel
        }
    }
    
    package "資料庫容器 (Port 33306)" #fce4ec {
        database "MySQL 8.0+\nwebpdtool" as MySQL
    }
}

package "外部系統" #f5f5f5 {
    [SFC System\n製造執行系統] as SFC
    [Modbus\n設備通訊] as Modbus
}

' 連線關係
Browser --> Nginx : HTTP
Nginx --> Vue : 靜態資源
Vue --> FastAPI : Axios\nAPI Calls

FastAPI --> AuthAPI
FastAPI --> ProjectsAPI
FastAPI --> StationsAPI
FastAPI --> TestPlansAPI
FastAPI --> TestsAPI
FastAPI --> MeasurementsAPI
FastAPI --> ResultsAPI

AuthAPI --> TestEngine
ProjectsAPI --> TestEngine
StationsAPI --> TestEngine
TestPlansAPI --> TestEngine
TestsAPI --> TestEngine
MeasurementsAPI --> TestEngine
ResultsAPI --> TestEngine

TestEngine --> InstrumentMgr
TestEngine --> MeasurementSvc
TestEngine --> SFCSvc

MeasurementSvc --> BaseMeasure
BaseMeasure <|-- PowerSet
BaseMeasure <|-- PowerRead
BaseMeasure <|-- CommandTest
BaseMeasure <|-- OtherMeasure

TestEngine --> UserModel
TestEngine --> ProjectModel
TestEngine --> StationModel
TestEngine --> TestPlanModel
TestEngine --> TestSessionModel
TestEngine --> TestResultModel
TestEngine --> SFCLogModel

UserModel --> MySQL : SQLAlchemy\nAsync
ProjectModel --> MySQL
StationModel --> MySQL
TestPlanModel --> MySQL
TestSessionModel --> MySQL
TestResultModel --> MySQL
SFCLogModel --> MySQL

SFCSvc ..> SFC : Web Service
InstrumentMgr ..> Modbus : TCP/IP

@enduml
```

### 測試執行流程

```plantuml
@startuml
!theme plain
skinparam activityBackgroundColor #fff
skinparam activityBorderColor #000
skinparam activityStartColor #90ee90
skinparam activityEndColor #ffcccb
skinparam activityDiamondBackgroundColor #ffd700
skinparam activityDiamondBorderColor #000

start

:使用者登入;

repeat
    :驗證使用者;
repeat while (驗證成功?) is (否) not (是)

:取得 JWT Token;

:選擇專案/站別;
:載入站別設定;
:載入測試計劃;

repeat
    :輸入序號 SN;
    
    repeat
        :驗證序號;
    repeat while (序號有效?) is (無效) not (有效)
    
    #87ceeb:創建測試會話\nTestSession;
    
    :開始測試;
    
    repeat
        :取得下一個測試項目;
        
        if (還有測試項目?) then (是)
            :載入測量模組;
            :執行測量;
            :取得測量值;
            :驗證限制值\nlimit_type & value_type;
            
            #87ceeb:儲存測試結果\nTestResult;
            :更新前端UI;
            
            if (測試失敗?) then (是且非runAllTest)
                break
            else (否或runAllTest模式)
                -> 繼續;
            endif
        else (否)
            break
        endif
    repeat while (繼續測試項目)
    
    :計算最終結果;
    
    #87ceeb:更新測試會話\nfinal_result;
    
    if (需要SFC上傳?) then (是)
        :上傳結果到SFC;
        #87ceeb:記錄SFC日誌\nSFCLog;
    endif
    
    :顯示測試報告;
    
repeat while (繼續測試?) is (是) not (否)

stop

@enduml
```

### 資料庫關係圖

```plantuml
@startuml
!theme plain
skinparam linetype ortho

entity "users" as users {
  *id : int <<PK>>
  --
  *username : varchar(50) <<UK>> -- 使用者名稱
  *password_hash : varchar(255) -- 密碼雜湊
  *role : enum -- 角色 (ENGINEER/OPERATOR/ADMIN)
  full_name : varchar(100) -- 全名
  email : varchar(100) -- 電子郵件
  is_active : boolean -- 啟用狀態
  created_at : timestamp -- 建立時間
  updated_at : timestamp -- 更新時間
}

entity "projects" as projects {
  *id : int <<PK>>
  --
  *project_code : varchar(50) <<UK>> -- 專案代碼
  *project_name : varchar(100) -- 專案名稱
  description : text -- 描述
  is_active : boolean -- 啟用狀態
  created_at : timestamp -- 建立時間
  updated_at : timestamp -- 更新時間
}

entity "stations" as stations {
  *id : int <<PK>>
  --
  *station_code : varchar(50) -- 站別代碼
  station_name : varchar(100) -- 站別名稱
  *project_id : int <<FK>> -- 專案ID
  test_plan_path : varchar(255) -- 測試計劃路徑
  is_active : boolean -- 啟用狀態
  created_at : timestamp -- 建立時間
  updated_at : timestamp -- 更新時間
}

entity "test_plans" as test_plans {
  *id : int <<PK>>
  --
  *station_id : int <<FK>> -- 站別ID
  item_no : int -- 測試項目編號
  item_name : varchar(100) -- 測試項目名稱
  test_type : varchar(50) -- 測試類型
  parameters : json -- 測試參數
  lower_limit : decimal(15,6) -- 下限值
  upper_limit : decimal(15,6) -- 上限值
  unit : varchar(20) -- 單位
  enabled : boolean -- 啟用狀態
  sequence_order : int -- 執行順序
  created_at : timestamp -- 建立時間
  updated_at : timestamp -- 更新時間
}

entity "test_sessions" as test_sessions {
  *id : int <<PK>>
  --
  serial_number : varchar(100) -- 產品序號
  *station_id : int <<FK>> -- 站別ID
  *user_id : int <<FK>> -- 使用者ID
  start_time : timestamp -- 開始時間
  end_time : timestamp -- 結束時間
  final_result : enum -- 最終結果 (PASS/FAIL/ABORT)
  total_items : int -- 總項目數
  pass_items : int -- 通過項目數
  fail_items : int -- 失敗項目數
  test_duration_seconds : int -- 測試時長(秒)
  created_at : timestamp -- 建立時間
}

entity "test_results" as test_results {
  *id : bigint <<PK>>
  --
  *session_id : int <<FK>> -- 測試會話ID
  *test_plan_id : int <<FK>> -- 測試計劃ID
  item_no : int -- 測試項目編號
  item_name : varchar(100) -- 測試項目名稱
  measured_value : decimal(15,6) -- 測量值
  lower_limit : decimal(15,6) -- 下限值
  upper_limit : decimal(15,6) -- 上限值
  unit : varchar(20) -- 單位
  result : enum -- 結果 (PASS/FAIL/SKIP/ERROR)
  error_message : text -- 錯誤訊息
  test_time : timestamp -- 測試時間
  execution_duration_ms : int -- 執行時長(毫秒)
}

entity "sfc_logs" as sfc_logs {
  *id : bigint <<PK>>
  --
  *session_id : int <<FK>> -- 測試會話ID
  operation : varchar(50) -- 操作類型
  request_data : json -- 請求資料
  response_data : json -- 回應資料
  status : enum -- 狀態 (SUCCESS/FAILED/TIMEOUT)
  error_message : text -- 錯誤訊息
  created_at : timestamp -- 建立時間
}

entity "configurations" as configurations {
  *id : int <<PK>>
  --
  *config_key : varchar(100) <<UK>> -- 設定鍵值
  config_value : json -- 設定值
  category : varchar(50) -- 類別
  description : text -- 描述
  is_system : boolean -- 系統設定
  created_at : timestamp -- 建立時間
  updated_at : timestamp -- 更新時間
}

entity "modbus_logs" as modbus_logs {
  *id : bigint <<PK>>
  --
  register_address : int -- 暫存器位址
  operation : enum -- 操作 (READ/WRITE)
  value : varchar(255) -- 值
  status : enum -- 狀態 (SUCCESS/FAILED)
  error_message : text -- 錯誤訊息
  created_at : timestamp -- 建立時間
}

' 關係定義
users ||--o{ test_sessions : "執行測試"
projects ||--o{ stations : "包含站別"
stations ||--o{ test_plans : "包含測試計劃"
stations ||--o{ test_sessions : "執行測試"
test_plans ||--o{ test_results : "產生結果"
test_sessions ||--|{ test_results : "包含測試結果"
test_sessions ||--o{ sfc_logs : "產生SFC日誌"

@enduml
```

---

## 📁 專案結構

```
WebPDTool/
├── backend/                    # FastAPI 後端應用
│   ├── app/
│   │   ├── api/               # RESTful API 路由 (8 模組)
│   │   │   ├── auth.py        # 認證 API
│   │   │   ├── projects.py    # 專案管理 API
│   │   │   ├── stations.py    # 站別管理 API
│   │   │   ├── testplans.py   # 測試計劃 API
│   │   │   ├── tests.py       # 測試執行 API
│   │   │   ├── measurements.py           # 測量執行 API
│   │   │   ├── measurement_results.py    # 測試結果查詢 API
│   │   │   └── __init__.py
│   │   ├── models/            # SQLAlchemy 資料模型
│   │   │   ├── user.py        # 使用者模型
│   │   │   ├── project.py     # 專案模型
│   │   │   ├── station.py     # 站別模型
│   │   │   ├── testplan.py    # 測試計劃模型
│   │   │   ├── test_session.py    # 測試會話模型
│   │   │   ├── test_result.py     # 測試結果模型
│   │   │   └── sfc_log.py         # SFC 日誌模型
│   │   ├── services/          # 業務邏輯層
│   │   │   ├── auth.py        # 認證服務
│   │   │   ├── measurement_service.py  # 測量服務 (含 runAllTest 模式)
│   │   │   ├── test_engine.py         # 測試引擎
│   │   │   ├── instrument_manager.py  # 儀器管理器
│   │   │   ├── sfc_service.py         # SFC 服務
│   │   │   ├── test_plan_service.py   # 測試計劃服務
│   │   │   └── __init__.py
│   │   ├── measurements/      # 測量模組
│   │   │   ├── base.py        # 測量基礎類別 (BaseMeasurement, 含 PDTool4 驗證邏輯)
│   │   │   ├── implementations.py  # 測量實作 (PowerSet, PowerRead, CommandTest, etc.)
│   │   │   ├── __init__.py
│   │   │   └── registry.py    # 測量類型註冊表
│   │   ├── core/              # 核心功能
│   │   │   ├── database.py    # 資料庫配置
│   │   │   ├── logging.py     # 日誌配置
│   │   │   ├── security.py    # 安全性配置
│   │   │   ├── exceptions.py  # 自訂異常
│   │   │   └── __init__.py
│   │   ├── utils/             # 工具函數
│   │   │   ├── csv_parser.py  # CSV 解析工具
│   │   │   ├── __init__.py
│   │   ├── schemas/           # Pydantic 資料驗證模型
│   │   ├── config.py          # 應用配置
│   │   ├── dependencies.py    # FastAPI 依賴注入
│   │   ├── main.py            # 應用入口點
│   │   └── __init__.py
│   ├── scripts/               # 工具腳本
│   │   ├── import_testplan.py # 測試計劃匯入工具
│   │   ├── batch_import.sh    # 批量匯入腳本
│   │   ├── test_refactoring.py # 重構測試套件
│   │   ├── hello_world.py     # 測試腳本
│   │   ├── test123.py         # 測試腳本
│   │   └── add_testplan_fields.sql # 資料庫遷移
│   ├── alembic/               # 資料庫遷移
│   │   ├── versions/          # 遷移版本
│   │   └── env.py             # Alembic 配置
│   ├── logs/                  # 應用日誌
│   │   ├── app.log
│   │   └── backend.log
│   ├── testplans/             # 測試計劃範例
│   ├── pyproject.toml         # Python 專案配置
│   ├── uv.lock                # uv 依賴鎖定檔案
│   ├── Dockerfile             # 後端 Docker 映像
│   ├── .env                   # 環境變數
│   ├── .env.example           # 環境變數範本
│   ├── .dockerignore          # Docker 忽略檔案
│   └── requirements.txt       # Python 依賴 (舊版)
├── frontend/                  # Vue 3 前端應用
│   ├── src/
│   │   ├── views/             # 頁面組件
│   │   │   ├── Login.vue      # 登入頁面
│   │   │   ├── SystemConfig.vue      # 系統配置
│   │   │   ├── TestMain.vue          # 測試執行主介面 (含 runAllTest 模式)
│   │   │   ├── TestPlanManage.vue    # 測試計劃管理
│   │   │   ├── TestExecution.vue     # 測試執行監控
│   │   │   └── TestHistory.vue       # 測試歷史查詢
│   │   ├── components/        # 可複用組件
│   │   │   └── ProjectStationSelector.vue  # 專案站別選擇器
│   │   ├── api/               # API 客戶端
│   │   │   ├── client.js      # Axios 客戶端配置
│   │   │   ├── auth.js        # 認證 API
│   │   │   ├── projects.js    # 專案 API
│   │   │   ├── testplans.js   # 測試計劃 API
│   │   │   └── tests.js       # 測試執行 API
│   │   ├── stores/            # Pinia 狀態管理
│   │   │   ├── auth.js        # 認證狀態
│   │   │   └── project.js     # 專案狀態
│   │   ├── router/            # Vue Router 配置
│   │   │   └── index.js
│   │   ├── utils/             # 工具函數
│   │   ├── App.vue            # 根組件
│   │   ├── main.js            # 應用入口點
│   │   └── public/            # 靜態資源
│   │       ├── index.html
│   │       ├── favicon.svg
│   │       └── UseResult_testPlan.csv # 測試計劃範例
│   ├── dist/                  # 建置輸出目錄
│   ├── node_modules/          # Node.js 依賴
│   ├── Dockerfile             # 前端 Docker 映像
│   ├── nginx.conf             # Nginx 配置
│   ├── package.json           # NPM 專案配置
│   ├── package-lock.json      # NPM 鎖定檔案
│   ├── vite.config.js         # Vite 配置
│   ├── .env.development       # 開發環境變數
│   ├── .dockerignore          # Docker 忽略檔案
│   └── README.md
├── database/                  # 資料庫設計
│   ├── schema.sql             # 資料庫 Schema
│   ├── seed_data.sql          # 初始資料
│   └── README.md
├── docker-compose.yml         # Docker Compose 配置
├── docker-compose.dev.yml     # 開發環境配置
├── docker-start.sh            # Docker 啟動腳本
├── .env.example               # 環境變數範本
├── .gitignore                 # Git 忽略檔案
├── docs/                      # 技術文檔
│   ├── index.md               # 文檔索引
│   ├── REFACTORING_SUMMARY.md         # 重構完成報告
│   ├── PDTool4_Measurement_Module_Analysis.md  # PDTool4 分析
│   ├── README_import_testplan.md       # 測試計劃匯入指南
│   ├── architecture_workflow.md        # 架構與工作流程
│   ├── measurement_modules.md          # 測量模組設計
│   ├── modbus_communication.md         # Modbus 通訊
│   ├── sfc_integration.md              # SFC 整合
│   ├── core_application.md             # 核心應用
│   ├── configuration_setup.md          # 配置設定
│   ├── modbus_communication.md         # Modbus 通訊
│   ├── ISSUE.md                        # 問題追蹤
│   ├── ISSUE3.md
│   ├── ISSUE4.md
│   ├── Measurement_api.md              # 測量 API
│   ├── Refactoring.md                  # 重構指南
│   ├── Docker部署指南.md               # Docker 部署
│   ├── phase5_implementation_report.md # Phase 5 實作報告
│   ├── command_field_usage.md          # 命令欄位使用說明
│   ├── Backend_Frontend_Refactoring_Analysis.md # 重構分析
│   ├── summary_best_practices.md       # 最佳實務總結
│   └── README.md
├── scripts/                  # 全域工具腳本
│   ├── start-backend-dev.sh  # 後端開發啟動
│   ├── start-frontend-dev.sh # 前端開發啟動
│   ├── start-dev.sh          # 全域開發啟動
│   └── README.md
├── PDTool4/                  # 舊系統 (供參考)
├── skill-stack.zip           # 技能包
├── vite                      # Vite 快取
├── CACHED                    # 快取目錄
├── resolve                   # 解析目錄
├── transferring              # 傳輸目錄
├── unpacking                 # 解壓目錄
├── exporting                 # 匯出目錄
└── logs/                     # 全域日誌
    └── frontend.log
```

---

### 後端架構

#### API 層 (backend/app/api/)

- **auth.py**: 認證與授權管理
- **projects.py**: 專案 CRUD 操作
- **stations.py**: 站別管理
- **testplans.py**: 測試計劃管理與 CSV 上傳
- **tests.py**: 測試會話執行與控制
- **measurements.py**: 測量任務執行
- **measurement_results.py**: 測試結果查詢與匯出

---

#### 資料模型層 (backend/app/models/)

- **user.py**: 使用者模型 (Admin/Engineer/Operator)
- **project.py**: 專案模型
- **station.py**: 測試站別模型
- **testplan.py**: 測試計劃項目模型
- **test_session.py**: 測試會話模型 (狀態追蹤)
- **test_result.py**: 測試結果模型
- **sfc_log.py**: SFC 整合日誌模型

---

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

---

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

---

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

---

#### API 客戶端 (frontend/src/api/)

- **client.js**: Axios 實例配置、請求/回應攔截器、錯誤處理
- **auth.js**: 登入、登出、Token 刷新
- **projects.js**: 專案列表、建立、更新、刪除
- **testplans.js**: 測試計劃 CRUD、CSV 上傳、重新排序
- **tests.js**: 測試會話管理、執行控制、結果上傳、儀器狀態

---

#### 狀態管理 (frontend/src/stores/)

- **auth.js**: 使用者認證狀態 (Pinia)
- **project.js**: 當前專案與站別狀態

---

### 資料庫架構

#### 核心表格

- **users**: 使用者資料 (username, password_hash, role, is_active)
- **projects**: 專案資料 (project_name, description)
- **stations**: 測試站別 (station_name, project_id, config_json)
- **testplans**: 測試計劃項目 (step_number, item_name, spec, measurement_type...)
- **test_sessions**: 測試會話 (barcode, status, start_time, end_time...)
- **test_results**: 測試結果 (measured_value, result, error_msg...)
- **sfc_logs**: SFC 整合日誌

---

## 📡 API 端點列表

### 認證 API (`/api/auth`)

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/login` | 使用者登入 |
| POST | `/login-form` | 表單登入 (OAuth2 相容) |
| POST | `/logout` | 登出 |
| GET | `/me` | 取得當前使用者資訊 |
| POST | `/refresh` | 刷新 Token |

---

### 專案管理 API (`/api/projects`)

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/` | 取得專案列表 |
| GET | `/{project_id}` | 取得專案詳情 (含站別) |
| POST | `/` | 建立新專案 |
| PUT | `/{project_id}` | 更新專案 |
| DELETE | `/{project_id}` | 刪除專案 |

---

### 站別管理 API (`/api`)

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/projects/{project_id}/stations` | 取得專案的站別列表 |
| GET | `/stations/{station_id}` | 取得站別詳情 |
| POST | `/stations` | 建立新站別 |
| PUT | `/stations/{station_id}` | 更新站別 |
| DELETE | `/stations/{station_id}` | 刪除站別 |

---

### 測試計劃 API (`/api`)

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/stations/{station_id}/testplan` | 取得站別的測試計劃 |
| GET | `/stations/{station_id}/testplan-names` | 取得測試計劃名稱列表 |
| GET | `/stations/{station_id}/testplan-map` | 取得測試點映射 |
| POST | `/stations/{station_id}/testplan/upload` | 上傳 CSV 測試計劃 |
| POST | `/testplans` | 建立測試項目 |
| GET | `/testplans/{testplan_id}` | 取得測試項目詳情 |
| PUT | `/testplans/{testplan_id}` | 更新測試項目 |
| DELETE | `/testplans/{testplan_id}` | 刪除測試項目 |
| POST | `/testplans/bulk-delete` | 批量刪除測試項目 |
| POST | `/testplans/reorder` | 重新排序測試項目 |
| POST | `/testplans/validate-test-point` | 驗證測試點 |
| GET | `/sessions/{session_id}/test-results` | 取得會話測試結果 |

---

### 測試執行 API (`/api/tests`)

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/sessions` | 建立測試會話 |
| POST | `/sessions/{session_id}/start` | 開始測試執行 |
| POST | `/sessions/{session_id}/stop` | 停止測試執行 |
| GET | `/sessions/{session_id}/status` | 取得測試會話即時狀態 |
| GET | `/sessions/{session_id}/results` | 取得測試會話的所有結果 |

---

### 測量執行 API (`/api/measurements`)

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/execute` | 執行單個測量 |
| POST | `/batch-execute` | 批量執行測量 |
| GET | `/types` | 取得支援的測量類型 |
| GET | `/instruments` | 取得儀器狀態列表 |
| GET | `/instruments/available` | 取得可用儀器列表 |
| POST | `/instruments/{instrument_id}/reset` | 重置儀器 |
| GET | `/session/{session_id}/results` | 取得會話測量結果 |
| POST | `/validate-params` | 驗證測量參數 |
| GET | `/measurement-templates` | 取得測量模板 |
| POST | `/execute-with-dependencies` | 執行具相依性的測量 |

---

### 測試結果查詢 API (`/api/measurement-results`)

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/sessions` | 查詢測試會話 (支援篩選與分頁) |
| GET | `/sessions/{session_id}` | 取得會話詳細結果 |
| GET | `/results` | 查詢測試結果 (支援多條件篩選) |
| GET | `/summary` | 取得測試結果統計摘要 |
| GET | `/export/csv/{session_id}` | 匯出測試結果為 CSV |
| DELETE | `/sessions/{session_id}` | 刪除測試會話與結果 |
| POST | `/cleanup` | 清理舊測試資料 |

---

## 📊 開發進度

### ✅ 階段 1: 基礎設施建置 (已完成)

- [x] 專案目錄結構建立
- [x] 後端 FastAPI 專案初始化
- [x] 前端 Vue 3 專案初始化
- [x] 資料庫 Schema 設計
- [x] Docker 容器化配置
- [x] Docker Compose 編排

---

### ✅ 階段 2: 核心認證系統 (已完成)

- [x] 後端認證模組 (JWT Token)
- [x] 使用者資料模型
- [x] 登入/登出 API
- [x] 前端登入介面
- [x] Token 管理和路由守衛
- [x] 角色權限控制 (Admin/Engineer/Operator)

---

### ✅ 階段 3: 專案與站別管理 (已完成)

- [x] 專案資料模型和 API
- [x] 站別資料模型和 API
- [x] 前端專案選擇組件
- [x] 前端站別選擇功能
- [x] 專案與站別關聯管理
- [x] 系統配置頁面

---

### ✅ 階段 4: 測試計劃管理 (已完成)

- [x] CSV 檔案解析功能
- [x] 測試計劃上傳 API
- [x] 測試計劃 CRUD API
- [x] 前端測試計劃管理介面
- [x] 測試項目編輯功能
- [x] 批量刪除和排序功能
- [x] 測試計劃表格顯示與操作
- [x] 測試計劃匯入工具 (scripts/import_testplan.py)

---

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

---

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

---

### ⏳ 階段 7: 生產環境優化 (待實作)

- [ ] 安全性強化 (輸入驗證、SQL 注入防護)
- [ ] 效能優化 (資料庫查詢、快取機制)
- [ ] 錯誤處理完善
- [ ] API 速率限制
- [ ] 監控與告警機制
- [ ] 備份與恢復策略

---

## 🚀 快速開始

### 系統需求

| 項目 | 版本需求 |
|------|---------|
| **Docker Engine** | 20.10+ |
| **Docker Compose** | 2.0+ |
| **端口需求** | 9080 (前端), 9100 (後端), 33306 (MySQL) |

---

### 方法 1: 使用 Docker Compose (推薦)

#### 步驟 1: 配置環境變數

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，設定必要參數
# 特別注意: SECRET_KEY、MYSQL_ROOT_PASSWORD、MYSQL_PASSWORD
vim .env
```

#### 步驟 2: 啟動服務

```bash
# 建置並啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

#### 步驟 3: 初始化資料庫

```bash
# 等待資料庫啟動完成 (約 30 秒)
# 執行資料庫初始化
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/schema.sql
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/seed_data.sql
```

#### 步驟 4: 存取應用

- **前端介面**: http://localhost:9080
- **後端 API 文件**: http://localhost:9100/docs

**預設帳號**:

| 角色 | 帳號 | 密碼 |
|------|------|------|
| 管理員 | `admin` | `admin123` |
| 工程師 | `engineer1` | `eng123` |
| 操作員 | `operator1` | `op123` |

---

#### 常用指令

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

---

### 方法 2: 本機開發模式

#### 前置需求

| 項目 | 版本需求 |
|------|---------|
| **Python** | 3.11+ |
| **Node.js** | 16+ |
| **MySQL** | 8.0+ |

#### 後端啟動

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

#### 前端啟動

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

> 前端將在 http://localhost:5173 啟動 (Vite 預設端口)

---

### 開發工具

#### API 測試

- **Swagger UI**: http://localhost:9100/docs
- **ReDoc**: http://localhost:9100/redoc

#### 資料庫管理

```bash
# 連線至資料庫
mysql -h localhost -P 33306 -u webpdtool -p

# 或使用 Docker
docker-compose exec db mysql -uwebpdtool -p webpdtool
```

#### 日誌查看

```bash
# 後端日誌
docker-compose logs -f backend

# 前端 Nginx 日誌
docker-compose logs -f frontend

# 資料庫日誌
docker-compose logs -f db
```

---

## 🧪 測試

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

---

## 🚢 部署

### 生產環境部署注意事項

#### 1. 安全性配置

- ✅ 修改預設密碼
- ✅ 使用強密碼的 SECRET_KEY
- ✅ 啟用 HTTPS (配置 Nginx SSL)
- ✅ 限制 CORS_ORIGINS

#### 2. 資料庫優化

- ✅ 定期備份資料庫
- ✅ 設定資料庫連線池大小
- ✅ 建立適當索引

#### 3. 效能優化

- ✅ 啟用 Nginx gzip 壓縮
- ✅ 配置 Redis 快取 (可選)
- ✅ 設定適當的 worker 數量

#### 4. 監控與日誌

- ✅ 設定日誌輪轉
- ✅ 整合監控工具 (如 Prometheus)
- ✅ 配置告警機制

---

### Docker 生產環境部署

```bash
# 使用生產環境配置啟動
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 檢查健康狀態
docker-compose ps
docker-compose exec backend python -c "import app; print('Backend OK')"
```

---

## ⚙️ 專案配置

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

| 服務 | 配置檔案 | 預設端口 |
|------|---------|----------|
| **前端** | `docker-compose.yml` | 9080 |
| **後端** | `backend/Dockerfile`, `backend/app/config.py` | 9100 |
| **資料庫** | `docker-compose.yml` | 33306 |

---

## 🎯 技術特色

### 後端特色

1. **完全非同步** - 使用 async/await 實作所有 I/O 操作，支援高併發測試執行
2. **類型安全** - Pydantic v2 資料驗證，確保 API 資料完整性
3. **依賴注入** - FastAPI 依賴注入系統，提供鬆耦合架構
4. **測試覆蓋** - 完整的 API 測試套件 (9 個測試類別,100% 通過率)
5. **模組化設計** - 清晰的分層架構 (API/Service/Model/Measurement)
6. **資料庫遷移** - Alembic 支援的資料庫版本控制
7. **uv 包管理** - 現代化的 Python 依賴管理工具

#### PDTool4 完整相容性

- **BaseMeasurement 抽象類別** - 定義標準化測量介面 (prepare/execute/cleanup)
- **7 種 limit_type 支援** - lower, upper, both, equality, inequality, partial, none
- **3 種 value_type 支援** - string, integer, float
- **runAllTest 模式** - 遇到錯誤時繼續執行測試，完全模擬 PDTool4 行為
- **PDTool4 儀器錯誤檢測** - 自動檢測 "No instrument found" 和 "Error:" 訊息
- **MEASUREMENT_REGISTRY** - 動態測量類型註冊表

---

### 前端特色

1. **Composition API** - Vue 3 最新語法，支援複雜邏輯重用
2. **現代建置工具** - Vite 提供快速開發體驗和優化生產建置
3. **響應式設計** - Element Plus UI 組件庫，提供豐富的介面元件
4. **狀態管理** - Pinia 輕量級狀態管理，支援 TypeScript
5. **API 整合** - Axios 客戶端配置，統一錯誤處理與 JWT Token 管理
6. **PDTool4 風格** - TestMain.vue 完全仿照原桌面應用設計
7. **即時狀態更新** - 輪詢機制追蹤測試執行狀態 (WebSocket 預留介面)

---

### 測試引擎特色

#### BaseMeasurement 抽象類別

- **標準化測量介面** - `prepare()`, `execute()`, `cleanup()` 三階段執行
- **智慧型結果驗證** - `validate_result()` 方法支援 PDTool4 所有 limit 類型
- **動態類型轉換** - 支援 string/integer/float 三種 value_type
- **完整 PDTool4 整合**:
  - 7 種 limit_type: `lower`, `upper`, `both`, `equality`, `inequality`, `partial`, `none`
  - 3 種 value_type: `string`, `integer`, `float`
  - 自動儀器錯誤檢測: "No instrument found", "Error:" 訊息處理
  - runAllTest 模式錯誤收集與繼續執行

#### TestEngine 測試編排器

- **非同步架構** - 基於 asyncio 的高效能測試執行
- **會話管理** - 完整的測試會話生命週期追蹤
- **任務調度** - 智慧型測量任務排程與結果記錄
- **runAllTest 模式實作**:
  - 錯誤容錯: 遇到失敗時繼續執行後續測試
  - 錯誤摘要: 執行結束時提供完整錯誤報告
  - PDTool4 行為一致性: 完全模擬原系統行為

#### InstrumentManager 儀器管理器

- **Singleton 模式** - 確保全系統儀器連線唯一性
- **連線池管理** - 高效能的儀器資源管理
- **狀態追蹤** - 即時儀器狀態監控 (IDLE/BUSY/ERROR/OFFLINE)
- **錯誤恢復** - 自動連線重置與故障處理

#### MEASUREMENT_REGISTRY 測量註冊表

- **動態載入** - 支援執行期測量類型註冊
- **類型驗證** - 參數檢查與設定驗證
- **擴充性** - 輕鬆新增自訂測量類型

#### PDTool4 完全相容性

- **驗證邏輯完整遷移** - 所有測試點驗證規則一對一對應
- **行為一致性** - runAllTest 模式前後端統一實作
- **錯誤處理** - PDTool4 風格的錯誤分類與報告

---

## 🔧 故障排除

### 常見問題

#### 1. Docker 容器無法啟動

```bash
# 檢查端口是否被占用
netstat -tuln | grep -E '9080|9100|33306'

# 停止占用端口的服務或修改配置檔案中的端口
```

#### 2. 資料庫連線失敗

```bash
# 檢查資料庫容器狀態
docker-compose ps db

# 查看資料庫日誌
docker-compose logs db

# 手動測試連線
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD}
```

#### 3. 前端無法連接後端 API

```bash
# 檢查後端服務狀態
docker-compose logs backend

# 驗證 API 是否正常
curl http://localhost:9100/docs

# 檢查前端環境變數
cat frontend/.env.development
```

#### 4. Token 過期或無效

```bash
# 清除瀏覽器 localStorage
# 或在瀏覽器開發者工具中執行:
localStorage.clear()
location.reload()
```

#### 5. 測試執行卡住或失敗

```bash
# 檢查測試引擎狀態
curl http://localhost:9100/api/tests/instruments/status

# 重置儀器連線
curl -X POST http://localhost:9100/api/tests/instruments/{instrument_id}/reset

# 查看後端日誌尋找錯誤
docker-compose logs -f backend | grep ERROR
```

---

## 🤝 貢獻指南

歡迎貢獻！請遵循以下步驟：

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送至分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 編碼規範

#### Python (後端)

- ✅ 遵循 PEP 8
- ✅ 使用 Black 格式化
- ✅ 類型提示 (Type Hints)
- ✅ Docstrings 說明

#### JavaScript/Vue (前端)

- ✅ ESLint 規則
- ✅ Prettier 格式化
- ✅ Composition API 優先
- ✅ 註解清晰

---

## 📄 授權

[請在此添加授權資訊]

---

## 📧 聯絡方式

[請在此添加聯絡資訊]

---

## 📚 參考文檔

- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [Vue 3 官方文檔](https://vuejs.org/)
- [Element Plus 文檔](https://element-plus.org/)
- [SQLAlchemy 2.0 文檔](https://docs.sqlalchemy.org/)
- [Pydantic 文檔](https://docs.pydantic.dev/)

---

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

---

## 📈 專案狀態與待辦事項

### 目前狀態 (v0.6.0)

| 項目 | 狀態 | 完成度 |
|------|------|--------|
| **版本** | v0.6.0 | - |
| **完成度** | 核心架構完成 | ~80% |
| **核心架構** | ✅ 已完成 | FastAPI + Vue 3 + MySQL |
| **API 層** | ✅ 已完成 | 70+ 端點，8 個模組 |
| **PDTool4 相容性** | ✅ 已完成 | 完整驗證邏輯與 runAllTest 模式 |
| **測試覆蓋** | ✅ 已完成 | 9 個測試類別，100% 通過率 |
| **前端介面** | ✅ 已完成 | 6 個主要頁面，PDTool4 風格 |
| **資料庫設計** | ✅ 已完成 | 7 個模型，包含遷移 |
| **容器化** | ✅ 已完成 | Docker Compose 完整配置 |
| **儀器驅動** | ⚠️ Stub 實作 | 需實作實際硬體介面 |
| **生產就緒** | ⚠️ 基本可用 | 需安全性強化 |

---

### 已完成的核心功能

#### 1. PDTool4 完整整合

- ✅ BaseMeasurement 抽象類別與 7 種 limit_type 支援
- ✅ runAllTest 模式錯誤處理與繼續執行
- ✅ PDTool4 儀器錯誤檢測機制
- ✅ 測試結果驗證邏輯完整遷移

#### 2. 完整測試引擎

- ✅ TestEngine 非同步測試編排器
- ✅ InstrumentManager Singleton 儀器管理
- ✅ MEASUREMENT_REGISTRY 動態註冊表
- ✅ 測試會話完整生命週期管理

#### 3. 全端開發

- ✅ FastAPI 後端 (async/await, Pydantic v2)
- ✅ Vue 3 前端 (Composition API, Element Plus)
- ✅ MySQL 資料庫 (SQLAlchemy 2.0)
- ✅ Docker 容器化部署

---

### 已知限制與待辦事項

#### 高優先級 🔴

- 🔄 實作實際儀器驅動 (取代 dummy implementations)
  - Power Supply 通訊 (GPIB/串列埠)
  - DMM 數位電表介面
  - Serial 通訊協定
- 🔄 安全性強化
  - 修改預設密碼與金鑰
  - 輸入驗證完善
  - CORS 設定優化

#### 中優先級 🟡

- 🔄 WebSocket 即時通訊 (取代輪詢機制)
- 🔄 前端測試歷史介面完善 (圖表分析)
- 🔄 PDF 報表生成功能
- 🔄 錯誤處理機制統一

#### 低優先級 🟢

- 🔄 Modbus TCP/RTU 整合
- 🔄 SFC WebService 實際連線
- 🔄 多語系支援
- 🔄 系統監控與告警機制
- 🔄 API 速率限制

---

## 📝 更新日誌

### v0.6.0 (最新) - 2026-01-05 - PDTool4 完整整合

#### ✅ PDTool4 核心邏輯完整整合

- BaseMeasurement 類別整合 test_point_runAllTest.py 驗證邏輯
- 支援完整的 7 種 limit_type: lower, upper, both, equality, inequality, partial, none
- 支援完整的 3 種 value_type: string, integer, float
- PDTool4 儀器錯誤檢測: "No instrument found", "Error:" 訊息處理

#### ✅ runAllTest 模式完整實作

- Backend measurement_service.py 實作錯誤收集繼續執行邏輯
- Frontend TestMain.vue 整合 runAllTest UI 與錯誤顯示
- 與 PDTool4 行為 100% 一致

#### ✅ 測試計劃匯入系統

- scripts/import_testplan.py 完整 CSV 匯入工具
- scripts/batch_import.sh 批量匯入自動化腳本
- docs/README_import_testplan.md 詳細使用指南

#### ✅ 前端介面優化

- ProjectStationSelector.vue 站別選擇功能修復
- TestPlanManage.vue API 參數整合修正
- TestMain.vue PDTool4 風格 UI 完善

#### ✅ 完整測試覆蓋

- 9 個測試類別全部通過 (100% 覆蓋率)
- scripts/test_refactoring.py 自動化測試套件
- 所有 limit_type 和 value_type 驗證測試

---

### v0.5.0 - 測試引擎核心架構

#### ✅ TestEngine 測試編排器實作

- 非同步測試執行架構 (asyncio)
- 測試會話狀態管理
- 測量任務智慧調度

#### ✅ InstrumentManager 儀器管理器

- Singleton 模式確保連線唯一性
- 儀器連線池管理
- 狀態追蹤與錯誤恢復

#### ✅ MEASUREMENT_REGISTRY 動態註冊

- 測量類型執行期註冊
- 參數驗證與類型檢查

#### ✅ 完整 API 擴展

- 測試執行 API (5+ 端點)
- 測量執行 API (10 端點)
- 測試結果查詢與 CSV 匯出

#### ✅ 前端 TestMain.vue 實作

- PDTool4 風格完整 UI
- 即時狀態輪詢機制
- 測試控制面板與進度顯示

---

### v0.4.0 - 測試計劃管理系統

#### ✅ CSV 檔案處理

- 測試計劃批量上傳
- 動態欄位映射
- 資料驗證與錯誤處理

#### ✅ 測試計劃 CRUD 操作

- 完整的建立/讀取/更新/刪除 API
- 項目重新排序功能
- 批量刪除支援

#### ✅ 前端管理介面

- TestPlanManage.vue 完整功能
- 表格操作與即時更新
- 匯入進度顯示

---

### v0.3.0 - 專案與站別管理

#### ✅ 專案管理模組

- 專案 CRUD API 與資料模型
- 前端專案選擇器元件
- 專案與站別關聯管理

#### ✅ 站別管理系統

- 站別設定與配置管理
- JSON 配置儲存
- 動態配置載入

---

### v0.2.0 - 認證與權限系統

#### ✅ JWT Token 認證

- 安全 Token 產生與驗證
- 自動刷新機制
- 跨域支援

#### ✅ 角色權限控制

- Admin/Engineer/Operator 三級權限
- API 端點權限檢查
- 前端路由守衛

#### ✅ 登入系統

- Vue 3 登入介面
- 表單驗證與錯誤處理
- 狀態持久化

---

### v0.1.0 - 專案基礎架構

#### ✅ FastAPI 後端初始化

- 非同步 Web 框架設定
- 模組化專案結構
- 開發環境配置

#### ✅ Vue 3 前端初始化

- Composition API 設定
- Vite 建置工具配置
- Element Plus UI 整合

#### ✅ Docker 容器化

- 多服務容器編排
- 開發/生產環境配置
- 健康檢查機制

#### ✅ MySQL 資料庫設計

- 完整 Schema 設計
- Alembic 遷移系統
- 初始資料填充

---

**Last Updated**: 2026-01-05  
**Status**: Core Architecture Complete (~80%), Production Ready Pending  
**Latest Version**: v0.6.0 - PDTool4 Complete Integration
