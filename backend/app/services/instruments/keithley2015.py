"""
KEITHLEY2015 Instrument Driver

Keithley 2015 THD Multimeter
Modern async driver implementation
"""
from typing import Dict, Any, Literal
from decimal import Decimal
from app.services.instruments.base import BaseInstrumentDriver


class KEITHLEY2015Driver(BaseInstrumentDriver):
    """
    Driver for Keithley 2015 THD Multimeter

    Supports:
    - THD/THDN/SINAD measurements
    - 12 measurement types (voltage, current, resistance, etc.)
    - Output signal generator control
    - Auto/manual frequency selection
    """

    # Measurement type mapping (12 types)
    TYPE_MAP = {
        '1': 'DISTortion',
        '2': 'VOLTage:DC',
        '3': 'VOLTage:AC',
        '4': 'CURRent:DC',
        '5': 'CURRent:AC',
        '6': 'RESistance',
        '7': 'FRESistance',
        '8': 'PERiod',
        '9': 'FREQuency',
        '10': 'TEMPerature',
        '11': 'DIODe',
        '12': 'CONTinuity',
    }

    # Mode mapping
    MODE_MAP = {
        '1': 'THD',
        '2': 'THDN',
        '3': 'SINAD',
    }

    # Impedance mapping
    IMPEDANCE_MAP = {
        '1': 'OHM50',
        '2': 'OHM600',
        '3': 'HIZ',
    }

    # Shape mapping
    SHAPE_MAP = {
        '1': 'ISINE',
        '2': 'PULSE',
    }

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("KEITHLEY2015 initialized")

    async def reset(self):
        """Reset the instrument to default state"""
        await self.write_command('*RST')
        self.logger.debug("KEITHLEY2015 reset")

    async def measure(
        self,
        mode: Literal['THD', 'THDN', 'SINAD'],
        meas_type: str,
        frequency: float = 0
    ) -> Decimal:
        """
        Perform measurement in specified mode and type

        Args:
            mode: Measurement mode (THD, THDN, SINAD)
            meas_type: Measurement type (DISTortion, VOLTage:DC, etc.)
            frequency: Frequency in Hz (0 for AUTO)

        Returns:
            Measured value
        """
        # Set distortion type
        await self.write_command(f':DIST:TYPE {mode}')

        # Set measurement function
        await self.write_command(f'func \'{meas_type}\'')

        # Set frequency (AUTO or specific value)
        if frequency == 0:
            await self.write_command(':DIST:FREQ:AUTO ON')
        else:
            await self.write_command(':DIST:FREQ:AUTO OFF')
            await self.write_command(f':DIST:FREQ {frequency}')

        # Initiate measurement
        await self.write_command('INIT')

        # Read result
        response = await self.query_command('READ?')
        return Decimal(response.strip())

    async def set_output(
        self,
        enabled: bool,
        frequency: float,
        amplitude: float,
        impedance: Literal['OHM50', 'OHM600', 'HIZ'],
        shape: Literal['ISINE', 'PULSE']
    ) -> None:
        """
        Configure output signal generator

        Args:
            enabled: True to enable output, False to disable
            frequency: Output frequency (10-20000 Hz)
            amplitude: Output amplitude (V RMS)
            impedance: Output impedance (OHM50, OHM600, HIZ)
            shape: Waveform shape (ISINE, PULSE)
        """
        # Set output state
        state = '1' if enabled else '0'
        await self.write_command(f'OUTP {state}')

        if enabled:
            # Set frequency
            await self.write_command(f'OUTP:FREQ {frequency}')

            # Set impedance
            await self.write_command(f'OUTP:IMP {impedance}')

            # Set amplitude
            await self.write_command(f'OUTP:AMPL {amplitude}')

            # Set shape
            await self.write_command(f'OUTP:CHANnel2 {shape}')

            # Query to verify
            response = await self.query_command('OUTP?')
            self.logger.debug(f"Output configured: {response}")

    async def get_identity(self) -> str:
        """Get instrument identification"""
        return await self.query_command('*IDN?')

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Command: Space-separated indices

        Command formats:
            1. Read Mode (6 indices):
               [0] = '1'
               [1] = Mode: '1'(THD), '2'(THDN), '3'(SINAD)
               [2] = Type: '1'-'12' (see TYPE_MAP)
               [3] = Frequency: '0'(AUTO) or numeric value
               [4-5] = Reserved/unused

            2. Output Mode (6 indices):
               [0] = '2'
               [1] = Output: '1'(ON), '0'(OFF)
               [2] = Frequency (Hz): 10-20000
               [3] = Amplitude (V RMS)
               [4] = Impedance: '1'(50Ω), '2'(600Ω), '3'(HIZ)
               [5] = Shape: '1'(ISINE), '2'(PULSE)

            3. Reset:
               [0] = '0' (triggers *IDN? and *RST)

        Returns:
            String result (for backward compatibility)
        """
        from app.services.instruments.base import validate_required_params

        # Validate required parameters
        validate_required_params(params, ['Command'])

        # Parse command indices
        cmd_str = params['Command']
        indices = cmd_str.split()

        if not indices:
            raise ValueError("Command parameter is empty")

        state = indices[0]

        try:
            # State 0: Reset
            if state == '0':
                identity = await self.get_identity()
                await self.reset()
                return identity

            # State 1: Measurement mode
            elif state == '1':
                if len(indices) < 4:
                    raise ValueError(f"Measurement mode requires at least 4 indices, got {len(indices)}")

                mode_idx = indices[1]
                type_idx = indices[2]
                freq_str = indices[3]

                # Map indices to values
                if mode_idx not in self.MODE_MAP:
                    raise ValueError(f"Invalid mode index: {mode_idx} (must be 1-3)")

                if type_idx not in self.TYPE_MAP:
                    raise ValueError(f"Invalid type index: {type_idx} (must be 1-12)")

                mode = self.MODE_MAP[mode_idx]
                meas_type = self.TYPE_MAP[type_idx]
                frequency = float(freq_str)

                # Perform measurement
                value = await self.measure(mode, meas_type, frequency)

                # Format output (handle scientific notation)
                result_str = str(value)
                self.logger.info(f"Measurement: {mode} {meas_type} = {result_str}")
                return result_str

            # State 2: Output mode
            elif state == '2':
                if len(indices) < 6:
                    raise ValueError(f"Output mode requires 6 indices, got {len(indices)}")

                output_idx = indices[1]
                freq_str = indices[2]
                ampl_str = indices[3]
                imp_idx = indices[4]
                shape_idx = indices[5]

                # Map indices to values
                enabled = (output_idx == '1')
                frequency = float(freq_str)
                amplitude = float(ampl_str)

                if imp_idx not in self.IMPEDANCE_MAP:
                    raise ValueError(f"Invalid impedance index: {imp_idx} (must be 1-3)")

                if shape_idx not in self.SHAPE_MAP:
                    raise ValueError(f"Invalid shape index: {shape_idx} (must be 1-2)")

                impedance = self.IMPEDANCE_MAP[imp_idx]
                shape = self.SHAPE_MAP[shape_idx]

                # Configure output
                await self.set_output(enabled, frequency, amplitude, impedance, shape)

                self.logger.info(f"Output configured: {'ON' if enabled else 'OFF'}, "
                               f"{frequency}Hz, {amplitude}V, {impedance}, {shape}")
                return '1'

            else:
                raise ValueError(f"Invalid state: {state} (must be 0, 1, or 2)")

        except Exception as e:
            error_msg = f"KEITHLEY2015 command failed: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
