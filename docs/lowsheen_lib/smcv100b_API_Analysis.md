# smcv100b API Analysis

## Overview

smcv100b.py is a sophisticated instrument driver for the Rohde & Schwarz SMCV100B vector signal generator. It provides high-level control for radio broadcasting test signals including DAB (Digital Audio Broadcasting), AM, and FM modulation modes. Unlike simpler SCPI-based drivers, this module uses the proprietary RsSmcv Python SDK, offering object-oriented access to complex instrument features.

**File Location:** `src/lowsheen_lib/smcv100b.py`
**Dependencies:**
- `RsSmcv` - Rohde & Schwarz SMCV SDK (proprietary)
- `remote_instrument.instrument_iniSetting` - Connection manager
- Standard: `sys`, `ast`, `time`, `re`, `pdb`

**Supported Modes:**
- **DAB (Digital Audio Broadcasting):** TDMB/DAB mode with transport stream playback
- **AM (Amplitude Modulation):** Audio AM modulation
- **FM (Frequency Modulation):** Audio FM modulation
- **IQ Modulation:** Baseband IQ signal output
- **RF Output Control:** General RF output enable/disable

## Architecture

```
smcv100b.py
├── conf (class)                 # Configuration constants
│   └── Mode (dict)             # Mode mapping: '0'→DAB, '1'→AM, '2'→FM
├── Parameter()                  # Command-line argument parser
├── Modulation Functions:
│   ├── dab()                   # DAB/TDMB control
│   ├── am()                    # AM control
│   ├── fm()                    # FM control
│   ├── iq()                    # IQ modulation control
│   └── rf()                    # RF output control
├── Utility Functions:
│   ├── initial()               # Instrument reset
│   ├── Reset()                 # Reset via RsSmcv
│   └── send_cmd_to_instrument() # Main command dispatcher
└── smcv100b_main()             # Entry point (PDTool4 integration)
```

**Design Pattern:** Command pattern with mode-based dispatching.

---

## Configuration Class

### conf.Mode Dictionary

Maps numeric mode identifiers to internal function names.

```python
class conf:
    Mode = {
        '0': 'auto_DAB',
        '1': 'auto_AM',
        '2': 'auto_FM',
    }
```

**Usage:**
```python
mode_string = conf.Mode.get('0', '')  # Returns 'auto_DAB'
mode_string = conf.Mode.get('1', '')  # Returns 'auto_AM'
mode_string = conf.Mode.get('2', '')  # Returns 'auto_FM'
```

**Purpose:** Provides human-readable names for mode selection in command parsing.

---

## Command Parsing

### Parameter(command)

Parses command-line arguments into global variables used by modulation functions.

#### Parameters
- `command` (list): Command tokens split from input string
  - Format: `['0']` for reset, or `[state, mode, freq, level, file...]`

#### Global Variables Set

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `RST` | bool | Reset flag (True if command[0]=='0') | `False` |
| `PrintHelp` | bool | Help flag (unused) | `False` |
| `State` | str | State string (unused) | `''` |
| `Out_Mode` | str | Modulation mode | `'auto_DAB'` |
| `Out_Freq` | float | RF frequency in Hz | `220.0e6` (220 MHz) |
| `Out_Level` | float | RF power in dBm | `-10.0` |
| `play_file` | str | DAB transport stream filename | `'test.ts'` |
| `file_path` | str | DAB file directory | `'/var/user/'` |

#### Command Format Examples

**Reset Command:**
```python
command = ['0']
# Sets: RST=True, all others default
```

**DAB Mode:**
```python
command = ['state', '0', '220', '-10', 'test.ts']
# Sets:
#   Out_Mode = 'auto_DAB'
#   Out_Freq = 220.0e6  (220 MHz * 1e6)
#   Out_Level = -10.0
#   play_file = 'test.ts'
```

**AM/FM Mode:**
```python
command = ['state', '1', '1000', '-20']
# Sets:
#   Out_Mode = 'auto_AM'
#   Out_Freq = 1000.0e6  (1000 MHz)
#   Out_Level = -20.0
```

#### Implementation

