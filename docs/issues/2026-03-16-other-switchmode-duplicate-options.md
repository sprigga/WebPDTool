# Issue: 儀器模式下拉選單與頂層測試類型重複選項

**日期：** 2026-03-16
**影響範圍：** `TestPlanManage.vue` 編輯對話框 > 基本資訊 > 儀器模式下拉選單
**嚴重性：** UI/UX（使用者操作混亂，不影響後端執行）
**狀態：** ✅ 已修正（三階段）

---

## 問題描述

在 `TestPlanManage.vue` 的測試項目編輯對話框中，「測試類型」與「儀器模式」之間存在多處重複選項，導致使用者不知道應從哪一層選擇。

### 問題一：`Other` 測試類型的儀器模式含有重複項

當「測試類型」選 `Other` 時，「儀器模式」出現 `wait`、`relay`、`console`、`comport`、`tcpip`——這些同時也是頂層「測試類型」選項。

### 問題二：`CommandTest` / `command` 的儀器模式含有重複項

當「測試類型」選 `CommandTest` 或 `command` 時，「儀器模式」出現 `android_adb`、`PEAK`——這些同時也是頂層「測試類型」選項。

### 問題三：`CommandTest` / `command` 本身與 `console` 功能重複

移除重複的儀器模式後，`CommandTest`/`command` 只剩 `custom` 一個選項，而 `custom` 的功能（執行 `command` 欄位的命令）與 `console` 測試類型完全相同——兩者都映射到後端的 `ConSoleMeasurement`。

### 問題四：`Other` 的 `chassis_rotation`/`test123`/`WAIT_FIX_5sec` 不應在通用 UI 出現

- `chassis_rotation`：已有頂層 `chassis_rotation` 測試類型（`ChassisRotationMeasurement`）
- `test123`、`WAIT_FIX_5sec`：是具體客製腳本名稱，不屬於通用 UI 選項

---

## 根本原因分析

### 資料流追蹤

前端的儀器模式選項來自後端 API：

```
GET /api/measurements/templates
→ MEASUREMENT_TEMPLATES (backend/app/config/instruments.py)
→ useMeasurementParams.js (computed: switchModes)
→ TestPlanManage.vue (el-select 儀器模式下拉)
```

`switchModes` 計算邏輯（無過濾）：

```javascript
// frontend/src/composables/useMeasurementParams.js:22
const switchModes = computed(() => {
  return Object.keys(templates.value[currentTestType.value])
})
```

→ 直接反映後端 `MEASUREMENT_TEMPLATES` 的 key，前端無任何過濾邏輯。
→ 只要後端定義了哪些 key，前端就全部顯示。

### 問題根源

`MEASUREMENT_TEMPLATES` 在 `case_type`/`execute_name` → `switch_mode` 遷移過程中（2026-03-16），將許多原本散落在 `case_type` 欄位的值整合進去，但未注意到與頂層 key 的命名衝突，導致相同功能在 UI 上出現在兩個地方。

後端執行時 **不依賴** `MEASUREMENT_TEMPLATES` 的定義來決定執行行為，`MEASUREMENT_TEMPLATES` 僅用於：
1. 前端 UI 下拉選單的選項生成
2. 前端 `DynamicParamForm` 的參數欄位渲染
3. 前端參數驗證（`/api/measurements/validate`）

---

## 除錯過程

### Step 1：確認問題範圍

查看 `TestPlanManage.vue` 儀器模式 `el-select` 的資料來源：

```vue
<!-- frontend/src/views/TestPlanManage.vue -->
<el-select v-model="editingItem.switch_mode" ...>
  <el-option v-for="mode in switchModes" :key="mode" :value="mode" />
</el-select>
```

`switchModes` 來自 `useMeasurementParams` composable，直接取後端回傳的 template keys。

### Step 2：列出 MEASUREMENT_TEMPLATES 頂層 key（即測試類型清單）

```bash
grep -n '^    "[A-Za-z0-9_]*": {' backend/app/config/instruments.py
```

輸出：`PowerSet`, `PowerRead`, `SFCtest`, `getSN`, `OPjudge`, `Other`, `Wait`, `Relay`, `comport`, `console`, `tcpip`, `CommandTest`, `command`, `android_adb`, `PEAK`, `wait`

### Step 3：對照各測試類型的 switch_mode，找出重複項

| 測試類型 | 問題 switch_mode | 重複的頂層測試類型 |
|---|---|---|
| `Other` | `wait` | `wait` / `Wait` |
| `Other` | `relay` | `Relay` |
| `Other` | `console` | `console` |
| `Other` | `comport` | `comport` |
| `Other` | `tcpip` | `tcpip` |
| `Other` | `chassis_rotation` | `chassis_rotation` |
| `Other` | `test123` | 客製腳本名稱，非通用選項 |
| `Other` | `WAIT_FIX_5sec` | 客製腳本名稱，且與 `Wait` 功能重複 |
| `CommandTest` | `android_adb` | `android_adb` |
| `CommandTest` | `PEAK` | `PEAK` |
| `command` | `android_adb` | `android_adb` |
| `command` | `PEAK` | `PEAK` |

### Step 4：確認後端執行行為不受影響

確認 `OtherMeasurement`（`implementations.py`）的執行邏輯：

```python
# OtherMeasurement.execute() 摘要
if switch_mode.lower() == "script":
    # 從 command 欄位讀取完整命令執行
    command = self.test_plan_item.get("command", "").strip()
    # 執行 shell command
else:
    # 將 switch_mode 值視為腳本名稱，找 scripts/{switch_mode}.py 執行
    script_path = os.path.join(scripts_dir, f"{switch_mode}.py")
```

