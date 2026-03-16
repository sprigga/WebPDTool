# Validation Rules Migration to MEASUREMENT_TEMPLATES

**日期：** 2026-03-16
**狀態：** 已完成
**相關檔案：**
- `backend/app/config/instruments.py` — MEASUREMENT_TEMPLATES (遷移目標)
- `backend/app/services/measurement_service.py` — validate_params() (遷移來源)
- `backend/tests/test_config/test_instruments_templates.py` — 新增驗證測試

---

## 問題背景

`MeasurementService.validate_params()` 使用兩層驗證策略：

```
1. 主要路徑 (primary path)
   validate_params_config() → 讀取 MEASUREMENT_TEMPLATES
   若找到對應模板 → 直接回傳驗證結果

2. 後備路徑 (legacy fallback)
   只有主要路徑回傳 "Unsupported combination" 時才啟用
   使用 measurement_service.py 內的硬編碼 validation_rules 字典
```

**問題：** `validation_rules` 字典中有許多測試類型尚未遷移到 `MEASUREMENT_TEMPLATES`，導致：
- 這些類型走後備路徑，驗證結果不一致
- 重複維護兩處驗證規則，容易出現分歧
- 後備路徑回傳 `"Legacy validation used"` 提示，前端顯示不必要的警告

---

## 遷移項目清單

遷移前，以下項目**僅存在**於 `validation_rules` 硬編碼字典，未在 `MEASUREMENT_TEMPLATES` 中：

| 類型 | Switch Modes | 狀態 |
|------|-------------|------|
| `CommandTest` | comport, tcpip, console, android_adb, PEAK, custom | ❌ 未遷移 |
| `command` | （同 CommandTest，為別名） | ❌ 未遷移 |
| `android_adb` | android_adb, custom | ❌ 未遷移 |
| `PEAK` | PEAK, custom | ❌ 未遷移 |
| `SFCtest` | webStep1_2, URLStep1_2, skip, WAIT_FIX_5sec | ⚠️ 只有 default |
| `getSN` | SN, IMEI, MAC | ⚠️ 只有 default |
| `wait`（小寫） | wait | ❌ 未遷移 |
| `Other` | test123, WAIT_FIX_5sec | ⚠️ 部分缺漏 |

---

## Schema 差異的關鍵判斷

遷移前需先釐清 `CommandTest` 與頂層 `comport`/`console`/`tcpip` 的 schema 差異：

| 來源 | 格式 | 必要參數 |
|------|------|---------|
| 頂層 `comport`（新式）| 使用 `Instrument` 欄位 | `Instrument`, `Command` |
| `CommandTest.comport`（PDTool4 舊式）| 使用 `Port`/`Baud` 欄位 | `Port`, `Baud`, `Command` |

**結論：** 兩者不能合併，必須各自保留獨立的 schema。`CommandTest` 使用 PDTool4 CSV 匯入的舊格式，頂層 `comport` 使用新式驅動格式。

---

## 修正步驟（TDD 流程）

### Chunk 1：新增 MEASUREMENT_TEMPLATES 條目

每個新類型均遵循「先寫測試 → 確認失敗 → 實作 → 確認通過」的 TDD 流程。

#### 1-1. CommandTest / command

在 `instruments.py` 的 `"tcpip"` 區塊之後新增：

```python
"CommandTest": {
    "comport": {
        "required": ["Port", "Baud", "Command"],
        "optional": ["keyWord", "spiltCount", "splitLength", "EqLimit", "Timeout"],
        "example": {"Port": "COM4", "Baud": "9600", "Command": "AT+VERSION"}
    },
    "tcpip": {
        "required": ["Host", "Port", "Command"],
        "optional": ["keyWord", "spiltCount", "splitLength", "Timeout"],
        "example": {"Host": "192.168.1.100", "Port": "5025", "Command": "*IDN?"}
    },
    "console": {
        "required": ["Command"],
        "optional": ["keyWord", "spiltCount", "splitLength", "Timeout"],
        "example": {"Command": "echo hello"}
    },
    "android_adb": {
        "required": ["Command"],
        "optional": ["Timeout"],
        "example": {"Command": "adb shell getprop ro.serialno"}
    },
    "PEAK": {
        "required": ["Command"],
        "optional": ["Timeout"],
        "example": {"Command": "send:0x01:0x02"}
    },
    "custom": {
        "required": [],
        "optional": ["command", "script_path"],
        "example": {"command": "python3 custom_script.py"}
    }
},
# "command" 為 CommandTest 的別名，內容完全相同
"command": { ... }  # 同上
```

