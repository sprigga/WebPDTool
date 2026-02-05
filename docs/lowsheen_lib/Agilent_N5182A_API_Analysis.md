# Agilent N5182A API Analysis

## Overview

The Agilent N5182A API is a Python-based instrument control library for the Agilent N5182A MXG X-Series Signal Generator. This module provides a command-line interface for controlling the signal generator's output parameters including frequency, amplitude, output state, and waveform modes.

**File Location:** `src/lowsheen_lib/Agelient_N5182A_API/Agilent_N5182A_API.py`

**Primary Dependencies:**
- `pyvisa` - VISA library for instrument communication
- `re` - Regular expression operations (imported but not actively used)
- `sys` - System-specific parameters and functions

---

## Architecture

### Module Structure

```
Agelient_N5182A_API/
├── Agilent_N5182A_API.py    # Main API implementation
├── Agilent_N5182A_API.exe    # Compiled executable version
├── Agilent N5182A API [chr]??[chr]???.pptx  # Documentation (PowerPoint)
└── Helper Command.txt        # Command-line help reference
```

### Design Pattern

The module follows a **procedural programming** pattern with:
- Configuration class for constants mapping
- Global variables for state management
- Sequential function execution (Parameter → Connect → Run → Close)

---

## API Reference

### Command-Line Interface

The API accepts 7 command-line arguments:

| Index | Parameter | Type | Description | Valid Values |
|-------|-----------|------|-------------|--------------|
| 1 | `Index` | string | GPIB interface index | e.g., "0" for `GPIB0::16::INSTR` |
| 2 | `Address` | string | GPIB device address | e.g., "16" for `GPIB0::16::INSTR` |
| 3 | `Output` | string | Output state | "0"=RST, "1"=OFF, "2"=ON |
| 4 | `Frequency` | string | Output frequency | Numerical with unit suffix (K/M/G) |
| 5 | `Amplitude` | string | Output power | Numerical in dBm |
| 6 | `Mode` | string | Signal mode | "1"=CW, "2"=ARB |
| 7 | `Shape` | string | ARB waveform (Mode 2 only) | "1"=SINE, "2"=RAMP |

### Usage Examples

```bash
# Show help
python Agilent_N5182A_API.py /h

# Set CW mode: 100KHz frequency, -10dBm amplitude, ON state
python Agilent_N5182A_API.py 0 16 2 100K -10 1

# Set ARB mode with RAMP waveform
python Agilent_N5182A_API.py 0 16 2 50M 0 2 2

# Reset instrument
python Agilent_N5182A_API.py 0 16 0
```

---

## Code Analysis

### Configuration Class

```python
class conf:
    Output = {
        '0': 'RST',    # Reset instrument
        '1': 'OFF',    # RF output off
        '2': 'ON',     # RF output on
    }
    Shape = {
        '1': 'SINE_TEST_WFM',  # Sine waveform
        '2': 'RAMP_TEST_WFM',  # Ramp waveform
    }
```

**Insight:** The configuration class uses string keys ('0', '1', '2') to map command-line arguments to instrument command values. This design allows for easy extension with new output states or waveform shapes.

---

### Global Variables

The following global variables are defined in the `Parameter()` function:

| Variable | Default | Purpose |
|----------|---------|---------|
| `RST` | False | Reset flag |
| `PrintHelp` | False | Help display flag |
| `Index` | '0' | GPIB interface index |
| `Address` | '22' | GPIB device address |
| `Output` | None | Output state (RST/OFF/ON) |
| `Freq` | None | Frequency string |
| `Ampl` | None | Amplitude string |
| `Mode` | None | Mode (CW/ARB) |
| `Shape` | None | ARB waveform shape |
| `Trig` | None | Trigger mode (commented out) |
| `instr` | None | VISA instrument session |

---

### Function Reference

#### `Parameter()`

Parses command-line arguments and populates global variables.

**Signature:** `def Parameter()`

**Behavior:**
- Checks for help flag (`/h`, `help`, `\h`)
- Parses arguments into global variables
- Maps output state and shape using `conf` class
- Handles optional arguments for frequency, amplitude, mode

**Code:**
```python
def Parameter():
    global RST,PrintHelp,Index,Address,Output,Freq,Ampl,Mode,Shape,Trig
    RST         = False
    PrintHelp   = False
    Index       = '0'
    Address     = '22'

    if len(sys.argv) > 1:
        if sys.argv[1] == "help" or sys.argv[1] == "/h" or sys.argv[1] == "\h":
            PrintHelp = True
        else:
            Index   =   sys.argv[1]
            Address =   sys.argv[2]
            Output  =   conf.Output.get(sys.argv[3], '')
            if len(sys.argv) > 4:
                Freq    =   sys.argv[4]
                Ampl    =   sys.argv[5]
                Mode    =   sys.argv[6]
                if len(sys.argv) > 7:
                    Shape   =   conf.Output.get(sys.argv[7], '')
```

