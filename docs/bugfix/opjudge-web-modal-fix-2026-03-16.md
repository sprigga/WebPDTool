# OPjudge Web Modal 修正紀錄

**日期：** 2026-03-16
**影響範圍：** OPjudge 測量類型在 Web/Docker 環境中執行
**症狀：** session 執行 opjudge_test 項目時，結果永遠是 FAIL，或拋出 `Unexpected OPjudge response` 錯誤

---

## Bug 1：PyQt5 ModuleNotFoundError

### 症狀

```
session id: 198, 測試項目: opjudge_test
錯誤訊息: ModuleNotFoundError: No module named 'PyQt5'
```

### 根本原因

`_execute_op_judge` 的 `script_map` 直接指向 `OPjudge_confirm.py`（PyQt5 GUI 版），
而 Docker/Web 容器內沒有 PyQt5，subprocess 啟動後立即崩潰。

```python
# 原有程式碼（有問題）
script_map = {
    "confirm": "./src/lowsheen_lib/OPjudge_confirm.py",   # PyQt5
    "YorN":    "./src/lowsheen_lib/OPjudge_YorN.py",      # PyQt5
}
```

### 修正方式

`backend/app/services/measurement_service.py`

優先使用 terminal 版本（不依賴 PyQt5），fallback 到 GUI 版本（實體硬體站保留相容性）：

```python
# 修正後
script_map_terminal = {
    "confirm": "./src/lowsheen_lib/OPjudge_confirm_terminal.py",
    "YorN":    "./src/lowsheen_lib/OPjudge_YorN_terminal.py",
}
script_map_gui = {
    "confirm": "./src/lowsheen_lib/OPjudge_confirm.py",
    "YorN":    "./src/lowsheen_lib/OPjudge_YorN.py",
}
terminal_path = script_map_terminal[switch_mode]
gui_path      = script_map_gui[switch_mode]
script_path   = terminal_path if os.path.exists(terminal_path) else gui_path
```

---

## Bug 2：stdout 雜訊導致 `Unexpected OPjudge response`

### 症狀

```
session id: 199, 測試項目: opjudge_test
錯誤訊息: Unexpected OPjudge response:
============================================================
TEST POINT: ('15',)
...
PRESS [ENTER] TO CONFIRM (PASS)
...
❌ OPERATOR REJECTED (CTRL+C)
FAIL
```

### 根本原因

terminal 版本腳本（`OPjudge_confirm_terminal.py`）把所有說明文字（header、warning、prompt）都
寫到 **stdout**，而不是 stderr（違反 CLI 慣例：機器可讀結果用 stdout，說明訊息用 stderr）。

`_execute_op_judge` 用 `stdout.strip().upper()` 取整段輸出，導致多行說明文字被當作
response 去比對 `"PASS"/"FAIL"`，自然不匹配。

```python
# 原有程式碼（有問題）
response = stdout.decode("utf-8", errors="replace").strip().upper()
# 取到整段說明文字，比對失敗
```

### 修正方式

`backend/app/services/measurement_service.py`

取 stdout 的**最後一行**：terminal 腳本（和 PyQt5 腳本）的結果永遠是最後一個 `print()`：

```python
# 修正後
full_output = stdout.decode("utf-8", errors="replace").strip()
last_line   = full_output.splitlines()[-1].strip() if full_output else ""
response    = last_line.upper()
```

---

## Bug 3：operator_judgment 被後端忽略，前端 Modal 無效

### 症狀

```
session id: 203, 測試項目: opjudge_test
量測值: 0.0, 結果: FAIL
```
操作員在前端 Modal 中按了「確認（PASS）」，但結果仍然是 FAIL。

### 除錯過程

1. **查 DB 記錄**，確認 `result = FAIL` 是後端寫入的，不是前端 limit 驗證造成的。
2. **查後端 log**，`Executing OPjudge measurement for 15` 後直接保存結果，確認有執行。
3. **查前端邏輯**，`measurementType !== 'OPjudge'` bypass 已正確加入，前端 limit 不是問題。
4. **查 TestPlan 設定**：`limit_type = "equality"`, `lower_limit = NULL`。
   - 懷疑 `equality` 驗證 `str(measured_value) == str(None)` → FAIL，但 `execute_single_measurement` 未呼叫 `validate_result()`，排除。
