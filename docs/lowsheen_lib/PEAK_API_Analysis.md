# PEAK API Analysis

## Overview

The PEAK API is a Python-based instrument control library for PEAK-System hardware devices, providing CAN (Controller Area Network) and LIN (Local Interconnect Network) bus communication capabilities. This module serves as a Python wrapper around the PEAK-System PCAN-Basic and PLIN-API DLLs, enabling automated testing and communication with automotive electronic control units (ECUs).

**Directory Location:** `src/lowsheen_lib/PEAK_API/`

**Primary Dependencies:**
- `ctypes` - Foreign Function Library for Python/DLL interoperation
- `PCANBasic.dll` / `libpcanbasic.so` / `libPCBUSB.dylib` - PCAN-Basic API library
- `PLinApi.dll` - PLIN-API library for LIN bus communication

**Supported Hardware:**
- PCAN-USB adapters (CAN and CAN-FD)
- PCAN-PCI adapters
- PCAN-LAN (gateway devices)
- PCAN-USB Pro LIN
- PLIN-USB adapters

---

## Architecture

### Module Structure

```
PEAK_API/
├── LookUpChannel.py      # Channel lookup and device discovery
├── PCANBasic.py          # PCAN-Basic API wrapper for CAN/CAN-FD
├── PLinApi.py            # PLIN-API wrapper for LIN bus
├── PEAK.py               # Main application (ManualCAN, PLinApiConsole)
└── README.txt            # Documentation
```

### Design Patterns

The module follows a **wrapper pattern** with:
- ctypes-based Foreign Function Interface (FFI) to native DLLs
- Structure-based message passing (TPCANMsg, TPCANMsgFD, TLINMsg)
- Handle-based resource management (TPCANHandle, HLINHW)
- Class-based API wrappers (PCANBasic, PLinApi, LookUpChannel)

---

## File-by-File Analysis

### PCANBasic.py

**Purpose:** Complete Python wrapper for the PCAN-Basic API, supporting CAN and CAN-FD communication.

**Key Components:**

| Type Definition | ctypes Type | Description |
|----------------|-------------|-------------|
| `TPCANHandle` | c_ushort | PCAN hardware channel handle |
| `TPCANStatus` | int | PCAN status/error code |
| `TPCANParameter` | c_ubyte | PCAN parameter to read/set |
| `TPCANDevice` | c_ubyte | PCAN device type |
| `TPCANMessageType` | c_ubyte | CAN message type |
| `TPCANBaudrate` | c_ushort | Baud rate register value |
| `TPCANBitrateFD` | c_char_p | CAN-FD bitrate string |
| `TPCANTimestampFD` | c_ulonglong | CAN-FD timestamp |

#### Message Structures

```python
# Standard CAN Message (8 bytes max)
class TPCANMsg (Structure):
    _fields_ = [
        ("ID",      c_uint),           # 11/29-bit message identifier
        ("MSGTYPE", TPCANMessageType), # Message type flags
        ("LEN",     c_ubyte),          # Data Length Code (0..8)
        ("DATA",    c_ubyte * 8)       # Message data (DATA[0]..DATA[7])
    ]

# CAN-FD Message (64 bytes max)
class TPCANMsgFD (Structure):
    _fields_ = [
        ("ID",      c_uint),           # 11/29-bit message identifier
        ("MSGTYPE", TPCANMessageType), # Message type flags
        ("DLC",     c_ubyte),          # Data Length Code (0..15)
        ("DATA",    c_ubyte * 64)      # Message data (DATA[0]..DATA[63])
    ]

# CAN Message Timestamp
class TPCANTimestamp (Structure):
    _fields_ = [
        ("millis",          c_uint),    # Milliseconds: 0..2^32-1
        ("millis_overflow", c_ushort),  # Roll-arounds of millis
        ("micros",          c_ushort)   # Microseconds: 0..999
    ]
```

#### PCANBasic Class Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `Initialize()` | Channel, Btr0Btr1, HwType, IOPort, Interrupt | TPCANStatus | Initialize CAN channel |
| `InitializeFD()` | Channel, BitrateFD | TPCANStatus | Initialize CAN-FD channel |
| `Uninitialize()` | Channel | TPCANStatus | Uninitialize channel(s) |
| `Reset()` | Channel | TPCANStatus | Reset RX/TX queues |
| `GetStatus()` | Channel | TPCANStatus | Get channel status |
| `Read()` | Channel | (TPCANStatus, TPCANMsg, TPCANTimestamp) | Read CAN message |
| `ReadFD()` | Channel | (TPCANStatus, TPCANMsgFD, TPCANTimestampFD) | Read CAN-FD message |
| `Write()` | Channel, MessageBuffer | TPCANStatus | Write CAN message |
| `WriteFD()` | Channel, MessageBuffer | TPCANStatus | Write CAN-FD message |
| `FilterMessages()` | Channel, FromID, ToID, Mode | TPCANStatus | Configure reception filter |
| `GetValue()` | Channel, Parameter | (TPCANStatus, value) | Get channel parameter |
| `SetValue()` | Channel, Parameter, Buffer | TPCANStatus | Set channel parameter |
| `GetErrorText()` | Error, Language | (TPCANStatus, text) | Get error description |
| `LookUpChannel()` | Parameters | (TPCANStatus, TPCANHandle) | Find channel by criteria |

