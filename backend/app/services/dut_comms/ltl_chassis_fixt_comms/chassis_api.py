"""
High-level API for Chassis Test Fixture Operations

Provides convenient async functions for common chassis operations.
"""

import logging
from typing import Tuple

from .chassis_transport import ChassisTransport, ChassisTransportError
from .chassis_msgs import (
    RotateTurntable,
    RotateTurntableStatus,
    GetTurntableAngle,
    TurntableAngleRsp,
    WaitForTurntable,
    WaitForTurntableStatus,
    ActuateCliffSensorDoor,
    ActuateCliffSensorDoorStatus,
    ReadEncoderCount,
    EncoderCount,
    operation_enum,
    close_open_enum,
    left_right_enum,
    status_enum,
)


logger = logging.getLogger(__name__)


async def rotate_turntable(
    port: str,
    operation: operation_enum,
    angle: int = 0,
    timeout: float = 5.0,
) -> status_enum:
    """
    Rotate the turntable.

    Args:
        port: Serial port name (e.g., '/dev/ttyUSB0')
        operation: Rotation operation (ROTATE_LEFT, ROTATE_RIGHT, ROTATE_TO_OPTO_SWITCH)
        angle: Target angle in degrees (0-359)
        timeout: Operation timeout in seconds

    Returns:
        Status code (SUCCESS, GENERAL_FAILURE, TIMEOUT_EXPIRED)

    Raises:
        ChassisTransportError: On communication failure

    Example:
        status = await rotate_turntable('/dev/ttyUSB0', operation_enum.ROTATE_LEFT, 90)
        if status == status_enum.SUCCESS:
            print("Rotation successful")
    """
    async with ChassisTransport(port, timeout=timeout) as transport:
        # Send rotation command
        msg = RotateTurntable()
        msg.operation = operation.value if isinstance(operation, operation_enum) else operation
        msg.angle = angle

        await transport.send_msg(msg)
        logger.info(f"Rotating turntable: operation={operation}, angle={angle}")

        # Receive response
        header, response, footer = await transport.get_msg()

        if not isinstance(response, RotateTurntableStatus):
            raise ChassisTransportError(
                f"Unexpected response type: {type(response).__name__}"
            )

        # Convert status value to enum
        status = status_enum(response.status)
        logger.info(f"Turntable rotation status: {status.name}")

        return status


async def get_turntable_angle(port: str, timeout: float = 2.0) -> int:
    """
    Get current turntable angle.

    Args:
        port: Serial port name
        timeout: Operation timeout in seconds

    Returns:
        Current angle in degrees (0-359)

    Raises:
        ChassisTransportError: On communication failure

    Example:
        angle = await get_turntable_angle('/dev/ttyUSB0')
        print(f"Current angle: {angle} degrees")
    """
    async with ChassisTransport(port, timeout=timeout) as transport:
        # Send get angle command
        msg = GetTurntableAngle()
        await transport.send_msg(msg)
        logger.info("Requesting turntable angle")

        # Receive response
        header, response, footer = await transport.get_msg()

        if not isinstance(response, TurntableAngleRsp):
            raise ChassisTransportError(
                f"Unexpected response type: {type(response).__name__}"
            )

        logger.info(f"Turntable angle: {response.angle} degrees")
        return response.angle


async def wait_for_turntable(
    port: str,
    timeout_seconds: int = 30,
    comm_timeout: float = 35.0,
) -> status_enum:
    """
    Wait for turntable operation to complete.

    Args:
        port: Serial port name
        timeout_seconds: Fixture operation timeout (sent to fixture)
        comm_timeout: Communication timeout (should be > timeout_seconds)

    Returns:
        Status code (SUCCESS, GENERAL_FAILURE, TIMEOUT_EXPIRED)

    Raises:
        ChassisTransportError: On communication failure

    Example:
        status = await wait_for_turntable('/dev/ttyUSB0', timeout_seconds=10)
        if status == status_enum.SUCCESS:
            print("Turntable operation completed")
    """
    async with ChassisTransport(port, timeout=comm_timeout) as transport:
        # Send wait command
        msg = WaitForTurntable()
        msg.timeout_seconds = timeout_seconds

        await transport.send_msg(msg)
        logger.info(f"Waiting for turntable (timeout={timeout_seconds}s)")

        # Receive response
        header, response, footer = await transport.get_msg()

        if not isinstance(response, WaitForTurntableStatus):
            raise ChassisTransportError(
                f"Unexpected response type: {type(response).__name__}"
            )

        status = status_enum(response.status)
        logger.info(f"Turntable wait status: {status.name}")

        return status


