"""
LTL Chassis Fixture Communication Module

Refactored from PDTool4 polish/dut_comms/ltl_chassis_fixt_comms/

Provides serial communication with chassis test fixture using CRC16Kermit.

Protocol:
- Serial: 9600 baud, 8N1
- Sync Word: 0xA5FF00CC
- CRC: CRC16Kermit
- Message Format: Header + Body + Footer

Supported Operations:
- Turntable control (rotate, get angle)
- Cliff sensor door actuation
- Encoder count reading
- Turntable wait operations

Example Usage:
    from app.services.dut_comms.ltl_chassis_fixt_comms import (
        ChassisTransport,
        rotate_turntable,
        read_encoder_count,
        operation_enum
    )

    # High-level API
    status = await rotate_turntable('/dev/ttyUSB0', operation_enum.ROTATE_LEFT, 90)

    # Low-level API
    async with ChassisTransport('/dev/ttyUSB0') as transport:
        msg = RotateTurntable()
        msg.operation = operation_enum.ROTATE_LEFT.value
        msg.angle = 90
        await transport.send_msg(msg)
        header, response, footer = await transport.get_msg()
"""

from .chassis_msgs import (
    # Enums
    close_open_enum,
    left_right_enum,
    status_enum,
    operation_enum,

    # Message classes
    TransportHeader,
    TransportFooter,
    ActuateCliffSensorDoor,
    ActuateCliffSensorDoorStatus,
    ReadEncoderCount,
    EncoderCount,
    WaitForTurntable,
    WaitForTurntableStatus,
    RotateTurntable,
    RotateTurntableStatus,
    GetTurntableAngle,
    TurntableAngleRsp,

    # Utilities
    serialize,
    deserialize,
    get_msg_size,
    type_msg_map,
    SYNC_WORD,
    TRANSPORT_OVERHEAD,
)

from .chassis_transport import (
    ChassisTransport,
    ChassisTransportError,
    ChassisCRCError,
    ChassisTimeoutError,
)

from .chassis_api import (
    rotate_turntable,
    get_turntable_angle,
    wait_for_turntable,
    actuate_cliff_sensor_door,
    read_encoder_count,
)

__all__ = [
    # Enums
    'close_open_enum',
    'left_right_enum',
    'status_enum',
    'operation_enum',

    # Message classes
    'TransportHeader',
    'TransportFooter',
    'ActuateCliffSensorDoor',
    'ActuateCliffSensorDoorStatus',
    'ReadEncoderCount',
    'EncoderCount',
    'WaitForTurntable',
    'WaitForTurntableStatus',
    'RotateTurntable',
    'RotateTurntableStatus',
    'GetTurntableAngle',
    'TurntableAngleRsp',

    # Utilities
    'serialize',
    'deserialize',
    'get_msg_size',
    'type_msg_map',
    'SYNC_WORD',
    'TRANSPORT_OVERHEAD',

    # Transport
    'ChassisTransport',
    'ChassisTransportError',
    'ChassisCRCError',
    'ChassisTimeoutError',

    # High-level API
    'rotate_turntable',
    'get_turntable_angle',
    'wait_for_turntable',
    'actuate_cliff_sensor_door',
    'read_encoder_count',
]
