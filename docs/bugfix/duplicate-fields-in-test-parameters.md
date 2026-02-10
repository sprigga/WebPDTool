# 修復測試參數設定區塊中的重複欄位問題

## 問題描述

在 `TestPlanManage.vue` 的測試項目編輯對話框中，「測試參數設定」區塊顯示了重複的欄位：
- 左側：`use_result`, `timeout`, `wait_msec`（來自動態參數表單）
- 右側：`Use Result`, `Timeout`, `Waitm Sec`（來自動態參數表單）

這些欄位同時也在「執行設定」區塊中正確顯示（作為資料表直接欄位）。

## 根本原因

1. **資料模型設計**：`use_result`, `timeout`, `wait_msec` 是 `TestPlan` 模型的直接欄位（定義於 `backend/app/models/testplan.py` lines 41-43）
2. **測量參數模板**：`MEASUREMENT_TEMPLATES["Other"]["script"]["optional"]` 錯誤地包含了這些欄位（定義於 `backend/app/config/instruments.py` line 161）
3. **顯示邏輯**：`DynamicParamForm` 元件會自動顯示測量參數模板中定義的所有參數

## 修復方案

### 1. 移除測量參數模板中的重複欄位

**檔案**：`backend/app/config/instruments.py`

**修改前**：
```python
"Other": {
    "script": {
        "required": [],
        "optional": ["use_result", "UseResult", "timeout", "Timeout", "wait_msec", "WaitmSec"],
        "example": {
            "timeout": "5000",
            "wait_msec": "0"
        }
    }
},
```

**修改後**：
```python
"Other": {
    "script": {
        # 修正: 移除 use_result, timeout, wait_msec 參數，這些是資料表直接欄位，不應放在 parameters JSON 中
        # 原有程式碼: optional: ["use_result", "UseResult", "timeout", "Timeout", "wait_msec", "WaitmSec"]
        # 說明: 這些欄位在 TestPlan 模型中是獨立欄位 (testplan.py lines 41-43)，
        #       並且在編輯表單的"執行設定"區塊中顯示 (TestPlanManage.vue lines 433-455)
        "required": [],
        "optional": [],
        "example": {}
    }
},
```

### 2. 更新測量執行邏輯優先順序

**檔案**：`backend/app/measurements/implementations.py`

**修改前**：
```python
# Get optional parameters
use_result = get_param(self.test_params, "use_result", "UseResult")
timeout = get_param(self.test_params, "timeout", "Timeout", default=5000)
wait_msec = get_param(self.test_params, "wait_msec", "WaitmSec") or self.test_plan_item.get("wait_msec", 0)
```

**修改後**：
```python
# 修正: 優先使用資料表直接欄位 (test_plan_item)，而非 parameters JSON
# 原有程式碼: 僅從 test_params (parameters JSON) 取值
# 說明: use_result, timeout, wait_msec 是 TestPlan 模型的直接欄位，應優先使用
use_result = self.test_plan_item.get("use_result") or get_param(self.test_params, "use_result", "UseResult")
timeout = self.test_plan_item.get("timeout") or get_param(self.test_params, "timeout", "Timeout", default=5000)
wait_msec = self.test_plan_item.get("wait_msec") or get_param(self.test_params, "wait_msec", "WaitmSec", default=0)
```

## 驗證結果

執行測試驗證修復：

```bash
# 檢查 API 回應
curl http://localhost:9100/api/measurements/templates | python3 -m json.tool | grep -A 10 '"Other"'

# 結果：
{
    "Other": {
        "script": {
            "required": [],
            "optional": [],  # ✅ 已移除重複欄位
            "example": {}
        }
    }
}
```

## 影響範圍

### 前端
- ✅ `DynamicParamForm` 元件不再顯示重複的 `use_result`, `timeout`, `wait_msec` 欄位
- ✅ 這些欄位只在「執行設定」區塊顯示（lines 433-455）

### 後端
- ✅ `OtherMeasurement` 類別優先使用資料表欄位值
- ✅ 向後相容：如果資料表欄位為空，仍會嘗試從 parameters JSON 讀取（支援舊資料）

## 相關檔案

- `frontend/src/views/TestPlanManage.vue` - 測試計劃管理介面
- `frontend/src/components/DynamicParamForm.vue` - 動態參數表單元件
- `backend/app/config/instruments.py` - 測量參數模板定義
- `backend/app/measurements/implementations.py` - 測量執行實作
- `backend/app/models/testplan.py` - TestPlan 資料模型

## 學習要點

1. **資料模型一致性**：避免在多個地方（直接欄位 vs. JSON 參數）儲存相同資料
2. **清晰的資料歸屬**：
   - 通用執行參數（timeout, wait_msec）→ 直接欄位
   - 測量類型特定參數（Instrument, Channel）→ JSON parameters
3. **優先順序設計**：當有多個資料來源時，明確定義優先順序（資料表欄位 > JSON 參數）
