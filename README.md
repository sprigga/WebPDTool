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
| **版本** | v0.8.1 |
| **完成度** | ~85-90% (核心架構完成，測量服務已重構，儀器驅動 100% 完成) |
| **最新更新** | 2026-02-06 - 測量服務架構重構 (66.6% 程式碼縮減)，25 種儀器驅動 100% 完成 |
| **狀態** | 核心功能完整，測量服務已優化，所有儀器驅動已實現，前端完善中 |

### ✨ 主要特色

- ✅ **完整 PDTool4 相容性** - 支援所有 7 種 limit_type 和 3 種 value_type
- ✅ **runAllTest 模式** - 遇到錯誤時繼續執行測試，與 PDTool4 完全一致
- ✅ **DUT 通訊系統** - 繼電器控制、機架旋轉、二進位協定支援 (3,100+ 行新代碼)
- ✅ **10+ 種測量類型** - PowerSet/Read, CommandTest, SFC, GetSN, OPJudge, Wait, Relay, ChassisRotation, RF_Measurement
- ✅ **25 種儀器驅動** - 100% 完成！Keysight, Keithley, ITECH, GW Instek, R&S, Anritsu 等完整實作
- ✅ **完整 API 層** - 8 個 API 模組，70+ 端點，模組化設計
- ✅ **進階日誌系統** - Redis 串流、請求追蹤、JSON 格式支援
- ✅ **現代化前端** - Vue 3 Composition API + Element Plus UI，專案管理完整實作

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

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "14px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 30,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
graph TD
    %% 此圖展示系統整體分層結構與主要資料流向

    %% 客戶端層
    subgraph ClientLayer["🌐 使用者端"]
        BrowserNode[Web 瀏覽器<br/>Chrome/Edge/Firefox]
    end

    %% 前端層
    subgraph FrontendLayer["🟢 前端服務 Port: 9080"]
        NginxNode[Nginx 反向代理<br/>靜態資源服務]
        VueNode[Vue 3 應用程式<br/>───────────<br/>Element Plus UI<br/>Pinia 狀態管理<br/>Vue Router 路由]
    end

    %% 後端層
    subgraph BackendLayer["🚀 後端服務 Port: 9100"]
        FastAPINode[FastAPI 應用入口<br/>Python 3.11+ 非同步框架]

        subgraph APILayer["API 路由層 - 8個模組, 70+ 端點"]
            direction TB
            AuthAPINode[🔐 認證授權模組<br/>JWT Token 管理]
            ProjectsAPINode[📁 專案管理模組<br/>CRUD 操作]
            StationsAPINode[🏠 站別管理模組<br/>測試站配置]
            TestPlansAPINode[📋 測試計劃模組<br/>測試項目管理]
            TestsAPINode[▶️ 測試執行模組<br/>會話控制與狀態]
            MeasurementsAPINode[📊 測量執行模組<br/>儀器驅動協調]
            ResultsAPINode[📈 測試結果模組<br/>資料查詢與匯出]
            DUTControlAPINode[🔧 DUT 控制模組<br/>繼電器/機架控制]
        end

        subgraph ServicesLayer["業務邏輯層 - 4個核心服務"]
            TestEngineNode[⚙️ 測試引擎<br/>─────────<br/>測試編排與調度<br/>非同步執行控制<br/>會話狀態管理<br/>runAllTest 模式]
            InstrumentMgrNode[🔌 儀器管理器<br/>─────────<br/>Singleton 連線池<br/>儀器狀態追蹤<br/>25 種驅動支援]
            MeasurementSvcNode[📏 測量服務<br/>─────────<br/>測量任務協調<br/>PDTool4 相容驗證<br/>錯誤收集處理]
            SFCSvcNode[🔗 SFC 服務<br/>─────────<br/>MES 系統整合<br/>製造資料上傳]
        end

        subgraph MeasurementsLayer["測量抽象層 - 10+ 測量類型"]
            BaseMeasureNode[📐 BaseMeasurement 基類<br/>──────────────<br/>prepare/execute/cleanup<br/>7 種 limit_type 驗證<br/>3 種 value_type 轉換]
        end

        subgraph ModelsLayer["資料持久層 - 9 個資料表"]
            ORMNode[💾 SQLAlchemy ORM<br/>───────────<br/>User/Project/Station<br/>TestPlan/Session<br/>TestResult/SFCLog<br/>Configuration]
        end
    end

    %% 資料庫層
    subgraph DatabaseLayer["🗄️ 資料庫服務 Port: 33306"]
        MySQLNode[(MySQL 8.0+<br/>────────<br/>資料庫: webpdtool<br/>字元集: utf8mb4<br/>連線池: 非同步)]
    end

    %% 外部系統
    subgraph ExternalLayer["🌍 外部系統整合"]
        SFCNode[🏭 SFC 製造執行系統<br/>WebService 通訊]
        ModbusNode[📡 Modbus 設備通訊<br/>TCP/IP 協定]
        InstrumentsNode[🔬 測試儀器<br/>────────<br/>Keysight/Keithley<br/>R&S/Anritsu<br/>25 種驅動支援]
    end

    %% 主要資料流向
    BrowserNode -->|HTTPS 請求| NginxNode
    NginxNode -->|反向代理| VueNode
    VueNode -->|REST API 呼叫<br/>Axios + JWT| FastAPINode

    FastAPINode -->|路由分派| APILayer
    APILayer -->|呼叫| ServicesLayer
    ServicesLayer -->|執行| MeasurementsLayer
    ServicesLayer -->|存取| ModelsLayer

    ModelsLayer -->|非同步 ORM<br/>SQLAlchemy 2.0| MySQLNode
    SFCSvcNode -.->|HTTPS POST<br/>JSON 格式| SFCNode
    InstrumentMgrNode -.->|TCP/IP<br/>VISA/SSH/CAN| InstrumentsNode
    InstrumentMgrNode -.->|Modbus RTU/TCP| ModbusNode

    %% 樣式定義
    classDef clientStyle fill:#e1f5ff,stroke:#0277bd,stroke-width:2px,color:#000
    classDef frontendStyle fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef backendStyle fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#000
    classDef dbStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
    classDef externalStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000

    class BrowserNode clientStyle
    class NginxNode,VueNode frontendStyle
    class FastAPINode,AuthAPINode,ProjectsAPINode,StationsAPINode,TestPlansAPINode,TestsAPINode,MeasurementsAPINode,ResultsAPINode,DUTControlAPINode,TestEngineNode,InstrumentMgrNode,MeasurementSvcNode,SFCSvcNode,BaseMeasureNode,ORMNode backendStyle
    class MySQLNode dbStyle
    class SFCNode,ModbusNode,InstrumentsNode externalStyle
