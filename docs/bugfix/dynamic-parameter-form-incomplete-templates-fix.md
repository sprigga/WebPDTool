# 動態參數表單測試類型不完整問題修復

**日期：** 2026-02-10
**問題嚴重程度：** 高
**影響範圍：** 測試計劃管理功能，動態參數表單

## 問題描述

用戶在測試計劃管理頁面新增測試項目時，遇到以下問題：

1. **測試類型下拉選單不完整**
   - 只顯示 3 個選項：PowerSet, PowerRead, CommandTest
   - 缺少：SFCtest, getSN, OPjudge, Other, Wait, Relay 等測試類型

2. **測試參數設定區域空白**
   - 選擇測試類型後，測試參數表單顯示「請先選擇測試類型和儀器模式」
   - 即使選擇了測試類型和儀器模式，參數表單仍不顯示

## 根本原因分析

### 問題 1：MEASUREMENT_TEMPLATES 定義不完整

**位置：** `backend/app/config/instruments.py`

**原因：**
- `MEASUREMENT_TEMPLATES` 字典只定義了 3 個測試類型（PowerSet, PowerRead, CommandTest）
- 雖然 `MEASUREMENT_TYPE_DESCRIPTIONS` 中列出了其他測試類型，但沒有對應的參數模板
- 前端 `useMeasurementParams` composable 的 `testTypes` 計算屬性從模板鍵值生成，導致下拉選單不完整

**影響：**
- 前端 API 調用 `GET /api/measurements/templates` 只返回 3 種測試類型
- 用戶無法為其他測試類型創建測試計劃項目

### 問題 2：Switch Mode 自動選擇邏輯缺失

**位置：**
- `frontend/src/composables/useMeasurementParams.js`
- `frontend/src/views/TestPlanManage.vue`

**原因：**
- `currentTemplate` 計算屬性要求**同時**選擇測試類型和儀器模式才返回模板
- 對於只有一個 switch mode 的測試類型（如 SFCtest 的 "default"），用戶不知道需要選擇儀器模式
- 導致參數表單始終顯示空狀態提示

**影響：**
- 即使選擇了測試類型，參數表單也不會自動顯示
- 用戶體驗差，需要額外手動選擇儀器模式

## 修復方案

### 修復 1：補充完整的測試類型模板

**檔案：** `backend/app/config/instruments.py`

**修改內容：**

在 `MEASUREMENT_TEMPLATES` 字典中新增以下測試類型：

```python
"SFCtest": {
    "default": {
        "required": ["Mode"],
        "optional": [],
        "example": {"Mode": "webStep1_2"}
    }
},
"getSN": {
    "default": {
        "required": ["Type"],
        "optional": ["SerialNumber"],
        "example": {"Type": "SN"}
    }
},
"OPjudge": {
    "default": {
        "required": ["Type"],
        "optional": ["Expected", "Result"],
        "example": {"Type": "YorN", "Expected": "PASS"}
    }
},
"Other": {
    "script": {
        "required": [],
        "optional": ["use_result", "UseResult", "timeout", "Timeout", "wait_msec", "WaitmSec"],
        "example": {"timeout": "5000", "wait_msec": "0"}
    }
},
"Wait": {
    "default": {
        "required": ["wait_msec"],
        "optional": ["WaitmSec"],
        "example": {"wait_msec": "1000"}
    }
},
"Relay": {
    "default": {
        "required": ["RelayName", "Action"],
        "optional": [],
        "example": {"RelayName": "RELAY_1", "Action": "ON"}
    }
}
```

**測試類型總數：** 9 種
- PowerSet
- PowerRead
- CommandTest
- SFCtest
- getSN
- OPjudge
- Other
- Wait
- Relay

### 修復 2：自動選擇單一 Switch Mode

**檔案 1：** `frontend/src/composables/useMeasurementParams.js`

**修改：** `currentTemplate` 計算屬性

