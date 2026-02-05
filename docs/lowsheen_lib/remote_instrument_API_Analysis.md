# remote_instrument API Analysis

## Overview

remote_instrument.py is the core instrument connection manager for PDTool4's lowsheen_lib driver library. It provides a unified interface for connecting to test instruments using multiple communication protocols (TCPIP/Socket, Serial/VISA, Serial/pySerial, GPIB). This module abstracts away protocol-specific configuration details, allowing instrument drivers to focus on command logic.

**File Location:** `src/lowsheen_lib/remote_instrument.py`
**Dependencies:**
- `pyvisa` - VISA protocol support (TCPIP, Serial, GPIB)
- `pyserial` - Direct COM port access
- `configparser` - INI file parsing
- Standard: `sys`, `os`

## Architecture

```
remote_instrument.py
├── instrument()                    # Auto-discovery via *IDN? (legacy)
├── instrument_iniSetting()         # Main connection manager (config-based)
│   ├── parse_comport_address()    # Parse "COM3/baud:115200"
│   ├── parse_serial_address()     # Parse "ASRL2::INSTR/baud:115200/bits:1"
│   ├── setup_serial()             # Configure VISA serial parameters
│   └── setup_tcpip_socket()       # Configure TCPIP socket parameters
└── instrument_initial()           # Reset instrument (*RST) (unused)
```

**Design Pattern:** Factory pattern - Returns appropriate connection object based on address format.

---

## Core Functions

### 1. instrument_iniSetting(instrument_name)

**Primary connection manager** - Creates instrument connection using configuration from `test_xml.ini`.

#### Parameters
- `instrument_name` (str): Instrument identifier key in INI file (e.g., "PSW3072_1")

#### Returns
- **Success:** Instrument object (Serial or VISA Resource)
  - `serial.Serial` for COM ports
  - `pyvisa.Resource` for VISA connections
- **Failure:** `None` (prints error message)

#### Configuration Format (test_xml.ini)

```ini
[Setting]
# TCPIP Socket
PSW3072_1 = TCPIP0::192.168.1.100::5025::SOCKET

# Serial via VISA
Keithley2015_1 = ASRL2::INSTR/baud:115200/bits:1

# Serial via pySerial
2306_1 = COM3/baud:115200

# GPIB
34970A_1 = GPIB0::9::INSTR
```

#### Connection Type Detection

The function auto-detects connection type based on address string format:

```python
def instrument_iniSetting(instrument_name):
    config = configparser.ConfigParser()
    FILE_NAME = '../../test_xml.ini'  # Relative to src/lowsheen_lib/
    config.read(FILE_NAME)

    inst_addr = config['Setting'][instrument_name]

    try:
        if 'COM' in inst_addr:
            # pySerial path
            comport_name, comport_baudrate = parse_comport_address(inst_addr)
            instrument = serial.Serial(comport_name, comport_baudrate, timeout=1)
        else:
            # PyVISA path
            rm = pyvisa.ResourceManager()
            instrument = rm.open_resource(inst_addr, timeout=5000)

            if "ASRL" in inst_addr:
                inst_addr, BaudRate, StopBits = parse_serial_address(inst_addr)
                setup_serial(instrument, BaudRate, StopBits)
            elif 'TCPIP' and "SOCKET" in inst_addr:
                setup_tcpip_socket(instrument)

    except Exception as e:
        print(f"[{instrument_name}] Instrument initialization failed: {str(e)}")
        return None

    return instrument
```

#### Connection Type Decision Tree

```
inst_addr contains "COM"?
├─ YES → pySerial (COM3/baud:115200)
│         └─ serial.Serial(port, baudrate, timeout=1)
│
└─ NO → PyVISA (VISA Resource Manager)
         ├─ Contains "ASRL"? → Serial via VISA
         │   └─ Configure baud rate and stop bits
         │
         ├─ Contains "TCPIP" AND "SOCKET"? → TCPIP Socket
         │   └─ Configure terminator and end-on-read
         │
         └─ Otherwise → Standard VISA (GPIB, USB-TMC, etc.)
             └─ Use default settings
```

---

### 2. parse_comport_address(address)

Parses pySerial COM port address string.

#### Format
```
COM<port>/baud:<baudrate>
```

