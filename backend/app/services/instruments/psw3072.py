"""
PSW3072 Instrument Driver

GW Instek PSW3072 Triple Output Power Supply
Modern async driver implementation
"""
from typing import Dict, Any
from decimal import Decimal
from app.services.instruments.base import BaseInstrumentDriver


class PSW3072Driver(BaseInstrumentDriver):
    """
    Driver for GW Instek PSW3072 Triple Output Power Supply

    Supports:
    - Voltage setting (0-30V per channel)
    - Current limiting (0-3A per channel)
    - Output enable/disable per channel
    - Three independent channels

    Note: PSW3072 uses direct ASCII serial commands (not SCPI)
    """

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("PSW3072 initialized")

    async def reset(self):
        """Reset the instrument - turn off all outputs"""
        # Turn off all three channels
        for channel in [1, 2, 3]:
            await self.set_output(False, channel)
        self.logger.debug("PSW3072 reset - all outputs OFF")

    async def set_voltage(self, voltage: float, channel: int = 1) -> None:
        """
        Set voltage for specified channel

        Args:
            voltage: Voltage value (0-30V)
            channel: Channel number (1, 2, or 3)

        Raises:
            ValueError: If voltage or channel is out of range
        """
        if not 1 <= channel <= 3:
            raise ValueError(f"Invalid channel: {channel} (must be 1, 2, or 3)")

        if not 0 <= voltage <= 30:
            raise ValueError(f"Invalid voltage: {voltage}V (must be 0-30V)")

        # PSW3072 uses direct ASCII commands
        cmd = f"VOLT{channel} {voltage:.2f}"
        await self.write_command(cmd)

        # Add delay for command processing (legacy compatibility)
        import asyncio
        await asyncio.sleep(0.1)

        self.logger.debug(f"Set channel {channel} voltage to {voltage}V")

    async def set_current(self, current: float, channel: int = 1) -> None:
        """
        Set current limit for specified channel

        Args:
            current: Current limit (0-3A)
            channel: Channel number (1, 2, or 3)

        Raises:
            ValueError: If current or channel is out of range
        """
        if not 1 <= channel <= 3:
            raise ValueError(f"Invalid channel: {channel} (must be 1, 2, or 3)")

        if not 0 <= current <= 3:
            raise ValueError(f"Invalid current: {current}A (must be 0-3A)")

        # PSW3072 uses direct ASCII commands
        cmd = f"CURR{channel} {current:.2f}"
        await self.write_command(cmd)

        # Add delay for command processing (legacy compatibility)
        import asyncio
        await asyncio.sleep(0.1)

        self.logger.debug(f"Set channel {channel} current limit to {current}A")

    async def set_output(self, enabled: bool, channel: int = 1) -> None:
        """
        Enable or disable output for specified channel

        Args:
            enabled: True to enable output, False to disable
            channel: Channel number (1, 2, or 3)

        Raises:
            ValueError: If channel is out of range
        """
        if not 1 <= channel <= 3:
            raise ValueError(f"Invalid channel: {channel} (must be 1, 2, or 3)")

        # PSW3072 uses direct ASCII commands
        state = 'ON' if enabled else 'OFF'
        cmd = f"OUTP{channel} {state}"
        await self.write_command(cmd)

        # Add delay for command processing (legacy compatibility)
        import asyncio
        await asyncio.sleep(0.1)

        self.logger.debug(f"Channel {channel} output {'enabled' if enabled else 'disabled'}")

    async def measure_voltage(self, channel: int = 1) -> Decimal:
        """
        Measure voltage on specified channel

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            Measured voltage value
        """
        if not 1 <= channel <= 3:
            raise ValueError(f"Invalid channel: {channel} (must be 1, 2, or 3)")

        cmd = f"MEAS:VOLT? CH{channel}"
        return await self.query_decimal(cmd)

    async def measure_current(self, channel: int = 1) -> Decimal:
        """
        Measure current on specified channel

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            Measured current value
        """
        if not 1 <= channel <= 3:
            raise ValueError(f"Invalid channel: {channel} (must be 1, 2, or 3)")

        cmd = f"MEAS:CURR? CH{channel}"
        return await self.query_decimal(cmd)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - SetVolt: Voltage setting (numeric string)
                - SetCurr: Current limit (numeric string)
                - Channel: Channel number (optional, defaults to 1)

        Returns:
            String result (for backward compatibility)
            - '1' on success
            - Error message string on failure

        Special behavior:
            - SetVolt='0' AND SetCurr='0' → Turn OFF output
            - Otherwise → Set voltage, current, turn ON output
        """
        from app.services.instruments.base import validate_required_params, get_param

        # Validate required parameters
        validate_required_params(params, ['SetVolt', 'SetCurr'])

        # Parse parameters
        set_volt = float(params['SetVolt'])
        set_curr = float(params['SetCurr'])
        channel = int(get_param(params, 'Channel', 1))

        # Validate channel
        if not 1 <= channel <= 3:
            return f"PSW3072 invalid channel: {channel} (must be 1, 2, or 3)"

        try:
            # Special case: both zero means turn off output
            if set_volt == 0 and set_curr == 0:
                await self.set_output(False, channel)
                self.logger.info(f"Channel {channel} turned OFF")
                return '1'

            # Normal case: set voltage, current, and turn on
            await self.set_voltage(set_volt, channel)
            await self.set_current(set_curr, channel)
            await self.set_output(True, channel)

            self.logger.info(f"Channel {channel} set to {set_volt}V, {set_curr}A limit, output ON")
            return '1'

        except ValueError as e:
            error_msg = f"PSW3072 parameter error: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"PSW3072 command failed: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