```

> **📖 架構說明**: 主圖展示系統整體分層結構，API→Services→Models/Measurements 的詳細連線關係見下圖。

### API 層與服務層連線關係

此圖展示 API 端點如何調用業務邏輯服務，以及服務之間的協作關係。

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "14px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 30,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
graph LR
    %% 此圖展示 API、Service、Measurement、Model 之間的調用關係

    subgraph APIGroup["📡 API 路由層 - 接收 HTTP 請求"]
        AuthAPI[認證 API]
        ProjectsAPI[專案 API]
        StationsAPI[站別 API]
        TestPlansAPI[測試計劃 API]
        TestsAPI[測試執行 API]
        MeasurementsAPI[測量執行 API]
        ResultsAPI[測試結果 API]
        DUTControlAPI[DUT 控制 API]
    end

    subgraph ServicesGroup["⚙️ 業務邏輯層 - 實現核心功能"]
        TestEngineService[測試引擎<br/>TestEngine]
        InstrumentMgrService[儀器管理器<br/>InstrumentMgr]
        MeasurementSvcService[測量服務<br/>MeasurementSvc]
        SFCSvcService[SFC 服務<br/>SFC Service]
    end

    subgraph MeasurementsGroup["📏 測量抽象層 - 執行具體測量"]
        BaseMeasureClass[測量基類<br/>BaseMeasurement]
    end

    subgraph ModelsGroup["💾 資料存取層 - ORM 操作"]
        ORMLayer[SQLAlchemy<br/>ORM 模型]
    end

    subgraph DBGroup["🗄️ 持久化儲存"]
        MySQLDB[(MySQL<br/>資料庫)]
    end

    %% API → Services 調用關係
    AuthAPI -->|Token 驗證/刷新| TestEngineService
    ProjectsAPI -->|CRUD 操作| TestEngineService
    StationsAPI -->|配置管理| TestEngineService
    TestPlansAPI -->|計劃載入/驗證| TestEngineService
    TestsAPI -->|會話控制/狀態| TestEngineService
    MeasurementsAPI -->|測量調度| MeasurementSvcService
    ResultsAPI -->|結果查詢| TestEngineService
    DUTControlAPI -->|繼電器/機架| TestEngineService

    %% Services 內部協作
    TestEngineService -->|獲取儀器連線| InstrumentMgrService
    TestEngineService -->|協調測量| MeasurementSvcService
    TestEngineService -->|上傳製造資料| SFCSvcService
    MeasurementSvcService -->|執行測量邏輯| BaseMeasureClass

    %% Services → Models 資料存取
    TestEngineService -->|讀寫測試資料| ORMLayer
    MeasurementSvcService -->|儲存測量結果| ORMLayer

    %% Models → Database 持久化
    ORMLayer -->|非同步 ORM 操作<br/>SQLAlchemy 2.0| MySQLDB

    %% 樣式定義
    classDef apiStyle fill:#e1bee7,stroke:#4a148c,stroke-width:2px,color:#000
    classDef svcStyle fill:#c5cae9,stroke:#1a237e,stroke-width:2px,color:#000
    classDef measureStyle fill:#b2dfdb,stroke:#00695c,stroke-width:2px,color:#000
    classDef modelStyle fill:#ffccbc,stroke:#bf360c,stroke-width:2px,color:#000
    classDef dbStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000

    class AuthAPI,ProjectsAPI,StationsAPI,TestPlansAPI,TestsAPI,MeasurementsAPI,ResultsAPI,DUTControlAPI apiStyle
    class TestEngineService,InstrumentMgrService,MeasurementSvcService,SFCSvcService svcStyle
    class BaseMeasureClass measureStyle
    class ORMLayer modelStyle
    class MySQLDB dbStyle
```

### 測試執行完整流程

