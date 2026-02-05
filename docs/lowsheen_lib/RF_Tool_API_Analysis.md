# RF_Tool API Analysis

## Overview

The RF_Tool directory contains a comprehensive RF (Radio Frequency) testing system for cellular communication standards (GSM, WCDMA, LTE, NR). This system integrates **Anritsu MT8872A** universal wireless test equipment with **Qualcomm QMSL** (Qualcomm Manufacturing Services Library) for automated RF measurements on manufactured devices.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PDTool4 Test System                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
┌───────────▼───────────┐       ┌───────────▼──────────────┐
│   MT8872A Control     │       │   QMSL DUT Control       │
│   (PyVISA/SCPI)       │       │   (Windows DLL)          │
│                       │       │                          │
│ • Generator           │       │ • GSM/WCDMA TX/RX        │
│ • Measurement         │       │ • LTE TX/RX              │
│ • Information         │       │ • NR TX/RX               │
└───────────┬───────────┘       │ • WiFi TX/GPS            │
            │                   └───────────┬──────────────┘
            │                               │
    ┌───────▼────────┐              ┌──────▼──────────┐
    │  MT8872A Unit  │◄─────RF──────►  Device Under   │
    │  (192.168.1.1) │   (Coaxial)   │  Test (DUT)     │
    └────────────────┘               └─────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Instrument Control** | PyVISA | SCPI command interface to MT8872A |
| **DUT Control** | QMSL DLLs | Qualcomm device control via FTM mode |
| **Communication** | TCP/IP (VISA) | Ethernet connection to test equipment |
| **Logging** | Text files | Timestamped command/response logs |
| **Configuration** | INI files | Test parameters per cellular standard |

---

## Module Reference

### 1. MT8872A_Generator.py

**Purpose:** Controls the MT8872A signal generator to output cellular signals for receiver testing.

#### Command-Line Interface

```bash
python MT8872A_Generator.py <IP> <InPort> <OutPort> <Freq> <Level> <BBMode> <Mode> <State> <Type>
```

#### Parameters

| Position | Parameter | Description | Example Values |
|----------|-----------|-------------|----------------|
| 1 | IP Address | MT8872A IP address | `192.168.1.1` |
| 2 | Input Port | Input port number | `1` or `2` |
| 3 | Output Port | Output port number | `1` or `2` |
| 4 | Frequency | Center frequency in MHz | `2140.0` |
| 5 | Level | Output power in dBm | `-18` |
| 6 | BBMode | Baseband mode | `1` (CW) or `2` (ARB) |
| 7 | Mode | Generation mode | `1` (NORMAL) or `2` (SEQUENCE) |
| 8 | State | Generator state | `1` (ON) or `0` (OFF) |
| 9 | Type | ARB waveform type | `0` (GSM), `1` (WCDMA), `2` (LTE), `3` (NR) |

#### Example Usage

```bash
# LTE signal at 2140 MHz, -18 dBm, ARB mode
python MT8872A_Generator.py 192.168.1.1 2 2 2140.0 -18 2 1 1 2

# CW signal (simple carrier wave)
python MT8872A_Generator.py 192.168.1.1 1 1 1950.0 -10 1 1 1 0
```

#### SCPI Command Sequence

1. **Initialization**
   ```scpi
   *RST                                    # Reset instrument
   SYST:LANG SCPI                          # Set SCPI language mode
   ```

2. **Configuration**
   ```scpi
   ROUte:PORT:CONNect:DIRection PORT2,PORT2
   :SOURce:GPRF:GENerator:RFSettings:FREQuency 2140.0MHZ
   :SOURce:GPRF:GENerator:RFSettings:LEVel -18
   :SOURce:GPRF:GENerator:BBMode ARB
   :SOURce:GPRF:GENerator:MODE NORMAL
   ```

