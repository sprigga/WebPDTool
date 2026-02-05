# Analog Discovery 2 API Analysis

## Overview

The Analog Discovery 2 API is a Python-based instrument control library for the Digilent Analog Discovery 2 (AD2) USB oscilloscope, function generator, and impedance analyzer. This module provides Python bindings to the Digilent WaveForms SDK C API through ctypes, supporting analog waveform generation/acquisition, digital I/O operations, and impedance measurements.

**File Location:** `src/lowsheen_lib/AnalogDiscovery2Api/`

**Primary Dependencies:**
- `ctypes` - C compatible data types and FFI (Foreign Function Interface)
- `dwf` - Digilent WaveForms SDK (dwf.dll on Windows, libdwf.so on Linux)
- `numpy` - Array operations and FFT processing
- `matplotlib` - Optional plotting (commented out in production)

---

## Architecture

### Module Structure

```
AnalogDiscovery2Api/
├── API_Analog.py              # Analog waveform I/O functions
├── API_Analog.exe             # Compiled executable (88 MB)
├── API_Digital.py             # Digital I/O functions (16 DIO lines)
├── API_Digital.exe            # Compiled executable (88 MB)
├── API_Impedance.py           # Impedance measurement functions
├── API_Impedance.exe          # Compiled executable (21 MB)
├── dwfconstants.py            # WaveForms SDK constants definitions
├── API_Analog_ExampleCommand.txt  # Command-line usage examples
├── record_Analog.csv          # Sample data output
└── Analog Discovery 2 ????.pptx    # Chinese documentation
```

### Design Pattern

The modules follow a **procedural programming** pattern with:
- Platform-specific dynamic library loading
- Global device handle (`hdwf`) for connection state
- ctypes-based FFI to C API
- Command-line argument parsing for standalone execution

`★ Insight ─────────────────────────────────────`
1. **Cross-Platform Library Loading**: The code uses `sys.platform` detection to load the appropriate SDK library (dwf.dll for Windows, libdwf.so for Linux, or framework on macOS)
2. **Ctypes FFI Pattern**: Instead of using Python bindings, the module directly calls C functions via ctypes, which requires manual type conversion (c_int, c_double, byref)
`─────────────────────────────────────────────────`

---

## Platform-Specific Configuration

### Dynamic Library Loading

```python
if platform.startswith("win"):
    # Windows
    dwf = ctypes.cdll.dwf
    constants_path = "C:/Program Files (x86)/Digilent/WaveFormsSDK/samples/py"
elif platform.startswith("darwin"):
    # macOS
    lib_path = "/Library/Frameworks/dwf.framework/dwf"
    dwf = ctypes.cdll.LoadLibrary(lib_path)
    constants_path = "/Applications/WaveForms.app/Contents/Resources/SDK/samples/py"
else:
    # Linux
    dwf = ctypes.cdll.LoadLibrary("libdwf.so")
    constants_path = "/usr/share/digilent/waveforms/samples/py"
```

### SDK Installation Paths

| Platform | Library Path | Constants Path |
|----------|--------------|----------------|
| Windows | `dwf.dll` (in PATH) | `C:/Program Files (x86)/Digilent/WaveFormsSDK/samples/py` |
| Linux | `/usr/lib/libdwf.so` | `/usr/share/digilent/waveforms/samples/py` |
| macOS | `/Library/Frameworks/dwf.framework/dwf` | `/Applications/WaveForms.app/Contents/Resources/SDK/samples/py` |

---

## API Reference: API_Analog.py

### Command-Line Interface

#### Mode 0: Analog Input (Oscilloscope)