此流程圖展示從使用者登入到測試完成的完整生命週期，包含 runAllTest 模式的錯誤處理邏輯。

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "14px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
flowchart TD
    %% 此圖展示測試執行的完整生命週期，包含 runAllTest 模式的錯誤容錯處理

    Start([🟢 流程開始])
    Login[使用者登入<br/>輸入帳號密碼]
    ValidateUser{{身分驗證<br/>通過?}}
    GetToken[取得 JWT Token<br/>儲存至 localStorage]

    SelectProject[選擇測試專案<br/>與站別]
    LoadConfig[載入站別配置<br/>儀器連線設定]
    LoadTestPlan[載入測試計劃<br/>CSV 項目清單]

    InputSN[輸入產品序號<br/>掃描條碼]
    ValidateSN{{SN 格式<br/>有效?}}
    CreateSession[創建測試會話<br/>記錄至 test_sessions]

    StartTest[啟動測試執行<br/>POST /api/tests/sessions/start]
    GetNextItem[獲取下一測試項目<br/>依 sequence_order 排序]

    HasItem{{還有未執行<br/>測試項目?}}
    CalcResult[計算最終結果<br/>PASS/FAIL 統計]
    LoadMeasure[載入測量配置<br/>MEASUREMENT_REGISTRY]

    Execute[執行測量<br/>prepare → execute → cleanup]
    GetValue[獲取測量值<br/>儀器讀取/命令執行]
    Validate[驗證測試點<br/>validate_result 方法]

    SaveResult[儲存測試結果<br/>記錄至 test_results]
    UpdateUI[更新前端 UI<br/>顯示即時狀態]

    TestFailed{{測試項目<br/>失敗?}}
    CheckRunAllTest{{runAllTest<br/>模式?}}
    CollectError[收集錯誤資訊<br/>繼續執行下一項]

    UpdateSession[更新會話狀態<br/>final_result, 統計資料]

    NeedSFC{{站別配置<br/>需上傳 SFC?}}
    UploadSFC[上傳至 SFC 系統<br/>MES 製造資料]
    LogSFC[記錄 SFC 日誌<br/>sfc_logs 表]
    ShowReport[顯示測試報告<br/>PASS/FAIL 摘要]

    ContinueTest{{繼續測試<br/>下一個產品?}}
    End([🔴 流程結束])

    %% 流程連接
    Start --> Login
    Login --> ValidateUser
    ValidateUser -->|❌ 驗證失敗| Login
    ValidateUser -->|✅ 驗證成功| GetToken

    GetToken --> SelectProject
    SelectProject --> LoadConfig
    LoadConfig --> LoadTestPlan

    LoadTestPlan --> InputSN
    InputSN --> ValidateSN
    ValidateSN -->|❌ 無效格式| InputSN
    ValidateSN -->|✅ 格式正確| CreateSession

    CreateSession --> StartTest
    StartTest --> GetNextItem

    GetNextItem --> HasItem
    HasItem -->|❌ 無更多項目| CalcResult
    HasItem -->|✅ 有下一項目| LoadMeasure

    LoadMeasure --> Execute
    Execute --> GetValue
    GetValue --> Validate

    Validate --> SaveResult
    SaveResult --> UpdateUI

    UpdateUI --> TestFailed
    TestFailed -->|❌ PASS| GetNextItem
    TestFailed -->|✅ FAIL/ERROR| CheckRunAllTest

    CheckRunAllTest -->|✅ 啟用| CollectError
    CheckRunAllTest -->|❌ 停用| CalcResult

    CollectError --> GetNextItem

    CalcResult --> UpdateSession

    UpdateSession --> NeedSFC
    NeedSFC -->|✅ 需要上傳| UploadSFC
    UploadSFC --> LogSFC
    LogSFC --> ShowReport
    NeedSFC -->|❌ 不需上傳| ShowReport

    ShowReport --> ContinueTest
    ContinueTest -->|✅ 繼續| InputSN
    ContinueTest -->|❌ 結束| End

    %% 樣式定義
    classDef dbOp fill:#bbdefb,stroke:#1565c0,stroke-width:2px,color:#000
    classDef decision fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000
    classDef startN fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef endN fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    classDef act fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000
    classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000

    %% 應用樣式
    class CreateSession,SaveResult,UpdateSession,LogSFC dbOp
    class ValidateUser,ValidateSN,HasItem,TestFailed,CheckRunAllTest,NeedSFC,ContinueTest decision
    class Login,GetToken,SelectProject,LoadConfig,LoadTestPlan,InputSN,StartTest,GetNextItem,LoadMeasure,Execute,GetValue,Validate,UpdateUI,CalcResult,UploadSFC,ShowReport act
    class CollectError error
    class Start startN
    class End endN
