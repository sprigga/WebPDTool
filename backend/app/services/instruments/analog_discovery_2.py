"""
Analog Discovery 2 Instrument Driver

Digilent Analog Discovery 2 USB Oscilloscope/Function Generator
Uses WaveForms SDK via ctypes
"""
from typing import Dict, Any, Optional, Literal
import asyncio
import sys
import re

from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param
from app.services.instrument_connection import BaseInstrumentConnection


class AnalogDiscovery2Driver(BaseInstrumentDriver):
    """
    Driver for Digilent Analog Discovery 2

    Supports:
    - Analog output (function generator)
    - Oscilloscope (future phases)
    - Digital I/O (future phases)

    Note: Requires WaveForms SDK installation
    Uses ctypes for FFI to C API
    Falls back to simulation mode if SDK unavailable
    """

    # Function name mapping
    FUNCTION_NAMES = {
        '0': 'DC',
        '1': 'Sine',
        '2': 'Square',
        '3': 'Triangle',
        '4': 'RampUp',
        '5': 'RampDown',
        '6': 'Pulse',
        '7': 'SinePower',
        '8': 'Noise',
        '9': 'Custom',
    }

    # Valid channel names for function generation
    VALID_AOUT_CHANNELS = ['CH1', 'CH2']

    def __init__(self, connection: BaseInstrumentConnection):
        super().__init__(connection)
        self._dwf = None
        self._hdwf = None
        self._is_simulation = True

    async def initialize(self):
        """Initialize the instrument and load SDK"""
        try:
            # Try to load WaveForms SDK
            if sys.platform.startswith("win"):
                from ctypes import cdll
                self._dwf = cdll.LoadLibrary("dwf.dll")
            elif sys.platform.startswith("darwin"):
                from ctypes import cdll
                self._dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
            else:
                from ctypes import cdll
                self._dwf = cdll.LoadLibrary("libdwf.so")

            self._open_device()
            self._is_simulation = False
            self.logger.info("Analog Discovery 2 initialized with SDK")

        except (ImportError, OSError) as e:
            self.logger.warning(f"WaveForms SDK not available, using simulation mode: {e}")
            self._dwf = None
            self._is_simulation = True

    async def reset(self):
        """Reset the instrument"""
        if not self._is_simulation and self._hdwf:
            await self.write_command('*RST')
        self.logger.debug("AD2 reset")

    def _open_device(self):
        """Open first available AD2 device"""
        if not self._dwf:
            return

        from ctypes import c_int, byref

        hdwf = c_int()
        result = self._dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

        if result != 0:
            self._hdwf = hdwf
        else:
            self.logger.error("Failed to open Analog Discovery 2 device")

    def _str_to_num(self, num_str: str) -> float:
        """
        Convert string with unit suffix to float value

        Args:
            num_str: String like "100K", "10M", "100u"

        Returns:
            Numeric value
        """
        if not num_str:
            return 0.0

        num_str = num_str.strip()
        unit = num_str[-1].upper()

        multipliers = {
            'U': 1e-6,
            'μ': 1e-6,
            'M': 1e6,
            'K': 1e3,
            'G': 1e9,
        }

        if unit in multipliers:
            return float(num_str[:-1]) * multipliers[unit]

        # Try regex extraction
        match = re.findall(r'-?\d+\.?\d*', num_str)
        return float(match[0]) if match else 0.0

    def _select_function(self, index: str) -> str:
        """Convert function index to name"""
        return self.FUNCTION_NAMES.get(index, 'Sine')

    async def set_analog_out(
        self,
        channel: int,
        function: str,
        frequency: float,
        amplitude: float,
        offset: float
    ) -> None:
        """
        Configure analog output (function generator)

        Args:
            channel: Channel number (0 or 1)
            function: Waveform function name
            frequency: Frequency in Hz
            amplitude: Amplitude in V
            offset: DC offset in V
        """
        if self._is_simulation or not self._dwf or not self._hdwf:
            self.logger.debug(f"[SIMULATION] Set analog out CH{channel}: {function} {frequency}Hz {amplitude}V")
            return

        from ctypes import c_double

        # Set node and function
        self._dwf.FDwfAnalogOutNodeEnableSet(
            self._hdwf, channel, 0, 1
        )

        func_code = getattr(self, f'FUNC_{function.upper()}', 1)
        self._dwf.FDwfAnalogOutNodeFunctionSet(
            self._hdwf, channel, 0, func_code
        )

        # Set parameters
        self._dwf.FDwfAnalogOutNodeFrequencySet(
            self._hdwf, channel, 0, c_double(frequency)
        )
        self._dwf.FDwfAnalogOutNodeAmplitudeSet(
            self._hdwf, channel, 0, c_double(amplitude)
        )
        self._dwf.FDwfAnalogOutNodeOffsetSet(
            self._hdwf, channel, 0, c_double(offset)
        )

        # Start output
        self._dwf.FDwfAnalogOutConfigure(self._hdwf, channel, 1)
        self.logger.debug(f"Set analog out CH{channel}: {function} {frequency}Hz {amplitude}V")

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Mode: 0=input, 1=output
                - Channel: Channel number
                - Function: Waveform function (for output)
                - Frequency: Frequency string
                - Amplitude: Amplitude string
                - Offset: Offset string

        Returns:
            Measurement result or status
        """
        mode = get_param(params, 'Mode', '0')

        if mode == '1':  # Output mode
            # Validate required parameters for output mode
            required = ['Channel', 'Function', 'Frequency', 'Amplitude', 'Offset']
            validate_required_params(params, required)

            channel = int(get_param(params, 'Channel', '1')) - 1  # Convert to 0-based
            func_index = get_param(params, 'Function', '1')
            function = self._select_function(func_index)
            frequency = self._str_to_num(get_param(params, 'Frequency', '1K'))
            amplitude = self._str_to_num(get_param(params, 'Amplitude', '1'))
            offset = self._str_to_num(get_param(params, 'Offset', '0'))

            await self.set_analog_out(channel, function, frequency, amplitude, offset)
            return f"OK - CH{channel + 1}: {function} {frequency}Hz {amplitude}V"

        else:
            # Input mode (oscilloscope) - not implemented in Phase 2
            raise NotImplementedError("Oscilloscope mode not implemented in Phase 2")