3. **Waveform Loading** (ARB mode only)
   ```scpi
   :SOURce:GPRF:GENerator:ARB:FILE:LOAD "MV887013A_14A_LTEFDD_TDD_0001"
   :SOURce:GPRF:GENerator:ARB:FILE:LOAD:STATus?  # Poll until complete
   :SOURce:GPRF:GENerator:ARB:WAVeform:PATTern:SELect "MV887013A_14A_LTEFDD_TDD_0001"
   ```

4. **Activation**
   ```scpi
   :SOURce:GPRF:GENerator:STATe ON
   ```

#### Supported Waveforms

| Standard | Waveform File(s) |
|----------|------------------|
| GSM | `MV887012A_GSM_0002` |
| WCDMA | `MV887011A_WCDMA_0002` |
| LTE | `MV887013A_14A_LTEFDD_TDD_0001` |
| NR (5G) | `MV887018A_NRFDD_0001`, `MV887019A_NRTDD_0001` |

#### Output

- **Stdout:** Parameter confirmation and waveform loading status
- **Log File:** `TXT_output_Log.txt` (timestamped SCPI commands and responses)

---

### 2. MT8872A_INF.py

**Purpose:** Query MT8872A instrument information (model, serial number, firmware version, etc.).

#### Command-Line Interface

```bash
python MT8872A_INF.py <Instrument> <Mode> <JSON_Params>
```

#### Query Modes

| Mode | Item | SCPI Query Command |
|------|------|-------------------|
| `1` | IDN | `*IDN?` |
| `2` | Serial Number | `SYSTem:INFormation:DEVice:ID?` |
| `3` | Firmware Version | `SYSTem:INFormation:MAINframe:PACKage:VERSion?` |
| `4` | Model | `SYSTem:INFormation:MAINframe?` |
| `5` | Software Model | `SYSTem:INFormation:MAINframe:SOFTware?` |
| `6` | Waveform License | `SYSTem:INFormation:MAINframe:WAVeform?` |
| `7` | MU887002A SN | `SYSTem:INFormation:MAINframe:DEVice:ID?` |
| `8` | MU887002A Model | `SYSTem:INFormation?` |
| `9` | MU887002A MAC Address | `SYSTem:COMMunicate:NET:HWADdress?` |

#### Example Usage

```bash
# Get instrument serial number
python MT8872A_INF.py 192.168.1.1 2 "{'Item': 'SN', 'Instrument': '192.168.1.1', 'Timeout': '10'}"

# Get firmware version
python MT8872A_INF.py 192.168.1.1 3 "{'Item': 'FWVer', 'Instrument': '192.168.1.1', 'Timeout': '10'}"
```

#### JSON Parameter Structure

```json
{
  "Item": "SN",              // Query item (SN, FWVer, Model, etc.)
  "Instrument": "192.168.1.1",  // Instrument IP address
  "Timeout": "10"            // Query timeout in seconds
}
```

#### Output

- **Stdout:** Query result (e.g., serial number string)
- **Log File:** `C:/Log/MT8872A/<Date>/RF_LOG_Inf_<Time>.txt`

---

### 3. MT8872A_Measurement.py

**Purpose:** Perform comprehensive RF measurements (Power, ACLR, OBW, SEM) on DUT transmissions.

#### Command-Line Interface

```bash
python MT8872A_Measurement.py <IP> <Mode> <InPort> <OutPort> <Band> <ULChannel> <Bandwidth>
```

#### Parameters

| Position | Parameter | Description | Example |
|----------|-----------|-------------|---------|
| 1 | IP Address | MT8872A IP | `192.168.1.1` |
| 2 | Mode | Cellular standard | `0` (GSM), `1` (WCDMA), `2` (LTE), `3` (NR) |
| 3 | Input Port | Input port | `1` or `2` |
| 4 | Output Port | Output port | `1` or `2` |
| 5 | Band | Frequency band | `1`, `3`, `7`, etc. |
| 6 | UL Channel | Uplink channel number | `18300` |
| 7 | Bandwidth | Channel bandwidth (MHz) | `5`, `10`, `20` |

#### Measurement Types

