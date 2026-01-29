# DUT 通訊模組分析

> 分析日期: 2026-01-28
> 版本: PDTool4
> 目錄: `polish/dut_comms/`

---

## 📋 目錄結構

```
dut_comms/
├── ls_comms/                 # LS 系列設備通訊 (串口)
│   ├── __init__.py
│   ├── ls_mod.py            # SafetyInterface 串口通訊實現
│   ├── ls_msgs.py           # 消息定義 (StructMessage 基類)
│   └── safety.txt           # 測試輸出示例
├── ltl_chassis_fixt_comms/   # 底盤治具通訊 (串口 + CRC16)
│   ├── __init__.py
│   ├── chassis_msgs.py      # Protocol Buffers 風格消息定義
│   ├── chassis_transport.py  # 傳輸層實現
│   ├── button_launch.py     # 按鈕啟動腳本
│   └── generate_c_include.py # C 頭文件生成工具
├── vcu_ether_comms/          # VCU 以太網通訊 (UDP + Protocol Buffers)
│   ├── __init__.py
│   ├── vcu_common.py        # UDP socket 工具
│   ├── vcu_cmds.py          # VCU 命令封裝 (489 行)
│   ├── vcu_ether_link.py    # VCUTestInterface 主類
│   ├── header.py            # 通訊消息頭定義
│   ├── vcu_req_replay.py    # 請求重放工具
│   ├── vcu_motor_command_timestamp.py
│   ├── proto/               # Protocol Buffers 消息定義 (40+ 文件, 18,247 行)
│   │   ├── __init__.py
│   │   ├── common_pb2.py
│   │   ├── test_msgs_pb2.py
│   │   ├── system_control_msgs_pb2.py
│   │   ├── battery_msgs_pb2.py
│   │   ├── traction_motor_msgs_pb2.py
│   │   ├── fault_codes_pb2.py
│   │   ├── imu_data_msgs_pb2.py
│   │   ├── gpio_test_msgs_pb2.py
│   │   ├── log_msgs_pb2.py
│   │   ├── version_info_pb2.py
│   │   ├── ... (40+ .proto / .pb2.py 文件)
│   │   └── build_vcu_proto_msgs.sh
├── semigloss_remote/          # 遠程控制工具
│   ├── __init__.py
│   └── get_semigloss_remote.sh
└── mkstruct.py               # C 結構解析器 (使用 pycparser)
```

---

## 一、核心架構概覽

**dut_comms** 提供多種設備通訊協議支持：

- ✅ **串口通訊**: LS 安全接口 + 底盤治具
- ✅ **UDP 通訊**: VCU (車輛控制單元) 以太網通訊
- ✅ **Protocol Buffers**: 結構化消息定義
- ✅ **CRC 校驗**: CRC32 (VCU) + CRC16Kermit (底盤)
- ✅ **線程安全**: SocketBuffer 線程讀緩衝區

---

## 二、各模組詳細分析

### 2.1 ls_comms/ - LS 系列設備通訊模組

#### 架構特點

**通訊方式**: 串口 (Serial Port)
**波特率**: 9600
**校驗方式**: CRC32 (zlib.crc32)

#### 核心類: SafetyInterface

**文件**: `ls_mod.py` (301 行)

**初始化**:
```python
class SafetyInterface(object):
    def __init__(self, port_name):
        self.port_name = port_name      # 例如 '/dev/ttyUSB0'
        self.port = None
```

**方法**:

| 方法 | 功能 |
|------|------|
| `open()` | 打開串口 (9600 baud) |
| `receive_packet()` | 接收並解析數據包 |
| `send_packet(msg_body_string)` | 發送數據包 |
| `close()` | 關閉串口 |
| `create_msg(command, params)` | 創建消息 |

#### 消息格式

**幀頭** (Header):
```
Offset 0-1:   Sync: 0xCA 0xFE (Little Endian: 0xFECA)
Offset 2-3:   Length: 2 bytes
Offset 4-7:   CRC: 4 bytes
Offset 8-9:   Message Format: 2 bytes
Offset 10-11:  Reserved: 2 bytes
Offset 12:     Command: 1 byte
Offset 13:     Response Indicator: 1 byte
Offset 14:     Sensor: 1 byte
Offset 15+:    Params: variable
```

**CRC 計算** (`ls_mod.py:14-19`):
```python
CRC_OFFSET = 8  # CRC covers everything below CRC in header

def get_crc(frame_header_str, complete_serialized_body_str):
    trimmed_header_str = frame_header_str[CRC_OFFSET:]  # 跳過 sync, length, crc
    header_crc_part = zlib.crc32(trimmed_header_str) & 0xFFFFFFFF
    crc = zlib.crc32(complete_serialized_body_str, header_crc_part) & 0xFFFFFFFF
    return crc
```

#### 消息定義 (`ls_msgs.py`)

**StructMessage 基類**:
```python
class StructMessage(object):
    def __init__(self):
        for name in self.fields:
            setattr(self, name, None)

    def serialize(self):
        return struct.pack(self.pack_str, *self.get_values())

    def deserialize(self, msg_blob):
        values = struct.unpack(self.pack_str, msg_blob)
        for name, value in zip(self.fields, values):
            setattr(self, name, value)
```

**消息類型**:

| 消息類 | 類型 ID | Pack String | 字段 |
|---------|---------|-------------|------|
| `MsgHeader` | - | `<HHIHH` | sync, length, crc, message_format, reserved |
| `CliffMsgBody_t` | 0 | `<BB` | command, params |
| `EncoderMsgBody_t` | 1 | `<BB` | command, params |

**命令映射**:
```python
CLIFF_MSG = 0
ENCODER_MSG = 1

command_msg_map = {
    CLIFF_MSG: CliffMsgBody_t,
    ENCODER_MSG: EncoderMsgBody_t,
}
```

#### 接收流程 (`ls_mod.py:54-185`)

**三步幀檢測**:

1. **Sync 檢測**: 獵取 `0xCA` 同步字
2. **Sync 檢測**: 確認第二字節 `0xFE`
3. **長度讀取**: 讀取消息長度
4. **數據讀取**: 根據命令類型讀取參數

**命令處理**:

| Command | Params Size | 返回值 |
|---------|-------------|---------|
| 0 (CLIFF_MSG) | 2 bytes | millivolts (電壓) |
| 1 (ENCODER_MSG) | 4 bytes | speed (編碼器速度) |

#### 使用示例 (`ls_mod.py:243-301`)

```python
safety_interface = SafetyInterface('/dev/ttyUSB0')
safety_interface.open()

# 發送懸崖傳感器請求
testPacket = safety_interface.create_msg(CLIFF_MSG, 0x01)
safety_interface.send_packet(testPacket)

# 接收響應
recv_packet, return_value = safety_interface.receive_packet()
```

---

### 2.2 ltl_chassis_fixt_comms/ - 底盤治具通訊模組

#### 架構特點

**通訊方式**: 串口 (Serial Port)
**波特率**: 9600
**校驗方式**: CRC16Kermit (PyCRC)
**同步字**: `0xA5FF00CC` (4 bytes)

#### 核心文件

| 文件 | 行數 | 功能 |
|------|------|------|
| `chassis_msgs.py` | 234 | 消息定義和序列化/反序列化 |
| `chassis_transport.py` | 159 | 傳輸層實現 |
| `button_launch.py` | 9 | 按鈕啟動腳本 |
| `generate_c_include.py` | 117 | C 頭文件生成器 |

#### 消息定義 (`chassis_msgs.py`)

**自動註冊機制** (`chassis_msgs.py:179-203`):
```python
# 掃描模組並自動註冊所有消息類
for name in dir(module):
    obj = getattr(module, name)
    if hasattr(obj, 'msg_type') and hasattr(obj, 'fields'):
        msg = obj
        module.type_msg_map[msg.msg_type] = msg
        module.msg_packing_format_map[msg] = build_msg_packing_format(msg)
        msg.field_enum_map = build_enum_map(msg)
```

**消息類**:

| 消息類 | 類型 ID | 字段 |
|---------|---------|------|
| `TransportHeader` | -10 | sync_word, length, msg_type |
| `TransportFooter` | -9 | crc16 |
| `ActuateCliffSensorDoor` | 0x10 | door_number, close_open |
| `ActuateCliffSensorDoorStatus` | 0x11 | status |
| `ReadEncoderCount` | 0x12 | left_right |
| `EncoderCount` | 0x13 | status, count |
| `WaitForTurntable` | 0x14 | timeout_seconds |
| `WaitForTurntableStatus` | 0x15 | status |
| `RotateTurntable` | 0x16 | operation, angle |
| `RotateTurntableStatus` | 0x17 | status |
| `GetTurntableAngle` | 0x1A | (無字段) |
| `TurntableAngleRsp` | 0x1B | angle |

**枚舉類**:

```python
class close_open_enum(Enum):
    CLOSE = 0
    OPEN = 1

class left_right_enum(Enum):
    LEFT = 0
    RIGHT = 1

class status_enum(Enum):
    SUCCESS = 0
    GENERAL_FAILURE = 1
    TIMEOUT_EXPIRED = 2

class operation_enum(Enum):
    ROTATE_TO_OPTO_SWITCH = 0
    ROTATE_LEFT = 1
    ROTATE_RIGHT = 2
```

#### 序列化/反序列化 (`chassis_msgs.py:136-144`)

```python
def serialize(msg_inst):
    return struct.pack(msg_packing_format_map[type(msg_inst)], *get_values(msg_inst))

def deserialize(msg_class, msg_blob):
    msg = msg_class()
    values = struct.unpack(msg_packing_format_map[msg_class], msg_blob)
    for name, value in zip(msg_class.fields, values):
        setattr(msg, name, value)
    return msg
```

#### 傳輸層 (`chassis_transport.py`)

**串口配置** (`chassis_transport.py:22-36`):
```python
BAUD_RATE = 9600
PARITY = serial.PARITY_NONE
FRAME_PAYLOAD_SIZE = serial.EIGHTBITS
STOP_BITS = serial.STOPBITS_ONE
TIMEOUT = 1
```