async def actuate_cliff_sensor_door(
    port: str,
    door_number: int,
    open_door: bool,
    timeout: float = 2.0,
) -> status_enum:
    """
    Open or close a cliff sensor door.

    Args:
        port: Serial port name
        door_number: Door number (0-4)
        open_door: True to open, False to close
        timeout: Operation timeout in seconds

    Returns:
        Status code (SUCCESS, GENERAL_FAILURE, TIMEOUT_EXPIRED)

    Raises:
        ChassisTransportError: On communication failure

    Example:
        # Open door 0
        status = await actuate_cliff_sensor_door('/dev/ttyUSB0', 0, True)

        # Close door 0
        status = await actuate_cliff_sensor_door('/dev/ttyUSB0', 0, False)
    """
    async with ChassisTransport(port, timeout=timeout) as transport:
        # Send door actuation command
        msg = ActuateCliffSensorDoor()
        msg.door_number = door_number
        msg.close_open = close_open_enum.OPEN.value if open_door else close_open_enum.CLOSE.value

        await transport.send_msg(msg)
        action = "Opening" if open_door else "Closing"
        logger.info(f"{action} cliff sensor door {door_number}")

        # Receive response
        header, response, footer = await transport.get_msg()

        if not isinstance(response, ActuateCliffSensorDoorStatus):
            raise ChassisTransportError(
                f"Unexpected response type: {type(response).__name__}"
            )

        status = status_enum(response.status)
        logger.info(f"Door actuation status: {status.name}")

        return status


async def read_encoder_count(
    port: str,
    left_encoder: bool = True,
    timeout: float = 2.0,
) -> Tuple[status_enum, int]:
    """
    Read encoder count value.

    Args:
        port: Serial port name
        left_encoder: True for left encoder, False for right
        timeout: Operation timeout in seconds

    Returns:
        Tuple of (status, count)

    Raises:
        ChassisTransportError: On communication failure

    Example:
        status, count = await read_encoder_count('/dev/ttyUSB0', left_encoder=True)
        if status == status_enum.SUCCESS:
            print(f"Left encoder count: {count}")
    """
    async with ChassisTransport(port, timeout=timeout) as transport:
        # Send read encoder command
        msg = ReadEncoderCount()
        msg.left_right = left_right_enum.LEFT.value if left_encoder else left_right_enum.RIGHT.value

        await transport.send_msg(msg)
        side = "left" if left_encoder else "right"
        logger.info(f"Reading {side} encoder count")

        # Receive response
        header, response, footer = await transport.get_msg()

        if not isinstance(response, EncoderCount):
            raise ChassisTransportError(
                f"Unexpected response type: {type(response).__name__}"
            )

        status = status_enum(response.status)
        logger.info(f"Encoder read status: {status.name}, count: {response.count}")

        return status, response.count


# Example usage
if __name__ == '__main__':
    import asyncio
    import sys

    async def test_api(port: str):
        """Test all API functions"""
        print(f"\n=== Testing Chassis API on {port} ===\n")

        try:
            # Test 1: Get current angle
            print("1. Getting current turntable angle...")
            angle = await get_turntable_angle(port)
            print(f"   Current angle: {angle}°\n")

            # Test 2: Rotate left
            print("2. Rotating left 45°...")
            status = await rotate_turntable(port, operation_enum.ROTATE_LEFT, 45)
            print(f"   Status: {status.name}\n")

            await asyncio.sleep(1)

            # Test 3: Get new angle
            print("3. Getting new angle...")
            angle = await get_turntable_angle(port)
            print(f"   Current angle: {angle}°\n")

            # Test 4: Return to home
            print("4. Rotating to home position...")
            status = await rotate_turntable(port, operation_enum.ROTATE_TO_OPTO_SWITCH, 0)
            print(f"   Status: {status.name}\n")

            await asyncio.sleep(2)

            # Test 5: Read left encoder
            print("5. Reading left encoder...")
            status, count = await read_encoder_count(port, left_encoder=True)
            print(f"   Status: {status.name}, Count: {count}\n")

            # Test 6: Open cliff sensor door 0
            print("6. Opening cliff sensor door 0...")
            status = await actuate_cliff_sensor_door(port, 0, True)
            print(f"   Status: {status.name}\n")

            await asyncio.sleep(1)

            # Test 7: Close cliff sensor door 0
            print("7. Closing cliff sensor door 0...")
            status = await actuate_cliff_sensor_door(port, 0, False)
            print(f"   Status: {status.name}\n")

            print("=== All tests completed ===")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    if len(sys.argv) < 2:
        print("Usage: python chassis_api.py <serial_port>")
        print("Example: python chassis_api.py /dev/ttyUSB0")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(test_api(sys.argv[1]))