##### GSM Measurements
- **TxPower:** Average transmit power
- **OFFPower:** Power during off period
- **RATio:** Power ratio
- **PFMaximum/PFMinimum:** Peak/minimum power in frequency
- **EPOWer:** Error power

##### WCDMA Measurements
- **TxPower:** Total transmit power
- **FLTPower:** Filtered power
- **ACLR:** Adjacent Channel Leakage Ratio
- **OBW:** Occupied Bandwidth
- **SEM:** Spectrum Emission Mask

##### LTE Measurements
- **TxPower (AVG/MAX/MIN/TTL/DVT/IND):** Multi-mode power measurements
- **ACLR (AVG/MAX/MIN/TTL/DVT):** Leakage measurements
- **SEM (JUDG/LOW/UPP/LDET/UDET):** Spectrum mask compliance
- **OBW:** Occupied bandwidth with upper/lower/center frequencies

##### NR (5G) Measurements
- **TxPower:** Transmit power
- **CHPower:** Channel power

#### Example Usage

```bash
# LTE Band 1, Channel 18300, 20 MHz bandwidth
python MT8872A_Measurement.py 192.168.1.1 2 2 2 1 18300 20

# WCDMA Band 1, Channel 9700, 5 MHz bandwidth
python MT8872A_Measurement.py 192.168.1.1 1 1 1 1 9700 5
```

#### Output

- **Stdout:** Measurement results (e.g., `Txpower_AVG=-10.5`)
- **Log File:** `C:/Log/MT8872A/<Date>/RF_LOG_Gen_<Time>_<Mode>_<Channel>.txt`

#### Measurement Flow

```
1. Initialize Instrument
   ├─> *RST
   ├─> SYST:LANG SCPI
   └─> Set port direction

2. Configure Standard-Specific Settings
   ├─> Set band, channel, bandwidth
   ├─> Enable measurement types (POW, ACLR, OBW, SEM)
   └─> Configure trigger settings

3. Start Measurement
   └─> :INITiate:CELLular:MEASurement:SINGle

4. Poll Measurement Status
   ├─> :FETCh:CELLular:MEASurement:STATe?
   ├─> Wait for completion (status = 0)
   └─> Handle errors (status = 5 or 12)

5. Fetch Results
   ├─> Power measurements
   ├─> ACLR measurements
   ├─> SEM measurements
   └─> OBW measurements
```

---

## QMSL Integration

### QMSL Executables

The directory contains Windows executables that wrap QMSL DLL functionality:

| Executable | Purpose | Cellular Standard |
|------------|---------|-------------------|
| `QMSL_GSM_TX.exe` | GSM transmitter test | GSM/GPRS/EDGE |
| `QMSL_GSM_RX.exe` | GSM receiver test | GSM/GPRS/EDGE |
| `QMSL_WCDMA_TX.exe` | WCDMA transmitter test | UMTS/HSPA |
| `QMSL_WCDMA_RX.exe` | WCDMA receiver test | UMTS/HSPA |
| `QMSL_LTE_TX.exe` | LTE transmitter test | LTE FDD/TDD |
| `QMSL_LTE_RX.exe` | LTE receiver test | LTE FDD/TDD |
| `QMSL_NR_TX.exe` | 5G NR transmitter test | 5G NR FR1/FR2 |
| `QMSL_NR_RX.exe` | 5G NR receiver test | 5G NR FR1/FR2 |
| `QMSL_WIFI_TxOn.exe` | WiFi transmit enable | WiFi 802.11a/b/g/n/ac |
| `QMSL_GPS.exe` | GPS functionality test | GPS/GNSS |

### FTM Mode

QMSL operates devices in **FTM (Factory Test Mode)**, a special Qualcomm diagnostic mode that bypasses the Android/modem OS for direct hardware control.

**FTM_On Directory:** Contains tools to boot devices into FTM mode via adb/fastboot.

### DLL Dependencies