#### PCAN Channel Handles

| Handle Value | Hardware Type | Channel |
|--------------|---------------|---------|
| `0x51` | PCAN_USBBUS1 | USB Channel 1 |
| `0x52` | PCAN_USBBUS2 | USB Channel 2 |
| `0x53` | PCAN_USBBUS3 | USB Channel 3 |
| `0x54` | PCAN_USBBUS4 | USB Channel 4 |
| `0x509 - 0x510` | PCAN_USBBUS9-16 | USB Channels 9-16 |
| `0x41 - 0x410` | PCAN_PCIBUS1-16 | PCI Channels 1-16 |
| `0x801 - 0x810` | PCAN_LANBUS1-16 | LAN Channels 1-16 |

#### Baud Rate Constants

| Constant | Value | Bitrate |
|----------|-------|---------|
| `PCAN_BAUD_1M` | 0x0014 | 1 MBit/s |
| `PCAN_BAUD_500K` | 0x001C | 500 kBit/s |
| `PCAN_BAUD_250K` | 0x011C | 250 kBit/s |
| `PCAN_BAUD_125K` | 0x031C | 125 kBit/s |
| `PCAN_BAUD_100K` | 0x432F | 100 kBit/s |
| `PCAN_BAUD_50K` | 0x472F | 50 kBit/s |

#### Message Type Flags

| Flag | Value | Description |
|------|-------|-------------|
| `PCAN_MESSAGE_STANDARD` | 0x00 | Standard Frame (11-bit ID) |
| `PCAN_MESSAGE_EXTENDED` | 0x02 | Extended Frame (29-bit ID) |
| `PCAN_MESSAGE_RTR` | 0x01 | Remote Transfer Request |
| `PCAN_MESSAGE_FD` | 0x04 | CAN-FD frame |
| `PCAN_MESSAGE_BRS` | 0x08 | Bit Rate Switch |
| `PCAN_MESSAGE_ESI` | 0x10 | Error State Indicator |

---

### PLinApi.py

**Purpose:** Complete Python wrapper for the PLIN-API, supporting LIN bus master and slave communication.

**Key Components:**

| Type Definition | ctypes Type | Description |
|----------------|-------------|-------------|
| `HLINCLIENT` | c_ubyte | LIN client handle |
| `HLINHW` | c_ushort | LIN hardware handle |
| `TLINError` | int | LIN error code |
| `TLINMsgType` | c_ubyte | Received message type |
| `TLINChecksumType` | c_ubyte | Message checksum type |
| `TLINHardwareMode` | c_ubyte | Hardware operation mode |
| `TLINHardwareState` | c_ubyte | Hardware status |

#### LIN Message Structures

```python
# LIN Message to be sent
class TLINMsg (Structure):
    _fields_ = [
        ("FrameId",        c_ubyte),           # Frame ID (6 bit) + Parity (2 bit)
        ("Length",         c_ubyte),           # Frame Length (1..8)
        ("Direction",      TLINDirection),     # Publisher/Subscriber
        ("ChecksumType",   TLINChecksumType),  # Classic/Enhanced/Auto
        ("Data",           c_ubyte * 8),       # Data bytes (0..7)
        ("Checksum",       c_ubyte)            # Frame Checksum
    ]

# Received LIN Message
class TLINRcvMsg (Structure):
    _fields_ = [
        ("Type",           TLINMsgType),       # Message type
        ("FrameId",        c_ubyte),           # Frame ID + Parity
        ("Length",         c_ubyte),           # Frame Length
        ("Direction",      TLINDirection),     # Direction
        ("ChecksumType",   TLINChecksumType),  # Checksum type
        ("Data",           c_ubyte * 8),       # Data bytes
        ("Checksum",       c_ubyte),           # Checksum
        ("ErrorFlags",     TLINMsgErrors),     # Error flags
        ("TimeStamp",      c_uint64),          # Timestamp in microseconds
        ("hHw",            HLINHW)             # Hardware handle
    ]

# LIN Frame Entry
class TLINFrameEntry (Structure):
    _fields_ = [
        ("FrameId",        c_ubyte),           # Frame ID (without parity)
        ("Length",         c_ubyte),           # Frame Length (1..8)
        ("Direction",      TLINDirection),     # Direction
        ("ChecksumType",   TLINChecksumType),  # Checksum type
        ("Flags",          c_ushort),          # Frame flags
        ("InitialData",    c_ubyte * 8)        # Initial data
    ]

# LIN Schedule Slot
class TLINScheduleSlot (Structure):
    _fields_ = [
        ("Type",           TLINSlotType),      # Slot type
        ("Delay",          c_ushort),          # Delay in milliseconds
        ("FrameId",        c_ubyte * 8),       # Frame IDs
        ("CountResolve",   c_ubyte),           # ID count / Resolve schedule
        ("Handle",         c_uint)             # Slot handle (read-only)
    ]
```

