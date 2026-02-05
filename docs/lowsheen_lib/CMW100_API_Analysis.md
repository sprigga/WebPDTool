# CMW100 API Analysis

## Overview

The CMW100 directory contains Python API modules for controlling the Rohde & Schwarz CMW100 wireless communications tester. These modules provide interfaces for Bluetooth and WiFi measurements, as well as LTE testing and signal generation capabilities.

**Target Instrument:** Rohde & Schwarz CMW100 (Wireless Communications Tester)

**Dependency:** `RsInstrument` package from Rohde & Schwarz (hosted on pypi.org)

## Architecture

### Core Components

```
CMW100/
├── API_BT_Meas.py          # Bluetooth measurement API
├── API_WiFi_Meas.py        # WiFi measurement API
├── API_LTE.py              # LTE measurement API (standalone)
├── API_LTE_module.py       # LTE measurement API (module)
├── API_Generator_module.py # Signal generator API
├── Helper Command.txt      # Command reference
└── CMW100 BT Wi-Fi API SOP.pptx # Documentation
```

### Communication Protocol

- **Primary Interface:** TCPIP (default: `TCPIP::localhost::INSTR`)
- **Alternative Interface:** GPIB (format: `GPIB<index>::<address>::INSTR`)
- **Driver Library:** RsInstrument (Rohde & Schwarz Python VISA wrapper)

---

## API Modules

### 1. API_BT_Meas.py - Bluetooth Measurement

**Purpose:** Perform Bluetooth RF measurements for BR (Basic Rate), EDR (Enhanced Data Rate), and LE (Low Energy) standards.

#### Command Line Interface

```bash
# Display help
API_BT_Meas.exe /h

# Full command format
API_BT_Meas.exe <Interface> <Index> <Address> <State> <Connector> <Frequency> <ENPower> <Repetition> <BurstType> <Asynchronous> [PacketType] [PatternType]
```

#### Parameters

| Index | Parameter | Description | Values/Range |
|-------|-----------|-------------|--------------|
| 1 | Interface | Communication interface | 1: GPIB, 2: TCPIP |
| 2 | Index | VISA interface index | 0 (default) |
| 3 | Address | Instrument address | 0: localhost, or IP/GPIB address |
| 4 | State | Measurement state | RST, 0: Off, 1: Run, 2: Stop |
| 5 | Connector | RF port connector | 1-8 (RA1-RA8) |
| 6 | Frequency | RF frequency | 100-6000 MHz |
| 7 | ENPower | Expected nominal power | 0-55 dBm |
| 8 | Repetition | Measurement mode | 0: Single, 1: Continuous |
| 9 | BurstType | Bluetooth type | 0: BR, 1: EDR, 2: LE |
| 10 | Asynchronous | Sync mode | 0: AUTO, or BD address |
| 11 | PacketType | BR packet type | 1: DH1, 2: DH3, 3: DH5 (BR only) |
| 12 | PatternType | Data pattern | 1: P44 (11110000), 2: P11 (10101010), 3: Other, 4: Alternating |

#### Key Functions

```python
# Configuration functions per burst type
BurstType_BR()   # Configure BR (Basic Rate) measurements
BurstType_EDR()  # Configure EDR measurements
BurstType_LE()   # Configure LE (Low Energy) measurements

# Result reading functions
Read_BR()   # Read BR measurement results
Read_EDR()  # Read EDR measurement results
Read_LE()   # Read LE measurement results
```

#### SCPI Commands Used

- `CONFigure:BLUetooth:MEAS:ISIGnal:BTYPe` - Set Bluetooth type
- `CONFigure:BLUetooth:MEAS:ISIGnal:ASYNchronize` - Set sync mode
- `INITiate:BLUetooth:MEAS:MEValuation` - Initiate measurement
- `FETCh:BLUetooth:MEAS:MEValuation:PVTime` - Fetch power vs time results

---

### 2. API_WiFi_Meas.py - WiFi Measurement

**Purpose:** Perform WiFi RF measurements for various 802.11 standards.

#### Command Line Interface

```bash
# Display help
API_WiFi_Meas.exe /h

# Full command format
API_WiFi_Meas.exe <Interface> <Index> <Address> <State> <Connector> <Frequency> <ENPower> <Repetition> <Standard> <Band> <BWidth> [TimeOut]
```

#### Parameters

| Index | Parameter | Description | Values/Range |
|-------|-----------|-------------|--------------|
| 1 | Interface | Communication interface | TCP, or GPIB index |
| 2 | Index | VISA interface index | GPIB board number |
| 3 | Address | Instrument address | 0: localhost, or IP address |
| 4 | State | Measurement state | RST, 0: Off, 1: Run, 2: Stop, 3: Read |
| 5 | Connector | RF port connector | 1-8 (RA1-RA8) |
| 6 | Frequency | RF frequency | In MHz |
| 7 | ENPower | Expected nominal power | -47 to 34 dBm |
| 8 | Repetition | Measurement mode | 0: Single, 1: Continuous |
| 9 | Standard | 802.11 standard | 1: b/g, 2: a/g, 3: n, 4: p, 5: ac, 6: ax |
| 10 | Band | Frequency band | 1: 2.4 GHz, 2: 5 GHz, 3: 4 GHz |
| 11 | BWidth | Channel bandwidth | 1: 5MHz, 2: 10MHz, 3: 20MHz, 4: 40MHz, 5: 80MHz, 6: 80+80MHz, 7: 160MHz |
| 12 | TimeOut | Trigger timeout | In seconds (optional) |

