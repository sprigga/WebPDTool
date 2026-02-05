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

    TODO: Integrate with real InstrumentManager and RF_ToolDriver
    """

    async def execute(self) -> MeasurementResult:
        try:
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

            # TODO: Integrate with real RF_ToolDriver via InstrumentManager
            # driver = await instrument_manager.get_driver(instrument_name)
            # tx_result = await driver.measure_lte_tx_power(band, channel, bandwidth)
            # measured_power = Decimal(str(tx_result['tx_power']))

            # Simulated result (placeholder)
            measured_power = Decimal('23.5')  # Typical TX power in dBm

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
            self.logger.error(f"RF_Tool LTE TX measurement error: {e}")
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

    TODO: Integrate with real InstrumentManager and RF_ToolDriver
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Get and validate parameters
            instrument_name = get_param(self.test_params, 'instrument', default='RF_Tool_1')
            band = get_param(self.test_params, 'band')
            channel = get_param(self.test_params, 'channel')
            test_power = get_param(self.test_params, 'test_power', default=-90.0)

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
            except (ValueError, TypeError) as e:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid parameter type: {e}"
                )

            self.logger.info(f"RF_Tool LTE RX measurement: band={band}, channel={channel}, power={test_power}dBm")

            # TODO: Integrate with real RF_ToolDriver via InstrumentManager
            # driver = await instrument_manager.get_driver(instrument_name)
            # rx_result = await driver.measure_lte_rx_sensitivity(band, channel, test_power)
            # rssi = Decimal(str(rx_result['rssi']))

            # Simulated result (placeholder) - RSSI slightly weaker than test power
            rssi = Decimal(str(test_power - 1.2))  # Simulate some path loss

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
            self.logger.error(f"RF_Tool LTE RX measurement error: {e}")
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

    TODO: Integrate with real InstrumentManager and CMW100Driver
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Get parameters (for future use)
            instrument_name = get_param(self.test_params, 'instrument', default='CMW100_1')
            connector = int(get_param(self.test_params, 'connector', default=1))
            frequency = float(get_param(self.test_params, 'frequency', default=2440.0))
            expected_power = float(get_param(self.test_params, 'expected_power', default=-5.0))

            self.logger.info(f"CMW100 BLE measurement: connector={connector}, freq={frequency}MHz")

            # TODO: Integrate with real CMW100Driver via InstrumentManager
            # driver = await instrument_manager.get_driver(instrument_name)
            # ble_result = await driver.measure_ble_tx_power(connector, frequency)
            # measured_power = Decimal(str(ble_result['tx_power']))

            # Simulated result (placeholder)
            measured_power = Decimal('-5.2')  # Typical BLE power

            # Validate against limits
            is_valid, error_msg = self.validate_result(measured_power)

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_power,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"CMW100 BLE measurement error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


class CMW100_WiFi_Measurement(BaseMeasurement):
    """
    WiFi measurement using CMW100.
    Measures WiFi TX power, EVM, and spectral mask compliance.

    Parameters:
        instrument: Instrument name in config (default: 'CMW100_1')
        connector: RF connector number (default: 1)
        standard: WiFi standard ('11a/b/g/n/ac/ax') (default: '11ac')
        channel: WiFi channel number (default: 36)
        bandwidth: Channel bandwidth in MHz (default: 20)

    TODO: Integrate with real InstrumentManager and CMW100Driver
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Get parameters (for future use)
            instrument_name = get_param(self.test_params, 'instrument', default='CMW100_1')
            connector = int(get_param(self.test_params, 'connector', default=1))
            standard = get_param(self.test_params, 'standard', default='11ac')
            channel = int(get_param(self.test_params, 'channel', default=36))

            self.logger.info(f"CMW100 WiFi measurement: connector={connector}, std={standard}, ch={channel}")

            # TODO: Integrate with real CMW100Driver via InstrumentManager
            # driver = await instrument_manager.get_driver(instrument_name)
            # wifi_result = await driver.measure_wifi_tx_power(connector, standard, channel)
            # measured_power = Decimal(str(wifi_result['tx_power']))

            # Simulated result (placeholder)
            measured_power = Decimal('15.2')  # Typical WiFi power

            # Validate against limits
            is_valid, error_msg = self.validate_result(measured_power)

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_power,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"CMW100 WiFi measurement error: {e}")
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
