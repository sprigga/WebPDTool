# WebPDTool Documentation

This directory contains comprehensive documentation for the WebPDTool production testing application (refactored from PDTool4).

## 📚 Documentation Structure

```
docs/
├── README.md                    # 本文件
├── index.md                     # PDTool4 應用程式總覽
│
├── analysis/                    # 技術分析報告
├── architecture/                # 系統架構設計
├── bugfix/                      # Bug 修復記錄
├── code_review/                 # 程式碼審查
├── deployment/                  # 部署配置指南
├── features/                    # 功能說明文件
├── guides/                      # 使用指南
├── implementation/              # 實作記錄
├── integration/                 # 系統整合
├── issues/                      # 問題追蹤
├── lowsheen_lib/               # 儀器驅動分析
├── Measurement/                 # 測量模組文件
├── plans/                       # 開發計劃
├── Polish/                      # PDTool4 Polish 版本分析
├── prompt/                      # 提示詞模板
├── refactoring/                 # 重構記錄
│   └── field-merging/          # 欄位合併重構
└── testplan/                    # 測試計劃相關
```

## 🚀 Quick Start

### For New Users
1. [deployment/Docker部署指南.md](./deployment/Docker部署指南.md) - 系統部署
2. [guides/quick_reference.md](./guides/quick_reference.md) - 快速參考
3. [guides/README_import_testplan.md](./guides/README_import_testplan.md) - 測試計劃匯入

### For Developers
1. [architecture/ARCHITECTURE_INDEX.md](./architecture/ARCHITECTURE_INDEX.md) - 系統架構
2. [guides/api_testing_examples.md](./guides/api_testing_examples.md) - API 測試
3. [refactoring/REFACTORING_SUMMARY.md](./refactoring/REFACTORING_SUMMARY.md) - 重構總結

## 📂 Major Categories

### 🏗️ System Architecture
- [architecture/](./architecture/) - 系統架構、模組關係、資料流程
- [index.md](./index.md) - PDTool4 應用程式總覽

### 🔧 Features & Configuration
- [features/](./features/) - 功能說明與架構
- [deployment/](./deployment/) - 部署與配置指南
- [guides/](./guides/) - 使用指南與最佳實踐

### 🔬 Measurement & Testing
- [Measurement/](./Measurement/) - 測量模組架構與實作
- [lowsheen_lib/](./lowsheen_lib/) - PDTool4 儀器驅動分析
- [testplan/](./testplan/) - 測試計劃格式與工具

### 🔌 Integration
- [integration/](./integration/) - 外部系統整合 (SFC, Modbus)

### 🛠️ Development & Maintenance
- [analysis/](./analysis/) - 技術分析與診斷報告
- [refactoring/](./refactoring/) - 重構計劃與執行記錄
- [implementation/](./implementation/) - 功能實作記錄
- [bugfix/](./bugfix/) - Bug 修復記錄
- [code_review/](./code_review/) - 程式碼審查記錄
- [issues/](./issues/) - 問題追蹤

### 📋 Planning & Research
- [plans/](./plans/) - 開發計劃與設計文件
- [Polish/](./Polish/) - PDTool4 Polish 版本程式碼分析

## 📝 Recent Updates (2026-02-10)

### Analysis & Refactoring
- ✅ [analysis/field-usage-analysis.md](./analysis/field-usage-analysis.md) - execute_name/case_type 欄位使用分析
- ✅ [refactoring/field-merging/merge-case-type-to-switch-mode.md](./refactoring/field-merging/merge-case-type-to-switch-mode.md) - 欄位合併實施報告
- ✅ 統一使用 switch_mode 欄位,簡化前後端邏輯

## 📖 Documentation Guidelines

### File Naming
- 使用小寫字母和連字符: `feature-name.md`
- 日期格式: `YYYY-MM-DD-description.md`

### Structure
1. 標題和日期
2. 問題/目標描述
3. 解決方案/實作
4. 測試驗證
5. 結論

## About PDTool4

PDTool4 is a comprehensive production testing application built with PySide2 for testing power delivery devices. It provides a GUI interface for operators to run various tests on devices under test (DUT) and integrates with Shop Floor Control (SFC) systems for production tracking and process control.