```python
def Parameter(command):
    global RST, MeasState, PrintHelp, State, Out_Mode, Out_Freq, Out_Level, play_file, file_path

    # Initialize defaults
    RST = False
    PrintHelp = False
    State = ''
    Out_Mode = ''
    Out_Freq = ''
    Out_Level = ''
    play_file = ''
    file_path = "/var/user/"

    if command[0] == "0":
        RST = True
    else:
        Out_Mode = conf.Mode.get(command[1], '')

        if Out_Mode == 'auto_DAB' or Out_Mode == 'auto_AM' or Out_Mode == 'auto_FM':
            Out_Freq = float(command[2]) * 1e6   # Convert MHz to Hz
            Out_Level = float(command[3])

        if Out_Mode == 'auto_DAB':
            if len(command) < 5:
                print(0, end='')
                return
            else:
                play_file = ' '.join(command[4:])  # Support filenames with spaces
```

**Important Notes:**
- Frequency is converted from MHz to Hz (multiplied by 1e6)
- DAB mode requires filename (5+ arguments)
- Filenames with spaces are supported via `' '.join(command[4:])`

---

## Modulation Control Functions

### 1. dab(instr, enable=True)

Controls DAB (Digital Audio Broadcasting) / TDMB (Terrestrial Digital Multimedia Broadcasting) mode.

#### Parameters
- `instr` (RsSmcv): RsSmcv instrument object
- `enable` (bool): True to enable DAB, False to disable

#### Returns
- `1` (int) on success
- `0` (int) on error

#### Global Variables Used
- `Out_Freq` (float): RF carrier frequency in Hz
- `Out_Level` (float): RF power level in dBm
- `play_file` (str): Transport stream filename
- `file_path` (str): Directory path for transport streams

#### Behavior

**Enable Mode (enable=True):**
1. Enable TDMB baseband
2. Enable RF output
3. Set RF frequency
4. Set RF power level
5. Configure transport stream source
6. Load transport stream file

**Disable Mode (enable=False):**
1. Disable TDMB baseband
2. Disable RF output

#### Implementation

```python
def dab(instr: RsSmcv, enable: bool = True) -> None:
    try:
        print(f"{'啟用' if enable else '禁用'} DAB 模式...", end='')

        instr.source.bb.tdmb.set_state(state=enable)

        if enable:
            print("RF 輸出已啟用")
            instr.output.state.set_value(True)

            # Set frequency and power
            instr.source.frequency.set_frequency(Out_Freq)
            instr.source.power.set_power(Out_Level)

            # Configure transport stream source
            instr.source.bb.tdmb.set_source(
                tdmb_source=enums.CodingInputSignalSource.TSPLayer
            )

            # Load transport stream file
            instr.tsGen.configure.set_play_file(
                play_file=file_path + play_file
            )
        else:
            instr.source.bb.tdmb.set_state(state=enable)
            instr.output.state.set_value(state=enable)

        return 1  # Success
    except Exception as e:
        print(f"控制DAB模式時出錯: {str(e)}", end='')
        return 0  # Error
```

#### RsSmcv SDK Calls

| Method | Purpose | Parameters |
|--------|---------|------------|
| `source.bb.tdmb.set_state()` | Enable/disable TDMB baseband | `state` (bool) |
| `output.state.set_value()` | Enable/disable RF output | `state` (bool) |
| `source.frequency.set_frequency()` | Set carrier frequency | Frequency in Hz (float) |
| `source.power.set_power()` | Set RF power | Power in dBm (float) |
| `source.bb.tdmb.set_source()` | Select TDMB signal source | `tdmb_source` (enum) |
| `tsGen.configure.set_play_file()` | Load transport stream file | `play_file` (str, full path) |

#### Transport Stream Configuration

**File Path Construction:**
```python
full_path = file_path + play_file
# Example: "/var/user/" + "test.ts" = "/var/user/test.ts"
```

**Source Options:**
- `enums.CodingInputSignalSource.TSPLayer` - Use transport stream player
- `enums.CodingInputSignalSource.TESTsignal` - Use test signal (commented out)

#### Error Handling
- Catches all exceptions
- Prints error message (Chinese)
- Returns `0` on failure instead of raising exception

---

### 2. am(instr, enable=True)