- `QMSL_MSVC10R.dll` - Main QMSL library (Microsoft Visual C++ 2010 Runtime)
- `QMSLFastConnect_MSVC10R.dll` - Fast connection library for QMSL

---

## Configuration Files

### GSM_Config.ini

```ini
[Setting]
Txpower=300          # Transmit power in 0.1 dBm units (30.0 dBm)
StartRb=0            # Starting resource block
NumberRb=50          # Number of resource blocks
BandWidth=20         # Bandwidth in MHz
LogPath=C:\\QMSL_Log # Log file directory
```

### LTE_Config.ini

```ini
[Setting]
Txpower=100          # Transmit power (10.0 dBm)
StartRb=0
NumberRb=20
BandWidth=20
LogPath=C:\\QMSL_Log
```

### WCDMA_Config.ini

```ini
[Setting]
Txpower=300          # Transmit power (30.0 dBm)
StartRb=0
NumberRb=50
BandWidth=10
```

### NR_Config.ini

```ini
[Setting]
Txpower=100          # Transmit power (10.0 dBm)
StartRb=0
NumberRb=10
BandWidth=5
LogPath=C:\\QMSL_Log
```

---

## Integration with PDTool4

### Usage Pattern

The RF_Tool modules are called from PDTool4 test plans as **CommandTest** measurement types:

```csv
ItemKey,ExecuteName,Command,Instrument
FT00-077,CommandTest,MT8872A_INF.py 192.168.1.1 2,MT8872A
FT00-078,CommandTest,MT8872A_Measurement.py 192.168.1.1 2 2 2 1 18300 20,MT8872A
```

### Subprocess Execution

PDTool4 executes RF tools via subprocess:

```python
import subprocess

# Example: Query instrument serial number
result = subprocess.run([
    'python',
    'src/lowsheen_lib/RF_tool/MT8872A_INF.py',
    '192.168.1.1',
    '2',
    "{'Item': 'SN', 'Instrument': '192.168.1.1', 'Timeout': '10'}"
], capture_output=True, text=True)

serial_number = result.stdout.strip()
```

---

## Logging System

### Log File Locations

- **MT8872A Logs:** `C:/Log/MT8872A/<YYYYMMDD>/RF_LOG_<Type>_<Timestamp>.txt`
- **QMSL Logs:** `C:/QMSL_Log/` (configured in .ini files)

### Log Format

```
---WRITE---
14:23:45:123456     :SOURce:GPRF:GENerator:RFSettings:FREQuency 2140.0MHZ
---READ---
14:23:45:234567     2140000000
---WRITE---
14:23:46:345678     :SOURce:GPRF:GENerator:STATe ON
```

**Format:** Timestamp (HH:MM:SS:microseconds) + Command/Response

---

## Error Handling

### MT8872A Measurement Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| `0` | Measurement complete | Fetch results |
| `5` | Synchronization word not detected | DUT not transmitting |
| `12` | Tx measurement timeout | DUT signal too weak |

### Common Errors

#### 1. No Instrument Found
**Cause:** Network connection failure to MT8872A
**Solution:**
- Verify IP address (default: 192.168.1.1)
- Check Ethernet cable connection
- Ping instrument to verify connectivity

#### 2. Waveform Loading Timeout
**Cause:** Missing waveform files or license
**Solution:**
- Install required MV waveform packages
- Verify license with Mode `6` (WFlicense query)

#### 3. QMSL DLL Load Failure
**Cause:** Missing Visual C++ 2010 Runtime
**Solution:** Install `vcredist_x86.exe` (VC++ 2010 Redistributable)

---

## Best Practices

### 1. Instrument Initialization
Always reset and configure language mode:
```python
visa_inst.write('*RST')
visa_inst.write('SYST:LANG SCPI')
```

### 2. Waveform Loading
Poll status until complete:
```python
while True:
    status = visa_inst.query(':SOURce:GPRF:GENerator:ARB:FILE:LOAD:STATus?')
    if status.strip() == '0':
        break
    time.sleep(0.5)
```