#### Parameters
- `address` (str): COM port address (e.g., "COM3/baud:115200")

#### Returns
- `tuple[str, int]`: (port_name, baudrate)
  - Example: `("COM3", 115200)`

#### Implementation
```python
def parse_comport_address(address):
    parts = address.split('/')
    comport_name = parts[0]           # "COM3"
    comport_baudrate = int(parts[1].split(':')[1])  # 115200
    return comport_name, comport_baudrate
```

#### Examples
| Input | Output |
|-------|--------|
| `COM3/baud:115200` | `("COM3", 115200)` |
| `COM5/baud:9600` | `("COM5", 9600)` |
| `COM10/baud:57600` | `("COM10", 57600)` |

---

### 3. parse_serial_address(address)

Parses VISA serial (ASRL) address string with extended parameters.

#### Format
```
ASRL<port>::INSTR/baud:<baudrate>/bits:<stopbits>
```

#### Parameters
- `address` (str): VISA serial address (e.g., "ASRL2::INSTR/baud:115200/bits:1")

#### Returns
- `tuple[str, int, str]`: (visa_address, baudrate, stopbits)
  - Example: `("ASRL2::INSTR", 115200, "1")`

#### Implementation
```python
def parse_serial_address(address):
    parts = address.split('/')
    inst_addr = parts[0]                    # "ASRL2::INSTR"
    BaudRate = int(parts[1].split(':')[1])  # 115200
    StopBits = parts[2].split(':')[1]       # "1"
    return inst_addr, BaudRate, StopBits
```

#### Examples
| Input | Output |
|-------|--------|
| `ASRL2::INSTR/baud:115200/bits:1` | `("ASRL2::INSTR", 115200, "1")` |
| `ASRL1::INSTR/baud:9600/bits:2` | `("ASRL1::INSTR", 9600, "2")` |
| `ASRL3::INSTR/baud:19200/bits:1.5` | `("ASRL3::INSTR", 19200, "1.5")` |

#### Stop Bits Values
- `"1"` - 1 stop bit (most common)
- `"1.5"` - 1.5 stop bits (rare)
- `"2"` - 2 stop bits
- `"0"` - Skip stop bits configuration

---

### 4. setup_serial(instrument, baud_rate, stop_bits)

Configures VISA serial port parameters (baud rate and stop bits).

#### Parameters
- `instrument`: VISA resource object
- `baud_rate` (int): Baud rate (e.g., 115200)
- `stop_bits` (str): Stop bits setting ("1", "1.5", "2", or "0")

#### VISA Attributes Configured

| Attribute | Purpose | Possible Values |
|-----------|---------|-----------------|
| `VI_ATTR_ASRL_BAUD` | Baud rate | 9600, 19200, 57600, 115200, etc. |
| `VI_ATTR_ASRL_STOP_BITS` | Stop bits | VI_ASRL_STOP_ONE, VI_ASRL_STOP_ONE5, VI_ASRL_STOP_TWO |

#### Implementation
```python
def setup_serial(instrument, baud_rate, stop_bits):
    print('setup_serial')

    # Set baud rate
    instrument.set_visa_attribute(constants.VI_ATTR_ASRL_BAUD, baud_rate)
    print('serial instrument setup BAUDRATE already')

    # Set stop bits (if not "0")
    if stop_bits != '0':
        stop_bits_mapping = {
            '1': constants.VI_ASRL_STOP_ONE,
            '1.5': constants.VI_ASRL_STOP_ONE5,
            '2': constants.VI_ASRL_STOP_TWO
        }
        stop_bits_value = stop_bits_mapping.get(stop_bits, constants.VI_ASRL_STOP_ONE)
        instrument.set_visa_attribute(constants.VI_ATTR_ASRL_STOP_BITS, stop_bits_value)
        print('serial instrument setup STOPBITS already')
```

#### Default Serial Settings (Not Configured)

The function only sets baud rate and stop bits. Other parameters use VISA defaults:
- Data bits: 8
- Parity: None
- Flow control: None

**Note:** If custom data bits/parity are needed, extend this function.

---

### 5. setup_tcpip_socket(instrument)

Configures TCPIP socket connection parameters for raw socket communication.

#### Parameters
- `instrument`: VISA resource object (TCPIP socket)

