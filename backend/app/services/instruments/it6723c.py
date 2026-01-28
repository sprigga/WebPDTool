"""
IT6723C Instrument Driver

ITECH IT6723C Programmable DC Power Supply
Modern async driver implementation
"""
from typing import Dict, Any
from decimal import Decimal
from app.services.instruments.base import BaseInstrumentDriver


class IT6723CDriver(BaseInstrumentDriver):
    """
    Driver for ITECH IT6723C Programmable DC Power Supply

    Features:
    - Voltage/Current setting
    - Output enable/disable
    - Voltage/Current measurement
    - High power capability (up to 150V, 10A, 1200W typical specs)
    """

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("IT6723C initialized")

    async def reset(self):
        """Reset the instrument - turn off output"""
        await self.write_command('OUTP OFF')
        self.logger.debug("IT6723C reset - output off")

    async def set_voltage(self, voltage: float) -> bool:
        """
        Set output voltage

        Args:
            voltage: Voltage value to set (in volts)

        Returns:
            True if successful
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
            # Tolerance: ±1% for voltage (stricter than MODEL2306)
            volt_tolerance = abs(set_volt * 0.01) if set_volt > 0 else 0.01
            if abs(float(measured_volt) - set_volt) > volt_tolerance:
                error_msg = "IT6723C set volt fail"
                self.logger.warning(
                    f"{error_msg}: set={set_volt}V, measured={measured_volt}V, "
                    f"tolerance={volt_tolerance}V"
                )
                return error_msg

            # Current validation (depends on load, less strict)
            # We'll just log it for monitoring
            self.logger.info(
                f"IT6723C configured: V={measured_volt}V, I={measured_curr}A "
                f"(set: V={set_volt}V, I={set_curr}A)"
            )

            return '1'

        except Exception as e:
            error_msg = f"IT6723C set fail: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
