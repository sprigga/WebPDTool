# lowsheen_lib Deprecation Analysis

**Date**: 2026-02-23
**Scope**: `backend/src/lowsheen_lib/`
**Status**: Partial Migration — Library is NOT fully deprecated (still actively called)

---

## Executive Summary

`lowsheen_lib` is the **original PDTool4 legacy library** — a collection of standalone Python subprocess scripts implementing hardware instrument drivers and UI dialogs. It is the predecessor to `backend/app/services/instruments/` and `backend/app/measurements/implementations.py`.

**Key Finding**: The library is **neither fully deprecated nor fully integrated**. The main app has a partially completed migration:
- ✅ `execute_single_measurement()` migrated to new async class-based system
- ❌ `_cleanup_used_instruments()` still calls `lowsheen_lib` scripts via subprocess
- ❌ `reset_instrument()` still hardcodes `lowsheen_lib` paths
- ❌ `instrument_executor.py` maintains a live `script_map` pointing to `lowsheen_lib`

---

## Where lowsheen_lib Is Still Called

### 1. `backend/app/services/instrument_executor.py` (lines 174–186)
```python
script_map = {
    'DAQ973A':  'DAQ973A_test.py',
    'MODEL2303': '2303_test.py',
    'MODEL2306': '2306_test.py',
    'IT6723C':  'IT6723C.py',
    'PSW3072':  'PSW3072.py',
    'ComPort':  'ComPortCommand.py',
    'Console':  'ConSoleCommand.py',
    'TCPIP':    'TCPIPCommand.py',
}
script_path = f"./src/lowsheen_lib/{script_file}"
```
**This is a live subprocess execution path.**

### 2. `backend/app/services/measurement_service.py`
- `_cleanup_used_instruments()` (lines ~374–388): calls legacy scripts with `--final` argument
- `reset_instrument()` (lines ~660–662): hardcodes paths to `DAQ973A_test.py` and `2303_test.py`
- `instrument_reset_map` in `__init__` (lines 47–59): maps instrument types to `lowsheen_lib` filenames

### 3. `backend/app/core/measurement_constants.py` (lines 137–138)
```python
LOWSHEEN_LIB_PATH = "./src/lowsheen_lib"
RF_TOOL_PATH = "./src/lowsheen_lib/RF_tool"
```
These constants anchor the path as a first-class configuration value.

---

## File-by-File Classification

### Group 1: Instrument Driver Scripts — Superseded but Still Called

These files implement the PDTool4 pattern: invoked via `subprocess.run(["python3", script_path, ...])`. All use `remote_instrument.py` for VISA/serial connections.

| File | Instrument | Modern Equivalent | Still Called By |
|------|-----------|-------------------|-----------------|
| `2303_test.py` | Keysight MODEL2303 power supply | `app/services/instruments/model2303.py` | `instrument_executor.py`, `measurement_service.py` |
| `2306_test.py` | Keysight MODEL2306 power supply | `app/services/instruments/model2306.py` | `instrument_executor.py` |
| `DAQ973A_test.py` | Keysight DAQ973A data acquisition | `app/services/instruments/daq973a.py` | `instrument_executor.py`, `measurement_service.py` |
| `IT6723C.py` | ITECH IT6723C power supply | `app/services/instruments/it6723c.py` | `instrument_executor.py` |
| `PSW3072.py` | GW Instek PSW3072 power supply | `app/services/instruments/psw3072.py` | `instrument_executor.py` |
| `2260B.py` | Keysight 2260B power supply | `app/services/instruments/a2260b.py` | `instrument_reset_map` in `measurement_service.py` |
| `APS7050.py` | APS7050 data acquisition | `app/services/instruments/aps7050.py` | `instrument_reset_map` |
| `34970A.py` | Keysight 34970A data acquisition | `app/services/instruments/a34970a.py` | `instrument_reset_map` |
| `Keithley2015.py` | Keithley 2015 multimeter | `app/services/instruments/keithley2015.py` | `instrument_reset_map` |
| `DAQ6510.py` | Keithley DAQ6510 | `app/services/instruments/daq6510.py` | `instrument_reset_map` |
| `MDO34.py` | Tektronix MDO34 oscilloscope | `app/services/instruments/mdo34.py` | `instrument_reset_map` |
| `smcv100b.py` | R&S SMCV100B signal generator | `app/services/instruments/smcv100b.py` | `instrument_reset_map` |