#### PLinApi Class Methods

**Client Management:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `RegisterClient()` | strName, hWnd, hClient | TLINError | Register client with LIN Manager |
| `RemoveClient()` | hClient | TLINError | Remove client from LIN Manager |
| `ConnectClient()` | hClient, hHw | TLINError | Connect client to hardware |
| `DisconnectClient()` | hClient, hHw | TLINError | Disconnect client from hardware |
| `ResetClient()` | hClient | TLINError | Flush client queue and reset counters |

**Hardware Management:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `InitializeHardware()` | hClient, hHw, byMode, wBaudrate | TLINError | Initialize hardware with mode/baudrate |
| `GetAvailableHardware()` | pBuff, wBuffSize, pCount | TLINError | Get available hardware handles |
| `ResetHardware()` | hClient, hHw | TLINError | Flush hardware queues and reset |
| `ResetHardwareConfig()` | hClient, hHw | TLINError | Reset hardware to defaults |
| `IdentifyHardware()` | hHw | TLINError | Blink LED to identify hardware |
| `GetHardwareParam()` | hHw, wParam, pBuff, wBuffSize | TLINError | Get hardware parameter |
| `SetHardwareParam()` | hClient, hHw, wParam, pBuff, wBuffSize | TLINError | Set hardware parameter |

**Message Communication:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `Write()` | hClient, hHw, pMsg | TLINError | Transmit LIN message |
| `Read()` | hClient, pMsg | TLINError | Read next message |
| `ReadMulti()` | hClient, pMsgBuff, iMaxCount, pCount | TLINError | Read multiple messages |

**Frame Configuration:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `SetFrameEntry()` | hClient, hHw, pFrameEntry | TLINError | Configure LIN frame |
| `GetFrameEntry()` | hHw, pFrameEntry | TLINError | Get frame configuration |
| `UpdateByteArray()` | hClient, hHw, bFrameId, bIndex, bLen, pData | TLINError | Update frame data |
| `RegisterFrameId()` | hClient, hHw, bFromFrameId, bToFrameId | TLINError | Set message filter |

**Schedule Management:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `SetSchedule()` | hClient, hHw, iScheduleNumber, pSchedule, iSlotCount | TLINError | Configure schedule slots |
| `GetSchedule()` | hHw, iScheduleNumber, pScheduleBuff, iMaxSlotCount, pSlotCount | TLINError | Get schedule slots |
| `DeleteSchedule()` | hClient, hHw, iScheduleNumber | TLINError | Remove schedule |
| `StartSchedule()` | hClient, hHw, iScheduleNumber | TLINError | Activate schedule |
| `SuspendSchedule()` | hClient, hHw | TLINError | Suspend active schedule |
| `ResumeSchedule()` | hClient, hHw | TLINError | Resume suspended schedule |

**Keep-Alive:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `StartKeepAlive()` | hClient, hHw, bFrameId, wPeriod | TLINError | Start keep-alive frame |
| `SuspendKeepAlive()` | hClient, hHw | TLINError | Suspend keep-alive |
| `ResumeKeepAlive()` | hClient, hHw | TLINError | Resume keep-alive |

**Utility Functions:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `GetStatus()` | hHw, pStatusBuff | TLINError | Get hardware status |
| `CalculateChecksum()` | pMsg | TLINError | Calculate message checksum |
| `GetPID()` | pframeid | TLINError | Get Protected ID |
| `GetVersion()` | pVerBuffer | TLINError | Get API version |
| `GetErrorText()` | dwError, bLanguage, strTextBuff, wBuffSize | TLINError | Get error description |
| `GetClientFilter()` | hClient, hHw, pRcvMask | TLINError | Get client filter |
| `SetClientFilter()` | hClient, hHw, iRcvMask | TLINError | Set client filter |

#### LIN Hardware Modes

| Mode | Value | Description |
|------|-------|-------------|
| `TLIN_HARDWAREMODE_NONE` | 0 | Not initialized |
| `TLIN_HARDWAREMODE_SLAVE` | 1 | Slave mode |
| `TLIN_HARDWAREMODE_MASTER` | 2 | Master mode |

#### LIN Message Directions

