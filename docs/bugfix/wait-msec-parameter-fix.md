# Wait_msec 參數傳遞問題修正

> **相關問題追蹤:** [ISSUE8_wait_msec_parameter_not_passed.md](./ISSUE8_wait_msec_parameter_not_passed.md)
>
> **問題編號:** Issue #8
>
> **修正日期:** 2026-02-10

## 問題描述

在測試計劃管理頁面使用動態參數表單設定 `wait_msec = 1000` 後，執行測試時出現錯誤：

```
WAIT_FIX_5sec: wait mode requires wait_msec > 0, got: 1000
```

這個錯誤訊息很矛盾 - 明明設定了 `1000`（大於 0），卻報錯說需要 `> 0`。

## 問題分析

### 數據流追蹤

1. **測試計劃管理頁面（TestPlanManage.vue）**
   - 使用 `DynamicParamForm` 元件設定參數
   - 保存時：`editingItem.parameters = { wait_msec: 1000 }`
   - ✅ 正確保存到資料庫 `test_plans.parameters` (JSON 欄位)

2. **測試執行頁面（TestMain.vue）**
   - `executeSingleItem()` 函數提取測試參數
   - 原有邏輯：只從 `item` 物件的頂層屬性提取參數
   - ❌ **問題**：沒有提取 `item.parameters` 中的值
   - 結果：`testParams` 缺少 `wait_msec` 欄位

3. **後端驗證（WaitMeasurement）**
   - `get_param(self.test_params, "wait_msec", "WaitmSec")` 返回 `None`
   - 回退到 `self.test_plan_item.get("wait_msec", 0)` 返回 `0`
   - ❌ 驗證失敗：`wait_msec = 0` 不符合 `> 0` 的要求

### 根本原因

**動態參數表單設定的值（`parameters` 欄位）未被前端傳遞到後端測試 API。**

## 解決方案

### 修正檔案 1：`frontend/src/views/TestMain.vue`

**位置：** `executeSingleItem` 函數，第 1011-1024 行

**修正內容：**

```javascript
// 原有程式碼：只提取資料庫欄位
Object.keys(item).forEach(key => {
  if (!['item_no', 'item_name', ...].includes(key)) {
    if (item[key] && item[key] !== '') {
      testParams[key] = item[key]
    }
  }
})

// 修正：排除 parameters 欄位，避免直接傳遞物件
Object.keys(item).forEach(key => {
  if (!['item_no', 'item_name', ..., 'parameters'].includes(key)) {
    if (item[key] && item[key] !== '') {
      testParams[key] = item[key]
    }
  }
})

// 新增：合併 parameters 欄位到 testParams（優先級最高）
if (item.parameters && typeof item.parameters === 'object') {
  Object.entries(item.parameters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      testParams[key] = value
    }
  })
}
```

**修正原理：**
- 將 `parameters` 欄位從直接提取中排除
- 單獨處理 `parameters` 物件，將其中的鍵值對合併到 `testParams`
- 這樣可以確保動態參數表單的值能正確傳遞到後端

### 修正檔案 2：`backend/app/measurements/implementations.py`

**位置：** `WaitMeasurement.execute()` 方法，第 757-769 行

**修正內容：**

```python
# 原有程式碼：直接驗證型別
wait_msec = (
    get_param(self.test_params, "wait_msec", "WaitmSec") or
    self.test_plan_item.get("wait_msec", 0)
)

if not isinstance(wait_msec, (int, float)) or wait_msec <= 0:
    return self.create_result(
        result="ERROR",
        error_message=f"wait mode requires wait_msec > 0, got: {wait_msec}"
    )

# 修正：增加型別轉換邏輯
wait_msec = (
    get_param(self.test_params, "wait_msec", "WaitmSec") or
    self.test_plan_item.get("wait_msec", 0)
)

# 新增：型別轉換
try:
    if isinstance(wait_msec, str):
        wait_msec = int(wait_msec)
    elif not isinstance(wait_msec, (int, float)):
        wait_msec = 0
except (ValueError, TypeError):
    wait_msec = 0

if not isinstance(wait_msec, (int, float)) or wait_msec <= 0:
    return self.create_result(
        result="ERROR",
        error_message=f"wait mode requires wait_msec > 0, got: {wait_msec} (type: {type(wait_msec).__name__})"
    )
```