#### Key Functions

```python
WiFi_Config()  # Configure WiFi measurement parameters
WiFi_Read()    # Read measurement results
```

#### Measurement Results (State = 3/Read)

When reading results, the following values are returned:

| Metric | Description |
|--------|-------------|
| Burst Power | Average burst power |
| Peak Power | Peak power during burst |
| Crest Factor | Peak-to-average ratio |
| EVM All Carriers | Error Vector Magnitude (all) |
| EVM Data Carriers | Error Vector Magnitude (data) |
| EVM Pilot Carriers | Error Vector Magnitude (pilot) |
| Center Frequency Error | Frequency offset |
| Symbol Clock Error | Timing error |
| IQ Offset | DC offset in IQ constellation |
| DC Power | DC power component |
| Gain Imbalance | I/Q gain mismatch |
| Quadrature Error | I/Q phase error |

#### SCPI Commands Used

- `CONFigure:WLAN:MEAS:ISIGnal:STANdard` - Set 802.11 standard
- `CONFigure:WLAN:MEAS:RFSettings:FREQuency:BAND` - Set frequency band
- `CONFigure:WLAN:MEAS:ISIGnal:BWIDth` - Set channel bandwidth
- `FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage` - Fetch modulation results

---

### 3. API_LTE_module.py - LTE Measurement Module

**Purpose:** Configure and control LTE measurements using a modular class-based approach.

#### Command Line Interface

```bash
# Parameter format: key=value
API_LTE_module.py *RST Duplex=<mode> RXConnector=<conn> Freq=<freq> ...
```

#### Parameters

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| *RST | Reset instrument flag | *RST (present) or omitted |
| Status | Measurement state | ON, STOP, ABORT |
| Duplex | Duplex mode | TDD, FDD |
| RXConnector | RF connector | R11, R15, etc. |
| Freq | Frequency | With unit (e.g., 1850E+6) |
| ENPower | Expected nominal power | dBm value |
| Bandwidth | Channel bandwidth | B100, B20, etc. |
| Trigger | Trigger source | 'Free Run (No Sync)', 'Power' |
| FreqOFF | Frequency offset | Hz value |
| Umargin | User margin | dB value |
| MLOffset | Mixer level offset | dB value |

#### Configuration Class

```python
class Conf:
    fn_DMODe(DMODe)        # Set duplex mode
    fn_RXConnector(conn)   # Set RF connector
    fn_Freq(freq)          # Set frequency
    fn_ENPower(power)      # Set expected power
    fn_CBANdwidth(bw)      # Set channel bandwidth
    fn_TRIGger(trigger)    # Set trigger source
    fn_FreqOFF(offset)     # Set frequency offset
    fn_UMARgin(margin)     # Set user margin
    fn_MLOFfset(offset)    # Set mixer level offset
    fn_Status(status)      # Control measurement (ON/STOP/ABORT)
```

#### SCPI Commands Used

- `CONFigure:LTE:MEAS:DMODe` - Set duplex mode (TDD/FDD)
- `CONFigure:LTE:MEAS:PCC:CBANdwidth` - Set carrier bandwidth
- `INITiate:LTE:MEAS:MEValuation` - Initiate LTE measurement
- `FETCh:LTE:MEAS:MEValuation:SEMask` - Fetch spectrum emission results

---

### 4. API_Generator_module.py - Signal Generator Module

**Purpose:** Configure the CMW100 as a signal generator (VSG - Vector Signal Generator) for producing various waveforms.

#### Command Line Interface

```bash
# Parameter format: key=value
API_Generator_module.py *RST Spath=<path> Port=<port> Freq=<freq> Level=<level> ...
```

#### Parameters

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| *RST | Reset instrument flag | *RST or omitted |
| Spath | Signal path | R11, R15, etc. |
| Port | Port configuration | Binary string (e.g., 10000000) |
| Freq | Output frequency | Hz value |
| Level | Output level | dBm value |
| File | ARB waveform file | Filename in quotes |
| Repetition | Repetition mode | Single, Continuous |
| Cycle | Number of cycles | Integer value |
| State | Generator state | ON, OFF |
| CreTable | Create correction table | Table definition string |
| Deactivate | Deactivate corrections | True |
| Tableport | Table port mapping | Port mapping string |

#### Configuration Class

