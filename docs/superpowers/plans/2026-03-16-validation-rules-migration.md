# Validation Rules Migration to MEASUREMENT_TEMPLATES Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all remaining hardcoded `validation_rules` entries in `measurement_service.py` into `MEASUREMENT_TEMPLATES` in `instruments.py`, then remove the now-redundant entries from the legacy fallback dict.

**Architecture:** The `validate_params()` method in `measurement_service.py` uses a two-tier strategy — primary path via `validate_params_config()` (reads `MEASUREMENT_TEMPLATES`) and a legacy fallback for "Unsupported combination" cases. Migrating entries to `MEASUREMENT_TEMPLATES` causes them to be handled by the primary path automatically; the fallback dict entries become dead code and can be emptied/commented out.

**Tech Stack:** Python, FastAPI backend — `backend/app/config/instruments.py`, `backend/app/services/measurement_service.py`, pytest

---

## Chunk 1: Audit and add missing MEASUREMENT_TEMPLATES entries

### Task 1: Add CommandTest / command unified templates

**Files:**
- Modify: `backend/app/config/instruments.py` (MEASUREMENT_TEMPLATES dict)

**What to add:** `CommandTest` and `command` as top-level keys with sub-modes: `comport`, `tcpip`, `console`, `android_adb`, `PEAK`, `custom`. These use the original PDTool4 schema (`Port`/`Baud`/`Command` for comport, etc.) — different from the newer `comport`/`console`/`tcpip` top-level keys that use `Instrument`/`Command`.

- [ ] **Step 1: Write failing test for CommandTest template lookup**

In `backend/tests/test_services/test_opjudge_measurement.py` OR create a new file:
`backend/tests/test_config/test_instruments_templates.py`

```python
# backend/tests/test_config/test_instruments_templates.py
import pytest
from app.config.instruments import MEASUREMENT_TEMPLATES, validate_params, get_template


class TestCommandTestTemplates:
    def test_commandtest_comport_template_exists(self):
        assert "CommandTest" in MEASUREMENT_TEMPLATES
        assert "comport" in MEASUREMENT_TEMPLATES["CommandTest"]

    def test_commandtest_comport_required_params(self):
        tmpl = get_template("CommandTest", "comport")
        assert tmpl is not None
        assert set(["Port", "Baud", "Command"]).issubset(set(tmpl["required"]))

    def test_commandtest_tcpip_required_params(self):
        tmpl = get_template("CommandTest", "tcpip")
        assert tmpl is not None
        assert set(["Host", "Port", "Command"]).issubset(set(tmpl["required"]))

    def test_commandtest_console_required_params(self):
        tmpl = get_template("CommandTest", "console")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_commandtest_android_adb_required_params(self):
        tmpl = get_template("CommandTest", "android_adb")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_commandtest_peak_required_params(self):
        tmpl = get_template("CommandTest", "PEAK")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_commandtest_custom_no_required(self):
        tmpl = get_template("CommandTest", "custom")
        assert tmpl is not None
        # custom mode — command is optional, script_path is optional
        assert tmpl["required"] == [] or "command" not in tmpl["required"]

    def test_command_alias_same_as_commandtest(self):
        """'command' measurement_type should mirror CommandTest modes."""
        assert "command" in MEASUREMENT_TEMPLATES
        for mode in ["comport", "tcpip", "console", "android_adb", "PEAK", "custom"]:
            assert mode in MEASUREMENT_TEMPLATES["command"], f"Missing mode: {mode}"

    def test_validate_params_commandtest_comport_valid(self):
        result = validate_params("CommandTest", "comport", {
            "Port": "COM4", "Baud": "9600", "Command": "AT+VERSION"
        })
        assert result["valid"] is True

    def test_validate_params_commandtest_comport_missing(self):
        result = validate_params("CommandTest", "comport", {"Port": "COM4"})
        assert result["valid"] is False
        assert "Baud" in result["missing_params"] or "Command" in result["missing_params"]

    def test_validate_params_command_tcpip_valid(self):
        result = validate_params("command", "tcpip", {
            "Host": "192.168.1.1", "Port": "5025", "Command": "*IDN?"
        })
        assert result["valid"] is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestCommandTestTemplates -v 2>&1 | head -40
```
Expected: FAIL — `CommandTest` not in `MEASUREMENT_TEMPLATES`