**Architectural difference**: Legacy scripts are synchronous, use `pyvisa` directly, print results to stdout. Modern drivers are async classes extending `BaseInstrumentDriver`, use logging, return typed results.

### Group 2: Command Channel Scripts — Superseded but Still Called

| File | Function | Modern Equivalent | Status |
|------|---------|-------------------|--------|
| `ComPortCommand.py` | Serial port command-response | `app/services/instruments/comport_command.py` | Still in `script_map` |
| `ConSoleCommand.py` | Shell command via `subprocess.Popen` | `app/services/instruments/console_command.py` | Still in `script_map` |
| `TCPIPCommand.py` | Binary TCP packets with CRC32 | `app/services/instruments/tcpip_command.py` | Still in `script_map` |

> Note: `ComPortCommand.py` contains `WindowsError` — Windows-only code that will fail on Linux/Docker.

### Group 3: OPjudge Scripts — Mixed State

| File | Technology | Status | Notes |
|------|-----------|--------|-------|
| `OPjudge_confirm.py` | PyQt5 GUI dialog | **DEPRECATED** | PyQt5 cannot run headless in Docker |
| `OPjudge_YorN.py` | PyQt5 GUI dialog | **DEPRECATED** | Same headless incompatibility |
| `OPjudge_confirm_terminal.py` | Terminal input | **ACTIVE** | Used by `scripts/test_opjudge.py` lines 19, 139 |
| `OPjudge_YorN_terminal.py` | Terminal input | **ACTIVE** | Used by `scripts/test_opjudge.py` line 79 |

The `*_terminal.py` variants are the current production path for OPjudge tests, explicitly written as "Compatible with WebPDTool measurement_service.py expectations."

### Group 4: Shared Infrastructure

| File | Role | Status |
|------|------|--------|
| `remote_instrument.py` | Shared helper for all legacy scripts — reads `test_xml.ini`, handles VISA/TCP/serial setup | Required by all Group 1 & 2 scripts; not used by `backend/app/` |
| `__init__.py` | Contains only BRAIN Corporation copyright comment | Dead file — no code |

### Group 5: Development/Test Fixtures

| File | Role | Status |
|------|------|--------|
| `testUTF/123.py` | Echoes arguments back — sanity-check fixture | Development only — not production code |
| `Wait_test.py` | Sleeps for `WaitmSec` ms, prints confirmation | Not in active `script_map` — likely fully migrated |

---

## Removable vs. Required Files