| Direction | Value | Description |
|-----------|-------|-------------|
| `TLIN_DIRECTION_DISABLED` | 0 | Direction disabled |
| `TLIN_DIRECTION_PUBLISHER` | 1 | Publisher (transmits data) |
| `TLIN_DIRECTION_SUBSCRIBER` | 2 | Subscriber (receives data) |
| `TLIN_DIRECTION_SUBSCRIBER_AUTOLENGTH` | 3 | Subscriber with auto length detection |

#### LIN Checksum Types

| Type | Value | Description |
|------|-------|-------------|
| `TLIN_CHECKSUMTYPE_CUSTOM` | 0 | Custom checksum |
| `TLIN_CHECKSUMTYPE_CLASSIC` | 1 | Classic checksum (LIN 1.x) |
| `TLIN_CHECKSUMTYPE_ENHANCED` | 2 | Enhanced checksum (LIN 2.0) |
| `TLIN_CHECKSUMTYPE_AUTO` | 3 | Auto-detect |

#### LIN Baud Rates

| Rate | Value |
|------|-------|
| 2400 | `c_ushort(2400)` |
| 9600 | `c_ushort(9600)` |
| 10400 | `c_ushort(10400)` |
| 19200 | `c_ushort(19200)` |

---

### LookUpChannel.py

**Purpose:** Utility class for dynamically finding and connecting to PCAN channels based on device criteria.

**Class Structure:**

```python
class LookUpChannel():
    def __init__(self, DeviceType, DeviceID, ControllerNumber, IPAddress=b""):
        """
        Parameters:
            DeviceType: Device type (e.g., b"PCAN_USB")
            DeviceID: Device identifier (e.g., b"5")
            ControllerNumber: Controller index (e.g., b"0")
            IPAddress: IP address for LAN channels
        """
```

**Lookup Parameters:**

| Parameter | Format | Description |
|-----------|--------|-------------|
| `LOOKUP_DEVICE_TYPE` | `"devicetype=<value>"` | Device type (PCAN_USB, PCAN_PCI, etc.) |
| `LOOKUP_DEVICE_ID` | `"deviceid=<value>"` | Device identifier |
| `LOOKUP_CONTROLLER_NUMBER` | `"controllernumber=<value>"` | Controller index (0-based) |
| `LOOKUP_IP_ADDRESS` | `"ipaddress=<value>"` | IP address (LAN only) |

**Usage Example:**
```python
lookup = LookUpChannel(
    DeviceType=b"PCAN_USB",
    DeviceID=b"5",
    ControllerNumber=b"0"
)
# Returns: devDevice, byChannel, handleValue
# Example: ('PCAN_USB', 1, '51')
```

**Helper Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_pcan_handle()` | (device, channel, handleValue) | Extract handle components |
| `GetFormattedError()` | str | Get error description |
| `FormatChannelName()` | str | Format channel name string |
| `GetDeviceName()` | str | Get device name string |

---

### PEAK.py

**Purpose:** Main application providing two primary classes - `ManualCAN` for CAN/CAN-FD operations and `PLinApiConsole` for LIN bus operations.

#### ManualCAN Class

**Purpose:** Handle CAN and CAN-FD message transmission and reception.

**Configuration Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PcanHandle` | None | PCAN channel handle |
| `IsFD` | False | CAN-FD mode flag |
| `Bitrate` | PCAN_BAUD_50K | CAN baud rate |
| `BitrateFD` | 80MHz clock | CAN-FD bitrate string |
| `para_ID` | 0x100 | Message ID for CAN |
| `para_FDID` | 0x110 | Message ID for CAN-FD |
| `para_LEN` | 8 | CAN data length (max 8) |
| `para_FDDLC` | 15 | CAN-FD DLC (0-15) |
| `para_FDLen` | 64 | CAN-FD data length (max 64) |

**Key Methods:**

| Method | Description |
|--------|-------------|
| `InputParameter()` | Parse command-line parameters |
| `WriteMessages()` | Send CAN/CAN-FD message |
| `WriteMessage()` | Send standard CAN message |
| `WriteMessageFD()` | Send CAN-FD message |
| `ReadMessages()` | Read CAN/CAN-FD messages |
| `ReadMessage()` | Read standard CAN message |
| `ReadMessageFD()` | Read CAN-FD message |
| `ProcessMessageCan()` | Process received CAN message |
| `ProcessMessageCanFd()` | Process received CAN-FD message |
| `GetLengthFromDLC()` | Convert DLC to data length |

**CAN-FD DLC to Length Mapping:**

| DLC | Data Length |
|-----|-------------|
| 0-8 | 0-8 bytes |
| 9 | 12 bytes |
| 10 | 16 bytes |
| 11 | 20 bytes |
| 12 | 24 bytes |
| 13 | 32 bytes |
| 14 | 48 bytes |
| 15 | 64 bytes |

**Baudrate Selection (CAN):**