---

#### `Connect()`

Establishes VISA connection to the instrument.

**Signature:** `def Connect()`

**Behavior:**
- Opens VISA resource using GPIB address format
- Sets global `instr` variable
- Exits on connection failure with error message

**Code:**
```python
def Connect():
    global instr
    try:
        instr = rm.open_resource('GPIB' + Index + '::' + Address + '::INSTR')
    except Exception as e:
        print("Could not open ViSession!")
        print("Check instruments and connections")
        print(e)
        sys.exit(0)
```

**Error Handling:** Catches connection errors and provides diagnostic messages before exiting.

---

#### `Run()`

Executes the instrument configuration based on parsed parameters.

**Signature:** `def Run()`

**Behavior Flow:**
1. If `Output == 'RST'`: calls `Reset()`
2. Otherwise:
   - Translates frequency format
   - Sets frequency via `FREQ` command
   - Sets power amplitude via `POW:AMPL` command
   - If ARB mode (Mode == '2'):
     - Sets ARB waveform
     - Configures trigger source
     - Enables ARB state and modulation
   - Sets output state if ON or OFF
   - Queries and prints confirmation

**Code:**
```python
def Run():
    if Output == 'RST':
        Reset()
    else:
        Freqency = translate_fre(Freq)
        instr.write('FREQ ' + Freqency + 'Hz')        # Set frequency
        instr.write('POW:AMPL ' + Ampl + ' dBm')      # Set power

        if Mode == '2':  # ARB Mode
            instr.write(':SOURce:RADio:ARB:WAVeform "WFM1:' + Shape + '"')
            instr.write(':PULM:SOUR:INT FRUN')          # Trigger Free Run
            instr.write(':SOURce:RADio:ARB:STATe ON')   # ARB Mode On
            instr.write(':OUTPut:MODulation:STATe ON')

        if Output == 'ON' or Output == 'OFF':
            instr.write('OUTP:STAT ' + Output)

        # Query status confirmation
        cw_freq = instr.query('FREQ:CW?')
        print(f"Source frequency is : {cw_freq.strip()}")

        power = instr.query('POW:AMPL?')
        print(f"Source power (dBm) is : {power.strip()}")

        rf_state_off = instr.query('OUTP?')
        rf_state_off = 'on' if int(rf_state_off) > 0 else 'off'
        print(f"Source RF state is now: {rf_state_off}")
```

---

#### `Reset()`

Resets the instrument to default settings.

**Signature:** `def Reset()`

**Behavior:**
- Queries and prints instrument identification
- Sends `*RST` SCPI command

**Code:**
```python
def Reset():
    print(instr.query('*IDN?'),end='')
    instr.write('*RST')
```

---

#### `Close()`

Closes the VISA instrument session and resource manager.

**Signature:** `def Close()`

**Code:**
```python
def Close():
    instr.close()
    rm.close()
```

---

#### `translate_fre()`

Translates frequency string from compact format (K/M/G suffix) to SCPI format.

**Signature:** `def translate_fre(Freq)`

**Input/Output Examples:**
| Input | Output |
|-------|--------|
| `"100K"` | `"100 k"` |
| `"50M"` | `"50 m"` |
| `"600G"` | `"600 g"` |
| `"1000"` | `"1000 "` |

**Code:**
```python
def translate_fre(Freq):
    unit = Freq[-1].upper()
    if unit =='K' or unit =='M' or unit =='G':
        if unit =='K':    Freq = Freq[:-1] + ' k'
        if unit =='M':    Freq = Freq[:-1] + ' m'
        if unit =='G':    Freq = Freq[:-1] + ' g'
    else:
        Freq = Freq +' '
    return Freq
```

---

#### `help()`

Prints command-line usage information.

**Signature:** `def help()`

**Note:** This function is defined but never called directly. The `PrintHelp` flag triggers the help output in `main()`.

---

## SCPI Commands Reference

The following SCPI (Standard Commands for Programmable Instruments) commands are used:

| Command | Description | Example |
|---------|-------------|---------|
| `FREQ <value>Hz` | Set frequency | `FREQ 100 kHZ` |
| `FREQ:CW?` | Query frequency | Returns current frequency |
| `POW:AMPL <value> dBm` | Set power amplitude | `POW:AMPL -10 dBm` |
| `POW:AMPL?` | Query power | Returns current power |
| `OUTP:STAT <state>` | Set RF output state | `OUTP:STAT ON` |
| `OUTP?` | Query output state | Returns 0 or 1 |
| `:SOURce:RADio:ARB:WAVeform` | Set ARB waveform | `:SOURce:RADio:ARB:WAVeform "WFM1:SINE_TEST_WFM"` |
| `:PULM:SOUR:INT FRUN` | Set trigger to free run | - |
| `:SOURce:RADio:ARB:STATe` | Set ARB mode state | `:SOURce:RADio:ARB:STATe ON` |
| `:OUTPut:MODulation:STATe` | Set modulation state | `:OUTPut:MODulation:STATe ON` |
| `*IDN?` | Query identification | Returns manufacturer, model, SN |
| `*RST` | Reset instrument | - |

