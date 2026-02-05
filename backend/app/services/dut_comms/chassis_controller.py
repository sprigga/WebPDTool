"""
Chassis Controller Service
Manages chassis fixture rotation for DUT testing
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from enum import IntEnum

logger = logging.getLogger(__name__)


class RotationDirection(IntEnum):
    """Chassis rotation direction constants"""
    CLOCKWISE = 6      # CW command code
    COUNTERCLOCKWISE = 9  # CCW command code


class ChassisController:
    """
    Controls chassis fixture rotation for DUT positioning.
    Maps to PDTool4's MyThread_CW/CCW functionality.
    """

    def __init__(self, device_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize chassis controller.

        Args:
            device_path: Serial port path (e.g., '/dev/ttyACM0')
            config: Additional configuration parameters
        """
        self.device_path = device_path or "/dev/ttyACM0"
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_rotating = False
        self._control_script = self.config.get("control_script", "./chassis_comms/chassis_fixture_bat.py")

    async def rotate(
        self,
        direction: RotationDirection,
        duration_ms: Optional[int] = None
    ) -> bool:
        """
        Rotate chassis in specified direction.

        Args:
            direction: RotationDirection.CLOCKWISE or COUNTERCLOCKWISE
            duration_ms: Optional rotation duration in milliseconds

        Returns:
            True if successful, False otherwise
        """
        try:
            if self._is_rotating:
                self.logger.warning("Chassis is already rotating")
                return False

            direction_name = "CLOCKWISE" if direction == RotationDirection.CLOCKWISE else "COUNTERCLOCKWISE"
            self.logger.info(f"Starting chassis rotation: {direction_name} (code={direction})")

            self._is_rotating = True

            # TODO: OLD IMPLEMENTATION (Script-based):
            # Build command arguments
            # Format: python chassis_fixture_bat.py <device> <direction_code> <command_type>
            # cmd_args = [
            #     "python3",
            #     self._control_script,
            #     self.device_path,
            #     str(direction),
            #     "1"  # Command type: 1 = rotation command
            # ]
            #
            # # Execute chassis control script asynchronously
            # process = await asyncio.create_subprocess_exec(...)
            #
            # NEW IMPLEMENTATION: Direct serial communication
            success = await self._send_rotation_command(direction, duration_ms)

            if not success:
                self.logger.error(f"Failed to execute chassis rotation: {direction_name}")
                return False

            self.logger.info(f"Chassis rotation {direction_name} completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Chassis rotation error: {e}", exc_info=True)
            return False
        finally:
            self._is_rotating = False

    async def _send_rotation_command(self, direction: RotationDirection, duration_ms: Optional[int] = None) -> bool:
        """
        Send rotation command to chassis fixture via serial protocol.

        Args:
            direction: RotationDirection.CLOCKWISE or COUNTERCLOCKWISE
            duration_ms: Optional rotation duration (not currently used by firmware)

        Returns:
            True if command executed successfully
        """
        try:
            from .ltl_chassis_fixt_comms.chassis_transport import ChassisTransport
            from .ltl_chassis_fixt_comms.chassis_msgs import (
                RotateTurntable,
                operation_enum,
                status_enum
            )

            # Map direction to operation
            # PDTool4 protocol: operation 1 = CCW (left), operation 2 = CW (right)
            if direction == RotationDirection.CLOCKWISE:
                operation = operation_enum.ROTATE_RIGHT.value  # 2
                angle = 90  # Default rotation angle in degrees
            else:  # COUNTERCLOCKWISE
                operation = operation_enum.ROTATE_LEFT.value  # 1
                angle = 90  # Default rotation angle in degrees

            # If duration_ms provided, calculate angle (assuming ~1 deg/ms speed)
            # This is a rough estimate - actual speed depends on hardware
            if duration_ms:
                angle = min(int(duration_ms / 10), 360)  # Cap at 360 degrees

            self.logger.debug(f"Sending rotation command: operation={operation}, angle={angle}")

            # Open connection and send command
            async with ChassisTransport(self.device_path) as transport:
                # Create rotation message
                msg = RotateTurntable()
                msg.operation = operation
                msg.angle = angle

                # Send command
                await transport.send_msg(msg)

                # Wait for response
                header, response, footer = await transport.get_msg()

                # Check status
                if hasattr(response, 'status'):
                    if response.status == status_enum.SUCCESS.value:
                        self.logger.info(f"Chassis rotation command successful")
                        return True
                    else:
                        self.logger.error(f"Chassis rotation failed with status: {response.status}")
                        return False
                else:
                    # Unexpected response type
                    self.logger.warning(f"Unexpected response type: {type(response)}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to send rotation command: {e}", exc_info=True)
            return False

    async def rotate_clockwise(self, duration_ms: Optional[int] = None) -> bool:
        """
        Rotate chassis clockwise.
        Maps to PDTool4's MyThread_CW.

        Args:
            duration_ms: Optional rotation duration

        Returns:
            True if successful
        """
        return await self.rotate(RotationDirection.CLOCKWISE, duration_ms)

    async def rotate_counterclockwise(self, duration_ms: Optional[int] = None) -> bool:
        """
        Rotate chassis counterclockwise.
        Maps to PDTool4's MyThread_CCW.

        Args:
            duration_ms: Optional rotation duration

        Returns:
            True if successful
        """
        return await self.rotate(RotationDirection.COUNTERCLOCKWISE, duration_ms)

    async def stop_rotation(self) -> bool:
        """
        Stop chassis rotation.

        Returns:
            True if successful
        """
        self.logger.info("Stopping chassis rotation")
        # TODO: Implement stop command if supported by hardware
        self._is_rotating = False
        return True

    def is_rotating(self) -> bool:
        """
        Check if chassis is currently rotating.

        Returns:
            True if rotating
        """
        return self._is_rotating


# Global chassis controller instance
_chassis_controller_instance: Optional[ChassisController] = None


def get_chassis_controller(
    device_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> ChassisController:
    """
    Get or create global chassis controller instance.

    Args:
        device_path: Device path for chassis control
        config: Configuration parameters

    Returns:
        ChassisController instance
    """
    global _chassis_controller_instance

    if _chassis_controller_instance is None:
        _chassis_controller_instance = ChassisController(device_path, config)

    return _chassis_controller_instance