| Command | Baudrate |
|---------|----------|
| `'5K'` | 5 kBit/s |
| `'10K'` | 10 kBit/s |
| `'20K'` | 20 kBit/s |
| `'50K'` | 50 kBit/s |
| `'100K'` | 100 kBit/s |
| `'125K'` | 125 kBit/s |
| `'250K'` | 250 kBit/s |
| `'500K'` | 500 kBit/s |
| `'800K'` | 800 kBit/s |
| `'1M'` | 1 MBit/s |

**CAN-FD Bitrate Configurations:**

| Command | Nominal | Data |
|---------|---------|------|
| `'1'` (50K) | 50 kBit/s | 50 kBit/s |
| `'2'` (500K) | 500 kBit/s | 2 MBit/s |
| `'3'` (250K) | 250 kBit/s | 2 MBit/s |

#### PLinApiConsole Class

**Purpose:** Console interface for LIN bus communication in Master or Slave mode.

**Configuration Parameters:**

| Parameter | Options | Description |
|-----------|---------|-------------|
| `para_Device` | '1', '2' | 1=PCAN-USB Pro, 2=PLIN-USB |
| `para_Channel` | '1', '2' | Channel number |
| `para_Mode` | '1', '2' | 1=Master, 2=Slave |
| `para_BaudRate` | '1'-'4' | 1=2400, 2=9600, 3=10400, 4=19200 |
| `para_Act` | '0'-'3' | 0=RST, 1=Receive All, 2=Receive, 3=Transition |
| `para_Direc` | '1', '2' | 1=Subscriber, 2=Publisher |

**Key Methods:**

| Method | Description |
|--------|-------------|
| `initialize()` | Initialize LIN client |
| `uninitialize()` | Cleanup and disconnect |
| `doLinConnect()` | Connect to LIN hardware |
| `doLinDisconnect()` | Disconnect from hardware |
| `ImportParameter()` | Parse command-line parameters |
| `getAvailableHardware()` | List available LIN devices |
| `configFrameTable()` | Configure frame entries |
| `menuConnect()` | Interactive connection menu |
| `menuRead()` | Interactive read menu |
| `menuWrite()` | Interactive write menu |
| `autoRead()` | Automatic message reading |
| `autoWrite()` | Automatic message writing |
| `RunLin()` | Main LIN execution loop |

---

## Command-Line Interface

### CAN/CAN-FD Commands

**Format:**
```
[DeviceType] [Status] [Type] [Channel] [ID] [Bitrate] [Data/Timeout] [ReadID/Continue] [Timeout] [Continue]
```

| Parameter | Description | Values |
|-----------|-------------|--------|
| DeviceType | Always "PCAN_USB" | - |
| Status | Operation mode | '0'=Read, '1'=Write, '2'=Write+Read |
| Type | CAN type | '1'=CAN, '2'=CAN-FD |
| Channel | Channel number | '1'-'16' |
| ID | Message ID (hex) | e.g., '100', '1FFFFFFF' |
| Bitrate | Bus speed | See baudrate tables |
| Data | Hex data bytes | '01,02,03,04,05,06,07,08' |
| Timeout | Read timeout (ms) | e.g., '5000' |
| Continue | Continue flag | '0'=Stop on receive, '1'=Continue |
| ReadID | Filter ID (hex) | For Write+Read mode |

**CAN Write Example:**
```bash
# Write CAN message, ID=0x100, 500K baud, data=01,02,03,04,05,06,07,08
PCAN_USB 1 1 1 100 500K 01,02,03,04,05,06,07,08
```

**CAN-FD Write Example:**
```bash
# Write CAN-FD message, ID=0x555, 64 bytes, 500K/2M baud
PCAN_USB 1 2 2 555 2 01,02,03,04,05,06,07,08,09,0A,0B,0C,0D,0E,0F,10
```

**CAN Read Example:**
```bash
# Read CAN message, ID=0x100, 500K baud, 5s timeout, stop on receive
PCAN_USB 0 1 1 100 500K 5000 0
```

**CAN-FD Read (All IDs) Example:**
```bash
# Read any CAN-FD message, 500K/2M baud, 5s timeout
PCAN_USB 0 2 1 ALL 2 5000 0
```

**CAN Write+Read Example:**
```bash
# Write then read specific ID, 500K baud
PCAN_USB 2 1 1 100 500K 01,02,03,04,05,06,07,08 43 5000 0
```

### LIN Commands

**Format:**
```
[DeviceType] [Device] [PCANPro/PLIN] [Channel] [Master/Slave] [BaudRate] [Action] [ID] [Subscriber/Publisher] [Data]
```

