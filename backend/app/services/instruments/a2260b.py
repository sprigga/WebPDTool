"""
2260B Instrument Driver

Keithley 2260B Programmable DC Power Supply
Modern async driver implementation
"""
from typing import Dict, Any
from decimal import Decimal
from app.services.instruments.base import BaseInstrumentDriver


class A2260BDriver(BaseInstrumentDriver):
    """
    Driver for Keithley 2260B Programmable DC Power Supply

    Features:
    - Voltage/Current setting (supports up to 105% of rated voltage)
    - Output enable/disable
    - Voltage/Current measurement
    - High precision and low noise
    """

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("2260B initialized")

    async def reset(self):
        """Reset the instrument - turn off output"""
        await self.write_command('OUTP OFF')
        self.logger.debug("2260B reset - output off")

    async def set_voltage(self, voltage: float) -> bool:
        """
        Set output voltage

        Args:
            voltage: Voltage value to set (in volts)
                     Can be set to 105% of rated voltage

        Returns:
            True if successful

        Note:
            Full command is SOUR:VOLT:LEV:IMM:AMPL <value>
            Simplified command is VOLT <value>
        """
        cmd = f"VOLT {voltage}"
        await self.write_command(cmd)
        self.logger.debug(f"Set voltage to {voltage}V")
        return True

    async def set_current(self, current: float) -> bool:
        """
        Set current limit

        Args:
            current: Current limit value (in amperes)

        Returns:
            True if successful
        """
        cmd = f"CURR {current}"
        await self.write_command(cmd)
        self.logger.debug(f"Set current limit to {current}A")
        return True

    async def set_output(self, enabled: bool) -> None:
        """
        Enable or disable output

        Args:
            enabled: True to enable, False to disable
        """
        state = 'ON' if enabled else 'OFF'
        cmd = f"OUTP {state}"
        await self.write_command(cmd)
        self.logger.debug(f"Output {state}")

    async def measure_voltage(self) -> Decimal:
        """
        Measure actual output voltage

        Returns:
            Measured voltage value
        """
        cmd = "MEAS:VOLT:DC?"
        return await self.query_decimal(cmd)

    async def measure_current(self) -> Decimal:
        """
        Measure actual output current

        Returns:
            Measured current value
        """
        cmd = "MEAS:CURR:DC?"
        return await self.query_decimal(cmd)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - SetVolt: Voltage value to set
                - SetCurr: Current limit value to set

        Returns:
            '1' on success, error message on failure
        """
        from app.services.instruments.base import validate_required_params

        # Validate required parameters
        validate_required_params(params, ['SetVolt', 'SetCurr'])

        set_volt_str = str(params['SetVolt'])
        set_curr_str = str(params['SetCurr'])

        # Parse values
        try:
            set_volt = float(set_volt_str)
            set_curr = float(set_curr_str)
        except ValueError as e:
            raise ValueError(f"Invalid voltage or current value: {e}")

        try:
            # Set voltage and current
            await self.set_voltage(set_volt)
            await self.set_current(set_curr)

            # Enable output
            await self.set_output(True)

            # Read back and verify
            measured_volt = await self.measure_voltage()
            measured_curr = await self.measure_current()

            # Validation: compare set and measured values
            # Legacy script rounds to 2 decimal places for comparison
            measured_volt_rounded = round(float(measured_volt), 2)
            set_volt_rounded = round(set_volt, 2)

            if measured_volt_rounded != set_volt_rounded:
                error_msg = "2260B set volt fail"
                self.logger.warning(
                    f"{error_msg}: set={set_volt_rounded}V, measured={measured_volt_rounded}V"
                )
                return error_msg

            # Current validation (depends on load)
            # Legacy script also checks current, but it depends on load
            # We'll log it for monitoring but not fail on mismatch
            measured_curr_rounded = round(float(measured_curr), 2)
            set_curr_rounded = round(set_curr, 2)

            if measured_curr_rounded != set_curr_rounded:
                self.logger.info(
                    f"Current mismatch (may be due to load): "
                    f"set={set_curr_rounded}A, measured={measured_curr_rounded}A"
                )

            self.logger.info(
                f"2260B configured: V={measured_volt_rounded}V, I={measured_curr_rounded}A "
                f"(set: V={set_volt_rounded}V, I={set_curr_rounded}A)"
            )

            return '1'

        except Exception as e:
            error_msg = f"2260B set fail: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