#### VISA Attributes Configured

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `VI_ATTR_TERMCHAR_EN` | `VI_TRUE` | Enable termination character detection |
| `VI_ATTR_TERMCHAR` | `10` (0x0A) | Set terminator to `\n` (line feed) |
| `VI_ATTR_SUPPRESS_END_EN` | `VI_TRUE` | Enable end-on-read suppression |

#### Implementation
```python
def setup_tcpip_socket(instrument):
    print('setup_tcpip_socket')

    # Enable termination character
    instrument.set_visa_attribute(constants.VI_ATTR_TERMCHAR_EN, constants.VI_TRUE)
    instrument.set_visa_attribute(constants.VI_ATTR_TERMCHAR, 10)  # \n = 0x0A
    print('socket instrument setup TERMCHAR already')

    # Enable end-on-read
    instrument.set_visa_attribute(constants.VI_ATTR_SUPPRESS_END_EN, constants.VI_TRUE)
    print('socket instrument setup END ON READ already')
```

#### Configuration Explained

**Termination Character (TERMCHAR):**
- **Purpose:** Automatically detect end of message
- **Value:** ASCII 10 (Line Feed, `\n`)
- **Behavior:** `read()` stops when `\n` is received

**End-on-Read Suppression:**
- **Purpose:** Prevent timeout errors on partial reads
- **Behavior:** Allow multiple reads until terminator is found

**Why These Settings?**
Most SCPI instruments use `\n` as message terminator. These settings ensure:
1. Commands like `*IDN?\n` get proper responses
2. Multi-line responses are handled correctly
3. Timeouts only occur on true communication failures

---

### 6. instrument() - Legacy Function

**Status:** Legacy - Replaced by `instrument_iniSetting()`

Auto-discovers instruments by querying all VISA resources with `*IDN?` and mapping model names to addresses.

#### Parameters
- `instrument_name` (str): Model name from *IDN? response (e.g., "N5767A")

#### Returns
- VISA resource object if found
- None if not found (prints error)

#### Implementation
```python
def instrument(instrument_name):
    rm = pyvisa.ResourceManager()
    inst_list = rm.list_resources()
    instrument_mapping = {}

    # Build mapping: model -> address
    for inst_addr in inst_list:
        instrument = rm.open_resource(inst_addr)
        instrument_id = instrument.query('*IDN?').split(',')[1].strip()
        instrument_mapping[instrument_id.strip()] = inst_addr
        instrument.close()

    # Find by name
    if instrument_name in instrument_mapping:
        inst_addr = instrument_mapping[instrument_name]
        instrument = rm.open_resource(inst_addr, timeout=5000)
        return instrument
    else:
        print("Error: The instrument name cannot find the corresponding port.")
        return None
```

#### Limitations

❌ **Why Legacy:**
1. **Slow:** Queries every VISA resource (can take 10+ seconds)
2. **Fragile:** Depends on *IDN? format (not all instruments support this)
3. **No Config:** Hard-coded logic, no external configuration
4. **No pySerial:** Only supports VISA resources

✅ **Use `instrument_iniSetting()` Instead:**
- Fast (direct connection)
- Configurable (test_xml.ini)
- Supports pySerial + VISA
- Protocol-agnostic

---

### 7. instrument_initial(instrument) - Unused Function

Sends `*RST` command to reset instrument to factory defaults.

#### Parameters
- `instrument`: VISA resource object

#### Implementation
```python
def instrument_initial(instrument):
    remote_cmd = '*RST'
    print("remote_cmd : " + str(remote_cmd))
    instrument.write(str(remote_cmd))
    print('instrument reset already')
```

#### Status
**Currently unused** - Most instrument drivers handle reset internally if needed.

**Reason:** Not all instruments support *RST, and some require specific initialization sequences.

---

## Supported Connection Types

### 1. TCPIP Socket

**Format:**
```
TCPIP<board>::<ip_address>::<port>::SOCKET
```

**Examples:**
```ini
PSW3072_1 = TCPIP0::192.168.1.100::5025::SOCKET
N5767A_1 = TCPIP0::10.0.0.5::5025::SOCKET
```

**Use Case:** Modern instruments with Ethernet/LAN interface using SCPI-RAW protocol.

**Configuration Applied:** Terminator = `\n`, end-on-read enabled

---

### 2. TCPIP VXI-11 (INSTR)