| Parameter | Description | Values |
|-----------|-------------|--------|
| DeviceType | Always "PCAN_USB" | - |
| Device | Device selection | '1' or '2' |
| Type | Hardware type | '1'=PCAN-USB Pro, '2'=PLIN-USB |
| Channel | Channel number | '1' or '2' |
| Mode | Master/Slave | '1'=Master, '2'=Slave |
| BaudRate | LIN speed | '1'=2400, '2'=9600, '3'=10400, '4'=19200 |
| Action | Operation | '0'=RST, '1'=Receive All, '2'=Receive, '3'=Transition |
| ID | Frame ID (hex) | e.g., '1A', '3C' |
| Direction | Data direction | '1'=Subscriber, '2'=Publisher |
| Data | Hex data bytes | '11;22;33;44;55;66;77;88' |

**LIN Write (Publisher) Example:**
```bash
# Master mode, 9600 baud, publish frame ID 0x1A
PCAN_USB 1 1 2 2 3 1A 2 11;22;33;44;55;66;77;88
```

**LIN Read (Subscriber) Example:**
```bash
# Slave mode, 9600 baud, subscribe to frame ID 0x1A
PCAN_USB 1 1 2 2 1 1A 1
```

**LIN Receive All Example:**
```bash
# Master mode, receive all frames
PCAN_USB 1 1 2 2 1
```

---

## Configuration

### test_xml.ini Format

The PEAK API reads device configuration from `test_xml.ini`:

```ini
[Setting]
PCAN_1 = 3
PCAN_2 = 5
PLIN_1 = 3
PLIN_2 = 5
```

**Device ID Mapping:**

The numeric value in the configuration file represents the device ID used for hardware lookup. Combined with the device type and channel number, the API constructs the lookup parameters to find the correct PCAN handle.

---

## Dependencies and Required DLLs

### Windows

| DLL | Description |
|-----|-------------|
| `PCANBasic.dll` | PCAN-Basic API (CAN/CAN-FD) |
| `PLinApi.dll` | PLIN-API (LIN bus) |

### Linux

| Library | Description |
|---------|-------------|
| `libpcanbasic.so` | PCAN-Basic API (CAN/CAN-FD) |

### macOS

| Library | Description |
|---------|-------------|
| `libPCBUSB.dylib` | PC-BUSB library (third-party, by MacCAN) |

---

## Data Flow Diagrams

### CAN Write Flow

```
┌─────────────────┐
│ Command Parser  │
│ (InputParameter) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LookUpChannel   │ → Find hardware handle
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ InitializeFD()  │ → Initialize CAN-FD channel
│ or Initialize() │ → Initialize CAN channel
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WriteMessageFD()│ → Send CAN-FD message
│ or WriteMessage()│ → Send CAN message
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Uninitialize()  │ → Cleanup
└─────────────────┘
```

### LIN Master Flow

```
┌─────────────────┐
│ ImportParameter │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RegisterClient  │ → Create client handle
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GetAvailableHw  │ → List hardware
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ConnectClient   │ → Connect to hardware
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ InitializeHardware│ → Set mode/baudrate
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SetFrameEntry   │ → Configure frame
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Write()         │ → Transmit LIN message
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DisconnectClient│ → Cleanup
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RemoveClient    │ → Unregister client
└─────────────────┘
```

---

## Error Codes

### PCAN Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0x00000 | PCAN_ERROR_OK | No error |
| 0x00001 | PCAN_ERROR_XMTFULL | Transmit buffer full |
| 0x00002 | PCAN_ERROR_OVERRUN | CAN controller read too late |
| 0x00004 | PCAN_ERROR_BUSLIGHT | Bus error: light limit |
| 0x00008 | PCAN_ERROR_BUSHEAVY | Bus error: heavy limit |
| 0x00010 | PCAN_ERROR_BUSOFF | Bus-off state |
| 0x00020 | PCAN_ERROR_QRCVEMPTY | Receive queue empty |
| 0x00100 | PCAN_ERROR_REGTEST | Hardware test failed |
| 0x00200 | PCAN_ERROR_NODRIVER | Driver not loaded |
| 0x00400 | PCAN_ERROR_HWINUSE | Hardware in use |
| 0x01400 | PCAN_ERROR_ILLHW | Invalid hardware handle |

### LIN Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | TLIN_ERROR_OK | Success |
| 1 | TLIN_ERROR_XMTQUEUE_FULL | Transmit queue full |
| 3 | TLIN_ERROR_RCVQUEUE_EMPTY | Receive queue empty |
| 5 | TLIN_ERROR_ILLEGAL_HARDWARE | Invalid hardware handle |
| 6 | TLIN_ERROR_ILLEGAL_CLIENT | Invalid client handle |
| 11 | TLIN_ERROR_ILLEGAL_BAUDRATE | Baudrate out of range |
| 12 | TLIN_ERROR_ILLEGAL_FRAMEID | Frame ID out of range (0-63) |
| 23 | TLIN_ERROR_ILLEGAL_HARDWARE_MODE | Invalid hardware mode |
| 1001 | TLIN_ERROR_OUT_OF_RESOURCE | Insufficient resources |
| 1002 | TLIN_ERROR_MANAGER_NOT_LOADED | LIN Manager not running |