```bash
python API_Analog.py 0 <channel> <frequency> <sample_count>
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `0` | int | Input mode indicator |
| `<channel>` | int | 1 or 2 (internally converted to 0-based index) |
| `<frequency>` | string | Sample rate with unit suffix (u/m/k/M) |
| `<sample_count>` | int | Number of samples to capture |

**Example:**
```bash
python API_Analog.py 0 1 1k 1k
# Channel 1, 1kHz sample rate, 1000 samples
```

#### Mode 1: Analog Output (Function Generator)

```bash
python API_Analog.py 1 <channel> <function> <frequency> <amplitude> <offset>
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `1` | int | Output mode indicator |
| `<channel>` | int | 1 or 2 (internally converted to 0-based index) |
| `<function>` | int | 0-10 (waveform type index) |
| `<frequency>` | string | Frequency with unit suffix (u/m/k/M) |
| `<amplitude>` | string | Amplitude in V |
| `<offset>` | string | DC offset in V |

**Example:**
```bash
python API_Analog.py 1 1 1 10k 2 0
# Channel 1, Sine wave (1), 10kHz, 2V amplitude, 0V offset
```

#### Version Check

```bash
python API_Analog.py Version
```

---

### Waveform Function Types

| Index | Function | Constant | Description |
|-------|----------|----------|-------------|
| 0 | DC | `funcDC` | Constant DC output |
| 1 | Sine | `funcSine` | Sine wave |
| 2 | Square | `funcSquare` | Square wave |
| 3 | Triangle | `funcTriangle` | Triangle wave |
| 4 | RampUp | `funcRampUp` | Ramp up |
| 5 | RampDown | `funcRampDown` | Ramp down |
| 6 | Pulse | `funcPulse` | Pulse wave |
| 7 | SinePower | `funcSinePower` | Sine with power |
| 8 | Noise | `funcNoise` | Random noise |
| 9 | Custom | `funcCustom` | Custom pattern |
| 10 | Play | `funcPlay` | Playback pattern |

---

### Function Reference

#### `connet()`

Establishes connection to the first available Analog Discovery 2 device.

**Signature:** `def connet() -> c_int`

**Returns:** Device handle (`hdwf`)

**Process:**
1. Loads platform-specific dwf library
2. Gets firmware version via `FDwfGetVersion()`
3. Sets close behavior: `FDwfParamSet(DwfParamOnClose, 0)` - continue running
4. Opens first device: `FDwfDeviceOpen(c_int(-1), byref(hdwf))`
5. Returns handle or exits on failure

**Code:**
```python
def connet():
    global dwf, hdwf, channel
    if sys.platform.startswith("win"):
        dwf = cdll.dwf
    elif sys.platform.startswith("darwin"):
        dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
    else:
        dwf = cdll.LoadLibrary("libdwf.so")

    hdwf = c_int()
    version = create_string_buffer(16)
    dwf.FDwfGetVersion(version)
    print("DWF Version: " + str(version.value))

    dwf.FDwfParamSet(DwfParamOnClose, c_int(0))  # 0 = run, 1 = stop, 2 = shutdown
    print("Opening first device...")
    dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

    if hdwf.value == hdwfNone.value:
        print("failed to open device")
        quit()
    return hdwf
```

---

#### `AnalogIn(hdwf, channel, frequency, nSamples)`

Configures and runs analog input acquisition (oscilloscope mode).

**Signature:** `def AnalogIn(hdwf, channel, frequency, nSamples)`

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `hdwf` | c_int | Device handle |
| `channel` | int | Channel number (0=CH1, 1=CH2) |
| `frequency` | float | Sample rate in Hz |
| `nSamples` | int | Number of samples to capture |

**Process:**
1. Get max buffer size: `FDwfAnalogInBufferSizeInfo()`
2. Set acquisition parameters:
   - Frequency: `FDwfAnalogInFrequencySet(hdwf, c_double(frequency))`
   - Buffer size: `FDwfAnalogInBufferSizeSet(hdwf, nSamples)`
   - Enable channel: `FDwfAnalogInChannelEnableSet(hdwf, channel, 1)`
   - Range: `FDwfAnalogInChannelRangeSet(hdwf, 0, c_double(2))` (2V pk2pk)