- [ ] **Step 3: Add CommandTest and command to MEASUREMENT_TEMPLATES**

In `backend/app/config/instruments.py`, after the `"tcpip"` block (around line 394), add:

```python
    # 新增: CommandTest — PDTool4 舊式格式 (Port/Baud/Command schema)
    # 注意: 與頂層 "comport"/"console"/"tcpip" key 不同，此格式不使用 Instrument 欄位
    "CommandTest": {
        "comport": {
            "required": ["Port", "Baud", "Command"],
            "optional": ["keyWord", "spiltCount", "splitLength", "EqLimit", "Timeout"],
            "example": {
                "Port": "COM4",
                "Baud": "9600",
                "Command": "AT+VERSION",
                "keyWord": "VERSION",
                "spiltCount": "1",
                "splitLength": "10"
            }
        },
        "tcpip": {
            "required": ["Host", "Port", "Command"],
            "optional": ["keyWord", "spiltCount", "splitLength", "Timeout"],
            "example": {
                "Host": "192.168.1.100",
                "Port": "5025",
                "Command": "*IDN?",
                "Timeout": "5"
            }
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
            # 自定義腳本模式: command 或 script_path 任一即可，無強制 required
            "required": [],
            "optional": ["command", "script_path"],
            "example": {"command": "python3 custom_script.py"}
        }
    },
    # 新增: "command" — CommandTest 的別名，對應 case_type='command' 的測試計畫
    "command": {
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
```

Also add to `MEASUREMENT_TYPE_DESCRIPTIONS`:

```python
    "CommandTest": {
        "name": "CommandTest",
        "description": "PDTool4-compatible command execution (comport/tcpip/console/adb/PEAK)",
        "category": "communication"
    },
    "command": {
        "name": "command",
        "description": "Alias for CommandTest (case_type='command')",
        "category": "communication"
    },
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestCommandTestTemplates -v
```
Expected: All PASS

---

### Task 2: Add android_adb and PEAK as top-level measurement types

**Files:**
- Modify: `backend/app/config/instruments.py`
- Modify: `backend/tests/test_config/test_instruments_templates.py`

- [ ] **Step 1: Write failing tests**

Append to `backend/tests/test_config/test_instruments_templates.py`:

```python
class TestAndroidAdbPeakTopLevel:
    def test_android_adb_top_level_exists(self):
        assert "android_adb" in MEASUREMENT_TEMPLATES

    def test_android_adb_mode_required(self):
        tmpl = get_template("android_adb", "android_adb")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_android_adb_validate_valid(self):
        result = validate_params("android_adb", "android_adb", {"Command": "adb shell ls"})
        assert result["valid"] is True

    def test_android_adb_validate_missing_command(self):
        result = validate_params("android_adb", "android_adb", {})
        assert result["valid"] is False

    def test_peak_top_level_exists(self):
        assert "PEAK" in MEASUREMENT_TEMPLATES

    def test_peak_mode_required(self):
        tmpl = get_template("PEAK", "PEAK")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_peak_validate_valid(self):
        result = validate_params("PEAK", "PEAK", {"Command": "send:0x01"})
        assert result["valid"] is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestAndroidAdbPeakTopLevel -v 2>&1 | head -30
```
Expected: FAIL

- [ ] **Step 3: Add android_adb and PEAK to MEASUREMENT_TEMPLATES**

In `backend/app/config/instruments.py`, append after the `"command"` block:

```python
    # 新增: android_adb — 作為頂層 measurement_type
    "android_adb": {
        "android_adb": {
            "required": ["Command"],
            "optional": ["Timeout", "serial"],
            "example": {"Command": "adb shell getprop ro.serialno"}
        },
        "custom": {
            "required": [],
            "optional": ["command", "script_path"],
            "example": {"command": "python3 custom_adb.py"}
        }
    },
    # 新增: PEAK — 作為頂層 measurement_type (對應 PEAK CAN 控制)
    "PEAK": {
        "PEAK": {
            "required": ["Command"],
            "optional": ["Timeout", "channel"],
            "example": {"Command": "send:0x01:0x02"}
        },
        "custom": {
            "required": [],
            "optional": ["command", "script_path"],
            "example": {"command": "python3 custom_peak.py"}
        }
    },
```

Also add to `MEASUREMENT_TYPE_DESCRIPTIONS`:

```python
    "android_adb": {
        "name": "android_adb",
        "description": "Android ADB command execution",
        "category": "communication"
    },
    "PEAK": {
        "name": "PEAK",
        "description": "PEAK CAN bus command execution",
        "category": "communication"
    },
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestAndroidAdbPeakTopLevel -v
```
Expected: All PASS

---

### Task 3: Add SFCtest explicit switch modes and getSN explicit modes

**Files:**
- Modify: `backend/app/config/instruments.py`
- Modify: `backend/tests/test_config/test_instruments_templates.py`

Currently `SFCtest` has only `"default"` mode. The validation_rules has `webStep1_2`, `URLStep1_2`, `skip`, `WAIT_FIX_5sec`. `getSN` has `"default"` mode; validation_rules has `SN`, `IMEI`, `MAC`.

- [ ] **Step 1: Write failing tests**

Append to `backend/tests/test_config/test_instruments_templates.py`:

```python
class TestSFCtestGetSNModes:
    def test_sfctest_webstep_mode_exists(self):
        assert "webStep1_2" in MEASUREMENT_TEMPLATES["SFCtest"]

    def test_sfctest_urlstep_mode_exists(self):
        assert "URLStep1_2" in MEASUREMENT_TEMPLATES["SFCtest"]

    def test_sfctest_skip_mode_exists(self):
        assert "skip" in MEASUREMENT_TEMPLATES["SFCtest"]

    def test_sfctest_wait_fix_mode_exists(self):
        assert "WAIT_FIX_5sec" in MEASUREMENT_TEMPLATES["SFCtest"]

    def test_sfctest_webstep_validate_no_required(self):
        result = validate_params("SFCtest", "webStep1_2", {})
        assert result["valid"] is True

    def test_getsn_sn_mode_exists(self):
        assert "SN" in MEASUREMENT_TEMPLATES["getSN"]

    def test_getsn_imei_mode_exists(self):
        assert "IMEI" in MEASUREMENT_TEMPLATES["getSN"]

    def test_getsn_mac_mode_exists(self):
        assert "MAC" in MEASUREMENT_TEMPLATES["getSN"]

    def test_getsn_sn_validate_no_required(self):
        result = validate_params("getSN", "SN", {})
        assert result["valid"] is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestSFCtestGetSNModes -v 2>&1 | head -30
```
Expected: FAIL

- [ ] **Step 3: Update SFCtest and getSN in MEASUREMENT_TEMPLATES**

In `backend/app/config/instruments.py`, replace the existing `SFCtest` entry:

```python
    # 原有程式碼: 只有 "default" mode
    # 修正: 新增 PDTool4 validation_rules 中的所有 switch_mode
    "SFCtest": {
        "default": {
            "required": ["Mode"],
            "optional": [],
            "example": {"Mode": "webStep1_2"}
        },
        "webStep1_2": {
            "required": [],
            "optional": [],
            "example": {}
        },
        "URLStep1_2": {
            "required": [],
            "optional": [],
            "example": {}
        },
        "skip": {
            "required": [],
            "optional": [],
            "example": {}
        },
        "WAIT_FIX_5sec": {
            "required": [],
            "optional": [],
            "example": {}
        }
    },
```

Replace the existing `getSN` entry:

