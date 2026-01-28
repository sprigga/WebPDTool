"""
MODEL2306 Instrument Driver

Keysight 2306 Dual Channel Battery Simulator & DC Power Supply
Modern async driver implementation
"""
from typing import Dict, Any, Literal
from decimal import Decimal
from app.services.instruments.base import BaseInstrumentDriver


class MODEL2306Driver(BaseInstrumentDriver):
    """
    Driver for Keysight 2306 Dual Channel Power Supply

    Features:
    - Dual independent channels (1 & 2)
    - Voltage/Current setting per channel
    - Output enable/disable per channel
    - Voltage/Current measurement per channel
    """

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("MODEL2306 initialized")

    async def reset(self):
        """Reset the instrument - turn off all outputs"""
        await self.write_command('OUTP OFF')
        await self.write_command('OUTP2 OFF')
        self.logger.debug("MODEL2306 reset - all outputs off")

    async def set_voltage(self, voltage: float, channel: Literal['1', '2'] = '1') -> bool:
        """
        Set output voltage for specified channel

        Args:
            voltage: Voltage value to set
            channel: Channel number ('1' or '2')

        Returns:
            True if successful
        """
        if channel == '1':
            cmd = f"SOUR:VOLT {voltage}"
        else:
            cmd = f"SOUR2:VOLT {voltage}"

        await self.write_command(cmd)
        self.logger.debug(f"Set channel {channel} voltage to {voltage}V")
        return True

    async def set_current(self, current: float, channel: Literal['1', '2'] = '1') -> bool:
        """
        Set current limit for specified channel

        Args:
            current: Current limit value
            channel: Channel number ('1' or '2')

        Returns:
            True if successful
        """
        if channel == '1':
            cmd = f"SOUR:CURR:LIM {current}"
        else:
            cmd = f"SOUR2:CURR:LIM {current}"

        await self.write_command(cmd)
        self.logger.debug(f"Set channel {channel} current limit to {current}A")
        return True

    async def set_output(self, enabled: bool, channel: Literal['1', '2'] = '1') -> None:
        """
        Enable or disable output for specified channel

        Args:
            enabled: True to enable, False to disable
            channel: Channel number ('1' or '2')
        """
        state = 'ON' if enabled else 'OFF'
        if channel == '1':
            cmd = f"OUTP {state}"
        else:
            cmd = f"OUTP2 {state}"

        await self.write_command(cmd)
        self.logger.debug(f"Channel {channel} output {state}")

    async def measure_voltage(self, channel: Literal['1', '2'] = '1') -> Decimal:
        """
        Measure actual output voltage on specified channel

        Args:
            channel: Channel number ('1' or '2')

        Returns:
            Measured voltage value
        """
        if channel == '1':
            cmd = "MEAS:VOLT?"
        else:
            cmd = "MEAS2:VOLT?"

        return await self.query_decimal(cmd)

    async def measure_current(self, channel: Literal['1', '2'] = '1') -> Decimal:
        """
        Measure actual output current on specified channel

        Args:
            channel: Channel number ('1' or '2')

        Returns:
            Measured current value
        """
        if channel == '1':
            cmd = "MEAS:CURR?"
        else:
            cmd = "MEAS2:CURR?"

        return await self.query_decimal(cmd)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Channel: '1' or '2'
                - SetVolt: Voltage value to set
                - SetCurr: Current limit value to set

        Returns:
            '1' on success, error message on failure

        Special behavior:
            - If SetVolt='0' AND SetCurr='0', turns OFF the output
            - Otherwise, sets voltage/current and turns ON the output
        """
        from app.services.instruments.base import validate_required_params, get_param

        # Validate required parameters
        validate_required_params(params, ['Channel', 'SetVolt', 'SetCurr'])

        channel = str(params['Channel'])
        if channel not in ['1', '2']:
            raise ValueError(f"Invalid channel: {channel} (must be '1' or '2')")

        set_volt_str = str(params['SetVolt'])
        set_curr_str = str(params['SetCurr'])

        # Parse values
        try:
            set_volt = float(set_volt_str)
            set_curr = float(set_curr_str)
        except ValueError as e:
            raise ValueError(f"Invalid voltage or current value: {e}")

        try:
            # Special case: both zero means turn off
            if set_volt == 0 and set_curr == 0:
                await self.set_output(False, channel)
                self.logger.info(f"Channel {channel} turned OFF")
                return '1'

            # Normal case: set voltage, current, and turn on
            await self.set_voltage(set_volt, channel)
            await self.set_current(set_curr, channel)
            await self.set_output(True, channel)

            # Read back and verify (optional validation)
            # Note: In legacy script, this validation was commented out
            # We'll do basic validation here
            measured_volt = await self.measure_voltage(channel)
            measured_curr = await self.measure_current(channel)

            # Tolerance check (±5% for voltage, current may vary based on load)
            volt_tolerance = abs(set_volt * 0.05)
            if abs(float(measured_volt) - set_volt) > volt_tolerance:
                error_msg = f"2306 channel {channel} set volt fail"
                self.logger.warning(
                    f"{error_msg}: set={set_volt}V, measured={measured_volt}V"
                )
                return error_msg

            # Note: Current validation depends on load, so we only log it
            self.logger.info(
                f"Channel {channel} configured: V={measured_volt}V, I={measured_curr}A"
            )

            return '1'

        except Exception as e:
            error_msg = f"2306 channel {channel} set fail: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