---

## Operational Modes

### CW Mode (Continuous Wave)

Standard signal generator mode with fixed frequency and amplitude.

**Parameters Required:**
- Index, Address, Output (1 or 2)
- Frequency (e.g., "100K", "50M")
- Amplitude (e.g., "-10")
- Mode = "1"

**Configuration Commands:**
```python
instr.write('FREQ <frequency>Hz')
instr.write('POW:AMPL <amplitude> dBm')
instr.write('OUTP:STAT <state>')
```

### ARB Mode (Arbitrary Waveform)

Advanced mode for custom waveforms.

**Parameters Required:**
- All CW parameters plus:
- Mode = "2"
- Shape ("1" for SINE, "2" for RAMP)

**Configuration Commands:**
```python
instr.write('FREQ <frequency>Hz')
instr.write('POW:AMPL <amplitude> dBm')
instr.write(':SOURce:RADio:ARB:WAVeform "WFM1:<shape>"')
instr.write(':PULM:SOUR:INT FRUN')
instr.write(':SOURce:RADio:ARB:STATe ON')
instr.write(':OUTPut:MODulation:STATe ON')
instr.write('OUTP:STAT <state>')
```

---

## GPIB Address Format

The instrument is addressed using GPIB (General Purpose Interface Bus) format:

**Format:** `GPIB<Index>::<Address>::INSTR`

**Examples:**
- `GPIB0::16::INSTR` → Index=0, Address=16
- `GPIB0::22::INSTR` → Index=0, Address=22 (default)

**Construction in Code:**
```python
resource_string = 'GPIB' + Index + '::' + Address + '::INSTR'
instr = rm.open_resource(resource_string)
```

---

## Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    __main__ Entry Point                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │  Parameter() │  Parse command-line arguments
                  └──────┬───────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
    ┌───────────┐                 ┌──────────┐
    │ PrintHelp │                 │ Connect()│  Open VISA session
    │   == True │                 └────┬─────┘
    └─────┬─────┘                      │
          │                            ▼
          ▼                    ┌─────────────┐
    ┌───────────┐              │     Run()   │  Configure instrument
    │   help()  │              └──────┬──────┘
    └───────────┘                     │
                              ┌───────┴────────┐
                              ▼                ▼
                       ┌──────────┐     ┌──────────┐
                       │  Reset() │     │  Configure│
                       └──────────┘     │  Settings│
                                        └─────┬────┘
                                              │
                                              ▼
                                        ┌──────────┐
                                        │  Close() │  Cleanup
                                        └──────────┘
```

---

## Integration with PDTool4

This API module is designed to be called from the PDTool4 test execution system as an external process. Based on the analysis of related code:

1. **Called as Subprocess:** The module can be compiled as an `.exe` or run as a `.py` script
2. **Usage Pattern:** PDTool4 passes parameters via command-line arguments
3. **Result Verification:** Status queries confirm configuration before returning

**Typical Integration Pattern:**
```python
# From PDTool4 measurement module
subprocess.run([
    'python', 'Agilent_N5182A_API.py',
    index, address, output, freq, ampl, mode
], check=True)
```

---

## Known Limitations and Observations

1. **Unused Import:** `re` module is imported but never used in the code
2. **Commented Code:** Trigger (Index 8) functionality is partially implemented but commented out
3. **Global State:** Heavy reliance on global variables makes the module non-reentrant
4. **Error Handling:** Limited error handling in `Run()` function - VISA errors may propagate uncaught
5. **Hardcoded Values:** Some SCPI commands use hardcoded prefixes ("WFM1:")
6. **No Validation:** Frequency and amplitude values are not validated before sending to instrument

---

## Maintenance Recommendations

1. **Consider Refactoring:** Move to class-based structure for better state management
2. **Add Validation:** Validate frequency range and amplitude limits before sending commands
3. **Error Handling:** Add try-catch blocks around VISA write/query operations
4. **Remove Unused Code:** Clean up commented trigger code and unused imports
5. **Documentation:** Add docstrings to all functions
6. **Testing:** Add unit tests for frequency translation function

---

## References

- **Agilent N5182A Documentation:** Refer to manufacturer's programming guide for complete SCPI command set
- **PyVISA Documentation:** https://pyvisa.readthedocs.io/
- **SCPI Standard:** IEEE 488.2

---

*Document generated: 2026-02-04*
*Source: Agilent_N5182A_API.py (Lines 1-126)*