```python
    # 原有程式碼: 只有 "default" mode
    # 修正: 新增 PDTool4 validation_rules 中的所有 switch_mode
    "getSN": {
        "default": {
            "required": ["Type"],
            "optional": ["SerialNumber"],
            "example": {"Type": "SN"}
        },
        "SN": {
            "required": [],
            "optional": ["SerialNumber"],
            "example": {}
        },
        "IMEI": {
            "required": [],
            "optional": [],
            "example": {}
        },
        "MAC": {
            "required": [],
            "optional": [],
            "example": {}
        }
    },
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestSFCtestGetSNModes -v
```
Expected: All PASS

---

### Task 4: Add wait (lowercase) and Other missing switch modes

**Files:**
- Modify: `backend/app/config/instruments.py`
- Modify: `backend/tests/test_config/test_instruments_templates.py`

Missing: `wait` top-level type (lowercase), `Other` switch modes `test123` and `WAIT_FIX_5sec`.

- [ ] **Step 1: Write failing tests**

Append to `backend/tests/test_config/test_instruments_templates.py`:

```python
class TestWaitAndOtherModes:
    def test_wait_lowercase_top_level_exists(self):
        assert "wait" in MEASUREMENT_TEMPLATES

    def test_wait_lowercase_mode_exists(self):
        assert "wait" in MEASUREMENT_TEMPLATES["wait"]

    def test_wait_lowercase_validate_no_required(self):
        result = validate_params("wait", "wait", {})
        assert result["valid"] is True

    def test_other_test123_mode_exists(self):
        assert "test123" in MEASUREMENT_TEMPLATES["Other"]

    def test_other_wait_fix_mode_exists(self):
        assert "WAIT_FIX_5sec" in MEASUREMENT_TEMPLATES["Other"]

    def test_other_test123_validate_no_required(self):
        result = validate_params("Other", "test123", {})
        assert result["valid"] is True

    def test_other_wait_fix_validate_no_required(self):
        result = validate_params("Other", "WAIT_FIX_5sec", {})
        assert result["valid"] is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestWaitAndOtherModes -v 2>&1 | head -30
```
Expected: FAIL

- [ ] **Step 3: Add wait (lowercase) top-level and Other missing modes**

In `backend/app/config/instruments.py`, add `wait` (lowercase) after the `Wait` block:

```python
    # 新增: "wait" (小寫) — 對應 validation_rules 中的 wait/Wait 型別
    # Wait (大寫) 已有 "default" mode，此處補充小寫別名
    "wait": {
        "wait": {
            "required": [],
            "optional": ["wait_msec", "WaitmSec"],
            "example": {"wait_msec": "1000"}
        }
    },
```

Also add to `MEASUREMENT_TYPE_DESCRIPTIONS`:

```python
    "wait": {
        "name": "wait",
        "description": "Wait/delay operation (lowercase alias for Wait)",
        "category": "utility"
    },
```

Update the existing `Other` block to add `test123` and `WAIT_FIX_5sec` modes:

```python
        # 原有程式碼: 以下 switch_mode 已存在: script, wait, relay, chassis_rotation, console, comport, tcpip
        # 新增: test123 和 WAIT_FIX_5sec (來自 validation_rules 遷移)
        "test123": {
            "required": [],
            "optional": ["arg"],
            "example": {"arg": "optional_argument"}
        },
        "WAIT_FIX_5sec": {
            "required": [],
            "optional": [],
            "example": {}
        },
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestWaitAndOtherModes -v
```
Expected: All PASS

- [ ] **Step 5: Run all new tests together**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py -v
```
Expected: All PASS

- [ ] **Step 6: Commit Chunk 1**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/config/instruments.py backend/tests/test_config/test_instruments_templates.py
git commit -m "feat: migrate CommandTest/command/android_adb/PEAK/SFCtest/getSN/wait/Other to MEASUREMENT_TEMPLATES"
```

---

## Chunk 2: Clean up legacy validation_rules in measurement_service.py

### Task 5: Comment out migrated entries from validation_rules fallback dict

**Files:**
- Modify: `backend/app/services/measurement_service.py` (lines ~689–787, the `validation_rules` dict)

