# LowSheen Library API Documentation

This directory contains comprehensive API analysis documentation for instrument drivers and APIs used in the PDTool4 testing framework.

## Available Documentation

### [Agilent N5182A API Analysis](Agilent_N5182A_API_Analysis.md)
**Instrument:** Agilent N5182A MXG X-Series Signal Generator
**File Location:** `src/lowsheen_lib/Agelient_N5182A_API/Agilent_N5182A_API.py`

**Features:**
- GPIB-based instrument control via PyVISA
- CW (Continuous Wave) and ARB (Arbitrary Waveform) modes
- Frequency, amplitude, and output state control
- SCPI command interface

**Key Functions:**
- `Parameter()` - Parse command-line arguments
- `Connect()` - Open VISA session
- `Run()` - Configure instrument
- `Reset()` - Reset to defaults
- `translate_fre()` - Convert frequency format

---

### [Analog Discovery 2 API Analysis](AnalogDiscovery2_API_Analysis.md)
**Instrument:** Digilent Analog Discovery 2 (AD2) USB Oscilloscope/Function Generator
**File Location:** `src/lowsheen_lib/AnalogDiscovery2Api/`

**Features:**
- Analog waveform generation and acquisition
- Digital I/O (16 DIO lines)
- Impedance measurement with 4-wire method
- Cross-platform support (Windows/Linux/macOS)
- FFT analysis for signal processing

**Modules:**
- `API_Analog.py` - Analog I/O functions (oscilloscope, function generator)
- `API_Digital.py` - Digital I/O operations
- `API_Impedance.py` - Impedance measurement
- `dwfconstants.py` - WaveForms SDK constants

**Key Functions (Analog):**
- `connet()` - Connect to AD2 device
- `AnalogIn()` - Acquire analog samples with FFT
- `AnalogOut()` - Generate waveforms (DC, Sine, Square, Triangle, etc.)
- `StrToNum()` - Convert unit suffix strings to numbers

**Key Functions (Digital):**
- `open()` - Open device
- `set_mode()` - Configure DIO direction
- `get_state()` - Read DIO pin state
- `set_state()` - Set DIO pin output
- `closeDigital()` - Reset digital interface

**Key Functions (Impedance):**
- 20 measurement types including impedance, phase, capacitance, inductance
- Exponential frequency sweep
- Automatic unit scaling

---

### [CMW100 API Analysis](CMW100_API_Analysis.md)
**Instrument:** Rohde & Schwarz CMW100 Wireless Communications Tester
**File Location:** `src/lowsheen_lib/CMW100/`

**Features:**
- Bluetooth RF measurements (BR/EDR/LE)
- WiFi measurements (802.11 a/b/g/n/p/ac/ax)
- LTE measurements (TDD/FDD)
- Signal generation (VSG) with ARB waveform support
- Frequency correction tables for system calibration

**Modules:**
- `API_BT_Meas.py` - Bluetooth measurement API
- `API_WiFi_Meas.py` - WiFi measurement API
- `API_LTE_module.py` - LTE measurement API (modular)
- `API_LTE.py` - LTE measurement API (standalone)
- `API_Generator_module.py` - Signal generator API

**Key Functions (Bluetooth):**
- `BurstType_BR()` - Configure BR (Basic Rate) measurements
- `BurstType_EDR()` - Configure EDR measurements
- `BurstType_LE()` - Configure LE (Low Energy) measurements
- `Read_BR()`, `Read_EDR()`, `Read_LE()` - Fetch measurement results

**Key Functions (WiFi):**
- `WiFi_Config()` - Configure WiFi measurement parameters
- `WiFi_Read()` - Read EVM, power, and modulation results

**Key Functions (LTE):**
- `Conf.fn_DMODe()` - Set duplex mode (TDD/FDD)
- `Conf.fn_Freq()` - Set carrier frequency
- `Conf.fn_CBANdwidth()` - Set channel bandwidth
- `Conf.fn_Status()` - Control measurement state (ON/STOP/ABORT)

**Key Functions (Generator):**
- `Conf.fn_Freq()` - Set output frequency
- `Conf.fn_Level()` - Set output level
- `Conf.fn_File()` - Select ARB waveform file
- `Conf.fn_Table()` - Create frequency correction table

---

### [Proto Utils Documentation](proto_utils_README.md)
**Module:** VCU (Vehicle Control Unit) Communication Protocol
**File Location:** `src/lowsheen_lib/proto_utils/`

**Features:**
- UDP-based communication with STM32 microcontroller
- Protocol Buffers message serialization
- Custom packet format with CRC32 validation
- Thread-safe connection management
- Motor control command interface

**Modules:**
- `VCUComm.py` - Low-level UDP socket communication
- `proto_msgs.py` - Message framing and serialization
- `cliff_test.py` - High-level motor control interface