3. Configure in auto mode: `FDwfAnalogInConfigure(hdwf, c_int(1), c_int(0))`
4. Start acquisition: `FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))`
5. Poll status until `DwfStateDone`
6. Read data: `FDwfAnalogInStatusData(hdwf, 0, rgdSamples1, nSamples)`
7. Perform FFT analysis and calculate peak frequency
8. Save to CSV: `C:/Log/AnalogDiscovery2/Analog_in/YYYYMMDD/Freq_X_Samp_Y_HHMMSS.csv`

**Output File Format:**
```csv
# Each line contains one sample value (rounded to 4 decimal places)
0.0123
-0.0456
0.0789
...
```

**FFT Analysis:**
- Uses `FDwfSpectrumFFT()` to compute frequency spectrum
- Converts to dBV: `20*log10(amplitude/sqrt(2))`
- Finds peak frequency (skipping first 5 bins for DC)
- Prints peak frequency in kHz

---

#### `AnalogOut(hdwf, channel, function, frequency, amplitude, offset)`

Generates analog output waveform.

**Signature:** `def AnalogOut(hdwf, channel, function, frequency, amplitude, offset)`

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `hdwf` | c_int | Device handle |
| `channel` | int | Channel (0=CH1, 1=CH2) |
| `function` | c_ubyte | Waveform type constant (funcDC, funcSine, etc.) |
| `frequency` | float | Frequency in Hz |
| `amplitude` | float | Amplitude in V |
| `offset` | float | Offset in V |

**Process:**
1. Set auto-configure off: `FDwfDeviceAutoConfigureSet(hdwf, c_int(0))`
2. Enable carrier node: `FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_int(1))`
3. Set waveform function: `FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, function)`
4. Set parameters:
   - Frequency: `FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(frequency))`
   - Amplitude: `FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(amplitude))`
   - Offset: `FDwfAnalogOutNodeOffsetSet(hdwf, channel, AnalogOutNodeCarrier, c_double(offset))`
5. Configure and start: `FDwfAnalogOutConfigure(hdwf, channel, c_int(1))`

**Code:**
```python
def AnalogOut(hdwf, channel, function, frequency, amplitude, offset):
    dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))
    dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_int(1))
    dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, eval(function))
    dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(frequency))
    dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(amplitude))
    dwf.FDwfAnalogOutNodeOffsetSet(hdwf, channel, AnalogOutNodeCarrier, c_double(offset))
    print("Generating sine wave...")
    dwf.FDwfAnalogOutConfigure(hdwf, channel, c_int(1))
```

---

#### `StrToNum(num)`

Converts string with unit suffix to float value.

**Signature:** `def StrToNum(num) -> float`

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `num` | str | Numeric string with optional unit suffix |

**Supported Units:**
| Unit | Multiplier | Example |
|------|------------|---------|
| `u` or `μ` | 1e-6 | `100u` → 0.0001 |
| `m` | 1e-3 | `10m` → 0.01 |
| `k` or `K` | 1e3 | `10k` → 10000 |
| `M` | 1e6 | `1M` → 1000000 |
| (none) | 1 | `100` → 100 |

**Error Handling:**
- If unit parsing fails, uses regex to extract first number: `re.findall(r'-?\d+\.?\d*', num)`

---

#### `SelectFunction(Index)`

Converts function index to string name for eval().

**Signature:** `def SelectFunction(Index) -> str`

**Index Mapping:**
| Index | Returns |
|-------|---------|
| '0' | 'DC' |
| '1' | 'Sine' |
| '2' | 'Square' |
| '3' | 'Triangle' |
| '4' | 'RampUp' |
| '5' | 'RampDown' |
| '6' | 'Pulse' |
| '7' | 'SinePower' |
| '8' | 'Noise' |
| '9' | 'Custom' |
| '10' | 'Play' |