**Goal:** Comment out all entries that are now covered by `MEASUREMENT_TEMPLATES`. Keep only entries that have no equivalent in `MEASUREMENT_TEMPLATES` or that have special runtime logic not expressible in templates (e.g., the custom switch_mode handling for CommandTest types which checks for `command`/`script_path` at runtime).

**Entries to comment out (now covered by MEASUREMENT_TEMPLATES):**
- `CommandTest` dict — entire block
- `command` dict — entire block
- `comport` dict — entire block (already in MEASUREMENT_TEMPLATES as top-level)
- `console` dict — entire block
- `tcpip` dict — entire block
- `android_adb` dict — entire block
- `PEAK` dict — entire block
- `SFCtest` — switch modes webStep1_2/URLStep1_2/skip/WAIT_FIX_5sec (keep dict shell since `default` still routes through legacy)
- `getSN` — switch modes SN/IMEI/MAC
- `wait` / `Wait` — both dicts
- `Other` — test123, WAIT_FIX_5sec, wait modes

**Keep as-is (no MEASUREMENT_TEMPLATES equivalent or special logic):**
- The runtime `has_parameter()` check logic for custom switch_mode (lines ~799–829) — this is runtime behavior, not just a template
- `OPjudge` — already migrated and noted, keep the comment explaining it's a fallback

- [ ] **Step 1: Write regression test confirming validate_params still works after cleanup**

Append to `backend/tests/test_config/test_instruments_templates.py`:

```python
class TestValidateParamsEndToEnd:
    """Regression tests: validate_params() in MeasurementService should use primary path for migrated types."""

    def test_service_commandtest_uses_primary_path(self):
        """CommandTest/comport should be validated via MEASUREMENT_TEMPLATES primary path."""
        from app.config.instruments import validate_params
        result = validate_params("CommandTest", "comport", {
            "Port": "COM4", "Baud": "9600", "Command": "AT"
        })
        assert result["valid"] is True
        # Should NOT say "Legacy validation used"
        assert not any("Legacy" in s for s in result.get("suggestions", []))

    def test_service_sfctest_webstep_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("SFCtest", "webStep1_2", {})
        assert result["valid"] is True
        assert not any("Legacy" in s for s in result.get("suggestions", []))

    def test_service_getsn_sn_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("getSN", "SN", {})
        assert result["valid"] is True

    def test_service_wait_lowercase_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("wait", "wait", {})
        assert result["valid"] is True

    def test_service_android_adb_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("android_adb", "android_adb", {"Command": "adb shell ls"})
        assert result["valid"] is True

    def test_service_peak_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("PEAK", "PEAK", {"Command": "send:0x01"})
        assert result["valid"] is True
```

- [ ] **Step 2: Run to verify all pass (they should — this tests MEASUREMENT_TEMPLATES directly)**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/test_config/test_instruments_templates.py::TestValidateParamsEndToEnd -v
```
Expected: All PASS (confirming primary path works before touching fallback)

- [ ] **Step 3: Comment out migrated validation_rules entries in measurement_service.py**

In `backend/app/services/measurement_service.py`, in the `validate_params()` method, update the `validation_rules` dict.

Replace:
```python
        validation_rules = {
            # ... PowerSet/PowerRead already empty ...
            "PowerSet": {},
            "PowerRead": {},
            "CommandTest": {
                "comport": ["Port", "Baud", "Command"],
                ...
            },
            "command": { ... },
            "comport": { ... },
            "console": { ... },
            "tcpip": { ... },
            "android_adb": { ... },
            "PEAK": { ... },
            "SFCtest": { ... },
            "getSN": { ... },
            "OPjudge": { ... },
            "wait": { ... },
            "Wait": { ... },
            "Other": { ... },
        }
