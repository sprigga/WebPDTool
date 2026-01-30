"""
LS Series Device Communication Module

Provides communication with LS series safety interface devices via serial port.
Refactored from PDTool4 polish/dut_comms/ls_comms/ module.

Key features:
- SafetyInterface: Serial communication with CRC32 frame detection
- Message definitions: CliffMsgBody_t, EncoderMsgBody_t
- 0xCAFE sync word detection
- 3-step frame detection: Sync → Length → CRC
"""
from .ls_msgs import (
    StructMessage,
    MsgHeader,
    CliffMsgBody_t,
    EncoderMsgBody_t,
    CLIFF_MSG,
    ENCODER_MSG,
    command_msg_map,
)
from .ls_mod import (
    SafetyInterface,
    SafetyInterfaceError,
    SafetyInterfaceConnectionError,
    SafetyInterfaceTimeout,
    read_cliff_sensor,
    read_encoder,
)

__all__ = [
    'StructMessage',
    'MsgHeader',
    'CliffMsgBody_t',
    'EncoderMsgBody_t',
    'CLIFF_MSG',
    'ENCODER_MSG',
    'command_msg_map',
    'SafetyInterface',
    'SafetyInterfaceError',
    'SafetyInterfaceConnectionError',
    'SafetyInterfaceTimeout',
    'read_cliff_sensor',
    'read_encoder',
]