```javascript
// 原有邏輯（有問題）
const currentTemplate = computed(() => {
  if (!currentTestType.value || !currentSwitchMode.value) {
    return null
  }
  return templates.value[currentTestType.value]?.[currentSwitchMode.value] || null
})

// 修復後邏輯
const currentTemplate = computed(() => {
  if (!currentTestType.value) {
    return null
  }

  // 如果沒有選擇 switch_mode，但測試類型只有一個 switch mode，自動使用它
  let switchMode = currentSwitchMode.value
  if (!switchMode && switchModes.value.length === 1) {
    switchMode = switchModes.value[0]
  }

  if (!switchMode) {
    return null
  }

  return templates.value[currentTestType.value]?.[switchMode] || null
})
```

**檔案 2：** `frontend/src/views/TestPlanManage.vue`

**修改：** `handleTestTypeChange` 方法

```javascript
// 原有邏輯（有問題）
const handleTestTypeChange = (testType) => {
  currentTestType.value = testType
  editingItem.switch_mode = ''
  editingItem.parameters = {}
}

// 修復後邏輯
const handleTestTypeChange = (testType) => {
  currentTestType.value = testType
  editingItem.switch_mode = ''
  editingItem.parameters = {}

  // 如果測試類型只有一個 switch mode，自動選擇它
  if (switchModes.value.length === 1) {
    editingItem.switch_mode = switchModes.value[0]
    currentSwitchMode.value = switchModes.value[0]
  }
}
```

## 修復驗證

### 後端驗證

```bash
# 檢查測試類型列表
curl -s http://localhost:9100/api/measurements/templates | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print('\n'.join(data['test_types']))"

# 預期輸出：
# PowerSet
# PowerRead
# CommandTest
# SFCtest
# getSN
# OPjudge
# Other
# Wait
# Relay
```

```bash
# 檢查特定測試類型的模板
curl -s http://localhost:9100/api/measurements/templates/SFCtest | python3 -m json.tool

# 預期輸出：
# {
#     "test_type": "SFCtest",
#     "switch_modes": {
#         "default": {
#             "required": ["Mode"],
#             "optional": [],
#             "example": {"Mode": "webStep1_2"}
#         }
#     }
# }
```

### 前端驗證

1. **訪問測試計劃管理頁面**
   - URL: http://localhost:9080/testplan
   - 登入後選擇專案和站別

2. **點擊「新增項目」按鈕**
   - 確認「測試類型」下拉選單顯示 9 個選項

3. **選擇只有一個 switch mode 的測試類型**（如 SFCtest）
   - 確認「儀器模式」自動填充為 "default"
   - 確認「測試參數設定」區域立即顯示參數表單
   - 確認顯示 "Mode" 必填欄位，範例值為 "webStep1_2"

4. **選擇有多個 switch mode 的測試類型**（如 PowerSet）
   - 確認「儀器模式」下拉選單顯示：DAQ973A, MODEL2303, MODEL2306
   - 選擇儀器模式後，確認參數表單正確顯示

5. **保存測試項目**
   - 填寫參數後點擊「儲存」
   - 確認參數正確保存到 `test_plans.parameters` JSON 欄位

## 部署步驟

### Docker 環境（推薦）

```bash
# 1. 重啟後端容器（載入更新的 MEASUREMENT_TEMPLATES）
docker-compose restart backend

# 2. 重新構建並啟動前端容器
docker-compose build --no-cache frontend
docker-compose up -d frontend

# 3. 確認容器狀態
docker-compose ps

# 4. 清除瀏覽器緩存
# - 按 Ctrl+Shift+R（Windows/Linux）或 Cmd+Shift+R（Mac）
# - 或使用無痕模式測試
```

### 本地開發環境

```bash
# 後端
cd backend
# Python 會自動載入更新的 instruments.py

# 前端
cd frontend
npm run build  # 如果是生產環境
npm run dev    # 如果是開發環境
```

## 影響範圍

### 修改的檔案

1. **後端**
   - `backend/app/config/instruments.py` - 新增 6 個測試類型模板