**發送消息** (`chassis_transport.py:38-56`):
```python
def send_msg(transport_fd, msg_inst):
    buff = io.StringIO()

    # 創建傳輸頭
    new_header = TransportHeader()
    new_header.sync_word = SYNC_WORD          # 0xA5FF00CC
    new_header.msg_type = msg_inst.msg_type
    new_header.length = get_msg_size(msg_inst) + TRANSPORT_OVERHEAD
    buff.write(serialize(new_header))

    # 寫入消息體
    buff.write(serialize(msg_inst))

    # 計算 CRC16Kermit
    crc16 = CRC16Kermit()
    crc = crc16.calculate(buff.getvalue())

    # 創建傳輸尾
    new_footer = TransportFooter()
    new_footer.crc16 = crc
    buff.write(serialize(new_footer))

    # 發送完整幀
    msg_str = buff.getvalue()
    transport_fd.write(msg_str)
```

**接收消息** (`chassis_transport.py:58-78`):
```python
def get_msg(transport_fd):
    frame_detector = deque('\xff' * HEADER_SIZE, maxlen=HEADER_SIZE)

    while True:
        input_byte = transport_fd.read(1)
        frame_detector.append(input_byte)
        header = deserialize(TransportHeader, ''.join(frame_detector))

        # Sync 檢測
        if header.sync_word == SYNC_WORD:
            break

    # 讀取消息體
    body = transport_fd.read(header.length - TRANSPORT_OVERHEAD)
    footer = transport_fd.read(FOOTER_SIZE)
    footer = deserialize(TransportFooter, footer)

    # 反序列化消息
    msg = deserialize(type_msg_map[header.msg_type], body)
    return header, msg, footer
```

#### C 頭文件生成 (`generate_c_include.py`)

**功能**: 從 Python 消息定義生成 C 語言頭文件

**生成的格式**:
```c
#include <stdint.h>
#pragma pack(1)

#define SYNC_WORD 0xa5ff00cc
#define TRANSPORT_OVERHEAD 8

enum MSGS_TYPES {
    MSGS_TYPE_ActuateCliffSensorDoor = 0x10,
    MSGS_TYPE_ActuateCliffSensorDoorStatus = 0x11,
    ...
};

enum MSGS_close_open {
    MSGS_CLOSE = 0,
    MSGS_OPEN = 1,
};

typedef struct MSGS_ActuateCliffSensorDoor_ {
    uint8_t door_number;
    uint8_t close_open;
} MSGS_ActuateCliffSensorDoor;
```

#### 按鈕啟動 (`button_launch.py`)

```python
import os, time
import serial
ser = serial.Serial('/dev/ttyUSB0')

while True:
    while not ser.getCTS():  # 等待按鈕按下 (CTS 信號)
        time.sleep(.0001)
    os.system('python chassis_transport.py /dev/ttyACM0')
```

---

### 2.3 vcu_ether_comms/ - VCU 以太網通訊模組

#### 架構特點

**通訊方式**: UDP (User Datagram Protocol)
**IP 地址**: `192.168.3.100` (可配置)
**端口**:
- 測試端口: 8156
- 連接端口: 8124
- 重放端口: 8253

**校驗方式**: CRC32 (zlib.crc32)
**消息格式**: Protocol Buffers (protobuf)
**頭同步**: `0xCAFE` (16-bit)

#### 核心文件

| 文件 | 行數 | 功能 |
|------|------|------|
| `vcu_ether_link.py` | 277 | VcuTestInterface 主類 |
| `vcu_cmds.py` | 489 | VCU 命令封裝函數 |
| `vcu_common.py` | 17 | UDP socket 工具 |
| `header.py` | 50 | CommMsgHeader_t 消息頭定義 |
| `vcu_req_replay.py` | 28 | 請求重放工具 |
| `proto/*.pb2.py` | 18,247 | Protocol Buffers 消息定義 |

#### Protocol Buffers 消息體系

**消息分類** (`proto/`):

| 分類 | 消息文件 | 主要內容 |
|------|----------|----------|
| 通用 | `common_pb2.py` | TimeStamp |
| 系統控制 | `system_control_msgs_pb2.py` | Reset, Power 等控制 |
| 電池 | `battery_msgs_pb2.py` | BatteryStatus, BatteryInfo |
| 牽引電機 | `traction_motor_msgs_pb2.py` | 電機速度、電流控制 |
| 故障代碼 | `fault_codes_pb2.py` | 錯誤代碼定義 |
| IMU 數據 | `imu_data_msgs_pb2.py` | 慣性測量單元數據 |
| GPIO | `gpio_test_msgs_pb2.py`, `gpio_init_v2_pb2.py` | GPIO 測試和初始化 |
| 日誌 | `log_msgs_pb2.py` | 日誌消息 |
| 版本信息 | `version_info_pb2.py` | 固件版本信息 |
| 測試消息 | `test_msgs_pb2.py` | TestCommandReq, TestCommandRsp (301 行) |
| 播放器 | `pager_msgs_pb2.py` | 分頁消息 |
| 清潔 | `scrubber_state_msgs_pb2.py`, `sweeper_msgs_pb2.py` | 清潔狀態和掃地機控制 |
| 吸塵 | `vacuum_msgs_pb2.py` | 吸塵機控制 |
| 門控 | `cliff_msgs_pb2.py` | 懸崖傳感器門控 |
| LED | `led_messages.proto` | LED 控制 |
| EEPROM | `eeprom_msgs_pb2.py` | EEPROM 讀寫 |
| 其他 | ... | 更多消息類型 |

#### 消息頭定義 (`header.py`)

**CommMsgHeader_t** (`header.py:41-49`):
```python
class CommMsgHeader_t(StructMessage):
    fields = OrderedDict((
        ("sync", ctypes.c_uint16),         # 0xCAFE
        ("length", ctypes.c_uint16),       # 消息體長度
        ("crc", ctypes.c_uint32),         # CRC32
        ("message_format", ctypes.c_uint16), # 1 = BareNanoPB
        ("reserved", ctypes.c_uint16),
    ))
    pack_str = "<HHIHH"
```

**常量** (`header.py:31-39`):
```python
MAGIC_SYNC_U16 = 0xCAFE
MESSAGE_FORMAT_BARE_NANO_PB = 1
MESSAGE_FORMAT_C_STRUCT = 3
MAX_MESSAGE_BODY_LENGTH = 1000

COMM_MSG_OK = 1
COMM_MSG_GENERAL_ERROR = 2
COMM_MSG_EEPROM_DATA_CRC_FAILED = 3
COMM_MSG_EEPROM_READ_FAILED = 4
```

#### CRC 計算 (`vcu_ether_link.py:90-94`)

```python
CRC_OFFSET = 8  # CRC covers everything below CRC in header

def get_crc(frame_header_str, complete_serialized_body_str):
    trimmed_header_str = frame_header_str[CRC_OFFSET:]
    header_crc_part = zlib.crc32(trimmed_header_str) & 0xFFFFFFFF
    crc = zlib.crc32(complete_serialized_body_str, header_crc_part) & 0xFFFFFFFF
    return crc
```

#### SocketBuffer 線程讀緩衝區 (`vcu_ether_link.py:41-78`)

**目的**: 線程安全的 UDP socket 讀取緩衝區

```python
class SocketBuffer(object):
    def __init__(self, sock):
        self._buff = list()
        self._sock = sock
        self._lock = threading.RLock()

    def fill(self, size):
        '''消耗 size 字節並添加到 _buff'''
        with self._lock:
            buff_len = len(self._buff)
            remaining_read = size - buff_len
            if remaining_read > 0:
                self._buff.extend(self._sock.recv(4096))

    def peek(self, size):
        '''非破壞性返回 _buff 前 size 字節的副本'''
        with self._lock:
            buff_len = len(self._buff)
            if buff_len < size:
                self.fill(size - buff_len)
            return ''.join(self._buff[:size])

    def read(self, size):
        '''從 _buff 消耗 size 字節'''
        read_str = self.peek(size)
        del self._buff[:size]
        return read_str
```

#### 三重幀檢測 (`vcu_ether_link.py:109-139`)

**recv_frame()** 實現三層檢測:

```python
def recv_frame(sock, timeout=3):
    sock_buffer = SocketBuffer(sock)
    frame_detector = deque('\xff' * HEADER_SIZE, maxlen=HEADER_SIZE)
    frame_header = header.CommMsgHeader_t()

    while True:
        input_byte = sock_buffer.read(1)
        frame_detector.append(input_byte)
        frame_header_str = ''.join(frame_detector)
        frame_header.deserialize(frame_header_str)

        # 1. Sync based framing
        if frame_header.sync == header.MAGIC_SYNC_U16:
            # 2. Length based framing
            if frame_header.length <= header.MAX_MESSAGE_BODY_LENGTH and \
               not frame_header.length == 0:
                # Peek ahead rest of frame
                msg_body_candidate_str = sock_buffer.peek(frame_header.length)

                # 3. CRC based framing
                recv_crc = get_crc(frame_header_str, msg_body_candidate_str)
                if recv_crc == frame_header.crc:
                    sock_buffer.read(frame_header.length)
                    return frame_header, frame_header_str, msg_body_candidate_str
```

#### VcuTestInterface 類 (`vcu_ether_link.py:171-266`)

**初始化**:
```python
class VcuTestInterface(object):
    def __init__(self):
        self.test_sock = None
        self.connect_sock = None
        self.verbose = True
        self.start_time = time.time()
```

**連接流程** (`vcu_ether_link.py:200-236`):
```python
def init_interface(self):
    # 1. 連接握手
    if not self.connect():
        raise VcuConnectFailed()

    # 2. 初始化測試 socket
    self.test_sock = get_udp_sock()
    self.test_sock.settimeout(.1)

    # 3. 發送初始測試請求
    req = self.get_new_msg()
    req.get_fw_version_req.dummy_field = 1
    return self.poll(req)
```

