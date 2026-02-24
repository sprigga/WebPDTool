"""
SMCV100B Instrument Driver

Rohde & Schwarz SMCV100B vector signal generator driver.
Supports DAB, AM, FM, and IQ modulation modes.

Based on: src/lowsheen_lib/smcv100b.py from PDTool4

Dependencies:
    - RsSmcv: Rohde & Schwarz SMCV SDK (proprietary)
    - Or PyVISA for SCPI-based control
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

try:
    from RsSmcv import RsSmcv
    RSMCV_AVAILABLE = True
except ImportError:
    RSMCV_AVAILABLE = False
    RsSmcv = None

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class SMCV100BDriver(BaseInstrumentDriver):
    """
    Rohde & Schwarz SMCV100B vector signal generator driver

    Supports:
    - DAB/TDMB (Digital Audio Broadcasting) with transport stream playback
    - AM (Amplitude Modulation) radio generation
    - FM (Frequency Modulation) radio generation
    - IQ baseband modulation output
    - General RF output control

    Connection configuration (VISAAddress):
        - address: VISA resource string (e.g., 'TCPIP0::192.168.1.200::5025::SOCKET')
        - timeout: Communication timeout in milliseconds
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize SMCV100B driver"""
        super().__init__(connection)
        self.instrument: Optional[RsSmcv] = None
        self.default_timeout = 10.0
        self._file_path = "/var/user/"  # Default transport stream path

    async def initialize(self):
        """Initialize instrument connection"""
        try:
            # Get connection string
            conn_config = self.connection.config.connection
            address = str(conn_config)

            # Try RsSmcv SDK first
            if RSMCV_AVAILABLE:
                def create_instr():
                    return RsSmcv(address)

                self.instrument = await asyncio.get_event_loop().run_in_executor(
                    None, create_instr
                )

                # Validate connection
                if not await self._is_connected():
                    raise ConnectionError("Instrument not responding")

                self.logger.info(f"SMCV100B connected via RsSmcv SDK: {address}")
            else:
                self.logger.warning("RsSmcv SDK not available, using SCPI fallback")
                # Fallback to SCPI via base class methods
                self.logger.info(f"SMCV100B connected via SCPI: {address}")

        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise

    async def _is_connected(self) -> bool:
        """Check if instrument is connected and responding"""
        if not RSMCV_AVAILABLE or not self.instrument:
            return False

        try:
            def check_conn():
                return (self.instrument.utilities.is_connection_active() and
                       self.instrument.utilities.query_str('*IDN?') != "")

            return await asyncio.get_event_loop().run_in_executor(
                None, check_conn
            )
        except:
            return False

    async def reset(self):
        """Reset instrument to default state"""
        try:
            if RSMCV_AVAILABLE and self.instrument:
                def do_reset():
                    self.instrument.utilities.reset()

                await asyncio.get_event_loop().run_in_executor(
                    None, do_reset
                )
            else:
                # SCPI reset
                await self.write_command("*RST\n")
                await asyncio.sleep(0.5)

            self.logger.info("Instrument reset completed")
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            raise

    async def configure_dab(self, frequency: float, power: float,
                            transport_file: str) -> Dict[str, Any]:
        """
        Configure DAB/TDMB mode

        Args:
            frequency: RF carrier frequency in Hz
            power: RF power level in dBm
            transport_file: Transport stream filename

        Returns:
            Dict with configuration result
        """
        try:
            self.logger.info(f"Configuring DAB: {frequency/1e6} MHz, {power} dBm, file={transport_file}")

            if RSMCV_AVAILABLE and self.instrument:
                def configure():
                    # Enable TDMB baseband
                    self.instrument.source.bb.tdmb.set_state(True)

                    # Enable RF output
                    self.instrument.output.state.set_value(True)

                    # Set frequency and power
                    self.instrument.source.frequency.set_frequency(frequency)
                    self.instrument.source.power.set_power(power)

                    # Configure transport stream source
                    self.instrument.source.bb.tdmb.set_source(
                        tdmb_source=1  # TSPayer
                    )

                    # Load transport stream file
                    full_path = self._file_path + transport_file
                    self.instrument.tsGen.configure.set_play_file(play_file=full_path)

                    return 1

                result = await asyncio.get_event_loop().run_in_executor(
                    None, configure
                )

                return {
                    'status': 'OK' if result == 1 else 'ERROR',
                    'mode': 'DAB',
                    'frequency': frequency,
                    'power': power,
                    'file': transport_file
                }
            else:
                # SCPI fallback
                await self.write_command(f"SOURce:FREQuency {frequency} Hz\n")
                await self.write_command(f"SOURce:POWer {power} dBm\n")
                await self.write_command("OUTPut:STATe ON\n")

                return {
                    'status': 'OK',
                    'mode': 'DAB',
                    'frequency': frequency,
                    'power': power,
                    'file': transport_file,
                    'note': 'SCPI mode, file loading not supported'
                }

        except Exception as e:
            self.logger.error(f"DAB configuration error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def configure_am(self, frequency: float, power: float) -> Dict[str, Any]:
        """
        Configure AM modulation mode

        Args:
            frequency: RF carrier frequency in Hz
            power: RF power level in dBm

        Returns:
            Dict with configuration result
        """
        try:
            self.logger.info(f"Configuring AM: {frequency/1e6} MHz, {power} dBm")

            if RSMCV_AVAILABLE and self.instrument:
                def configure():
                    # Enable AM baseband
                    self.instrument.source.bb.radio.am.set_state(True)

                    # Enable RF output
                    self.instrument.output.state.set_value(True)

                    # Set frequency and power
                    self.instrument.source.frequency.set_frequency(frequency)
                    self.instrument.source.power.set_power(power)

                    return 1

                result = await asyncio.get_event_loop().run_in_executor(
                    None, configure
                )

                return {
                    'status': 'OK' if result == 1 else 'ERROR',
                    'mode': 'AM',
                    'frequency': frequency,
                    'power': power
                }
            else:
                # SCPI fallback
                await self.write_command("SOURce:BB:RAdio:AM:STATe ON\n")
                await self.write_command(f"SOURce:FREQuency {frequency} Hz\n")
                await self.write_command(f"SOURce:POWer {power} dBm\n")
                await self.write_command("OUTPut:STATe ON\n")

                return {
                    'status': 'OK',
                    'mode': 'AM',
                    'frequency': frequency,
                    'power': power
                }

        except Exception as e:
            self.logger.error(f"AM configuration error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def configure_fm(self, frequency: float, power: float) -> Dict[str, Any]:
        """
        Configure FM modulation mode

        Args:
            frequency: RF carrier frequency in Hz
            power: RF power level in dBm

        Returns:
            Dict with configuration result
        """
        try:
            self.logger.info(f"Configuring FM: {frequency/1e6} MHz, {power} dBm")

            if RSMCV_AVAILABLE and self.instrument:
                def configure():
                    # Enable FM baseband
                    self.instrument.source.bb.radio.fm.set_state(True)

                    # Enable RF output
                    self.instrument.output.state.set_value(True)

                    # Set frequency and power
                    self.instrument.source.frequency.set_frequency(frequency)
                    self.instrument.source.power.set_power(power)

                    return 1

                result = await asyncio.get_event_loop().run_in_executor(
                    None, configure
                )

                return {
                    'status': 'OK' if result == 1 else 'ERROR',
                    'mode': 'FM',
                    'frequency': frequency,
                    'power': power
                }
            else:
                # SCPI fallback
                await self.write_command("SOURce:BB:RAdio:FM:STATe ON\n")
                await self.write_command(f"SOURce:FREQuency {frequency} Hz\n")
                await self.write_command(f"SOURce:POWer {power} dBm\n")
                await self.write_command("OUTPut:STATe ON\n")

                return {
                    'status': 'OK',
                    'mode': 'FM',
                    'frequency': frequency,
                    'power': power
                }

        except Exception as e:
            self.logger.error(f"FM configuration error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def configure_iq(self, enable: bool = True) -> Dict[str, Any]:
        """
        Configure IQ modulation output

        Args:
            enable: Enable or disable IQ output

        Returns:
            Dict with configuration result
        """
        try:
            self.logger.info(f"Configuring IQ: enable={enable}")

            if RSMCV_AVAILABLE and self.instrument:
                def configure():
                    self.instrument.source.iq.set_state(enable)
                    return 1

                result = await asyncio.get_event_loop().run_in_executor(
                    None, configure
                )

                return {
                    'status': 'OK' if result == 1 else 'ERROR',
                    'mode': 'IQ',
                    'enabled': enable
                }
            else:
                # SCPI fallback
                state = "ON" if enable else "OFF"
                await self.write_command(f"SOURce:BB:IQ:STATe {state}\n")

                return {
                    'status': 'OK',
                    'mode': 'IQ',
                    'enabled': enable
                }

        except Exception as e:
            self.logger.error(f"IQ configuration error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def set_rf_output(self, enable: bool = True) -> Dict[str, Any]:
        """
        Control RF output state

        Args:
            enable: Enable or disable RF output

        Returns:
            Dict with operation result
        """
        try:
            self.logger.info(f"Setting RF output: enable={enable}")

            if RSMCV_AVAILABLE and self.instrument:
                def set_output():
                    self.instrument.output.state.set_value(enable)
                    return 1

                result = await asyncio.get_event_loop().run_in_executor(
                    None, set_output
                )

                return {
                    'status': 'OK' if result == 1 else 'ERROR',
                    'rf_enabled': enable
                }
            else:
                # SCPI fallback
                state = "ON" if enable else "OFF"
                await self.write_command(f"OUTPut:STATe {state}\n")

                return {
                    'status': 'OK',
                    'rf_enabled': enable
                }

        except Exception as e:
            self.logger.error(f"RF output control error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute SMCV100B command

        Parameters in params dict:
            - mode (str, required): Modulation mode
                - 'DAB': DAB/TDMB mode (requires file parameter)
                - 'AM': AM modulation
                - 'FM': FM modulation
                - 'IQ': IQ modulation
                - 'RF': RF output control
                - 'RESET': Reset instrument
            - frequency (float, required for RF modes): Frequency in MHz
            - power (float, required for RF modes): Power in dBm
            - file (str, required for DAB): Transport stream filename
            - enable (bool, optional): Enable/disable for IQ/RF modes
            - file_path (str, optional): Transport stream directory

        Returns:
            Operation result string
        """
        validate_required_params(params, ['mode'])

        mode = get_param(params, 'mode', 'Mode')

        self.logger.info(f"Executing SMCV100B command: mode={mode}")

        # Update file path if provided
        file_path = get_param(params, 'file_path')
        if file_path:
            self._file_path = file_path

        if mode == 'RESET' or mode == '0':
            result = await self.reset()
            return "Reset completed"

        elif mode == 'DAB' or mode == '0':
            # DAB mode: mode '0' in original PDTool4
            frequency = float(get_param(params, 'frequency', default=220.0)) * 1e6  # MHz to Hz
            power = float(get_param(params, 'power', default=-10.0))
            transport_file = get_param(params, 'file', 'File')

            if not transport_file:
                raise ValueError("DAB mode requires 'file' parameter")

            result = await self.configure_dab(frequency, power, transport_file)

            if result['status'] == 'OK':
                return f"DAB enabled: {result['frequency']/1e6} MHz, {result['power']} dBm, file={transport_file}"
            else:
                raise RuntimeError(f"DAB configuration failed: {result.get('error', 'Unknown error')}")

        elif mode == 'AM' or mode == '1':
            # AM mode: mode '1' in original PDTool4
            frequency = float(get_param(params, 'frequency', default=1000.0)) * 1e6
            power = float(get_param(params, 'power', default=-20.0))

            result = await self.configure_am(frequency, power)

            if result['status'] == 'OK':
                return f"AM enabled: {result['frequency']/1e6} MHz, {result['power']} dBm"
            else:
                raise RuntimeError(f"AM configuration failed: {result.get('error', 'Unknown error')}")

        elif mode == 'FM' or mode == '2':
            # FM mode: mode '2' in original PDTool4
            frequency = float(get_param(params, 'frequency', default=98.5)) * 1e6
            power = float(get_param(params, 'power', default=-15.0))

            result = await self.configure_fm(frequency, power)

            if result['status'] == 'OK':
                return f"FM enabled: {result['frequency']/1e6} MHz, {result['power']} dBm"
            else:
                raise RuntimeError(f"FM configuration failed: {result.get('error', 'Unknown error')}")

        elif mode == 'IQ':
            enable = get_param(params, 'enable', default=True)
            if isinstance(enable, str):
                enable = enable.lower() in ('true', '1', 'yes', 'on')

            result = await self.configure_iq(enable)

            if result['status'] == 'OK':
                return f"IQ output {'enabled' if result['enabled'] else 'disabled'}"
            else:
                raise RuntimeError(f"IQ configuration failed: {result.get('error', 'Unknown error')}")

        elif mode == 'RF':
            enable = get_param(params, 'enable', default=True)
            if isinstance(enable, str):
                enable = enable.lower() in ('true', '1', 'yes', 'on')

            result = await self.set_rf_output(enable)

            if result['status'] == 'OK':
                return f"RF output {'enabled' if result['rf_enabled'] else 'disabled'}"
            else:
                raise RuntimeError(f"RF output control failed: {result.get('error', 'Unknown error')}")

        else:
            raise ValueError(f"Unknown mode: {mode}")

    async def close(self):
        """Close instrument connection"""
        if RSMCV_AVAILABLE and self.instrument:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.instrument.close
                )
                self.logger.info("SMCV100B connection closed")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")

    def __del__(self):
        """Ensure connection is closed on cleanup"""
        if RSMCV_AVAILABLE and self.instrument:
            try:
                self.instrument.close()
            except:
                pass
