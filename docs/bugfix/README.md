# Bug Fix 文檔索引

本目錄包含 WebPDTool 專案的所有已知問題追蹤和解決方案文檔。

## 文檔結構

```
docs/bugfix/
├── README.md                                          # 本文件 - 索引頁
├── ISSUE.md                                          # Issue #1 - 登入 API 500 錯誤
├── ISSUE3.md                                         # Issue #3 - (待補充標題)
├── ISSUE4.md                                         # Issue #4 - (待補充標題)
├── ISSUE5_measurement_init_signature.md              # Issue #5 - 測量初始化簽章錯誤
├── ISSUE6_other_measurement_random_values.md         # Issue #6 - Other 測量返回隨機值
├── ISSUE7_database_schema_mismatch.md                # Issue #7 - 資料庫架構不匹配
├── ISSUE8_wait_msec_parameter_not_passed.md          # Issue #8 - wait_msec 參數未傳遞
├── BUGFIX_INVALID_PARAMETERS.md                      # 無效參數修正
├── ISSUE_script_not_found_fix.md                     # 腳本找不到問題修正
├── circular-import-fix.md                            # 循環導入問題修正
├── docker-desktop-wsl2-db-connection-fix.md          # Docker Desktop WSL2 資料庫連線修正
├── dynamic-parameter-form-incomplete-templates-fix.md # 動態參數表單模板不完整修正
├── dynamic-parameter-form-no-display-fix.md          # 動態參數表單不顯示修正
├── migration_fix_20260209.md                         # 2026-02-09 遷移修正
└── wait-msec-parameter-fix.md                        # wait_msec 參數修正（詳細指南）
```

## 問題分類

### 🔴 關鍵問題（Critical）

影響系統核心功能或導致服務無法使用的問題。

| 問題編號 | 標題 | 狀態 | 日期 | 文檔 |
|---------|------|------|------|------|
| Issue #1 | 登入 API 返回 500 錯誤（bcrypt 密碼驗證） | ✅ 已修正 | 2025-12-17 | [ISSUE.md](./ISSUE.md) |
| Issue #7 | 資料庫架構不匹配 | ✅ 已修正 | 2026-02-09 | [ISSUE7_database_schema_mismatch.md](./ISSUE7_database_schema_mismatch.md) |

### 🟡 重要問題（High）

影響主要功能但有暫時解決方案的問題。

| 問題編號 | 標題 | 狀態 | 日期 | 文檔 |
|---------|------|------|------|------|
| Issue #5 | 測量初始化簽章錯誤 | ✅ 已修正 | - | [ISSUE5_measurement_init_signature.md](./ISSUE5_measurement_init_signature.md) |
| Issue #6 | Other 測量類型返回隨機值而非執行腳本 | ✅ 已修正 | - | [ISSUE6_other_measurement_random_values.md](./ISSUE6_other_measurement_random_values.md) |
| Issue #8 | wait_msec 參數未正確傳遞到後端 | ✅ 已修正 | 2026-02-10 | [ISSUE8_wait_msec_parameter_not_passed.md](./ISSUE8_wait_msec_parameter_not_passed.md) |
| Issue #9 | console/comport/tcpip 測量執行鏈多重錯誤 | ✅ 已修正 | 2026-02-24 | [ISSUE9_console_comport_tcpip_measurement_chain.md](./ISSUE9_console_comport_tcpip_measurement_chain.md) |

### 🟢 一般問題（Medium）

影響部分功能但不阻礙主要工作流程的問題。

| 問題編號 | 標題 | 狀態 | 日期 | 文檔 |
|---------|------|------|------|------|
| - | 循環導入問題 | ✅ 已修正 | - | [circular-import-fix.md](./circular-import-fix.md) |
| - | 動態參數表單不顯示 | ✅ 已修正 | - | [dynamic-parameter-form-no-display-fix.md](./dynamic-parameter-form-no-display-fix.md) |
| - | 動態參數表單模板不完整 | ✅ 已修正 | - | [dynamic-parameter-form-incomplete-templates-fix.md](./dynamic-parameter-form-incomplete-templates-fix.md) |
| - | 腳本檔案找不到 | ✅ 已修正 | - | [ISSUE_script_not_found_fix.md](./ISSUE_script_not_found_fix.md) |

### ⚙️ 環境配置問題

與開發環境或部署環境相關的問題。

| 問題編號 | 標題 | 狀態 | 日期 | 文檔 |
|---------|------|------|------|------|
| - | Docker Desktop WSL2 資料庫連線問題 | ✅ 已修正 | - | [docker-desktop-wsl2-db-connection-fix.md](./docker-desktop-wsl2-db-connection-fix.md) |
| - | 資料庫遷移問題 | ✅ 已修正 | 2026-02-09 | [migration_fix_20260209.md](./migration_fix_20260209.md) |

### 📝 資料驗證問題

與參數驗證或資料格式相關的問題。

| 問題編號 | 標題 | 狀態 | 日期 | 文檔 |
|---------|------|------|------|------|
| - | 無效參數錯誤 | ✅ 已修正 | - | [BUGFIX_INVALID_PARAMETERS.md](./BUGFIX_INVALID_PARAMETERS.md) |

## 最近修正的問題

