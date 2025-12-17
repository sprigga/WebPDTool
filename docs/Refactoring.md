# PDTool4 重構計劃 (Refactoring Plan)

## 專案概述 (Project Overview)

本文檔描述了將 PDTool4 從現有的桌面應用程式架構重構為現代化 Web 應用程式的完整計劃。

### 現有架構
- **前端 (Frontend)**: PySide2 桌面應用程式
- **後端 (Backend)**: Python 整合式邏輯
- **資料層 (Data Layer)**: CSV 檔案、INI 配置檔

### 目標架構 (Target Architecture)
- **前端 (Frontend)**: Vue 3 (JavaScript)
- **後端 (Backend)**: FastAPI (Python)
- **資料庫 (Database)**: MySQL
- **反向代理 (Reverse Proxy)**: Nginx

---

## 技術堆疊 (Technology Stack)

### 前端技術 (Frontend Technologies)
- **框架**: Vue 3 (Composition API)
- **語言**: JavaScript
- **UI 框架**: Element Plus / Ant Design Vue / Vuetify
- **狀態管理**: Pinia
- **HTTP 客戶端**: Axios
- **路由**: Vue Router
- **建置工具**: Vite

### 後端技術 (Backend Technologies)
- **框架**: FastAPI
- **語言**: Python 3.9+
- **ORM**: SQLAlchemy
- **資料驗證**: Pydantic
- **非同步支援**: asyncio, async/await
- **API 文檔**: Swagger UI (自動生成)
- **認證**: JWT (JSON Web Tokens)

### 資料庫 (Database)
- **主資料庫**: MySQL 8.0+
- **連線池**: SQLAlchemy connection pool
- **遷移工具**: Alembic

### 反向代理 (Reverse Proxy)
- **伺服器**: Nginx
- **功能**:
  - 靜態檔案服務
  - API 請求轉發
  - SSL/TLS 終止
  - 負載平衡 (未來擴展)

---

## 系統架構設計 (System Architecture Design)