**connect()** (`vcu_ether_link.py:200-219`):
```python
def connect(self, connect_retries=15):
    self.connect_sock = get_udp_sock()
    self.connect_sock.settimeout(.1)

    for i in xrange(connect_retries):
        flush_udp_recv(self.connect_sock)
        connect_msg = 'connect'
        self.connect_sock.sendto(connect_msg, CONNECT_ENDPOINT)

        try:
            connect_rsp = self.connect_sock.recv(len(connect_msg))
            if self.verbose:
                print connect_msg, connect_rsp
        except socket.timeout:
            continue

        if connect_msg == connect_rsp:
            return True
        time.sleep(.1)
    return False
```

**poll()** (`vcu_ether_link.py:238-266`):
```python
def poll(self, request, request_type=header.MESSAGE_FORMAT_BARE_NANO_PB):
    assert request_type == header.MESSAGE_FORMAT_BARE_NANO_PB
    return self._protobuf_poll(request)

def _protobuf_poll(self, request):
    # 設置時間戳
    if request.WhichOneof('comm_msg') == 'test_command_req':
        request.test_command_req.timestamp = int((time.time() - self.start_time) * 1000)

    if self.verbose:
        print 'Protobuf Request="%s"' % request

    # 序列化並發送
    request_str = request.SerializeToString()
    send_msg_body(self.test_sock, TEST_ENDPOINT, request_str)

    # 接收響應
    resp_header, resp_header_str, response_str = recv_frame(self.test_sock)
    response = comm_messages_pb2.CommMsgBody()
    response.ParseFromString(response_str)

    if self.verbose:
        print 'Protobuf Response="%s"' % response
    return response
```

#### VCU 命令封裝 (`vcu_cmds.py`)

**主要功能分類**:

1. **牽引電機控制**
   - `drive_motor(intf, channel, speed, motor_command_timestamp)`
   - `MotorDriveThread` - 線程化電機控制
   - `cmd_loop()` - 循環命令執行

2. **吸塵機控制**
   - `vacuum_on(intf)`
   - `vacuum_off(intf)`
   - `vacuum_speed(intf, speed)`

3. **掃地機控制**
   - `sweeper_on(intf, speed=1500)`
   - `sweeper_off(intf)`
   - `actuator_extend()`, `actuator_retract()`, `actuator_stop()`

4. **傳感器讀取**
   - `read_cliff_sensors(intf)`
   - `read_bumper_sensors(intf)`
   - `read_bumper_side_sensors(intf)`
   - `read_wheel_lift_sensors(intf)`

5. **EEPROM 操作**
   - `eeprom_vcu_info_read(intf)`
   - `eeprom_vcu_info_write(intf, ...)`
   - `eeprom_chassis_info_read/write(...)`
   - `eeprom_eol_info_read/write(...)`

6. **電源控制**
   - `lidar_power_on/off(intf)`
   - `lbcm_power_on/off(intf)`

7. **蜂鳴器控制**
   - `beeper_on_blindspot(intf)`
   - `beeper_disable(intf)`
   - `beeper_read_status(intf)`

8. **LED 控制**
   - `led_set_state(intf, state)` - 強制 GPIO 高/低
   - `led_normal(intf)` - 返回 SPI 模式

9. **其他**
   - `get_bag_status(intf)`
   - `get_blue_button_status(intf)`
   - `read_lift_handle_sensor(intf)`

#### MotorDriveThread 線程類 (`vcu_cmds.py:373-437`)

**目的**: 單獨線程控制電機，50ms 定時

```python
class MotorDriveThread(threading.Thread):
    thr_inst = None
    thr_inst_lock = threading.RLock()

    def __init__(self, intf, channel, speed,
                 update_rate=0.050,
                 at_speed_window=0.02,
                 at_speed_boxcar_avg_size=8):
        threading.Thread.__init__(self)
        self.thr_inst_lock.acquire()  # 阻止其他實例

        self.setDaemon(True)
        self.intf = intf
        self.channel = channel
        self.speed = speed
        self.update_rate = update_rate
        self.at_speed_boxcar_avg = collections.deque([0xFFFF] * at_speed_boxcar_avg_size,
                                                 maxlen=at_speed_boxcar_avg_size)
        self.at_speed_event = threading.Event()  # 電機達到目標速度事件
        self.done = threading.Event()           # 退出事件

    def run(self):
        try:
            while not self.done.is_set():
                test_state, motor_command_timestamp = drive_motor(
                    self.intf, self.channel, self.speed, motor_command_timestamp)

                # 讀取速度
                if self.channel == LEFT:
                    readback_speed = test_state.traction_left_speed_mps
                else:
                    readback_speed = test_state.traction_right_speed_mps

                # 計算移動平均
                self.at_speed_boxcar_avg.append(readback_speed)
                avg = sum(self.at_speed_boxcar_avg) / float(len(self.at_speed_boxcar_avg))

                # 檢查是否達到目標速度
                if self.speed < 0:
                    if abs(self.speed) - avg < self.at_speed_window:
                        self.at_speed_event.set()
                else:
                    if self.speed - avg < self.at_speed_window:
                        self.at_speed_event.set()

                sleep_until_timestamp(time.time() + self.update_rate)
        finally:
            self.at_speed_event.set()

    def teardown(self):
        self.thr_inst_lock.release()
```

#### 測試消息示例 (`test_msgs.proto`)

**TestCommandReq** (請求):
```protobuf
message TestCommandReq {
    uint32 timestamp = 1;                         // 主機與 VCU 時間同步
    float drive_command1 = 2;                   // 差速驅動命令 1
    float drive_command2 = 3;                   // 差速驅動命令 2
    uint32 actuator_command = 4;            // 執行器命令
    uint32 uart_command = 5;
    uint32 ethernet_command = 6;
    uint32 motor_command_timestamp = 7;     // 電機命令時間戳和 CRC
    uint32 state_flags = 8;
    uint32 imu_flags = 9;
    uint32 testing_cmd = 10;
    uint32 cliff_id = 11;
    float cliff_threshold = 12;
    int32 vac = 13;                       // -1 忽略, 0 禁用, 1 正常, 2 渦輪
    int32 beep_type = 14;                   // -1 忽略, 0 禁用, 1 盲點蜂鳴
    int32 sweeper_command = 15;
    float pwm_left = 16;      // 0.2-0.8 範圍, 0 全後退, 1 全前進
    float pwm_right = 17;
    bool test_f3_comms = 18;
}
```

**TestCommandRsp** (響應):
```protobuf
message TestCommandRsp {
    uint32 response_code = 1;
    uint32 timestamp_us = 2;                 // 測量時間戳 (us), 2^32-1 循環
    uint32 cpu_board_rev = 3;               // CPU 板版本號
    uint32 machine_id = 4;                   // 機器 ID
    uint32 mcu_status = 5;                  // 微控制器狀態
    uint32 estop_code = 6;                  // E-Stop 錯誤代碼
    // ... 更多字段

    // IMU 數據
    uint32 imu_used = 10;
    repeated int32 imu_gyro = 11;
    repeated float imu_gyro_rads_avg = 12;
    repeated int32 imu_acc = 13;
    repeated float imu_acc_Gs_avg = 14;
    float heading_angle = 16;
    float angular_velocity = 17;
    uint32 imu_temp = 18;

    // 差速驅動
    int32 traction_left_distance_mm = 20;
    int32 traction_right_distance_mm = 21;
    float traction_left_command = 22;
    float traction_right_command = 23;
    int32 traction_left_raw_throttle = 24;
    int32 traction_right_raw_throttle = 25;
    float traction_left_speed_mps = 26;     // 過濾後速度
    float traction_right_speed_mps = 27;
    float traction_right_current_ma = 28;
    float traction_left_current_ma = 29;

    // 傳感器
    repeated bool cliff_state = 32;
    repeated float cliff_voltage = 33;
    int32 beeper_status = 34;
    int32 vac = 35;
    bool front_bumper_1 = 36;
    bool front_bumper_2 = 37;
    bool lift_handle_extended = 38;
    uint32 actuator_current_ma = 39;

    F3CommsResult_t f3_comms_test_result = 40;
}
```

#### UDP Socket 工具 (`vcu_common.py`)

```python
import socket

def get_udp_sock():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return sock

def flush_udp_recv(sock, byte_size_to_flush=2**16):
    '''清除 socket 接收緩衝區'''
    timeout = sock.gettimeout()
    try:
        sock.settimeout(.0001)
        try:
            trash = sock.recv(byte_size_to_flush)
        except socket.timeout:
            pass
    finally:
        sock.settimeout(timeout)
```

#### 請求重放 (`vcu_req_replay.py`)

**用途**: 預定義的請求包重放

```python
REPLAY = '''
4500 0035 704b 4000 4011 42b7 c0a8 0301 c0a8 0364
b1d1 203d 0021 87e8 9596 bc12 6601 0000 9e66 6400
0125 0918 0021 5714 0000 00b5 22
'''

def get_replay():
    replay = REPLAY.strip().replace(' ', '')
    replay_str = ''.join((chr(int(replay[i:i+2], 16))
                       for i in range(0, 48, 2)))
    return replay_str

def do_replay():
    replay_str = get_replay()
    req_replay_sock = vcu_common.get_udp_sock()
    return req_replay_sock.sendto(replay_str, REQ_REPLAY_ENDPOINT)
```

---

### 2.4 semigloss_remote/ - 遠程控制工具

#### get_semigloss_remote.sh

**用途**: 從 GitHub 拉取 semigloss 遠程控制模組

```bash
#!/bin/bash -e
rm -rf semigloss
rm -rf remote
git clone --depth 1 --branch $1 git@github.com:braincorp/semigloss.git

cp -R semigloss/remote .
rm -rf semigloss

touch remote/src/__init__.py
touch remote/__init__.py
```

**參數**: `$1` - Git 分支名

---

### 2.5 mkstruct.py - C 結構解析器

#### 架構

**文件**: `mkstruct.py` (171 行)
**依賴**: pycparser, ctypes

#### 功能

從 C 頭文件生成 Python 消息類

**流程**:
```
C 頭文件 (.h)
    ↓
pycparser 解析
    ↓
提取 struct 和 enum
    ↓
生成 Python 類
    ↓
輸出到 stdout
```

#### 核心函數