### 2026-02-24
- **Issue #9**: console/comport/tcpip 測量類型執行鏈多重修正
  - 修正 `executeSingleItem()` specialTypes 覆寫問題（→ OtherMeasurement）
  - 修正 smcv100b.py 預存在縮排 SyntaxError
  - 修正 `measurement_service.py` 未設定 `"parameters"` key 導致 `self.test_params = {}`
  - 新增 console_1/comport_1/tcpip_1 虛擬儀器至 `_load_default_config()`（type="LOCAL"）
  - 修正三個 Measurement 類別的字串型 `measured_value` 丟棄 bug
  - 修正前端非數值 `measured_value` 觸發 DB DECIMAL 欄位 500 錯誤

### 2026-02-10
- **Issue #8**: wait_msec 參數未正確傳遞到後端
  - 修正動態參數表單的值無法傳遞到測試執行 API
  - 增加後端型別轉換邏輯（字串 → 數字）
  - 改進錯誤訊息格式

### 2026-02-09
- **Issue #7**: 資料庫架構不匹配
- 資料庫遷移修正

## 常見問題類型

### 1. 參數傳遞問題

**典型症狀:**
- 前端設定的參數後端收不到
- 參數驗證失敗但值看起來正確
- 測試執行時報錯 "Missing required parameter"

**相關文檔:**
- [ISSUE8_wait_msec_parameter_not_passed.md](./ISSUE8_wait_msec_parameter_not_passed.md)
- [BUGFIX_INVALID_PARAMETERS.md](./BUGFIX_INVALID_PARAMETERS.md)

### 2. 測量執行問題

**典型症狀:**
- 測量類型返回錯誤結果
- 腳本無法執行
- 儀器初始化失敗

**相關文檔:**
- [ISSUE5_measurement_init_signature.md](./ISSUE5_measurement_init_signature.md)
- [ISSUE6_other_measurement_random_values.md](./ISSUE6_other_measurement_random_values.md)
- [ISSUE_script_not_found_fix.md](./ISSUE_script_not_found_fix.md)

### 3. UI 元件問題

**典型症狀:**
- 表單不顯示
- 參數欄位缺失
- 選項清單為空

**相關文檔:**
- [dynamic-parameter-form-no-display-fix.md](./dynamic-parameter-form-no-display-fix.md)
- [dynamic-parameter-form-incomplete-templates-fix.md](./dynamic-parameter-form-incomplete-templates-fix.md)

### 4. 環境配置問題

**典型症狀:**
- Docker 容器無法啟動
- 資料庫連線失敗
- 依賴套件衝突

**相關文檔:**
- [docker-desktop-wsl2-db-connection-fix.md](./docker-desktop-wsl2-db-connection-fix.md)
- [circular-import-fix.md](./circular-import-fix.md)

## 如何使用這些文檔

### 遇到問題時

1. **搜尋關鍵字**: 使用錯誤訊息或症狀在本頁面搜尋
2. **查看分類**: 根據問題類型找到相關分類
3. **閱讀詳細文檔**: 點擊連結查看完整的問題分析和解決方案
4. **按照步驟修正**: 依照文檔中的步驟進行修正
5. **驗證修正**: 執行文檔中的測試步驟確認問題已解決

### 記錄新問題時

1. **創建新文檔**: 使用格式 `ISSUE{N}_{簡短描述}.md`
2. **參考現有格式**: 參考 [ISSUE8_wait_msec_parameter_not_passed.md](./ISSUE8_wait_msec_parameter_not_passed.md) 的結構
3. **包含必要章節**:
   - 問題描述
   - 根本原因
   - 解決方案
   - 測試驗證
   - 影響範圍
4. **更新本索引**: 在本文件中新增問題條目
5. **提交到版本控制**: 使用描述性的 commit message

## 文檔撰寫指南

### 標準章節結構

```markdown
# 問題追蹤和解決方案文檔

## Issue #N: 問題標題

### 問題描述
**錯誤日期**: YYYY-MM-DD
**錯誤類型**: Error Type
**發生位置**: 程式碼位置

### 根本原因
詳細分析問題產生的原因...

### 完整錯誤堆棧
錯誤訊息和堆棧資訊...

### 解決方案
#### 方案概述
#### 修改的文件
#### 測試驗證

### 影響範圍
### 部署步驟
### 預防措施
### 相關文件
### 變更歷史
```

### 撰寫原則

1. **清晰性**: 使用簡單明瞭的語言
2. **完整性**: 包含足夠的上下文和細節
3. **可操作性**: 提供明確的修正步驟
4. **可追溯性**: 記錄修正歷史和相關文件

## 統計資訊

- **總問題數**: 15+
- **已修正問題**: 15+
- **進行中問題**: 0
- **未解決問題**: 0

最後更新: 2026-02-24

## 聯絡資訊

如果您在使用這些文檔時遇到問題，或發現新的 bug，請：

1. 檢查現有文檔是否已記錄類似問題
2. 如果是新問題，創建新的 ISSUE 文檔
3. 更新本索引文件
4. 提交 Pull Request

## 相關資源

### 內部文檔
- [系統架構文檔](../architecture/)
- [API 文檔](../api/)
- [開發指南](../development/)

### 外部資源
- [WebPDTool GitHub Repository](https://github.com/your-org/webpdtool)
- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [Vue.js 文檔](https://vuejs.org/)
- [Element Plus 文檔](https://element-plus.org/)

## 版本資訊

| 版本 | 日期 | 變更內容 |
|------|------|---------|
| 1.0 | 2026-02-10 | 初始版本，整理所有 bug fix 文檔 |
| 1.1 | 2026-02-10 | 新增 Issue #8 (wait_msec 參數問題) |