Controls AM (Amplitude Modulation) audio mode.

#### Parameters
- `instr` (RsSmcv): RsSmcv instrument object
- `enable` (bool): True to enable AM, False to disable

#### Returns
- `1` (int) on success
- `0` (int) on error

#### Global Variables Used
- `Out_Freq` (float): RF carrier frequency in Hz
- `Out_Level` (float): RF power level in dBm

#### Behavior

**Enable Mode (enable=True):**
1. Enable AM baseband
2. Enable RF output
3. Set RF frequency
4. Set RF power level

**Disable Mode (enable=False):**
1. Disable AM baseband
2. Disable RF output

#### Implementation

```python
def am(instr: RsSmcv, enable: bool = True) -> None:
    try:
        if enable:
            print("連接到audio AM...", end='')
            instr.source.bb.radio.am.set_state(state=enable)
            instr.output.state.set_value(enable)

            # Set frequency and power
            instr.source.frequency.set_frequency(Out_Freq)
            instr.source.power.set_power(Out_Level)
        else:
            print("關閉audio AM...", end='')
            instr.source.bb.radio.am.set_state(state=enable)
            instr.output.state.set_value(enable)

        return 1  # Success
    except Exception as e:
        print(f"控制AM程序執行出錯: {str(e)}", end='')
        if 'instr' in locals():
            instr.close()
        return 0  # Error
```

#### RsSmcv SDK Calls

| Method | Purpose | Parameters |
|--------|---------|------------|
| `source.bb.radio.am.set_state()` | Enable/disable AM modulation | `state` (bool) |
| `output.state.set_value()` | Enable/disable RF output | `state` (bool) |
| `source.frequency.set_frequency()` | Set carrier frequency | Frequency in Hz (float) |
| `source.power.set_power()` | Set RF power | Power in dBm (float) |

#### Audio Source

**Default AM Audio Source:** Internal audio generator (not configurable in this function).

**Note:** For external audio input, additional SDK calls would be needed (not implemented).

---

### 3. fm(instr, enable=True)

Controls FM (Frequency Modulation) audio mode.

#### Parameters
- `instr` (RsSmcv): RsSmcv instrument object
- `enable` (bool): True to enable FM, False to disable

#### Returns
- `1` (int) on success
- `0` (int) on error

#### Global Variables Used
- `Out_Freq` (float): RF carrier frequency in Hz
- `Out_Level` (float): RF power level in dBm

#### Behavior

**Enable Mode (enable=True):**
1. Enable FM baseband
2. Enable RF output
3. Set RF frequency
4. Set RF power level

**Disable Mode (enable=False):**
1. Disable FM baseband
2. Disable RF output

#### Implementation

```python
def fm(instr: RsSmcv, enable: bool = True) -> None:
    try:
        if enable:
            print("連接到audio FM...", end='')
            instr.source.bb.radio.fm.set_state(state=enable)
            instr.output.state.set_value(True)
            instr.source.frequency.set_frequency(Out_Freq)
            instr.source.power.set_power(Out_Level)
        else:
            print("關閉audio FM...", end='')
            instr.source.bb.radio.fm.set_state(state=enable)
            instr.output.state.set_value(enable)

        return 1  # Success
    except Exception as e:
        print(f"控制FM程序執行出錯: {str(e)}", end='')
        if 'instr' in locals():
            instr.close()
        return 0  # Error
```

#### RsSmcv SDK Calls

| Method | Purpose | Parameters |
|--------|---------|------------|
| `source.bb.radio.fm.set_state()` | Enable/disable FM modulation | `state` (bool) |
| `output.state.set_value()` | Enable/disable RF output | `state` (bool) |
| `source.frequency.set_frequency()` | Set carrier frequency | Frequency in Hz (float) |
| `source.power.set_power()` | Set RF power | Power in dBm (float) |

---

### 4. iq(instr, enable=True)

Controls IQ modulation output (baseband IQ signal).

#### Parameters
- `instr` (RsSmcv): RsSmcv instrument object
- `enable` (bool): True to enable IQ, False to disable

#### Returns
- `1` (int) on success
- `0` (int) on error

#### Global Variables Used
- None (IQ state only)

#### Implementation

