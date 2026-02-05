"""
CMW100 Instrument Driver

Rohde & Schwarz CMW100 Wireless Communications Tester
Supports Bluetooth LE and WiFi RF measurements using RsInstrument library
"""
from typing import Dict, Any, Optional
from decimal import Decimal
import asyncio
import logging

from app.services.instruments.base import (
    BaseInstrumentDriver,
    validate_required_params,
    get_param
)

logger = logging.getLogger(__name__)


class CMW100Driver(BaseInstrumentDriver):
    """
    Driver for Rohde & Schwarz CMW100 wireless communications tester

    Supports:
    - Bluetooth LE TX power measurement
    - WiFi TX power and EVM measurement
    - Simulation mode for development without hardware

    Connection: TCPIP or GPIB via RsInstrument library

    Reference: docs/lowsheen_lib/CMW100_API_Analysis.md
    """

    def __init__(self, connection):
        super().__init__(connection)
        # Detect simulation mode from address (sim://cmw100)
        self.simulation_mode = self.connection.config.connection.address.startswith('sim://')
        self._rs_instr = None

    async def initialize(self) -> None:
        """
        Initialize the CMW100 instrument

        For real hardware: Initialize RsInstrument connection
        For simulation mode: Set up mock state
        """
        if self.simulation_mode:
            self.logger.info("CMW100 initialized in SIMULATION mode")
            return

        try:
            await self._init_rs_instrument()
            self.logger.info("CMW100 initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize CMW100: {e}")
            raise

    async def reset(self) -> None:
        """
        Reset instrument to default state

        Equivalent to PDTool4's *RST command
        """
        if self.simulation_mode:
            self.logger.debug("CMW100 reset (simulation)")
            return

        try:
            await self.write_command("*RST")
            await asyncio.sleep(0.5)
            self.logger.info("CMW100 reset successfully")
        except Exception as e:
            self.logger.warning(f"Failed to reset CMW100: {e}")

    # ========================================================================
    # Bluetooth LE Measurements
    # ========================================================================

    async def measure_ble_tx_power(
        self,
        connector: int,
        frequency: float,
        expected_power: float,
        burst_type: str = "LE"
    ) -> Dict[str, Any]:
        """
        Measure Bluetooth LE TX power

        Args:
            connector: RF connector number (1-8, RA1-RA8)
            frequency: RF frequency in MHz (2402-2480 for BLE)
            expected_power: Expected nominal power in dBm
            burst_type: Bluetooth type ("LE", "BR", or "EDR")

        Returns:
            Dict with measurement results:
            {
                'tx_power': Decimal,      # Measured TX power in dBm
                'frequency_error': Decimal, # Frequency error in Hz
                'delta_power': Decimal,   # Power from expected in dB
                'status': str,            # 'PASS' or 'FAIL'
                'error': str or None      # Error message if any
            }

        Reference: CMW100_API_Analysis.md - API_BT_Meas.py
        SCPI: CONFigure:BLUetooth:MEAS:ISIGnal
        """
        if self.simulation_mode:
            return await self._simulate_ble_measurement(connector, frequency, expected_power)

        try:
            # Validate parameters
            if not 1 <= connector <= 8:
                raise ValueError(f"Invalid connector: {connector} (must be 1-8)")

            if not 2400 <= frequency <= 6000:
                raise ValueError(f"Invalid frequency: {frequency} MHz (must be 2400-6000)")

            # Configure BLE measurement
            await self.configure_ble_measurement(connector, frequency, burst_type)

            # Initiate measurement
            await self.write_command("INITiate:BLUetooth:MEAS:MEValuation")

            # Wait for measurement completion (BLE measurements are fast, ~1-2 seconds)
            await asyncio.sleep(2.0)

            # Fetch results
            return await self._fetch_ble_results(expected_power)

        except Exception as e:
            self.logger.error(f"BLE TX power measurement failed: {e}")
            return {
                'tx_power': Decimal('0'),
                'frequency_error': Decimal('0'),
                'delta_power': Decimal('0'),
                'status': 'ERROR',
                'error': str(e)
            }

    async def configure_ble_measurement(
        self,
        connector: int,
        frequency: float,
        burst_type: str = "LE"
    ) -> None:
        """
        Configure Bluetooth measurement parameters

        Args:
            connector: RF connector number (1-8)
            frequency: RF frequency in MHz
            burst_type: Bluetooth type ("LE", "BR", or "EDR")
        """
        # Map burst type to SCPI value
        burst_map = {
            "BR": "BR",
            "EDR": "EDR",
            "LE": "LE"
        }
        burst_scpi = burst_map.get(burst_type.upper(), "LE")

        # Configure Bluetooth type
        await self.write_command(f"CONFigure:BLUetooth:MEAS:ISIGnal:BTYPe {burst_scpi}")

        # Set connector (signal path)
        await self.write_command(f"CONFigure:BLUetooth:MEAS:RFSettings:CONNector RA{connector}")

        # Set frequency
        await self.write_command(f"CONFigure:BLUetooth:MEAS:RFSettings:FREQuency {frequency}MHZ")

        # Set sync mode to AUTO
        await self.write_command("CONFigure:BLUetooth:MEAS:ISIGnal:ASYNchronize AUTO")

        self.logger.debug(f"Configured BLE measurement: connector={connector}, freq={frequency}MHz, type={burst_scpi}")

    async def _fetch_ble_results(self, expected_power: float) -> Dict[str, Any]:
        """
        Fetch BLE measurement results from instrument

        Args:
            expected_power: Expected power for delta calculation

        Returns:
            Dict with measurement results
        """
        try:
            # Fetch average power
            tx_power = await self.query_decimal("FETCh:BLUetooth:MEAS:MEValuation:PVTime:AVERage:POWer?")

            # Fetch frequency error
            freq_error = await self.query_decimal("FETCh:BLUetooth:MEAS:MEValuation:MODulation:FERRor?")

            # Calculate delta from expected
            delta_power = float(tx_power) - expected_power

            # Determine pass/fail (simple threshold: ±3 dB)
            status = "PASS" if abs(delta_power) <= 3.0 else "WARN"

            self.logger.info(f"BLE TX power: {tx_power} dBm (expected {expected_power}, delta {delta_power:+.2f} dB)")

            return {
                'tx_power': tx_power,
                'frequency_error': freq_error,
                'delta_power': Decimal(str(delta_power)),
                'status': status,
                'error': None
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch BLE results: {e}")
            return {
                'tx_power': Decimal('0'),
                'frequency_error': Decimal('0'),
                'delta_power': Decimal('0'),
                'status': 'ERROR',
                'error': str(e)
            }

    async def _simulate_ble_measurement(
        self,
        connector: int,
        frequency: float,
        expected_power: float
    ) -> Dict[str, Any]:
        """
        Simulate BLE TX power measurement (for development without hardware)

        Returns realistic values with some random variation
        """
        import random

        # Simulate realistic BLE power range: -10 to +15 dBm
        # Add some random variation from expected (±2 dB)
        variation = random.uniform(-2.0, 2.0)
        tx_power = Decimal(str(max(min(expected_power + variation, 15), -10)))

        # Frequency error: ±5 kHz typical
        freq_error = Decimal(str(random.uniform(-5000, 5000)))

        delta_power = float(tx_power) - expected_power
        status = "PASS" if abs(delta_power) <= 3.0 else "WARN"

        self.logger.info(f"[SIM] BLE TX power: {tx_power} dBm (expected {expected_power}, delta {delta_power:+.2f} dB)")

        return {
            'tx_power': tx_power,
            'frequency_error': freq_error,
            'delta_power': Decimal(str(delta_power)),
            'status': status,
            'error': None
        }

    # ========================================================================
    # WiFi Measurements
    # ========================================================================

    async def measure_wifi_tx_power(
        self,
        connector: int,
        standard: str,
        channel: int,
        bandwidth: int,
        expected_power: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Measure WiFi TX power and EVM

        Args:
            connector: RF connector number (1-8)
            standard: WiFi standard ('b/g', 'a/g', 'n', 'ac', 'ax')
            channel: WiFi channel number
            bandwidth: Channel bandwidth in MHz (5, 10, 20, 40, 80)
            expected_power: Expected power in dBm (optional, for delta calculation)

        Returns:
            Dict with measurement results:
            {
                'tx_power': Decimal,      # Average TX power in dBm
                'peak_power': Decimal,    # Peak power in dBm
                'evm_all': Decimal,       # EVM all carriers in dB
                'evm_data': Decimal,      # EVM data carriers in dB
                'evm_pilot': Decimal,     # EVM pilot carriers in dB
                'frequency_error': Decimal, # Center frequency error in Hz
                'delta_power': Decimal,   # Power from expected in dB (if expected_power given)
                'status': str,            # 'PASS' or 'FAIL'
                'error': str or None      # Error message if any
            }

        Reference: CMW100_API_Analysis.md - API_WiFi_Meas.py
        SCPI: CONFigure:WLAN:MEAS:ISIGnal
        """
        if self.simulation_mode:
            return await self._simulate_wifi_measurement(connector, standard, channel, bandwidth, expected_power)

        try:
            # Validate parameters
            if not 1 <= connector <= 8:
                raise ValueError(f"Invalid connector: {connector} (must be 1-8)")

            # Map standard to SCPI value
            standard_map = {
                'b/g': 'B',
                'a/g': 'A',
                'n': 'N',
                'ac': 'AC',
                'ax': 'AX'
            }
            standard_scpi = standard_map.get(standard.lower(), 'AC')

            # Configure WiFi measurement
            await self.configure_wifi_measurement(connector, standard, channel, bandwidth)

            # Initiate measurement
            await self.write_command("INITiate:WLAN:MEAS:MEValuation")

            # Wait for measurement completion (WiFi measurements take ~3-5 seconds)
            await asyncio.sleep(3.0)

            # Fetch results
            return await self._fetch_wifi_results(expected_power)

        except Exception as e:
            self.logger.error(f"WiFi TX power measurement failed: {e}")
            return {
                'tx_power': Decimal('0'),
                'peak_power': Decimal('0'),
                'evm_all': Decimal('0'),
                'evm_data': Decimal('0'),
                'evm_pilot': Decimal('0'),
                'frequency_error': Decimal('0'),
                'delta_power': Decimal('0'),
                'status': 'ERROR',
                'error': str(e)
            }

    async def configure_wifi_measurement(
        self,
        connector: int,
        standard: str,
        channel: int,
        bandwidth: int
    ) -> None:
        """
        Configure WiFi measurement parameters

        Args:
            connector: RF connector number (1-8)
            standard: WiFi standard ('b/g', 'a/g', 'n', 'ac', 'ax')
            channel: WiFi channel number
            bandwidth: Channel bandwidth in MHz
        """
        # Map standard to SCPI value
        standard_map = {
            'b/g': 'B',
            'a/g': 'A',
            'n': 'N',
            'ac': 'AC',
            'ax': 'AX'
        }
        standard_scpi = standard_map.get(standard.lower(), 'AC')

        # Configure standard
        await self.write_command(f"CONFigure:WLAN:MEAS:ISIGnal:STANdard {standard_scpi}")

        # Set connector
        await self.write_command(f"CONFigure:WLAN:MEAS:RFSettings:CONNector RA{connector}")

        # Map channel to frequency band (simplified - actual mapping depends on standard)
        if channel <= 14:
            band = "2.4G"
            freq_mhz = 2412 + (channel - 1) * 5
        else:
            band = "5G"
            # 5 GHz channel to frequency mapping (simplified)
            freq_mhz = 5180 + (channel - 36) * 5

        await self.write_command(f"CONFigure:WLAN:MEAS:RFSettings:FREQuency:BAND {band}")
        await self.write_command(f"CONFigure:WLAN:MEAS:RFSettings:FREQuency {freq_mhz}MHZ")

        # Map bandwidth to SCPI value
        bw_map = {5: 'MHZ5', 10: 'MHZ10', 20: 'MHZ20', 40: 'MHZ40', 80: 'MHZ80'}
        bw_scpi = bw_map.get(bandwidth, 'MHZ20')
        await self.write_command(f"CONFigure:WLAN:MEAS:ISIGnal:BWIDth {bw_scpi}")

        self.logger.debug(f"Configured WiFi measurement: connector={connector}, std={standard_scpi}, ch={channel}, bw={bandwidth}MHz")

    async def _fetch_wifi_results(self, expected_power: Optional[float]) -> Dict[str, Any]:
        """
        Fetch WiFi measurement results from instrument

        Args:
            expected_power: Expected power for delta calculation (optional)

        Returns:
            Dict with measurement results
        """
        try:
            # Fetch power measurements
            tx_power = await self.query_decimal("FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage:TXPower?")
            peak_power = await self.query_decimal("FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage:MAXPower?")

            # Fetch EVM measurements
            evm_all = await self.query_decimal("FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage:EVM:ALL?")
            evm_data = await self.query_decimal("FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage:EVM:DATA?")
            evm_pilot = await self.query_decimal("FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage:EVM:PILot?")

            # Fetch frequency error
            freq_error = await self.query_decimal("FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage:FERRor?")

            # Calculate delta if expected power provided
            delta_power = Decimal('0')
            if expected_power is not None:
                delta_power = Decimal(str(float(tx_power) - expected_power))

            # Determine pass/fail based on EVM (typical threshold: -25 dB for 11ac)
            status = "PASS" if float(evm_all) <= -25.0 else "FAIL"

            self.logger.info(f"WiFi TX power: {tx_power} dBm, EVM: {evm_all} dB, status: {status}")

            return {
                'tx_power': tx_power,
                'peak_power': peak_power,
                'evm_all': evm_all,
                'evm_data': evm_data,
                'evm_pilot': evm_pilot,
                'frequency_error': freq_error,
                'delta_power': delta_power,
                'status': status,
                'error': None
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch WiFi results: {e}")
            return {
                'tx_power': Decimal('0'),
                'peak_power': Decimal('0'),
                'evm_all': Decimal('0'),
                'evm_data': Decimal('0'),
                'evm_pilot': Decimal('0'),
                'frequency_error': Decimal('0'),
                'delta_power': Decimal('0'),
                'status': 'ERROR',
                'error': str(e)
            }

    async def _simulate_wifi_measurement(
        self,
        connector: int,
        standard: str,
        channel: int,
        bandwidth: int,
        expected_power: Optional[float]
    ) -> Dict[str, Any]:
        """
        Simulate WiFi TX power measurement (for development without hardware)

        Returns realistic values with some random variation
        """
        import random

        # Simulate realistic WiFi power range: 5-25 dBm (varies by standard)
        if standard.lower() in ['b/g', 'a/g']:
            base_power = 18.0
        elif standard.lower() == 'n':
            base_power = 16.0
        elif standard.lower() == 'ac':
            base_power = 15.0
        else:  # ax
            base_power = 14.0

        # Add random variation (±2 dB)
        variation = random.uniform(-2.0, 2.0)
        tx_power = Decimal(str(base_power + variation))

        # Peak power slightly higher (1-3 dB)
        peak_power = Decimal(str(float(tx_power) + random.uniform(1.0, 3.0)))

        # EVM: -35 to -50 dB typical (lower is better)
        evm_all = Decimal(str(random.uniform(-50, -35)))
        evm_data = Decimal(str(float(evm_all) + random.uniform(0, 2)))  # Slightly worse
        evm_pilot = Decimal(str(float(evm_all) - random.uniform(0, 2)))  # Slightly better

        # Frequency error: ±20 kHz typical
        freq_error = Decimal(str(random.uniform(-20000, 20000)))

        # Calculate delta if expected power provided
        delta_power = Decimal('0')
        if expected_power is not None:
            delta_power = Decimal(str(float(tx_power) - expected_power))

        # Determine pass/fail based on EVM
        status = "PASS" if float(evm_all) <= -25.0 else "FAIL"

        self.logger.info(f"[SIM] WiFi TX power: {tx_power} dBm, EVM: {evm_all} dB, status: {status}")

        return {
            'tx_power': tx_power,
            'peak_power': peak_power,
            'evm_all': evm_all,
            'evm_data': evm_data,
            'evm_pilot': evm_pilot,
            'frequency_error': freq_error,
            'delta_power': delta_power,
            'status': status,
            'error': None
        }

    # ========================================================================
    # RsInstrument Initialization
    # ========================================================================

    async def _init_rs_instrument(self) -> None:
        """
        Initialize RsInstrument connection

        RsInstrument is the official Rohde & Schwarz Python library
        that provides better CMW100 support than generic PyVISA

        Reference: https://pypi.org/project/RsInstrument/
        """
        try:
            # Import RsInstrument (optional dependency)
            from RsInstrument import RsInstrument

            # Get connection parameters
            address = self.connection.config.connection.address
            timeout = self.connection.config.connection.timeout

            # Initialize RsInstrument (run in thread pool for blocking call)
            loop = asyncio.get_event_loop()

            def _init():
                # Create RsInstrument instance
                instr = RsInstrument(
                    resource_name=address,
                    id_query=True,
                    reset=False,
                    options='QueryInstrStatus=True'
                )

                # Configure timeouts
                instr.visa_timeout = timeout
                instr.opc_timeout = timeout
                instr.instrument_status_checking = True

                return instr

            self._rs_instr = await loop.run_in_executor(None, _init)

            # Set SCPI language mode
            await self.write_command("SYST:LANG SCPI")

            self.logger.info(f"RsInstrument initialized for {address}")

        except ImportError:
            raise ImportError(
                "RsInstrument library not installed. "
                "Install with: pip install RsInstrument"
            )
        except Exception as e:
            self.logger.error(f"RsInstrument initialization failed: {e}")
            raise

    async def write_command(self, command: str) -> None:
        """
        Write command to instrument (override for RsInstrument)

        Args:
            command: SCPI command string
        """
        if self.simulation_mode:
            self.logger.debug(f"[SIM] Write: {command}")
            return

        if self._rs_instr:
            # Use RsInstrument's write method
            loop = asyncio.get_event_loop()

            def _write():
                self._rs_instr.write_str(command)

            await loop.run_in_executor(None, _write)
            self.logger.debug(f"RsInstrument write: {command}")
        else:
            # Fallback to base class method
            await super().write_command(command)

    async def query_command(self, command: str) -> str:
        """
        Query instrument and return response (override for RsInstrument)

        Args:
            command: SCPI query command string

        Returns:
            Instrument response string
        """
        if self.simulation_mode:
            # Return mock response for common queries
            if "TXPower?" in command:
                return "15.5"
            elif "EVM" in command:
                return "-35.5"
            elif "FERRor?" in command:
                return "5000"
            else:
                return "0"

        if self._rs_instr:
            # Use RsInstrument's query method
            loop = asyncio.get_event_loop()

            def _query():
                return self._rs_instr.query_str(command).strip()

            response = await loop.run_in_executor(None, _query)
            self.logger.debug(f"RsInstrument query: {command} -> {response}")
            return response
        else:
            # Fallback to base class method
            return await super().query_command(command)