**Related Documents:**
- [Proto Utils API Reference](proto_utils_API_Reference.md) - Complete API documentation
- [Proto Utils Design Guide](proto_utils_Design_Guide.md) - Architecture and design patterns

**Key Functions (VCUComm):**
- `try_cpu_stm_connect()` - Establish UDP connection with retry
- `_send_comm_packet()` - Send packet with automatic retry
- `receive_msg()` - Receive message with timeout

**Key Functions (ProtoMsgs):**
- `_create_header()` - Create packet header with CRC
- `get_crc()` - Calculate CRC32 checksum
- `deserialize_message()` - Parse received protobuf message

**Key Functions (TestObject):**
- `create_test_req_msg()` - Create motor control command
- `send_test_msg()` - Send command and receive response

---

### [Keithley 2260B Power Supply API Analysis](2260B_API_Analysis.md)
**Instrument:** Keithley 2260B Series Programmable DC Power Supply
**File Location:** `src/lowsheen_lib/2260B.py`

**Features:**
- SCPI-based voltage and current control
- Closed-loop verification of set values
- Output enable/disable control
- Command-line interface for subprocess execution

**Key Functions:**
- `get_cmd_string()` - Generate SCPI commands for voltage/current
- `send_cmd_to_instrument()` - Execute commands with verification
- `initial()` - Safe output disable for cleanup

**Command Mapping:**
- Set Voltage: `VOLT {value}`
- Set Current: `CURR {value}`
- Query Voltage: `MEAS:VOLT:DC?`
- Query Current: `MEAS:CURR:DC?`
- Output Control: `OUTP ON/OFF`

---

### [Keithley 2303 Power Supply API Analysis](2303_API_Analysis.md)
**Instrument:** Keithley 2303 Power Supply
**File Location:** `src/lowsheen_lib/2303_test.py`

**Features:**
- Simplified SCPI command set (identical to 2260B)
- Voltage and current control with verification
- Single-channel operation
- Subprocess-based integration

**Key Functions:**
- `get_cmd_string()` - Generate SCPI commands
- `send_cmd_to_instrument()` - Execute with verification
- `initial()` - Cleanup mode (disable output)

**Command Mapping:**
- Set Voltage: `VOLT {value}`
- Set Current: `CURR {value}`
- Query Voltage: `MEAS:VOLT:DC?`
- Query Current: `MEAS:CURR:DC?`
- Output Control: `OUTP ON/OFF`

---

### [Keithley 2306 Dual-Channel Power Supply API Analysis](2306_API_Analysis.md)
**Instrument:** Keithley 2306 Dual-Channel Battery/Charger Simulator
**File Location:** `src/lowsheen_lib/2306_test.py`

**Features:**
- Dual independent channel control (Channel 1 & 2)
- Channel-specific SCPI commands
- Zero-value detection for output disable
- Verification disabled (commented out for performance)

**Key Functions:**
- `get_cmd_string()` - Generate channel-specific SCPI commands
- `send_cmd_to_instrument()` - Execute with channel selection
- `initial()` - Disable both channels for cleanup

**Channel 1 Commands:**
- Set Voltage: `SOUR:VOLT {value}`
- Set Current: `SOUR:CURR:LIM {value}`
- Query Voltage: `MEAS:VOLT?`
- Query Current: `MEAS:CURR?`
- Output Control: `OUTP ON/OFF`

**Channel 2 Commands:**
- Set Voltage: `SOUR2:VOLT {value}`
- Set Current: `SOUR2:CURR:LIM {value}`
- Query Voltage: `MEAS2:VOLT?`
- Query Current: `MEAS2:CURR?`
- Output Control: `OUTP2 ON/OFF`

---

## Common Patterns

### Command-Line Interface

All instrument APIs follow a similar command-line pattern:

```bash
python <API_Module.py> <mode> <parameters...>
```

Example usage:
```bash
# Agilent N5182A - Set CW mode
python Agilent_N5182A_API.py 0 16 2 100K -10 1

# Analog Discovery 2 - Generate sine wave
python API_Analog.py 1 1 1 10k 2 0

# Analog Discovery 2 - Read DIO pin
python API_Digital.py 0 1

# CMW100 - Bluetooth BR measurement
python API_BT_Meas.py 2 0 0 1 1 2450 10 0 0 0 1 1

# CMW100 - WiFi 802.11ac measurement
python API_WiFi_Meas.py TCP 0 0 1 1 5500 28 0 5 2 5

# Keithley 2260B - Set 12V @ 3A
python 2260B.py normal "{'Instrument': 'MODEL2260B_1', 'SetVolt': '12', 'SetCurr': '3'}"

# Keithley 2303 - Set 5V @ 3A
python 2303_test.py normal "{'Instrument': 'MODEL2303_1', 'SetVolt': '5', 'SetCurr': '3'}"

# Keithley 2306 - Enable Channel 1 at 3.3V @ 1.5A
python 2306_test.py normal "{'Instrument': 'MODEL2306_1', 'Channel': '1', 'SetVolt': '3.3', 'SetCurr': '1.5'}"

# Keithley 2306 - Disable Channel 1
python 2306_test.py test "{'Instrument': 'MODEL2306_1', 'Channel': '1', 'SetVolt': '0', 'SetCurr': '0'}"
```