5. **回到根本**：terminal 腳本的 `input()` 在容器沒有 TTY 時拋 `EOFError` → 腳本輸出 `FAIL`。
   前端 Modal 雖然送出 `operator_judgment = "PASS"`，但原邏輯**只有 script 不存在時**才讀取 `operator_judgment`，script 存在時直接跑 subprocess，忽略了前端的結果。

### 根本原因

```python
# 原有流程（有問題）
if not os.path.exists(script_path):          # script 存在 → 跳過
    fallback_judgment = test_params["operator_judgment"]
    return PASS/FAIL based on fallback_judgment

# 直接跑 subprocess —— operator_judgment 被完全忽略
process = await asyncio.create_subprocess_exec(...)
# input() → EOFError → 輸出 FAIL
```

### 修正方式

`backend/app/services/measurement_service.py`

新增第一優先路徑：`operator_judgment` 存在時直接回傳，不執行 subprocess。
執行優先順序改為：

| 優先順序 | 條件 | 行為 |
|---------|------|------|
| 1 | `test_params` 含 `operator_judgment` | **直接使用**（Web Modal 模式） |
| 2 | script 不存在 | 回傳 ERROR |
| 3 | script 存在 | 執行 subprocess（實體硬體站模式） |

```python
# 修正後
# 1. operator_judgment 優先（Web 模式）
web_judgment = None
for key in test_params:
    if key.lower() == "operator_judgment":
        web_judgment = str(test_params[key]).upper()
        break

if web_judgment is not None:
    if web_judgment in ("PASS", "1", "YES", "Y"):
        return MeasurementResult(result="PASS", measured_value=Decimal("1"))
    else:
        return MeasurementResult(result="FAIL", measured_value=Decimal("0"))

# 2. script 不存在 → ERROR
if not os.path.exists(script_path):
    return MeasurementResult(result="ERROR", error_message=f"Script {script_path} not found")

# 3. 執行 subprocess（實體硬體站）
process = await asyncio.create_subprocess_exec(...)
```

---

## Bug 4：前端 limit 驗證覆蓋 OPjudge 結果（潛在問題）

### 症狀

雖然 session 203 的根本原因是 Bug 3，但前端的 limit 驗證也存在潛在問題：
當 `measured_value = 0`（數字型，代表 FAIL）且 TestPlan 有 `lower_limit` 時，
`0 < lower_limit` 會再次強制設 `result = FAIL`，即使後端回傳 PASS 也會被覆蓋。

### 修正方式

`frontend/src/views/TestMain.vue`

```js
// 修正後：OPjudge 跳過 limit 二次驗證
if (measurementType !== 'OPjudge' && response.measured_value !== null ...) {
    // limit 驗證邏輯
}
```

---

## 前端 OPjudge Modal 實作

同次修正中新增了 Web 操作員判斷 Modal（`TestMain.vue`）：

- 測試執行到 `OPjudge` 且無靜態 `operator_judgment` 時，暫停並顯示 Modal
- `confirm` 模式：只顯示「確認」按鈕（→ PASS）
- `YorN` 模式：顯示 PASS / FAIL 兩個按鈕
- 使用 Promise + resolve callback 實現 `await waitForOpJudge()`，不需要 WebSocket
- 操作員點擊後，結果注入 `testParams.operator_judgment`，後端走優先路徑回傳

```js
// 暫停 loop，等待操作員點擊
const judgment = await waitForOpJudge()   // Modal 顯示
testParams.operator_judgment = judgment    // 注入結果
// 繼續執行 API 呼叫
```

---

## 修改的檔案

| 檔案 | 修改內容 |
|------|---------|
| `backend/app/services/measurement_service.py` | Bug 1、2、3 修正 |
| `frontend/src/views/TestMain.vue` | OPjudge Modal + Bug 4 修正 |
| `backend/tests/test_services/test_opjudge_measurement.py` | 更新 fallback 測試斷言 |