| File | Can Be Removed? | Reason |
|------|----------------|--------|
| `OPjudge_confirm.py` | ✅ **Yes** | PyQt5 GUI deprecated; `*_terminal.py` variant handles this |
| `OPjudge_YorN.py` | ✅ **Yes** | Same — superseded by terminal variant |
| `__init__.py` | ✅ **Yes** (or clear content) | No code — only copyright comment |
| `testUTF/123.py` | ✅ **Yes** | Development fixture, not production |
| `Wait_test.py` | ✅ **Yes** (after verifying `app/` path works) | Not in `script_map`; modern equivalent exists |
| `2303_test.py` | ❌ No | Still invoked by `instrument_executor.py` and `measurement_service.py` |
| `2306_test.py` | ❌ No | Still in `instrument_executor.py` `script_map` |
| `DAQ973A_test.py` | ❌ No | Still in `script_map` and `measurement_service.py` reset |
| `IT6723C.py` | ❌ No | Still in `script_map` |
| `PSW3072.py` | ❌ No | Still in `script_map` |
| `2260B.py` | ❌ No | Still in `instrument_reset_map` |
| `APS7050.py` | ❌ No | Still in `instrument_reset_map` |
| `34970A.py` | ❌ No | Still in `instrument_reset_map` |
| `Keithley2015.py` | ❌ No | Still in `instrument_reset_map` |
| `DAQ6510.py` | ❌ No | Still in `instrument_reset_map` |
| `MDO34.py` | ❌ No | Still in `instrument_reset_map` |
| `smcv100b.py` | ❌ No | Still in `instrument_reset_map` |
| `ComPortCommand.py` | ❌ No | Still in `script_map` |
| `ConSoleCommand.py` | ❌ No | Still in `script_map` |
| `TCPIPCommand.py` | ❌ No | Still in `script_map` |
| `remote_instrument.py` | ❌ No | Required by all non-removable legacy scripts |
| `OPjudge_confirm_terminal.py` | ❌ No | Active production path |
| `OPjudge_YorN_terminal.py` | ❌ No | Active production path |

**Safe to remove now: 5 files** (`OPjudge_confirm.py`, `OPjudge_YorN.py`, `__init__.py` content, `testUTF/123.py`, `Wait_test.py`)

---

## Architecture Gap: Incomplete Migration

The `measurement_service.py` comment (line 8) states:
> "Removed 1401 lines of duplicate legacy code (66.6% reduction)"

However, the cleanup path was never migrated:

```
Test Measurement Flow:
  execute_single_measurement()  ──→  NEW async class system (BaseMeasurement subclasses)
  _cleanup_used_instruments()   ──→  LEGACY subprocess calls into lowsheen_lib  ← Gap
  reset_instrument()            ──→  LEGACY subprocess calls into lowsheen_lib  ← Gap
```

The `instrument_reset_map` in `MeasurementService.__init__` is the clearest indicator — it maps instrument types to `lowsheen_lib` filenames for cleanup purposes, even though the measurement execution itself was migrated.

---

## Recommended Remediation Plan

### Phase 1: Safe Immediate Removals
Remove clearly deprecated files with no active callers:
1. `OPjudge_confirm.py` — PyQt5 GUI, incompatible with headless Docker
2. `OPjudge_YorN.py` — Same
3. `testUTF/123.py` — Development fixture

### Phase 2: Complete the Cleanup Path Migration
Migrate `_cleanup_used_instruments()` and `reset_instrument()` in `measurement_service.py` to use the modern `BaseInstrumentDriver` reset methods instead of subprocess calls.

### Phase 3: Migrate instrument_executor.py script_map
Replace the subprocess `script_map` in `instrument_executor.py` with calls to the corresponding `app/services/instruments/` driver classes.

### Phase 4: Remove Remaining Legacy Scripts
Once Phases 2 & 3 are complete, all instrument scripts plus `remote_instrument.py` can be archived.

---

## Risk Notes

- **`ComPortCommand.py`** uses `WindowsError` — will raise `NameError` on Linux/Docker. If this path is ever hit in production, it will crash.
- **`remote_instrument.py`** reads `test_xml.ini` at a hardcoded relative path — this path may not resolve correctly when called as a subprocess from the Docker container.
- All subprocess calls use `./src/lowsheen_lib/` relative paths, which depend on the working directory being `backend/`. If the CWD changes, all subprocess calls silently fail.

---

## Related Files

- `backend/app/services/instrument_executor.py` — Live bridge calling `lowsheen_lib` via subprocess
- `backend/app/services/measurement_service.py` — Contains both new path and residual legacy cleanup calls
- `backend/app/measurements/implementations.py` — Modern replacement (the `Other` class)
- `backend/app/core/measurement_constants.py` — Defines `LOWSHEEN_LIB_PATH` as a constant
- `backend/scripts/test_opjudge.py` — Active caller of OPjudge terminal scripts
