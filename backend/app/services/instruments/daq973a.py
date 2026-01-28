"""
Keysight DAQ973A Data Acquisition System Driver

Refactored from PDTool4's DAQ973A_test.py
Supports:
- Channel switching (OPEN/CLOSE)
- Voltage measurement (AC/DC)
- Current measurement (AC/DC)
- Resistance, capacitance, frequency, temperature measurement
"""
from typing import Dict, Any, Optional, Literal
from decimal import Decimal
import asyncio

from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class DAQ973ADriver(BaseInstrumentDriver):
    """
    Keysight DAQ973A Data Acquisition System Driver

    Channels:
    - 101-120: General purpose channels
    - 121-122: Current measurement channels
    """

    # Supported measurement types
    MEASUREMENT_TYPES = {
        'VOLT': ['AC', 'DC'],
        'CURR': ['AC', 'DC'],
        'RES': [],
        'FRES': [],
        'DIOD': [],
        'CAP': [],
        'FREQ': [],
        'PER': [],
        'TEMP': [],
    }

    # Channel validation
    CURRENT_CHANNELS = ['121', '122']  # Only these channels support current measurement

    async def initialize(self):
        """Initialize DAQ973A to known state"""
        await self.reset()

    async def reset(self):
        """Reset instrument to default state"""
        await self.write_command('*RST')
        await asyncio.sleep(0.5)
        self.logger.info(f"DAQ973A {self.instrument_id} reset complete")

    # ========================================================================
    # Channel Control
    # ========================================================================

    async def open_channels(self, channels: list[str]) -> bool:
        """
        Open relay channels

        Args:
            channels: List of channel numbers (e.g., ['101', '102'])

        Returns:
            True if successful
        """
        if not channels:
            raise ValueError("No channels specified")

        channel_str = ','.join(channels)
        open_cmd = f"ROUT:OPEN (@{channel_str})"
        check_cmd = f"ROUT:OPEN? (@{channel_str})"

        await self.write_command(open_cmd)
        await asyncio.sleep(0.1)

        # Verify
        response = await self.query_command(check_cmd)
        success = '1' in response

        if success:
            self.logger.info(f"Opened channels: {channel_str}")
        else:
            self.logger.warning(f"Failed to open channels: {channel_str}")

        return success

    async def close_channels(self, channels: list[str]) -> bool:
        """
        Close relay channels

        Args:
            channels: List of channel numbers (e.g., ['101', '102'])

        Returns:
            True if successful
        """
        if not channels:
            raise ValueError("No channels specified")

        channel_str = ','.join(channels)
        close_cmd = f"ROUT:CLOS (@{channel_str})"
        check_cmd = f"ROUT:CLOS? (@{channel_str})"

        await self.write_command(close_cmd)
        await asyncio.sleep(0.1)

        # Verify
        response = await self.query_command(check_cmd)
        success = '1' in response

        if success:
            self.logger.info(f"Closed channels: {channel_str}")
        else:
            self.logger.warning(f"Failed to close channels: {channel_str}")

        return success

    # ========================================================================
    # Measurements
    # ========================================================================

    async def measure_voltage(
        self,
        channels: list[str],
        type: Literal['AC', 'DC'] = 'DC'
    ) -> Decimal:
        """
        Measure voltage on specified channels

        Args:
            channels: List of channel numbers
            type: 'AC' or 'DC'

        Returns:
            Measured voltage value
        """
        if not channels:
            raise ValueError("No channels specified")

        channel_str = ','.join(channels)
        cmd = f"MEAS:VOLT:{type}? (@{channel_str})"

        response = await self.query_command(cmd)
        value = Decimal(response)

        self.logger.info(f"Voltage measurement ({type}): {value}V on channels {channel_str}")
        return value

    async def measure_current(
        self,
        channels: list[str],
        type: Literal['AC', 'DC'] = 'DC'
    ) -> Decimal:
        """
        Measure current on specified channels

        Args:
            channels: List of channel numbers (must be 121 or 122)
            type: 'AC' or 'DC'

        Returns:
            Measured current value
        """
        if not channels:
            raise ValueError("No channels specified")

        # Validate current channels
        invalid = [ch for ch in channels if ch not in self.CURRENT_CHANNELS]
        if invalid:
            raise ValueError(
                f"Invalid current measurement channels: {invalid}. "
                f"Only channels {self.CURRENT_CHANNELS} support current measurement."
            )

        channel_str = ','.join(channels)
        cmd = f"MEAS:CURR:{type}? (@{channel_str})"

        response = await self.query_command(cmd)
        value = Decimal(response)

        self.logger.info(f"Current measurement ({type}): {value}A on channels {channel_str}")
        return value

    async def measure_resistance(self, channels: list[str]) -> Decimal:
        """Measure 2-wire resistance"""
        channel_str = ','.join(channels)
        cmd = f"MEAS:RES? (@{channel_str})"
        response = await self.query_command(cmd)
        return Decimal(response)

    async def measure_fresistance(self, channels: list[str]) -> Decimal:
        """Measure 4-wire resistance"""
        channel_str = ','.join(channels)
        cmd = f"MEAS:FRES? (@{channel_str})"
        response = await self.query_command(cmd)
        return Decimal(response)

    async def measure_capacitance(self, channels: list[str]) -> Decimal:
        """Measure capacitance"""
        channel_str = ','.join(channels)
        cmd = f"MEAS:CAP? (@{channel_str})"
        response = await self.query_command(cmd)
        return Decimal(response)

    async def measure_frequency(self, channels: list[str]) -> Decimal:
        """Measure frequency"""
        channel_str = ','.join(channels)
        cmd = f"MEAS:FREQ? (@{channel_str})"
        response = await self.query_command(cmd)
        return Decimal(response)

    async def measure_period(self, channels: list[str]) -> Decimal:
        """Measure period"""
        channel_str = ','.join(channels)
        cmd = f"MEAS:PER? (@{channel_str})"
        response = await self.query_command(cmd)
        return Decimal(response)

    async def measure_diode(self, channels: list[str]) -> Decimal:
        """Measure diode voltage"""
        channel_str = ','.join(channels)
        cmd = f"MEAS:DIOD? (@{channel_str})"
        response = await self.query_command(cmd)
        return Decimal(response)

    async def measure_temperature(self, channels: list[str]) -> Decimal:
        """
        Measure temperature

        Note: Temperature measurement may require settling time
        """
        channel_str = ','.join(channels)
        cmd = f"MEAS:TEMP? (@{channel_str})"

        # First query to trigger measurement
        await self.query_command(cmd)
        await asyncio.sleep(2)  # Wait for temperature sensor to settle

        # Second query to get stable reading
        response = await self.query_command(cmd)
        return Decimal(response)

    # ========================================================================
    # High-Level API (compatible with PDTool4 parameter format)
    # ========================================================================

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute command based on PDTool4 parameter format

        Expected parameters:
        - Item: Command type (OPEN, CLOS, VOLT, CURR, RES, etc.)
        - Channel: Channel number(s)
        - Type: Measurement type (AC, DC) - optional

        Returns:
            String result for compatibility
        """
        # Validate required parameters
        is_valid, error = validate_required_params(params, ['Item', 'Channel'])
        if not is_valid:
            raise ValueError(error)

        item = get_param(params, 'Item', 'item')
        channel = get_param(params, 'Channel', 'channel')
        type_ = get_param(params, 'Type', 'type', default=None)

        # Parse channels
        channels = self._parse_channels(channel)

        # Execute based on item type
        if item == 'OPEN':
            success = await self.open_channels(channels)
            return '1' if success else '0'

        elif item == 'CLOS':
            success = await self.close_channels(channels)
            return '1' if success else '0'

        elif item == 'VOLT':
            if type_ is None:
                raise ValueError("Type (AC/DC) required for voltage measurement")
            value = await self.measure_voltage(channels, type_)
            return f'{value:.3f}'

        elif item == 'CURR':
            if type_ is None:
                raise ValueError("Type (AC/DC) required for current measurement")
            value = await self.measure_current(channels, type_)
            return f'{value:.3f}'

        elif item == 'RES':
            value = await self.measure_resistance(channels)
            return f'{value:.3f}'

        elif item == 'FRES':
            value = await self.measure_fresistance(channels)
            return f'{value:.3f}'

        elif item == 'CAP':
            value = await self.measure_capacitance(channels)
            return f'{value:.3f}'

        elif item == 'FREQ':
            value = await self.measure_frequency(channels)
            return f'{value:.3f}'

        elif item == 'PER':
            value = await self.measure_period(channels)
            return f'{value:.3f}'

        elif item == 'DIOD':
            value = await self.measure_diode(channels)
            return f'{value:.3f}'

        elif item == 'TEMP':
            value = await self.measure_temperature(channels)
            return f'{value:.3f}'

        else:
            raise ValueError(f"Unknown command: {item}")

    def _parse_channels(self, channel_input: Any) -> list[str]:
        """
        Parse channel input to list of channel numbers

        Supports:
        - Single channel: '101'
        - Multiple channels: '(101, 102, 103)'
        - List: ['101', '102']
        """
        if isinstance(channel_input, list):
            return [str(ch) for ch in channel_input]

        channel_str = str(channel_input).strip()

        # Remove parentheses if present
        if channel_str.startswith('(') and channel_str.endswith(')'):
            channel_str = channel_str[1:-1]

        # Split by comma
        channels = [ch.strip() for ch in channel_str.split(',')]

        return channels
