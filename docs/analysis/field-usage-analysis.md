# 欄位使用分析報告

## 日期: 2026-02-10

## 分析目標
確認 TestPlan 模型中的 `execute_name` 和 `case_type` 欄位是否被 backend 服務或 API 使用。

## 調查結果

### 1. execute_name (執行名稱)

#### 資料庫層
- ✅ 定義在 `backend/app/models/testplan.py:38`
- ✅ 包含在 API Schema (`backend/app/schemas/testplan.py`)
- ✅ CSV 匯入有處理 (`backend/app/utils/csv_parser.py:163`)

#### 後端業務邏輯層
- ❌ **沒有任何 service 或 measurement 層直接讀取此欄位**
- ❌ 不在 `backend/app/services/test_engine.py` 中被使用
- ❌ 不在 `backend/app/services/measurement_service.py` 中被使用
- ❌ 不在 `backend/app/measurements/implementations.py` 中被使用

#### 前端層
- ✅ 在 `TestMain.vue:1009` 中被讀取
- ✅ 轉換為 `measurement_type` 傳給後端 API (`TestMain.vue:1060-1072`)
- ✅ 在測試執行表格中顯示為"測試指令"

#### 結論
`execute_name` 是一個**前端使用的欄位**:
- 後端僅負責儲存和傳遞,不參與業務邏輯
- 前端讀取此欄位並轉換為 `measurement_type` 參數傳給後端
- 後端 API 接收的是 `measurement_type`,而非直接使用 `execute_name`

---

### 2. case_type (案例類型)

#### 資料庫層
- ✅ 定義在 `backend/app/models/testplan.py:39`
- ✅ 包含在 API Schema (`backend/app/schemas/testplan.py`)
- ✅ CSV 匯入有處理 (`backend/app/utils/csv_parser.py:164`)

#### 後端業務邏輯層
- ✅ **在測試引擎中被積極使用**

##### 使用場景 A: 測試類型決策 (`test_engine.py:221-233`)
```python
case_type = test_plan_item.case_type
special_case_types = {'wait', 'relay', 'chassis_rotation', 'console', 'comport', 'tcpip'}

# 如果 case_type 是特殊類型，使用 case_type 作為測試命令
if case_type and case_type.strip() and case_type.lower() in special_case_types:
    test_command = case_type
else:
    test_command = test_type
```

##### 使用場景 B: 自訂腳本選擇 (`implementations.py:82-94`)
```python
# OtherMeasurement 類別從 case_type 取得腳本名稱
switch_mode = (
    self.test_plan_item.get("case_type", "") or
    self.test_plan_item.get("switch_mode", "") or
    self.test_plan_item.get("item_name", "")
).strip()
```

##### 使用場景 C: 命令測試支援 (`measurement_service.py:458-469`)
```python
# 支援 case_type 作為 measurement_type
"command": {...},
# 直接支援 case_type 作為 measurement_type
"comport": {...},
"console": {...},
"tcpip": {...},
```

#### 前端層
- ✅ 在 `TestMain.vue:1006` 中被讀取
- ✅ 轉換為 `switch_mode` 傳給後端 API (`TestMain.vue:1074`)

#### 結論
`case_type` 是一個**後端和前端都有使用的核心欄位**:
- 後端: 決定測試執行邏輯、腳本選擇、特殊測試類型處理
- 前端: 轉換為 `switch_mode` 參數傳給後端
- 影響範圍: 測試執行引擎、測量實作、參數驗證

---

## 修改建議與實施

### 已實施: 方案2 - 隱藏 execute_name

#### 修改內容

##### 1. TestPlanManage.vue - 測試計劃管理介面

**表格欄位 (行 117):**
```vue
<!-- 原有程式碼: 顯示 execute_name 欄位 -->
<!-- 修正: 隱藏 execute_name 欄位 (僅用於 CSV 匯入儲存,不影響後端業務邏輯) -->
<!-- <el-table-column prop="execute_name" label="執行名稱" width="120" /> -->
```

