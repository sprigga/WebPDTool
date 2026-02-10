# Bug Fix Summary: use_result 機制完整修復

## 概述

本次修復解決了 WebPDTool 中 `use_result` 機制無法正常工作的問題。`use_result` 是 PDTool4 的重要功能，允許一個測試項目使用之前測試項目的結果作為輸入參數。

## 問題現象

測試項目 `123_2` 配置了 `use_result="123_1"`，期望：
1. 獲取 `123_1` 的測量結果 `"123"`
2. 將 `"123"` 作為參數傳給腳本
3. 腳本輸出 `"456"`

實際結果：`measured_value = None`

## 根本原因

問題涉及三個層級的錯誤：

### 1. 後端優先級錯誤 (關鍵)
**文件**: `backend/app/measurements/implementations.py`
```python
# 錯誤: 優先使用資料庫值，忽略前端替換值
use_result = self.test_plan_item.get("use_result") or get_param(self.test_params, "use_result", "UseResult")
```

### 2. 前端大小寫不兼容
**文件**: `frontend/src/views/TestMain.vue`
```javascript
// 錯誤: 只檢查大寫，資料庫是小寫
if (testParams.UseResult) { ... }
```

### 3. 字典鍵值不匹配
**文件**: `frontend/src/views/TestMain.vue`
```javascript
// 錯誤: 只用 item_no 存儲，use_result 用 item_name 查找
testResults.value[item.item_no] = measuredValue
```

## 完整修復方案

### 修復 1: 反轉後端優先級

**文件**: `backend/app/measurements/implementations.py`

```python
# 修正: 優先使用前端替換值
use_result = get_param(self.test_params, "use_result", "UseResult") or self.test_plan_item.get("use_result")
```

**效果**: 後端使用前端已替換的實際測量值，而非資料庫中的測項名稱

### 修復 2: 雙重大小寫支持

**文件**: `frontend/src/views/TestMain.vue`

```javascript
// 同時處理小寫和大寫
if (testParams.use_result) { /* 處理小寫 */ }
if (testParams.UseResult) { /* 處理大寫 */ }
```

**效果**: 兼容資料庫小寫欄位和舊版大寫命名

### 修復 3: 雙鍵值存儲

**文件**: `frontend/src/views/TestMain.vue`

```javascript
// 同時用 item_no 和 item_name 存儲
testResults.value[item.item_no] = measuredValueStr
testResults.value[item.item_name] = measuredValueStr
```

**效果**: 支持兩種查找方式，無論 `use_result` 使用哪種格式

### 修復 4: 整數格式保留

**文件**: `backend/app/measurements/implementations.py`

```python
# 優先解析為整數
if output.isdigit():
    measured_value = int(output)  # "123" → 123
else:
    measured_value = float(output)  # "123.45" → 123.45
```

**效果**: 避免 `"123"` 變成 `"123.0"`

### 修復 5: 前端數值標準化

**文件**: `frontend/src/views/TestMain.vue`

```javascript
// 去除整數的 .0 後綴
if (typeof useResultValue === 'string' && /^\d+\.0$/.test(useResultValue)) {
  normalizedValue = useResultValue.replace(/\.0$/, '')
}
```

**效果**: 將 `"123.0"` 轉為 `"123"`，防禦性編程

## 修復後的完整流程

```
1. 123_1 執行
   → test123.py 輸出 "123"
   → 後端解析為 int(123)
   → 前端存儲: testResults[2] = "123", testResults["123_1"] = "123"

2. 123_2 執行
   → API 返回 use_result = "123_1"
   → 前端查找: testResults["123_1"] = "123"
   → 前端標準化: "123" (已是整數格式)
   → 前端替換: testParams.use_result = "123"
   → 發送到後端: test_params = { use_result: "123", ... }

3. 後端處理
   → 優先檢查 test_params.use_result = "123" ✓
   → 構建命令: python3 test123.py "123"
   → 執行腳本，輸出 "456"
   → 測量值: "456" (PASS)
```

## 驗證步驟

### 1. 前端 Console 日誌

```javascript
[DEBUG] testParams.use_result (原始): 123_1
[DEBUG] 從 testResults 查找: 123_1 → 123
[DEBUG] 替換後 use_result: 123
[DEBUG] 最終 testParams.use_result: 123
```

### 2. 後端日誌

```python
[DEBUG] use_result from test_plan_item (原始值): 123_1
[DEBUG] use_result from test_params (前端替換值): 123
[DEBUG] Final use_result value: 123
[DEBUG] Executing command: python3 /path/to/test123.py 123
[DEBUG] Script output: 456
[DEBUG] Parsed as integer: 456
```

### 3. 測試結果

```
123_1: PASS (measured_value: "123")
123_2: PASS (measured_value: "456")
```

## 修改文件清單

| 文件 | 修改內容 | 行數 |
|------|----------|------|
| `backend/app/measurements/implementations.py` | 優先級反轉、整數解析、日誌增強 | ~107-112, ~238-250 |
| `frontend/src/views/TestMain.vue` | 雙重大小寫、雙鍵存儲、數值標準化 | ~864-876, ~1071-1104 |

## 向後兼容性

✅ **完全向後兼容**
- 支持小寫 `use_result` 和大寫 `UseResult`
- 支持數字和字串鍵值查找
- 優先使用前端替換值，回退到資料庫值

## 相關文檔

詳細分析請參考以下文檔:

1. **use_result-parameter-priority-fix.md** - 後端優先級錯誤詳細分析
2. **test-results-dual-key-storage-fix.md** - 雙鍵值存儲機制說明
3. **frontend-useresult-case-sensitivity-fix.md** - 大小寫兼容性修復

## 修復日期

2025-02-10

## 修復人員

Claude Code (AI Assistant)

## 測試狀態

⏳ 待用戶驗證

請執行以下命令測試:
```bash
# 後端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# 前端
cd frontend
npm run dev
```

然後執行測試並檢查 Console 和後端日誌。