**修正原理：**
- 增加字串到數字的自動轉換邏輯
- 容錯處理：如果轉換失敗，設為 0 觸發驗證錯誤
- 錯誤訊息增加型別資訊，方便除錯

## 測試驗證

### 測試場景 1：數字型別參數

**測試數據：**
```javascript
item.parameters = { wait_msec: 1000 }
```

**期望結果：**
- ✅ 前端提取：`testParams.wait_msec = 1000` (number)
- ✅ 後端接收：`wait_msec = 1000` (int)
- ✅ 驗證通過：等待 1000 毫秒

### 測試場景 2：字串型別參數

**測試數據：**
```javascript
item.parameters = { wait_msec: "1000" }
```

**期望結果：**
- ✅ 前端提取：`testParams.wait_msec = "1000"` (string)
- ✅ 後端轉換：`wait_msec = 1000` (int)
- ✅ 驗證通過：等待 1000 毫秒

### 測試場景 3：資料庫欄位覆蓋

**測試數據：**
```javascript
item.wait_msec = 500          // 資料庫欄位
item.parameters = { wait_msec: 1000 }  // 動態參數表單
```

**期望結果：**
- ✅ 前端提取：`testParams.wait_msec = 1000` (parameters 優先)
- ✅ 後端接收：`wait_msec = 1000` (int)
- ✅ 驗證通過：等待 1000 毫秒（使用動態參數的值）

## 影響範圍

### 受影響的測試類型

這個修正不僅適用於 `WaitMeasurement`，所有使用動態參數表單的測試類型都會受益：

1. **Wait** - 等待測試
2. **PowerSet** - 電源設定（Instrument, SetVolt, SetCurr）
3. **PowerRead** - 電源讀取（Instrument, Channel, Item）
4. **RF_Tool_LTE_TX** - LTE 發射測試
5. **RF_Tool_LTE_RX** - LTE 接收測試
6. **CMW100_BLE** - 藍牙測試
7. **CMW100_WiFi** - WiFi 測試
8. **其他所有使用 DynamicParamForm 的測試類型**

### 向後相容性

✅ **完全向後相容**

- CSV 匯入的測試項目（直接寫入資料庫欄位）不受影響
- 手動建立的測試項目（不使用動態參數表單）不受影響
- 修正只是增加了 `parameters` 欄位的支援，不影響既有邏輯

## 最佳實踐建議

### 對於測試計劃設計者

1. **優先使用動態參數表單**
   - 在測試計劃管理頁面新增/編輯測試項目時
   - 選擇測試類型和儀器模式後
   - 在「測試參數設定」區塊填寫參數

2. **參數優先級**
   - `parameters` (動態參數表單) > 資料庫欄位
   - 如果同時設定了 `parameters.wait_msec` 和 `wait_msec` 欄位
   - 系統會優先使用 `parameters.wait_msec` 的值

3. **參數驗證**
   - 動態參數表單會自動驗證必填參數
   - 保存前確保所有必填參數都已填寫
   - 參數範例值會顯示在輸入框下方

### 對於開發者

1. **新增測試類型時**
   - 在 `backend/app/measurements/implementations.py` 中實作測量類別
   - 使用 `get_param(self.test_params, ...)` 提取參數
   - 建議增加型別轉換邏輯，提升容錯性

2. **參數模板配置**
   - 在 `backend/measurement_templates.json` 中定義參數模板
   - 指定必填/選填參數、型別、範例值
   - 前端 `DynamicParamForm` 會自動生成對應表單

3. **錯誤訊息改進**
   - 錯誤訊息中包含參數名稱、期望值、實際值、型別
   - 方便使用者快速定位問題

## 相關文件

- [動態參數表單使用指南](../dynamic-parameter-form-usage.md)
- [動態參數表單設計文件](../dynamic-parameter-form-design.md)
- [測試計劃管理指南](../test-plan-management.md)
- [測量系統架構](../architecture/measurement-system.md)

## 變更歷史

| 日期 | 修正內容 | 修正人員 |
|------|---------|---------|
| 2026-02-10 | 修正動態參數表單值未傳遞到後端的問題 | Claude Code |
| 2026-02-10 | 增加後端型別轉換邏輯 | Claude Code |
| 2026-02-10 | 改進錯誤訊息（包含型別資訊） | Claude Code |
