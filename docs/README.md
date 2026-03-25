# WebPDTool Documentation

**最後更新：** 2026-03-25

---

## 快速導航

| 角色 | 推薦閱讀路徑 |
|------|------------|
| **新用戶** | [Docker 部署指南](./deployment/Docker部署指南.md) → [快速參考](./guides/quick_reference.md) → [測試計畫匯入](./guides/README_import_testplan.md) |
| **開發者** | [架構索引](./architecture/ARCHITECTURE_INDEX.md) → [代碼分析](./CODEBASE_ANALYSIS.md) → [API 測試範例](./guides/api_testing_examples.md) |
| **架構師** | [架構索引](./architecture/ARCHITECTURE_INDEX.md) → [完整後端分析](./architecture/backend_complete_analysis.md) → [模組關係](./architecture/backend_module_relationships.md) |

---

## 文件目錄

```
docs/
├── README.md                  # 本文件 - 文件索引
├── CODEBASE_ANALYSIS.md       # 完整代碼庫分析
├── pytest-migration-summary.md # Pytest 遷移總結
│
├── architecture/              # 系統架構
│   ├── ARCHITECTURE_INDEX.md  # 架構文件主索引
│   ├── backend_complete_analysis.md
│   ├── backend_module_relationships.md
│   ├── backend_request_flows.md
│   ├── mermaid_diagrams.md
│   ├── core_application.md
│   ├── architecture_workflow.md
│   └── modbus_architecture.md
│
├── guides/                   # 使用指南
│   ├── quick_reference.md
│   ├── README_import_testplan.md
│   ├── api_testing_examples.md
│   ├── command_field_usage.md
│   ├── measurement_testplan_integration.md
│   ├── INSTRUMENT_QUICK_START.md
│   ├── component-integration-guide.md
│   ├── use_result_debug_guide.md
│   ├── uml_diagram.md
│   ├── code_review.md
│   ├── ralph_loop_usage.md
│   ├── claude-md-and-memory-guide.md
│   └── summary_best_practices.md
│
├── features/                 # 功能說明
│   ├── automatic-report-generation.md
│   ├── report-generation-quickstart.md
│   ├── project-manage.md
│   ├── instrument-management-ui.md
│   ├── test-results-csv-export.md
│   ├── test-session-bulk-delete.md
│   ├── modbus-listener-integration.md
│   ├── modbus-auto-trigger-test.md
│   ├── configuration-architecture.md
│   ├── testplan-parameters-architecture.md
│   ├── dynamic-validation-types.md
│   ├── validation-rules-migration.md
│   ├── instrument-config-database-migration.md
│   ├── alembic-docker-migration-guide.md
│   ├── dynamic-parameter-form-usage.md
│   ├── command-measurement-migration.md
│   ├── console-comport-tcpip-validation.md
│   ├── comport-instrument-field-analysis.md
│   └── mdo34-measurement-implementation.md
│
├── deployment/               # 部署配置
│   ├── Docker部署指南.md
│   └── configuration_setup.md
│
├── integration/              # 系統整合
│   ├── sfc_integration.md
│   └── modbus_communication.md
│
├── Measurement/              # 測量模組
│   ├── measurement_modules.md
│   ├── Measurement_api.md
│   ├── Power_Set_Read_Measurement.md
│   ├── Other_Measurement.md
│   ├── OPjudge_Measurement.md
│   └── OneCSV_Atlas.md
│
├── lowsheen_lib/             # 儀器驅動分析（30+ 檔案）
│   ├── README.md
│   ├── INSTRUMENT_MIGRATION.md
│   └── ... (儀器 API 分析)
│
├── bugfix/                   # Bug 修復記錄（40+ 檔案）
├── refactoring/              # 重構記錄
├── implementation/           # 實作記錄
├── code_review/              # 代碼審查
├── plans/                    # 開發計劃
├── Polish/                   # PDTool4 Polish 版本分析
├── prompt/                   # 提示詞模板
└── testplan/                 # 測試計劃相關
```