2. **前端**
   - `frontend/src/composables/useMeasurementParams.js` - 修改 `currentTemplate` 邏輯
   - `frontend/src/views/TestPlanManage.vue` - 修改 `handleTestTypeChange` 方法

### 不受影響的部分

- 所有現有測試計劃資料保持不變
- API 端點簽名未改變
- 資料庫架構未改變
- 向後兼容，現有功能繼續運作

## 設計決策

### 為什麼使用 "default" 作為 Switch Mode？

對於只有一種執行方式的測試類型（如 SFCtest, getSN, OPjudge），使用 "default" 作為統一的 switch mode 名稱有以下好處：

1. **簡化配置**：不需要為每個測試類型創建特定的 switch mode 名稱
2. **前端自動化**：前端可以自動檢測並選擇唯一的 switch mode
3. **擴展性**：如果未來需要為這些測試類型添加多種執行方式，可以保留 "default" 並新增其他模式

### 為什麼不將 Switch Mode 設為可選？

雖然可以修改 API 讓 switch_mode 完全可選，但保留必選設計有以下原因：

1. **架構一致性**：所有測試類型都遵循 `test_type` + `switch_mode` 的模式
2. **清晰的數據模型**：資料庫中明確記錄每個測試項目使用的執行模式
3. **未來擴展**：如果某個測試類型需要添加新的執行模式，不需要修改 API 設計
4. **驗證邏輯統一**：參數驗證邏輯可以統一處理，無需特殊情況判斷

## 未來改進建議

### Phase 2 功能（未來實現）

1. **CSV 上傳時的參數預覽**
   - 在上傳 CSV 時顯示參數預覽表格
   - 允許用戶在保存前編輯參數
   - 批量驗證所有導入的測試項目

2. **參數模板系統**
   - 允許用戶保存常用參數組合為模板
   - 快速應用模板到新測試項目
   - 模板版本管理

3. **儀器自動發現**
   - 自動檢測連接的儀器
   - 在儀器模式下拉選單中顯示可用儀器
   - 驗證選擇的儀器是否在線

4. **自定義測試類型**
   - 允許用戶定義新的測試類型
   - 動態配置參數定義
   - 插件式架構支持第三方測試類型

## 測試結果

### 功能測試

| 測試項目 | 結果 | 備註 |
|---------|------|------|
| 後端 API 返回 9 種測試類型 | ✅ PASS | 使用 curl 驗證 |
| 前端下拉選單顯示 9 個選項 | ✅ PASS | 瀏覽器測試 |
| SFCtest 自動選擇 "default" | ✅ PASS | 選擇後立即顯示參數表單 |
| getSN 自動選擇 "default" | ✅ PASS | 參數表單正確顯示 |
| PowerSet 需手動選擇儀器模式 | ✅ PASS | 顯示 3 個儀器選項 |
| 參數驗證正常運作 | ✅ PASS | 缺少必填參數時顯示錯誤 |
| 保存測試項目成功 | ✅ PASS | 參數正確存儲到資料庫 |

### 回歸測試

| 測試項目 | 結果 | 備註 |
|---------|------|------|
| 現有測試計劃載入正常 | ✅ PASS | 無數據遷移問題 |
| 編輯現有測試項目 | ✅ PASS | 向後兼容 |
| CSV 上傳功能 | ✅ PASS | 不受影響 |
| 測試執行功能 | ✅ PASS | 測量邏輯未改變 |

## 相關文檔

- [動態參數表單設計文檔](../plans/2026-02-09-dynamic-parameter-form-design.md)
- [動態參數表單使用指南](../features/dynamic-parameter-form-usage.md)
- [測量實現指南](../features/measurement-implementations.md)
- [CLAUDE.md 專案概述](../../CLAUDE.md)

## 變更歷史

| 日期 | 版本 | 修改內容 |
|-----|------|---------|
| 2026-02-10 | 1.0 | 初始版本 - 修復測試類型不完整問題 |
