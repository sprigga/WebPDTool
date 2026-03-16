# Power Measurement Templates Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate missing PowerSet and PowerRead instrument validation rules from the legacy `validation_rules` dictionary in `measurement_service.py` to `MEASUREMENT_TEMPLATES` in `instruments.py`, then remove the migrated entries from the legacy dict.

**Architecture:** The `MeasurementService.validate_params()` method has two validation paths:
1. **Primary path:** `validate_params_config()` from `instruments.py` (uses `MEASUREMENT_TEMPLATES`)
2. **Fallback path:** Hardcoded `validation_rules` dict (for backwards compatibility)

Currently, `MEASUREMENT_TEMPLATES` has partial coverage of PowerSet/PowerRead instruments. The legacy dict has **additional instruments** not in MEASUREMENT_TEMPLATES:
- PowerSet: IT6723C, PSW3072, 2260B, APS7050, KEITHLEY2015
- PowerRead: 2015, 6510, APS7050, MDO34, MT8870A_INF, KEITHLEY2015

This migration consolidates all instrument rules into `MEASUREMENT_TEMPLATES`, making the legacy dict truly a fallback for unmigrated types only.

**Tech Stack:** Python 3.11+, pytest, FastAPI, SQLAlchemy

---
## Chunk 1: Add Missing PowerSet Instruments to MEASUREMENT_TEMPLATES

### Task 1: Add IT6723C PowerSet Template

**Files:**
- Modify: `backend/app/config/instruments.py:75-76`

- [ ] **Step 1: Add IT6723C PowerSet template after MODEL2306**