```python
def iq(instr: RsSmcv, enable: bool = True) -> None:
    try:
        if enable:
            instr.source.iq.set_state(state=enable)
        else:
            instr.source.iq.set_state(state=enable)
        return 1  # Success
    except Exception as e:
        print(f"程序執行出錯: {str(e)}", end='')
        if 'instr' in locals():
            instr.close()
        return 0  # Error
```

**Note:** This function only controls IQ output state without setting frequency/power.

---

### 5. rf(instr, enable=True)

Controls general RF output without modulation configuration.

#### Parameters
- `instr` (RsSmcv): RsSmcv instrument object
- `enable` (bool): True to enable RF, False to disable

#### Returns
- `1` (int) on success
- `0` (int) on error

#### Global Variables Used
- None (RF state only)

#### Implementation

```python
def rf(instr: RsSmcv, enable: bool = True) -> None:
    try:
        if enable:
            instr.output.state.set_value(state=enable)
        else:
            instr.output.state.set_value(state=enable)
        return 1  # Success
    except Exception as e:
        print(f"程序執行出錯: {str(e)}", end='')
        if 'instr' in locals():
            instr.close()
        return 0  # Error
```

**Use Case:** Quick RF output on/off without changing modulation settings.

---

## Utility Functions

### 1. initial(instrument)

Resets the instrument to factory defaults using the SDK's reset method.

#### Parameters
- `instrument`: Raw connection object (from `instrument_iniSetting`)

#### Implementation

```python
def initial(instrument):
    try:
        inst = RsSmcv(instrument)
        inst.utilities.reset()
    except Exception as e:
        print(f"Not connected: {str(e)}", end='')
```

**Note:** Creates temporary RsSmcv wrapper around connection object.

---

### 2. Reset()

Resets the instrument using the global `inst` object.

#### Returns
- `1` (int) on success

#### Implementation

```python
def Reset():
    print(inst.utilities.query_str('*IDN?'), end='')
    inst.utilities.reset()
    return 1
```

**Note:** Queries *IDN? before reset (for logging).

---

### 3. send_cmd_to_instrument(instrument, command)

Main command dispatcher that creates RsSmcv object and routes commands to appropriate modulation functions.

#### Parameters
- `instrument`: Raw connection object (from `instrument_iniSetting`)
- `command` (list): Parsed command tokens

#### Returns
- `1` (int) on success
- `0` (int) on error

#### Behavior

1. **Create RsSmcv wrapper** around connection object
2. **Validate connection** (check if active and responds to *IDN?)
3. **Parse command** via `Parameter(command)`
4. **Route to function:**
   - `RST == True` → `Reset()`
   - `Out_Mode == 'auto_DAB'` → `dab(inst, True)`
   - `Out_Mode == 'auto_AM'` → `am(inst, True)`
   - `Out_Mode == 'auto_FM'` → `fm(inst, True)`

#### Implementation

```python
def send_cmd_to_instrument(instrument, command):
    global inst
    try:
        inst = RsSmcv(instrument)

        # Validate connection
        if not inst.utilities.is_connection_active():
            return 0

        if inst.utilities.query_str('*IDN?') == "":
            return 0

        # Parse and execute
        Parameter(command)

        if RST == True:
            Reset()
        elif Out_Mode == "auto_DAB":
            response_str = dab(inst, True)
        elif Out_Mode == 'auto_AM':
            response_str = am(inst, True)
        else:  # Out_Mode == 'auto_FM'
            response_str = fm(inst, True)

        return response_str

    except Exception as e:
        print(f"程序執行出錯: {str(e)}", end='')
    finally:
        if 'inst' in locals():
            inst.close()
```

#### Connection Validation

**Two-level validation:**
1. `is_connection_active()` - Check socket/VISA connection
2. `query_str('*IDN?')` - Verify instrument responds

---

## PDTool4 Integration

### smcv100b_main(test_uid, TestParams, SNIndex)

Entry point for PDTool4 test framework integration.

#### Parameters
- `test_uid` (str): Test sequence identifier
  - `'--final'` for cleanup
  - Other values for normal operation