**Note:** The returned string is prefixed with 'func' in main: `function = 'func' + function`

---

## API Reference: API_Digital.py

### Command-Line Interface

#### Mode 0: Read DIO Pin

```bash
python API_Digital.py 0 <channel>
# or
python API_Digital.py Mode=0 Channel=1
```

#### Mode 1: Set DIO Pin

```bash
python API_Digital.py 1 <channel> <state>
# or
python API_Digital.py Mode=1 Channel=1 SetState=1
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `<mode>` | int | 0=input/read, 1=output/write |
| `<channel>` | int | DIO channel (0-15) |
| `<state>` | int | 0=LOW, 1=HIGH (mode 1 only) |

---

### Function Reference

#### `open()`

Opens the first available device and returns device data container.

**Signature:** `def open() -> data`

**Returns:** `data` class instance with `handle` attribute

**Code:**
```python
class data:
    """stores the device handle and the device name"""
    handle = ctypes.c_int(0)
    name = ""

def open():
    device_handle = ctypes.c_int()
    dwf.FDwfDeviceOpen(ctypes.c_int(-1), ctypes.byref(device_handle))
    data.handle = device_handle
    return data
```

---

#### `set_mode(device_data, channel, output)`

Configures DIO pin as input or output.

**Signature:** `def set_mode(device_data, channel, output)`

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `device_data` | data class | Device data container |
| `channel` | int | DIO channel (0-15) |
| `output` | bool | True=output, False=input |

**Process:**
1. Get current output enable mask: `FDwfDigitalIOOutputEnableGet(device_data.handle, byref(mask))`
2. Convert mask to 16-bit binary string
3. Set bit at position `15 - channel` (MSB first)
4. Convert back to integer
5. Set enable mask: `FDwfDigitalIOOutputEnableSet(device_data.handle, ctypes.c_int(mask))`

`★ Insight ─────────────────────────────────────`
1. **Bit Position Mapping**: The DIO channels use MSB-first ordering (channel 0 = bit 15, channel 15 = bit 0), which is inverted from typical LSB-first conventions
2. **Mask Manipulation Pattern**: The set_mode, get_state, and set_state functions all use the same pattern: read current mask → convert to binary list → modify bit → convert back to integer
`─────────────────────────────────────────────────`

---

#### `get_state(device_data, channel)`

Reads current state of DIO pin.

**Signature:** `def get_state(device_data, channel) -> bool`

**Returns:** `True` if HIGH, `False` if LOW

**Process:**
1. Update status: `FDwfDigitalIOStatus(device_data.handle)`
2. Read input state: `FDwfDigitalIOInputStatus(device_data.handle, byref(data))`
3. Convert to binary string and check bit at position `15 - channel`

---

#### `set_state(device_data, channel, value)`

Sets DIO pin to HIGH or LOW.

**Signature:** `def set_state(device_data, channel, value)`

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `device_data` | data class | Device data container |
| `channel` | int | DIO channel (0-15) |
| `value` | bool | True=HIGH, False=LOW |

**Process:**
1. Get current output state: `FDwfDigitalIOOutputGet(device_data.handle, byref(mask))`
2. Convert to binary string
3. Set bit at position `15 - channel` based on value
4. Convert back to integer
5. Set output state: `FDwfDigitalIOOutputSet(device_data.handle, ctypes.c_int(mask))`

---

#### `closeDigital(device_data)`

Resets digital I/O interface.

**Signature:** `def closeDigital(device_data)`

**Code:**
```python
def closeDigital(device_data):
    """reset the instrument"""
    dwf.FDwfDigitalIOReset(device_data.handle)
    return