**gen_defines()** (`mkstruct.py:68-87`):
```python
def gen_defines(src):
    defines = list()
    for line in src.splitlines():
        line = line.strip()
        if '#define' in line:
            tokens = line.split(' ')
            try:
                while True:
                    tokens.remove('')
            except ValueError:
                pass
            assert tokens[0] == '#define', tokens
            if len(tokens) == 3:
                defines.append('%s = %s' % (tokens[1], tokens[2]))
            elif len(tokens) == 2:
                defines.append('%s = None' % (tokens[1]))
            else:
                raise UndefinedCDefineBehavior(line)
    return defines
```

**get_struct_class()** (`mkstruct.py:97-123`):
```python
def get_struct_class(ast_typedef_struct, byte_order=BYTE_ORDER):
    pack_str = byte_order.pack_str
    fields = []

    for field in ast_typedef_struct.type.type.decls:
        f_name = field.name
        id_type = field.type.type
        type_name = id_type.names[0]
        c_struct_type_name, c_struct_type = get_c_type(type_name)
        fields.append((f_name, c_struct_type_name, c_struct_type))

    name_of_struct = ast_typedef_struct.name
    class_str = class_header.format(name_of_struct=name_of_struct)

    for f_name, c_struct_type_name, c_struct_type in fields:
        newline = ' ' * 8
        newline += '("%s", ctypes.%s),' % (f_name, c_struct_type_name)
        class_str += newline + '\n'
        pack_str += c_struct_type._type_

    class_str += class_footer.format(pack_str=pack_str)
    return class_str
```

**get_enums_and_struct_classes()** (`mkstruct.py:127-154`):
```python
def get_enums_and_struct_classes(srcfilename):
    ast = pycparser.parse_file(srcfilename, use_cpp=True)

    enums = []
    structs = []

    for synt_ele in ast:
        # 查找 struct
        if type(synt_ele) is pycparser.c_ast.Typedef:
            if type(synt_ele.type) is pycparser.c_ast.TypeDecl:
                if type(synt_ele.type.type) is pycparser.c_ast.Struct:
                    structs.append(get_struct_class(synt_ele))

        # 查找 enum
        elif type(synt_ele) is pycparser.c_ast.Decl:
            if type(synt_ele.type) is pycparser.c_ast.Enum:
                enum_list = synt_ele.type.values.enumerators
                i_offset = 0
                for i, e in enumerate(enum_list):
                    if e.value is not None:
                        i_offset = int(e.value.value)
                    enums.append('%s = %s' % (e.name, i + i_offset))

    return enums, structs
```

**輸出模板** (`mkstruct.py:21-59`):
```python
class_header = '''
class {name_of_struct}(StructMessage):
    fields = OrderedDict((
'''

class_footer = '''    ))
    pack_str = "{pack_str}"
'''

module_header = '''
import ctypes
import struct
from collections import OrderedDict

class StructMessage(object):
    def __init__(self):
        for name in self.fields:
            setattr(self, name, None)

    def get_msg_size(self):
        return struct.calcsize(self.pack_str)

    def get_values(self):
        values = []
        for name in self.fields:
            values.append(getattr(self, name))
        return values

    def serialize(self):
        return struct.pack(self.pack_str, *self.get_values())

    def deserialize(self, msg_blob):
        values = struct.unpack(self.pack_str, msg_blob)
        for name, value in zip(self.fields, values):
            setattr(self, name, value)
'''
```

**使用示例**:
```bash
python mkstruct.py my_messages.h > my_messages.py
```

---

## 三、通訊協議比較

### 3.1 ls_comms vs ltl_chassis_fixt_comms

| 特性 | ls_comms | ltl_chassis_fixt_comms |
|------|-----------|-----------------------|
| 物理層 | 串口 | 串口 |
| 波特率 | 9600 | 9600 |
| 同步字 | 0xCAFE (2 bytes) | 0xA5FF00CC (4 bytes) |
| 校驗 | CRC32 | CRC16Kermit |
| 消息定義 | StructMessage | StructMessage (自動註冊) |
| 序列化 | struct.pack/unpack | struct.pack/unpack |
| 支持的命令 | 懸崖傳感器, 編碼器 | 轉盤, 編碼器, 懸崖門控 |

### 3.2 vcu_ether_comms 協議

| 層次 | 技術 | 說明 |
|------|------|------|
| 物理層 | Ethernet UDP | UDP 套接字 |
| 連接層 | Connect 握手 | 'connect' 字符串回顯 |
| 傳輸層 | 三重幀檢測 | Sync + Length + CRC |
| 數據鏈路層 | CommMsgHeader_t | 0xCAFE + CRC32 + 長度 |
| 應用層 | Protocol Buffers | google.protobuf |

### 3.3 CRC 計算比較

```python
# ls_comms + vcu_ether_comms
CRC_OFFSET = 8
def get_crc(header_str, body_str):
    trimmed = header_str[CRC_OFFSET:]
    header_crc = zlib.crc32(trimmed) & 0xFFFFFFFF
    crc = zlib.crc32(body_str, header_crc) & 0xFFFFFFFF
    return crc

# ltl_chassis_fixt_comms
crc16 = CRC16Kermit()
crc = crc16.calculate(header + body)
```

---

## 四、關鍵設計模式

### 4.1 模板方法模式 (Template Method)

**應用**: `StructMessage` 基類

```python
class StructMessage(object):
    def serialize(self):
        return struct.pack(self.pack_str, *self.get_values())

    def deserialize(self, msg_blob):
        values = struct.unpack(self.pack_str, msg_blob)
        for name, value in zip(self.fields, values):
            setattr(self, name, value)
```

### 4.2 工廠模式 (Factory)

**應用**: `command_msg_map` (ls_comms)

```python
command_msg_map = {
    CLIFF_MSG: CliffMsgBody_t,
    ENCODER_MSG: EncoderMsgBody_t,
}

def create_msg(command, params):
    msg_type = command_msg_map[command]
    body = msg_type()
    body.command = command
    body.params = params
    return body
```

**應用**: `type_msg_map` (ltl_chassis_fixt_comms)

```python
# 自動註冊所有消息
for name in dir(module):
    obj = getattr(module, name)
    if hasattr(obj, 'msg_type') and hasattr(obj, 'fields'):
        module.type_msg_map[obj.msg_type] = obj
```

### 4.3 觀察者模式 (Observer)

**應用**: `MotorDriveThread` 事件機制

```python
self.at_speed_event = threading.Event()  # 電機達到目標速度事件
self.done = threading.Event()           # 退出事件

# 等待電機達到目標速度
motor_thr.at_speed_event.wait(20)
```

### 4.4 適配器模式 (Adapter)

**應用**: `SocketBuffer` 適配 UDP socket

```python
class SocketBuffer(object):
    def __init__(self, sock):
        self._buff = list()
        self._sock = sock
        self._lock = threading.RLock()

    def read(self, size):
        read_str = self.peek(size)
        del self._buff[:size]
        return read_str
```

### 4.5 策略模式 (Strategy)

**應用**: 不同的 CRC 計算策略

```python
# ls_comms + vcu_ether_comms
crc = zlib.crc32(body_str, header_crc) & 0xFFFFFFFF

# ltl_chassis_fixt_comms
crc = CRC16Kermit().calculate(header + body)
```

### 4.6 線程安全模式 (Thread-Safe)

**應用**: `SocketBuffer` + `MotorDriveThread`

```python
# SocketBuffer
self._lock = threading.RLock()

with self._lock:
    self._buff.extend(self._sock.recv(4096))

# MotorDriveThread
self.thr_inst_lock = threading.RLock()

def __init__(self, ...):
    self.thr_inst_lock.acquire()  # 阻止其他實例
```

---

## 五、技術棧

### 通訊協議

| 協議 | 庫 | 用途 |
|------|-----|------|
| Serial | pyserial | 串口通訊 |
| UDP | socket | 以太網通訊 |
| Protocol Buffers | google.protobuf | 消息序列化 |

### 校驗

| 算法 | 庫 | 用途 |
|------|-----|------|
| CRC32 | zlib | ls_comms, vcu_ether_comms |
| CRC16Kermit | PyCRC | ltl_chassis_fixt_comms |

### 二進制處理

| 操作 | 庫 | 用途 |
|------|-----|------|
| struct.pack/unpack | struct | 二進制打包/解包 |
| ctypes | ctypes | C 類型定義 |
| OrderedDict | collections | 字段順序保持 |

### 並發

| 工具 | 用途 |
|------|------|
| threading.Thread | MotorDriveThread |
| threading.RLock | 線程安全鎖 |
| threading.Event | 線程同步事件 |
| deque | 線程安全隊列 |

### 代碼生成

| 工具 | 用途 |
|------|------|
| pycparser | C 頭文件解析 (mkstruct.py) |
| protoc | Protocol Buffers 編譯器 |
| build_vcu_proto_msgs.sh | Proto 編譯腳本 |

---

## 六、執行流程分析

