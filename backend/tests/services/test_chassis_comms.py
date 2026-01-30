"""
Tests for Chassis Fixture Communication Module

Tests message serialization, CRC calculation, and protocol conformance.
"""

import pytest
from app.services.dut_comms.ltl_chassis_fixt_comms import (
    # Messages
    RotateTurntable,
    GetTurntableAngle,
    ActuateCliffSensorDoor,
    ReadEncoderCount,
    TransportHeader,
    TransportFooter,
    # Enums
    operation_enum,
    close_open_enum,
    left_right_enum,
    status_enum,
    # Utilities
    serialize,
    deserialize,
    get_msg_size,
    SYNC_WORD,
    TRANSPORT_OVERHEAD,
)
from app.services.dut_comms.ltl_chassis_fixt_comms.crc16_kermit import CRC16Kermit


class TestCRC16Kermit:
    """Test CRC16 Kermit checksum calculation"""

    def test_standard_test_vector(self):
        """Test with standard CRC16-Kermit test vector"""
        crc = CRC16Kermit()
        result = crc.calculate(b'123456789')
        assert result == 0x2189

    def test_empty_data(self):
        """Test CRC of empty data"""
        crc = CRC16Kermit()
        result = crc.calculate(b'')
        assert result == 0x0000

    def test_single_byte(self):
        """Test CRC of single byte"""
        crc = CRC16Kermit()
        result = crc.calculate(b'\x00')
        assert result == 0x0000

        result = crc.calculate(b'A')
        assert result == 0x538D


class TestMessageSerialization:
    """Test message serialization and deserialization"""

    def test_rotate_turntable_serialize(self):
        """Test RotateTurntable message serialization"""
        msg = RotateTurntable()
        msg.operation = operation_enum.ROTATE_LEFT.value
        msg.angle = 90

        blob = serialize(msg)
        assert len(blob) == get_msg_size(msg)

        # Deserialize and verify
        recovered = deserialize(RotateTurntable, blob)
        assert recovered.operation == msg.operation
        assert recovered.angle == msg.angle

    def test_actuate_cliff_sensor_door(self):
        """Test ActuateCliffSensorDoor message"""
        msg = ActuateCliffSensorDoor()
        msg.door_number = 4
        msg.close_open = close_open_enum.OPEN.value

        blob = serialize(msg)
        recovered = deserialize(ActuateCliffSensorDoor, blob)

        assert recovered.door_number == 4
        assert recovered.close_open == close_open_enum.OPEN.value

    def test_read_encoder_count(self):
        """Test ReadEncoderCount message"""
        msg = ReadEncoderCount()
        msg.left_right = left_right_enum.LEFT.value

        blob = serialize(msg)
        recovered = deserialize(ReadEncoderCount, blob)

        assert recovered.left_right == left_right_enum.LEFT.value

    def test_get_turntable_angle(self):
        """Test GetTurntableAngle message (no fields)"""
        msg = GetTurntableAngle()

        blob = serialize(msg)
        assert len(blob) == 0  # No fields

        recovered = deserialize(GetTurntableAngle, blob)
        assert isinstance(recovered, GetTurntableAngle)


class TestTransportProtocol:
    """Test transport layer protocol"""

    def test_transport_header(self):
        """Test TransportHeader serialization"""
        header = TransportHeader()
        header.sync_word = SYNC_WORD
        header.length = 20
        header.msg_type = 0x10

        blob = serialize(header)
        assert len(blob) == 8  # 4 + 2 + 2 bytes

        recovered = deserialize(TransportHeader, blob)
        assert recovered.sync_word == SYNC_WORD
        assert recovered.length == 20
        assert recovered.msg_type == 0x10

    def test_transport_footer(self):
        """Test TransportFooter serialization"""
        footer = TransportFooter()
        footer.crc16 = 0x1234

        blob = serialize(footer)
        assert len(blob) == 2  # 2 bytes

        recovered = deserialize(TransportFooter, blob)
        assert recovered.crc16 == 0x1234

    def test_transport_overhead(self):
        """Test transport overhead calculation"""
        assert TRANSPORT_OVERHEAD == 10  # 8 (header) + 2 (footer)

    def test_complete_frame(self):
        """Test complete frame construction"""
        # Create message
        msg = RotateTurntable()
        msg.operation = operation_enum.ROTATE_TO_OPTO_SWITCH.value
        msg.angle = 0

        # Create header
        header = TransportHeader()
        header.sync_word = SYNC_WORD
        header.msg_type = msg.msg_type
        header.length = get_msg_size(msg) + TRANSPORT_OVERHEAD

        # Serialize header and body
        header_bytes = serialize(header)
        body_bytes = serialize(msg)

        # Calculate CRC
        crc = CRC16Kermit()
        crc_value = crc.calculate(header_bytes + body_bytes)

        # Create footer
        footer = TransportFooter()
        footer.crc16 = crc_value

        footer_bytes = serialize(footer)

        # Complete frame
        frame = header_bytes + body_bytes + footer_bytes
        assert len(frame) == header.length

        # Verify CRC
        calculated_crc = crc.calculate(header_bytes + body_bytes)
        assert calculated_crc == crc_value


class TestEnums:
    """Test enumeration types"""

    def test_operation_enum(self):
        """Test operation_enum values"""
        assert operation_enum.ROTATE_TO_OPTO_SWITCH.value == 0
        assert operation_enum.ROTATE_LEFT.value == 1
        assert operation_enum.ROTATE_RIGHT.value == 2

    def test_close_open_enum(self):
        """Test close_open_enum values"""
        assert close_open_enum.CLOSE.value == 0
        assert close_open_enum.OPEN.value == 1

    def test_left_right_enum(self):
        """Test left_right_enum values"""
        assert left_right_enum.LEFT.value == 0
        assert left_right_enum.RIGHT.value == 1

    def test_status_enum(self):
        """Test status_enum values"""
        assert status_enum.SUCCESS.value == 0
        assert status_enum.GENERAL_FAILURE.value == 1
        assert status_enum.TIMEOUT_EXPIRED.value == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
