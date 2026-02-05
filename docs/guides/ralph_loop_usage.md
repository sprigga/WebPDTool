# Ralph Loop 使用指南

## 概述

Ralph Loop 是 Claude Code 中的一個自動化迭代執行技能（skill），它能夠自主地完成複雜的多步驟任務。Ralph 會分析任務、制定計劃、執行步驟，並根據結果自我調整，直到任務完成。

## 基本用法

### 語法

```bash
/ralph-loop <任務描述>
```

### 選項參數

- `--max-iterations N` - 限制最大迭代次數（預設通常為 10-15 次）

## 使用範例

### 1. 功能開發

```bash
/ralph-loop Build a REST API for user management with CRUD operations
```

```bash
/ralph-loop 為測試計劃管理添加批量匯入功能，支援多個 CSV 檔案同時上傳
```

### 2. Bug 修復

```bash
/ralph-loop Fix the authentication timeout issue in the login flow
```

```bash
/ralph-loop 修復測試執行過程中的記憶體洩漏問題，當運行超過 100 個測試項目時系統變慢
```

### 3. 程式碼重構

```bash
/ralph-loop Refactor the measurement service to use dependency injection
```

```bash
/ralph-loop 重構前端測試執行介面，將 TestMain.vue 拆分為更小的可重用元件
```

### 4. 錯誤處理增強

```bash
/ralph-loop Add comprehensive error handling to the test engine --max-iterations 20
```

```bash
/ralph-loop 為所有儀器驅動實作添加完整的錯誤處理和重試機制
```

## Ralph Loop 工作流程

```
1. 任務分析
   ├─ 理解任務需求
   ├─ 分析相關程式碼
   └─ 制定執行計劃

2. 迭代執行
   ├─ 執行單一步驟
   ├─ 驗證結果
   ├─ 根據反饋調整
   └─ 繼續下一步驟

3. 自我修正
   ├─ 檢測失敗
   ├─ 分析原因
   └─ 調整策略

4. 完成檢查
   ├─ 驗證所有目標
   ├─ 執行測試
   └─ 產生總結
```

## 何時使用 Ralph Loop

### ✅ 適合使用的情境

1. **多檔案重構任務**
   - 需要同時修改多個相關檔案
   - 涉及資料庫 schema、API 路由、前端元件的連動修改
   - 範例：將同步 API 轉換為非同步實作

2. **複雜功能開發**
   - 功能涉及前後端多個層級
   - 需要建立新的資料模型、API 端點、UI 元件
   - 範例：實作測試報告匯出功能（PDF/Excel）

3. **需要探索的除錯任務**
   - 問題原因不明確，需要逐步調查
   - 涉及多個模組之間的互動
   - 範例：找出並修復測試執行中的資料競爭問題

4. **架構層級的改進**
   - 需要評估多種實作方案
   - 涉及系統多個部分的協調變更
   - 範例：將儀器管理從單例模式改為連接池模式

### ❌ 不需要使用的情境

1. **簡單的單檔案編輯**
   - 只需要修改一個檔案的幾行程式碼
   - 範例：修正拼寫錯誤、調整 CSS 樣式

2. **明確的快速修復**
   - 解決方案很明顯，不需要探索
   - 範例：更新已知的錯誤 API 端點路徑

3. **需要逐步監督的任務**
   - 每一步都需要人工審查和決策
   - 範例：敏感的資料庫遷移操作

## WebPDTool 專案的實際應用範例

### 範例 1：實作新的量測類型

```bash
/ralph-loop 實作一個新的量測類型 'TemperatureMeasurement'，包含：
1. 在 measurements/implementations.py 中建立類別
2. 在 registry.py 中註冊
3. 建立對應的測試案例
4. 更新 API 文件
```

### 範例 2：優化測試執行效能

```bash
/ralph-loop 優化測試執行引擎的效能，目標是減少 30% 的執行時間：
1. 分析目前的效能瓶頸
2. 實作平行測試執行
3. 優化資料庫查詢
4. 添加效能測試驗證改進
--max-iterations 25
```

### 範例 3：實作即時測試狀態更新

```bash
/ralph-loop 將測試執行狀態更新從輪詢改為 WebSocket：
1. 在後端實作 WebSocket 端點
2. 在前端建立 WebSocket 連接管理
3. 更新 TestMain.vue 使用即時更新
4. 處理連線中斷和重連邏輯
5. 添加整合測試
```