```

---

## API Reference: API_Impedance.py

### Command-Line Interface

```bash
python API_Impedance.py <mode> <start_freq> <stop_freq> <frequency> <steps> <amplitude> <reference>
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `<mode>` | int | 0=W1-C1-DUT-C2-R-GND, 1=W1-C1-R-C2-DUT-GND, 8=AD IA adapter |
| `<start_freq>` | string | Start frequency with unit suffix |
| `<stop_freq>` | string | Stop frequency with unit suffix |
| `<frequency>` | string | Single frequency to measure |
| `<steps>` | int | Number of frequency steps |
| `<amplitude>` | string | Excitation amplitude in V |
| `<reference>` | string | Reference resistor value in Ohms |

**Example:**
```bash
python API_Impedance.py 0 1k 1M 1k 151 1 1k
# Mode 0, 1kHz-1MHz sweep, 151 steps, 1V amplitude, 1kΩ reference
```

---

### Measurement Configuration

#### Global Variables

```python
ConnectMode = 0
frequency = 1e3      # Frequency in Hz
steps = 151          # Number of frequency steps
start = 1e3          # Start frequency in Hz
stop = 1e6           # Stop frequency in Hz
Amplitude = 1        # Excitation amplitude in V
reference = 1e3      # Reference resistor value in Ohms
mode = 0             # Connection mode
```

---

#### Measurement Types (20 outputs)

The `rgMeasure` array defines all 20 measurement types:

| Index | Constant | Name | Unit |
|-------|----------|------|------|
| 0 | `DwfAnalogImpedanceImpedance` | Impedance | Ohm |
| 1 | `DwfAnalogImpedanceImpedancePhase` | ImpedancePhase | Radian |
| 2 | `DwfAnalogImpedanceResistance` | Resistance | Ohm |
| 3 | `DwfAnalogImpedanceReactance` | Reactance | Ohm |
| 4 | `DwfAnalogImpedanceAdmittance` | Admittance | S |
| 5 | `DwfAnalogImpedanceAdmittancePhase` | AdmittancePhase | Radian |
| 6 | `DwfAnalogImpedanceConductance` | Conductance | S |
| 7 | `DwfAnalogImpedanceSusceptance` | Susceptance | S |
| 8 | `DwfAnalogImpedanceSeriesCapacitance` | SeriesCapacitance | F |
| 9 | `DwfAnalogImpedanceParallelCapacitance` | ParallelCapacitance | F |
| 10 | `DwfAnalogImpedanceSeriesInductance` | SeriesInductance | H |
| 11 | `DwfAnalogImpedanceParallelInductance` | ParallelInductance | H |
| 12 | `DwfAnalogImpedanceDissipation` | Dissipation | X |
| 13 | `DwfAnalogImpedanceQuality` | Quality | X |
| 14 | `DwfAnalogImpedanceVrms` | Vrms | V |
| 15 | `DwfAnalogImpedanceVreal` | Vreal | V |
| 16 | `DwfAnalogImpedanceVimag` | Vimag | V |
| 17 | `DwfAnalogImpedanceIrms` | Irms | A |
| 18 | `DwfAnalogImpedanceIreal` | Ireal | A |
| 19 | `DwfAnalogImpedanceIimag` | Iimag | A |

---

#### Connection Modes

| Mode | Configuration | Description |
|------|---------------|-------------|
| 0 | W1-C1-DUT-C2-R-GND | Standard 4-wire measurement |
| 1 | W1-C1-R-C2-DUT-GND | Alternative 4-wire |
| 8 | AD IA adapter | Impedance Analyzer adapter |

---

#### Unit Scaling

Values are automatically scaled to appropriate SI prefixes:

| Range | Prefix | Multiplier |
|-------|--------|------------|
| ≥ 1G | G | 1e9 |
| ≥ 1M | M | 1e6 |
| ≥ 1k | k | 1e3 |
| < 1 | m | 1e-3 |
| < 1e-3 | u | 1e-6 |
| < 1e-6 | n | 1e-9 |
| < 1e-9 | p | 1e-12 |

**Phase values (radians) are not scaled.**

---

#### Frequency Step Calculation

Uses exponential frequency distribution:

```python
hz = stop * pow(10.0, 1.0*(1.0*1/(steps-1)-1)*math.log10(stop/start))
```

This formula generates logarithmically spaced frequencies between start and stop.

---

## dwfconstants.py Reference

### Device Enumeration Filters

| Constant | Value | Description |
|----------|-------|-------------|
| `enumfilterAll` | 0 | All devices |
| `enumfilterUSB` | 0x0000001 | USB-connected devices |
| `enumfilterNetwork` | 0x0000002 | Network-connected devices |
| `enumfilterAXI` | 0x0000004 | AXI devices |
| `enumfilterDemo` | 0x4000000 | Demo simulation mode |

### Device IDs

| Constant | Value | Device |
|----------|-------|--------|
| `devidEExplorer` | 1 | Analog Explorer |
| `devidDiscovery` | 2 | Analog Discovery 1 |
| `devidDiscovery2` | 3 | **Analog Discovery 2** |
| `devidDDiscovery` | 4 | Digital Discovery |
| `devidADP3X50` | 6 | Analog Pro |
| `devidADP5250` | 8 | Analog Pro 5250 |

### Acquisition States

| Constant | Value | Description |
|----------|-------|-------------|
| `DwfStateReady` | 0 | Ready to configure |
| `DwfStateConfig` | 4 | Configuration mode |
| `DwfStateArmed` | 1 | Armed, waiting for trigger |
| `DwfStateRunning` | 3 | Running acquisition |
| `DwfStateDone` | 2 | Acquisition complete |

### Trigger Sources

| Constant | Value | Description |
|----------|-------|-------------|
| `trigsrcNone` | 0 | No trigger |
| `trigsrcPC` | 1 | PC/Software trigger |
| `trigsrcAnalogIn` | 4 | Internal analog input trigger |
| `trigsrcDigitalIn` | 5 | Internal digital input trigger |
| `trigsrcExternal1-4` | 11-14 | External trigger inputs |

### Analog Out Signal Types

| Constant | Value | Waveform |
|----------|-------|----------|
| `funcDC` | 0 | Constant DC |
| `funcSine` | 1 | Sine wave |
| `funcSquare` | 2 | Square wave |
| `funcTriangle` | 3 | Triangle wave |
| `funcRampUp` | 4 | Ramp up |
| `funcRampDown` | 5 | Ramp down |
| `funcNoise` | 6 | Random noise |
| `funcPulse` | 7 | Pulse wave |
| `funcCustom` | 30 | Custom waveform |
| `funcPlay` | 31 | Playback waveform |

### Analog Out Node Types

| Constant | Value | Description |
|----------|-------|-------------|
| `AnalogOutNodeCarrier` | 0 | Carrier (main) signal |
| `AnalogOutNodeFM` | 1 | Frequency modulation |
| `AnalogOutNodeAM` | 2 | Amplitude modulation |

### Parameters

| Constant | Value | Description |
|----------|-------|-------------|
| `DwfParamOnClose` | 4 | 0=continue, 1=stop, 2=shutdown |
| `DwfParamAnalogOut` | 7 | 0=disable, 1=enable analog out |
| `DwfParamFrequency` | 8 | System frequency in Hz |

---

## Execution Flow Diagrams

### Analog Input Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Line Arguments                   │
│         python API_Analog.py 0 <ch> <freq> <samples>        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │   connet()   │  Load dwf library, open device
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  AnalogIn()  │  Configure acquisition
                  └──────┬───────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌───────────────┐ ┌─────────────┐ ┌──────────────┐
│ Set Frequency │ │ Set Buffer  │ │ Enable Ch    │
└───────────────┘ └─────────────┘ └──────────────┘
        └────────────────┼────────────────┘
                         ▼
                  ┌──────────────┐
                  │   Configure  │  Start acquisition
                  │   & Start    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Poll Status  │  Wait for DwfStateDone
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Read Data    │  FDwfAnalogInStatusData()
                  └──────┬───────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌───────────────┐ ┌─────────────┐ ┌──────────────┐