**Format:**
```
TCPIP<board>::<ip_address>::<device_name>::INSTR
```

**Examples:**
```ini
Oscilloscope_1 = TCPIP0::192.168.1.50::inst0::INSTR
```

**Use Case:** Instruments using VXI-11 protocol (older Agilent/Keysight instruments).

**Configuration Applied:** Default VISA settings (no custom config)

---

### 3. Serial via VISA (ASRL)

**Format:**
```
ASRL<port>::INSTR/baud:<baudrate>/bits:<stopbits>
```

**Examples:**
```ini
Keithley2015_1 = ASRL2::INSTR/baud:115200/bits:1
DMM_1 = ASRL1::INSTR/baud:9600/bits:0
```

**Use Case:** Serial instruments accessed through VISA layer (USB-to-Serial adapters).

**Configuration Applied:** Baud rate, stop bits

---

### 4. Serial via pySerial (COM)

**Format:**
```
COM<port>/baud:<baudrate>
```

**Examples:**
```ini
2306_1 = COM3/baud:115200
PowerSupply_2 = COM5/baud:9600
```

**Use Case:** Direct COM port access (faster than VISA serial, useful for non-VISA protocols).

**Configuration Applied:** Baud rate, timeout=1 second

---

### 5. GPIB

**Format:**
```
GPIB<board>::<address>::INSTR
```

**Examples:**
```ini
34970A_1 = GPIB0::9::INSTR
Multimeter_1 = GPIB0::22::INSTR
```

**Use Case:** Legacy instruments with GPIB interface.

**Configuration Applied:** Default VISA settings

---

### 6. USB-TMC (USB Instruments)

**Format:**
```
USB<board>::<vendor_id>::<product_id>::<serial>::INSTR
```

**Examples:**
```ini
SignalGen_1 = USB0::0x0957::0x1796::MY12345678::INSTR
```

**Use Case:** Modern USB instruments (auto-detected by PyVISA).

**Configuration Applied:** Default VISA settings

---

## Configuration File Format

### test_xml.ini Structure

```ini
[Setting]
# Power Supplies
PSW3072_1 = TCPIP0::192.168.1.100::5025::SOCKET
PSW3072_2 = COM3/baud:115200

# Multimeters
Keithley2015_1 = ASRL2::INSTR/baud:115200/bits:1
34970A_1 = GPIB0::9::INSTR

# Signal Generators
N5182A_1 = TCPIP0::192.168.1.200::5025::SOCKET

# Other Instruments
DMM_1 = USB0::0x0957::0x1796::MY12345678::INSTR
```

### Naming Convention

**Format:** `<Model>_<Index>`
- `Model`: Instrument model (e.g., PSW3072, Keithley2015)
- `Index`: Sequential number for multiple units (1, 2, 3...)

**Examples:**
- `PSW3072_1` - First PSW3072 power supply
- `PSW3072_2` - Second PSW3072 power supply
- `Keithley2015_1` - First Keithley 2015 multimeter

---

## Error Handling

### Current Implementation

```python
try:
    # Connection logic
except Exception as e:
    print(f"[{instrument_name}] Instrument initialization failed: {str(e)}")
    return None
```

**Behavior:**
- ✅ Catches all exceptions
- ✅ Prints descriptive error message with instrument name
- ✅ Returns None instead of crashing
- ❌ Does not log to file
- ❌ Does not distinguish error types

### Common Error Scenarios

| Error | Cause | Message Example |
|-------|-------|-----------------|
| KeyError | Instrument not in INI | `KeyError: 'PSW3072_1'` |
| VisaIOError | Connection timeout | `VI_ERROR_TMO: Timeout expired` |
| SerialException | COM port in use | `PermissionError: [Errno 13]` |
| ValueError | Invalid address format | `ValueError: invalid literal for int()` |

### Recommended Error Handling

```python
from pyvisa import VisaIOError
from serial import SerialException

try:
    instrument = instrument_iniSetting('PSW3072_1')
    if instrument is None:
        raise ConnectionError("Instrument initialization returned None")
except KeyError:
    print(f"Error: '{instrument_name}' not found in test_xml.ini")
except VisaIOError as e:
    print(f"VISA error: {e}")
except SerialException as e:
    print(f"Serial port error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Usage Examples

### Basic Connection

```python
from remote_instrument import instrument_iniSetting

