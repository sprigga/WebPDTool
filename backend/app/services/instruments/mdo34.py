"""
MDO34 Instrument Driver

Tektronix MDO34 Mixed Domain Oscilloscope
Modern async driver implementation
"""
from typing import Dict, Any
from decimal import Decimal
from app.services.instruments.base import BaseInstrumentDriver


class MDO34Driver(BaseInstrumentDriver):
    """
    Driver for Tektronix MDO34 Mixed Domain Oscilloscope

    Supports:
    - 4 analog channels
    - 38 measurement types
    - Auto-setup
    - Waveform measurements
    """

    # Measurement type mapping (38 types)
    MEASUREMENT_TYPES = {
        '1': 'AMPlitude',
        '2': 'AREa',
        '3': 'BURst',
        '4': 'CARea',
        '5': 'CMEan',
        '6': 'CRMs',
        '7': 'DELay',
        '8': 'FALL',
        '9': 'FREQuency',
        '10': 'HIGH',
        '11': 'HITS',
        '12': 'LOW',
        '13': 'MAXimum',
        '14': 'MEAN',
        '15': 'MEDian',
        '16': 'MINImum',
        '17': 'NDUty',
        '18': 'NEDGECount',
        '19': 'NOVershoot',
        '20': 'NPULSECount',
        '21': 'NWIdth',
        '22': 'PEAKHits',
        '23': 'PDUty',
        '24': 'PEDGECount',
        '25': 'PERIod',
        '26': 'PHAse',
        '27': 'PK2Pk',
        '28': 'POVershoot',
        '29': 'PPULSECount',
        '30': 'PWIdth',
        '31': 'RISe',
        '32': 'RMS',
        '33': 'SIGMA1',
        '34': 'SIGMA2',
        '35': 'SIGMA3',
        '36': 'STDdev',
        '37': 'TOVershoot',
        '38': 'WAVEFORMS',
    }

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("MDO34 initialized")

    async def reset(self):
        """Reset the instrument to default state"""
        await self.write_command('*RST')
        self.logger.debug("MDO34 reset")

    async def select_channel(self, channel: int) -> None:
        """
        Select specific channel and disable others

        Args:
            channel: Channel number (1-4)
        """
        if not 1 <= channel <= 4:
            raise ValueError(f"Invalid channel: {channel} (must be 1-4)")

        # Disable all channels first
        for ch in range(1, 5):
            state = 'ON' if ch == channel else 'OFF'
            await self.write_command(f'SELECT:CH{ch} {state}')

        self.logger.debug(f"Selected channel {channel}, others disabled")

    async def auto_setup(self, simulation: bool = False) -> None:
        """
        Perform automatic setup and wait for completion

        This command configures the oscilloscope for optimal signal viewing.
        Blocks until autoset is complete.

        Args:
            simulation: Skip polling in simulation mode
        """
        # Execute autoset
        await self.write_command(':AUTOSet EXECute')

        # In simulation mode, skip the polling (simulation always returns '1.234')
        if simulation:
            self.logger.debug("Auto-setup completed (simulation mode)")
            return

        # Poll BUSY? until autoset completes
        import asyncio
        max_retries = 100  # 10 seconds max
        retry_count = 0

        while retry_count < max_retries:
            response = await self.query_command('BUSY?')
            if response.strip() == '0':
                break

            await asyncio.sleep(0.1)  # 100ms poll interval
            retry_count += 1

        if retry_count >= max_retries:
            raise TimeoutError("Auto-setup timeout (exceeded 10 seconds)")

        self.logger.debug("Auto-setup completed")

    async def measure(self, channel: int, meas_type: str) -> Decimal:
        """
        Measure signal parameter on specified channel

        Args:
            channel: Channel number (1-4)
            meas_type: Measurement type (e.g., 'FREQuency', 'AMPlitude')

        Returns:
            Measured value
        """
        import asyncio
        from app.services.instrument_connection import SimulationInstrumentConnection

        # Detect if we're in simulation mode
        is_simulation = isinstance(self.connection, SimulationInstrumentConnection)

        # Select channel
        await self.select_channel(channel)

        # Perform auto-setup
        await self.auto_setup(simulation=is_simulation)

        # Configure measurement 4 (using MEAS4 slot)
        await self.write_command(f'MEASUrement:MEAS4:SOURCE1 CH{channel}')
        await self.write_command('MEASUrement:MEAS4:STATE ON')
        await self.write_command(f'MEASUrement:MEAS4:TYPE {meas_type}')

        # In simulation mode, skip type confirmation polling
        if not is_simulation:
            # Wait for type change confirmation (poll with 1-second interval)
            max_retries = 10  # 10 seconds max
            retry_count = 0

            while retry_count < max_retries:
                response = await self.query_command('MEASUrement:MEAS4:TYPE?')
                current_type = response.strip()

                if current_type == meas_type:
                    break

                await asyncio.sleep(1.0)  # 1-second poll interval
                retry_count += 1

            if retry_count >= max_retries:
                raise TimeoutError(f"Measurement type confirmation timeout for {meas_type}")

        # Read measurement value
        response = await self.query_command('MEASUrement:MEAS4:VALue?')

        # Clean response (strip prefix and newlines)
        value_str = response.strip().replace(':MEASUREMENT:MEAS4:VALUE ', '')

        return Decimal(value_str)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Item: Measurement type index ('1'-'38')
                - Channel: Channel number (1-4)

        Returns:
            String result (for backward compatibility)
            - Measurement value as string
            - None on failure (empty string)
        """
        from app.services.instruments.base import validate_required_params

        # Validate required parameters
        validate_required_params(params, ['Item', 'Channel'])

        # Parse parameters
        item_idx = str(params['Item'])
        channel = int(params['Channel'])

        # Validate channel
        if not 1 <= channel <= 4:
            raise ValueError(f"Invalid channel: {channel} (must be 1-4)")

        # Validate measurement type index
        if item_idx not in self.MEASUREMENT_TYPES:
            raise ValueError(
                f"Invalid measurement type index: {item_idx} (must be 1-38)"
            )

        meas_type = self.MEASUREMENT_TYPES[item_idx]

        try:
            # Perform measurement
            value = await self.measure(channel, meas_type)

            result_str = str(value)
            self.logger.info(f"MDO34 CH{channel} {meas_type}: {result_str}")
            return result_str

        except TimeoutError as e:
            error_msg = f"MDO34 measurement timeout: {str(e)}"
            self.logger.error(error_msg)
            return ''  # Legacy compatibility: return empty on timeout

        except Exception as e:
            error_msg = f"MDO34 measurement failed: {str(e)}"
            self.logger.error(error_msg)
            return ''  # Legacy compatibility: return empty on error