### 6.1 ls_comms 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 初始化                                              │
├─────────────────────────────────────────────────────────────┤
│   SafetyInterface('/dev/ttyUSB0')                         │
│         ↓                                               │
│   open()                                               │
│     serial.Serial(port_name, 9600)                      │
│         ↓                                               │
│   端口已打開                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 創建消息                                           │
├─────────────────────────────────────────────────────────────┤
│   create_msg(command, params)                             │
│         ↓                                               │
│   body = command_msg_map[command]()                       │
│   body.command = command                                 │
│   body.params = params                                    │
│         ↓                                               │
│   msg_body_string = body.serialize()                      │
│   header_string = create_header(msg_body_string)            │
│         ↓                                               │
│   msg = header_string + msg_body_string                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 發送消息                                           │
├─────────────────────────────────────────────────────────────┤
│   send_packet(msg)                                      │
│     port.write(msg)                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 接收響應                                           │
├─────────────────────────────────────────────────────────────┤
│   receive_packet()                                       │
│         ↓                                               │
│   獵取 Sync 0xCA                                       │
│         ↓                                               │
│   確認 Sync 0xFE                                       │
│         ↓                                               │
│   讀取 Length                                           │
│         ↓                                               │
│   讀取 CRC                                             │
│         ↓                                               │
│   讀取 Message Format                                    │
│         ↓                                               │
│   讀取 Command                                          │
│         ↓                                               │
│   根據 Command 讀取 Params                                │
│         ↓                                               │
│   解析並返回 (recv_packet, return_value)                  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 vcu_ether_comms 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 初始化                                              │
├─────────────────────────────────────────────────────────────┤
│   VcuTestInterface()                                     │
│         ↓                                               │
│   start_time = time.time()                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 連接握手                                              │
├─────────────────────────────────────────────────────────────┤
│   init_interface()                                       │
│         ↓                                               │
│   connect()                                            │
│     發送 'connect' 到 (192.168.3.100, 8124)            │
│     等待回顯 'connect'                                 │
│     重試最多 15 次                                      │
│         ↓                                               │
│   創建 test_sock (UDP, 8156)                           │
│         ↓                                               │
│   發送初始測試請求                                       │
│     get_fw_version_req.dummy_field = 1                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 構建請求                                            │
├─────────────────────────────────────────────────────────────┤
│   get_new_msg() 或 get_new_test_msg()                    │
│         ↓                                               │
│   CommMsgBody()                                        │
│   req.Clear()                                          │
│   設置請求字段                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 發送請求                                            │
├─────────────────────────────────────────────────────────────┤
│   poll(req)                                            │
│         ↓                                               │
│   設置時間戳                                            │
│     req.test_command_req.timestamp =                      │
│       int((time.time() - start_time) * 1000)             │
│         ↓                                               │
│   序列化                                               │
│     request_str = request.SerializeToString()                │
│         ↓                                               │
│   創建幀頭                                              │
│     header.sync = 0xCAFE                                │
│     header.length = len(request_str)                        │
│     header.crc = get_crc(header, request_str)             │
│         ↓                                               │
│   發送 UDP                                             │
│     sock.sendto(header + request, TEST_ENDPOINT)            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. 接收響應 (三重幀檢測)                                │
├─────────────────────────────────────────────────────────────┤
│   recv_frame(sock)                                      │
│         ↓                                               │
│   SocketBuffer 讀取                                      │
│     while True:                                         │
│       input_byte = sock.read(1)                          │
│       frame_detector.append(input_byte)                     │
│       frame_header.deserialize(detector)                    │
│         ↓                                               │
│       1. Sync 檢測                                     │
│         if frame_header.sync == 0xCAFE:                   │
│             ↓                                           │
│           2. Length 檢測                                   │
│           if length <= MAX_LENGTH and length > 0:          │
│               ↓                                       │
│             3. CRC 檢測                                    │
│             recv_crc = get_crc(header, body)               │
│             if recv_crc == header.crc:                     │
│                 return header, body                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. 解析響應                                            │
├─────────────────────────────────────────────────────────────┤
│   response = CommMsgBody()                               │
│   response.ParseFromString(response_str)                    │
│         ↓                                               │
│   return response                                        │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 MotorDriveThread 執行流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 初始化                                              │
├─────────────────────────────────────────────────────────────┤
│   MotorDriveThread(intf, channel, speed)                 │
│         ↓                                               │
│   thr_inst_lock.acquire()  # 阻止其他實例                │
│   setDaemon(True)                                       │
│   初始化 boxcar_avg [0xFFFF * 8]                          │
│   初始化 at_speed_event, done 事件                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 啟動線程                                            │
├─────────────────────────────────────────────────────────────┤
│   start()                                               │
│         ↓                                               │
│   run()                                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 運行循環                                            │
├─────────────────────────────────────────────────────────────┤
│   while not done.is_set():                               │
│         ↓                                               │
│     drive_motor(intf, channel, speed, timestamp)         │
│       發送電機命令                                        │
│       接收電機響應                                        │
│         ↓                                               │
│     讀取速度                                              │
│       if channel == LEFT:                                 │
│         readback_speed = response.traction_left_speed_mps     │
│       else:                                              │
│         readback_speed = response.traction_right_speed_mps    │
│         ↓                                               │
│     更新移動平均                                          │
│       boxcar_avg.append(readback_speed)                    │
│       avg = sum(boxcar_avg) / len(boxcar_avg)            │
│         ↓                                               │
│     檢查是否達到目標速度                                    │
│       if abs(speed) - avg < at_speed_window:              │
│         at_speed_event.set()                              │
│         ↓                                               │
│     sleep_until_timestamp(tick + update_rate)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 退出清理                                              │
├─────────────────────────────────────────────────────────────┤
│   done.is_set() = True                                  │
│         ↓                                               │
│   電機速度設為 0.5                                        │
│   at_speed_event.set()                                   │
│   teardown()                                            │
│     thr_inst_lock.release()                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 七、擴展點

### 7.1 新增串口通訊協議

在 `dut_comms/` 下創建新子目錄:

```
dut_comms/
└── my_protocol/
    ├── __init__.py
    ├── my_protocol_mod.py
    └── my_protocol_msgs.py
```

**步驟**:
1. 繼承 `StructMessage` 基類
2. 定義消息字段和 pack_str
3. 實現串口發送/接收
4. 實現 CRC 校驗

### 7.2 新增 VCU 命令

在 `vcu_cmds.py` 中添加新函數:

```python
def my_new_command(intf, param1, param2):
    req = intf.get_new_msg()
    req.my_new_req.param1 = param1
    req.my_new_req.param2 = param2
    rsp = intf.poll(req)
    if rsp.my_new_rsp.response_code != RESP_GOOD:
        raise VcuCommResponseCodeFailure(str(rsp.my_new_rsp.response_code))
    return rsp.my_new_rsp.return_value
```

### 7.3 新增 Protocol Buffers 消息

1. 在 `proto/` 創建 `.proto` 文件
2. 編譯為 `_pb2.py`
3. 在 `comm_messages.proto` 中導入

### 7.4 新增 CRC 算法

在相關模組中實現新的 CRC 函數:

```python
import crcmod

def get_crc_new_algorithm(header_str, body_str):
    # 實現新的 CRC 算法
    pass
```

---

## 八、潛在改進區域

### 8.1 錯誤處理

**問題**: 某些異常處理不夠完善

**建議**:
- 添加更詳細的異常信息
- 統一異常處理策略
- 添加超時機制

**示例**:
```python
# 當前
def poll(self, request):
    response = comm_messages_pb2.CommMsgBody()
    response.ParseFromString(response_str)
    if not response: raise VcuPollFailed()

# 改進
def poll(self, request, timeout=3):
    try:
        response_str = recv_frame(self.test_sock, timeout)
    except socket.timeout:
        raise VcuTimeoutError(f"Timeout after {timeout}s")

    response = comm_messages_pb2.CommMsgBody()
    try:
        response.ParseFromString(response_str)
    except Exception as e:
        raise VcuParseError(f"Failed to parse response: {e}")
```

### 8.2 代碼重複

**問題**: `StructMessage` 基類在多個文件中重複定義

**建議**: 創建共享的 `struct_message.py` 模組

**重複位置**:
- `ls_comms/ls_msgs.py`
- `ltl_chassis_fixt_comms/chassis_msgs.py`
- `vcu_ether_comms/header.py`

**改進**:
```python
# polish/dut_comms/common/struct_message.py
class StructMessage(object):
    def __init__(self):
        for name in self.fields:
            setattr(self, name, None)

    # ... 其他方法

# 各模組導入
from polish.dut_comms.common.struct_message import StructMessage
```

### 8.3 文檔

**問題**: 缺少詳細的 docstrings

**建議**:
- 為所有公共方法添加 docstrings
- 使用標準文檔格式 (Google/NumPy)
- 添加使用示例

**示例**:
```python
def drive_motor(intf, channel, speed, motor_command_timestamp=None):
    """
    控制牽引電機

    Args:
        intf: VcuTestInterface 實例
        channel: LEFT 或 RIGHT
        speed: 目標速度 (m/s), 範圍 -0.8 到 0.8
        motor_command_timestamp: 電機命令時間戳

    Returns:
        tuple: (test_command_rsp, timestamp_us)

    Raises:
        VcuCommResponseCodeFailure: 如果響應碼非 RESP_GOOD

    Example:
        >>> test_state, ts = drive_motor(intf, LEFT, 0.5)
        >>> print(f"Left speed: {test_state.traction_left_speed_mps} m/s")
    """
```

### 8.4 測試

**問題**: 缺少單元測試

**建議**:
- 使用 pytest 添加單元測試
- 測試覆蓋率目標 > 80%
- 添加集成測試

**測試示例**:
```python
# tests/test_vcu_cmds.py
import pytest
from polish.dut_comms.vcu_ether_comms.vcu_cmds import drive_motor

def test_drive_motor_speed_range():
    """測試速度範圍驗證"""
    # 測試合法速度
    for speed in [0.2, 0.5, 0.8]:
        # 應該接受
        pass

    # 測試非法速度
    with pytest.raises(ValueError):
        drive_motor(intf, LEFT, 1.5)  # 超出範圍
```

### 8.5 類型提示

**問題**: 缺少 Python 類型提示

**建議**:
```python
def drive_motor(
    intf: VcuTestInterface,
    channel: bool,
    speed: float,
    motor_command_timestamp: Optional[int] = None
) -> Tuple[CommMsgBody, int]:
    pass
```

### 8.6 日誌改進

**問題**: 日誌記錄使用 `print` 語句

**建議**:
```python
import logging

logger = logging.getLogger(__name__)

def drive_motor(intf, channel, speed, motor_command_timestamp=None):
    logger.debug(f"Driving motor: channel={channel}, speed={speed}")
    # ...
    logger.info(f"Motor response: speed={readback_speed}")
```

### 8.7 性能優化

**問題**: 大量消息時可能存在性能瓶頸

**建議**:
- 支持批量發送
- 緩存常用消息
- 優化序列化/反序列化

