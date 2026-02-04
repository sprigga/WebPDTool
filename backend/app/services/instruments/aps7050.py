"""
APS7050 Instrument Driver

GW Instek APS-7000 Series Programmable AC/DC Power Source
with built-in DMM and relay control
"""
from typing import Dict, Any, Literal, List
from decimal import Decimal
import asyncio
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class APS7050Driver(BaseInstrumentDriver):
    """
    Driver for GW Instek APS-7000 Series Power Source with DMM

    Supports:
    - AC/DC voltage/current measurements
    - Relay switching (OPEN/CLOSE)
    - Resistance, capacitance, frequency, period measurements
    - Diode and temperature measurements
    - Raw SCPI command execution (unique to APS7050)
    """

    # Channel validation rules
    CURRENT_CHANNELS = ['21', '22']  # Only channels 21, 22 support current measurement
    VALID_CHANNELS = [f'{i:02d}' for i in range(1, 21)]  # Channels 01-20
    RELAY_CHANNELS = [f'{i:02d}' for i in range(1, 21)]  # Relay channels 01-20

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("APS7050 initialized")

    async def reset(self):
        """Reset the instrument to default state"""
        await self.write_command('*RST')
        await asyncio.sleep(0.5)
        self.logger.debug("APS7050 reset")

    def _validate_channels(self, channels: List[str], command: str) -> None:
        """Validate channel numbers for specific commands"""
        if command == 'CURR':
            invalid = [ch for ch in channels if ch not in self.CURRENT_CHANNELS]
            if invalid:
                raise ValueError(
                    f"Current measurement only on channels {self.CURRENT_CHANNELS}, "
                    f"got invalid: {invalid}"
                )

    def _parse_channel_spec(self, channel_spec: Any) -> List[str]:
        """Parse channel specification to list of channel strings"""
        if isinstance(channel_spec, str):
            channels = [ch.strip() for ch in channel_spec.split(',')]
        elif isinstance(channel_spec, (tuple, list)):
            channels = [str(ch) for ch in channel_spec]
        else:
            channels = [str(channel_spec)]

        normalized = []
        for ch in channels:
            ch = ch.strip()
            if len(ch) == 3 and ch.startswith('1'):
                ch = ch[1:]  # "101" -> "01"
            normalized.append(ch.zfill(2))  # Ensure 2 digits
        return normalized

    async def open_channels(self, channels: List[str]) -> str:
        """Open (disconnect) specified relay channels"""
        channel_list = ','.join(channels)
        cmd = f"ROUT:OPEN (@{channel_list})"
        await self.write_command(cmd)
        response = await self.query_command(f"ROUT:OPEN? (@{channel_list})")
        self.logger.debug(f"Opened channels {channel_list}: {response}")
        return response

    async def close_channels(self, channels: List[str]) -> str:
        """Close (connect) specified relay channels"""
        channel_list = ','.join(channels)
        cmd = f"ROUT:CLOS (@{channel_list})"
        await self.write_command(cmd)
        response = await self.query_command(f"ROUT:CLOS? (@{channel_list})")
        self.logger.debug(f"Closed channels {channel_list}: {response}")
        return response

    async def measure_voltage(
        self,
        channels: List[str],
        type: Literal['AC', 'DC'] = 'DC'
    ) -> Decimal:
        """Measure voltage on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:VOLT:{type}? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_current(
        self,
        channels: List[str],
        type: Literal['AC', 'DC'] = 'DC'
    ) -> Decimal:
        """Measure current on specified channels (channels 21/22 only)"""
        self._validate_channels(channels, 'CURR')
        channel_list = ','.join(channels)
        cmd = f"MEAS:CURR:{type}? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_resistance(
        self,
        channels: List[str],
        four_wire: bool = False
    ) -> Decimal:
        """Measure resistance on specified channels"""
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

    async def execute_raw_command(self, command: str) -> str:
        """
        Execute raw SCPI command (APS7050 unique feature)

        Args:
            command: Raw SCPI command string (supports \\n escape sequences)

        Returns:
            Instrument response
        """
        # Convert escape sequences
        processed_cmd = command.replace('\\n', '\n').replace('\\r', '\r')
        return await self.query_command(processed_cmd)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Item: Command type (OPEN, CLOS, VOLT, CURR, etc.)
                - Channel: Channel specification
                - Type: AC/DC type (for VOLT/CURR)
                - Command: Raw SCPI command (optional, takes priority)

        Returns:
            String result (for backward compatibility)
        """
        # Check for raw command first (APS7050 unique feature)
        raw_cmd = get_param(params, 'Command')
        if raw_cmd:
            return await self.execute_raw_command(raw_cmd)

        # Standard command processing
        validate_required_params(params, ['Item', 'Channel'])

        item = params['Item'].upper()
        channel_spec = params['Channel']
        type_ = get_param(params, 'Type', 'DC', default='DC').upper()

        channels = self._parse_channel_spec(channel_spec)

        # Execute command based on item type
        if item == 'OPEN':
            result = await self.open_channels(channels)
            return str(result) if result is not None else '0'

        elif item == 'CLOS':
            result = await self.close_channels(channels)
            return str(result) if result is not None else '0'

        elif item == 'VOLT':
            value = await self.measure_voltage(channels, type_)
            return f'{value:.3f}'

        elif item == 'CURR':
            value = await self.measure_current(channels, type_)
            return f'{value:.3f}'

        elif item == 'RES':
            value = await self.measure_resistance(channels, four_wire=False)
            return f'{value:.3f}'

        elif item == 'FRES':
            value = await self.measure_resistance(channels, four_wire=True)
            return f'{value:.3f}'

        elif item == 'FREQ':
            value = await self.measure_frequency(channels)
            return f'{value:.3f}'

        else:
            raise ValueError(f"Unknown command: {item}")
