# WebPDTool 架構分析文件索引

**最後更新:** 2026-03-25
**文件數量:** 8 個核心文件
**分析範圍:** 完整架構 + 3 個重構追蹤

---

## 快速導航

| 需求 | 建議閱讀路徑 |
|------|-------------|
| **新開發者入門** | architecture_overview.md → measurement_abstraction_layer.md → frontend_architecture.md |
| **重構工作參考** | field-usage-analysis.md → case-type-code-path-tracing.md → lowsheen_lib_migration_validation_2026_02_24.md |
| **系統理解** | architecture_highlights.md + test_execution_engine.md |
| **API 開發** | frontend_architecture.md (API layer section) + test_execution_engine.md |

---

## 一、架構分析文件

### 1. [architecture_overview.md](./architecture_overview.md)
**創建日期:** 2026-03-10
**文件大小:** ~20KB

**內容涵蓋:**
- 完整專案架構概覽
- 技術堆疊解構 (Vue 3, FastAPI, SQLAlchemy 2.0, MySQL 8.0)
- 關鍵組件與交互說明
- 開發命令與服務埠
- 架構優勢與設計模式

**適用場景:** 新人入門、架構理解、技術選型評估

### 2. [measurement_abstraction_layer.md](./measurement_abstraction_layer.md)
**創建日期:** 2026-03-10
**文件大小:** ~45KB

**內容涵蓋:**
- PDTool4 相容層深入剖析
- BaseMeasurement 抽象類別與三階段生命週期
- 17 個測量實作類別
- 驗證邏輯 (7 種限制類型 + 3 種值類型)
- Registry 系統與擴展模式
- MeasurementService 整合

**適用場景:** 新增測量類型、理解 PDTool4 相容性、調試測試失敗

### 3. [frontend_architecture.md](./frontend_architecture.md)
**創建日期:** 2026-03-10
**文件大小:** ~40KB

**內容涵蓋:**
- Vue 3 Composition API 架構
- Pinia 狀態管理 (auth, project, users)
- Axios API 整合與 JWT 認證
- Vue Router 認證守衛
- 組件架構與可重用性
- 10 個主要視圖及其職責

**適用場景:** 前端開發、API 整合、狀態管理、新增頁面

### 4. [test_execution_engine.md](./test_execution_engine.md)
**創建日期:** 2026-03-10
**文件大小:** ~38KB

**內容涵蓋:**
- TestEngine 單例編排
- MeasurementService 調度
- InstrumentManager 連線池
- runAllTest 模式實作
- 完整執行生命週期
- 並發與 async 模式

**適用場景:** 測試執行調試、理解並發模式、故障排查

### 5. [architecture_highlights.md](./architecture_highlights.md)
**創建日期:** 2026-03-10
**文件大小:** ~12KB

**內容涵蓋:**
- 關鍵架構決策摘要
- 核心優勢與技術選擇
- 資料流圖
- 效能優化
- 安全考量
- 未來增強機會

**適用場景:** 快速架構評估、高層次理解、技術審查

---

## 二、重構分析文件

### 6. [case-type-code-path-tracing.md](./case-type-code-path-tracing.md)
**創建日期:** 2026-02-10
**文件大小:** ~25KB

**分析重點:**
- `case_type` 欄位完整程式碼路徑追蹤
- 遷移至 `switch_mode` 的整合分析
- 14 個檔案、26 處程式碼位置的影響分析
- 向前相容性考量

**基於:** `../refactoring/field-merging/merge-case-type-to-switch-mode.md`

### 7. [lowsheen_lib_migration_validation_2026_02_24.md](./lowsheen_lib_migration_validation_2026_02_24.md)
**創建日期:** 2026-02-24
**文件大小:** ~28KB

**分析重點:**
- `lowsheen_lib/` → `app/measurements/` + `app/services/instruments/` 遷移驗證
- Strangler Fig 模式成功評估
- 15 個腳本的覆蓋率矩陣
- Gap 識別: MDO34 缺少實作、legacy cleanup 路徑仍存在
- 風險評估與嚴重性評級

**基於:** `../code_review/LOWSHEEN_LIB_DEPRECATION_ANALYSIS_2026_02_23.md`

### 8. [field-usage-analysis.md](./field-usage-analysis.md)
**創建日期:** 2026-02-10
**文件大小:** ~8KB

**分析重點:**
- `execute_name` 與 `case_type` 欄位使用分析
- 決策: 隱藏 `execute_name` (僅前端使用)、保留 `case_type` (核心業務邏輯)
- 跨 5 層的資料流追蹤 (CSV → DB → API → Frontend → Backend services)
- 實施建議

---

## 三、文件交叉參考

### 相關性圖

```
field-usage-analysis.md (分析)
        ↓
        ↓ 決定合併 case_type → switch_mode
        ↓
case-type-code-path-tracing.md (追蹤)

lowsheen_lib_migration_validation_2026_02_24.md (驗證)
        ↓
        ↓ 識別 MDO34 gap
        ↓
[待] MDO34 實作分析
```