**編輯表單 (行 344-365):**
```vue
<!-- 原有程式碼: 顯示執行名稱和案例類型欄位 -->
<!-- 修正: 隱藏 execute_name (僅用於 CSV 匯入),保留 case_type (影響測試執行邏輯) -->
<el-row :gutter="20">
  <!-- 隱藏 execute_name 欄位 -->
  <el-col :span="12">
    <el-form-item label="案例類型">
      <el-input
        v-model="editingItem.case_type"
        placeholder="例如: wait, comport, test123 (影響測試執行邏輯)"
      />
      <template #label>
        <span>案例類型
          <el-tooltip
            content="用於指定測試腳本名稱或特殊測試類型 (wait, relay, console, comport, tcpip 等)"
            placement="top"
          >
            <el-icon><QuestionFilled /></el-icon>
          </el-tooltip>
        </span>
      </template>
    </el-form-item>
  </el-col>
</el-row>
```

**Icon 導入 (行 522):**
```javascript
import { Upload, Plus, Delete, QuestionFilled } from '@element-plus/icons-vue'
```

##### 2. TestMain.vue - 測試執行介面

**表格欄位 (行 170):**
```vue
<!-- 原有程式碼: 顯示 execute_name 作為測試指令 -->
<!-- 說明: execute_name 在測試執行時被轉換為 measurement_type,保留顯示以便使用者了解測試類型 -->
<el-table-column prop="execute_name" label="測試指令" width="120" show-overflow-tooltip />
```

#### 保留資料庫欄位
- ✅ 資料庫 `test_plans` 表保留 `execute_name` 欄位
- ✅ CSV 匯入功能繼續處理 `execute_name` (向後相容)
- ✅ API Schema 保留此欄位 (可選填)

#### 不影響功能
- ✅ 後端業務邏輯完全不受影響 (原本就不使用此欄位)
- ✅ CSV 匯入功能正常運作
- ✅ 測試執行流程正常運作
- ✅ 前端仍可從 `test_type` 推導 `measurement_type`

---

## 技術見解

### 資料流程分析

#### execute_name 的資料流
```
CSV 檔案 (ExecuteName 欄位)
  ↓ (CSV Parser)
資料庫 test_plans.execute_name
  ↓ (API GET /api/testplans)
前端 TestMain.vue
  ↓ (轉換為 measurement_type)
後端 API /api/measurements/execute
  ↓
MeasurementService.execute_single_measurement()
```

**關鍵點:**
- 後端從未直接讀取 `test_plans.execute_name`
- 前端讀取後轉換為 API 參數 `measurement_type`
- 這是一個**前端資料轉換欄位**,非後端業務欄位

#### case_type 的資料流
```
CSV 檔案 (case 欄位)
  ↓ (CSV Parser)
資料庫 test_plans.case_type
  ↓ (API GET /api/testplans)
前端 TestMain.vue
  ↓ (轉換為 switch_mode)
後端 API /api/measurements/execute
  ↓
TestEngine.execute_test_session()
  ├─ 讀取 test_plan_item.case_type
  ├─ 判斷是否為特殊類型
  └─ 決定 test_command
    ↓
MeasurementService.execute_measurement()
    ↓
BaseMeasurement 子類別 (使用 case_type 選擇腳本)
```

**關鍵點:**
- 後端**直接讀取**資料庫的 `case_type` 欄位
- 用於業務邏輯決策 (特殊測試類型、腳本選擇)
- 這是一個**後端業務核心欄位**

---

## 未來建議

### 1. 考慮完全移除 execute_name
如果確認永遠不會在後端使用:
- 從資料庫 schema 移除
- 從 API schema 移除
- 從 CSV parser 移除
- 前端直接使用 `test_type` 作為 `measurement_type`

### 2. 統一欄位命名
建議將前端的參數命名與後端對齊:
- 前端: `measurement_type` (目前從 execute_name 轉換而來)
- 後端: `measurement_type` (API 參數)
- 資料庫: `test_type` (實際欄位)

### 3. 加強欄位文件說明
在 API 文件和使用手冊中明確說明:
- `test_type`: 測試類型 (PowerSet, PowerRead, CommandTest 等)
- `case_type`: 案例類型 / 腳本名稱 (wait, test123, comport 等)
- `execute_name`: (已廢棄) 僅用於 CSV 匯入向後相容

---

## 版本記錄

- **2026-02-10**: 初始分析報告
- **2026-02-10**: 實施方案2 - 隱藏 execute_name 欄位