### 整體架構圖 (High-Level Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                         用戶端 (Client)                       │
│                      瀏覽器 (Web Browser)                      │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (反向代理)                          │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │  靜態檔案     │    │  API 代理     │                       │
│  │  (Vue App)   │    │  (/api/*)    │                       │
│  └──────────────┘    └──────────────┘                       │
└──────────┬────────────────────┬─────────────────────────────┘
           │                    │
           ↓                    ↓
┌──────────────────┐  ┌──────────────────────────────────────┐
│   靜態檔案        │  │      FastAPI 後端伺服器                │
│   (Vue 3 SPA)    │  │  ┌────────────────────────────┐      │
└──────────────────┘  │  │      API 路由層             │      │
                      │  │  (Authentication, Tests,    │      │
                      │  │   Results, Config, etc.)    │      │
                      │  └────────────┬───────────────┘      │
                      │               ↓                       │
                      │  ┌────────────────────────────┐      │
                      │  │      業務邏輯層             │      │
                      │  │  (Test Engine, SFC,         │      │
                      │  │   Modbus, Instruments)      │      │
                      │  └────────────┬───────────────┘      │
                      │               ↓                       │
                      │  ┌────────────────────────────┐      │
                      │  │      資料訪問層             │      │
                      │  │  (SQLAlchemy ORM)           │      │
                      │  └────────────┬───────────────┘      │
                      └───────────────┼──────────────────────┘
                                      ↓
                      ┌────────────────────────────┐
                      │       MySQL 資料庫          │
                      │  ┌──────────────────────┐  │
                      │  │  Users               │  │
                      │  │  Projects            │  │
                      │  │  Stations            │  │
                      │  │  TestPlans           │  │
                      │  │  TestResults         │  │
                      │  │  Configurations      │  │
                      │  │  SFC_Logs            │  │
                      │  └──────────────────────┘  │
                      └────────────────────────────┘
```

### 分層架構詳細說明 (Layered Architecture Details)

#### 1. 前端層 (Presentation Layer - Vue 3)
- **登入頁面**: 使用者認證、專案/站別選擇
- **測試主頁**: 測試控制、結果顯示、即時狀態
- **配置管理**: 測試計劃、儀器設定、系統參數
- **歷史查詢**: 測試結果查詢、報表生成
- **系統管理**: 使用者管理、權限控制

#### 2. API 層 (API Layer - FastAPI)
- **認證 API**: 登入、登出、權限驗證
- **測試 API**: 測試執行、狀態查詢、結果上傳
- **配置 API**: 讀取/更新測試計劃、系統設定
- **SFC API**: SFC 系統整合介面
- **Modbus API**: Modbus 通訊控制
- **報表 API**: 資料查詢、統計分析

#### 3. 業務邏輯層 (Business Logic Layer)
- **測試引擎**: 測試流程編排、測試項目執行
- **儀器控制**: 儀器初始化、測量執行、結果讀取
- **SFC 整合**: SFC 通訊、資料同步
- **Modbus 服務**: Modbus 監聽、資料交換
- **驗證邏輯**: 資料驗證、結果判定

#### 4. 資料訪問層 (Data Access Layer)
- **ORM 模型**: SQLAlchemy 資料庫模型
- **資料庫操作**: CRUD 操作封裝
- **事務管理**: 資料一致性保證

---

## 資料庫設計 (Database Schema Design)

### 核心資料表 (Core Tables)

#### Users (使用者表)
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('engineer', 'operator', 'admin') NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role)
);
```

#### Projects (專案表)
```sql
CREATE TABLE projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project_code (project_code)
);
```

#### Stations (站別表)
```sql
CREATE TABLE stations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    station_code VARCHAR(50) NOT NULL,
    station_name VARCHAR(100) NOT NULL,
    project_id INT NOT NULL,
    test_plan_path VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_station (project_id, station_code),
    INDEX idx_station_code (station_code)
);
```

#### TestPlans (測試計劃表)
```sql
CREATE TABLE test_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    station_id INT NOT NULL,
    item_no INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    parameters JSON,
    lower_limit DECIMAL(15,6),
    upper_limit DECIMAL(15,6),
    unit VARCHAR(20),
    enabled BOOLEAN DEFAULT TRUE,
    sequence_order INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_station_sequence (station_id, sequence_order)
);
```

#### TestSessions (測試會話表)
```sql
CREATE TABLE test_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    serial_number VARCHAR(100) NOT NULL,
    station_id INT NOT NULL,
    user_id INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    final_result ENUM('PASS', 'FAIL', 'ABORT') NULL,
    total_items INT,
    pass_items INT,
    fail_items INT,
    test_duration_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES stations(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_serial_number (serial_number),
    INDEX idx_station_time (station_id, start_time),
    INDEX idx_result (final_result)
);
```

#### TestResults (測試結果表)
```sql
CREATE TABLE test_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    test_plan_id INT NOT NULL,
    item_no INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    measured_value DECIMAL(15,6),
    lower_limit DECIMAL(15,6),
    upper_limit DECIMAL(15,6),
    unit VARCHAR(20),
    result ENUM('PASS', 'FAIL', 'SKIP', 'ERROR') NOT NULL,
    error_message TEXT,
    test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_duration_ms INT,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (test_plan_id) REFERENCES test_plans(id),
    INDEX idx_session (session_id),
    INDEX idx_result (result),
    INDEX idx_test_time (test_time)
);
```

#### Configurations (系統配置表)
```sql
CREATE TABLE configurations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSON NOT NULL,
    category VARCHAR(50),
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category)
);
```

#### SFC_Logs (SFC 通訊記錄表)
```sql
CREATE TABLE sfc_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    operation VARCHAR(50) NOT NULL,
    request_data JSON,
    response_data JSON,
    status ENUM('SUCCESS', 'FAILED', 'TIMEOUT') NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

#### Modbus_Logs (Modbus 通訊記錄表)
```sql
CREATE TABLE modbus_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    register_address INT NOT NULL,
    operation ENUM('READ', 'WRITE') NOT NULL,
    value VARCHAR(255),
    status ENUM('SUCCESS', 'FAILED') NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
);
```

---

## API 端點設計 (API Endpoints Design)

### 認證模組 (Authentication)
- `POST /api/auth/login` - 使用者登入
- `POST /api/auth/logout` - 使用者登出
- `GET /api/auth/me` - 獲取當前使用者資訊
- `POST /api/auth/refresh` - 刷新 Token

### 專案與站別 (Projects & Stations)
- `GET /api/projects` - 獲取專案列表
- `GET /api/projects/{id}` - 獲取專案詳情
- `GET /api/projects/{id}/stations` - 獲取專案下的站別
- `POST /api/projects` - 創建專案 (管理員)
- `PUT /api/projects/{id}` - 更新專案 (管理員)
- `DELETE /api/projects/{id}` - 刪除專案 (管理員)

### 測試計劃 (Test Plans)
- `GET /api/stations/{id}/testplan` - 獲取站別測試計劃
- `POST /api/stations/{id}/testplan` - 上傳測試計劃
- `PUT /api/testplans/{id}` - 更新測試項目
- `DELETE /api/testplans/{id}` - 刪除測試項目

### 測試執行 (Test Execution)
- `POST /api/tests/sessions` - 創建測試會話
- `POST /api/tests/sessions/{id}/start` - 開始測試
- `POST /api/tests/sessions/{id}/results` - 上傳測試結果
- `POST /api/tests/sessions/{id}/complete` - 完成測試
- `GET /api/tests/sessions/{id}` - 獲取測試會話資訊
- `GET /api/tests/sessions/{id}/status` - 獲取測試狀態

### 測試結果查詢 (Test Results Query)
- `GET /api/results/search` - 搜索測試結果
- `GET /api/results/sessions/{id}` - 獲取會話詳細結果
- `GET /api/results/statistics` - 獲取統計資料
- `GET /api/results/export` - 匯出測試資料

### SFC 整合 (SFC Integration)
- `POST /api/sfc/check-in` - SFC 報到
- `POST /api/sfc/check-out` - SFC 報出
- `POST /api/sfc/upload-data` - 上傳資料到 SFC
- `GET /api/sfc/logs` - 獲取 SFC 記錄

### Modbus 通訊 (Modbus Communication)
- `GET /api/modbus/status` - 獲取 Modbus 狀態
- `POST /api/modbus/start` - 啟動 Modbus 服務
- `POST /api/modbus/stop` - 停止 Modbus 服務
- `GET /api/modbus/registers` - 讀取寄存器
- `POST /api/modbus/registers` - 寫入寄存器

### 系統配置 (System Configuration)
- `GET /api/config` - 獲取系統配置
- `PUT /api/config/{key}` - 更新配置項
- `GET /api/config/instruments` - 獲取儀器配置
- `PUT /api/config/instruments` - 更新儀器配置

---

## 開發階段與模組順序 (Development Phases & Module Sequence)

### 階段 1: 基礎設施建置 (Infrastructure Setup)
**目標**: 建立開發環境與基礎架構

#### 1.1 開發環境設置
- [ ] 安裝 Node.js、Python 3.9+、MySQL 8.0
- [ ] 配置 Git 版本控制
- [ ] 建立專案目錄結構

#### 1.2 資料庫建置
- [ ] 安裝並配置 MySQL
- [ ] 執行資料庫 Schema 創建腳本
- [ ] 建立測試資料庫
- [ ] 配置 Alembic 遷移工具

#### 1.3 後端專案初始化
- [ ] 建立 FastAPI 專案結構
- [ ] 配置虛擬環境 (使用 uv)
- [ ] 安裝核心依賴套件
- [ ] 建立基本配置檔案

#### 1.4 前端專案初始化
- [ ] 使用 Vite 建立 Vue 3 專案
- [ ] 安裝 UI 框架和依賴
- [ ] 配置路由和狀態管理
- [ ] 建立基本專案結構

**交付成果**:
- 完整的開發環境
- 可運行的資料庫
- 空白但可啟動的前後端專案

---

### 階段 2: 核心認證系統 (Core Authentication)
**目標**: 實現使用者認證與授權機制

#### 2.1 後端認證模組
- [ ] 設計並實現 User 資料模型
- [ ] 實現密碼加密與驗證
- [ ] 實現 JWT Token 生成與驗證
- [ ] 建立登入/登出 API
- [ ] 實現權限中介軟體

#### 2.2 前端登入介面
- [ ] 設計登入頁面 UI
- [ ] 實現登入表單驗證
- [ ] 整合登入 API
- [ ] 實現 Token 存儲與管理
- [ ] 實現路由守衛

**測試重點**:
- 登入功能驗證
- Token 有效性測試
- 權限檢查測試

**交付成果**:
- 完整的認證系統
- 可登入的 Web 應用

---

### 階段 3: 專案與站別管理 (Project & Station Management)
**目標**: 實現專案和站別的管理功能

#### 3.1 後端資料模型與 API
- [ ] 建立 Projects 和 Stations 資料模型
- [ ] 實現專案 CRUD API
- [ ] 實現站別 CRUD API
- [ ] 建立專案與站別關聯邏輯

#### 3.2 前端管理介面
- [ ] 設計專案列表頁面
- [ ] 設計站別選擇介面
- [ ] 實現專案/站別新增編輯功能
- [ ] 整合後端 API

**測試重點**:
- 專案與站別 CRUD 操作
- 資料關聯正確性

**交付成果**:
- 專案與站別管理功能
- 使用者可選擇專案和站別

---

### 階段 4: 測試計劃管理 (Test Plan Management)
**目標**: 實現測試計劃的上傳、顯示與編輯

#### 4.1 後端測試計劃模組
- [ ] 建立 TestPlans 資料模型
- [ ] 實現 CSV 檔案解析功能
- [ ] 實現測試計劃上傳 API
- [ ] 實現測試計劃查詢 API
- [ ] 實現測試項目編輯 API

#### 4.2 前端測試計劃介面
- [ ] 設計測試計劃上傳介面
- [ ] 設計測試項目列表顯示
- [ ] 實現測試項目編輯功能
- [ ] 實現測試計劃預覽功能

**測試重點**:
- CSV 檔案解析正確性
- 測試計劃儲存與讀取
- 測試項目參數驗證

**交付成果**:
- 測試計劃管理功能
- 可上傳和編輯測試計劃

---

### 階段 5: 測試執行引擎 (Test Execution Engine)
**目標**: 實現核心測試執行邏輯

#### 5.1 後端測試引擎
- [ ] 建立測試會話管理
- [ ] 實現測試流程編排器
- [ ] 移植測量模組 (Measurement Modules)
- [ ] 實現儀器控制抽象層
- [ ] 建立測試結果收集器

#### 5.2 測試執行 API
- [ ] 實現測試會話創建 API
- [ ] 實現測試啟動 API
- [ ] 實現測試狀態查詢 API
- [ ] 實現測試結果上傳 API
- [ ] 實現測試完成 API

#### 5.3 前端測試執行介面
- [ ] 設計測試主畫面
- [ ] 實現序號輸入功能
- [ ] 實現測試啟動控制
- [ ] 實現即時狀態顯示
- [ ] 實現測試結果表格顯示

**測試重點**:
- 測試流程正確性
- 測試結果準確性
- 儀器通訊穩定性

**交付成果**:
- 完整的測試執行系統
- 可執行基本測試流程

---

### 階段 6: Modbus 整合 (Modbus Integration)
**目標**: 實現 Modbus TCP/IP 通訊功能

#### 6.1 後端 Modbus 服務
- [ ] 移植 Modbus 監聽模組
- [ ] 實現 Modbus 服務控制
- [ ] 建立寄存器映射邏輯
- [ ] 實現自動測試觸發
- [ ] 建立 Modbus 日誌記錄

#### 6.2 Modbus API 與前端整合
- [ ] 實現 Modbus 控制 API
- [ ] 建立前端 Modbus 狀態監控
- [ ] 實現 Modbus 參數配置介面

**測試重點**:
- Modbus 連線穩定性
- 寄存器讀寫正確性
- 自動觸發功能驗證

**交付成果**:
- Modbus 通訊功能
- 可透過 Modbus 觸發測試

---

### 階段 7: SFC 系統整合 (SFC Integration)
**目標**: 實現與 SFC 系統的整合

#### 7.1 後端 SFC 模組
- [ ] 移植 SFC 通訊模組
- [ ] 實現 SFC 報到/報出邏輯
- [ ] 實現資料上傳功能
- [ ] 建立 SFC 日誌記錄
- [ ] 實現錯誤處理與重試機制

#### 7.2 SFC API 與前端整合
- [ ] 實現 SFC 操作 API
- [ ] 建立前端 SFC 狀態顯示
- [ ] 實現 SFC 配置介面
- [ ] 實現 SFC 日誌查詢介面

**測試重點**:
- SFC 通訊正確性
- 資料上傳完整性
- 錯誤處理機制驗證

**交付成果**:
- SFC 整合功能
- 可與 SFC 系統通訊

---

### 階段 8: 測試結果查詢與報表 (Results Query & Reporting)
**目標**: 實現測試結果查詢和統計報表

#### 8.1 後端查詢模組
- [ ] 實現進階搜索功能
- [ ] 實現統計分析功能
- [ ] 實現資料匯出功能 (CSV, Excel)
- [ ] 建立資料快取機制

#### 8.2 前端查詢介面
- [ ] 設計搜索條件介面
- [ ] 實現結果列表顯示
- [ ] 實現詳細結果查看
- [ ] 實現統計圖表顯示
- [ ] 實現資料匯出功能

**測試重點**:
- 查詢效能測試
- 統計資料準確性
- 匯出檔案格式正確性

**交付成果**:
- 測試結果查詢系統
- 統計報表功能

---

### 階段 9: 系統配置管理 (System Configuration)
**目標**: 實現系統配置的 Web 化管理

#### 9.1 後端配置模組
- [ ] 建立配置資料模型
- [ ] 實現配置讀取/更新 API
- [ ] 實現儀器配置管理
- [ ] 實現配置版本控制

#### 9.2 前端配置介面
- [ ] 設計系統配置頁面
- [ ] 實現儀器配置編輯
- [ ] 實現 Modbus 配置介面
- [ ] 實現 SFC 配置介面

**測試重點**:
- 配置修改生效驗證
- 配置版本回滾測試

**交付成果**:
- 完整的配置管理系統
- 無需手動編輯配置檔案

---

### 階段 10: Nginx 部署與優化 (Nginx Deployment & Optimization)
**目標**: 配置 Nginx 並優化系統效能

#### 10.1 Nginx 配置
- [ ] 安裝並配置 Nginx
- [ ] 配置靜態檔案服務
- [ ] 配置 API 反向代理
- [ ] 配置 SSL/TLS 證書
- [ ] 配置 Gzip 壓縮

#### 10.2 效能優化
- [ ] 前端建置優化
- [ ] 後端 API 效能優化
- [ ] 資料庫查詢優化
- [ ] 配置快取策略

#### 10.3 部署自動化
- [ ] 建立部署腳本
- [ ] 配置自動備份
- [ ] 建立監控機制

**測試重點**:
- 負載測試
- 效能基準測試
- 安全性測試

**交付成果**:
- 生產環境部署
- 完整的部署文檔

---

### 階段 11: 測試與文檔 (Testing & Documentation)
**目標**: 完善測試覆蓋與文檔

#### 11.1 測試完善
- [ ] 單元測試 (Backend)
- [ ] 整合測試 (API)
- [ ] E2E 測試 (Frontend)
- [ ] 效能測試
- [ ] 安全性測試

#### 11.2 文檔編寫
- [ ] API 文檔完善 (Swagger)
- [ ] 使用者操作手冊
- [ ] 系統管理員指南
- [ ] 開發者文檔
- [ ] 部署與維護文檔

**交付成果**:
- 完整的測試報告
- 完整的文檔體系

---

### 階段 12: 上線與維護 (Production & Maintenance)
**目標**: 系統上線與持續維護

#### 12.1 上線準備
- [ ] 資料遷移 (CSV → MySQL)
- [ ] 使用者培訓
- [ ] 灰度發布
- [ ] 監控告警配置

#### 12.2 持續維護
- [ ] 問題追蹤與修復
- [ ] 功能迭代
- [ ] 效能監控與優化
- [ ] 安全性更新

**交付成果**:
- 穩定運行的生產系統
- 維護計劃與流程

---

## 專案目錄結構 (Project Directory Structure)

```
WebPDTool/
├── backend/                      # FastAPI 後端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 應用程式入口
│   │   ├── config.py            # 配置管理
│   │   ├── dependencies.py      # 依賴注入
│   │   ├── api/                 # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # 認證 API
│   │   │   ├── projects.py      # 專案管理 API
│   │   │   ├── stations.py      # 站別管理 API
│   │   │   ├── testplans.py     # 測試計劃 API
│   │   │   ├── tests.py         # 測試執行 API
│   │   │   ├── results.py       # 結果查詢 API
│   │   │   ├── sfc.py           # SFC 整合 API
│   │   │   ├── modbus.py        # Modbus API
│   │   │   └── config.py        # 配置 API
│   │   ├── models/              # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── station.py
│   │   │   ├── testplan.py
│   │   │   ├── test_session.py
│   │   │   ├── test_result.py
│   │   │   └── config.py
│   │   ├── schemas/             # Pydantic 模式
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── test.py
│   │   │   └── result.py
│   │   ├── services/            # 業務邏輯
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── test_engine.py
│   │   │   ├── sfc_service.py
│   │   │   ├── modbus_service.py
│   │   │   └── instrument_manager.py
│   │   ├── core/                # 核心功能
│   │   │   ├── __init__.py
│   │   │   ├── database.py      # 資料庫連線
│   │   │   ├── security.py      # 安全相關
│   │   │   └── logging.py       # 日誌配置
│   │   ├── measurements/        # 測量模組 (移植自舊系統)
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── command_test.py
│   │   │   ├── power_read.py
│   │   │   └── ...
│   │   └── utils/               # 工具函數
│   │       ├── __init__.py
│   │       ├── csv_parser.py
│   │       └── validators.py
│   ├── alembic/                 # 資料庫遷移
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/                   # 測試
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   └── test_services/
│   ├── requirements.txt         # Python 依賴
│   ├── pyproject.toml           # uv 配置
│   └── .env.example             # 環境變數範例
│
├── frontend/                    # Vue 3 前端
│   ├── public/                  # 靜態資源
│   │   └── index.html
│   ├── src/
│   │   ├── main.js              # 應用程式入口
│   │   ├── App.vue              # 根組件
│   │   ├── router/              # 路由配置
│   │   │   └── index.js
│   │   ├── stores/              # Pinia 狀態管理
│   │   │   ├── auth.js
│   │   │   ├── test.js
│   │   │   └── config.js
│   │   ├── views/               # 頁面組件
│   │   │   ├── Login.vue
│   │   │   ├── TestMain.vue
│   │   │   ├── TestHistory.vue
│   │   │   ├── TestPlanManage.vue
│   │   │   └── SystemConfig.vue
│   │   ├── components/          # 通用組件
│   │   │   ├── TestTable.vue
│   │   │   ├── StatusBar.vue
│   │   │   └── ...
│   │   ├── api/                 # API 呼叫
│   │   │   ├── client.js        # Axios 配置
│   │   │   ├── auth.js
│   │   │   ├── test.js
│   │   │   └── ...
│   │   ├── utils/               # 工具函數
│   │   │   ├── validators.js
│   │   │   └── formatters.js
│   │   └── assets/              # 資源文件
│   │       ├── styles/
│   │       └── images/
│   ├── package.json             # npm 配置
│   ├── vite.config.js           # Vite 配置
│   └── .env.development         # 開發環境變數
│
├── nginx/                       # Nginx 配置
│   ├── nginx.conf               # 主配置
│   ├── sites-available/
│   │   └── pdtool.conf          # 站點配置
│   └── ssl/                     # SSL 證書
│
├── database/                    # 資料庫相關
│   ├── schema.sql               # 資料庫 Schema
│   ├── migrations/              # 手動遷移腳本
│   └── seed_data.sql            # 初始資料
│
├── scripts/                     # 部署與維護腳本
│   ├── deploy.sh                # 部署腳本
│   ├── backup.sh                # 備份腳本
│   └── migrate_data.py          # 資料遷移腳本
│
├── docs/                        # 文檔
│   ├── api/                     # API 文檔
│   ├── user_manual/             # 使用者手冊
│   └── dev_guide/               # 開發指南
│
├── PDTool4/                     # 舊系統 (保留供參考)
│
├── docker-compose.yml           # Docker 編排 (選用)
├── .gitignore
└── README.md
```

---

## 技術實作重點 (Technical Implementation Highlights)

### 1. 前端 Vue 3 最佳實踐
- 使用 Composition API 提升程式碼復用性
- 使用 TypeScript 增強型別安全 (選用)
- 實現響應式設計支援多種螢幕
- 使用 WebSocket 實現即時測試狀態更新
- 實現前端路由守衛保護頁面

### 2. FastAPI 後端最佳實踐
- 使用依賴注入管理資料庫連線
- 實現 async/await 提升並發效能
- 使用 Pydantic 進行資料驗證
- 實現中介軟體處理 CORS、認證
- 使用背景任務處理長時間測試

### 3. 資料庫優化
- 合理使用索引提升查詢效能
- 實現讀寫分離 (進階)
- 使用連線池管理連線
- 定期清理歷史資料
- 實現資料備份策略

### 4. 安全性考量
- 使用 HTTPS 加密傳輸
- 實現 JWT Token 認證
- 密碼使用 bcrypt 加密
- 實現 CSRF 防護
- API 請求頻率限制
- 輸入資料驗證與清理

### 5. 效能優化
- 前端懶加載與程式碼分割
- 實現 API 響應快取
- 資料庫查詢優化
- Nginx Gzip 壓縮
- 靜態資源 CDN (進階)

---

## 風險與挑戰 (Risks & Challenges)

### 技術風險
1. **儀器通訊相容性**: 舊系統的儀器控制邏輯可能難以直接移植
   - **緩解策略**: 保留原有測量模組,逐步重構

2. **即時性要求**: Web 架構可能影響測試即時性
   - **緩解策略**: 使用 WebSocket 和非同步處理

3. **資料遷移**: CSV 資料遷移到 MySQL 可能遺失資訊
   - **緩解策略**: 詳細規劃遷移腳本並充分測試

### 業務風險
1. **使用者習慣改變**: 從桌面應用轉到 Web 需要適應期
   - **緩解策略**: 保持 UI 相似性,提供培訓

2. **生產中斷風險**: 切換系統可能影響生產
   - **緩解策略**: 灰度發布,雙系統並行一段時間

### 時程風險
1. **開發時程延遲**: 低估開發複雜度
   - **緩解策略**: 分階段交付,優先實現核心功能

---

## 成功指標 (Success Criteria)

### 功能指標
- [ ] 所有核心測試功能正常運作
- [ ] SFC 整合成功率 > 99%
- [ ] Modbus 通訊穩定性 > 99.5%
- [ ] 測試結果與舊系統一致性 > 99%

### 效能指標
- [ ] API 響應時間 < 200ms (P95)
- [ ] 頁面載入時間 < 2 秒
- [ ] 系統可用性 > 99.5%
- [ ] 支援並發測試站 ≥ 20

### 使用者體驗
- [ ] 使用者滿意度 > 85%
- [ ] 操作流程簡化 > 30%
- [ ] 培訓時間 < 2 小時

---

## 參考資源 (References)

### 技術文檔
- [Vue 3 官方文檔](https://vuejs.org/)
- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文檔](https://docs.sqlalchemy.org/)
- [Nginx 文檔](https://nginx.org/en/docs/)

### 現有系統文檔
- [PDTool4 架構文檔](./architecture_workflow.md)
- [測量模組文檔](./measurement_modules.md)
- [SFC 整合文檔](./sfc_integration.md)
- [Modbus 通訊文檔](./modbus_communication.md)

---

## 版本歷史 (Version History)

| 版本 | 日期 | 作者 | 說明 |
|------|------|------|------|
| 1.0 | 2025-12-16 | System | 初始版本 |

---

## 附註 (Notes)

1. 本重構計劃應根據實際開發進度調整
2. 各階段可視情況並行開發以加速進度
3. 保持與 PDTool4 舊系統的相容性直到完全遷移
4. 定期回顧並更新本文檔