**示例**:
```python
class VcuTestInterface(object):
    def __init__(self):
        self._msg_cache = {}

    def get_cached_msg(self, msg_type):
        """緩存常用消息對象"""
        if msg_type not in self._msg_cache:
            self._msg_cache[msg_type] = self.get_new_msg(msg_type)
        msg = self._msg_cache[msg_type]
        msg.Clear()
        return msg
```

### 8.8 配置驗證

**問題**: IP 地址和端口硬編碼

**建議**:
```python
# config/vcu_config.py
VCU_CONFIG = {
    'ip': '192.168.3.100',
    'test_port': 8156,
    'connect_port': 8124,
    'timeout': 3.0,
}

class VcuTestInterface(object):
    def __init__(self, config=None):
        if config is None:
            config = VCU_CONFIG
        self.ip = config['ip']
        self.test_port = config['test_port']
        # ...
```

### 8.9 線程安全

**問題**: `MotorDriveThread` 的鎖機制可能導致死鎖

**建議**:
```python
class MotorDriveThread(threading.Thread):
    thr_inst_lock = threading.RLock()

    def __init__(self, intf, channel, speed, **kwargs):
        # 使用 try-finally 確保鎖釋放
        try:
            self.thr_inst_lock.acquire()
        except:
            raise RuntimeError("Failed to acquire motor thread lock")

        try:
            threading.Thread.__init__(self, **kwargs)
            # ... 其他初始化
        except Exception:
            self.thr_inst_lock.release()
            raise
```

### 8.10 Python 2/3 兼容性

**問題**: 代碼混用 Python 2 和 3 語法

**建議**:
- 統一使用 Python 3
- 移除 `print "string"` 語法
- 使用 `six` 庫處理兼容性

**示例**:
```python
# 當前
print 'Protobuf Request="%s"' % request

# 改進
from six.moves import builtins as six_builtins
print('Protobuf Request="{}"'.format(request))
```

---

## 九、關鍵文件索引

| 文件路徑 | 行數 | 核心功能 | 依賴 |
|----------|------|----------|------|
| `ls_comms/ls_mod.py` | 301 | SafetyInterface 串口通訊 | serial, zlib, ls_msgs |
| `ls_comms/ls_msgs.py` | 62 | LS 消息定義 | struct, ctypes |
| `ltl_chassis_fixt_comms/chassis_msgs.py` | 234 | 底盤消息定義 | struct, enum, ctypes |
| `ltl_chassis_fixt_comms/chassis_transport.py` | 159 | 底盤傳輸層 | serial, PyCRC, chassis_msgs |
| `ltl_chassis_fixt_comms/generate_c_include.py` | 117 | C 頭文件生成 | struct, ctypes |
| `vcu_ether_comms/vcu_ether_link.py` | 277 | VcuTestInterface | socket, protobuf, zlib, threading |
| `vcu_ether_comms/vcu_cmds.py` | 489 | VCU 命令封裝 | protobuf, threading, time |
| `vcu_ether_comms/vcu_common.py` | 17 | UDP 工具 | socket |
| `vcu_ether_comms/header.py` | 50 | CommMsgHeader_t | struct, ctypes |
| `vcu_ether_comms/vcu_req_replay.py` | 28 | 請求重放 | vcu_common |
| `vcu_ether_comms/proto/test_msgs_pb2.py` | ~3000 | 測試消息 | protobuf |
| `vcu_ether_comms/proto/*.pb2.py` | 18,247 | 所有 Protocol Buffers 消息 | protobuf |
| `mkstruct.py` | 171 | C 結構解析器 | pycparser, ctypes |
| `semigloss_remote/get_semigloss_remote.sh` | 13 | 遠程控制拉取 | git |

---

## 十、使用示例

### 10.1 ls_comms 使用示例

```python
from polish.dut_comms.ls_comms.ls_mod import SafetyInterface
from polish.dut_comms.ls_comms.ls_msgs import CLIFF_MSG, ENCODER_MSG

# 1. 初始化
si = SafetyInterface('/dev/ttyUSB0')
si.open()

# 2. 讀取懸崖傳感器 1
packet = si.create_msg(CLIFF_MSG, 0x01)
si.send_packet(packet)
recv_packet, voltage = si.receive_packet()
print(f"Cliff 1 voltage: {voltage}V")

# 3. 讀取編碼器 1
packet = si.create_msg(ENCODER_MSG, 0x01)
si.send_packet(packet)
recv_packet, speed = si.receive_packet()
print(f"Encoder 1 speed: {speed}")

# 4. 關閉
si.close()
```

### 10.2 ltl_chassis_fixt_comms 使用示例

```python
from polish.dut_comms.ltl_chassis_fixt_comms.chassis_transport import (
    get_serial_port, send_msg, get_msg
)
from polish.dut_comms.ltl_chassis_fixt_comms.chassis_msgs import (
    RotateTurntable, close_open_enum, operation_enum
)

# 1. 打開串口
port = get_serial_port('/dev/ttyUSB0')

# 2. 旋轉轉盤
msg = RotateTurntable()
msg.operation = operation_enum.ROTATE_LEFT.value
msg.angle = 90
send_msg(port, msg)

# 3. 接收響應
header, rsp, footer = get_msg(port)
print(f"Status: {rsp.status}")
print(f"Angle: {rsp.angle}")

# 4. 關閉
port.close()
```

### 10.3 vcu_ether_comms 使用示例

#### 基本連接和測試

```python
from polish.dut_comms.vcu_ether_comms.vcu_ether_link import VcuTestInterface

# 1. 初始化接口
intf = VcuTestInterface()
intf.verbose = False

# 2. 連接
try:
    resp = intf.init_interface()
    print("Connected successfully")
except Exception as e:
    print(f"Connection failed: {e}")

# 3. 讀取固件版本
print(f"Firmware version: {resp.get_fw_version_rsp.fw_version}")
```

#### 電機控制

```python
from polish.dut_comms.vcu_ether_comms.vcu_cmds import (
    drive_motor, MotorDriveThread, LEFT, RIGHT
)

# 1. 簡單電機控制
test_state, timestamp = drive_motor(intf, LEFT, 0.5)
print(f"Left motor speed: {test_state.traction_left_speed_mps} m/s")
print(f"Left motor current: {test_state.traction_left_current_ma} mA")

# 2. 線程化電機控制 (帶速度監控)
motor_thr = MotorDriveThread(intf, LEFT, 0.5)
motor_thr.start()

# 等待電機達到目標速度
motor_thr.at_speed_event.wait(20)
print("Motor reached target speed!")

# 停止電機
motor_thr.done.set()
motor_thr.join()
motor_thr.teardown()
```

#### 吸塵機控制

```python
from polish.dut_comms.vcu_ether_comms.vcu_cmds import (
    vacuum_on, vacuum_off, vacuum_speed
)

# 1. 打開吸塵機
rsp = vacuum_on(intf)
print(f"Vacuum state: {rsp.vacuum_test_rsp.vacuum_state}")
print(f"Vacuum current: {rsp.vacuum_test_rsp.vacuum_current_ma} mA")

# 2. 設置速度
state, current = vacuum_speed(intf, speed=2)  # 0=off, 1=normal, 2=turbo
print(f"Vacuum state: {state}, current: {current} mA")

# 3. 關閉吸塵機
vacuum_off(intf)
```

#### 掃地機控制

```python
from polish.dut_comms.vcu_ether_comms.vcu_cmds import (
    sweeper_on, sweeper_off,
    actuator_extend, actuator_retract
)

# 1. 打開掃地機
status, current, rpm = sweeper_on(intf, speed=1500)
print(f"Sweeper status: {status}, current: {current} mA, RPM: {rpm}")

# 2. 伸出執行器
actuator_status, actuator_current = actuator_extend(intf)
print(f"Actuator status: {actuator_status}, current: {actuator_current} mA")

# 3. 縮回執行器
actuator_status, actuator_current = actuator_retract(intf)

# 4. 關閉掃地機
sweeper_off(intf)
```

#### 傳感器讀取

```python
from polish.dut_comms.vcu_ether_comms.vcu_cmds import (
    read_cliff_sensors, read_bumper_sensors,
    read_wheel_lift_sensors
)

# 1. 讀取懸崖傳感器
cliff_state, cliff_voltage = read_cliff_sensors(intf)
print(f"Cliff state: {cliff_state}")
print(f"Cliff voltage: {cliff_voltage} V")

# 2. 讀取保險槓
bumper1, bumper2 = read_bumper_sensors(intf)
print(f"Bumper 1: {bumper1}, Bumper 2: {bumper2}")

# 3. 讀取輪子抬升傳感器
left_lifted, right_lifted = read_wheel_lift_sensors(intf)
print(f"Left wheel lifted: {left_lifted}")
print(f"Right wheel lifted: {right_lifted}")
```

#### EEPROM 操作

```python
from polish.dut_comms.vcu_ether_comms.vcu_cmds import (
    eeprom_vcu_info_read, eeprom_vcu_info_write
)

# 1. 讀取 VCU 信息
serial_num, hw_rev, date_time, tester_id, fixture_id, batt_cutoff = \
    eeprom_vcu_info_read(intf)
print(f"Serial: {serial_num}")
print(f"HW Rev: {hw_rev}")
print(f"Test Time: {date_time}")
print(f"Tester ID: {tester_id}")
print(f"Fixture ID: {fixture_id}")
print(f"Battery Cutoff: {batt_cutoff} mV")

# 2. 寫入 VCU 信息
eeprom_vcu_info_write(
    intf,
    serial_num="VCU12345",
    hw_rev=2,
    date_time="2026-01-28_12:00:00",
    tester_id=1,
    fixture_id=10,
    pri_batt_cutoff_mv=12000
)
```

#### 循環命令

```python
from polish.dut_comms.vcu_ether_comms.vcu_cmds import cmd_loop, drive_motor

# 定義命令函數
def my_command(intf, speed):
    return drive_motor(intf, LEFT, speed)

# 執行循環
final_return = cmd_loop(
    intf,
    cmd=my_command,
    cmd_args=(0.5,),
    cadence=0.025,      # 25ms 間隔
    total_duration=1.0    # 執行 1 秒
)
print(f"Final speed: {final_return.traction_left_speed_mps}")
```