# Connect to power supply
power_supply = instrument_iniSetting('PSW3072_1')
if power_supply is None:
    print("Connection failed")
    exit(1)

# Use instrument
power_supply.write('VOLT 12\n')
power_supply.write('OUTP ON\n')

# Cleanup
power_supply.close()
```

### Handling Different Connection Types

```python
# TCPIP Socket
socket_inst = instrument_iniSetting('PSW3072_1')
socket_inst.write('*IDN?\n')
response = socket_inst.read()

# Serial via pySerial
serial_inst = instrument_iniSetting('2306_1')
serial_inst.write(b'VOLT 5\n')
time.sleep(0.1)
response = serial_inst.read(100)

# VISA Serial
visa_serial = instrument_iniSetting('Keithley2015_1')
visa_serial.query('*IDN?')
```

### Error Handling Pattern

```python
def safe_connect(instrument_name, retries=3):
    for attempt in range(retries):
        inst = instrument_iniSetting(instrument_name)
        if inst is not None:
            return inst
        time.sleep(1)
    raise ConnectionError(f"Failed to connect to {instrument_name} after {retries} attempts")

# Usage
try:
    dmm = safe_connect('34970A_1')
    idn = dmm.query('*IDN?')
    print(f"Connected: {idn}")
except ConnectionError as e:
    print(e)
```

### Context Manager Pattern

```python
from contextlib import contextmanager

@contextmanager
def instrument_context(instrument_name):
    inst = instrument_iniSetting(instrument_name)
    if inst is None:
        raise ConnectionError(f"Cannot connect to {instrument_name}")
    try:
        yield inst
    finally:
        inst.close()

# Usage
with instrument_context('PSW3072_1') as psu:
    psu.write('VOLT 12\n')
    psu.write('OUTP ON\n')
# Auto-closed after block
```

---

## Integration with Instrument Drivers

### Standard Driver Pattern

```python
# Example: PSW3072.py
from remote_instrument import instrument_iniSetting
import sys
import ast

if __name__ == "__main__":
    sequence = sys.argv[1]
    args = ast.literal_eval(sys.argv[2])

    # Get instrument name from args
    instrument_name = args['Instrument']

    # Connect
    instrument = instrument_iniSetting(instrument_name)
    if instrument is None:
        print("Error: Cannot connect to instrument")
        sys.exit(1)

    # Execute commands
    if sequence == '--final':
        instrument.write('OUTP OFF\n')
    else:
        volt = args['SetVolt']
        curr = args['SetCurr']
        instrument.write(f'VOLT {volt}\n')
        instrument.write(f'CURR {curr}\n')
        instrument.write('OUTP ON\n')

    print("1")  # Success
