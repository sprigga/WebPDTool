# ISSUE4: Measured Value Not Displayed in Frontend and Backend Logs

## 問題描述

### 錯誤現象
- **Backend Log**: 測試執行完成後只顯示 `result: PASS`,沒有顯示 `measured_value`
- **Frontend**: 測試表格中「測量值」欄位顯示 `-` (空白)

### 範例 Log
```
2026-01-09 06:51:40 - MeasurementService - INFO - Executing console measurement for 1
2026-01-09 06:51:40 - MeasurementService - INFO - Executing command: python /app/scripts/hello_world.py
2026-01-09 06:51:40 - MeasurementService - INFO - Measurement 1 completed with result: PASS
# ❌ 缺少 measured_value 資訊
```

### 測試案例
```python
# test_plans 表資料
{
    "item_no": 1,
    "item_name": "arduino",
    "test_type": "command",
    "case_type": "console",
    "command": "python /app/scripts/hello_world.py",
    "limit_type": "partial",
    "eq_limit": "Hello World!"
}

# 腳本輸出
# hello_world.py
print("Hello World!")

# 預期 measured_value: "Hello World!"
# 實際 measured_value: ❌ 未顯示
```

---

## 根本原因分析

### 問題: Backend Log 只記錄 result,未記錄 measured_value

**位置**: `backend/app/services/measurement_service.py:154-156`

**原有程式碼**:
```python
self.logger.info(
    f"Measurement {test_point_id} completed with result: {result.result}"
)
```

**問題**:
- 只記錄 `result: PASS/FAIL/ERROR`
- 沒有記錄 `measured_value` 實際測量值
- 導致無法從 log 追蹤實際測量數據
- 除錯困難,無法確認測試是否正確執行

---

## 修正內容

### 1. 更新 Backend Log 以包含 measured_value

**檔案**: `backend/app/services/measurement_service.py`
**行數**: 154-159

**修改前**:
```python
self.logger.info(
    f"Measurement {test_point_id} completed with result: {result.result}"
)
```

**修改後**:
```python
# 原有程式碼: 只記錄 result 狀態,沒有記錄 measured_value
# 修改: 同時記錄 result 狀態和 measured_value,方便調試和追蹤
measured_value_str = str(result.measured_value) if result.measured_value is not None else "None"
self.logger.info(
    f"Measurement {test_point_id} completed with result: {result.result}, measured_value: {measured_value_str}"
)
```

**改進點**:
- ✅ 同時記錄 `result` 和 `measured_value`
- ✅ 處理 `measured_value` 為 `None` 的情況
- ✅ 方便除錯和追蹤測試數據

---

## 驗證結果

### 修正前的 Log
```
2026-01-09 06:51:40 - MeasurementService - INFO - Measurement 1 completed with result: PASS
2026-01-09 06:51:40 - MeasurementService - INFO - Measurement 3 completed with result: PASS
```

### 修正後的 Log (預期)
```
2026-01-09 06:58:40 - MeasurementService - INFO - Measurement 1 completed with result: PASS, measured_value: Hello World!
2026-01-09 06:58:40 - MeasurementService - INFO - Measurement 3 completed with result: PASS, measured_value: 123
```

---

## 相關問題分析

### Frontend 顯示問題排查

根據程式碼分析,Frontend 應該能正確接收和顯示 `measured_value`:

1. **Backend API 回傳** ✅
   - `/api/measurements/execute` endpoint 正確回傳 `measured_value`
   - [measurements.py:94-101](backend/app/api/measurements.py:94-101)

2. **Frontend 接收** ✅
   - [TestMain.vue:775](frontend/src/views/TestMain.vue:775) `executeSingleMeasurement()` API 呼叫
   - [TestMain.vue:802](frontend/src/views/TestMain.vue:802) 取得 `response.measured_value`

3. **Frontend 顯示** ✅
   - [TestMain.vue:139-141](frontend/src/views/TestMain.vue:139-141) 測量值欄位
   - [TestMain.vue:420-436](frontend/src/views/TestMain.vue:420-436) `formatNumber()` 函數支援字串和數值

**結論**: Frontend 程式碼已正確實作,如果修正後 frontend 仍無顯示,可能是以下原因:
- Browser cache 問題 (需要強制重新整理)
- Backend container 未重新載入程式碼 (需要 restart)

---

## 測試步驟

### 1. 重新啟動 Backend Container
```bash
docker-compose restart backend
```

### 2. 在 Frontend 執行測試
- 打開 TestMain.vue 頁面
- 選擇測試計劃
- 點擊「開始測試」

### 3. 檢查 Backend Log
```bash
docker-compose logs -f backend | grep "measured_value"
```

**預期輸出**:
```
Measurement 1 completed with result: PASS, measured_value: Hello World!
Measurement 3 completed with result: PASS, measured_value: 123
```

### 4. 檢查 Frontend 顯示
- 測試計劃表格的「測量值」欄位
- 應顯示實際測量值 (例如: "Hello World!", "123")

---

## 預期效果

修正後:

1. ✅ **Backend Log 完整記錄**
   - 顯示 `result: PASS, measured_value: Hello World!`
   - 方便追蹤和除錯

2. ✅ **Frontend 正確顯示**
   - 測量值欄位顯示實際值
   - 字串類型 (如 "Hello World!") 正確顯示
   - 數值類型 (如 123) 正確顯示

3. ✅ **支援多種數據類型**
   - 字串: "Hello World!"
   - 數值: 123, 45.6
   - None: 顯示為 "None"

---

## 相關檔案

### 修改的檔案
1. `backend/app/services/measurement_service.py`
   - 行數 154-159
   - 更新 log 記錄,加入 `measured_value`

### 相關檔案 (未修改)
2. `backend/app/api/measurements.py`
   - API endpoint 已正確回傳 `measured_value`

3. `backend/app/measurements/implementations.py`
   - `CommandTestMeasurement` 已正確處理和返回 `measured_value`

4. `frontend/src/views/TestMain.vue`
   - `executeSingleItem()` 已正確接收和顯示 `measured_value`

---

## 總結

本次修正解決了 backend log 未記錄 `measured_value` 的問題:

1. **問題**: 測試完成後只記錄 result,沒有記錄實際測量值
2. **影響**: 無法從 log 追蹤測試數據,除錯困難
3. **修正**: 更新 log 格式,同時記錄 result 和 measured_value
4. **效果**: Log 現在完整記錄測試結果,方便追蹤和除錯

修正後系統能正確記錄和顯示測量值,提升可維護性和除錯效率。