### 10.4 mkstruct.py 使用示例

**C 頭文件** (`my_messages.h`):
```c
#include <stdint.h>

#define SYNC_WORD 0xCAFE
#define MAX_LENGTH 1000

typedef struct {
    uint8_t command;
    uint16_t param1;
    uint32_t param2;
} MyMessage_t;
```

**生成 Python 代碼**:
```bash
python mkstruct.py my_messages.h > my_messages.py
```

**輸出** (`my_messages.py`):
```python
import ctypes
import struct
from collections import OrderedDict

class StructMessage(object):
    def __init__(self):
        for name in self.fields:
            setattr(self, name, None)

    def get_msg_size(self):
        return struct.calcsize(self.pack_str)

    def get_values(self):
        values = []
        for name in self.fields:
            values.append(getattr(self, name))
        return values

    def serialize(self):
        return struct.pack(self.pack_str, *self.get_values())

    def deserialize(self, msg_blob):
        values = struct.unpack(self.pack_str, msg_blob)
        for name, value in zip(self.fields, values):
            setattr(self, name, value)

SYNC_WORD = 0xCAFE
MAX_LENGTH = 1000

class MyMessage_t(StructMessage):
    fields = OrderedDict((
        ("command", ctypes.c_uint8),
        ("param1", ctypes.c_uint16),
        ("param2", ctypes.c_uint32),
    ))
    pack_str = "<BHI"
```

**使用生成的代碼**:
```python
from my_messages import MyMessage_t

msg = MyMessage_t()
msg.command = 1
msg.param1 = 100
msg.param2 = 1000

serialized = msg.serialize()
print(f"Serialized: {serialized.hex()}")

recv_msg = MyMessage_t()
recv_msg.deserialize(serialized)
print(f"Command: {recv_msg.command}")
print(f"Param1: {recv_msg.param1}")
print(f"Param2: {recv_msg.param2}")
```

---

## 十一、總結

**dut_comms** 是一個功能完整的設備通訊框架，具有以下特點：

### 優點
✅ 支持多種通訊協議 (串口, UDP)
✅ 結構化消息定義 (StructMessage, Protocol Buffers)
✅ 可靠的幀檢測機制 (Sync + Length + CRC)
✅ 線程安全的實現 (SocketBuffer, RLock)
✅ 豐富的 VCU 命令封裝
✅ 自動消息註冊機制
✅ 跨語言支持 (Python ↔ C)

### 需要改進
⚠️ Python 2/3 兼容性問題
⚠️ 代碼重複 (StructMessage)
⚠️ 缺少單元測試
⚠️ 文檔不完善
⚠️ 錯誤處理不夠細緻
⚠️ 硬編碼配置 (IP 地址)
⚠️ 使用 `print` 而非 `logging`

### 適用場景
- ✅ 製造測試中的設備通訊
- ✅ 串口設備控制 (安全接口, 底盤治具)
- ✅ 以太網設備控制 (VCU 車輛控制)
- ✅ 跨語言集成 (Python ↔ C)
- ✅ 自動化測試 (線程化命令執行)

### 技術亮點
- **三重幀檢測**: Sync + Length + CRC 確保數據完整性
- **線程安全**: SocketBuffer 線程讀緩衝區
- **自動註冊**: 消息類型自動映射
- **封裝完善**: 高層命令函數簡化使用
- **跨協議**: 統一的 StructMessage 基類

---

## 十二、WebPDTool 實現狀態

### 12.1 架構對比

| 層次 | PDTool4 | WebPDTool (backend/app/) |
|------|---------|-------------------------|
| 應用層 | Direct imports | FastAPI + Measurements |
| 測試框架 | Polish testing framework | BaseMeasurement abstractions |
| 通訊層 | dut_comms modules | instrument_connection.py |
| 數據層 | SQLite | SQLAlchemy 2.0 (async) |

### 12.2 已完成功能

#### 通用通訊基礎設施 ✅

**文件**: `backend/app/services/instrument_connection.py` (498 行)

**實現的連接類**:

| 連接類 | 功能 | 狀態 |
|---------|------|------|
| `BaseInstrumentConnection` | 抽象基類 (ABC) | ✅ |
| `VISAInstrumentConnection` | VISA/USB/LAN/GPIB 通訊 | ✅ |
| `SerialInstrumentConnection` | 串口通訊 (pyserial) | ✅ |
| `SimulationInstrumentConnection` | 模擬連接 (測試用) | ✅ |

**核心功能**:
- ✅ Async/await 支持所有操作
- ✅ 上下文管理器 (`async with`)
- ✅ 連接池 (`InstrumentConnectionPool`)
- ✅ 錯誤處理 (`InstrumentConnectionError`, `InstrumentCommandError`)
- ✅ 串口配置 (baudrate, parity, stopbits, bytesize)
- ✅ VISA 配置 (timeout, serial settings)

**配置管理**: `backend/app/core/instrument_config.py` (311 行)

```python
class SerialAddress(InstrumentAddress):
    type: Literal["SERIAL"] = "SERIAL"
    port: str = Field(..., description="COM port name, e.g., COM3 or /dev/ttyUSB0")
    baudrate: int = 115200
    stopbits: int = 1
    parity: str = "N"
    bytesize: int = 8

class TCPIPSocketAddress(InstrumentAddress):
    type: Literal["TCPIP_SOCKET"] = "TCPIP_SOCKET"
    host: str
    port: int
```

#### 簡單通訊命令 ✅

**文件**: `backend/src/lowsheen_lib/`

| 文件 | 功能 | 行數 |
|------|------|------|
| `ComPortCommand.py` | 串口命令發送 | 148 |
| `TCPIPCommand.py` | TCP/IP 命令 + CRC32 | 115 |

**ComPortCommand.py 實現**:
```python
def get_response(ser, timeout, ReslineCount):
    response = ''
    start_time = time.time()
    get_total_line = 0
    end_count = 0

    while (time.time() - start_time) < timeout:
        if ser.in_waiting > 0:
            line_response = ser.readline().decode('utf-8', errors='replace').strip()
            get_total_line += 1
            if response:
                response += '\n'
            response += line_response
            end_count = 0

            if ReslineCount != '':
                if get_total_line >= ReslineCount:
                    break
```

**TCPIPCommand.py 實現**:
```python
def calculate_crc32(data):
    return binascii.crc32(data)

def main(TCP_IP, TCP_PORT, MESSAGE):
    crc32_checksum = calculate_crc32(MESSAGE)
    MESSAGE_WITH_CRC = MESSAGE + crc32_checksum.to_bytes(4, byteorder='big')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_IP, TCP_PORT))
    sock.send(MESSAGE_WITH_CRC)
    response = read_response(sock)
```

#### 測量抽象層 ✅

**文件**: `backend/app/measurements/base.py`

```python
class BaseMeasurement(ABC):
    @abstractmethod
    async def prepare(self, params: Dict[str, Any]):
        pass

    @abstractmethod
    async def execute(self) -> MeasurementResult:
        pass

    @abstractmethod
    async def cleanup(self):
        pass
```

**已實現的測量類型**:
- `DummyMeasurement` - 隨機值測試
- `CommandTestMeasurement` - 外部命令執行
- `SerialNumberMeasurement` - 序列號讀取

### 12.3 未完成功能

#### ls_comms - LS 系列設備通訊 ❌

| 功能 | PDTool4 | WebPDTool |
|------|---------|-----------|
| SafetyInterface 類 | ✅ 301 行 | ❌ 未實現 |
| CRC32 計算 | ✅ zlib.crc32 | ❌ 無 |
| StructMessage 基類 | ✅ ls_msgs.py | ❌ 無 |
| 懸崖傳感器命令 | ✅ CLIFF_MSG | ❌ 無 |
| 編碼器命令 | ✅ ENCODER_MSG | ❌ 無 |
| 幀頭解析 (0xCAFE) | ✅ | ❌ 無 |
| 三步幀檢測 | ✅ | ❌ 無 |

**需要實現的文件**:
```
backend/app/services/dut_comms/ls_comms/
├── __init__.py
├── ls_mod.py          # SafetyInterface
└── ls_msgs.py         # StructMessage + 消息定義
```

#### ltl_chassis_fixt_comms - 底盤治具通訊 ❌

| 功能 | PDTool4 | WebPDTool |
|------|---------|-----------|
| Protocol Buffers 消息 | ✅ chassis_msgs.py | ❌ 無 |
| CRC16Kermit 校驗 | ✅ PyCRC | ❌ 無 |
| 同步字 (0xA5FF00CC) | ✅ | ❌ 無 |
| 轉盤控制命令 | ✅ RotateTurntable | ❌ 無 |
| 編碼器讀取 | ✅ ReadEncoderCount | ❌ 無 |
| 懸崖門控 | ✅ ActuateCliffSensorDoor | ❌ 無 |
| 自動註冊機制 | ✅ | ❌ 無 |
| C 頭文件生成 | ✅ generate_c_include.py | ❌ 無 |

**需要實現的文件**:
```
backend/app/services/dut_comms/ltl_chassis_fixt_comms/
├── __init__.py
├── chassis_msgs.py         # 消息定義
├── chassis_transport.py    # 傳輸層
└── generate_c_include.py  # C 頭文件生成
```

#### vcu_ether_comms - VCU 以太網通訊 ❌

| 功能 | PDTool4 | WebPDTool |
|------|---------|-----------|
| VcuTestInterface 類 | ✅ vcu_ether_link.py | ❌ 無 |
| Protocol Buffers | ✅ 40+ .pb2.py 文件 | ❌ 無 |
| UDP socket 工具 | ✅ vcu_common.py | ❌ 無 |
| 三重幀檢測 | ✅ | ❌ 無 |
| SocketBuffer 線程緩衝區 | ✅ | ❌ 無 |
| CommMsgHeader_t 消息頭 | ✅ header.py | ❌ 無 |
| 電機控制命令 | ✅ vcu_cmds.py (489 行) | ❌ 無 |
| MotorDriveThread | ✅ 線程化電機控制 | ❌ 無 |
| 吸塵機/掃地機控制 | ✅ | ❌ 無 |
| 傳感器讀取 | ✅ | ❌ 無 |
| EEPROM 操作 | ✅ | ❌ 無 |