```

With (comment out migrated, keep special-logic entries):
```python
        # 後備驗證規則字典 (legacy fallback)
        # 以下條目已遷移到 MEASUREMENT_TEMPLATES (2026-03-16)，保留為歷史記錄
        # 任何列於此處的類型，若已在 MEASUREMENT_TEMPLATES 中，主要路徑 (validate_params_config) 會優先處理
        validation_rules = {
            "PowerSet": {},   # 已遷移 (2026-03-16)
            "PowerRead": {},  # 已遷移 (2026-03-16)

            # 原有程式碼: CommandTest / command 硬編碼驗證
            # 已遷移到 MEASUREMENT_TEMPLATES (2026-03-16)
            # "CommandTest": { "comport": [...], "tcpip": [...], "console": [...],
            #                  "android_adb": [...], "PEAK": [...], "custom": [...] },
            # "command": { ... },  # CommandTest 的別名

            # 原有程式碼: comport/console/tcpip/android_adb/PEAK 作為頂層 measurement_type
            # 已遷移到 MEASUREMENT_TEMPLATES (2026-03-16)
            # "comport": { "comport": [...], "custom": [...] },
            # "console": { "console": [...], "custom": [...] },
            # "tcpip": { "tcpip": [...], "custom": [...] },
            # "android_adb": { "android_adb": [...], "custom": [...] },
            # "PEAK": { "PEAK": [...], "custom": [...] },

            # 原有程式碼: SFCtest 顯式 switch_mode 已遷移到 MEASUREMENT_TEMPLATES (2026-03-16)
            # "SFCtest": { "webStep1_2": [], "URLStep1_2": [], "skip": [], "WAIT_FIX_5sec": [] },

            # 原有程式碼: getSN 顯式 switch_mode 已遷移到 MEASUREMENT_TEMPLATES (2026-03-16)
            # "getSN": {"SN": [], "IMEI": [], "MAC": []},

            # OPjudge: 已在 MEASUREMENT_TEMPLATES 中，此為後備說明
            # 通常由 validate_params_config (primary path) 先行處理
            "OPjudge": {
                "YorN": ["ImagePath", "content"],
                "confirm": ["ImagePath", "content"],
            },

            # 原有程式碼: wait/Wait 已遷移到 MEASUREMENT_TEMPLATES (2026-03-16)
            # "wait": {"wait": []},
            # "Wait": {"wait": []},

            # 原有程式碼: Other test123/WAIT_FIX_5sec/wait modes 已遷移到 MEASUREMENT_TEMPLATES (2026-03-16)
            # "Other": { "test123": [], "custom": [], "WAIT_FIX_5sec": [], "wait": [] },
        }
```

- [ ] **Step 4: Run full test suite to catch regressions**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/ -v --tb=short 2>&1 | tail -30
```
Expected: All previously passing tests still PASS

- [ ] **Step 5: Verify validate_params service method still handles custom switch_mode logic**

The runtime `has_parameter()` checks for unknown switch_modes in CommandTest types (lines ~797–829) are **NOT** removed — they handle the runtime case where a custom switch_mode (not in templates) needs `command` or `script_path`. Confirm this code block is still present:

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
grep -n "has_parameter" app/services/measurement_service.py | head -10
```
Expected: Lines still present in the file

- [ ] **Step 6: Commit Chunk 2**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add backend/app/services/measurement_service.py backend/tests/test_config/test_instruments_templates.py
git commit -m "refactor: comment out migrated validation_rules entries now covered by MEASUREMENT_TEMPLATES"
```

---

## Final Verification

- [ ] **Run complete backend test suite**

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run pytest tests/ -v --tb=short 2>&1 | tail -40
```
Expected: All tests PASS, no regressions

- [ ] **Verify MEASUREMENT_TEMPLATES coverage**

Manually confirm these keys exist in `MEASUREMENT_TEMPLATES`:
```
PowerSet, PowerRead, SFCtest (+ webStep1_2/URLStep1_2/skip/WAIT_FIX_5sec),
getSN (+ SN/IMEI/MAC), OPjudge, Other (+ test123/WAIT_FIX_5sec),
Wait, Relay, wait, comport, console, tcpip,
CommandTest (+ comport/tcpip/console/android_adb/PEAK/custom),
command (+ same modes), android_adb, PEAK
```