---

## Integration with PDTool4

The PEAK API is designed for integration into the PDTool4 testing framework:

1. **Called as Subprocess:** The module can be run as a standalone script or compiled executable
2. **Parameter Passing:** Uses command-line arguments for all configuration
3. **Configuration File:** Reads device IDs from `test_xml.ini`
4. **Return Values:** Status messages printed to stdout

**Typical Integration Pattern:**
```python
# From PDTool4 measurement module
subprocess.run([
    'python', 'PEAK.py', 'CAN_write',
    json.dumps({
        'Item': 'CAN',
        'Instrument': 'PCAN_1',
        'Command': 'PCAN_USB 1 1 1 100 500K 01,02,03,04,05,06,07,08'
    })
], check=True)
```

---

## Usage Examples

### Example 1: CAN Message Write (500K baud)

```python
from PCANBasic import *

# Initialize CAN channel
pcan = PCANBasic()
result = pcan.Initialize(PCAN_USBBUS1, PCAN_BAUD_500K)

if result == PCAN_ERROR_OK:
    # Create message
    msg = TPCANMsg()
    msg.ID = 0x100
    msg.MSGTYPE = PCAN_MESSAGE_EXTENDED.value
    msg.LEN = 8
    msg.DATA = (c_ubyte * 8)(0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08)

    # Send message
    result = pcan.Write(PCAN_USBBUS1, msg)

    # Cleanup
    pcan.Uninitialize(PCAN_NONEBUS)
```

### Example 2: CAN-FD Message Write

```python
from PCANBasic import *

# Initialize CAN-FD channel
pcan = PCANBasic()
bitrateFD = b'f_clock=80000000,nom_brp=10,nom_tseg1=12,nom_tseg2=3,nom_sjw=3,data_brp=4,data_tseg1=7,data_tseg2=2,data_sjw=1'
result = pcan.InitializeFD(PCAN_USBBUS1, bitrateFD)

if result == PCAN_ERROR_OK:
    # Create CAN-FD message (64 bytes)
    msg = TPCANMsgFD()
    msg.ID = 0x100
    msg.MSGTYPE = PCAN_MESSAGE_EXTENDED.value | PCAN_MESSAGE_FD.value | PCAN_MESSAGE_BRS.value
    msg.DLC = 15  # 64 bytes
    msg.DATA = (c_ubyte * 64)(*[i % 256 for i in range(64)])

    # Send message
    result = pcan.WriteFD(PCAN_USBBUS1, msg)

    # Cleanup
    pcan.Uninitialize(PCAN_NONEBUS)
```

### Example 3: CAN Message Read with Timeout

```python
import time
from PCANBasic import *

pcan = PCANBasic()
pcan.Initialize(PCAN_USBBUS1, PCAN_BAUD_500K)

start_time = time.time()
timeout = 5.0  # 5 seconds

while time.time() - start_time < timeout:
    result, msg, timestamp = pcan.Read(PCAN_USBBUS1)

    if result == PCAN_ERROR_OK:
        # Process message
        print(f"ID: {hex(msg.ID)}, Data: {[hex(msg.DATA[i]) for i in range(msg.LEN)]}")
        break
    elif result == PCAN_ERROR_QRCVEMPTY:
        time.sleep(0.01)
    else:
        print(f"Error: {hex(result)}")
        break

pcan.Uninitialize(PCAN_NONEBUS)
```

### Example 4: LIN Master Write

```python
import PLinApi
from ctypes import *

# Create LIN API instance
plin = PLinApi.PLinApi()

# Register client
hClient = PLinApi.HLINCLIENT(0)
plin.RegisterClient("MyClient", None, hClient)

# Get available hardware
hwCount = c_ushort(0)
hwBuffer = (PLinApi.HLINHW * 16)()
plin.GetAvailableHardware(hwBuffer, 32, hwCount)

# Connect to first hardware
hHw = hwBuffer[0]
plin.ConnectClient(hClient, hHw)

# Initialize as Master
mode = PLinApi.TLIN_HARDWAREMODE_MASTER
baudrate = c_ushort(9600)
plin.InitializeHardware(hClient, hHw, mode, baudrate)

# Configure frame entry
frameEntry = PLinApi.TLINFrameEntry()
frameEntry.FrameId = c_ubyte(0x1A)
frameEntry.Length = c_ubyte(8)
frameEntry.Direction = PLinApi.TLIN_DIRECTION_PUBLISHER
frameEntry.ChecksumType = PLinApi.TLIN_CHECKSUMTYPE_CLASSIC
plin.SetFrameEntry(hClient, hHw, frameEntry)

# Create and send message
msg = PLinApi.TLINMsg()
msg.FrameId = c_ubyte(0x1A)
msg.Length = c_ubyte(8)
msg.Direction = PLinApi.TLIN_DIRECTION_PUBLISHER
msg.ChecksumType = PLinApi.TLIN_CHECKSUMTYPE_CLASSIC
msg.Data = (c_ubyte * 8)(0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88)

# Calculate checksum and send
plin.CalculateChecksum(msg)
plin.Write(hClient, hHw, msg)

# Cleanup
plin.DisconnectClient(hClient, hHw)
plin.RemoveClient(hClient)
```