### 範例 4：增強錯誤處理

```bash
/ralph-loop 為儀器連線失敗情境添加完整的錯誤處理：
1. 在 InstrumentManager 中添加重試機制
2. 實作指數退避策略
3. 添加詳細的錯誤日誌
4. 在前端顯示友善的錯誤訊息
5. 更新相關文件
--max-iterations 15
```

## 最佳實踐

### 1. 提供清晰的任務描述

**好的描述：**
```bash
/ralph-loop 重構測試計劃匯入功能，支援批量上傳並添加驗證檢查，包括重複檢測和格式驗證
```

**不佳的描述：**
```bash
/ralph-loop 改進匯入功能
```

### 2. 明確列出預期結果

**好的描述：**
```bash
/ralph-loop 實作使用者權限管理功能，包含：
1. 資料庫 schema 更新（roles 和 permissions 表）
2. API 端點（CRUD 操作）
3. 前端管理介面
4. 單元測試和整合測試
```

### 3. 設定合理的迭代限制

- 簡單任務：預設值即可（10-15）
- 中等複雜度：15-20 次迭代
- 高度複雜：20-30 次迭代

### 4. 提供上下文資訊

如果任務涉及特定的檔案或模組，可以在描述中提及：

```bash
/ralph-loop 基於 backend/app/measurements/implementations.py 中的現有模式，
實作一個新的 'NetworkTest' 量測類型，用於測試網路連線和延遲
```

## 監控和中止

### 查看進度

Ralph Loop 執行時會顯示：
- 目前執行的步驟
- 已完成的任務
- 遇到的問題和解決方案

### 中止執行

如果需要中止 Ralph Loop：

```bash
/cancel-ralph
```

或使用標準的中止快捷鍵（通常是 Ctrl+C）。

## 與其他技能的比較

| 技能 | 適用情境 | 互動程度 | 任務複雜度 |
|------|---------|---------|-----------|
| ralph-loop | 自主完成複雜任務 | 低（自動執行） | 高 |
| feature-dev | 引導式功能開發 | 中（需要確認） | 中到高 |
| test-driven-development | TDD 流程開發 | 高（每步確認） | 中 |
| systematic-debugging | 系統化除錯 | 中 | 中 |

## 常見問題

### Q1: Ralph Loop 會自動提交程式碼嗎？

不會。Ralph Loop 只會進行程式碼變更，但不會自動 commit 或 push。完成後你需要自己檢查變更並決定是否提交。

### Q2: 如果 Ralph Loop 卡住了怎麼辦？

可以使用 `/cancel-ralph` 中止執行，然後檢查已完成的部分，調整任務描述後重新執行。

### Q3: Ralph Loop 可以處理需要人工輸入的任務嗎？

不建議。如果任務需要頻繁的人工決策或輸入，使用其他更互動式的技能會更合適。

### Q4: 執行失敗後如何恢復？

Ralph Loop 有自我修正能力，會嘗試從失敗中恢復。如果多次失敗，它會調整策略或尋求協助。

## 進階用法

### 結合其他工具

Ralph Loop 可以與其他開發工具結合使用：

```bash
# 先使用 Ralph Loop 實作功能
/ralph-loop 實作新的測試報告功能

# 完成後使用 code-review 檢查品質
/code-review
```

### 分段執行大型任務

對於特別複雜的任務，可以分解為多個 Ralph Loop 執行：

```bash
# 階段 1：資料庫層
/ralph-loop 為測試報告功能建立資料模型和遷移腳本

# 階段 2：API 層
/ralph-loop 實作測試報告的 API 端點

# 階段 3：前端層
/ralph-loop 建立測試報告的前端介面
```

## 相關文件

- [Code Review Guide](./code_review.md) - 程式碼審查指南
- [Best Practices](./summary_best_practices.md) - 專案最佳實踐
- [Test Plan Import](./README_import_testplan.md) - 測試計劃匯入說明

## 總結

Ralph Loop 是處理複雜、多步驟任務的強大工具。通過提供清晰的任務描述和合理的限制，它可以自主地完成大量工作，讓開發者專注於更高層級的架構決策和業務邏輯。

記住：**任務描述越清晰，Ralph Loop 的執行效果越好。**
