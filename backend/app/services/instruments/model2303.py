"""
Keysight MODEL2303 Dual-Channel Power Supply Driver

Refactored from PDTool4's 2303_test.py
Supports:
- Voltage and current setting
- Output enable/disable
- Measurement readback
"""
from typing import Dict, Any
from decimal import Decimal
import asyncio

from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class MODEL2303Driver(BaseInstrumentDriver):
    """
    Keysight MODEL2303 Dual-Channel Power Supply Driver

    Features:
    - Dual channel output
    - Voltage range: 0-20V
    - Current range: 0-3A
    - Measurement readback for verification
    """

    async def initialize(self):
        """Initialize power supply"""
        # Turn off output initially
        await self.set_output(False)
        self.logger.info(f"MODEL2303 {self.instrument_id} initialized")

    async def reset(self):
        """Reset power supply (called during cleanup)"""
        await self.set_output(False)
        self.logger.info(f"MODEL2303 {self.instrument_id} output disabled")

    # ========================================================================
    # Voltage and Current Control
    # ========================================================================

    async def set_voltage(self, voltage: float) -> bool:
        """
        Set output voltage

        Args:
            voltage: Voltage in volts (0-20V)

        Returns:
            True if set successfully
        """
        if not 0 <= voltage <= 20:
            raise ValueError(f"Voltage must be 0-20V, got {voltage}V")

        await self.write_command(f"VOLT {voltage}")
        await asyncio.sleep(0.1)

        # Verify
        measured = await self.measure_voltage()
        success = abs(measured - Decimal(str(voltage))) < Decimal('0.1')

        if success:
            self.logger.info(f"Set voltage: {voltage}V (measured: {measured}V)")
        else:
            self.logger.warning(f"Voltage mismatch: set {voltage}V, measured {measured}V")

        return success

    async def set_current(self, current: float) -> bool:
        """
        Set output current limit

        Args:
            current: Current in amperes (0-3A)

        Returns:
            True if set successfully
        """
        if not 0 <= current <= 3:
            raise ValueError(f"Current must be 0-3A, got {current}A")

        await self.write_command(f"CURR {current}")
        await asyncio.sleep(0.1)

        # Verify
        measured = await self.measure_current()
        success = abs(measured - Decimal(str(current))) < Decimal('0.1')

        if success:
            self.logger.info(f"Set current: {current}A (measured: {measured}A)")
        else:
            self.logger.warning(f"Current mismatch: set {current}A, measured {measured}A")

        return success

    async def set_output(self, enabled: bool) -> None:
        """
        Enable or disable output

        Args:
            enabled: True to enable, False to disable
        """
        cmd = "OUTP ON" if enabled else "OUTP OFF"
        await self.write_command(cmd)

        state = "enabled" if enabled else "disabled"
        self.logger.info(f"Output {state}")

    # ========================================================================
    # Measurements
    # ========================================================================

    async def measure_voltage(self) -> Decimal:
        """
        Measure output voltage

        Returns:
            Measured voltage in volts
        """
        response = await self.query_command("MEAS:VOLT:DC?")
        value = Decimal(response)
        return round(value, 2)

    async def measure_current(self) -> Decimal:
        """
        Measure output current

        Returns:
            Measured current in amperes
        """
        response = await self.query_command("MEAS:CURR:DC?")
        value = Decimal(response)
        return round(value, 2)

    # ========================================================================
    # High-Level API (compatible with PDTool4 parameter format)
    # ========================================================================

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute command based on PDTool4 parameter format

        Expected parameters:
        - SetVolt: Target voltage (V)
        - SetCurr: Target current (A)

        Returns:
            '1' if successful, error message otherwise
        """
        # Validate required parameters
        is_valid, error = validate_required_params(params, ['SetVolt', 'SetCurr'])
        if not is_valid:
            raise ValueError(error)

        set_volt = float(get_param(params, 'SetVolt', 'set_volt'))
        set_curr = float(get_param(params, 'SetCurr', 'set_curr'))

        # Set voltage and current
        volt_ok = await self.set_voltage(set_volt)
        curr_ok = await self.set_current(set_curr)

        # Enable output
        await self.set_output(True)

        # Check results
        errors = []
        if not volt_ok:
            errors.append('volt')
        if not curr_ok:
            errors.append('curr')

        if not errors:
            return '1'
        else:
            return f"2303 set {' and '.join(errors)} fail"