```

### Driver Best Practices

1. **Always check for None:**
   ```python
   instrument = instrument_iniSetting(name)
   if instrument is None:
       sys.exit(1)  # Or raise exception
   ```

2. **Use timeout for operations:**
   ```python
   instrument.timeout = 5000  # 5 seconds
   ```

3. **Close on exit (VISA only):**
   ```python
   try:
       # ... operations ...
   finally:
       if hasattr(instrument, 'close'):
           instrument.close()
   ```

4. **Handle both pySerial and VISA:**
   ```python
   # For write operations
   if isinstance(instrument, serial.Serial):
       instrument.write(cmd.encode())
   else:
       instrument.write(cmd)
   ```

---

## Troubleshooting

### Connection Issues

#### Problem: "Instrument initialization failed: VI_ERROR_RSRC_NFOUND"
**Cause:** VISA resource not found
**Solution:**
1. Check physical connection
2. Verify IP address/port in test_xml.ini
3. Run `pyvisa-info` to list available resources

#### Problem: "PermissionError: [Errno 13] Permission denied: 'COM3'"
**Cause:** COM port already in use
**Solution:**
1. Close other applications using the port
2. Restart computer if port is locked
3. Check Device Manager (Windows) for port conflicts

#### Problem: "KeyError: 'PSW3072_1'"
**Cause:** Instrument not defined in test_xml.ini
**Solution:**
Add instrument to `[Setting]` section:
```ini
[Setting]
PSW3072_1 = TCPIP0::192.168.1.100::5025::SOCKET
```

### Configuration Issues

#### Problem: Slow connection (10+ seconds)
**Cause:** Using legacy `instrument()` function
**Solution:** Use `instrument_iniSetting()` instead

#### Problem: Timeout on serial communication
**Cause:** Incorrect baud rate
**Solution:** Verify baud rate matches instrument:
```ini
# Check instrument manual for correct baud rate
Keithley2015_1 = ASRL2::INSTR/baud:115200/bits:1  # Correct
```

#### Problem: Garbled responses from socket
**Cause:** Missing terminator configuration
**Solution:** Verify `setup_tcpip_socket()` is being called (check for "SOCKET" in address)

---

## Performance Considerations

### Connection Time

| Connection Type | Typical Time | Notes |
|----------------|--------------|-------|
| TCPIP Socket | 50-200ms | Fast, depends on network |
| VISA Serial | 200-500ms | VISA overhead |
| pySerial | 50-100ms | Fastest serial option |
| GPIB | 100-300ms | Depends on bus speed |
| USB-TMC | 100-200ms | Moderate speed |

### Optimization Tips

1. **Reuse connections:**
   ```python
   # Bad: Connect for each command
   for cmd in commands:
       inst = instrument_iniSetting('DMM_1')
       inst.write(cmd)
       inst.close()

   # Good: Connect once
   inst = instrument_iniSetting('DMM_1')
   for cmd in commands:
       inst.write(cmd)
   inst.close()
   ```

2. **Use pySerial for simple protocols:**
   ```ini
   # Slower (VISA overhead)
   Device_1 = ASRL3::INSTR/baud:115200/bits:1

   # Faster (direct)
   Device_1 = COM3/baud:115200
   ```

3. **Batch commands when possible:**
   ```python
   # Slower: Multiple writes
   inst.write('VOLT 12\n')
   inst.write('CURR 3\n')
   inst.write('OUTP ON\n')

   # Faster: Single write (if instrument supports)
   inst.write('VOLT 12;CURR 3;OUTP ON\n')
   ```

---

## Design Patterns

### Strengths

✅ **Protocol Abstraction:** Single interface for multiple protocols
✅ **Configuration-Driven:** Easy to reconfigure without code changes
✅ **Error Resilience:** Returns None instead of crashing
✅ **Extensible:** Easy to add new connection types

### Weaknesses

❌ **No Connection Pooling:** Creates new connection each time
❌ **No Connection Validation:** Doesn't verify instrument responds
❌ **No Logging:** Only prints to stdout
❌ **No Retry Logic:** Single attempt, no automatic retry
❌ **Mixed Return Types:** Returns Serial or VISA object (type inconsistency)

### Suggested Improvements

```python
# 1. Add connection validation
def instrument_iniSetting(instrument_name, validate=True):
    inst = _connect(instrument_name)  # Existing logic

    if validate and inst is not None:
        try:
            if hasattr(inst, 'query'):
                idn = inst.query('*IDN?')
            # Validate response...
        except:
            inst.close()
            return None
    return inst

# 2. Add retry logic
def instrument_iniSetting(instrument_name, retries=3):
    for attempt in range(retries):
        inst = _connect(instrument_name)
        if inst is not None:
            return inst
        time.sleep(0.5)
    return None

# 3. Add logging
import logging
def instrument_iniSetting(instrument_name):
    logging.info(f"Connecting to {instrument_name}...")
    # ... connection logic ...
    if inst is None:
        logging.error(f"Failed to connect to {instrument_name}")
    else:
        logging.info(f"Successfully connected to {instrument_name}")
    return inst
```

---

## Summary

**remote_instrument.py Characteristics:**

✅ **Strengths:**
- Unified interface for multiple protocols
- Configuration-based (no hardcoding)
- Supports both VISA and pySerial
- Handles protocol-specific setup automatically
- Error handling with descriptive messages

⚠️ **Limitations:**
- No connection pooling or caching
- No connection validation
- Mixed return types (Serial vs VISA)
- No retry logic
- Limited logging

**Use Case:** Ideal for test environments where:
- Multiple instrument types are used
- Connection parameters change between test stations
- Protocol flexibility is needed
- Simple error handling is sufficient

**For Production:** Consider adding connection pooling, validation, logging, and retry mechanisms.