→ `OtherMeasurement` 接受**任意** switch_mode 值（只要對應的 `.py` 檔存在），不依賴 `MEASUREMENT_TEMPLATES` 的 key 定義。

確認 `CommandTest`/`command` 的後端映射：

```python
# MEASUREMENT_REGISTRY (implementations.py)
"COMMAND_TEST": ConSoleMeasurement,  # CommandTest → ConSoleMeasurement
"command": ConSoleMeasurement,       # command     → ConSoleMeasurement
"console": ConSoleMeasurement,       # console     → ConSoleMeasurement（相同 class）
```

→ `CommandTest`、`command`、`console` 三者都映射到同一個 `ConSoleMeasurement`，功能完全等同。

### Step 5：確認 CSV 向下相容不受影響

後端 `MEASUREMENT_REGISTRY` 在 `MEASUREMENT_TEMPLATES` 移除後仍保留所有映射：

```python
"COMMAND_TEST": ConSoleMeasurement,
"command": ConSoleMeasurement,
```

→ 舊有 CSV 匯入的測試計劃（`test_type='CommandTest'` 或 `test_type='command'`）執行時完全不受影響。

---

## 修正方式

### 階段一：移除 `Other` 的 `wait/relay/console/comport/tcpip`（第一次）

**修改檔案：** `backend/app/config/instruments.py`

從 `MEASUREMENT_TEMPLATES["Other"]` 移除 5 個與頂層測試類型重複的 switch_mode key（`wait`、`relay`、`console`、`comport`、`tcpip`）。

### 階段二：處理 `CommandTest`/`command` 的重複問題

**修改檔案：** `backend/app/config/instruments.py`

**第一步**：從 `CommandTest` 和 `command` 移除 `android_adb`/`PEAK` switch_mode（與頂層 test_type 重複）。

**第二步**：確認只剩 `custom` 的 `CommandTest`/`command` 是否有獨特價值：
- `custom` 的功能 = 執行 `command` 欄位的命令 = `console` test_type 的原生功能
- 結論：`CommandTest`/`command` 整體從 `MEASUREMENT_TEMPLATES` 移除，UI 不再顯示

```python
# 已移除（改為註解）
# "CommandTest": { "custom": { ... } }
# "command": { "custom": { ... } }
```

### 階段三：`Other` 方案 A——只保留 `script`

**修改檔案：** `backend/app/config/instruments.py`

評估 `Other` 剩餘選項（`script`、`chassis_rotation`、`test123`、`WAIT_FIX_5sec`）後，決定採用方案 A：只保留 `script`。

| switch_mode | 移除原因 |
|---|---|
| `chassis_rotation` | 已是獨立頂層 test_type（`ChassisRotationMeasurement`） |
| `test123` | 具體客製腳本名稱，不屬於通用 UI 選項；改用 `script` + `command` 欄位 |
| `WAIT_FIX_5sec` | 客製腳本名稱，且功能與頂層 `Wait`/`wait` 重複 |

最終結果：

```python
"Other": {
    "script": {
        # 通用腳本執行模式: 從「命令」(command) 欄位讀取完整命令或腳本路徑執行
        "required": [],
        "optional": [],
        "example": {}
    }
}
```

**附加效果：** `Other` 只有一個 switch_mode，`useMeasurementParams.js` 的 `handleTestTypeChange` 會自動選取 `script`（`switchModes.length === 1` 邏輯），使用者無需手動選擇儀器模式。

---

## 測試更新

**修改檔案：** `backend/tests/test_config/test_instruments_templates.py`

```bash
python3 -m pytest tests/test_config/test_instruments_templates.py -v
# 結果: 35 passed
```

新增/更新的測試覆蓋：
- `test_commandtest_not_in_templates` — CommandTest 已從 MEASUREMENT_TEMPLATES 移除
- `test_command_not_in_templates` — command 已從 MEASUREMENT_TEMPLATES 移除
- `test_other_only_script_mode` — Other 只剩 script switch_mode
- `test_other_test123_not_in_templates` — test123 已移除
- `test_other_wait_fix_not_in_templates` — WAIT_FIX_5sec 已移除
- `test_other_chassis_rotation_not_in_templates` — chassis_rotation 已移除
- `test_other_script_mode_exists` — script 仍存在
- `test_other_script_validate_no_required` — script 模式不需必填參數

---

## 最終 UI 行為

| 測試類型 | 修正前儀器模式選項 | 修正後儀器模式選項 |
|---|---|---|
| `Other` | `script`, `chassis_rotation`, `test123`, `WAIT_FIX_5sec`, `wait`, `relay`, `console`, `comport`, `tcpip` | `script`（自動選取） |
| `CommandTest` | `android_adb`, `PEAK`, `custom` | *(已從測試類型下拉移除)* |
| `command` | `android_adb`, `PEAK`, `custom` | *(已從測試類型下拉移除)* |

---

## 相關檔案

| 檔案 | 說明 |
|---|---|
| `backend/app/config/instruments.py` | MEASUREMENT_TEMPLATES 定義（主要修改） |
| `backend/tests/test_config/test_instruments_templates.py` | 對應測試（已更新） |
| `frontend/src/composables/useMeasurementParams.js` | switchModes computed property（無需修改） |
| `frontend/src/views/TestPlanManage.vue` | 儀器模式下拉選單（無需修改） |
| `backend/app/measurements/implementations.py` | OtherMeasurement / MEASUREMENT_REGISTRY（無需修改） |