│ Save to CSV   │ │ FFT Compute │ │ Find Peak    │
└───────────────┘ └─────────────┘ └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Close Device │  FDwfDeviceCloseAll()
                  └──────────────┘
```

### Digital I/O Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Line Arguments                   │
│         python API_Digital.py <mode> <channel> [state]      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │    open()    │  Open device
                  └──────┬───────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
     ┌──────────────┐         ┌──────────────┐
     │ Mode = 0     │         │ Mode = 1     │
     │ (Read)       │         │ (Write)      │
     └──────┬───────┘         └──────┬───────┘
            │                        │
            ▼                        ▼
     ┌──────────────┐         ┌──────────────┐
     │ set_mode()   │         │ set_mode()   │
     │ (input)      │         │ (output)     │
     └──────┬───────┘         └──────┬───────┘
            │                        │
            ▼                        ▼
     ┌──────────────┐         ┌──────────────┐
     │ get_state()  │         │ set_state()  │
     └──────┬───────┘         └──────┬───────┘
            │                        │
            ▼                        ▼
     ┌──────────────┐         ┌──────────────┐
     │ Print State  │         │ Set Output   │
     └──────┬───────┘         └──────┬───────┘
            └────────────────┬────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Close Device │  FDwfDeviceCloseAll()
                  └──────────────┘
```

---

## Integration with PDTool4

The Analog Discovery 2 API modules are designed to be called as external processes from the PDTool4 test execution system.

### Usage Pattern

```python
# From PDTool4 oneCSV_atlas_2.py
subprocess.check_output([
    'python', './src/lowsheen_lib/API_Analog.py',
    '1',  # Mode: output
    '1',  # Channel: 1
    '1',  # Function: Sine
    '10k', # Frequency: 10kHz
    '2',  # Amplitude: 2V
    '0'   # Offset: 0V
])
```

### Device Location Mapping

The instrument location is passed via test parameters:
```python
TestParams['Instrument'] = 'AD2_Channel1'  # Example
```

### Cleanup Pattern

After test completion, instruments are cleaned up with `--final` flag:
```python
for instrument_location, instrument_py in used_instruments.items():
    subprocess.check_output([
        'python',
        f'./src/lowsheen_lib/{instrument_py}',
        '--final',
        str(TestParams)
    ])
```

---

## Known Limitations

1. **Hardcoded Paths**: Log path `C:/Log/` is hardcoded for Windows
2. **No Return Values**: Functions don't return status codes; errors print and exit
3. **Global State**: Heavy reliance on global variables makes modules non-reentrant
4. **Limited Error Handling**: Most C API calls don't check return values
5. **Channel Indexing**: Channel numbers are 1-indexed in CLI but 0-indexed internally
6. **MSB-First DIO**: Digital channels use inverted bit ordering (channel 0 = bit 15)

---

## Maintenance Recommendations

1. **Add Return Codes**: Return success/failure status instead of exiting
2. **Configuration File**: Move hardcoded paths to configuration
3. **Error Handling**: Add try-catch blocks around C API calls
4. **Class-Based Refactor**: Consider class-based design for better state management
5. **Documentation**: Add docstrings to all functions
6. **Unit Tests**: Add tests for StrToNum, SelectFunction, and bit manipulation

---

## References

- **Digilent WaveForms SDK:** https://digilent.com/reference/software/waveforms/waveforms-sdk/start
- **Analog Discovery 2 Reference:** https://digilent.com/reference/test-and-measurement/analog-discovery-2/start
- **Python ctypes Documentation:** https://docs.python.org/3/library/ctypes.html

---

*Document generated: 2026-02-04*
*Source files: API_Analog.py (249 lines), API_Digital.py (333 lines), API_Impedance.py (181 lines), dwfconstants.py (270 lines)*