```python
MEASUREMENT_TEMPLATES = {
    "PowerSet": {
        # ... existing entries (DAQ973A, MODEL2303, MODEL2306) ...
        "IT6723C": {
            "required": ["Instrument", "SetVolt", "SetCurr"],
            "optional": ["OVP", "OCP"],
            "example": {
                "Instrument": "it6723c_1",
                "SetVolt": "5.0",
                "SetCurr": "2.0"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

### Task 2: Add PSW3072 PowerSet Template

**Files:**
- Modify: `backend/app/config/instruments.py:84`

- [ ] **Step 1: Add PSW3072 PowerSet template after IT6723C**

```python
        "PSW3072": {
            "required": ["Instrument", "SetVolt", "SetCurr"],
            "optional": ["OVP", "OCP"],
            "example": {
                "Instrument": "psw3072_1",
                "SetVolt": "12.0",
                "SetCurr": "1.0"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

### Task 3: Add 2260B PowerSet Template

**Files:**
- Modify: `backend/app/config/instruments.py:92`

- [ ] **Step 1: Add 2260B PowerSet template after PSW3072**

```python
        "2260B": {
            "required": ["Instrument", "SetVolt", "SetCurr"],
            "optional": ["Frequency"],
            "example": {
                "Instrument": "2260b_1",
                "SetVolt": "5.0",
                "SetCurr": "0.5"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

### Task 4: Add APS7050 PowerSet Template

**Files:**
- Modify: `backend/app/config/instruments.py:100`

- [ ] **Step 1: Add APS7050 PowerSet template after 2260B**

```python
        "APS7050": {
            "required": ["Instrument", "Channel", "SetVolt", "SetCurr"],
            "optional": ["OVP", "OCP"],
            "example": {
                "Instrument": "aps7050_1",
                "Channel": "1",
                "SetVolt": "5.0",
                "SetCurr": "1.0"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

### Task 5: Add KEITHLEY2015 PowerSet Template

**Files:**
- Modify: `backend/app/config/instruments.py:109`

- [ ] **Step 1: Add KEITHLEY2015 PowerSet template after APS7050**

```python
        "KEITHLEY2015": {
            "required": ["Instrument", "Command"],
            "optional": ["Range", "NPLC"],
            "example": {
                "Instrument": "keithley2015_1",
                "Command": "SOURCE:VOLTAGE 5.0"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

- [ ] **Step 3: Commit PowerSet templates**

```bash
git add backend/app/config/instruments.py
git commit -m "feat: add IT6723C, PSW3072, 2260B, APS7050, KEITHLEY2015 to PowerSet MEASUREMENT_TEMPLATES"
```

---
## Chunk 2: Add Missing PowerRead Instruments to MEASUREMENT_TEMPLATES

### Task 6: Add 2015 PowerRead Template

**Files:**
- Modify: `backend/app/config/instruments.py:131`

- [ ] **Step 1: Add 2015 PowerRead template after KEITHLEY2015**

```python
    "PowerRead": {
        # ... existing entries (DAQ973A, 34970A, KEITHLEY2015) ...
        "2015": {
            "required": ["Instrument", "Command"],
            "optional": ["Range", "NPLC"],
            "example": {
                "Instrument": "2015_1",
                "Command": "MEASURE:VOLTAGE?"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

### Task 7: Add 6510 PowerRead Template

**Files:**
- Modify: `backend/app/config/instruments.py:139`

- [ ] **Step 1: Add 6510 PowerRead template after 2015**

```python
        "6510": {
            "required": ["Instrument", "Item"],
            "optional": ["Range", "NPLC"],
            "example": {
                "Instrument": "daq6510_1",
                "Item": "volt"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

### Task 8: Add APS7050 PowerRead Template

**Files:**
- Modify: `backend/app/config/instruments.py:147`

- [ ] **Step 1: Add APS7050 PowerRead template after 6510**

```python
        "APS7050": {
            "required": ["Instrument", "Item"],
            "optional": ["Range"],
            "example": {
                "Instrument": "aps7050_1",
                "Item": "current"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

### Task 9: Add MDO34 PowerRead Template

**Files:**
- Modify: `backend/app/config/instruments.py:155`

- [ ] **Step 1: Add MDO34 PowerRead template after APS7050**

```python
        "MDO34": {
            "required": ["Instrument", "Channel", "Item"],
            "optional": ["Range"],
            "example": {
                "Instrument": "mdo34_1",
                "Channel": "1",
                "Item": "volt"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

### Task 10: Add MT8870A_INF PowerRead Template

**Files:**
- Modify: `backend/app/config/instruments.py:164`

- [ ] **Step 1: Add MT8870A_INF PowerRead template after MDO34**

```python
        "MT8870A_INF": {
            "required": ["Instrument", "Item"],
            "optional": ["Range"],
            "example": {
                "Instrument": "mt8870a_1",
                "Item": "power"
            }
        },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/config/instruments.py`
Expected: No syntax errors (exit code 0)

- [ ] **Step 3: Commit PowerRead templates**

```bash
git add backend/app/config/instruments.py
git commit -m "feat: add 2015, 6510, APS7050, MDO34, MT8870A_INF to PowerRead MEASUREMENT_TEMPLATES"
```

---
## Chunk 3: Update MEASUREMENT_TYPE_DESCRIPTIONS

### Task 11: Add Descriptions for New Instruments (if needed)

**Files:**
- Modify: `backend/app/config/instruments.py:16-41` (AVAILABLE_INSTRUMENTS section)
- Modify: `backend/app/config/instruments.py:303-366` (MEASUREMENT_TYPE_DESCRIPTIONS section)

**Note:** AVAILABLE_INSTRUMENTS already contains IT6723C, PSW3072, 2260B, APS7050. Verify these exist.

- [ ] **Step 1: Verify AVAILABLE_INSTRUMENTS has all new instruments**

Check that the following exist in AVAILABLE_INSTRUMENTS:
- IT6723C (in power_supplies)
- PSW3072 (in power_supplies)
- 2260B (in power_supplies)
- APS7050 (in power_supplies)
- 6510 (in multimeters)
- MDO34 (in rf_analyzers)
- MT8870A (in rf_analyzers)

If any are missing, add them following the existing pattern.

- [ ] **Step 2: Verify MEASUREMENT_TYPE_DESCRIPTIONS entries exist**

The PowerSet and PowerRead descriptions already exist. No changes needed here.

- [ ] **Step 3: Verify and commit if changes made**

Run: `python3 -m py_compile backend/app/config/instruments.py`
If changes were made:
```bash
git add backend/app/config/instruments.py
git commit -m "docs: ensure AVAILABLE_INSTRUMENTS includes all migrated PowerSet/PowerRead devices"
```

---
## Chunk 4: Remove Migrated Entries from Legacy validation_rules

### Task 12: Remove PowerSet Entries from Legacy Dict

**Files:**
- Modify: `backend/app/services/measurement_service.py:689-700`

- [ ] **Step 1: Comment out migrated PowerSet instruments**

Replace lines 689-700 with:

```python
        # 原有程式碼: IT6723C, PSW3072, 2260B, APS7050, KEITHLEY2015 已遷移到 MEASUREMENT_TEMPLATES
        # 保留此處註解以記錄遷移日期
        # "PowerSet": {
        #     "DAQ973A": ["Instrument", "Channel", "Item"],      # 已在 MEASUREMENT_TEMPLATES
        #     "MODEL2303": ["Instrument", "SetVolt", "SetCurr"],  # 已在 MEASUREMENT_TEMPLATES
        #     "MODEL2306": ["Instrument", "Channel", "SetVolt", "SetCurr"],  # 已在 MEASUREMENT_TEMPLATES
        #     "IT6723C": ["Instrument", "SetVolt", "SetCurr"],    # 已遷移 (2026-03-16)
        #     "PSW3072": ["Instrument", "SetVolt", "SetCurr"],    # 已遷移 (2026-03-16)
        #     "2260B": ["Instrument", "SetVolt", "SetCurr"],      # 已遷移 (2026-03-16)
        #     "APS7050": ["Instrument", "Channel", "SetVolt", "SetCurr"],  # 已遷移 (2026-03-16)
        #     "34970A": ["Instrument", "Channel", "Item"],        # 已在 MEASUREMENT_TEMPLATES
        #     "KEITHLEY2015": ["Instrument", "Command"],          # 已遷移 (2026-03-16)
        # },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/services/measurement_service.py`
Expected: No syntax errors (exit code 0)

### Task 13: Remove PowerRead Entries from Legacy Dict

**Files:**
- Modify: `backend/app/services/measurement_service.py:701-710`

- [ ] **Step 1: Comment out migrated PowerRead instruments**

Replace lines 701-710 with:

```python
        # 原有程式碼: 2015, 6510, APS7050, MDO34, MT8870A_INF, KEITHLEY2015 已遷移到 MEASUREMENT_TEMPLATES
        # 保留此處註解以記錄遷移日期
        # "PowerRead": {
        #     "DAQ973A": ["Instrument", "Channel", "Item", "Type"],  # 已在 MEASUREMENT_TEMPLATES
        #     "34970A": ["Instrument", "Channel", "Item"],           # 已在 MEASUREMENT_TEMPLATES
        #     "2015": ["Instrument", "Command"],                    # 已遷移 (2026-03-16)
        #     "6510": ["Instrument", "Item"],                       # 已遷移 (2026-03-16)
        #     "APS7050": ["Instrument", "Item"],                    # 已遷移 (2026-03-16)
        #     "MDO34": ["Instrument", "Channel", "Item"],           # 已遷移 (2026-03-16)
        #     "MT8870A_INF": ["Instrument", "Item"],                # 已遷移 (2026-03-16)
        #     "KEITHLEY2015": ["Instrument", "Command"],            # 已遷移 (2026-03-16)
        # },
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -m py_compile backend/app/services/measurement_service.py`
Expected: No syntax errors (exit code 0)

- [ ] **Step 3: Commit legacy dict removal**

```bash
git add backend/app/services/measurement_service.py
git commit -m "refactor: remove migrated PowerSet/PowerRead entries from legacy validation_rules"
```

---
## Chunk 5: Add Validation Tests

### Task 14: Test validate_params_config with New Instruments

**Files:**
- Create: `backend/tests/test_config/test_power_templates_validation.py`

- [ ] **Step 1: Write test file**

```python
"""
Test PowerSet and PowerRead validation rules in MEASUREMENT_TEMPLATES.
Ensures all migrated instruments validate correctly via validate_params_config().
"""
import pytest
from app.config.instruments import validate_params, MEASUREMENT_TEMPLATES


class TestPowerSetTemplates:
    """Test PowerSet MEASUREMENT_TEMPLATES validation."""

    @pytest.mark.parametrize("instrument", [
        "DAQ973A", "MODEL2303", "MODEL2306", "IT6723C", "PSW3072",
        "2260B", "APS7050", "34970A", "KEITHLEY2015"
    ])
    def test_powerset_instrument_exists(self, instrument):
        """All PowerSet instruments should exist in MEASUREMENT_TEMPLATES."""
        assert "PowerSet" in MEASUREMENT_TEMPLATES
        assert instrument in MEASUREMENT_TEMPLATES["PowerSet"]

    def test_powerset_daq973a_valid_params(self):
        """DAQ973A PowerSet requires Instrument, Channel, Item."""
        result = validate_params("PowerSet", "DAQ973A", {
            "Instrument": "daq973a_1",
            "Channel": "101",
            "Item": "volt"
        })
        assert result["valid"] is True
        assert result["missing_params"] == []

    def test_powerset_daq973a_missing_required(self):
        """DAQ973A PowerSet with missing Channel should fail."""
        result = validate_params("PowerSet", "DAQ973A", {
            "Instrument": "daq973a_1",
            "Item": "volt"
        })
        assert result["valid"] is False
        assert "Channel" in result["missing_params"]

    @pytest.mark.parametrize("instrument", [
        "IT6723C", "PSW3072", "2260B"
    ])
    def test_powerset_volt_curr_instruments(self, instrument):
        """IT6723C, PSW3072, 2260B require Instrument, SetVolt, SetCurr."""
        result = validate_params("PowerSet", instrument, {
            "Instrument": f"{instrument.lower()}_1",
            "SetVolt": "5.0",
            "SetCurr": "1.0"
        })
        assert result["valid"] is True

    def test_powerset_aps7050_valid_params(self):
        """APS7050 PowerSet requires Instrument, Channel, SetVolt, SetCurr."""
        result = validate_params("PowerSet", "APS7050", {
            "Instrument": "aps7050_1",
            "Channel": "1",
            "SetVolt": "5.0",
            "SetCurr": "1.0"
        })
        assert result["valid"] is True

    def test_powerset_keithley2015_valid_params(self):
        """KEITHLEY2015 PowerSet requires Instrument, Command."""
        result = validate_params("PowerSet", "KEITHLEY2015", {
            "Instrument": "keithley2015_1",
            "Command": "SOURCE:VOLTAGE 5.0"
        })
        assert result["valid"] is True


class TestPowerReadTemplates:
    """Test PowerRead MEASUREMENT_TEMPLATES validation."""

    @pytest.mark.parametrize("instrument", [
        "DAQ973A", "34970A", "KEITHLEY2015", "2015", "6510",
        "APS7050", "MDO34", "MT8870A_INF"
    ])
    def test_powerread_instrument_exists(self, instrument):
        """All PowerRead instruments should exist in MEASUREMENT_TEMPLATES."""
        assert "PowerRead" in MEASUREMENT_TEMPLATES
        assert instrument in MEASUREMENT_TEMPLATES["PowerRead"]

    def test_powerread_daq973a_valid_params(self):
        """DAQ973A PowerRead requires Instrument, Channel, Item, Type."""
        result = validate_params("PowerRead", "DAQ973A", {
            "Instrument": "daq973a_1",
            "Channel": "101",
            "Item": "volt",
            "Type": "DC"
        })
        assert result["valid"] is True

    def test_powerread_2015_valid_params(self):
        """2015 PowerRead requires Instrument, Command."""
        result = validate_params("PowerRead", "2015", {
            "Instrument": "2015_1",
            "Command": "MEASURE:VOLTAGE?"
        })
        assert result["valid"] is True

    def test_powerread_6510_valid_params(self):
        """6510 PowerRead requires Instrument, Item."""
        result = validate_params("PowerRead", "6510", {
            "Instrument": "daq6510_1",
            "Item": "volt"
        })
        assert result["valid"] is True

    def test_powerread_aps7050_valid_params(self):
        """APS7050 PowerRead requires Instrument, Item."""
        result = validate_params("PowerRead", "APS7050", {
            "Instrument": "aps7050_1",
            "Item": "current"
        })
        assert result["valid"] is True

    def test_powerread_mdo34_valid_params(self):
        """MDO34 PowerRead requires Instrument, Channel, Item."""
        result = validate_params("PowerRead", "MDO34", {
            "Instrument": "mdo34_1",
            "Channel": "1",
            "Item": "volt"
        })
        assert result["valid"] is True

    def test_powerread_mt8870a_inf_valid_params(self):
        """MT8870A_INF PowerRead requires Instrument, Item."""
        result = validate_params("PowerRead", "MT8870A_INF", {
            "Instrument": "mt8870a_1",
            "Item": "power"
        })
        assert result["valid"] is True


class TestTemplateStructure:
    """Test MEASUREMENT_TEMPLATES structure completeness."""

    @pytest.mark.parametrize("instrument_type", ["PowerSet", "PowerRead"])
    def test_template_has_required_keys(self, instrument_type):
        """Each template should have required, optional, and example keys."""
        for instrument, template in MEASUREMENT_TEMPLATES[instrument_type].items():
            assert "required" in template
            assert "optional" in template
            assert "example" in template
            assert isinstance(template["required"], list)
            assert isinstance(template["optional"], list)
            assert isinstance(template["example"], dict)

    def test_powerset_all_instruments_accounted_for(self):
        """Verify all PowerSet instruments from legacy dict are now in MEASUREMENT_TEMPLATES."""
        # These were in the legacy validation_rules dict
        expected_instruments = [
            "DAQ973A", "MODEL2303", "MODEL2306", "IT6723C", "PSW3072",
            "2260B", "APS7050", "34970A", "KEITHLEY2015"
        ]
        actual_instruments = set(MEASUREMENT_TEMPLATES["PowerSet"].keys())
        assert set(expected_instruments) == actual_instruments

    def test_powerread_all_instruments_accounted_for(self):
        """Verify all PowerRead instruments from legacy dict are now in MEASUREMENT_TEMPLATES."""
        expected_instruments = [
            "DAQ973A", "34970A", "2015", "6510", "APS7050",
            "MDO34", "MT8870A_INF", "KEITHLEY2015"
        ]
        actual_instruments = set(MEASUREMENT_TEMPLATES["PowerRead"].keys())
        assert set(expected_instruments) == actual_instruments
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_config/test_power_templates_validation.py -v`
Expected: PASS (all tests should pass after migration is complete)

- [ ] **Step 3: Commit tests**

```bash
git add backend/tests/test_config/test_power_templates_validation.py
git commit -m "test: add PowerSet/PowerRead MEASUREMENT_TEMPLATES validation tests"
```

---
## Chunk 6: Integration Test with MeasurementService

### Task 15: Test MeasurementService.validate_params Uses New Templates

**Files:**
- Create: `backend/tests/test_services/test_measurement_service_validation.py`

- [ ] **Step 1: Write integration test**

```python
"""
Test that MeasurementService.validate_params correctly delegates to
validate_params_config for migrated PowerSet/PowerRead instruments.
"""
import pytest
from app.services.measurement_service import MeasurementService


class TestMeasurementServicePowerValidation:
    """Test MeasurementService.validate_params with PowerSet/PowerRead."""

    @pytest.fixture
    def service(self):
        return MeasurementService()

    # PowerSet tests
    @pytest.mark.parametrize("instrument,switch_mode,test_params", [
        ("IT6723C", "IT6723C", {"Instrument": "it1", "SetVolt": "5", "SetCurr": "1"}),
        ("PSW3072", "PSW3072", {"Instrument": "psw1", "SetVolt": "12", "SetCurr": "0.5"}),
        ("2260B", "2260B", {"Instrument": "2260b_1", "SetVolt": "5", "SetCurr": "1"}),
        ("APS7050", "APS7050", {"Instrument": "aps1", "Channel": "1", "SetVolt": "5", "SetCurr": "1"}),
        ("KEITHLEY2015", "KEITHLEY2015", {"Instrument": "k2015_1", "Command": "SOURCE:VOLTAGE 5"}),
    ])
    async def test_powerset_migrated_instruments_validate(self, service, instrument, switch_mode, test_params):
        """Migrated PowerSet instruments should validate via MEASUREMENT_TEMPLATES (primary path)."""
        result = await service.validate_params("PowerSet", switch_mode, test_params)
        # Primary path (validate_params_config) returns structured result
        assert "valid" in result
        assert result["valid"] is True

    # PowerRead tests
    @pytest.mark.parametrize("instrument,switch_mode,test_params", [
        ("2015", "2015", {"Instrument": "2015_1", "Command": "MEASURE:VOLTAGE?"}),
        ("6510", "6510", {"Instrument": "6510_1", "Item": "volt"}),
        ("APS7050", "APS7050", {"Instrument": "aps1", "Item": "current"}),
        ("MDO34", "MDO34", {"Instrument": "mdo1", "Channel": "1", "Item": "volt"}),
        ("MT8870A_INF", "MT8870A_INF", {"Instrument": "mt1", "Item": "power"}),
    ])
    async def test_powerread_migrated_instruments_validate(self, service, instrument, switch_mode, test_params):
        """Migrated PowerRead instruments should validate via MEASUREMENT_TEMPLATES (primary path)."""
        result = await service.validate_params("PowerRead", switch_mode, test_params)
        assert "valid" in result
        assert result["valid"] is True

    async def test_missing_required_params_returns_error(self, service):
        """Missing required params should return valid=False with missing_params list."""
        result = await service.validate_params("PowerSet", "IT6723C", {
            "Instrument": "it1"
            # Missing: SetVolt, SetCurr
        })
        assert result["valid"] is False
        assert "SetVolt" in result["missing_params"]
        assert "SetCurr" in result["missing_params"]

    async def test_unknown_instrument_returns_error(self, service):
        """Unknown instrument should return structured error."""
        result = await service.validate_params("PowerSet", "UNKNOWN_INSTRUMENT", {})
        assert result["valid"] is False
        assert len(result["suggestions"]) > 0
```

- [ ] **Step 2: Run integration tests**

Run: `uv run pytest backend/tests/test_services/test_measurement_service_validation.py -v`
Expected: PASS (all tests should pass)

- [ ] **Step 3: Commit integration tests**

```bash
git add backend/tests/test_services/test_measurement_service_validation.py
git commit -m "test: add MeasurementService PowerSet/PowerRead validation integration tests"
```

---
## Chunk 7: Verify and Finalize

### Task 16: Run Full Test Suite

- [ ] **Step 1: Run all tests to ensure no regressions**

Run: `uv run pytest backend/tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 2: Run specific validation tests**

Run: `uv run pytest backend/tests/ -k "validation" -v`
Expected: All validation-related tests pass

- [ ] **Step 3: Check for any remaining references to removed instruments**

Run: `grep -r "IT6723C\|PSW3072\|2260B" backend/app/services/measurement_service.py`
Expected: Only the commented-out migration note should appear

### Task 17: Update Documentation

- [ ] **Step 1: Create migration documentation**

Create: `docs/migration/power-measurement-templates-2026-03-16.md`

```markdown
# PowerSet/PowerRead Instrument Templates Migration

**Date:** 2026-03-16

## Summary

Migrated PowerSet and PowerRead instrument validation rules from the legacy
`validation_rules` dictionary in `measurement_service.py` to `MEASUREMENT_TEMPLATES`
in `instruments.py`.

## Migrated Instruments

### PowerSet (5 instruments added)
- IT6723C: required=[Instrument, SetVolt, SetCurr]
- PSW3072: required=[Instrument, SetVolt, SetCurr]
- 2260B: required=[Instrument, SetVolt, SetCurr]
- APS7050: required=[Instrument, Channel, SetVolt, SetCurr]
- KEITHLEY2015: required=[Instrument, Command]

### PowerRead (6 instruments added)
- 2015: required=[Instrument, Command]
- 6510: required=[Instrument, Item]
- APS7050: required=[Instrument, Item]
- MDO34: required=[Instrument, Channel, Item]
- MT8870A_INF: required=[Instrument, Item]
- KEITHLEY2015: required=[Instrument, Command]

## Files Changed

### Modified
- `backend/app/config/instruments.py`: Added 11 instrument templates
- `backend/app/services/measurement_service.py`: Commented out migrated entries

### Added Tests
- `backend/tests/test_config/test_power_templates_validation.py`: Template validation tests
- `backend/tests/test_services/test_measurement_service_validation.py`: Integration tests

## Verification

All instruments now validate through the primary path (`validate_params_config()`),
improving consistency and enabling automatic API documentation via `/types` endpoint.

## Next Steps

- Continue migrating remaining types in legacy `validation_rules` (CommandTest, SFCtest, etc.)
- Eventually remove the entire legacy fallback dict once all types are migrated
```

- [ ] **Step 2: Commit documentation**

```bash
git add docs/migration/power-measurement-templates-2026-03-16.md
git commit -m "docs: record PowerSet/PowerRead templates migration"
```

### Task 18: Final Verification

- [ ] **Step 1: Verify API endpoint returns new instruments**

Run: `curl http://localhost:9100/api/types | jq '.[] | select(.name == "PowerSet" or .name == "PowerRead")'`

Expected: JSON showing PowerSet with 9 switches and PowerRead with 8 switches

- [ ] **Step 2: Final commit for completion**

```bash
git add -A
git commit -m "feat: complete PowerSet/PowerRead instrument templates migration

- Added IT6723C, PSW3072, 2260B, APS7050, KEITHLEY2015 to PowerSet
- Added 2015, 6510, APS7050, MDO34, MT8870A_INF, KEITHLEY2015 to PowerRead
- Removed migrated entries from legacy validation_rules dict
- Added comprehensive validation tests
- Updated migration documentation

All PowerSet/PowerRead instruments now validate via MEASUREMENT_TEMPLATES."
```

---
## Completion Checklist

- [ ] All PowerSet instruments in MEASUREMENT_TEMPLATES
- [ ] All PowerRead instruments in MEASUREMENT_TEMPLATES
- [ ] Legacy validation_rules entries commented out with migration notes
- [ ] Template validation tests pass
- [ ] Integration tests pass
- [ ] Full test suite passes
- [ ] Documentation updated
- [ ] API /types endpoint returns new instruments

---
**End of Plan**
