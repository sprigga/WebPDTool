# 修正 use_result 機制（UseResult 依賴注入）

## 問題描述

測試項目 "123_2" 的測量值為 `None`，而不是預期的 "456"。

錯誤訊息：
```
Partial failed: '456' not in 'None'
```

## 根本原因

### 1. 大小寫不匹配問題

**位置:** `frontend/src/views/TestMain.vue` line 1040

```javascript
// 錯誤: 檢查大寫的 UseResult，但資料庫欄位是小寫的 use_result
if (testParams.UseResult && testResults.value[testParams.UseResult]) {
```

資料庫欄位名稱是 `use_result`（小寫），但前端代碼檢查的是 `UseResult`（大寫），導致依賴注入邏輯完全失效。

### 2. Key 查找不匹配問題

**testResults 儲存邏輯:** 使用 `item.item_no` 作為 key
```javascript
testResults.value[item.item_no] = String(result.measured_value)
// 例如: testResults.value[2] = "123"
```

**use_result 欄位值:** 儲存的是 `item_name`
```
123_2 的 use_result = "123_1" (item_name，不是 item_no)
```

**查找邏輯:**
```javascript
testResults.value[testParams.use_result]
// 查找: testResults.value["123_1"]
// 但實際儲存的 key 是: testResults.value[2]
// 結果: undefined (查找失敗)
```

### 3. 值未替換問題

即使查找成功，前端也沒有將 `use_result` 的值替換為實際的測量結果：

```javascript
// 錯誤邏輯
testParams.use_result = "123_1"  // 項目名稱
// 傳遞給後端 → 後端執行: python test123.py "123_1"
// test123.py 收到 "123_1"，不符合條件，不輸出任何內容
// 結果: measured_value = None
```

正確邏輯應該是：
```javascript
testParams.use_result = "123"  // 123_1 的測量結果
// 傳遞給後端 → 後端執行: python test123.py "123"
// test123.py 收到 "123"，符合條件，輸出 "456"
// 結果: measured_value = "456"
```

### 4. test123.py 腳本邏輯

```python
if len(sys.argv) > 1:
    if sys.argv[1] == '123':
        print('456')
else:
    print('123')
```

- 無參數 → 輸出 "123"
- 參數 = "123" → 輸出 "456"
- 其他參數 → **不輸出任何內容** ← 這就是為什麼 measured_value = None

## 執行流程分析

### 修正前的錯誤流程

```
測試項目 123_1:
  → 執行: python test123.py (無參數)
  → 輸出: "123"
  → testResults.value[2] = "123"  (用 item_no 作為 key)

測試項目 123_2:
  → use_result = "123_1"
  → 檢查: testParams.UseResult (大寫) → undefined (欄位名稱不匹配)
  → 沒有替換值
  → testParams.use_result = "123_1" (原值，未替換)
  → 後端收到: use_result = "123_1"
  → 執行: python test123.py "123_1"
  → test123.py: sys.argv[1] = "123_1" ≠ "123" → 不輸出
  → measured_value = None (空輸出)
  → 驗證: "456" partial in "None" → FAIL
```

### 修正後的正確流程

```
測試項目 123_1:
  → 執行: python test123.py (無參數)
  → 輸出: "123"
  → testResults.value[2] = "123"
  → testResults.value["123_1"] = "123"  (同時用 item_name 作為 key)

測試項目 123_2:
  → use_result = "123_1"
  → 檢查: testParams.use_result (小寫) → 找到
  → 查找: testResults.value["123_1"] → "123" (找到了！)
  → 替換值: testParams.use_result = "123"
  → 後端收到: use_result = "123"
  → 執行: python test123.py "123"
  → test123.py: sys.argv[1] = "123" → 輸出 "456"
  → measured_value = "456"
  → 驗證: "456" partial in "456" → PASS
```

## 解決方案

### 1. 修正前端大小寫和值替換邏輯

**檔案:** `frontend/src/views/TestMain.vue` (line 1039-1045)

```javascript
// 原有程式碼: 只檢查大寫的 UseResult
if (testParams.UseResult && testResults.value[testParams.UseResult]) {
  const useResultValue = testResults.value[testParams.UseResult]
  if (testParams.Command) {
    testParams.Command = testParams.Command + ' ' + useResultValue
  }
}

// 修正後: 支援小寫和大寫，並替換值
// 處理小寫 use_result (資料庫欄位名稱)
if (testParams.use_result && testResults.value[testParams.use_result]) {
  const useResultValue = testResults.value[testParams.use_result]
  // 將 use_result 的值替換為實際的測量結果
  testParams.use_result = useResultValue

  // 如果有 Command 欄位，也附加結果值 (PDTool4 兼容)
  if (testParams.Command) {
    testParams.Command = testParams.Command + ' ' + useResultValue
  }
}

// 處理大寫 UseResult (向後兼容舊的命名)
if (testParams.UseResult && testResults.value[testParams.UseResult]) {
  const useResultValue = testResults.value[testParams.UseResult]
  testParams.UseResult = useResultValue

  if (testParams.Command) {
    testParams.Command = testParams.Command + ' ' + useResultValue
  }
}
```

### 2. 修正 testResults 儲存邏輯

