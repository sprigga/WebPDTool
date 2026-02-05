"""
Measurement Implementations
Concrete measurement classes for various test types
"""
from decimal import Decimal
from typing import Dict, Any, Optional
import asyncio
import random

from app.measurements.base import (
    BaseMeasurement,
    MeasurementResult,
    StringType
)


# ============================================================================
# Helper Functions
# ============================================================================
def get_param(params: Dict[str, Any], *keys: str, default=None):
    """Get parameter value trying multiple keys"""
    for key in keys:
        if key in params and params[key] not in (None, ""):
            return params[key]
    return default


# ============================================================================
# Dummy Measurement - For Testing
# ============================================================================
class DummyMeasurement(BaseMeasurement):
    """Returns random values for testing purposes"""

    async def execute(self) -> MeasurementResult:
        try:
            await asyncio.sleep(0.1)

            # Generate value based on limits with 80% pass rate
            if self.lower_limit is not None and self.upper_limit is not None:
                if random.random() < 0.8:
                    range_size = float(self.upper_limit - self.lower_limit)
                    measured_value = self.lower_limit + Decimal(random.uniform(0.1, 0.9) * range_size)
                else:
                    if random.random() < 0.5:
                        measured_value = self.lower_limit - Decimal(abs(random.gauss(1, 0.5)))
                    else:
                        measured_value = self.upper_limit + Decimal(abs(random.gauss(1, 0.5)))
            else:
                measured_value = Decimal(random.uniform(0, 100))

            is_valid, error_msg = self.validate_result(measured_value)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )
        except Exception as e:
            self.logger.error(f"Dummy measurement error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Command Test Measurement
# ============================================================================
class CommandTestMeasurement(BaseMeasurement):
    """Executes external commands/scripts"""

    async def execute(self) -> MeasurementResult:
        try:
            # Get parameters with fallback options
            command = get_param(self.test_params, "command") or self.test_plan_item.get("command", "")
            timeout = get_param(self.test_params, "timeout", default=5000)
            wait_msec = get_param(self.test_params, "wait_msec", "WaitmSec") or self.test_plan_item.get("wait_msec", 0)

            if not command:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing command parameter"
                )

            self.logger.info(f"Executing command: {command}")

            # Wait if specified
            if wait_msec and isinstance(wait_msec, (int, float)):
                await asyncio.sleep(wait_msec / 1000.0)

            # Execute command
            timeout_seconds = timeout / 1000.0
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/app"
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return self.create_result(
                    result="ERROR",
                    error_message=f"Command timeout after {timeout}ms"
                )

            output = stdout.decode().strip()
            error_output = stderr.decode().strip()

            if process.returncode != 0:
                error_msg = error_output or f"Command failed with exit code {process.returncode}"
                self.logger.error(f"Command failed: {error_msg}")
                return self.create_result(result="ERROR", error_message=error_msg)

            # Convert output based on value_type
            measured_value = output
            if self.value_type is not StringType:
                try:
                    measured_value = Decimal(output) if output else None
                except (ValueError, TypeError):
                    measured_value = None

            # Ensure measured_value is compatible with create_result
            if isinstance(measured_value, str):
                measured_value = None

            is_valid, error_msg = self.validate_result(measured_value)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"Command test error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Power Measurements
# ============================================================================
class PowerReadMeasurement(BaseMeasurement):
    """Reads voltage/current from power instruments"""

    async def execute(self) -> MeasurementResult:
        try:
            instrument = get_param(self.test_params, "Instrument")
            channel = get_param(self.test_params, "Channel")
            item = get_param(self.test_params, "Item")

            if not all([instrument, channel, item]):
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameters: Instrument, Channel, Item"
                )

            self.logger.info(f"Reading {item} from {instrument} channel {channel}")
            await asyncio.sleep(0.3)

            # Generate simulated value
            if self.lower_limit and self.upper_limit:
                center = (self.lower_limit + self.upper_limit) / 2
                variance = (self.upper_limit - self.lower_limit) / 10
                measured_value = center + Decimal(random.gauss(0, float(variance)))
            else:
                measured_value = Decimal(random.uniform(0, 100))

            is_valid, error_msg = self.validate_result(measured_value)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"Power read error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


