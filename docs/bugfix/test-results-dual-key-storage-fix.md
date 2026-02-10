# testResults 雙鍵值存儲機制修復

## 問題描述

前端 `testResults` 字典使用 `item_no` (數字) 作為鍵，但 `use_result` 欄位存儲的是 `item_name` (字串)，導致查找失敗。

### 問題場景

```javascript
// 存儲時使用 item_no (數字)
testResults.value[2] = "123"

// 查找時使用 item_name (字串)
const value = testResults.value["123_1"]  // undefined - 找不到!
```

## 根本原因

**文件**: `frontend/src/views/TestMain.vue` (第 864-876 行)

**原始代碼**:
```javascript
// Store result for dependency usage (UseResult機制)
if (result.measured_value !== null) {
  testResults.value[item.item_no] = String(result.measured_value)
}
```

**問題分析**:
1. 存儲時只使用 `item.item_no` (如 `2`) 作為鍵
2. `use_result` 欄位可能存儲 `item_name` (如 `"123_1"`) 或 `item_no` (如 `2`)
3. 當 `use_result="123_1"` 時，查找 `testResults.value["123_1"]` 返回 `undefined`
4. 即使後端優先級正確，前端也無法找到對應的測量結果

## 解決方案

**文件**: `frontend/src/views/TestMain.vue` (第 864-876 行)

**修正後代碼**:
```javascript
// Store result for dependency usage (UseResult機制)
// 修正: 同時用 item_no 和 item_name 作為 key
// 例如: use_result="123_1" (item_name) 或 use_result="2" (item_no)
if (result.measured_value !== null) {
  const measuredValueStr = String(result.measured_value)
  testResults.value[item.item_no] = measuredValueStr        // 用序號作為 key
  testResults.value[item.item_name] = measuredValueStr      // 用名稱作為 key
}
```

## 效果

### 修正前
```javascript
testResults.value = { 2: "123", 3: "1.0" }
// testResults.value["123_1"] → undefined
```

### 修正後
```javascript
testResults.value = { 2: "123", 3: "1.0", "123_1": "123", "WAIT_FIX_5sec": "1.0" }
// testResults.value["123_1"] → "123" ✓
// testResults.value[2] → "123" ✓
```

## 技術細節

### 鍵值類型

| 來源 | 類型 | 示例 |
|------|------|------|
| `item_no` | Number | `2` |
| `item_name` | String | `"123_1"` |

### JavaScript 對象鍵值轉換

```javascript
const obj = {}
obj[2] = "value"      // 鍵: 2 (數字)
obj["2"] = "value"    // 鍵: "2" (字串) - 不同的鍵!

// 訪問時必須匹配類型
obj[2]    // "value" ✓
obj["2"]  // undefined ✗
```

### 雙鍵值存儲的好處

1. **兼容性**: 支持兩種查找方式
   ```javascript
   testResults.value[use_result]  // use_result 可能是數字或字串
   ```

2. **靈活性**: 不需要關心 `use_result` 存儲的是哪種格式
   ```javascript
   // 這兩種都可以工作
   testResults.value["123_1"]  // item_name 查找
   testResults.value[2]         // item_no 查找
   ```

3. **向後兼容**: 現有代碼使用 `item_no` 查找仍然有效

## 驗證

### 前端 Console 日誌

```
[DEBUG] testResults.value: Proxy(Object) {2: '123', 3: '1', 123_1: '123', WAIT_FIX_5sec: '1'}
[DEBUG] testResults keys: ['2', '3', '123_1', 'WAIT_FIX_5sec']
[DEBUG] 從 testResults 查找: 123_1 → 123
```

### 查找測試

```javascript
// 假設 item_no = 2, item_name = "123_1", measured_value = "123"

// 修正前
testResults.value[2]        // "123" ✓
testResults.value["123_1"]  // undefined ✗

// 修正後
testResults.value[2]        // "123" ✓
testResults.value["123_1"]  // "123" ✓
```

## 相關修復

此修復與以下問題相關:

1. **use_result 參數優先級錯誤** (`use_result-parameter-priority-fix.md`)
   - 即使此修復解決了查找問題，如果後端優先級錯誤，替換值仍會被忽略
   - 兩個修復必須同時存在才能完全解決問題

2. **數值格式標準化** (`use_result-parameter-priority-fix.md` 中的修正 3)
   - 解決找到值後的格式問題（`"123.0"` → `"123"`）

## 影響範圍

### 修改的文件
- `frontend/src/views/TestMain.vue` (第 864-876 行)

### 影響的測試項目
- 所有使用 `use_result` 機制的測試項目
- 特別是 `use_result` 使用 `item_name` 格式的測試

### 性能影響
- **最小**: 只是多存儲一個鍵值對
- **內存**: 每個測項結果多佔用一個引用（可忽略不計）

## 向後兼容性

✅ 完全向後兼容
- 現有使用 `item_no` 查找的代碼仍然有效
- 新增 `item_name` 鍵不會覆蓋 `item_no` 鍵

## 修復日期

2025-02-10

## 修復人員

Claude Code (AI Assistant)