- `TestParams` (dict): Test parameters dictionary
  - `'Instrument'` (str): Instrument name from test_xml.ini
  - `'Command'` (str): Space-separated command string
- `SNIndex`: Serial number index (passed to `instrument_iniSetting`)

#### Returns
- `str`: "1" on success, "0" or error message on failure

#### Implementation

```python
def smcv100b_main(test_uid, TestParams, SNIndex):
    sequence = test_uid
    args = TestParams
    SNIndex = SNIndex

    Instrument_value = args.get('Instrument', '')
    command = args.get('Command', '321')
    command = command.split()  # Convert string to list

    # Connect to instrument
    instrument = instrument_iniSetting(Instrument_value, SNIndex)
    if instrument is None:
        print("instrument is None")
        sys.exit(10)

    # Execute command
    if sequence == '--final':
        response = initial(instrument)
    else:
        response = send_cmd_to_instrument(instrument, command)

    print(response)
    return str(response)
```

#### Integration Example

**From PowerSetMeasurement.py (hypothetical):**
```python
test_params = {
    'Instrument': 'SMCV100B_1',
    'Command': 'state 0 220 -10 test.ts'  # DAB mode
}
result = smcv100b_main('dab_test', test_params, 0)
if result == '1':
    print("DAB signal activated")
```

#### Cleanup Mode

**Cleanup command:**
```python
result = smcv100b_main('--final', {'Instrument': 'SMCV100B_1'}, 0)
# Resets instrument to defaults
```

---

## Command-Line Interface (Legacy)

The module originally supported standalone CLI usage (now commented out):

```python
# if __name__ == "__main__":
#     sequence = sys.argv[1]
#     args = sys.argv[2]
#     args = ast.literal_eval(args)
#     SNIndex = sys.argv[3]
```

**Example Usage (if uncommented):**
```bash
python smcv100b.py normal "{'Instrument': 'SMCV100B_1', 'Command': 'state 0 220 -10 test.ts'}" 0
```

---

## RsSmcv SDK Overview

### SDK Architecture

The RsSmcv SDK provides object-oriented access to SMCV100B features:

```
RsSmcv(connection)
├── utilities                    # Connection management
│   ├── reset()                 # Reset instrument
│   ├── query_str()            # Query SCPI commands
│   ├── is_connection_active() # Check connection status
│   └── idn_string             # *IDN? response
├── source                      # Signal source configuration
│   ├── frequency              # RF frequency
│   │   └── set_frequency()
│   ├── power                  # RF power
│   │   └── set_power()
│   ├── bb                     # Baseband configuration
│   │   ├── tdmb              # DAB/TDMB
│   │   │   ├── set_state()
│   │   │   └── set_source()
│   │   └── radio             # AM/FM
│   │       ├── am.set_state()
│   │       └── fm.set_state()
│   └── iq                     # IQ modulation
│       └── set_state()
├── output                      # RF output control
│   └── state.set_value()
└── tsGen                       # Transport stream generator
    └── configure.set_play_file()
```

### Key SDK Features

**Connection Management:**
```python
inst = RsSmcv(visa_resource)
inst.utilities.is_connection_active()  # Returns bool
inst.utilities.query_str('*IDN?')     # Returns string
inst.close()
```

**Frequency/Power:**
```python
inst.source.frequency.set_frequency(220e6)  # 220 MHz
inst.source.power.set_power(-10.0)          # -10 dBm
```

**Modulation Control:**
```python
inst.source.bb.tdmb.set_state(True)
inst.source.bb.radio.am.set_state(True)
inst.source.bb.radio.fm.set_state(True)
```

**Output Control:**
```python
inst.output.state.set_value(True)   # RF ON
inst.output.state.set_value(False)  # RF OFF
```

---

## Configuration

Instrument connections configured in `test_xml.ini`:

```ini
[Setting]
SMCV100B_1 = TCPIP0::192.168.1.200::5025::SOCKET
```

**Connection Type:** TCPIP Socket (SCPI-RAW protocol)

---

## Error Handling

### Current Implementation

**Pattern:**
```python
try:
    # Operations
    return 1  # Success
except Exception as e:
    print(f"Error message: {str(e)}", end='')
    if 'instr' in locals():
        instr.close()
    return 0  # Error
```

