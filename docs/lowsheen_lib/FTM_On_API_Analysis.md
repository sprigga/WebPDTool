# FTM_On WiFi RF Tool API Analysis

**Analysis Date:** 2025-01-04
**Component:** `src/lowsheen_lib/RF_tool/FTM_On/`
**Purpose:** WiFi FTM (Factory Test Mode) RF testing automation for Qualcomm chipsets

---

## Overview

The FTM_On module provides automated WiFi RF testing capabilities for devices using Qualcomm QCA6390 chipsets. It enables switching between normal operation and Factory Test Mode (FTM) for TX power testing on different WiFi chains.

### Primary Use Case
- Manufacturing test environment for WiFi-enabled products
- Automated TX power measurement on Chain 1 and Chain 2
- Integration with PDTool4 test execution framework

---

## Architecture

```
FTM_On/
├── PythonSubprocess_FTM_Entrance.py    # Entry point: Open FTM mode
├── PythonSubprocess_FTM.py              # Core: ADB & FTM setup logic
├── WiFi_FTM_Entrance.bat                # Launcher for FTM setup
├── WiFi_FTM.bat                         # Launch ftmdaemon process
├── API_WIFI_TxOn_chain1_AutoDetect.exe  # TX Chain 1 test executable
├── API_WIFI_TxOn_chain2_AutoDetect.exe  # TX Chain 2 test executable
├── PythonSubprocess_close_Entrance.py   # Entry point: Close FTM mode
├── PythonSubprocess_close.py            # Core: Window cleanup logic
├── WiFi_FTM_close.bat                   # Launcher for cleanup
├── Walrus_FCT1_testPlan.csv             # PDTool4 test plan
├── QMSL_MSVC10R.dll                     # Qualcomm QMSL library
└── QMSLFastConnect_MSVC10R.dll          # QMSL Fast Connect library
```

---

## Execution Flow

### Phase 1: Open FTM Mode (Test Start)

```
Test Plan Execution
        ↓
PythonSubprocess_FTM_Entrance.py
        ↓
WiFi_FTM_Entrance.bat (new window)
        ↓
PythonSubprocess_FTM.py
        ↓
┌─────────────────────────────────────┐
│ 1. adb root                          │
│ 2. adb remount                       │
│ 3. adb shell rmmod qca6390           │
│ 4. adb shell insmod qca_cld3_*.ko    │
│    con_mode_ftm=5                    │
│ 5. adb shell ifconfig wlan0 up       │
│ 6. WiFi_FTM.bat (ftmdaemon -n -dd)   │
│ 7. API_WIFI_TxOn_chain*.exe          │
│ 8. Close "Entrance" window            │
└─────────────────────────────────────┘
```

### Phase 2: Close FTM Mode (Test End)

```
Test Plan Execution
        ↓
PythonSubprocess_close_Entrance.py
        ↓
WiFi_FTM_close.bat (new window)
        ↓
PythonSubprocess_close.py
        ↓
┌─────────────────────────────────────┐
│ 1. Close "FTM Mode" window           │
│ 2. Close "Close" window              │
└─────────────────────────────────────┘
```

---

## API Reference

### PythonSubprocess_FTM_Entrance.py

**Purpose:** Entry point script that launches the FTM setup process in a new command window.

```python
# File: PythonSubprocess_FTM_Entrance.py
import subprocess
import time

print('Open FTM Entrance')
process1 = subprocess.run('.\src\lowsheen_lib\RF_tool\FTM_On\WiFi_FTM_Entrance.bat')
```

**Key Points:**
- Acts as a minimal launcher wrapper
- Executes `WiFi_FTM_Entrance.bat` which opens a new window titled "Entrance"
- Process is non-blocking (returns immediately after batch launch)

---

### PythonSubprocess_FTM.py

**Purpose:** Core FTM setup and TX test execution script.

**Dependencies:**
- `subprocess` - Process spawning
- `time` - Sleep delays
- `pyautogui` - Window management (Alt+F4)

