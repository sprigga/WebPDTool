"""
34970A Instrument Driver

Keysight 34970A Data Acquisition/Switch Unit
Modern async driver implementation
"""
from typing import Dict, Any, Literal, List
from decimal import Decimal
from app.services.instruments.base import BaseInstrumentDriver


class A34970ADriver(BaseInstrumentDriver):
    """
    Driver for Keysight 34970A Data Acquisition/Switch Unit

    Supports:
    - Channel switching (OPEN/CLOSE)
    - Voltage/Current measurements (AC/DC)
    - Resistance measurements (2-wire/4-wire)
    - Capacitance, Frequency, Period measurements
    - Diode, Temperature measurements
    """

    # Channel validation rules
    CURRENT_CHANNELS = ['21', '22']  # Only channels 21, 22 support current measurement
    VALID_CHANNELS = [f'{i:02d}' for i in range(1, 21)]  # Channels 01-20

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("34970A initialized")

    async def reset(self):
        """Reset the instrument to default state"""
        await self.write_command('*RST')
        self.logger.debug("34970A reset")

    def _validate_channels(self, channels: List[str], command: str) -> None:
        """
        Validate channel numbers for specific commands

        Args:
            channels: List of channel numbers (as strings)
            command: Command type (e.g., 'CURR', 'VOLT')

        Raises:
            ValueError: If channels are invalid for the command
        """
        if command == 'CURR':
            # Current measurements only on channels 21, 22
            invalid = [ch for ch in channels if ch not in self.CURRENT_CHANNELS]
            if invalid:
                raise ValueError(
                    f"Current measurement only supported on channels {self.CURRENT_CHANNELS}, "
                    f"got invalid channels: {invalid}"
                )

    def _parse_channel_spec(self, channel_spec: Any) -> List[str]:
        """
        Parse channel specification to list of channel strings

        Args:
            channel_spec: Can be:
                - String: "101,102,103" or "101"
                - Tuple: (101, 102, 103)
                - List: [101, 102, 103]

        Returns:
            List of channel strings: ['01', '02', '03']
        """
        if isinstance(channel_spec, str):
            # String format: "101,102,103" or "101"
            channels = [ch.strip() for ch in channel_spec.split(',')]
        elif isinstance(channel_spec, (tuple, list)):
            # Tuple/List format: (101, 102, 103)
            channels = [str(ch) for ch in channel_spec]
        else:
            channels = [str(channel_spec)]

        # Normalize to 2-digit format (e.g., "1" -> "01", "101" -> "01")
        # Remove leading '1' if present (slot number in 3-digit format)
        normalized = []
        for ch in channels:
            ch = ch.strip()
            if len(ch) == 3 and ch.startswith('1'):
                ch = ch[1:]  # "101" -> "01"
            normalized.append(ch.zfill(2))  # Ensure 2 digits

        return normalized

    async def open_channels(self, channels: List[str]) -> str:
        """
        Open (disconnect) specified channels

        Args:
            channels: List of channel numbers

        Returns:
            Query response from instrument
        """
        channel_list = ','.join(channels)
        cmd = f"ROUT:OPEN (@{channel_list})"
        await self.write_command(cmd)

        # Query to confirm
        response = await self.query_command(f"ROUT:OPEN? (@{channel_list})")
        self.logger.debug(f"Opened channels {channel_list}: {response}")
        return response

    async def close_channels(self, channels: List[str]) -> str:
        """
        Close (connect) specified channels

        Args:
            channels: List of channel numbers

        Returns:
            Query response from instrument
        """
        channel_list = ','.join(channels)
        cmd = f"ROUT:CLOS (@{channel_list})"
        await self.write_command(cmd)

        # Query to confirm
        response = await self.query_command(f"ROUT:CLOS? (@{channel_list})")
        self.logger.debug(f"Closed channels {channel_list}: {response}")
        return response

    async def measure_voltage(
        self,
        channels: List[str],
        type: Literal['AC', 'DC'] = 'DC'
    ) -> Decimal:
        """
        Measure voltage on specified channels

        Args:
            channels: List of channel numbers
            type: AC or DC measurement

        Returns:
            Measured voltage value
        """
        channel_list = ','.join(channels)
        cmd = f"MEAS:VOLT:{type}? (@{channel_list})"
        response = await self.query_command(cmd)
        return await self.query_decimal(cmd)

    async def measure_current(
        self,
        channels: List[str],
        type: Literal['AC', 'DC'] = 'DC'
    ) -> Decimal:
        """
        Measure current on specified channels

        Args:
            channels: List of channel numbers (must be 21 or 22)
            type: AC or DC measurement

        Returns:
            Measured current value
        """
        # Validate channels
        self._validate_channels(channels, 'CURR')

        channel_list = ','.join(channels)
        cmd = f"MEAS:CURR:{type}? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_resistance(
        self,
        channels: List[str],
        four_wire: bool = False
    ) -> Decimal:
        """
        Measure resistance on specified channels

        Args:
            channels: List of channel numbers
            four_wire: Use 4-wire (FRES) or 2-wire (RES) measurement

        Returns:
            Measured resistance value
        """
        channel_list = ','.join(channels)
        cmd_type = 'FRES' if four_wire else 'RES'
        cmd = f"MEAS:{cmd_type}? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_capacitance(self, channels: List[str]) -> Decimal:
        """Measure capacitance on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:CAP? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_frequency(self, channels: List[str]) -> Decimal:
        """Measure frequency on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:FREQ? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_period(self, channels: List[str]) -> Decimal:
        """Measure period on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:PER? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_diode(self, channels: List[str]) -> Decimal:
        """Measure diode voltage on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:DIOD? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_temperature(self, channels: List[str]) -> Decimal:
        """Measure temperature on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:TEMP? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Item: Command type (OPEN, CLOS, VOLT, CURR, etc.)
                - Channel: Channel specification (string, tuple, or list)
                - Type: AC/DC type (optional, for VOLT/CURR)

        Returns:
            String result (for backward compatibility)
        """
        from app.services.instruments.base import validate_required_params, get_param

        # Validate required parameters
        validate_required_params(params, ['Item', 'Channel'])

        item = params['Item'].upper()
        channel_spec = params['Channel']
        # Type is optional - only required for VOLT/CURR measurements
        type_ = get_param(params, 'Type', 'DC')
        if type_ is not None:
            type_ = type_.upper()
        else:
            type_ = 'DC'

        # Parse channel specification
        channels = self._parse_channel_spec(channel_spec)

        # Execute command based on item type
        if item == 'OPEN':
            result = await self.open_channels(channels)
            return str(result) if result is not None else '0'

        elif item == 'CLOS':
            result = await self.close_channels(channels)
            return str(result) if result is not None else '0'

        elif item == 'VOLT':
            if type_ not in ['AC', 'DC']:
                raise ValueError(f"Invalid voltage type: {type_} (must be AC or DC)")
            value = await self.measure_voltage(channels, type_)
            return f'{value:.3f}'

        elif item == 'CURR':
            if type_ not in ['AC', 'DC']:
                raise ValueError(f"Invalid current type: {type_} (must be AC or DC)")
            value = await self.measure_current(channels, type_)
            return f'{value:.3f}'

        elif item == 'RES':
            value = await self.measure_resistance(channels, four_wire=False)
            return f'{value:.3f}'

        elif item == 'FRES':
            value = await self.measure_resistance(channels, four_wire=True)
            return f'{value:.3f}'

        elif item == 'CAP':
            value = await self.measure_capacitance(channels)
            return f'{value:.3e}'

        elif item == 'FREQ':
            value = await self.measure_frequency(channels)
            return f'{value:.3f}'

        elif item == 'PER':
            value = await self.measure_period(channels)
            return f'{value:.3e}'

        elif item == 'DIOD':
            value = await self.measure_diode(channels)
            return f'{value:.3f}'

        elif item == 'TEMP':
            value = await self.measure_temperature(channels)
            return f'{value:.2f}'

        else:
            raise ValueError(f"Unknown command: {item}")
