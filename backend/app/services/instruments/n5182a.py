"""
Agilent N5182A Instrument Driver

Agilent N5182A MXG X-Series Signal Generator
Supports CW and ARB modes
"""
from typing import Dict, Any, Literal
import asyncio
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class N5182ADriver(BaseInstrumentDriver):
    """
    Driver for Agilent N5182A MXG Signal Generator

    Supports:
    - CW (Continuous Wave) mode
    - ARB (Arbitrary Waveform) mode
    - Frequency, amplitude, output state control
    """

    # Output state mapping
    OUTPUT_STATES = {
        '0': 'RST',    # Reset
        '1': 'OFF',
        '2': 'ON',
    }

    # Waveform shapes for ARB mode
    WAVEFORMS = {
        '1': 'SINE_TEST_WFM',
        '2': 'RAMP_TEST_WFM',
    }

    async def initialize(self):
        """Initialize the instrument"""
        await self.write_command('*RST')
        await asyncio.sleep(0.5)
        self.logger.info("N5182A initialized")

    async def reset(self):
        """Reset the instrument to default state"""
        identification = await self.query_command('*IDN?')
        self.logger.info(f"Resetting N5182A: {identification}")
        await self.write_command('*RST')
        await asyncio.sleep(0.5)

    def _translate_frequency(self, freq: str) -> str:
        """
        Translate frequency string from compact format to SCPI format

        Args:
            freq: Frequency string like "100K", "50M", "1G"

        Returns:
            SCPI format like "100 k", "50 m", "1 g"
        """
        if not freq:
            return '0 '

        freq = freq.strip()
        unit = freq[-1].upper()

        if unit in ('K', 'M', 'G'):
            # Remove last char and add space + lowercase unit
            return f"{freq[:-1]} {unit.lower()}"
        else:
            # No unit suffix, add space
            return f"{freq} "

    async def set_frequency(self, frequency: str) -> None:
        """
        Set output frequency

        Args:
            frequency: Frequency string (e.g., "100K", "50M")
        """
        freq_scpi = self._translate_frequency(frequency)
        cmd = f'FREQ {freq_scpi}Hz'
        await self.write_command(cmd)
        self.logger.debug(f"Set frequency to {frequency}")

    async def set_amplitude(self, amplitude: str) -> None:
        """
        Set power amplitude

        Args:
            amplitude: Amplitude in dBm (e.g., "-10")
        """
        cmd = f'POW:AMPL {amplitude} dBm'
        await self.write_command(cmd)
        self.logger.debug(f"Set amplitude to {amplitude} dBm")

    async def set_output_state(self, state: Literal['ON', 'OFF', 'RST']) -> None:
        """
        Set RF output state

        Args:
            state: Output state ('ON', 'OFF', or 'RST')
        """
        if state == 'RST':
            await self.reset()
        else:
            cmd = f'OUTP:STAT {state}'
            await self.write_command(cmd)
            self.logger.debug(f"Set output state to {state}")

    async def set_arb_waveform(self, shape: str) -> None:
        """
        Set ARB waveform

        Args:
            shape: Waveform shape key ('1' for SINE, '2' for RAMP)
        """
        if shape not in self.WAVEFORMS:
            raise ValueError(f"Invalid waveform shape: {shape}")

        waveform = self.WAVEFORMS[shape]
        cmd = f':SOURce:RADio:ARB:WAVeform "WFM1:{waveform}"'
        await self.write_command(cmd)

        # Configure trigger to free run
        await self.write_command(':PULM:SOUR:INT FRUN')
        await self.write_command(':SOURce:RADio:ARB:STATe ON')
        await self.write_command(':OUTPut:MODulation:STATe ON')
        self.logger.debug(f"Set ARB waveform to {waveform}")

    async def query_frequency(self) -> str:
        """Query current frequency setting"""
        return await self.query_command('FREQ:CW?')

    async def query_amplitude(self) -> str:
        """Query current power amplitude"""
        return await self.query_command('POW:AMPL?')

    async def query_output_state(self) -> bool:
        """Query RF output state"""
        response = await self.query_command('OUTP?')
        return int(response.strip()) > 0

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Output: '0'=RST, '1'=OFF, '2'=ON
                - Frequency: Frequency string (e.g., "100K")
                - Amplitude: Amplitude in dBm
                - Mode: '1'=CW, '2'=ARB
                - Shape: Waveform shape (for ARB mode)

        Returns:
            Status confirmation string
        """
        # Map output state
        output_key = get_param(params, 'Output', '0', default='0')
        output = self.OUTPUT_STATES.get(output_key, 'OFF')

        if output == 'RST':
            identification = await self.query_command('*IDN?')
            await self.write_command('*RST')
            return identification

        # Set frequency and amplitude
        frequency = get_param(params, 'Frequency')
        if frequency:
            await self.set_frequency(frequency)

        amplitude = get_param(params, 'Amplitude')
        if amplitude:
            await self.set_amplitude(amplitude)

        # Configure ARB mode if specified
        mode = get_param(params, 'Mode', '1')
        if mode == '2':  # ARB mode
            shape = get_param(params, 'Shape', '1')
            await self.set_arb_waveform(shape)

        # Set output state
        if output in ('ON', 'OFF'):
            await self.set_output_state(output)

        # Return status confirmation
        freq = await self.query_frequency()
        power = await self.query_command('POW:AMPL?')
        rf_state = 'on' if await self.query_output_state() else 'off'

        return f"FREQ:{freq.strip()}, POWER:{power.strip()}, RF:{rf_state}"