**Key Functions:**

#### `close_window(window_title: str) -> bool`

Closes a Windows command prompt window by title using pyautogui.

```python
def close_window(window_title):
    windows = pyautogui.getWindowsWithTitle(window_title)
    for window in windows:
        if window_title in window.title:
            window.activate()
            time.sleep(1)
            pyautogui.hotkey('alt', 'f4')
            return True
    return False
```

**Parameters:**
- `window_title` (str): Title of window to close (e.g., "Entrance", "FTM Mode", "Close")

**Returns:**
- `bool`: True if window found and closed, False otherwise

**Main Execution Sequence:**

```python
# 1. Gain ADB root access
subprocess.run(['adb', 'root'])

# 2. Remount filesystem as writable
subprocess.run(['adb', 'remount'])

# 3. Remove existing qca6390 driver module
subprocess.run(['adb', 'shell', 'rmmod', 'qca6390'])

# 4. Insert driver with FTM mode (con_mode_ftm=5)
subprocess.run(['adb', 'shell', 'insmod',
                'vendor/lib/modules/qca_cld3_qca6390.ko',
                'con_mode_ftm=5'])

# 5. Bring up wlan0 interface
subprocess.run(['adb', 'shell', 'ifconfig', 'wlan0', 'up'])

# 6. Start FTM daemon in new window
subprocess.run('.\src\lowsheen_lib\RF_tool\FTM_ON\WiFi_FTM.bat')

# 7. Wait for daemon initialization
time.sleep(2)

# 8. Execute TX power test (Chain 1 or Chain 2)
process1 = subprocess.run('.\src\lowsheen_lib\RF_tool\FTM_On\API_WIFI_TxOn_chain1_AutoDetect.exe',
                          capture_output=True, text=True, shell=True)

# 9. Self-close the "Entrance" window
window_title = "Entrance"
close_window(window_title)
```

**Critical Parameters:**
- `con_mode_ftm=5`: FTM (Factory Test Mode) parameter for QCA6390 driver
- `ftmdaemon -n -dd`: FTM daemon with no console (-n) and debug display (-dd)

---

### PythonSubprocess_close_Entrance.py

**Purpose:** Entry point script that launches the FTM cleanup process.

```python
# File: PythonSubprocess_close_Entrance.py
import subprocess
import time

process1 = subprocess.run('.\src\lowsheen_lib\RF_tool\FTM_On\WiFi_FTM_Close.bat')
```

---

### PythonSubprocess_close.py

**Purpose:** Cleanup script to close all FTM-related windows after testing.

**Key Functions:**

#### `close_window(window_title: str) -> bool`

Same implementation as in `PythonSubprocess_FTM.py`.

**Main Execution Sequence:**

```python
# 1. Close FTM daemon window
window_title = "FTM Mode"
close_window(window_title)

# 2. Close cleanup window itself
window_title = "Close"
close_window(window_title)
```

**Note:** Does NOT restore normal WiFi driver mode. Device remains in FTM mode until reboot.

---

## Batch Files

### WiFi_FTM_Entrance.bat

```batch
start "Entrance" cmd /k "python .\src\lowsheen_lib\RF_tool\FTM_On\PythonSubprocess_FTM.py"
```

- Opens a new command window titled "Entrance"
- `/k` flag keeps window open after execution
- Executes Python FTM setup script

### WiFi_FTM.bat

```batch
start "FTM Mode" cmd /k "adb shell ftmdaemon -n -dd"
```

- Opens a new command window titled "FTM Mode"
- Launches FTM daemon via ADB shell
- `-n`: No console mode
- `-dd`: Debug display mode

### WiFi_FTM_close.bat

```batch
start "Close" cmd /k "python .\src\lowsheen_lib\RF_tool\FTM_On\PythonSubprocess_close.py"
```

- Opens a new command window titled "Close"
- Executes Python cleanup script

---

## Test Plan Integration

### Walrus_FCT1_testPlan.csv