**需要實現的文件**:
```
backend/app/services/dut_comms/vcu_ether_comms/
├── __init__.py
├── vcu_ether_link.py     # VcuTestInterface
├── vcu_cmds.py           # VCU 命令封裝
├── vcu_common.py         # UDP 工具
├── header.py             # CommMsgHeader_t
├── vcu_req_replay.py     # 請求重放
└── proto/
    ├── common_pb2.py
    ├── test_msgs_pb2.py
    ├── battery_msgs_pb2.py
    ├── traction_motor_msgs_pb2.py
    ├── fault_codes_pb2.py
    ├── imu_data_msgs_pb2.py
    ├── gpio_test_msgs_pb2.py
    └── ... (40+ .pb2.py 文件)
```

#### 通訊工具 ❌

| 工具 | PDTool4 | WebPDTool |
|------|---------|-----------|
| mkstruct.py | ✅ C 結構解析器 | ❌ 無 |
| pycparser 集成 | ✅ | ❌ 無 |
| C 頭文件生成 | ✅ | ❌ 無 |
| 構建腳本 | ✅ build_vcu_proto_msgs.sh | ❌ 無 |

### 12.4 實現差異總結

#### 通訊協議支持對比

| 協議 | PDTool4 | WebPDTool | 差異說明 |
|------|---------|-----------|----------|
| 串口 (Serial) | ✅ ls_comms + ltl_chassis | ✅ SerialInstrumentConnection | WebPDTool 只有基礎串口，缺少協議層 |
| UDP | ✅ vcu_ether_comms | ✅ TCPIPConnection | WebPDTool 只有 TCP，缺少 UDP |
| Protocol Buffers | ✅ 40+ .pb2.py | ❌ 無 | WebPDTool 未整合 protobuf |
| CRC32 | ✅ zlib.crc32 | ✅ TCPIPCommand.py | WebPDTool 只有簡單 CRC32 |
| CRC16Kermit | ✅ PyCRC | ❌ 無 | WebPDTool 未實現 |

#### 核心類對比

| 核心類 | PDTool4 | WebPDTool | 狀態 |
|---------|---------|-----------|------|
| StructMessage | ✅ | ❌ | 未實現 |
| SafetyInterface | ✅ | ❌ | 未實現 |
| VcuTestInterface | ✅ | ❌ | 未實現 |
| MotorDriveThread | ✅ | ❌ | 未實現 |
| SocketBuffer | ✅ | ❌ | 未實現 |
| BaseInstrumentConnection | ❌ | ✅ | 已實現 (async 版本) |
| InstrumentConnectionPool | ❌ | ✅ | 已實現 (async 版本) |

#### 消息體系對比

| 消息類型 | PDTool4 | WebPDTool |
|----------|---------|-----------|
| LS 消息 | ✅ CliffMsgBody_t, EncoderMsgBody_t | ❌ 無 |
| 底盤消息 | ✅ RotateTurntable, EncoderCount 等 | ❌ 無 |
| VCU 消息 | ✅ 40+ protobuf 消息 | ❌ 無 |
| 測試消息 | ✅ TestCommandReq/Rsp | ❌ 無 |
| 電池消息 | ✅ battery_msgs_pb2.py | ❌ 無 |
| IMU 消息 | ✅ imu_data_msgs_pb2.py | ❌ 無 |

### 12.5 遷移建議

#### 階段 1: 基礎通訊層 (短期)

```python
# backend/app/services/dut_comms/ls_comms/ls_mod.py
from app.services.instrument_connection import SerialInstrumentConnection
import zlib
import struct

class SafetyInterface(SerialInstrumentConnection):
    def __init__(self, port_name: str):
        super().__init__(config=SerialAddress(port=port_name, baudrate=9600))
        self.port_name = port_name

    async def receive_packet(self):
        # 實現三步幀檢測
        # Sync 0xCA, 0xFE → Length → CRC
        pass

    async def send_packet(self, msg_body_string: str):
        # 創建幀頭 (sync, length, crc)
        # 發送數據
        pass
```

#### 階段 2: 消息定義 (中期)

```python
# backend/app/services/dut_comms/ls_comms/ls_msgs.py
from collections import OrderedDict
import struct
import ctypes

class StructMessage:
    fields = OrderedDict()
    pack_str = ""

    def __init__(self):
        for name in self.fields:
            setattr(self, name, None)

    def serialize(self):
        return struct.pack(self.pack_str, *self.get_values())

    def deserialize(self, msg_blob):
        values = struct.unpack(self.pack_str, msg_blob)
        for name, value in zip(self.fields, values):
            setattr(self, name, value)

    def get_values(self):
        return [getattr(self, name) for name in self.fields]

class CliffMsgBody_t(StructMessage):
    fields = OrderedDict((
        ("command", ctypes.c_uint8),
        ("params", ctypes.c_uint8),
    ))
    pack_str = "<BB"
```

#### 階段 3: VCU 集成 (長期)

```python
# backend/app/services/dut_comms/vcu_ether_comms/vcu_ether_link.py
from app.services.instrument_connection import TCPIPConnection
import asyncio
from collections import deque
import threading

class SocketBuffer:
    def __init__(self, sock):
        self._buff = list()
        self._sock = sock
        self._lock = threading.RLock()

    async def fill(self, size):
        loop = asyncio.get_event_loop()
        async with self._lock:
            while len(self._buff) < size:
                data = await loop.sock_recv(self._sock, 4096)
                self._buff.extend(data)

class VcuTestInterface:
    def __init__(self):
        self.test_sock = None
        self.connect_sock = None

    async def init_interface(self):
        # 連接握手
        if not await self.connect():
            raise VcuConnectFailed()
        # 初始化測試 socket
        pass

    async def connect(self):
        self.connect_sock = await self._get_udp_sock()
        # 實現 'connect' 握手
        pass
```

#### 階段 4: Protocol Buffers 整合 (長期)

```python
# backend/app/services/dut_comms/vcu_ether_comms/proto/test_msgs_pb2.py
# 從 PDTool4 遷移現有的 .pb2.py 文件
# 或使用 protoc 重新編譯 .proto 文件
```

### 12.6 優先級建議

#### 高優先級

1. **ls_comms 遷移**
   - 實現 SafetyInterface 類
   - 實現 StructMessage 基類
   - 實現懸崖傳感器和編碼器命令
   - **估計**: 1-2 週

2. **VCU 基礎通訊**
   - 實現 VcuTestInterface
   - 實現 SocketBuffer
   - 實現三重幀檢測
   - **估計**: 2-3 週

#### 中優先級

3. **底盤治具通訊**
   - 實現 CRC16Kermit
   - 實現轉盤和編碼器命令
   - 實現自動註冊機制
   - **估計**: 1-2 週

4. **Protocol Buffers 整合**
   - 遷移所有 .pb2.py 文件
   - 實現消息序列化/反序列化
   - **估計**: 2-3 週

#### 低優先級

5. **工具和腳本**
   - 實現 mkstruct.py
   - 實現 C 頭文件生成器
   - 實現構建腳本
   - **估計**: 1 週

6. **VCU 高級命令**
   - 實現 MotorDriveThread
   - 實現所有 VCU 命令封裝 (vcu_cmds.py)
   - 實現 EEPROM 操作
   - **估計**: 3-4 週

### 12.7 測試策略

#### 單元測試

```python
# tests/services/dut_comms/test_ls_comms.py
import pytest
from app.services.dut_comms.ls_comms.ls_mod import SafetyInterface
from app.services.dut_comms.ls_comms.ls_msgs import CliffMsgBody_t

@pytest.mark.asyncio
async def test_safety_interface_connect():
    si = SafetyInterface('/dev/ttyUSB0')
    await si.connect()
    assert si.is_connected

@pytest.mark.asyncio
async def test_cliff_sensor_read():
    si = SafetyInterface('/dev/ttyUSB0')
    await si.connect()
    packet = si.create_msg(CLIFF_MSG, 0x01)
    await si.send_packet(packet)
    recv_packet, voltage = await si.receive_packet()
    assert voltage > 0
```

#### 集成測試

```python
# tests/services/dut_comms/test_vcu_integration.py
import pytest
from app.services.dut_comms.vcu_ether_comms.vcu_ether_link import VcuTestInterface

@pytest.mark.asyncio
async def test_vcu_connection():
    intf = VcuTestInterface()
    await intf.init_interface()
    assert intf.test_sock is not None

@pytest.mark.asyncio
async def test_vcu_motor_control():
    from app.services.dut_comms.vcu_ether_comms.vcu_cmds import drive_motor
    intf = VcuTestInterface()
    await intf.init_interface()
    test_state, timestamp = await drive_motor(intf, LEFT, 0.5)
    assert test_state.traction_left_speed_mps > 0
```

### 12.8 文件路徑對照

| PDTool4 路徑 | WebPDTool 建議路徑 | 狀態 |
|---------------|---------------------|------|
| `PDTool4/polish/dut_comms/ls_comms/` | `backend/app/services/dut_comms/ls_comms/` | 待遷移 |
| `PDTool4/polish/dut_comms/ltl_chassis_fixt_comms/` | `backend/app/services/dut_comms/ltl_chassis_fixt_comms/` | 待遷移 |
| `PDTool4/polish/dut_comms/vcu_ether_comms/` | `backend/app/services/dut_comms/vcu_ether_comms/` | 待遷移 |
| `PDTool4/polish/dut_comms/mkstruct.py` | `backend/app/services/dut_comms/mkstruct.py` | 待遷移 |
| `PDTool4/src/lowsheen_lib/ComPortCommand.py` | `backend/src/lowsheen_lib/ComPortCommand.py` | ✅ 已存在 |
| `PDTool4/src/lowsheen_lib/TCPIPCommand.py` | `backend/src/lowsheen_lib/TCPIPCommand.py` | ✅ 已存在 |

---

**文檔版本**: 2.0
**最後更新**: 2026-01-29
**WebPDTool 實現狀態分析**: Claude Code
