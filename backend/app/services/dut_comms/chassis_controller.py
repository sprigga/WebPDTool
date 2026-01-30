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

            # Build command arguments
            # Format: python chassis_fixture_bat.py <device> <direction_code> <command_type>
            cmd_args = [
                "python3",
                self._control_script,
                self.device_path,
                str(direction),
                "1"  # Command type: 1 = rotation command
            ]

            # Execute chassis control script asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for process completion with timeout
            timeout = (duration_ms / 1000.0) if duration_ms else 10.0
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                if process.returncode != 0:
                    error_msg = stderr.decode().strip() if stderr else f"Exit code: {process.returncode}"
                    self.logger.error(f"Chassis rotation failed: {error_msg}")
                    return False

                output = stdout.decode().strip()
                if output:
                    self.logger.debug(f"Chassis rotation output: {output}")

                self.logger.info(f"Chassis rotation {direction_name} completed successfully")
                return True

            except asyncio.TimeoutError:
                self.logger.error(f"Chassis rotation timeout after {timeout}s")
                process.kill()
                await process.wait()
                return False

        except FileNotFoundError:
            self.logger.error(f"Chassis control script not found: {self._control_script}")
            return False
        except Exception as e:
            self.logger.error(f"Chassis rotation error: {e}", exc_info=True)
            return False
        finally:
            self._is_rotating = False

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