### 3. Measurement Polling
Always check measurement state before fetching:
```python
while True:
    state = visa_inst.query(':FETCh:CELLular:MEASurement:STATe?')
    if '0' in state:  # Complete
        break
    elif '5' in state or '12' in state:  # Error
        raise MeasurementError()
    time.sleep(1)
```

### 4. Resource Management
Close VISA resources properly:
```python
try:
    # Measurements
finally:
    visa_inst.close()
    rm.close()
```

---

## Technical Notes

### PyVISA Configuration

- **VISA Library:** `c:/windows/system32/visa32.dll` (NI-VISA or Keysight IO Libraries)
- **Resource String Format:** `TCPIP0::<IP>::inst0::INSTR`
- **Timeout:** Handled by individual query commands

### Network Configuration

**MT8872A Default Settings:**
- IP Address: `192.168.1.1`
- Subnet Mask: `255.255.255.0`
- Port: Standard VISA TCP/IP (not explicitly configured)

**Recommended PC Network:**
- Static IP: `192.168.1.100`
- Subnet Mask: `255.255.255.0`
- Gateway: None (direct connection)

### Measurement Accuracy

- **Power Measurements:** ±0.5 dB typical
- **ACLR Measurements:** ±1.0 dB typical
- **Frequency Accuracy:** ±10 Hz (after warm-up)

### Performance Considerations

- **Generator Waveform Loading:** 5-15 seconds per waveform
- **Measurement Duration:**
  - GSM: 2-5 seconds
  - WCDMA: 3-8 seconds
  - LTE: 5-10 seconds
  - NR: 5-15 seconds

---

## Maintenance

### Calibration

MT8872A requires annual calibration. Check calibration status:
```scpi
:CALibration:DATE?
```

### Firmware Updates

1. Download firmware from Anritsu support portal
2. Use MT8872A web interface (http://192.168.1.1)
3. Navigate to System → Software Update
4. Upload `.pkg` file and reboot

### Waveform Updates

Install new waveform packages via USB:
1. Copy `.wv` files to USB drive
2. Insert into MT8872A front USB port
3. System → File Manager → Import Waveforms

---

## Troubleshooting

### Issue: "Error: An error occurred while Visa writing"

**Possible Causes:**
1. Instrument not powered on
2. Network cable disconnected
3. Incorrect IP address
4. VISA driver not installed

**Diagnosis:**
```bash
# Ping test
ping 192.168.1.1

# Check VISA installation
python -c "import pyvisa; print(pyvisa.ResourceManager().list_resources())"
```

### Issue: Measurement always times out

**Possible Causes:**
1. DUT not in FTM mode
2. Incorrect frequency/band configuration
3. RF cable disconnected
4. DUT transmit power too low

**Diagnosis:**
- Manually trigger measurement on MT8872A front panel
- Use spectrum analyzer view to verify signal presence
- Check FTM mode with adb: `adb shell getprop ro.bootmode`

### Issue: QMSL executable fails to run

**Possible Causes:**
1. Missing DLL dependencies
2. No Qualcomm device connected
3. USB driver not installed

**Diagnosis:**
```bash
# Check dependencies
dumpbin /dependents QMSL_LTE_TX.exe

# Verify device connection
adb devices

# Check FTM diagnostic port
# Should show Qualcomm HS-USB Diagnostics port
```

---

## References

### Official Documentation

- **Anritsu MT8872A User Manual:** Operation and programming guide
- **QMSL Programmer's Guide:** API reference for QMSL library
- **3GPP Specifications:**
  - GSM: TS 51.010
  - WCDMA: TS 34.121
  - LTE: TS 36.521
  - NR: TS 38.521

### Related Files

- `src/lowsheen_lib/remote_instrument.py` - Instrument configuration reader
- `testPlan/*/` - Example test plans using RF measurements

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-04 | Initial documentation based on codebase analysis |

---

**Document Status:** Production Ready
**Maintained By:** PDTool4 Development Team
**Last Updated:** 2026-02-04