```csv
ID,ItemKey,ValueType,LimitType,EqLimit,LL,UL,PassOrFail,measureValue,ExecuteName,case,Port,Baud,Command,InitialCommand,Timeout,WaitmSec,Instrument,Channel,Item,Type,ImagePath,content,keyWord,spiltCount,splitLength
console,FT00-000,string,none,,,,,,CommandTest,console,,,python .\src\lowsheen_lib\RF_tool\FTM_On\PythonSubprocess_FTM_Entrance.py,,,,,,,,,,,,
TX2,FT00-000,string,none,,,,,,CommandTest,console,,,.\src\lowsheen_lib\RF_tool\FTM_On\API_WIFI_TxOn_chain2_AutoDetect.exe,,,,,,,,,,,,
close,FT00-000,string,none,,,,,,CommandTest,console,,,python .\src\lowsheen_lib\RF_tool\FTM_On\PythonSubprocess_close_Entrance.py,,,,,,,,,,,,
```

**Test Sequence:**
1. **console**: Open FTM mode via `PythonSubprocess_FTM_Entrance.py`
2. **TX2**: Execute Chain 2 TX test via `API_WIFI_TxOn_chain2_AutoDetect.exe`
3. **close**: Cleanup windows via `PythonSubprocess_close_Entrance.py`

**Note:** For Chain 1 testing, replace TX2 row with:
```csv
TX1,FT00-000,string,none,,,,,,CommandTest,console,,,.\src\lowsheen_lib\RF_tool\FTM_On\API_WIFI_TxOn_chain1_AutoDetect.exe,,,,,,,,,,,,
```

---

## Dependencies

### External Tools

| Tool | Purpose |
|------|---------|
| `adb` | Android Debug Bridge for device communication |
| `pyautogui` | Python GUI automation library |
| `ftmdaemon` | Qualcomm FTM daemon (on-device) |

### DLL Libraries

| Library | Purpose |
|---------|---------|
| `QMSL_MSVC10R.dll` | Qualcomm Mobile Station Modem Library |
| `QMSLFastConnect_MSVC10R.dll` | QMSL Fast Connect wrapper |

### Executables

| Executable | Purpose |
|------------|---------|
| `API_WIFI_TxOn_chain1_AutoDetect.exe` | TX Chain 1 power test with auto-detection |
| `API_WIFI_TxOn_chain2_AutoDetect.exe` | TX Chain 2 power test with auto-detection |

---

## Configuration

### ADB Commands Reference

| Command | Purpose |
|---------|---------|
| `adb root` | Restart adbd with root permissions |
| `adb remount` | Remount /system as writable (requires root) |
| `adb shell rmmod qca6390` | Remove Qualcomm WiFi driver |
| `adb shell insmod <module> con_mode_ftm=5` | Load driver in FTM mode |
| `adb shell ifconfig wlan0 up` | Enable WiFi interface |
| `adb shell ftmdaemon -n -dd` | Start FTM daemon |

### FTM Mode Parameter (con_mode_ftm)

| Value | Mode |
|-------|------|
| 0 | Normal mode |
| 5 | FTM (Factory Test Mode) |

---

## Window Management

### Window Titles

| Title | Purpose | Lifecycle |
|-------|---------|-----------|
| "Entrance" | FTM setup process | Created by WiFi_FTM_Entrance.bat, closed by PythonSubprocess_FTM.py |
| "FTM Mode" | FTM daemon | Created by WiFi_FTM.bat, closed by PythonSubprocess_close.py |
| "Close" | Cleanup process | Created by WiFi_FTM_close.bat, self-closes |

### Window Close Mechanism

The `close_window()` function uses a two-step process:
1. `window.activate()` - Bring window to foreground
2. `pyautogui.hotkey('alt', 'f4')` - Send Alt+F4 to close

**Limitations:**
- Requires Windows OS (pyautogui specific)
- Window must have exact title match
- Fails if window is not responding

---

