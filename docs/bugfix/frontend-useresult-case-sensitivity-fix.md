# 前端 UseResult 大小寫兼容性修復

## 問題描述

前端檢查 `testParams.UseResult` (大寫)，但資料庫欄位是 `use_result` (小寫)，導致 `use_result` 機制無法觸發。

### 問題分析

**資料庫 Schema**:
```sql
CREATE TABLE test_plans (
  ...
  use_result VARCHAR(100),  -- 小寫
  ...
);
```

**前端代碼** (修正前):
```javascript
// 只檢查大寫 UseResult
if (testParams.UseResult) {
  const useResultValue = testResults.value[testParams.UseResult]
  // ...
}
```

**結果**:
- `testParams.use_result` = `"123_1"` (存在，但被忽略)
- `testParams.UseResult` = `undefined`
- 條件 `testParams.UseResult` 為 `false`，邏輯不執行

## 根本原因

**文件**: `frontend/src/views/TestMain.vue`

### 1. 命名不一致

- **資料庫**: 使用小寫 `use_result`
- **前端代碼**: 使用大寫 `UseResult`
- 這可能來自舊版 PDTool4 的命名習慣

### 2. 單一檢查邏輯

```javascript
// 只檢查大寫
if (testParams.UseResult) { ... }
```

這意味著如果 API 返回小寫 `use_result`，前端完全無法處理。

## 解決方案

**文件**: `frontend/src/views/TestMain.vue` (第 1071-1104 行)

### 修正策略: 雙重檢查 + 優先級

```javascript
// 處理小寫 use_result (資料庫欄位名稱)
if (testParams.use_result) {
  console.log('[DEBUG] 找到小寫 use_result:', testParams.use_result)
  const useResultValue = testResults.value[testParams.use_result]
  if (useResultValue !== undefined) {
    // 標準化和替換邏輯...
    testParams.use_result = normalizedValue
  }
}

// 處理大寫 UseResult (向後兼容舊的命名)
if (testParams.UseResult) {
  console.log('[DEBUG] 找到大寫 UseResult:', testParams.UseResult)
  const useResultValue = testResults.value[testParams.UseResult]
  if (useResultValue !== undefined) {
    // 標準化和替換邏輯...
    testParams.UseResult = normalizedValue
  }
}
```

### 設計原則

1. **優先小寫**: 先處理 `use_result` (當前資料庫標準)
2. **兼容大寫**: 再處理 `UseResult` (舊版兼容)
3. **分別替換**: 兩個欄位都執行獨立的替換邏輯
4. **詳細日誌**: 記錄每一步以便調試

## 效果

### 修正前

```javascript
testParams = {
  use_result: "123_1",  // 被忽略
  UseResult: undefined
}

// if (testParams.UseResult) → false，不執行
```

### 修正後

```javascript
testParams = {
  use_result: "123_1",  // ✓ 被處理
  UseResult: undefined
}

// if (testParams.use_result) → true，執行替換
```

## 驗證

### 場景 1: 小寫 use_result (當前標準)

```javascript
testParams = { use_result: "123_1" }
testResults = { "123_1": "123" }

// 結果
testParams.use_result = "123"  // ✓ 替換成功
```

### 場景 2: 大寫 UseResult (舊版兼容)

```javascript
testParams = { UseResult: "123_1" }
testResults = { "123_1": "123" }

// 結果
testParams.UseResult = "123"  // ✓ 替換成功
```

### 場景 3: 同時存在 (優先小寫)

```javascript
testParams = {
  use_result: "123_1",  // ✓ 先處理
  UseResult: "123_1"    // ✓ 也處理
}

// 結果
testParams.use_result = "123"
testParams.UseResult = "123"
```

## JavaScript 屬性訪問

### 區分大小寫

```javascript
const obj = { use_result: "value1" }

obj.use_result  // "value1" ✓
obj.UseResult   // undefined ✗
```

### 條件判斷

```javascript
const obj = { use_result: "123_1" }

if (obj.use_result) {  // true ✓
  // 執行
}

if (obj.UseResult) {   // false ✗
  // 不執行
}
```

## 相關修復

此修復與以下問題相關:

1. **testResults 雙鍵值存儲** (`test-results-dual-key-storage-fix.md`)
   - 即使檢查正確的欄位，如果 testResults 鍵值不匹配也找不到

2. **後端優先級修復** (`use_result-parameter-priority-fix.md`)
   - 前端替換後，後端需要使用替換值而非資料庫值

3. **數值格式標準化** (`use_result-parameter-priority-fix.md` 中的修正 3)
   - 替換後的值需要標準化格式

## 影響範圍

### 修改的文件
- `frontend/src/views/TestMain.vue` (第 1071-1104 行)

### 影響的測試項目
- 所有使用 `use_result` 機制的測試項目
- 特別是使用小寫 `use_result` 的測試

### 向後兼容性

✅ 完全向後兼容
- 支持小寫 `use_result` (新標準)
- 支持大寫 `UseResult` (舊版)
- 兩者可以同時存在並分別處理

## 最佳實踐

### 資料庫欄位命名

✅ **推薦**: 使用小寫 + 下劃線
```sql
use_result VARCHAR(100)
```

❌ **不推薦**: 使用大寫 + 駝峰
```sql
UseResult VARCHAR(100)
```

### 前端代碼處理

✅ **推薦**: 雙重檢查
```javascript
if (testParams.use_result) { /* ... */ }
if (testParams.UseResult) { /* ... */ }
```

❌ **不推薦**: 單一檢查
```javascript
if (testParams.UseResult) { /* ... */ }
```

## 修復日期

2025-02-10

## 修復人員

Claude Code (AI Assistant)