### Integration with PDTool4

These APIs are called as subprocesses from the PDTool4 test execution system (`oneCSV_atlas_2.py`):

```python
subprocess.check_output([
    'python', './src/lowsheen_lib/<API_Module>.py',
    '<mode>', '<param1>', '<param2>', ...
])
```

### Version Check

All modules support a version query:

```bash
python <API_Module.py> Version
```

---

## Instrument Communication Protocols

| Instrument | Protocol | Library |
|------------|----------|---------|
| Agilent N5182A | GPIB (IEEE 488) | PyVISA |
| Analog Discovery 2 | USB (Custom) | Digilent WaveForms SDK (ctypes) |
| R&S CMW100 | TCPIP / GPIB | RsInstrument (Rohde & Schwarz) |
| STM32 VCU | UDP | Socket + Protocol Buffers |
| Keithley 2260B | GPIB / USB / Ethernet | PyVISA (via remote_instrument) |
| Keithley 2303 | GPIB / USB / Ethernet | PyVISA (via remote_instrument) |
| Keithley 2306 | GPIB / USB / Ethernet | PyVISA (via remote_instrument) |

---

## Device Location Mapping

In PDTool4, instrument locations are specified in test plan CSV and passed to measurement modules:

```python
TestParams['Instrument'] = 'AD2_Channel1'  # Analog Discovery 2
TestParams['Instrument'] = 'GPIB0::16::INSTR'  # Agilent N5182A
TestParams['Instrument'] = 'TCPIP::192.168.1.100::INSTR'  # R&S CMW100
```

---

## Adding New Instrument APIs

When adding documentation for a new instrument API:

1. Create a new markdown file: `<Instrument>_API_Analysis.md`
2. Follow the existing structure:
   - Overview with dependencies
   - Architecture and module structure
   - Command-line interface documentation
   - Function reference with signatures
   - Code examples
   - Integration patterns with PDTool4
3. Update this README with a link to the new documentation

---

## Dependencies

### Python Libraries
- `ctypes` - FFI for C libraries (Analog Discovery 2)
- `pyvisa` - VISA instrument communication (Agilent)
- `RsInstrument` - Rohde & Schwarz instrument control (CMW100)
- `numpy` - Array operations and FFT
- `matplotlib` - Optional plotting

### External SDKs
- **Digilent WaveForms SDK** - Required for Analog Discovery 2
  - Windows: Included with WaveForms installation
  - Linux: `libdwf.so` in `/usr/lib/`
  - Download: https://digilent.com/reference/software/waveforms/waveforms-sdk/start

- **VISA Runtime** - Required for GPIB/USB instrument communication
  - NI-VISA: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
  - Keysight VISA: https://www.keysight.com/us/en/lib/software-detail/computer-software/keysight-io-libraries-suite/2175306.html

- **RsInstrument Package** - Required for R&S CMW100
  - PyPI: https://pypi.org/project/RsInstrument/
  - Documentation: Included with package installation
  - Compatible with R&S VISA or NI-VISA

---

## Troubleshooting

### Analog Discovery 2 Not Detected

**Symptoms:** `failed to open device` message

**Solutions:**
1. Check WaveForms software is installed
2. Verify device is connected via USB
3. On Linux, add udev rules:
   ```bash
   # /etc/udev/rules.d/60-digilent.rules
   ATTR{idVendor}=="0403", ATTR{idProduct}=="6010", MODE="0666"
   ATTR{idVendor}=="0403", ATTR{idProduct=="6014", MODE="0666"
   ```
4. Reload udev: `sudo udevadm control --reload-rules && sudo udevadm trigger`

### Agilent N5182A Connection Timeout

**Symptoms:** `Could not open ViSession!`

**Solutions:**
1. Verify GPIB address is correct
2. Check NI-VISA or Keysight VISA is installed
3. Test with VISA Interactive Control (NI MAX)
4. Check GPIB cable connections

### CMW100 Connection Issues

**Symptoms:** `Error initializing the instrument session`

**Solutions:**
1. Verify TCPIP address is reachable (ping test)
2. Check RsInstrument package is installed: `pip show RsInstrument`
3. Verify instrument is powered on and network configured
4. Test with default connection: `TCPIP::localhost::INSTR`

---

## Maintenance Notes

- Documentation generated: 2026-02-04
- Compatible with PDTool4 v0.7.0+
- For code updates, regenerate documentation after significant changes

---

*PDTool4 LowSheen Library Documentation*