---

## 依功能類別索引

### 系統架構

| 文件 | 描述 |
|------|------|
| [架構索引](./architecture/ARCHITECTURE_INDEX.md) | 架構文件主入口 |
| [完整後端分析](./architecture/backend_complete_analysis.md) | 後端架構詳解 |
| [模組依賴關係](./architecture/backend_module_relationships.md) | 模組間依賴 |
| [請求流程](./architecture/backend_request_flows.md) | 請求序列圖 |
| [Modbus 架構](./architecture/modbus_architecture.md) | Modbus TCP 模組 |
| [代碼庫分析](./CODEBASE_ANALYSIS.md) | 完整代碼庫分析 |

### 快速開始

| 文件 | 描述 |
|------|------|
| [Docker 部署指南](./deployment/Docker部署指南.md) | 使用 Docker Compose 部署 |
| [快速參考](./guides/quick_reference.md) | 開發者快速參考手冊 |
| [測試計畫匯入](./guides/README_import_testplan.md) | CSV 測試計畫匯入指南 |
| [API 測試範例](./guides/api_testing_examples.md) | API 端點測試範例 |

### 測試與測量

| 文件 | 描述 |
|------|------|
| [測量模組架構](./Measurement/measurement_modules.md) | 測量抽象層架構 |
| [測試計畫參數架構](./features/testplan-parameters-architecture.md) | 測試計畫參數系統 |
| [測試整合指南](./guides/measurement_testplan_integration.md) | 測試整合指南 |
| [Command 欄位使用](./guides/command_field_usage.md) | Command 欄位說明 |

### 儀器驅動

| 文件 | 描述 |
|------|------|
| [儀器庫說明](./lowsheen_lib/README.md) | PDTool4 儀器驅動庫索引 |
| [儀器遷移指南](./lowsheen_lib/INSTRUMENT_MIGRATION.md) | 儀器驅動遷移指南 |
| [儀器管理 UI](./features/instrument-management-ui.md) | 儀器管理界面 |
| [儀器配置數據庫遷移](./features/instrument-config-database-migration.md) | 配置遷移 |

### 功能實作

| 文件 | 描述 |
|------|------|
| [自動報告生成](./features/automatic-report-generation.md) | 自動報告功能 |
| [專案管理](./features/project-manage.md) | 專案管理功能 |
| [測試結果 CSV 匯出](./features/test-results-csv-export.md) | 結果匯出功能 |
| [批量刪除會話](./features/test-session-bulk-delete.md) | 批量刪除功能 |
| [動態驗證類型](./features/dynamic-validation-types.md) | 動態驗證系統 |

### Modbus 整合

| 文件 | 描述 |
|------|------|
| [Modbus 架構](./architecture/modbus_architecture.md) | Modbus TCP 模組架構 |
| [Modbus 監聽器整合](./features/modbus-listener-integration.md) | 監聽器功能實作 |
| [Modbus 自動觸發測試](./features/modbus-auto-trigger-test.md) | SN 讀取自動觸發（v0.8.0） |

### Bug 修復與重構

| 文件 | 描述 |
|------|------|
| [Bug 修復記錄](./bugfix/) | 40+ 修復記錄 |
| [重構記錄](./refactoring/) | 系統重構歷史 |
| [代碼審查](./code_review/) | 代碼審查記錄 |

---

## 關鍵統計

| 指標 | 數值 |
|------|------|
| 後端代碼 | 24,190+ 行 |
| API 端點 | ~60 個 |
| 數據庫表 | 9 個 |
| 測量類型 | 20+ 種 |
| 儀器驅動 | 23 個 |

---

## 關於 PDTool4

PDTool4 是一個使用 PySide2 構建的綜合生產測試應用程式，用於測試電源傳輸設備。它提供 GUI 介面供操作員執行各種測試，並與 Shop Floor Control (SFC) 系統整合進行生產追蹤和流程控制。

WebPDTool 是 PDTool4 的完整網頁式重構版本，保持相容性的同時現代化架構。
