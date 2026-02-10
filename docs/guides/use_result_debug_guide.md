# use_result 機制調試指南

## 當前狀態

### 已完成的修正

1. **前端 UseResult 處理邏輯** (TestMain.vue)
   - ✅ 添加小寫 `use_result` 的處理
   - ✅ 添加大寫 `UseResult` 的兼容處理
   - ✅ 將 use_result 的值替換為實際測量結果
   - ✅ 添加詳細的日誌追蹤

2. **前端 testResults 存儲邏輯** (TestMain.vue)
   - ✅ 同時使用 item_no 和 item_name 作為鍵
   - ✅ 支援兩種鍵值格式，提高兼容性

3. **資料庫配置**
   - ✅ 123_2 的 eq_limit 已修正為 "456"
   - ✅ use_result 欄位配置正確 (123_2 → 123_1)

4. **後端日誌追蹤** (implementations.py)
   - ✅ 添加 test_plan_item 和 test_params 的詳細日誌
   - ✅ 追蹤 use_result 的來源和最終值

### 調試日誌輸出

前端會輸出以下日誌（在瀏覽器 Console 中）：

```
[DEBUG] ==========================================
[DEBUG] 項目: 123_1
[DEBUG] item 欄位: [...]
[DEBUG] item.use_result: ...
[DEBUG] item.UseResult: ...
[DEBUG] item.parameters: ...
[DEBUG] 建構後的 testParams: ...
[DEBUG] 合併 parameters 後的 testParams: ...
[DEBUG] testParams.use_result: ...
[DEBUG] testParams.UseResult: ...
[DEBUG] ==========================================
[DEBUG] UseResult 處理開始
[DEBUG] 項目: ...
[DEBUG] testParams.use_result (原始): ...
[DEBUG] testParams.UseResult (原始): ...
[DEBUG] testResults.value: ...
[DEBUG] testResults keys: ...
[DEBUG] 從 testResults 查找: ...
[DEBUG] 替換後 use_result: ...
[DEBUG] 最終 testParams.use_result: ...
[DEBUG] ==========================================
```

後端會輸出以下日誌（在後端日誌中）：

```
[DEBUG] test_plan_item keys: [...]
[DEBUG] test_params keys: [...]
[DEBUG] use_result from test_plan_item: ...
[DEBUG] use_result from test_params: ...
[DEBUG] Final use_result value: ...
[DEBUG] timeout: ..., wait_msec: ...
```

## 下一步調試步驟

### 1. 啟動後端服務

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100
```

### 2. 啟動前端服務

```bash
cd frontend
npm run dev
```

### 3. 執行測試並觀察日誌

1. 打開瀏覽器並訪問前端（通常是 http://localhost:5173）
2. 打開瀏覽器開發者工具（F12）
3. 切換到 Console 選項卡
4. 選擇專案和站別
5. 開始測試
6. 觀察控制台輸出的 [DEBUG] 日誌

### 4. 關鍵檢查點

#### 檢查點 1: API 返回的數據
- 確認 `item.use_result` 是否為 "123_1"
- 確認 `item.UseResult` 是否為 undefined

#### 檢查點 2: testParams 建構
- 確認 `testParams.use_result` 是否為 "123_1"
- 確認是否被排除列表過濾掉（不應該）

#### 檢查點 3: testResults 字典
- 確認 `testResults.value` 是否包含 "123_1" 鍵
- 確認 `testResults.value["123_1"]` 是否為 "123"

#### 檢查點 4: use_result 替換
- 確認 `testParams.use_result` 是否從 "123_1" 變為 "123"
- 確認 `testParams.UseResult` 是否從 undefined 保持不變

#### 檢查點 5: 後端接收
- 確認後端日誌中的 `Final use_result value` 是否為 "123"
- 確認腳本執行時的參數是否為 "123"

### 5. 常見問題排查

#### 問題 A: testResults 字典為空

**原因**: 123_1 的測量結果沒有被正確存儲

**檢查**:
- 確認 123_1 的執行結果是否成功
- 檢查存儲邏輯（TestMain.vue 第 864-876 行）
- 確認 `result.measured_value` 是否為 null

#### 問題 B: use_result 沒有被替換

**原因**: testParams.use_result 的值與 testResults 的鍵不匹配

**檢查**:
- 確認 `testParams.use_result` 的值（例如 "123_1"）
- 確認 `testResults.value` 的鍵（可能是 2 而不是 "123_1"）
- 檢查類型是否匹配（字串 vs 數字）

#### 問題 C: 後端收到的值仍是項目名稱

**原因**: 前端的替換邏輯沒有執行

**檢查**:
- 確認前端日誌中的 "替換後 use_result"
- 檢查條件判斷是否正確
- 確認 testResults 字典是否正確初始化

## 修正清單

- [x] 前端添加小寫 use_result 處理
- [x] 前端添加雙重鍵值存儲
- [x] 前端添加詳細日誌
- [x] 後端添加詳細日誌
- [x] 資料庫配置修正（eq_limit）
- [ ] 用戶測試驗證
- [ ] 根據日誌調整邏輯

## 測試預期結果

執行測試後，應該看到：

```
項目 123_1:
  → 執行: python test123.py (無參數)
  → 輸出: "123"
  → testResults.value[2] = "123"
  → testResults.value["123_1"] = "123"
  → 結果: PASS (eq_limit="123", 測量值="123")

項目 123_2:
  → use_result = "123_1"
  → 查找: testResults.value["123_1"] = "123"
  → 替換: use_result = "123"
  → 執行: python test123.py "123"
  → 輸出: "456"
  → 結果: PASS (eq_limit="456", 測量值="456")
```

## 如果問題仍然存在

如果按照上述步驟調試後問題仍然存在，請提供：

1. 瀏覽器 Console 的完整日誌（特別是 [DEBUG] 部分）
2. 後端日誌的相關部分（特別是 [DEBUG] 部分）
3. 123_1 和 123_2 的執行結果和錯誤訊息

這樣可以精確定位問題發生的位置。