## Error Handling

### Current Implementation

The current code has minimal error handling:
- `subprocess.run()` return values are not checked
- No exception handling for ADB failures
- No timeout mechanisms
- Window close failures only print to console

### Potential Failure Points

1. **ADB not connected**: All ADB commands will fail
2. **Driver module not found**: `insmod` will fail
3. **Device not rooted**: `adb root` and `remount` will fail
4. **Window title mismatch**: `close_window()` returns False
5. **pyautogui permissions**: May fail on locked systems

---

## Known Issues

1. **No Driver Restoration**: After FTM test, device remains in FTM mode until reboot
2. **Window Management Fragility**: Relies on exact window titles and pyautogui
3. **No Verification**: ADB commands are not verified for success
4. **Hardcoded Paths**: All paths use Windows backslashes and relative paths
5. **No Timeout**: Infinite wait if commands hang
6. **Chain Test Separate**: Chain 1 and Chain 2 require separate executables

---

## Usage Example

### Running Chain 1 TX Test

```bash
# Method 1: Via PDTool4 test plan
# Use Walrus_FCT1_testPlan.csv with TX1 row

# Method 2: Direct execution
python .\src\lowsheen_lib\RF_tool\FTM_On\PythonSubprocess_FTM_Entrance.py
# Wait for completion
python .\src\lowsheen_lib\RF_tool\FTM_On\PythonSubprocess_close_Entrance.py
```

### Expected Output

```
Open FTM Entrance

Send command: adb root

Send command: adb remount

Send command: adb shell rmmod qca6390

Send command: adb shell insmod vendor/lib/modules/qca_cld3_qca6390.ko con_mode_ftm=5

Send command: adb shell ifconfig wlan0 up

Send command: adb shell ftmdaemon -n -dd

Send command: API_WIFI_TxOn_chain1_AutoDetect.exe
Success close window: Entrance
```

---

## Integration with PDTool4

### CommandTest Type

The FTM_On module integrates with PDTool4's `CommandTest` measurement type:

```python
# In test plan CSV:
# ExecuteName: CommandTest
# Command: python .\src\lowsheen_lib\RF_tool\FTM_On\PythonSubprocess_FTM_Entrance.py
```

This allows FTM testing to be included in automated test sequences alongside other measurements.

---

## Future Improvements

### Suggested Enhancements

1. **Process Verification**: Check return codes from subprocess calls
2. **Timeout Handling**: Add timeouts to prevent hanging
3. **Driver Restoration**: Reload driver in normal mode after testing
4. **Error Recovery**: Retry logic for transient failures
5. **Cross-Platform**: Replace pyautogui with platform-agnostic solution
6. **Chain Selection**: Single executable with chain parameter
7. **Configuration File**: Externalize hardcoded paths and parameters
8. **Logging**: Structured logging for debugging
9. **Status Monitoring**: Query FTM daemon for test completion
10. **Result Parsing**: Extract and return actual measurement values

---

## Technical Specifications

### Target Device
- **Chipset**: Qualcomm QCA6390
- **Driver Module**: `qca_cld3_qca6390.ko`
- **FTM Daemon**: `ftmdaemon`
- **Interface**: `wlan0`

### Test Executables
- **API Layer**: Likely uses Qualcomm QMSL API
- **Auto-Detect**: Automatic chain/power detection
- **Output**: Captured via `capture_output=True`

### Platform Requirements
- **OS**: Windows (pyautogui dependency)
- **Python**: 3.x with pyautogui
- **ADB**: Android Debug Bridge
- **Device**: Android device with USB debugging enabled

---

## Related Documentation

- [Qualcomm QMSL Library](https://github.com/quic) (proprietary, requires NDA)
- [Android ADB Documentation](https://developer.android.com/studio/command-line/adb)
- [pyautogui Documentation](https://pyautogui.readthedocs.io/)

---

**Document Version:** 1.0
**Last Updated:** 2025-01-04
**Status:** Complete Analysis