**檔案:** `frontend/src/views/TestMain.vue` (line 864-867)

```javascript
// 原有程式碼: 只用 item_no 作為 key
if (result.measured_value !== null) {
  testResults.value[item.item_no] = String(result.measured_value)
}

// 修正後: 同時用 item_no 和 item_name 作為 key
if (result.measured_value !== null) {
  const measuredValueStr = String(result.measured_value)
  testResults.value[item.item_no] = measuredValueStr    // 用序號作為 key (例如: 2)
  testResults.value[item.item_name] = measuredValueStr  // 用名稱作為 key (例如: "123_1")
}
```

這樣無論 `use_result` 欄位儲存的是 item_no 還是 item_name，都能正確查找到對應的測量結果。

## 測試驗證

### 1. 資料庫配置檢查

```sql
SELECT item_no, item_name, switch_mode, use_result, eq_limit, limit_type
FROM test_plans
WHERE item_name IN ('123_1', '123_2')
ORDER BY item_no;
```

預期結果：
```
item_no=2, item_name='123_1', use_result=NULL,    eq_limit='123', limit_type='partial'
item_no=4, item_name='123_2', use_result='123_1', eq_limit='456', limit_type='partial'
```

**注意:** 如果 `123_2` 的 `eq_limit` 仍然是 "123"，需要修改為 "456"：

```sql
UPDATE test_plans
SET eq_limit = '456'
WHERE item_name = '123_2';
```

### 2. 測試腳本驗證

建立測試腳本 `backend/scripts/test_use_result.py`：

```python
#!/usr/bin/env python3
import sys

if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg == '123':
        print('456')
    elif arg == '456':
        print('789')
    else:
        print(f'Received: {arg}')
else:
    print('123')
```

手動測試：
```bash
cd backend
python scripts/test123.py          # 輸出: 123
python scripts/test123.py 123      # 輸出: 456
python scripts/test123.py 123_1    # 輸出: (空) ← 原本的問題
```

### 3. 完整測試流程

1. 刷新前端頁面（重新載入修正後的代碼）
2. 選擇專案和站別
3. 載入測試計劃
4. 開始測試
5. 觀察測試結果：
   - 123_1: 測量值 = "123", 結果 = PASS
   - 123_2: 測量值 = "456", 結果 = PASS

### 4. 檢查日誌

**前端瀏覽器 Console:**
```javascript
// 應該看到 testResults 正確儲存
testResults.value = {
  2: "123",
  "123_1": "123",
  4: "456",
  "123_2": "456"
}
```

**後端日誌:**
```
INFO - Executing Other script: .../backend/scripts/test123.py
INFO - use_result value: 123  (已替換為實際值，而不是 "123_1")
INFO - Measurement completed: measured_value=456, result=PASS
```

## UseResult 機制說明

### 用途

UseResult (use_result) 是 PDTool4 的依賴注入機制，允許一個測試項目使用前一個測試項目的測量結果作為輸入參數。

### 應用場景

1. **串聯測試**:
   - 項目 A 讀取設備序號 → 項目 B 使用該序號查詢資料庫

2. **累加計算**:
   - 項目 A 測量電壓 → 項目 B 使用該電壓計算功率

3. **條件測試**:
   - 項目 A 檢查設備類型 → 項目 B 根據類型執行不同測試

### 配置方式

在測試計劃中設定：
- `use_result` 欄位: 填入前一個測試項目的 `item_name` 或 `item_no`
- 例如: 項目 "123_2" 要使用項目 "123_1" 的結果，則設定 `use_result = "123_1"`

### 執行邏輯

1. 前端執行測試項目時，將測量結果儲存在 `testResults` 字典中
2. 遇到有 `use_result` 欄位的項目時，從 `testResults` 查找對應的測量結果
3. 將查找到的結果值替換 `use_result` 欄位的原值
4. 將替換後的值傳遞給後端
5. 後端將該值作為命令行參數傳遞給腳本

## 相關檔案

- `frontend/src/views/TestMain.vue` - 測試執行介面，包含 UseResult 處理邏輯
- `backend/app/measurements/implementations.py` - OtherMeasurement 類別，處理腳本執行
- `backend/scripts/test123.py` - 測試腳本範例
- `backend/scripts/test_use_result.py` - 改進的測試腳本
- `docs/fix-measured-value-database-error.md` - 相關錯誤修正文檔

## 注意事項

1. **testResults 的 key 格式**: 同時支援 item_no（數字）和 item_name（字串）
2. **use_result 的值**: 應該填入前置項目的 `item_name`，而非 `item_no`（雖然兩者都支援）
3. **腳本參數處理**: 腳本必須能正確處理傳入的參數，否則可能不輸出或輸出錯誤內容
4. **大小寫敏感**: 資料庫欄位名稱是小寫的 `use_result`，但為了兼容性也支援大寫 `UseResult`

## 修正時間

2026-02-10

## 相關問題

- [fix-measured-value-database-error.md](./fix-measured-value-database-error.md) - measured_value 資料類型錯誤
- [fix-switch-mode-database-schema.md](./fix-switch-mode-database-schema.md) - switch_mode 欄位缺失錯誤