```

### 資料庫關係圖

展示系統中 9 個核心資料表之間的關聯性與資料流向。

```mermaid
erDiagram
    %% 使用者與測試會話關係
    users ||--o{ test_sessions : "執行測試"

    %% 專案與站別關係
    projects ||--o{ stations : "包含站別"

    %% 站別與測試計劃/會話關係
    stations ||--o{ test_plans : "定義測試計劃"
    stations ||--o{ test_sessions : "執行測試會話"

    %% 測試計劃與測試結果關係
    test_plans ||--o{ test_results : "產生測試結果"

    %% 測試會話與測試結果/SFC日誌關係
    test_sessions ||--|{ test_results : "包含測試結果"
    test_sessions ||--o{ sfc_logs : "產生 SFC 日誌"

    %% 資料表定義
    users {
        bigint id PK "主鍵"
        varchar(50) username UK "使用者名稱(唯一)"
        varchar(255) password_hash "bcrypt 密碼雜湊"
        enum role "角色: ADMIN/ENGINEER/OPERATOR"
        varchar(100) full_name "全名"
        varchar(100) email "電子郵件"
        boolean is_active "帳號啟用狀態"
        timestamp created_at "建立時間"
        timestamp updated_at "更新時間"
    }

    projects {
        int id PK "主鍵"
        varchar(50) project_code UK "專案代碼(唯一)"
        varchar(100) project_name "專案名稱"
        text description "專案描述"
        boolean is_active "啟用狀態"
        timestamp created_at "建立時間"
        timestamp updated_at "更新時間"
    }

    stations {
        int id PK "主鍵"
        varchar(50) station_code "站別代碼"
        varchar(100) station_name "站別名稱"
        int project_id FK "所屬專案 ID"
        varchar(255) test_plan_path "測試計劃檔案路徑"
        json config_json "站別配置(JSON)"
        boolean is_active "啟用狀態"
        timestamp created_at "建立時間"
        timestamp updated_at "更新時間"
    }

    test_plans {
        int id PK "主鍵"
        int station_id FK "所屬站別 ID"
        int item_no "測試項目編號"
        varchar(100) item_name "測試項目名稱"
        varchar(50) test_type "測試類型(10+種)"
        json parameters "測試參數(JSON)"
        decimal lower_limit "下限值"
        decimal upper_limit "上限值"
        varchar(20) limit_type "限制類型(7種)"
        varchar(20) value_type "值類型(3種)"
        varchar(20) unit "測量單位"
        boolean enabled "啟用狀態"
        int sequence_order "執行順序"
        timestamp created_at "建立時間"
        timestamp updated_at "更新時間"
    }

    test_sessions {
        int id PK "主鍵"
        varchar(100) serial_number "產品序號(SN)"
        int station_id FK "執行站別 ID"
        int user_id FK "執行者 ID"
        timestamp start_time "開始時間"
        timestamp end_time "結束時間"
        enum final_result "最終結果: PASS/FAIL/ABORT"
        int total_items "總測試項目數"
        int pass_items "通過項目數"
        int fail_items "失敗項目數"
        int test_duration_seconds "測試時長(秒)"
        timestamp created_at "建立時間"
    }

    test_results {
        bigint id PK "主鍵"
        int session_id FK "測試會話 ID"
        int test_plan_id FK "測試計劃 ID"
        int item_no "測試項目編號"
        varchar(100) item_name "測試項目名稱"
        decimal measured_value "實際測量值"
        decimal lower_limit "規格下限"
        decimal upper_limit "規格上限"
        varchar(20) unit "測量單位"
        enum result "測試結果: PASS/FAIL/SKIP/ERROR"
        text error_message "錯誤訊息"
        timestamp test_time "測試時間"
        int execution_duration_ms "執行時長(毫秒)"
    }

    sfc_logs {
        bigint id PK "主鍵"
        int session_id FK "關聯測試會話 ID"
        varchar(50) operation "操作類型"
        json request_data "SFC 請求資料"
        json response_data "SFC 回應資料"
        enum status "狀態: SUCCESS/FAILED/TIMEOUT"
        text error_message "錯誤訊息"
        timestamp created_at "建立時間"
    }

    configurations {
        int id PK "主鍵"
        varchar(100) config_key UK "設定鍵值(唯一)"
        json config_value "設定值(JSON)"
        varchar(50) category "設定類別"
        text description "描述說明"
        boolean is_system "系統設定標記"
        timestamp created_at "建立時間"
        timestamp updated_at "更新時間"
    }

    modbus_logs {
        bigint id PK "主鍵"
        int register_address "Modbus 暫存器位址"
        enum operation "操作: READ/WRITE"
        varchar(255) value "讀取/寫入值"
        enum status "狀態: SUCCESS/FAILED"
        text error_message "錯誤訊息"
        timestamp created_at "建立時間"
    }
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

#### API 層 (backend/app/api/) - 8 個模組

1. **auth.py** - 認證與授權管理 (JWT Token)
2. **projects.py** - 專案 CRUD 操作
3. **stations.py** - 站別管理
4. **testplan/** - 測試計劃模組 (queries, mutations, sessions, validation) - 已模組化
5. **tests.py** - 測試會話執行與控制
6. **measurements.py** - 測量任務執行
7. **results/** - 測試結果模組 (sessions, measurements, reports, export, cleanup, summary) - 已模組化
8. **dut_control.py** - DUT 通訊控制 (繼電器切換、機架旋轉) ✨ **新增**

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

- **auth.py** - JWT Token 管理、密碼驗證
- **test_engine.py** - 測試編排引擎 (TestEngine, 507 行)
  - 非同步測試執行 (asyncio)
  - 測試會話狀態管理 (`TestExecutionState`)
  - 測量任務調度
  - 自動報表生成 (CSV 匯出)
  - runAllTest 模式支援
- **instrument_manager.py** - 儀器管理器 (Singleton)
  - 儀器連線池管理
  - 儀器狀態追蹤
  - 連線重置機制
- **measurement_service.py** - 測量服務協調 (709 行)
  - **架構更新 (2026-02-06)**: 從雙路徑架構重構為單路徑架構
  - 所有測量執行現在委派給 implementations.py 類別
  - 移除 1,401 行重複的 legacy 程式碼 (66.6% 縮減: 2,103 → 702 行)
  - execute_single_measurement() 現在專門使用 get_measurement_class()
- **report_service.py** - 自動報表生成服務

---

#### DUT 通訊系統 (backend/app/services/dut_comms/) ✨ **2026-01-30 新增 (~3,100 行)**

- **relay_controller.py** - 繼電器開關控制 (映射 PDTool4 的 MeasureSwitchON/OFF)
- **chassis_controller.py** - 機架旋轉控制 (映射 PDTool4 的 MyThread_CW/CCW)
- **ls_comms/** - LS 通訊協定實作
- **vcu_ether_comms/** - VCU 乙太網路通訊
- **ltl_chassis_fixt_comms/** - 機架夾具二進位協定 (CRC16 校驗)
- **common/struct_message.py** - 二進位訊息封包處理

---

#### 儀器驅動層 (backend/app/services/instruments/) ✨ **25 種儀器驅動 100% 完成**

**資料擷取器 (DAQ)**
- **daq973a.py** - Keysight DAQ973A 多功能資料擷取器
- **daq6510.py** - Keithley DAQ6510 資料擷取/記錄系統
- **a34970a.py** - Agilent 34970A 資料擷取/切換單元

**電源供應器 (Power Supply)**
- **model2303.py** - Keithley 2303 電源供應器
- **model2306.py** - Keithley 2306 電源供應器
- **it6723c.py** - ITECH IT6723C 電源供應器
- **psw3072.py** - GW Instek PSW3072 電源供應器
- **aps7050.py** - GW Instek APS-7050 AC/DC 電源 + DMM (Phase 2)
- **a2260b.py** - Keithley 2260B 可程控直流電源

**測量儀器**
- **keithley2015.py** - Keithley 2015 數位電表
- **mdo34.py** - Tektronix MDO34 混合域示波器
- **n5182a.py** - Agilent N5182A MXG 訊號產生器 (Phase 2)

**RF 測試儀器 (Phase 3)**
- **cmw100.py** - R&S CMW100 無線通訊測試儀 (BLE/WiFi, RsInstrument SDK)
- **mt8872a.py** - Anritsu MT8872A LTE 射頻測試工具 (PyVISA)
- **smcv100b.py** - R&S SMCV100B 向量訊號產生器 (RsSmcv)

**多功能與特殊儀器 (Phase 2)**
- **analog_discovery_2.py** - Digilent AD2 USB 多功能儀器 (WaveForms SDK)
- **ftm_on.py** - FTM 測試模式控制器

**通用通訊介面 (Phase 1)**
- **comport_command.py** - 通用 COM Port 串口介面
- **tcpip_command.py** - 通用 TCP/IP 網路介面
- **console_command.py** - 控制台命令執行器
- **wait_test.py** - 測試延遲/等待控制

**控制器與通訊 (Phase 3)**
- **l6mpu_ssh.py** - L6MPU SSH 控制器
- **l6mpu_ssh_comport.py** - L6MPU SSH + Serial 混合控制器
- **l6mpu_pos_ssh.py** - L6MPU Position 位置控制器
- **peak_can.py** - PEAK CAN 總線介面

**基礎架構**
- **base.py** - `BaseInstrumentDriver` 抽象基礎類別
  - `initialize()` - 儀器初始化
  - `reset()` - 儀器重置
  - async/await 完整支援

> **🎉 PDTool4 儀器驅動 100% 完成** - 所有 25 種儀器驅動已實現並整合

---

#### 測量模組層 (backend/app/measurements/)

- **base.py**: BaseMeasurement 抽象基礎類別 (379 行)
  - 定義測量介面規範 (`setup()` / `execute()` / `cleanup()`)
  - MeasurementResult 資料結構
  - 結果驗證機制 (支援 PDTool4 所有 limit 類型)
  - 值類型轉換 (string/integer/float)
  - **PDTool4 驗證邏輯完整整合** (支援 7 種 limit_type, 3 種 value_type)
  - runAllTest 模式錯誤處理
  - PDTool4 儀器錯誤檢測 ("No instrument found", "Error:")

- **implementations.py**: 10+ 種測量實作 (509 行)
  - **DummyMeasurement** - 測試用假測量
  - **PowerSetMeasurement** - 電源供應器控制
  - **PowerReadMeasurement** - 電壓/電流讀取
  - **CommandTestMeasurement** - Shell 命令執行測試
  - **SFCMeasurement** - SFC (MES) 整合測試
  - **GetSNMeasurement** - 產品序號取得
  - **OPJudgeMeasurement** - 操作員手動判定
  - **WaitMeasurement** - 延遲等待
  - **RelayMeasurement** - DUT 繼電器控制 ✨ **新增** (對應 PDTool4 MeasureSwitchON/OFF)
  - **ChassisRotationMeasurement** - 機架旋轉控制 ✨ **新增** (對應 PDTool4 MyThread_CW/CCW)

- **registry.py**: MEASUREMENT_REGISTRY 測量類型註冊表

---

#### 架構分析與設計模式

**測量抽象層 (Measurement Abstraction Layer)**

WebPDTool 實現了完整的測量抽象層，與 PDTool4 的 Polish 框架對應：

| 層級 | PDTool4 (Polish) | WebPDTool (FastAPI) | 功能 |
|------|-----------------|-------------------|------|
| 抽象基類 | `polish.Measurement` | `BaseMeasurement` | 定義測量介面 |
| 生命週期 | `setup()`/`measure()`/`teardown()` | `prepare()`/`execute()`/`cleanup()` | 三階段執行 |
| 測試點 | `test_point` | `MeasurementResult` | 結果資料結構 |
| 驗證邏輯 | `test_point_runAllTest.py` | `validate_result()` | 限制檢查 |

**測量分派機制 (Measurement Dispatch)**

```python
# PDTool4: oneCSV_atlas_2.py
if exec_name == 'SFCtest':
    SFC_GONOGOMeasurement.MeasureSwitchON(...).run()
elif exec_name == 'PowerSet':
    PowerSetMeasurement.MeasureSwitchON(...).run()

# WebPDTool: registry.py + MEASUREMENT_REGISTRY
MEASUREMENT_REGISTRY = {
    'SFCtest': SFCMeasurement,
    'PowerSet': PowerSetMeasurement,
    'PowerRead': PowerReadMeasurement,
    'CommandTest': CommandTestMeasurement,
    'getSN': GetSNMeasurement,
    'OPjudge': OPJudgeMeasurement,
    'Wait': WaitMeasurement,
    'Relay': RelayMeasurement,
    'ChassisRotation': ChassisRotationMeasurement,
}
```

**資料流模式 (Data Flow Pattern)**

```
CSV Test Plan → 測量分派 → 執行測量 → 驗證結果 → 儲存資料庫
     ↓              ↓            ↓           ↓            ↓
   params     Registry      execute()   validate()   TestResult
```

**關鍵設計決策**

1. **非同步優先**: 所有 I/O 操作使用 async/await，支援高併發
2. **Singleton 模式**: InstrumentManager 確保儀器連線唯一性
3. **Registry 模式**: 動態測量類型註冊，易於擴展
4. **三階段執行**: prepare → execute → cleanup，對應 Polish 的 setup → measure → teardown
5. **runAllTest 相容**: 錯誤收集與繼續執行邏輯完整實作

---

### 前端架構 (~4,200 行 Vue 代碼)

#### 頁面組件 (frontend/src/views/)

**✅ 完整實作**
- **Login.vue** (190 行) - 使用者登入介面，表單驗證
- **TestMain.vue** (1,781 行) - 測試執行主控台 (完整 PDTool4 風格 UI)
  - 專案/站別選擇器整合
  - SFC 配置對話框
  - runAllTest 模式切換
  - 即時測試結果表格
  - 進度追蹤與統計
  - 狀態徽章 (PASS/FAIL/SKIP/ERROR)
  - 循環計數器
- **ProjectManage.vue** (704 行) - 專案與站別完整 CRUD 管理 ✨
  - 專案表格 (排序/篩選)
  - 站別管理
  - 建立/編輯對話框
  - 刪除確認機制
  - 基於角色的權限控制 (僅 Admin)
- **TestPlanManage.vue** (935 行) - 測試計劃管理
- **TestExecution.vue** (565 行) - 測試執行監控

**⚠️ 佔位符 (待完善)**
- **TestHistory.vue** (16 行) - 測試歷史查詢 (僅佔位符)
- **SystemConfig.vue** (16 行) - 系統配置 (僅佔位符)

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

### ✅ 階段 5: 測試執行引擎 (完整實作 ✅)

- [x] 測試會話資料模型 (TestSession)
- [x] 測試結果資料模型 (TestResult)
- [x] BaseMeasurement 抽象基礎類別 (378 行)
  - [x] **PDTool4 驗證邏輯完整整合** (支援 7 種 limit_type)
  - [x] runAllTest 模式錯誤處理
  - [x] PDTool4 儀器錯誤檢測
- [x] 10+ 種測量實作模組 (1,632 行)
  - [x] PowerSet, PowerRead, CommandTest
  - [x] SFCtest, getSN, OPjudge, Wait
  - [x] **Relay, ChassisRotation** (新增，對應 PDTool4)
  - [x] 完整的 limit 類型支援 (lower/upper/both/equality/inequality/partial/none)
  - [x] 值類型轉換 (string/integer/float)
- [x] TestEngine 測試編排引擎 (507 行)
  - [x] 非同步測試執行 (asyncio)
  - [x] 測試會話狀態管理 (`TestExecutionState`)
  - [x] 測量任務調度
  - [x] 自動報表生成 (CSV)
- [x] InstrumentManager 儀器管理器
  - [x] Singleton 模式實作
  - [x] 儀器連線池管理
  - [x] 儀器狀態追蹤
- [x] 完整 API 層 (8 個模組)
  - [x] 測試執行相關 API
  - [x] 測量執行相關 API
  - [x] 測試會話管理 API
  - [x] 測試結果查詢與匯出 API
  - [x] **DUT 控制 API** (新增)
- [x] 前端測試執行主介面 (TestMain.vue, 1,781 行)
  - [x] PDTool4 風格 UI 設計
  - [x] 測試控制面板
  - [x] 條碼掃描輸入
  - [x] 測試計劃表格顯示
  - [x] 進度與狀態顯示
  - [x] **runAllTest 模式整合**
- [x] 即時狀態輪詢機制
- [x] 儀器狀態查詢與重置
- [x] MEASUREMENT_REGISTRY 測量類型註冊表
- [x] 測試計劃匯入工具與批量匯入腳本
- [x] 完整的測試覆蓋 (9 個測試類別)

---

### ✅ 階段 6: DUT 通訊與進階功能 (2026-01 完成 ✅)

- [x] **DUT 通訊系統** (~3,100 行新代碼) ✨
  - [x] 繼電器控制 (relay_controller.py)
  - [x] 機架旋轉控制 (chassis_controller.py)
  - [x] LS 通訊協定
  - [x] VCU 乙太網路通訊
  - [x] 機架夾具二進位協定 (CRC16)
- [x] **進階日誌系統 v2** ✨
  - [x] Redis 串流支援
  - [x] 請求上下文追蹤 (request_id, user_id, session_id)
  - [x] JSON 日誌格式
  - [x] 背景日誌刷新器
- [x] **ProjectManage 前端頁面** (704 行) ✨
  - [x] 完整 CRUD 介面
  - [x] 基於角色的權限 UI
  - [x] 刪除確認與空狀態
  - [x] 響應式設計

---

### ✅ 階段 7: 儀器驅動完整實現 (2026-02 完成 ✅)

**Phase 1 - 通用通訊介面 (完成 ✅)**
- [x] **ComPortCommand** - 通用串口介面
- [x] **TCPIPCommand** - 通用 TCP/IP 網路介面
- [x] **ConSoleCommand** - 控制台命令執行器
- [x] **Wait_test** - 測試延遲控制

**Phase 2 - 常用測試儀器 (完成 ✅)**
- [x] **APS7050** - GW Instek AC/DC 電源 + DMM
- [x] **N5182A** - Agilent 訊號產生器
- [x] **AnalogDiscovery2** - USB 多功能儀器
- [x] **FTM_On** - FTM 測試模式控制器

**Phase 3 - RF 測試儀器 (完成 ✅)**
- [x] **CMW100** - R&S CMW100 無線通訊測試儀 (BLE/WiFi)
  - [x] RsInstrument SDK 整合
  - [x] BLE TX Power 測量
  - [x] WiFi TX Power & EVM 測量
  - [x] 單元測試套件
- [x] **MT8872A** - Anritsu LTE 射頻測試工具
  - [x] PyVISA 整合
  - [x] LTE TX/RX 測量
  - [x] 單元測試套件

**Phase 3 - 低優先級儀器 (完成 ✅)**
- [x] **L6MPU_SSH** - i.MX8MP SSH 控制器
- [x] **L6MPU_SSH_COMPORT** - L6MPU SSH + Serial 混合控制器
- [x] **L6MPU_POS_SSH** - L6MPU 位置控制器
- [x] **PEAK_CAN** - PEAK CAN 總線介面
- [x] **SMCV100B** - R&S SMCV100B 向量訊號產生器

**🎉 儀器驅動 100% 完成 (25/25)** - 所有 PDTool4 儀器驅動已完整實現！

---

### ⚠️ 階段 8: 前端完善與生產優化 (進行中 40%)

**前端完善 (40% 完成)**
- [x] TestMain, ProjectManage, TestPlanManage 完整實作
- ⏳ TestHistory 介面 (僅 16 行佔位符)
- ⏳ SystemConfig 介面 (僅 16 行佔位符)
- [ ] 測試結果圖表分析
- [ ] PDF 報表生成功能

---

### ⏳ 階段 8: 生產環境優化與測試 (待實作 0%)

**安全性強化**
- [ ] 修改預設密碼與金鑰
- [ ] 輸入驗證完善
- [ ] CORS 設定優化
- [ ] SQL 注入防護加強

**效能優化**
- [ ] 資料庫查詢優化
- [ ] Redis 快取機制
- [ ] API 速率限制

**測試與監控**
- [ ] 完整的 pytest 測試套件 (API 端點)
- [ ] 前端單元測試 (Vitest)
- [ ] 監控與告警機制 (Prometheus)
- [ ] 健康檢查完善
- [ ] 日誌輪轉與備份策略

**進階功能**
- [ ] WebSocket 即時通訊 (取代輪詢)
- [ ] 儀器校驗管理
- [ ] 系統日誌與審計
- [ ] 權限細粒度控制
- [ ] 多語系支援

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

### 目前狀態 (v0.8.0 - 2026-02-05)

| 項目 | 狀態 | 完成度 | 說明 |
|------|------|--------|------|
| **版本** | v0.8.0 | - | 儀器驅動 100% 完成 |
| **整體完成度** | 核心完整 | **85-90%** | 儀器驅動完成，前端完善中 |
| **核心架構** | ✅ 已完成 | 100% | FastAPI + Vue 3 + MySQL |
| **API 層** | ✅ 已完成 | 95% | 8 個模組，70+ 端點 |
| **測試引擎** | ✅ 已完成 | 98% | TestEngine + InstrumentManager |
| **測量系統** | ✅ 已完成 | 95% | 10+ 種測量類型，完整 PDTool4 相容 |
| **DUT 通訊** | ✅ 已完成 | 90% | 繼電器/機架控制，3K+ 行新代碼 |
| **儀器驅動** | ✅ 已完成 | 100% | **25 種驅動全部實現** 🎉 |
| **資料庫** | ✅ 已完成 | 100% | 9 個表格，完整 Schema |
| **前端核心** | ✅ 已完成 | 85% | TestMain/ProjectManage 完整 |
| **前端管理** | ⚠️ 部分完成 | 40% | History/Config 為佔位符 |
| **日誌系統** | ✅ 已完成 | 90% | Redis 串流、請求追蹤 |
| **容器化** | ✅ 已完成 | 100% | Docker Compose 完整配置 |
| **SFC 整合** | ⚠️ 框架完成 | 30% | 需 WebService 客戶端 |
| **測試覆蓋** | ⚠️ 基本完成 | 40% | 儀器驅動測試完整，需完整 API 測試 |
| **生產就緒** | ⚠️ 接近完成 | 80% | 需前端完善與安全性強化 |

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

#### 3. 25 種儀器驅動 100% 完成 🎉

**Phase 1 - 通用通訊介面 (4/4)**
- ComPortCommand, TCPIPCommand, ConSoleCommand, Wait_test

**Phase 2 - 常用測試儀器 (4/4)**
- APS7050, N5182A, AnalogDiscovery2, FTM_On

**Phase 3 - RF 測試儀器 (2/2)**
- CMW100 (R&S) - RsInstrument SDK, BLE/WiFi 測量
- MT8872A (Anritsu) - PyVISA, LTE TX/RX 測量

**Phase 3 - 低優先級儀器 (5/5)**
- L6MPU_SSH, L6MPU_SSH_COMPORT, L6MPU_POS_SSH
- PEAK_CAN (python-can)
- SMCV100B (RsSmcv)

**核心儀器 (10/10)**
- 資料擷取: DAQ973A, DAQ6510, 34970A
- 電源供應: 2303, 2306, IT6723C, PSW3072, 2260B, APS7050
- 測量儀器: Keithley2015, MDO34, N5182A
- 多功能: AnalogDiscovery2, FTM_On

#### 4. 全端開發

- ✅ FastAPI 後端 (async/await, Pydantic v2)
- ✅ Vue 3 前端 (Composition API, Element Plus)
- ✅ MySQL 資料庫 (SQLAlchemy 2.0)
- ✅ Docker 容器化部署
- ✅ 測試會話完整生命週期管理

#### 3. 全端開發

- ✅ FastAPI 後端 (async/await, Pydantic v2)
- ✅ Vue 3 前端 (Composition API, Element Plus)
- ✅ MySQL 資料庫 (SQLAlchemy 2.0)
- ✅ Docker 容器化部署

---

### 已知限制與待辦事項

#### 高優先級 🔴

- 🔄 安全性強化
  - 修改預設密碼與金鑰
  - 輸入驗證完善
  - CORS 設定優化
- 🔄 前端介面完善
  - TestHistory 介面實作
  - SystemConfig 介面實作

#### 中優先級 🟡

- 🔄 WebSocket 即時通訊 (取代輪詢機制)
- 🔄 測試結果圖表分析
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

### v0.8.1 (最新) - 2026-02-06 - 測量服務架構重構 ✨

#### ✅ 測量服務架構優化 (66.6% 程式碼縮減)

**架構重構**
- **單路徑執行模型**: 從雙路徑 (legacy subprocess + modern async) 重構為單路徑架構
- **程式碼精簡**: 移除 1,401 行重複的 legacy 程式碼 (2,103 → 702 行，66.6% 縮減)
- **統一分派**: 所有測量執行現在委派給 `implementations.py` 類別
- **清理完成**: 移除 `measurement_dispatch` 字典中的重複執行器

**技術細節**
- `execute_single_measurement()` 現在專門使用 `get_measurement_class()`
- Legacy subprocess helper (`_execute_instrument_command`) 僅保留向後相容性
- 測量服務從 2,103 行精簡至 709 行
- 所有測量類型統一透過 `MEASUREMENT_REGISTRY` 分派

**效益**
- 更簡潔的程式碼結構
- 統一的錯誤處理路徑
- 更容易維護和擴展
- 減少 66.6% 的重複程式碼

---

### v0.8.0 - 2026-02-05 - 儀器驅動完整實現 🎉

#### ✅ Phase 3 儀器驅動完整實現 (100% 完成)

**RF 測試儀器**
- **CMW100Driver** (Rohde & Schwarz CMW100)
  - RsInstrument SDK 完整整合
  - BLE TX Power 測量 (連接器、頻率、預期功率)
  - WiFi TX Power & EVM 測量 (標準、頻道、頻寬)
  - 模擬模式支援 (sim://cmw100)
  - 單元測試套件 (tests/test_instruments/test_cmw100.py)

- **MT8872ADriver** (Anritsu MT8872A)
  - PyVISA SCPI 命令整合
  - LTE TX Power 測量 (頻段、頻道、頻寬)
  - LTE RX Sensitivity 測量
  - Signal Generator 模式 (RX 測試)
  - 波形支援: GSM, WCDMA, LTE, NR
  - 單元測試套件 (tests/test_instruments/test_mt8872a.py)

**低優先級儀器**
- **L6MPUSSHDriver** - i.MX8MP SSH 控制器 (paramiko)
- **L6MPUSSHComPortDriver** - L6MPU SSH + Serial 混合控制器
- **L6MPUPOSSHDriver** - L6MPU 位置控制器
- **PEAKCANDriver** - PEAK CAN 總線介面 (python-can)
- **SMCV100BDriver** - R&S SMCV100B 向量訊號產生器 (RsSmcv)

**通用通訊介面 (Phase 1)**
- **ComPortCommand** - 通用串口介面
- **TCPIPCommand** - 通用 TCP/IP 網路介面
- **ConSoleCommand** - 控制台命令執行器
- **Wait_test** - 測試延遲控制

**測量整合**
- RF 測量類更新使用真實儀器驅動
- BLE_TxPowerMeasurement 使用 CMW100Driver
- LTE_TxPowerMeasurement 使用 MT8872ADriver
- 連線池管理與儀器初始化

**依賴套件更新**
```txt
RsInstrument>=1.50.0  # CMW100/SMCV100B 專用
pyvisa>=1.13.0        # MT8872A 通用 VISA
paramiko>=3.0.0       # SSH 連線 (L6MPU)
python-can>=4.0.0     # CAN 總線 (PEAK)
```

#### ✅ 儀器實現狀態文檔更新

- 更新 `docs/lowsheen_lib/Instrument_Implementation_Status.md` 至 v1.4
- 完成度: 100% (25/25 儀器驅動)
- 所有 PDTool4 儀器驅動已完成重構

#### ✅ 測試覆蓋

- 新增 RF 儀器單元測試
- 測試覆蓋: Phase 3 RF + Phase 3 Low Priority

---

### v0.7.0 - 2026-01-30 - DUT 通訊系統與進階功能

#### ✅ DUT 通訊系統完整實作 (~3,000 行新代碼)

- **繼電器控制系統** (relay_controller.py)
  - 對應 PDTool4 的 MeasureSwitchON/MeasureSwitchOFF
  - RelayMeasurement 測量類型整合
  - 非同步繼電器切換控制

- **機架旋轉系統** (chassis_controller.py)
  - 對應 PDTool4 的 MyThread_CW/MyThread_CCW
  - ChassisRotationMeasurement 測量類型整合
  - 順時針/逆時針旋轉控制

- **通訊協定層實作**
  - LS 通訊協定 (ls_comms/)
  - VCU 乙太網路通訊 (vcu_ether_comms/)
  - 機架夾具二進位協定 (ltl_chassis_fixt_comms/)
  - CRC16 校驗封包處理 (struct_message.py)

#### ✅ 10 種儀器驅動完整實作 (~88KB)

- **資料擷取器**: DAQ973A, DAQ6510, 34970A
- **電源供應器**: Keithley 2303/2306, ITECH IT6723C, GW Instek PSW3072
- **測量儀器**: Keithley 2015 DMM, MDO34 示波器, A2260B 產生器
- **架構**: BaseInstrumentDriver 抽象基礎類別，完整 async/await

#### ✅ 進階日誌系統 v2 (logging_v2.py)

- Redis 串流支援 (可選)
- 請求上下文追蹤 (request_id, user_id, session_id)
- JSON 日誌格式選項
- 背景日誌刷新器

#### ✅ ProjectManage 前端頁面 (704 行)

- 完整專案與站別 CRUD 介面
- 基於角色的權限控制 UI (僅 Admin 可操作)
- 空狀態與響應式設計
- 刪除確認機制

#### ✅ 文檔重組

- 重新整理專案文檔結構
- 測試結構重組 (docs/, tests/)

---

### v0.6.0 - 2026-01-05 - PDTool4 完整整合

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

**Last Updated**: 2026-02-06
**Status**: Core Complete (85-90%), Instrument Drivers 100% Complete, Measurement Service Refactored
**Latest Version**: v0.8.1 - Measurement Service Architecture Refactoring (25/25)

**Key Recent Additions**:
- ✨ **Architecture Refactoring** - Measurement service simplified to single-path execution (66.6% code reduction)
- 🎉 **Phase 3 Complete** - All 25 instrument drivers implemented (100%)
- ✨ RF Instrument Drivers - CMW100 (R&S), MT8872A (Anritsu) with SDK integration
- ✨ Low Priority Instruments - L6MPU series (3), PEAK CAN, SMCV100B
- ✨ Phase 1 Communication Interfaces - ComPort, TCPIP, Console, Wait
- ✨ Complete Test Coverage - Unit tests for all Phase 3 instruments

**Current Focus**:
- 🔧 TestHistory & SystemConfig frontend pages
- 🔧 Production security hardening
- 🔧 WebSocket real-time communication (replacing polling)