```python
class Conf:
    fn_Spath(path)          # Set signal path
    fn_Port(port)           # Configure port usage
    fn_Freq(freq)           # Set frequency
    fn_Level(level)         # Set output level
    fn_File(file)           # Select ARB waveform file
    fn_REPetition(rep)      # Set repetition mode
    fn_Cycle(count)         # Set cycle count
    fn_State(state)         # Control generator (ON/OFF)
    fn_Table(definition)    # Create frequency correction table
    fn_Deactivate()         # Deactivate all corrections
    fn_Mapping_Port(mapping) # Map correction table to port
```

#### Special Features

**Port Configuration:** The Port parameter uses an 8-character binary string where each character represents a port:
- `1` = ON
- `0` = OFF
- Example: `10000000` = Port 1 ON, others OFF

**Frequency Correction Tables:** Can create and activate frequency-dependent correction tables for each port to compensate for system losses.

#### SCPI Commands Used

- `SOURce:GPRF:GEN:RFSettings:FREQuency` - Set output frequency
- `SOURce:GPRF:GEN:RFSettings:LEVel` - Set output level
- `SOURce:GPRF:GEN:ARB:FILE` - Select ARB waveform file
- `CONFigure:BASE:FDCorrection:CTABle:CREate` - Create frequency correction table

---

### 5. API_LTE.py - LTE Measurement (Standalone)

**Purpose:** Standalone LTE measurement script with hardcoded parameters (similar to API_LTE_module but with fixed values).

**Note:** This is a simplified version of the LTE measurement with parameters defined in the `parameter()` function. Designed for quick testing and demonstration.

#### Key Features

- Uses default TDD mode at 1850 MHz
- Fetches TX power statistics (Current, Average, Min, Max, StdDev)
- Simple 2-second measurement cycle

---

## Common Patterns

### 1. Connection Management

All modules follow the same connection pattern:

```python
from RsInstrument import *

def connect():
    global specan
    specan = None
    try:
        specan = RsInstrument(resource_string, True, False)
        specan.visa_timeout = 500   # VISA read timeout
        specan.opc_timeout = 500    # OPC-sync timeout
        specan.instrument_status_checking = True  # Auto error check
    except Exception as ex:
        print('Error initializing instrument session:\n' + ex.args[0])
        exit()
```

### 2. Parameter Parsing

Two styles of parameter parsing are used:

**Positional Arguments (BT_Meas, WiFi_Meas):**
```python
if len(sys.argv) > 1:
    Interface = sys.argv[1]
    Index = sys.argv[2]
    Address = sys.argv[3]
    State = sys.argv[4]
    # ... etc
```

**Key-Value Arguments (LTE_module, Generator_module):**
```python
for i in range(len(sys.argv)):
    if sys.argv[i].find('Freq=') != -1:
        Freq = sys.argv[i][sys.argv[i].find('Freq=')+len('Freq='):]
    # ... etc
```

### 3. SCPI Command Structure

Commands follow hierarchical SCPI syntax:

```
<Root>:<System>:<Subsystem>:<Function> <Parameter>
```

Examples:
- `CONFigure:LTE:MEAS:DMODe TDD`
- `INITiate:BLUetooth:MEAS:MEValuation`
- `FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage?`

---

## Usage Examples

### Bluetooth BR Measurement

```bash
# Single BR measurement at 2450 MHz
API_BT_Meas.exe 2 0 0 1 1 2450 10 0 0 0 1 1
```

### WiFi 802.11ac Measurement

```bash
# Single 802.11ac measurement at 5.5 GHz, 80MHz bandwidth
API_WiFi_Meas.exe TCP 0 0 1 1 5500 28 0 5 2 5
```

### LTE Measurement with Parameters

```bash
# LTE TDD measurement
API_LTE_module.py Duplex=TDD RXConnector=R11 Freq=1850E+6 ENPower=7 Status=ON
```

### Signal Generator Configuration

```bash
# Configure generator at 2.4 GHz
API_Generator_module.py Spath=R11 Freq=2.4E+9 Level=-10 State=ON
```

---

## Error Handling

Common error conditions:

1. **Connection Timeout:** `visa_timeout` and `opc_timeout` settings may need adjustment for slow measurements
2. **Invalid Parameters:** Range validation is performed by the instrument
3. **Measurement Failures:** Check instrument status via `*ESR?` and `*OPC?` queries

---

## Dependencies

```bash
pip install RsInstrument
```

The RsInstrument package requires:
- Python 3.6+
- VISA runtime (NI-VISA or Rohde & Schwarz VISA)

---

## References

- **RsInstrument Documentation:** https://pypi.org/project/RsInstrument/
- **CMW100 User Manual:** Available from Rohde & Schwarz support
- **SCPI Standard:** IEEE 488.2

---

## Notes

1. All `.exe` files mentioned are compiled versions of corresponding `.py` files using PyInstaller
2. Default connection is `TCPIP::localhost::INSTR` for development
3. The `Helper Command.txt` file contains quick reference for command-line parameters
4. The PowerPoint file (`CMW100 BT Wi-Fi API SOP.pptx`) likely contains detailed operational procedures

---

*Document generated from code analysis - 2025*