### Example 5: LIN Slave Read

```python
import PLinApi
from ctypes import *

plin = PLinApi.PLinApi()

hClient = PLinApi.HLINCLIENT(0)
plin.RegisterClient("SlaveClient", None, hClient)

# Get and connect to hardware
hwBuffer = (PLinApi.HLINHW * 16)()
hwCount = c_ushort(0)
plin.GetAvailableHardware(hwBuffer, 32, hwCount)
hHw = hwBuffer[0]
plin.ConnectClient(hClient, hHw)

# Initialize as Slave
mode = PLinApi.TLIN_HARDWAREMODE_SLAVE
baudrate = c_ushort(9600)
plin.InitializeHardware(hClient, hHw, mode, baudrate)

# Configure subscriber frame
frameEntry = PLinApi.TLINFrameEntry()
frameEntry.FrameId = c_ubyte(0x1A)
frameEntry.Length = c_ubyte(8)
frameEntry.Direction = PLinApi.TLIN_DIRECTION_SUBSCRIBER
frameEntry.ChecksumType = PLinApi.TLIN_CHECKSUMTYPE_CLASSIC
plin.SetFrameEntry(hClient, hHw, frameEntry)

# Set filter to receive all frames
mask = c_uint64(0xFFFFFFFFFFFFFFFF)
plin.SetClientFilter(hClient, hHw, mask)

# Read messages
rcvMsg = PLinApi.TLINRcvMsg()
while True:
    result = plin.Read(hClient, rcvMsg)

    if result == PLinApi.TLIN_ERROR_OK:
        if rcvMsg.Type == PLinApi.TLIN_MSGTYPE_STANDARD:
            data = [hex(rcvMsg.Data[i]) for i in range(rcvMsg.Length)]
            print(f"ID: {hex(rcvMsg.FrameId)}, Data: {data}")
    elif result == PLinApi.TLIN_ERROR_RCVQUEUE_EMPTY:
        pass
    else:
        break

# Cleanup
plin.DisconnectClient(hClient, hHw)
plin.RemoveClient(hClient)
```

### Example 6: Using LookUpChannel

```python
from LookUpChannel import LookUpChannel

# Find PCAN-USB device with ID=5, Channel=1
lookup = LookUpChannel(
    DeviceType=b"PCAN_USB",
    DeviceID=b"5",
    ControllerNumber=b"0"
)

# Access results
device = lookup.devDevice      # 'PCAN_USB'
channel = lookup.byChannel      # 1
handleValue = lookup.handleValue  # '51'

# Use handle with PCANBasic
from PCANBasic import *
pcan = PCANBasic()
pcan.Initialize(PCAN_USBBUS1, PCAN_BAUD_500K)
```

---

## Known Limitations

1. **Platform-Specific DLLs:** Different DLLs required for Windows, Linux, and macOS
2. **Driver Installation:** PEAK-System drivers must be installed before API usage
3. **Hardware Dependencies:** Requires PEAK-System hardware adapters
4. **Channel Availability:** Channels must be available (not in use by other applications)
5. **Error Handling:** Some error conditions may require hardware reset
6. **LIN Frame Limit:** LIN supports maximum 64 frame IDs (0-63)
7. **CAN-FD DLC Mapping:** DLC to data length conversion follows specific table (not linear)

---

## Maintenance Recommendations

1. **Error Recovery:** Implement robust error handling with hardware reset capabilities
2. **Resource Cleanup:** Always call Uninitialize/RemoveClient before exit
3. **Filter Management:** Use message filters to reduce CPU load in high-traffic scenarios
4. **Thread Safety:** PCANBasic/PLinApi instances are not thread-safe
5. **Version Compatibility:** Ensure DLL version matches API wrapper version
6. **Testing:** Test with actual hardware before deployment

---

## References

- **PEAK-System Documentation:** https://www.peak-system.com/
- **PCAN-Basic API Manual:** Hardware documentation package
- **PLIN-API Manual:** LIN bus programming reference
- **CAN Specification:** ISO 11898
- **LIN Specification:** LIN Consortium

---

*Document generated: 2026-02-04*
*Source: PEAK_API (PCANBasic.py, PLinApi.py, LookUpChannel.py, PEAK.py)*
