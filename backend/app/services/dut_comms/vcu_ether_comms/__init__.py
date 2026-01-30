"""
VCU (Vehicle Control Unit) Ethernet Communication Module

Provides async UDP communication with VCU devices via Ethernet.
Refactored from PDTool4 polish/dut_comms/vcu_ether_comms/ module.

Key features:
- VcuTestInterface: UDP communication with CRC32 frame detection
- Triple-frame detection: Sync (0xCAFE) + Length + CRC validation
- SocketBuffer: Thread-safe buffered reading
- Connection handshake: 'connect' string echo
- Protocol Buffers message support (vcu_cmds.py)

Default endpoints:
- Test port: 8156
- Connect port: 8124
- IP: 192.168.3.100
"""
from .vcu_common import (
    get_udp_sock,
    flush_udp_recv,
    VCU_DEFAULT_IP,
    VCU_TEST_PORT,
    VCU_CONNECT_PORT,
    TEST_ENDPOINT,
    CONNECT_ENDPOINT,
)
from .header import (
    CommMsgHeader_t,
    MAGIC_SYNC_U16,
    MESSAGE_FORMAT_BARE_NANO_PB,
    MESSAGE_FORMAT_C_STRUCT,
    MAX_MESSAGE_BODY_LENGTH,
    COMM_MSG_OK,
    create_header,
    calculate_crc,
)
from .vcu_ether_link import (
    VcuTestInterface,
    VcuConnectFailed,
    VcuTimeout,
    VcuPollFailed,
    SocketBuffer,
)

__all__ = [
    'get_udp_sock',
    'flush_udp_recv',
    'VCU_DEFAULT_IP',
    'VCU_TEST_PORT',
    'VCU_CONNECT_PORT',
    'TEST_ENDPOINT',
    'CONNECT_ENDPOINT',
    'CommMsgHeader_t',
    'MAGIC_SYNC_U16',
    'MESSAGE_FORMAT_BARE_NANO_PB',
    'MESSAGE_FORMAT_C_STRUCT',
    'MAX_MESSAGE_BODY_LENGTH',
    'COMM_MSG_OK',
    'create_header',
    'calculate_crc',
    'VcuTestInterface',
    'VcuConnectFailed',
    'VcuTimeout',
    'VcuPollFailed',
    'SocketBuffer',
]
