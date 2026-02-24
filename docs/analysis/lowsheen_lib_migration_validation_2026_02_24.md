# lowsheen_lib Migration Validation

**Date**: 2026-02-24
**Scope**: `backend/src/lowsheen_lib/` → `backend/app/measurements/` + `backend/app/services/instruments/`
**Based on**: `docs/code_review/LOWSHEEN_LIB_DEPRECATION_ANALYSIS_2026_02_23.md`
**Status**: ~70% Complete — Execution path migrated, Cleanup/Reset paths still legacy

---

## Executive Summary

This document validates the deprecation analysis from 2026-02-23 against the current codebase. The primary finding is that migration is **partially complete**:

- ✅ `execute_single_measurement()` fully delegates to `implementations.py` (modern async classes)
- ❌ `_cleanup_used_instruments()` still calls `lowsheen_lib` scripts via subprocess
- ❌ `reset_instrument()` still hardcodes `lowsheen_lib` paths
- ❌ `instrument_executor.py` `script_map` is still live code (though bypassed for primary execution)

---

## Migration Pattern: Strangler Fig

The migration uses a **strangler fig pattern**: the new async class-based system grew around the legacy subprocess calls.

- `execute_single_measurement()` was fully strangled (primary path now goes entirely through `implementations.py`)
- `_cleanup_used_instruments()` and `reset_instrument()` remain legacy — these are called far less frequently during test teardown, which is why they were deprioritized

---

## Active Legacy Call Sites (Remaining Gaps)

| File | Line | Legacy Call | Gap Type |
|------|------|-------------|----------|
| `measurement_service.py` | 378 | `script_path = f"./src/lowsheen_lib/{script_name}"` | Cleanup path |
| `measurement_service.py` | 660 | `"./src/lowsheen_lib/DAQ973A_test.py"` | Reset path |
| `measurement_service.py` | 662 | `"./src/lowsheen_lib/2303_test.py"` | Reset path |
| `instrument_executor.py` | 164–186 | Full `script_map` (15 entries) → `./src/lowsheen_lib/` | Legacy subprocess bridge |

### `_cleanup_used_instruments()` — measurement_service.py:372–395

```python
async def _cleanup_used_instruments(self, used_instruments: Dict[str, str]):
    for instrument_location, script_name in used_instruments.items():
        script_path = f"./src/lowsheen_lib/{script_name}"  # ← LEGACY
        await asyncio.create_subprocess_exec(
            "python3", script_path, "--final", str(test_params), ...
        )
```

### `reset_instrument()` — measurement_service.py:654–671

```python
async def reset_instrument(self, instrument_id: str):
    if instrument_id.startswith("daq973a"):
        script_path = "./src/lowsheen_lib/DAQ973A_test.py"  # ← LEGACY
    elif instrument_id.startswith("model2303"):
        script_path = "./src/lowsheen_lib/2303_test.py"      # ← LEGACY
```

### `instrument_executor.py` script_map — lines 164–186

```python
script_map = {
    'DAQ973A': 'DAQ973A_test.py',
    '34970A': '34970A.py',
    'APS7050': 'APS7050.py',
    'MDO34': 'MDO34.py',
    'KEITHLEY2015': 'Keithley2015.py',
    'MT8870A_INF': 'RF_tool/MT8872A_INF.py',
    'MODEL2303': '2303_test.py',
    'MODEL2306': '2306_test.py',
    'DAQ6510': 'DAQ6510.py',
    '2260B': '2260B.py',
    'IT6723C': 'IT6723C.py',
    'PSW3072': 'PSW3072.py',
    'ComPort': 'ComPortCommand.py',
    'Console': 'ConSoleCommand.py',
    'TCPIP': 'TCPIPCommand.py',
}
script_path = f"./src/lowsheen_lib/{script_file}"  # ← LEGACY
```

**Note**: `instrument_executor.py` script_map is still live code. However, since `execute_single_measurement()` in `measurement_service.py` now delegates directly to `implementations.py` classes, the `script_map` is **bypassed for the primary execution path**. It would only be reached if another caller invokes the legacy execution method directly.

---

## Coverage Matrix: `lowsheen_lib` vs `implementations.py`

