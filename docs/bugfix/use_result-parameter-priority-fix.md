# use_result 參數優先級錯誤修復

## 問題描述

測試項目 `123_2` 使用 `use_result="123_1"` 時，無法正確獲取 `123_1` 的測量結果作為參數，導致 `measured_value` 為 `None` 而不是預期的 `"456"`。

### 預期行為
```
123_1: 執行 test123.py → 輸出 "123"
123_2: use_result="123_1" → 獲取 "123" 作為參數 → 執行 test123.py "123" → 輸出 "456"
```

### 實際行為
```
123_1: 執行 test123.py → 輸出 "123"
123_2: use_result="123_1" → 獲取 "123_1" (而非 "123") → 執行 test123.py "123_1" → 輸出空值 → measured_value = None
```

## 根本原因

### 1. 後端優先級錯誤

**文件**: `backend/app/measurements/implementations.py`

**問題代碼** (第 107 行):
```python
use_result = self.test_plan_item.get("use_result") or get_param(self.test_params, "use_result", "UseResult")
```

**問題分析**:
- `test_plan_item.get("use_result")` 返回資料庫原始值 `"123_1"` (測項名稱)
- `test_params` 包含前端已替換的值 `"123"` (實際測量值)
- 由於使用 `or` 運算符，當 `test_plan_item.get("use_result")` 返回任何真值（如 `"123_1"`）時，後面的 `test_params` 檢查永遠不會執行
- 結果：前端精心替換的值被完全忽略

### 2. 數值格式問題

**文件**: `backend/app/measurements/implementations.py`

**問題代碼** (第 244 行):
```python
measured_value = float(output)  # "123" → 123.0
```

**問題分析**:
- 腳本輸出 `"123"` (字串)
- 後端使用 `float()` 轉換，得到 `123.0` (浮點數)
- 前端接收到 `123.0`，轉為字串後為 `"123.0"`
- 腳本 `test123.py` 檢查 `sys.argv[1] == '123'`，但收到的是 `"123.0"`，條件不匹配

## 解決方案

### 修正 1: 反轉優先級

**文件**: `backend/app/measurements/implementations.py` (第 107-109 行)

**修正後**:
```python
# 優先使用 test_params (前端替換後的值)，只有當 test_params 沒有時才使用 test_plan_item
use_result = get_param(self.test_params, "use_result", "UseResult") or self.test_plan_item.get("use_result")
timeout = get_param(self.test_params, "timeout", "Timeout") or self.test_plan_item.get("timeout", 5000)
wait_msec = get_param(self.test_params, "wait_msec", "WaitmSec") or self.test_plan_item.get("wait_msec", 0)
```

**說明**:
1. 優先檢查 `test_params`，這是前端已經處理過的值（將 `"123_1"` 替換為實際測量值 `"123"`）
2. 如果 `test_params` 中沒有，則回退到 `test_plan_item`（資料庫原始值）
3. 這樣既支持新的替換機制，也保持向後兼容性

### 修正 2: 保留整數格式

**文件**: `backend/app/measurements/implementations.py` (第 238-250 行)

**修正後**:
```python
# 嘗試轉換為數字，失敗則使用字串
# 修正: 對於整數類型的輸出，保持整數格式而非浮點數
try:
    # 先嘗試解析為整數
    if output.isdigit() or (output.startswith('-') and output[1:].isdigit()):
        measured_value = int(output)
        self.logger.info(f"[DEBUG] Parsed as integer: {measured_value}")
    else:
        # 嘗試解析為浮點數
        measured_value = float(output)
        self.logger.info(f"[DEBUG] Parsed as float: {measured_value}")
except ValueError:
    # 字串結果 (e.g., "Hello World!")
    measured_value = StringType.cast(output)
    self.logger.info(f"[DEBUG] Parsed as string: {measured_value}")
```

**說明**:
1. 對於純數字字串（如 `"123"`），優先解析為 `int` 而非 `float`
2. 對於帶小數點的字串（如 `"123.45"`），解析為 `float`
3. 對於非數字字串，保持為字串
4. 這樣可以避免 `"123"` 變成 `"123.0"`

### 修正 3: 前端數值標準化 (防禦性編程)

**文件**: `frontend/src/views/TestMain.vue` (第 1071-1104 行)

**修正後**:
```javascript
// 處理小寫 use_result (資料庫欄位名稱)
if (testParams.use_result) {
  const useResultValue = testResults.value[testParams.use_result]
  if (useResultValue !== undefined) {
    // 修正: 標準化數值格式，去除 ".0" 後綴以匹配腳本期望
    let normalizedValue = useResultValue
    if (typeof useResultValue === 'string' && /^\d+\.0$/.test(useResultValue)) {
      normalizedValue = useResultValue.replace(/\.0$/, '')
    }
    testParams.use_result = normalizedValue
  }
}
```

**說明**:
1. 使用正則表達式 `/^\d+\.0$/` 檢測整數浮點格式（如 `"123.0"`）
2. 將其轉換為純整數字串（`"123.0"` → `"123"`）
3. 保留真實小數（如 `"123.45"` 不變）
4. 這是防禦性編程，即使後端返回 `"123.0"`，前端也能正確處理

## 驗證步驟

### 1. 檢查前端日誌

執行測試後，瀏覽器 Console 應顯示:

```
[DEBUG] testParams.use_result (原始): 123_1
[DEBUG] 從 testResults 查找: 123_1 → 123
[DEBUG] 標準化數值: 123 → 123
[DEBUG] 替換後 use_result: 123
```

### 2. 檢查後端日誌

後端日誌應顯示:

```
[DEBUG] use_result from test_plan_item (原始值): 123_1
[DEBUG] use_result from test_params (前端替換值): 123
[DEBUG] Final use_result value: 123
[DEBUG] Parsed as integer: 123
```

### 3. 檢查測試結果

```
項目 123_1: PASS (measured_value: "123")
項目 123_2: PASS (measured_value: "456")
```

## 影響範圍

### 修改的文件
1. `backend/app/measurements/implementations.py` - 後端測量實現
2. `frontend/src/views/TestMain.vue` - 前端測試執行邏輯

### 影響的測試項目
- 所有使用 `use_result` 機制的測試項目
- 特別是依賴其他測項結果作為輸入參數的測試

### 向後兼容性
✅ 完全向後兼容
- 如果前端不發送 `test_params.use_result`，後端會使用資料庫的 `test_plan_item.use_result`
- 新的優先級邏輯只是改變了檢查順序，不影響現有功能

## 相關文檔

- `docs/fix-use-result-mechanism.md` - use_result 機制問題分析
- `docs/use_result_debug_guide.md` - use_result 調試指南
- `docs/fix-measured-value-database-error.md` - 測量值資料庫錯誤分析

## 修復日期

2025-02-10

## 修復人員

Claude Code (AI Assistant)