### 外部相關文件

| 文件 | 位置 | 說明 |
|------|------|------|
| `CLAUDE.md` | `/` | 專案開發指南 |
| `ARCHITECTURE_INDEX.md` | `../architecture/` | 主架構參考索引 (16 個文件) |
| `README.md` | `../lowsheen_lib/` | 儀器驅動文件 |
| `pytest-migration-summary.md` | `../` | 測試框架遷移指南 |
| `merge-case-type-to-switch-mode.md` | `../refactoring/field-merging/` | 重構實施報告 |
| `LOWSHEEN_LIB_DEPRECATION_ANALYSIS_2026_02_23.md` | `../code_review/` | 棄用分析 |

---

## 四、快速參考表

### 欄位使用分析 (case-type-code-path-tracing.md)

| 檔案 | 行數 | 使用次數 | 狀態 |
|------|------|----------|------|
| TestPlanManage.vue | 121, 347-349, 597, 864, 927 | 5 | 🔴 顯示保留，輸入已移除 |
| TestMain.vue | 1006-1008 | 1 | 🔴 向後相容邏輯 |
| test_engine.py | 220-223, 248-249 | 2 | 🟡 向後相容 |
| implementations.py | 71-94 | 1 | 🟡 向後相容 |
| testplan.py (Schema) | 33, 65 | 2 | 🔴 保留 |
| testplan.py (Model) | 39 | 1 | 🔴 保留 |
| measurement_service.py | 458, 467, 594 | 3 | 🟡 註解說明 |
| csv_parser.py | 164 | 1 | 🔴 保留 |
| import_testplan.py | 102, 238 | 2 | 🔴 保留 |

### 遷移覆蓋率 (lowsheen_lib_migration_validation_2026_02_24.md)

| lowsheen_lib 腳本 | 現代驅動 | implementations.py 覆蓋 | 狀態 |
|-------------------|----------|------------------------|------|
| DAQ973A_test.py | daq973a.py | PowerReadMeasurement | ✅ 已遷移 |
| 2303_test.py | model2303.py | PowerRead + PowerSet | ✅ 已遷移 |
| 2306_test.py | model2306.py | PowerRead + PowerSet | ✅ 已遷移 |
| IT6723C.py | it6723c.py | PowerRead + PowerSet | ✅ 已遷移 |
| MDO34.py | mdo34.py | ❌ 無實作 | ⚠️ Gap |
| ComPortCommand.py | comport_command.py | CommandTest stub | ⚠️ 僅 stub |

---

## 五、文檔狀態總結

| 文件 | 狀態 | 審查日期 |
|------|------|----------|
| architecture_overview.md | ✅ 完成 | 2026-03-10 |
| measurement_abstraction_layer.md | ✅ 完成 | 2026-03-10 |
| frontend_architecture.md | ✅ 完成 | 2026-03-10 |
| test_execution_engine.md | ✅ 完成 | 2026-03-10 |
| architecture_highlights.md | ✅ 完成 | 2026-03-10 |
| field-usage-analysis.md | ✅ 完成 | 2026-02-10 |
| case-type-code-path-tracing.md | ✅ 完成 | 2026-02-10 |
| lowsheen_lib_migration_validation_2026_02_24.md | ✅ 完成 | 2026-02-24 |

---

## 六、關鍵發現

### 架構優勢
1. **完整 PDTool4 相容性:** 精確複製遺留行為
2. **現代網頁架構:** Async/await、JWT、Vue 3 Composition API
3. **模組化設計:** 清晰的關注點分離、可擴展組件
4. **強大的錯誤處理:** 全面的故障模式與恢復

### 重構成功
1. **欄位整合:** `case_type` → `switch_mode` 遷移影響最小
2. **函式庫遷移:** `lowsheen_lib/` → async class-based system (70% 完成)
3. **欄位使用:** 清楚區分前端僅用 vs 後端核心欄位
4. **向後相容性:** 所有重構努力均維持向後相容

### 風險管理
1. **Gap 識別:** MDO34 缺少實作、legacy cleanup 路徑
2. **嚴重性評估:** 高/中/低風險分類
3. **向前相容性:** 支援未來遷移與增強
4. **全面覆蓋:** 分析所有 14 個檔案與 26 處程式碼位置

---

## 七、貢獻新分析

新增分析文件時請遵循:

1. **檔名模式:** `topic-date.md` 或 `topic_description.md`
2. **新增條目:** 在此 ARCHITECTURE_INDEX.md 中添加簡短描述
3. **參考相關文件:** 在「相關文件」區段中引用
4. **維持格式:** 一致的 markdown 格式與標題層次
5. **實用範例:** 包含檔案路徑與行號（如適用）
6. **快速參考:** 如適當，添加關鍵發現的快速參考區段

---

**最後更新:** 2026-03-25
**文件版本:** 2.0 (統一版)
**維護者:** WebPDTool 架構團隊