### Error Scenarios

| Scenario | Detection | Return Value |
|----------|-----------|--------------|
| Connection failed | `instrument is None` | `sys.exit(10)` |
| Instrument not responding | `*IDN?` empty | `0` |
| Connection not active | `is_connection_active()` | `0` |
| SDK exception | `Exception` caught | `0` |
| Missing DAB file | `len(command) < 5` | Prints `0` |

### Limitations

❌ **No Specific Error Types:** All errors return `0` or `sys.exit(10)`
❌ **No Error Details:** Limited error information for debugging
❌ **No Logging:** Only prints to stdout
❌ **No Retry Logic:** Single attempt

---

## Best Practices

### 1. Always Validate Connection

```python
instrument = instrument_iniSetting('SMCV100B_1', SNIndex)
if instrument is None:
    raise ConnectionError("Cannot connect to SMCV100B")
```

### 2. Check Return Values

```python
result = smcv100b_main('dab_test', params, 0)
if result != '1':
    print(f"SMCV100B operation failed: {result}")
```

### 3. Always Call Cleanup

```python
try:
    result = smcv100b_main('test', params, 0)
    # ... test operations ...
finally:
    smcv100b_main('--final', {'Instrument': 'SMCV100B_1'}, 0)
```

### 4. Validate Parameters Before Calling

```python
def validate_dab_params(freq_mhz, power_dbm, filename):
    assert 400 <= freq_mhz <= 3000, "Frequency out of range (400-3000 MHz)"
    assert -145 <= power_dbm <= 20, "Power out of range (-145 to 20 dBm)"
    assert os.path.exists(f"/var/user/{filename}"), "Transport stream file not found"
```

---

## Usage Examples

### Example 1: DAB Signal Generation

```python
# Test parameters
params = {
    'Instrument': 'SMCV100B_1',
    'Command': 'state 0 220 -10 radio_test.ts'
    # Mode 0 = DAB, 220 MHz, -10 dBm, file: radio_test.ts
}

# Activate DAB signal
result = smcv100b_main('dab_test', params, 0)
if result == '1':
    print("DAB signal active at 220 MHz, -10 dBm")
    # ... perform measurements ...
else:
    print("Failed to activate DAB signal")

# Cleanup
smcv100b_main('--final', {'Instrument': 'SMCV100B_1'}, 0)
```

### Example 2: AM Signal Generation

```python
# Test parameters
params = {
    'Instrument': 'SMCV100B_1',
    'Command': 'state 1 1000 -20'
    # Mode 1 = AM, 1000 MHz, -20 dBm
}

# Activate AM signal
result = smcv100b_main('am_test', params, 0)
if result == '1':
    print("AM signal active at 1000 MHz, -20 dBm")
else:
    print("Failed to activate AM signal")

# Cleanup
smcv100b_main('--final', {'Instrument': 'SMCV100B_1'}, 0)
```

### Example 3: FM Signal Generation

```python
# Test parameters
params = {
    'Instrument': 'SMCV100B_1',
    'Command': 'state 2 98.5 -15'
    # Mode 2 = FM, 98.5 MHz, -15 dBm
}

# Activate FM signal
result = smcv100b_main('fm_test', params, 0)
if result == '1':
    print("FM signal active at 98.5 MHz, -15 dBm")
else:
    print("Failed to activate FM signal")

# Cleanup
smcv100b_main('--final', {'Instrument': 'SMCV100B_1'}, 0)
```

### Example 4: Instrument Reset

```python
# Reset to factory defaults
params = {
    'Instrument': 'SMCV100B_1',
    'Command': '0'  # Reset command
}

result = smcv100b_main('reset', params, 0)
if result == '1':
    print("Instrument reset successful")
```

---

## Comparison with Other Drivers

### smcv100b.py vs PSW3072.py

| Feature | smcv100b.py | PSW3072.py |
|---------|-------------|------------|
| Protocol | RsSmcv SDK (OOP) | SCPI commands (text) |
| Complexity | High (DAB/AM/FM) | Low (voltage/current) |
| Error Handling | Try-except with returns | Minimal |
| Connection Validation | 2-level (active + *IDN?) | None |
| Parameter Parsing | Complex (mode-based) | Simple (2 parameters) |
| Return Values | 1/0 (int) | 1/str (mixed) |
| Cleanup Support | Yes (--final) | Yes (--final) |

