"""
Relay Controller Service
Manages relay switching for device testing
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from enum import IntEnum
import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)


class RelayState(IntEnum):
    """Relay state constants matching PDTool4"""
    SWITCH_OPEN = 0   # ON state
    SWITCH_CLOSED = 1  # OFF state


class RelayController:
    """
    Controls relay switching for DUT testing.
    Maps to PDTool4's MeasureSwitchON/OFF functionality.
    """

    def __init__(self, device_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize relay controller.

        Args:
            device_path: Path to relay control device (e.g., '/dev/ttyUSB0')
            config: Additional configuration parameters
        """
        self.device_path = device_path or "/dev/ttyUSB0"
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._current_state: Optional[RelayState] = None
        self._baud_rate = self.config.get("baud_rate", 115200)  # Default from PDTool4
        self._timeout = self.config.get("timeout", 1.0)

    async def set_relay_state(self, state: RelayState, channel: int = 1) -> bool:
        """
        Set relay to specified state.

        Args:
            state: RelayState.SWITCH_OPEN (0) or RelayState.SWITCH_CLOSED (1)
            channel: Relay channel number (default: 1)

        Returns:
            True if successful, False otherwise
        """
        try:
            state_name = "OPEN" if state == RelayState.SWITCH_OPEN else "CLOSED"
            self.logger.info(f"Setting relay channel {channel} to {state_name} (state={state})")

            # TODO: Implement actual relay control via serial port or other interface
            # ORIGINAL CODE (Simulated):
            # await asyncio.sleep(0.1)  # Simulate hardware delay
            #
            # NEW CODE: Real relay control via serial communication
            success = await self._send_relay_command(channel, state)

            if not success:
                self.logger.error(f"Failed to send relay command to channel {channel}")
                return False

            self._current_state = state
            self.logger.info(f"Relay channel {channel} set to {state_name} successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to set relay state: {e}", exc_info=True)
            return False

    async def _send_relay_command(self, channel: int, state: RelayState) -> bool:
        """
        Send relay command via serial port.
        Protocol based on PDTool4's ComportToRelay.py

        Args:
            channel: Relay channel number (1-16)
            state: RelayState.SWITCH_OPEN (ON) or RelayState.SWITCH_CLOSED (OFF)

        Returns:
            True if command sent successfully
        """
        try:
            # Build command string
            # Format: "<channel> <state>" where state is 'o' (on/open) or 'f' (off/closed)
            state_char = 'o' if state == RelayState.SWITCH_OPEN else 'f'
            command = f"{channel} {state_char} "

            self.logger.debug(f"Sending relay command: '{command}' to {self.device_path}")

            # Open serial port and send command
            # Using synchronous serial in thread to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self._send_serial_sync,
                command
            )

            return success

        except Exception as e:
            self.logger.error(f"Error sending relay command: {e}", exc_info=True)
            return False

    def _send_serial_sync(self, command: str) -> bool:
        """
        Synchronous serial communication (runs in executor).

        Args:
            command: Command string to send

        Returns:
            True if successful
        """
        ser = None
        try:
            # Open serial port
            ser = serial.Serial(
                port=self.device_path,
                baudrate=self._baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self._timeout
            )

            # Wait for Arduino to initialize (PDTool4 pattern)
            import time
            time.sleep(2)

            # Send command
            ser.write(command.encode('utf-8'))
            ser.flush()

            self.logger.info(f"Serial command sent successfully: {command.strip()}")
            return True

        except serial.SerialException as e:
            self.logger.error(f"Serial communication error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in serial communication: {e}", exc_info=True)
            return False
        finally:
            if ser and ser.is_open:
                ser.close()

    async def switch_on(self, channel: int = 1) -> bool:
        """
        Switch relay ON (OPEN state).
        Maps to PDTool4's MeasureSwitchON.

        Args:
            channel: Relay channel number

        Returns:
            True if successful
        """
        return await self.set_relay_state(RelayState.SWITCH_OPEN, channel)

    async def switch_off(self, channel: int = 1) -> bool:
        """
        Switch relay OFF (CLOSED state).
        Maps to PDTool4's MeasureSwitchOFF.

        Args:
            channel: Relay channel number

        Returns:
            True if successful
        """
        return await self.set_relay_state(RelayState.SWITCH_CLOSED, channel)

    async def get_current_state(self) -> Optional[RelayState]:
        """
        Get current relay state.

        Returns:
            Current RelayState or None if unknown
        """
        return self._current_state

    async def reset(self, channel: int = 1) -> bool:
        """
        Reset relay to default state (CLOSED/OFF).

        Args:
            channel: Relay channel number

        Returns:
            True if successful
        """
        self.logger.info(f"Resetting relay channel {channel}")
        return await self.switch_off(channel)


# Global relay controller instance
_relay_controller_instance: Optional[RelayController] = None


def get_relay_controller(
    device_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> RelayController:
    """
    Get or create global relay controller instance.

    Args:
        device_path: Device path for relay control
        config: Configuration parameters

    Returns:
        RelayController instance
    """
    global _relay_controller_instance

    if _relay_controller_instance is None:
        _relay_controller_instance = RelayController(device_path, config)

    return _relay_controller_instance