#### 1-2. android_adb / PEAK（頂層類型）

```python
"android_adb": {
    "android_adb": {
        "required": ["Command"],
        "optional": ["Timeout", "serial"],
        "example": {"Command": "adb shell getprop ro.serialno"}
    },
    "custom": {"required": [], "optional": ["command", "script_path"], "example": {}}
},
"PEAK": {
    "PEAK": {
        "required": ["Command"],
        "optional": ["Timeout", "channel"],
        "example": {"Command": "send:0x01:0x02"}
    },
    "custom": {"required": [], "optional": ["command", "script_path"], "example": {}}
},
```

#### 1-3. SFCtest 擴充

原本只有 `"default"` mode，新增明確的 switch_mode：

```python
"SFCtest": {
    "default": {"required": ["Mode"], ...},
    # 新增:
    "webStep1_2": {"required": [], "optional": [], "example": {}},
    "URLStep1_2":  {"required": [], "optional": [], "example": {}},
    "skip":        {"required": [], "optional": [], "example": {}},
    "WAIT_FIX_5sec": {"required": [], "optional": [], "example": {}}
}
```

#### 1-4. getSN 擴充

```python
"getSN": {
    "default": {"required": ["Type"], "optional": ["SerialNumber"], ...},
    # 新增:
    "SN":   {"required": [], "optional": ["SerialNumber"], "example": {}},
    "IMEI": {"required": [], "optional": [], "example": {}},
    "MAC":  {"required": [], "optional": [], "example": {}}
}
```

#### 1-5. wait（小寫）頂層類型

```python
"wait": {
    "wait": {
        "required": [],
        "optional": ["wait_msec", "WaitmSec"],
        "example": {"wait_msec": "1000"}
    }
}
```

#### 1-6. Other 補充 modes

在既有 `Other` 區塊中新增：

```python
"test123":     {"required": [], "optional": ["arg"], "example": {}},
"WAIT_FIX_5sec": {"required": [], "optional": [], "example": {}}
```

### Chunk 2：清理 validation_rules 後備字典

確認所有類型通過主要路徑後，將 `measurement_service.py` 中對應的 `validation_rules` 條目注解掉（保留原始碼作記錄）：

```python
validation_rules = {
    "PowerSet": {},   # 已遷移 (2026-03-16)
    "PowerRead": {},  # 已遷移 (2026-03-16)

    # 原有程式碼: CommandTest / command 硬編碼驗證
    # 已遷移到 MEASUREMENT_TEMPLATES (2026-03-16)
    # "CommandTest": { ... },
    # "command": { ... },

    # ... (其他已遷移條目均以 # 注解保留)

    # OPjudge: 後備驗證路徑仍保留（主要路徑也有，雙重保障）
    "OPjudge": {
        "YorN": ["ImagePath", "content"],
        "confirm": ["ImagePath", "content"],
    },
}
```

**重要：** `has_parameter()` 執行期函式（約 lines 807-874）**不能移除**。它處理未知 switch_mode 的自訂腳本邏輯（檢查 `command` 或 `script_path` 是否存在），這是靜態模板無法表達的執行期行為。

---

## 除錯過程

### 問題 1：CommandTest vs. comport 的 schema 混淆

**現象：** `CommandTest.comport` 應使用 `Port`/`Baud`/`Command`，但頂層 `comport` 使用 `Instrument`/`Command`。若直接將 `CommandTest.comport` 指向頂層 `comport` 的 template，舊 CSV 測試計畫的驗證會失敗。

**診斷：**
```python
# 頂層 comport（新式驅動）
get_template("comport", "comport")
# → required: ["Instrument", "Command"]

# CommandTest.comport（PDTool4 CSV 匯入格式）
# 不存在於 MEASUREMENT_TEMPLATES → 走後備路徑
# → required: ["Port", "Baud", "Command"]
```

**修正：** 為 `CommandTest` 建立獨立的 schema 條目，保留 `Port`/`Baud` 格式。不與頂層 `comport` 合併。