### smcv100b.py vs IT6723C.py

| Feature | smcv100b.py | IT6723C.py |
|---------|-------------|------------|
| SDK Usage | Proprietary (RsSmcv) | Standard (PyVISA) |
| Query Support | Yes (via SDK) | Yes (SCPI) |
| Measurement | No | Yes (voltage/current) |
| Mode Complexity | High (3+ modes) | Low (on/off) |
| File Handling | Yes (transport streams) | No |

---

## Troubleshooting

### Issue: "instrument is None"
**Cause:** Cannot connect to SMCV100B
**Solutions:**
1. Check network connection (ping 192.168.1.200)
2. Verify IP address in test_xml.ini
3. Check firewall settings (port 5025)
4. Restart instrument

### Issue: "Not connected" error
**Cause:** Instrument connection lost during operation
**Solutions:**
1. Check network stability
2. Verify instrument is powered on
3. Check VISA library installation
4. Try `inst.utilities.reset()`

### Issue: DAB playback fails (returns 0)
**Cause:** Transport stream file not found
**Solutions:**
1. Verify file exists: `ls /var/user/test.ts`
2. Check file permissions (readable)
3. Ensure correct filename (case-sensitive)
4. Use full path in `file_path` variable

### Issue: Connection timeout
**Cause:** Instrument not responding to *IDN?
**Solutions:**
1. Increase timeout: `instrument.timeout = 10000`
2. Check instrument SCPI interface is enabled
3. Verify TCPIP socket is configured correctly
4. Try resetting instrument manually

---

## Future Enhancements

### Recommended Improvements

1. **Add Disable Functions:**
   ```python
   def disable_dab(instr):
       return dab(instr, enable=False)

   def disable_am(instr):
       return am(instr, enable=False)

   def disable_fm(instr):
       return fm(instr, enable=False)
   ```

2. **Add Query Functions:**
   ```python
   def query_frequency(instr):
       return instr.source.frequency.get_frequency()

   def query_power(instr):
       return instr.source.power.get_power()

   def query_output_state(instr):
       return instr.output.state.get_value()
   ```

3. **Add Parameter Validation:**
   ```python
   FREQ_RANGE = (100e6, 6e9)  # 100 MHz to 6 GHz
   POWER_RANGE = (-145, 20)   # -145 to +20 dBm

   def validate_rf_params(freq, power):
       if not (FREQ_RANGE[0] <= freq <= FREQ_RANGE[1]):
           raise ValueError(f"Frequency {freq/1e6} MHz out of range")
       if not (POWER_RANGE[0] <= power <= POWER_RANGE[1]):
           raise ValueError(f"Power {power} dBm out of range")
   ```

4. **Add Error Details:**
   ```python
   def dab(instr, enable=True):
       try:
           # ... operations ...
           return (1, "Success")
       except Exception as e:
           return (0, f"DAB error: {str(e)}")
   ```

5. **Add Logging:**
   ```python
   import logging

   def send_cmd_to_instrument(instrument, command):
       logging.info(f"Command: {command}")
       try:
           # ... operations ...
           logging.info(f"Success: {response_str}")
       except Exception as e:
           logging.error(f"Failed: {str(e)}")
   ```

---

## Summary

**smcv100b.py Characteristics:**

✅ **Strengths:**
- High-level SDK abstraction (RsSmcv)
- Complex modulation support (DAB/AM/FM)
- Connection validation (2-level)
- Mode-based command routing
- Transport stream file support
- Error handling with graceful degradation

⚠️ **Limitations:**
- No query functions for verification
- No parameter validation
- Limited error details
- No logging capability
- Mixed global variables usage
- Chinese error messages (localization issue)

**Use Case:** Ideal for RF test environments where:
- DAB/AM/FM broadcasting tests are required
- Transport stream playback is needed
- Complex modulation schemes are tested
- Rohde & Schwarz instruments are used

**For Production:** Consider adding parameter validation, enhanced error reporting, logging, and query functions for verification.