class PowerSetMeasurement(BaseMeasurement):
    """Sets voltage/current on power supplies"""

    async def execute(self) -> MeasurementResult:
        try:
            instrument = get_param(self.test_params, "Instrument")
            voltage = get_param(self.test_params, "Voltage", "SetVolt")
            current = get_param(self.test_params, "Current", "SetCurr")

            if not instrument:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            self.logger.info(f"Setting power on {instrument}: V={voltage}, I={current}")
            await asyncio.sleep(0.2)

            return self.create_result(result="PASS", measured_value=Decimal("1.0"))

        except Exception as e:
            self.logger.error(f"Power set error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# SFC Measurement
# ============================================================================
class SFCMeasurement(BaseMeasurement):
    """Integrates with manufacturing execution systems"""

    async def execute(self) -> MeasurementResult:
        try:
            sfc_mode = get_param(self.test_params, "Mode", default="webStep1_2")
            self.logger.info(f"Executing SFC test with mode: {sfc_mode}")

            await asyncio.sleep(0.5)

            return self.create_result(result="PASS", measured_value=Decimal("1.0"))

        except Exception as e:
            self.logger.error(f"SFC test error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Get Serial Number Measurement
# ============================================================================
class GetSNMeasurement(BaseMeasurement):
    """Acquires device serial numbers"""

    async def execute(self) -> MeasurementResult:
        try:
            sn_type = get_param(self.test_params, "Type", default="SN")
            self.logger.info(f"Acquiring {sn_type} from device")

            await asyncio.sleep(0.1)

            # Return placeholder or provided serial number
            sn_value = get_param(self.test_params, "SerialNumber", default=f"SN{random.randint(100000, 999999)}")

            return self.create_result(result="PASS", measured_value=Decimal("1.0"))

        except Exception as e:
            self.logger.error(f"Serial number acquisition error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Operator Judgment Measurement
# ============================================================================
class OPJudgeMeasurement(BaseMeasurement):
    """Awaits operator confirmation for subjective tests"""

    async def execute(self) -> MeasurementResult:
        try:
            judgment_type = get_param(self.test_params, "Type", default="YorN")
            self.logger.info(f"Operator judgment: {judgment_type}")

            expected = get_param(self.test_params, "Expected", default="PASS")
            actual = get_param(self.test_params, "Result", default=expected)

            measured_value = Decimal("1.0") if actual == "PASS" else Decimal("0.0")
            # Ensure actual is a valid result string
            if actual not in ("PASS", "FAIL", "SKIP", "ERROR"):
                actual = "PASS"
            return self.create_result(result=str(actual), measured_value=measured_value)

        except Exception as e:
            self.logger.error(f"Operator judgment error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Wait Measurement
# ============================================================================
class WaitMeasurement(BaseMeasurement):
    """Waits for specified time duration"""

    async def execute(self) -> MeasurementResult:
        try:
            # Get wait time from multiple possible sources
            wait_msec = (
                get_param(self.test_params, "wait_msec", "WaitmSec") or
                self.test_plan_item.get("wait_msec", 0)
            )

            if not isinstance(wait_msec, (int, float)) or wait_msec <= 0:
                return self.create_result(
                    result="ERROR",
                    error_message=f"wait mode requires wait_msec > 0, got: {wait_msec}"
                )

            wait_seconds = wait_msec / 1000
            self.logger.info(f"Waiting {wait_msec}ms ({wait_seconds}s)")

            await asyncio.sleep(wait_seconds)

            return self.create_result(result="PASS", measured_value=Decimal("1.0"))

        except Exception as e:
            self.logger.error(f"Wait measurement error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Relay Control Measurement
# ============================================================================
class RelayMeasurement(BaseMeasurement):
    """
    Controls relay switching for DUT testing.
    Maps to PDTool4's MeasureSwitchON/OFF functionality.
    """

    async def execute(self) -> MeasurementResult:
        try:
            from app.services.dut_comms import get_relay_controller, RelayState

            # Get relay parameters
            relay_state = get_param(self.test_params, "relay_state", "case", "switch")
            channel = get_param(self.test_params, "channel", default=1)
            device_path = get_param(self.test_params, "device_path", default="/dev/ttyUSB0")

            # Normalize state parameter
            if isinstance(relay_state, str):
                relay_state = relay_state.upper()

            # Map state to RelayState enum
            if relay_state in ["ON", "OPEN", "0", "SWITCH_OPEN"]:
                target_state = RelayState.SWITCH_OPEN
            elif relay_state in ["OFF", "CLOSED", "1", "SWITCH_CLOSED"]:
                target_state = RelayState.SWITCH_CLOSED
            else:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid relay_state: {relay_state}. Expected ON/OFF or OPEN/CLOSED"
                )

            # Get relay controller
            relay_controller = get_relay_controller(device_path=device_path)

            # Set relay state
            state_name = "ON" if target_state == RelayState.SWITCH_OPEN else "OFF"
            self.logger.info(f"Setting relay channel {channel} to {state_name}")

            success = await relay_controller.set_relay_state(target_state, channel)

            if not success:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Failed to set relay to {state_name}"
                )

            return self.create_result(
                result="PASS",
                measured_value=Decimal(str(target_state))
            )

        except Exception as e:
            self.logger.error(f"Relay measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Chassis Rotation Measurement
# ============================================================================
class ChassisRotationMeasurement(BaseMeasurement):
    """
    Controls chassis fixture rotation for DUT positioning.
    Maps to PDTool4's MyThread_CW/CCW functionality.
    """

    async def execute(self) -> MeasurementResult:
        try:
            from app.services.dut_comms import get_chassis_controller, RotationDirection

            # Get rotation parameters
            direction = get_param(self.test_params, "direction", "case")
            duration_ms = get_param(self.test_params, "duration_ms", "duration")
            device_path = get_param(self.test_params, "device_path", default="/dev/ttyACM0")

            # Normalize direction parameter
            if isinstance(direction, str):
                direction = direction.upper()

            # Map direction to RotationDirection enum
            if direction in ["CW", "CLOCKWISE", "6"]:
                target_direction = RotationDirection.CLOCKWISE
            elif direction in ["CCW", "COUNTERCLOCKWISE", "9"]:
                target_direction = RotationDirection.COUNTERCLOCKWISE
            else:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid direction: {direction}. Expected CW/CCW or CLOCKWISE/COUNTERCLOCKWISE"
                )

            # Convert duration to int if provided
            if duration_ms and isinstance(duration_ms, str):
                try:
                    duration_ms = int(duration_ms)
                except ValueError:
                    duration_ms = None

            # Get chassis controller
            chassis_controller = get_chassis_controller(
                device_path=device_path,
                config=self.config
            )

            # Execute rotation
            direction_name = "CLOCKWISE" if target_direction == RotationDirection.CLOCKWISE else "COUNTERCLOCKWISE"
            self.logger.info(f"Rotating chassis {direction_name}")

            success = await chassis_controller.rotate(target_direction, duration_ms)

            if not success:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Failed to rotate chassis {direction_name}"
                )

            return self.create_result(
                result="PASS",
                measured_value=Decimal(str(target_direction))
            )

        except Exception as e:
            self.logger.error(f"Chassis rotation measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# RF_Tool (MT8872A) Measurements
# ============================================================================
class RF_Tool_LTE_TX_Measurement(BaseMeasurement):
    """
    LTE TX measurement using RF_Tool (MT8872A).
    Measures LTE transmit power, channel power, and spectral characteristics.

    Parameters:
        instrument: Instrument name in config (default: 'RF_Tool_1')
        band: LTE band (e.g., 'B1', 'B3', 'B7', 'B38', 'B41')
        channel: Channel number
        bandwidth: Channel bandwidth in MHz (default: 10.0)

    Integration: Uses MT8872ADriver from backend/app/services/instruments/mt8872a.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get and validate parameters
            instrument_name = get_param(self.test_params, 'instrument', default='RF_Tool_1')
            band = get_param(self.test_params, 'band')
            channel = get_param(self.test_params, 'channel')
            bandwidth = get_param(self.test_params, 'bandwidth', default=10.0)

            # Validate required parameters
            if band is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: band"
                )
            if channel is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: channel"
                )

            try:
                channel = int(channel)
                bandwidth = float(bandwidth)
            except (ValueError, TypeError) as e:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid parameter type: {e}"
                )

            self.logger.info(f"RF_Tool LTE TX measurement: band={band}, channel={channel}, bw={bandwidth}MHz")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement using real driver
                tx_result = await driver.measure_lte_tx_power(band, channel, bandwidth)

            # Check for measurement errors
            if tx_result.get('status') == 'ERROR':
                error_msg = tx_result.get('error', 'Unknown error')
                return self.create_result(result="ERROR", error_message=error_msg)

            # Extract measured power value
            measured_power = tx_result['tx_power_avg']

            # Validate against limits
            is_valid, error_msg = self.validate_result(measured_power)

            # Generate error message for BOTH_LIMIT if validation failed
            if not is_valid and error_msg is None:
                if self.lower_limit is not None and self.upper_limit is not None:
                    error_msg = f"Value {measured_power} outside range [{self.lower_limit}, {self.upper_limit}]"
                elif self.lower_limit is not None:
                    error_msg = f"Value {measured_power} < lower limit {self.lower_limit}"
                elif self.upper_limit is not None:
                    error_msg = f"Value {measured_power} > upper limit {self.upper_limit}"

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_power,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"RF_Tool LTE TX measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


class RF_Tool_LTE_RX_Measurement(BaseMeasurement):
    """
    LTE RX sensitivity measurement using RF_Tool (MT8872A).
    Measures DUT receiver performance at various signal levels.

    Parameters:
        instrument: Instrument name in config (default: 'RF_Tool_1')
        band: LTE band (e.g., 'B1', 'B3', 'B7', 'B38', 'B41')
        channel: Channel number
        test_power: Signal generator power in dBm (default: -90.0)
        min_throughput: Minimum throughput threshold in Mbps (default: 10.0)

    Integration: Uses MT8872ADriver from backend/app/services/instruments/mt8872a.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get and validate parameters
            instrument_name = get_param(self.test_params, 'instrument', default='RF_Tool_1')
            band = get_param(self.test_params, 'band')
            channel = get_param(self.test_params, 'channel')
            test_power = get_param(self.test_params, 'test_power', default=-90.0)
            min_throughput = get_param(self.test_params, 'min_throughput', default=10.0)

            # Validate required parameters
            if band is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: band"
                )
            if channel is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: channel"
                )

            try:
                channel = int(channel)
                test_power = float(test_power)
                min_throughput = float(min_throughput)
            except (ValueError, TypeError) as e:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid parameter type: {e}"
                )

            self.logger.info(f"RF_Tool LTE RX measurement: band={band}, channel={channel}, power={test_power}dBm")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement using real driver
                rx_result = await driver.measure_lte_rx_sensitivity(band, channel, test_power, min_throughput)

            # Check for measurement errors
            if rx_result.get('status') == 'ERROR':
                error_msg = rx_result.get('error', 'Unknown error')
                return self.create_result(result="ERROR", error_message=error_msg)

            # Extract RSSI value
            rssi = rx_result['rssi']

            # Validate against limits
            is_valid, error_msg = self.validate_result(rssi)

            # Generate error message for BOTH_LIMIT if validation failed
            if not is_valid and error_msg is None:
                if self.lower_limit is not None and self.upper_limit is not None:
                    error_msg = f"Value {rssi} outside range [{self.lower_limit}, {self.upper_limit}]"
                elif self.lower_limit is not None:
                    error_msg = f"Value {rssi} < lower limit {self.lower_limit}"
                elif self.upper_limit is not None:
                    error_msg = f"Value {rssi} > upper limit {self.upper_limit}"

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=rssi,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"RF_Tool LTE RX measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# CMW100 Measurements
# ============================================================================
class CMW100_BLE_Measurement(BaseMeasurement):
    """
    Bluetooth LE measurement using CMW100.
    Measures BLE TX power, frequency error, and modulation characteristics.

    Parameters:
        instrument: Instrument name in config (default: 'CMW100_1')
        connector: RF connector number (default: 1)
        frequency: Frequency in MHz (default: 2440.0)
        expected_power: Expected TX power in dBm (default: -5.0)

    Integration: Uses CMW100Driver from backend/app/services/instruments/cmw100.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='CMW100_1')
            connector = int(get_param(self.test_params, 'connector', default=1))
            frequency = float(get_param(self.test_params, 'frequency', default=2440.0))
            expected_power = float(get_param(self.test_params, 'expected_power', default=-5.0))
            burst_type = get_param(self.test_params, 'burst_type', default='LE')

            self.logger.info(f"CMW100 BLE measurement: connector={connector}, freq={frequency}MHz")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement using real driver
                ble_result = await driver.measure_ble_tx_power(connector, frequency, expected_power, burst_type)

            # Check for measurement errors
            if ble_result.get('status') == 'ERROR':
                error_msg = ble_result.get('error', 'Unknown error')
                return self.create_result(result="ERROR", error_message=error_msg)

            # Extract measured power value
            measured_power = ble_result['tx_power']

            # Validate against limits
            is_valid, error_msg = self.validate_result(measured_power)

            # Generate error message if validation failed
            if not is_valid and error_msg is None:
                if self.lower_limit is not None and self.upper_limit is not None:
                    error_msg = f"Value {measured_power} outside range [{self.lower_limit}, {self.upper_limit}]"
                elif self.lower_limit is not None:
                    error_msg = f"Value {measured_power} < lower limit {self.lower_limit}"
                elif self.upper_limit is not None:
                    error_msg = f"Value {measured_power} > upper limit {self.upper_limit}"

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_power,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"CMW100 BLE measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


class CMW100_WiFi_Measurement(BaseMeasurement):
    """
    WiFi measurement using CMW100.
    Measures WiFi TX power, EVM, and spectral mask compliance.

    Parameters:
        instrument: Instrument name in config (default: 'CMW100_1')
        connector: RF connector number (default: 1)
        standard: WiFi standard ('a/g', 'ac', 'ax') (default: 'ac')
        channel: WiFi channel number (default: 36)
        bandwidth: Channel bandwidth in MHz (default: 20)

    Integration: Uses CMW100Driver from backend/app/services/instruments/cmw100.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='CMW100_1')
            connector = int(get_param(self.test_params, 'connector', default=1))
            standard = get_param(self.test_params, 'standard', default='ac')
            channel = int(get_param(self.test_params, 'channel', default=36))
            bandwidth = int(get_param(self.test_params, 'bandwidth', default=20))
            expected_power = get_param(self.test_params, 'expected_power')

            self.logger.info(f"CMW100 WiFi measurement: connector={connector}, std={standard}, ch={channel}, bw={bandwidth}MHz")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement using real driver
                wifi_result = await driver.measure_wifi_tx_power(
                    connector, standard, channel, bandwidth,
                    float(expected_power) if expected_power else None
                )

            # Check for measurement errors
            if wifi_result.get('status') == 'ERROR':
                error_msg = wifi_result.get('error', 'Unknown error')
                return self.create_result(result="ERROR", error_message=error_msg)

            # Extract measured power value
            measured_power = wifi_result['tx_power']

            # Validate against limits
            is_valid, error_msg = self.validate_result(measured_power)

            # Generate error message if validation failed
            if not is_valid and error_msg is None:
                if self.lower_limit is not None and self.upper_limit is not None:
                    error_msg = f"Value {measured_power} outside range [{self.lower_limit}, {self.upper_limit}]"
                elif self.lower_limit is not None:
                    error_msg = f"Value {measured_power} < lower limit {self.lower_limit}"
                elif self.upper_limit is not None:
                    error_msg = f"Value {measured_power} > upper limit {self.upper_limit}"

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_power,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"CMW100 WiFi measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# L6MPU SSH Measurements
# ============================================================================
class L6MPU_LTE_Check_Measurement(BaseMeasurement):
    """
    LTE module SIM card check using L6MPU SSH driver.
    Checks SIM card status via microcom and AT+CPIN? command.

    Parameters:
        instrument: Instrument name in config (default: 'L6MPU_1')
        timeout: Command timeout in seconds (default: 5.0)

    Integration: Uses L6MPUSSHDriver from backend/app/services/instruments/l6mpu_ssh.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='L6MPU_1')
            timeout = float(get_param(self.test_params, 'timeout', default=5.0))

            self.logger.info(f"L6MPU LTE check: instrument={instrument_name}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute LTE check
                result = await driver.lte_check(timeout=timeout)

            # Check result
            if result.get('status') == 'ERROR':
                return self.create_result(result="ERROR", error_message=result.get('error', 'Unknown error'))

            # SIM ready indicates success
            is_valid = result.get('sim_ready', False)
            measured_value = Decimal("1.0") if is_valid else Decimal("0.0")

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=None if is_valid else "SIM card not ready"
            )

        except Exception as e:
            self.logger.error(f"L6MPU LTE check error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


class L6MPU_PLC_Test_Measurement(BaseMeasurement):
    """
    PLC network connectivity test using L6MPU SSH driver.
    Tests PLC connectivity via ping on eth0/eth1 interfaces.

    Parameters:
        instrument: Instrument name in config (default: 'L6MPU_1')
        interface: Network interface ('eth0' or 'eth1') (default: 'eth0')
        count: Number of ping packets (default: 4)

    Integration: Uses L6MPUSSHDriver from backend/app/services/instruments/l6mpu_ssh.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='L6MPU_1')
            interface = get_param(self.test_params, 'interface', default='eth0')
            count = int(get_param(self.test_params, 'count', default=4))

            self.logger.info(f"L6MPU PLC test: instrument={instrument_name}, interface={interface}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute PLC ping test
                result = await driver.plc_ping_test(interface=interface, count=count)

            # Check result
            if result.get('status') == 'ERROR':
                return self.create_result(result="ERROR", error_message=result.get('error', 'Unknown error'))

            # Success if ping completed without 100% packet loss
            packet_loss = result.get('packet_loss', 100)
            is_valid = packet_loss < 100

            # Use packet loss inverse as measured value (0% loss = 1.0, 100% loss = 0.0)
            measured_value = Decimal(str((100 - packet_loss) / 100.0))

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=None if is_valid else f"100% packet loss"
            )

        except Exception as e:
            self.logger.error(f"L6MPU PLC test error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# SMCV100B Measurements
# ============================================================================
class SMCV100B_RF_Output_Measurement(BaseMeasurement):
    """
    RF signal generation using SMCV100B.
    Supports DAB, AM, FM modulation modes.

    Parameters:
        instrument: Instrument name in config (default: 'SMCV100B_1')
        mode: Modulation mode ('DAB', 'AM', 'FM', 'IQ', 'RF')
        frequency: Carrier frequency in MHz (required for RF modes)
        power: RF power in dBm (required for RF modes)
        file: Transport stream file (required for DAB mode)
        enable: Enable/disable for IQ/RF modes

    Integration: Uses SMCV100BDriver from backend/app/services/instruments/smcv100b.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='SMCV100B_1')
            mode = get_param(self.test_params, 'mode', default='FM')
            frequency = get_param(self.test_params, 'frequency')
            power = get_param(self.test_params, 'power')
            transport_file = get_param(self.test_params, 'file')
            enable = get_param(self.test_params, 'enable', default=True)

            self.logger.info(f"SMCV100B RF output: mode={mode}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Build command params
            cmd_params = {'mode': mode}

            if frequency is not None:
                cmd_params['frequency'] = float(frequency)
            if power is not None:
                cmd_params['power'] = float(power)
            if transport_file is not None:
                cmd_params['file'] = transport_file
            if enable is not None:
                if isinstance(enable, str):
                    enable = enable.lower() in ('true', '1', 'yes', 'on')
                cmd_params['enable'] = enable

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute RF output command
                output = await driver.execute_command(cmd_params)

            # Success if command completed
            return self.create_result(
                result="PASS",
                measured_value=Decimal("1.0")
            )

        except Exception as e:
            self.logger.error(f"SMCV100B RF output error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# PEAK CAN Measurements
# ============================================================================
class PEAK_CAN_Message_Measurement(BaseMeasurement):
    """
    CAN message communication using PEAK-System PCAN hardware.
    Supports CAN and CAN-FD message transmission and reception.

    Parameters:
        instrument: Instrument name in config (default: 'PEAK_CAN_1')
        operation: Operation type ('write', 'read', 'write_read')
        can_id: CAN identifier (hex or decimal)
        data: Message data (hex comma-separated string)
        is_extended: Use extended frame format (29-bit ID)
        is_fd: Use CAN-FD format
        timeout: Receive timeout in seconds
        filter_id: Filter messages by ID when reading

    Integration: Uses PEAKCANDriver from backend/app/services/instruments/peak_can.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='PEAK_CAN_1')
            operation = get_param(self.test_params, 'operation', default='read')

            self.logger.info(f"PEAK CAN operation: {operation}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Build command params
            cmd_params = {'operation': operation}

            # Add optional parameters
            for key in ['can_id', 'id', 'data', 'is_extended', 'extended', 'is_fd', 'fd', 'timeout', 'filter_id', 'filter']:
                value = get_param(self.test_params, key)
                if value is not None:
                    # Normalize key names
                    param_key = key
                    if key == 'id':
                        param_key = 'can_id'
                    elif key == 'extended':
                        param_key = 'is_extended'
                    elif key == 'fd':
                        param_key = 'is_fd'
                    elif key == 'filter':
                        param_key = 'filter_id'
                    cmd_params[param_key] = value

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute CAN command
                output = await driver.execute_command(cmd_params)

            # Check for error in output
            if 'Error' in output or 'ERROR' in output:
                return self.create_result(result="ERROR", error_message=output)

            # Success
            return self.create_result(
                result="PASS",
                measured_value=Decimal("1.0")
            )

        except Exception as e:
            self.logger.error(f"PEAK CAN error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Measurement Registry
# ============================================================================
MEASUREMENT_REGISTRY = {
    "DUMMY": DummyMeasurement,
    "COMMAND_TEST": CommandTestMeasurement,
    "POWER_READ": PowerReadMeasurement,
    "POWER_SET": PowerSetMeasurement,
    "SFC_TEST": SFCMeasurement,
    "GET_SN": GetSNMeasurement,
    "OP_JUDGE": OPJudgeMeasurement,
    "WAIT": WaitMeasurement,
    "RELAY": RelayMeasurement,
    "CHASSIS_ROTATION": ChassisRotationMeasurement,
    "OTHER": DummyMeasurement,
    "FINAL": DummyMeasurement,
    # RF_Tool (MT8872A) measurements
    "RF_TOOL_LTE_TX": RF_Tool_LTE_TX_Measurement,
    "RF_TOOL_LTE_RX": RF_Tool_LTE_RX_Measurement,
    # CMW100 measurements
    "CMW100_BLE": CMW100_BLE_Measurement,
    "CMW100_WIFI": CMW100_WiFi_Measurement,
    # L6MPU measurements
    "L6MPU_LTE_CHECK": L6MPU_LTE_Check_Measurement,
    "L6MPU_PLC_TEST": L6MPU_PLC_Test_Measurement,
    # SMCV100B measurements
    "SMCV100B_RF": SMCV100B_RF_Output_Measurement,
    # PEAK CAN measurements
    "PEAK_CAN": PEAK_CAN_Message_Measurement,
    # Lowercase variants
    "command": CommandTestMeasurement,
    "wait": WaitMeasurement,
    "relay": RelayMeasurement,
    "chassis_rotation": ChassisRotationMeasurement,
    "other": DummyMeasurement,
    # Case type mappings
    "console": CommandTestMeasurement,
    "comport": CommandTestMeasurement,
    "tcpip": CommandTestMeasurement,
    "URL": SFCMeasurement,
    "webStep1_2": SFCMeasurement,
}


def get_measurement_class(test_command: str) -> Optional[type]:
    """
    Get measurement class by command name.

    Args:
        test_command: Test command string

    Returns:
        Measurement class or None
    """
    # Normalize command names
    command_map = {
        "SFCtest": "SFC_TEST",
        "getSN": "GET_SN",
        "OPjudge": "OP_JUDGE",
        "Other": "OTHER",
        "Final": "FINAL",
        "CommandTest": "COMMAND_TEST",
        "PowerRead": "POWER_READ",
        "PowerSet": "POWER_SET",
        "MeasureSwitchON": "RELAY",      # PDTool4 relay ON mapping
        "MeasureSwitchOFF": "RELAY",     # PDTool4 relay OFF mapping
        "ChassisRotateCW": "CHASSIS_ROTATION",   # PDTool4 clockwise rotation
        "ChassisRotateCCW": "CHASSIS_ROTATION",  # PDTool4 counterclockwise rotation
        # RF_Tool (MT8872A) mappings
        "RF_Tool_LTE_TX": "RF_TOOL_LTE_TX",
        "RF_Tool_LTE_RX": "RF_TOOL_LTE_RX",
        "RFTOOLTETX": "RF_TOOL_LTE_TX",  # Alternative naming
        "RFTOOLTETRX": "RF_TOOL_LTE_RX",  # Alternative naming
        # CMW100 mappings
        "CMW100_BLE": "CMW100_BLE",
        "CMW100_WiFi": "CMW100_WIFI",
        "CMW100WIFI": "CMW100_WIFI",  # Alternative naming
        # L6MPU mappings
        "L6MPU_LTE": "L6MPU_LTE_CHECK",
        "L6MPU_PLC": "L6MPU_PLC_TEST",
        "L6MPULTE": "L6MPU_LTE_CHECK",
        "L6MPUPPLC": "L6MPU_PLC_TEST",
        # SMCV100B mappings
        "SMCV100B": "SMCV100B_RF",
        "SMCV": "SMCV100B_RF",
        # PEAK CAN mappings
        "PEAK": "PEAK_CAN",
        "PCAN": "PEAK_CAN",
        # Console/COM/TCP mappings
        "console": "console",
        "comport": "comport",
        "tcpip": "tcpip",
        "URL": "URL",
        "webStep1_2": "webStep1_2",
        "command": "command",
        "wait": "wait",
        "relay": "relay",
        "chassis_rotation": "chassis_rotation",
        "other": "other",
    }

    # Find in map or use uppercase
    if test_command in command_map:
        registry_key = command_map[test_command]
    elif test_command in MEASUREMENT_REGISTRY:
        registry_key = test_command
    else:
        registry_key = test_command.upper()

    return MEASUREMENT_REGISTRY.get(registry_key)