---

### 問題 2：code review 發現 custom mode 測試缺漏

**現象：** 第一次實作後，spec reviewer 指出 `android_adb` 和 `PEAK` 的頂層 key 各自應有 `custom` mode，但測試未覆蓋。

**診斷：**
```
❌ TestAndroidAdbPeakTopLevel 沒有測試 custom mode 是否存在
❌ test_command_alias_same_as_commandtest 只檢查 mode key 存在，未驗證 required 參數一致
```

**修正：**
```python
# 新增 custom mode 測試
def test_android_adb_custom_mode_exists(self):
    assert "custom" in MEASUREMENT_TEMPLATES["android_adb"]

def test_peak_custom_mode_exists(self):
    assert "custom" in MEASUREMENT_TEMPLATES["PEAK"]

# 強化 command alias 測試：驗證 required 參數相同
def test_command_alias_same_as_commandtest(self):
    for mode in ["comport", "tcpip", "console", "android_adb", "PEAK", "custom"]:
        assert mode in MEASUREMENT_TEMPLATES["command"]
        ct_required = MEASUREMENT_TEMPLATES["CommandTest"][mode]["required"]
        cmd_required = MEASUREMENT_TEMPLATES["command"][mode]["required"]
        assert ct_required == cmd_required, f"Mode '{mode}' required params differ: ..."
```

---

## 測試結構

測試檔案：`backend/tests/test_config/test_instruments_templates.py`

```
TestCommandTestTemplates       — 11 tests
  CommandTest/command 模板存在性與必要參數、alias 完整性

TestAndroidAdbPeakTopLevel     — 9 tests
  android_adb/PEAK 頂層類型存在性、custom mode、validate_params

TestSFCtestGetSNModes          — 9 tests
  SFCtest/getSN 顯式 switch_mode 存在與無參數驗證

TestWaitAndOtherModes          — 7 tests
  wait 小寫頂層類型、Other test123/WAIT_FIX_5sec

TestValidateParamsEndToEnd     — 6 tests (regression)
  確認各類型走主要路徑（不觸發 Legacy 提示）
```

執行方式：
```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py -v
```

---

## 遷移後的架構狀態

```
validate_params(measurement_type, switch_mode, params)
    │
    ├─ validate_params_config()  ← 讀 MEASUREMENT_TEMPLATES
    │   ├─ 找到模板 → 直接回傳結果（主要路徑）
    │   └─ 未找到 → 回傳 "Unsupported combination"
    │
    └─ (若 "Unsupported combination") → validation_rules fallback
        ├─ PowerSet: {}          (空，已遷移)
        ├─ PowerRead: {}         (空，已遷移)
        ├─ OPjudge: {...}        (保留為雙重保障)
        └─ # 其他全部已注解
```

**MEASUREMENT_TEMPLATES 完整覆蓋範圍（遷移後）：**

```
PowerSet     — DAQ973A, MODEL2303, MODEL2306, IT6723C, PSW3072, 2260B, APS7050, KEITHLEY2015, 34970A
PowerRead    — DAQ973A, 34970A, KEITHLEY2015, 2015, 6510, APS7050, MDO34, MT8870A_INF
SFCtest      — default, webStep1_2, URLStep1_2, skip, WAIT_FIX_5sec
getSN        — default, SN, IMEI, MAC
OPjudge      — confirm, YorN
Other        — script, wait, relay, chassis_rotation, console, comport, tcpip, test123, WAIT_FIX_5sec
Wait         — default
Relay        — default
wait         — wait
comport      — comport
console      — console
tcpip        — tcpip
CommandTest  — comport, tcpip, console, android_adb, PEAK, custom
command      — （同 CommandTest）
android_adb  — android_adb, custom
PEAK         — PEAK, custom
```

---

## 注意事項

1. **`spiltCount` 拼字為 PDTool4 原始命名**（非 `splitCount`），遷移時保持原樣以維持相容性。
2. **`has_parameter()` 不可移除**：`measurement_service.py` 中的執行期自訂腳本判斷邏輯不是靜態規則，template 無法取代。
3. **`OPjudge` 後備保留**：雖然主要路徑已有模板，後備字典中的 `OPjudge` 保留作雙重保障。