| `lowsheen_lib` Script | Modern Driver (`app/services/instruments/`) | `implementations.py` Coverage | Status |
|-----------------------|----------------------------------------------|-------------------------------|--------|
| `DAQ973A_test.py` | `daq973a.py` | `PowerReadMeasurement` (DAQ973A branch) | ✅ Migrated |
| `2303_test.py` | `model2303.py` | `PowerReadMeasurement` + `PowerSetMeasurement` (MODEL2303) | ✅ Migrated |
| `2306_test.py` | `model2306.py` | `PowerReadMeasurement` + `PowerSetMeasurement` (MODEL2306) | ✅ Migrated |
| `IT6723C.py` | `it6723c.py` | `PowerReadMeasurement` + `PowerSetMeasurement` (IT6723C) | ✅ Migrated |
| `PSW3072.py` | `psw3072.py` | `PowerSetMeasurement` (APS7050/PSW3072/A2260B branch) | ✅ Migrated |
| `2260B.py` | `a2260b.py` | `PowerSetMeasurement` (A2260B branch) | ✅ Migrated |
| `APS7050.py` | `aps7050.py` | `PowerSetMeasurement` (APS7050 branch) | ✅ Migrated |
| `34970A.py` | `a34970a.py` | `PowerReadMeasurement` (34970A branch) | ✅ Migrated |
| `Keithley2015.py` | `keithley2015.py` | `PowerReadMeasurement` (KEITHLEY2015 branch) | ✅ Migrated |
| `DAQ6510.py` | `daq6510.py` | `PowerReadMeasurement` (DAQ6510 branch) | ✅ Migrated |
| `smcv100b.py` | `smcv100b.py` | `SMCV100B_RF_Output_Measurement` | ✅ Migrated |
| `MDO34.py` | `mdo34.py` *(driver exists)* | **No `MDO34Measurement` class** in `implementations.py` | ❌ **Gap** |
| `ComPortCommand.py` | `comport_command.py` | Mapped to `CommandTestMeasurement` (stub) | ⚠️ Stub only |
| `ConSoleCommand.py` | `console_command.py` | Mapped to `CommandTestMeasurement` (stub) | ⚠️ Stub only |
| `TCPIPCommand.py` | `tcpip_command.py` | Mapped to `CommandTestMeasurement` (stub) | ⚠️ Stub only |
| `Wait_test.py` | `wait_test.py` | `WaitMeasurement` | ✅ Migrated |
| `OPjudge_confirm_terminal.py` | — | `OPJudgeMeasurement` (no real terminal I/O) | ⚠️ Stub only |
| `OPjudge_YorN_terminal.py` | — | `OPJudgeMeasurement` (no real terminal I/O) | ⚠️ Stub only |

---

## New Finding (Beyond Deprecation Analysis)

### MDO34 — Missing `implementations.py` Coverage

The deprecation analysis noted MDO34 was in `instrument_reset_map`. The current codebase reveals a deeper gap:

- ✅ Modern driver exists: `backend/app/services/instruments/mdo34.py`
- ❌ No `MDO34Measurement` class in `implementations.py`
- ❌ `PowerReadMeasurement._measure_with_driver()` has **no MDO34 branch**
- ❌ Still in `instrument_executor.py` `script_map` pointing to `lowsheen_lib/MDO34.py`

**Risk**: If any test plan uses MDO34 for measurement, `PowerReadMeasurement` will reach the `else: raise ValueError(...)` path and return an ERROR result. Unlike other instruments, there is no modern measurement path available for MDO34 at all.

---

## Remediation Plan Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Remove: `OPjudge_confirm.py`, `OPjudge_YorN.py`, `testUTF/123.py` | ❌ Not done — files still exist |
| Phase 2 | Migrate `_cleanup_used_instruments()` to use modern `BaseInstrumentDriver` reset methods | ❌ Still legacy subprocess |
| Phase 3 | Replace `instrument_executor.py` `script_map` with driver class calls | ⚠️ Bypassed but not removed |
| Phase 4 | Remove remaining legacy scripts after Phases 2 & 3 complete | ❌ Blocked |
| **New** | Add `MDO34Measurement` class to `implementations.py` | ❌ Gap not in original plan |

---

## Risk Assessment

| Risk | Severity | Notes |
|------|----------|-------|
| `_cleanup_used_instruments()` subprocess CWD dependency | High | Must run from `backend/` dir; Docker CWD change silently breaks cleanup |
| `ComPortCommand.py` has `WindowsError` | High | Will raise `NameError` on Linux/Docker if this path is hit |
| MDO34 has no `implementations.py` coverage | Medium | Returns ERROR for any MDO34 measurement — no fallback |
| `instrument_reset_map` in `MeasurementService.__init__` | Low | Maps to `lowsheen_lib` filenames but `execute_single_measurement()` bypasses it |
| `LOWSHEEN_LIB_PATH` constant still defined | Low | `measurement_constants.py:137–138` anchors paths — cosmetic but misleading |
