"""
Modbus Listener Service
Refactored from PDTool4 ModbusListener.py for web architecture

Key differences from PDTool4:
- No Qt Signals (use WebSocket callbacks instead)
- No QThread (runs in FastAPI background task)
- Singleton pattern per station via ModbusManager
- Database-backed configuration
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any

from app.schemas.modbus import ModbusConfigCreate, ModbusConfigResponse
from app.services.modbus.modbus_config import modbus_config_to_dict


logger = logging.getLogger(__name__)


class ModbusListenerService:
    """
    Modbus TCP Listener Service (Async)

    Listens for SN from Modbus device, manages test state, and reports results.
    Replaces PDTool4's Qt-based ModbusListener with FastAPI-compatible async service.

    Lifecycle:
    1. Initialize with config
    2. Start: Connect to Modbus device and begin polling
    3. On SN received: Trigger callback with SN string
    4. On test complete: Write PASS/FAIL result
    5. Stop: Close connection and cleanup
    """

    def __init__(self, config: ModbusConfigCreate):
        """
        Initialize Modbus listener

        Args:
            config: Modbus configuration
        """
        self.station_id = config.station_id
        self.server_host = config.server_host
        self.server_port = config.server_port
        self.device_id = config.device_id
        self.enabled = config.enabled
        self.simulation_mode = config.simulation_mode

        # Modbus client (created in async context, lazy import to allow unit testing without hardware)
        self.client = None

        # Control flags
        self.running = False
        self.connected = False
        self._task: Optional[asyncio.Task] = None
        self._testing = False  # True between sn_received and write_test_result
        self._testing_since: Optional[datetime] = None  # timestamp when _testing was set
        self._testing_timeout_seconds = 300  # auto-clear _testing after 5 min if write_result never arrives

        # Statistics
        self.cycle_count = 0
        self.start_time: Optional[datetime] = None
        self.last_sn: Optional[str] = None
        self.last_error: Optional[str] = None

        # Callbacks (replace Qt Signals)
        self.on_sn_received: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.on_connected: Optional[Callable[[bool], None]] = None  # (connected: bool)
        self.on_cycle: Optional[Callable[[int], None]] = None  # (cycle_count: int)

        # Modbus register configuration (PDTool4 compatible format)
        self.modbus_scheme = modbus_config_to_dict(
            ModbusConfigResponse(**config.model_dump(), id=0)
        )

    async def start(self) -> None:
        """
        Start the Modbus listener

        Creates background task that polls for SN
        """
        if self.running:
            logger.warning(f"Modbus listener for station {self.station_id} already running")
            return

        self.running = True
        self.start_time = datetime.utcnow()
        self.cycle_count = 0

        # Create background task
        self._task = asyncio.create_task(self._run_async())

        logger.info(f"Modbus listener started for station {self.station_id}")

    async def stop(self) -> None:
        """
        Stop the Modbus listener

        Cancels background task and closes connection
        """
        if not self.running:
            return

        self.running = False

        # Cancel background task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Close connection
        if self.client:
            self.client.close()
            self.client = None

        self.connected = False
        self._testing = False
        self._testing_since = None
        logger.info(f"Modbus listener stopped for station {self.station_id}")

    async def inject_sn(self, sn: str) -> None:
        """
        Inject a SN directly (simulation mode only).

        Called by the WebSocket endpoint when action='inject_sn' is received.
        Fires on_sn_received if the listener is running and in simulation mode.
        """
        if not self.simulation_mode:
            logger.warning(f"inject_sn called on station {self.station_id} but simulation_mode is off, ignoring")
            return
        if not self.running:
            logger.warning(f"inject_sn called on station {self.station_id} but listener is not running, ignoring")
            return
        self.last_sn = sn
        if self.on_sn_received:
            self.on_sn_received(sn)

    async def _run_async(self) -> None:
        """
        Main async listening loop

        Polls Modbus device for SN, handles connection errors.
        In simulation_mode, skips real TCP connection and idles (SNs are injected
        via inject_sn / WS action 'inject_sn').
        """
        from pymodbus.exceptions import ModbusException

        delay_time = int(self.modbus_scheme["Delay"])

        # --- Simulation mode: no real TCP client needed ---
        if self.simulation_mode:
            try:
                # Mark as "connected" immediately so status indicators light up
                self.connected = True
                if self.on_connected:
                    self.on_connected(True)
                logger.info(f"Modbus listener station {self.station_id}: simulation mode, waiting for inject_sn")

                while self.running:
                    self.cycle_count += 1
                    if self.on_cycle:
                        self.on_cycle(self.cycle_count)
                    await asyncio.sleep(delay_time)

            except asyncio.CancelledError:
                logger.info(f'Simulation listener for station {self.station_id} cancelled gracefully')
            finally:
                self.connected = False
            return
        # --- End simulation mode ---

        from pymodbus.client import AsyncModbusTcpClient

        try:
            # Create client in async context
            if self.client is None:
                self.client = AsyncModbusTcpClient(
                    host=self.server_host,
                    port=self.server_port
                )

            # Main polling loop — connect handled inside loop for reconnect support
            while self.running:
                # Check connection, reconnect if needed
                if not self.client.connected:
                    connected = await self.client.connect()
                    if not connected:
                        errmsg = f"Cannot connect to Modbus server {self.server_host}:{self.server_port}"
                        self.last_error = errmsg
                        if self.connected:
                            self.connected = False
                            if self.on_connected:
                                self.on_connected(False)
                        # self.connected = False  # moved into the if-block above
                        if self.on_error:
                            self.on_error(errmsg)
                        logger.error(errmsg)
                        # Wait before retry to avoid tight reconnect loop
                        await asyncio.sleep(delay_time)
                        continue

                # Notify on first connection (was False, now True)
                if not self.connected:
                    self.connected = True
                    if self.on_connected:
                        self.on_connected(True)
                # self.connected = True  # moved into the if-block above

                try:
                    # Auto-clear _testing if write_result never arrived within timeout
                    if self._testing and self._testing_since:
                        elapsed = (datetime.utcnow() - self._testing_since).total_seconds()
                        if elapsed > self._testing_timeout_seconds:
                            logger.warning(
                                f"Station {self.station_id}: _testing timed out after {elapsed:.0f}s, "
                                f"clearing flag to allow next SN"
                            )
                            self._testing = False
                            self._testing_since = None

                    # Read ready status
                    ready_status = await self._read_registers_async()

                    if ready_status == 0x01:
                        # SN ready, read it
                        await self._read_sn_async()

                    # Clear error on success
                    self.last_error = None

                    self.cycle_count += 1
                    logger.debug(f"Device {self.device_id} listening cycle {self.cycle_count}")
                    if self.on_cycle:
                        self.on_cycle(self.cycle_count)

                except ModbusException as e:
                    logger.error(f"Modbus operation error: {e}")
                    self.last_error = str(e)
                    if self.on_error:
                        self.on_error(str(e))
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    self.last_error = str(e)
                    if self.on_error:
                        self.on_error(str(e))

                # Wait before next poll
                await asyncio.sleep(delay_time)

        except asyncio.CancelledError:
            logger.info(f'Listener task for station {self.station_id} cancelled gracefully')
        except Exception as e:
            logger.error(f'Error in Modbus listener for station {self.station_id}: {e}')
            self.last_error = str(e)
        finally:
            if self.client:
                self.client.close()
            self.connected = False

    async def _read_registers_async(self) -> Optional[int]:
        """
        Read ready status register

        Returns:
            Register value or None if error
        """
        from pymodbus.exceptions import ModbusException

        address = self._str2hex(self.modbus_scheme["ready_status_Add"])
        count = self._str2hex(self.modbus_scheme["ready_status_Len"])

        try:
            rr = await self.client.read_holding_registers(
                address=address,
                count=count,
                device_id=self.device_id
            )

            if rr.isError():
                logger.warning('Unable to read status data.')
                return None

            value = rr.registers[0] if rr.registers else None
            if value is not None:
                logger.info(
                    f"[Modbus] {self.server_host}:{self.server_port} "
                    f"ReadHoldingReg addr=0x{address:04X} count={count} "
                    f"-> 0x{value:04X} ({value})"
                )
            else:
                logger.info(
                    f"[Modbus] {self.server_host}:{self.server_port} "
                    f"ReadHoldingReg addr=0x{address:04X} count={count} -> (no data)"
                )
            return value

        except ModbusException as e:
            logger.error(f'Modbus error reading status: {e}')
            return None

    async def _read_sn_async(self) -> None:
        """
        Read SN from Modbus device and emit callback
        """
        # Guard: skip if previous test result has not been written back yet
        if self._testing:
            logger.debug(f"Station {self.station_id}: _read_sn skipped, previous test still in progress")
            return

        from pymodbus.exceptions import ModbusException

        sn_address = self._str2hex(self.modbus_scheme["read_sn_Add"])
        sn_length = self._str2hex(self.modbus_scheme["read_sn_Len"])

        ready_status_address = self._str2hex(self.modbus_scheme["ready_status_Add"])
        test_status_address = self._str2hex(self.modbus_scheme["test_status_Add"])
        in_testing_value = self._str2hex(self.modbus_scheme["in_testing_Val"])

        try:
            # Read SN registers
            rr = await self.client.read_holding_registers(
                address=sn_address,
                count=sn_length,
                device_id=self.device_id
            )

            if rr.isError():
                logger.warning('Unable to read SN data.')
                return

            registers_sn = rr.registers

            # Issue 1 fix: clear ready_status (write 0x00) so device stops
            # asserting ready and prevents re-triggering on next poll cycle
            wr_ready = await self.client.write_register(
                address=ready_status_address,
                value=0x00,
                device_id=self.device_id
            )
            if wr_ready.isError():
                logger.warning("Failed to clear ready_status register.")
            else:
                logger.info(f"Cleared ready_status register {ready_status_address}")

            # Write test status = "in testing"
            wr = await self.client.write_register(
                address=test_status_address,
                value=in_testing_value,
                device_id=self.device_id
            )

            if wr.isError():
                logger.warning("Failed to write test status.")
            else:
                logger.info(f"Wrote {in_testing_value} to register {test_status_address}")

            # Reset test result
            test_result_address = self._str2hex(self.modbus_scheme["test_result_Add"])
            test_no_result = self._str2hex(self.modbus_scheme["test_no_Result"])

            wr2 = await self.client.write_register(
                address=test_result_address,
                value=test_no_result,
                device_id=self.device_id
            )

            if wr2.isError():
                logger.warning("Failed to write test result.")

            if registers_sn:
                logger.info(f"SN Register values = {registers_sn}")

            # Decode SN from registers
            ascii_string = self._decode_sn(registers_sn or [])
            self.last_sn = ascii_string

            # Mark testing in progress — prevents re-entry until write_test_result clears it
            self._testing = True
            self._testing_since = datetime.utcnow()

            # Emit callback (replaces Qt Signal)
            if self.on_sn_received:
                self.on_sn_received(ascii_string)

            logger.info(f"SN value = {ascii_string}")

        except ModbusException as e:
            logger.error(f'Modbus error in read_sn: {e}')

    async def write_test_result(self, passed: bool) -> None:
        """
        Write test result (PASS/FAIL) to Modbus device

        Args:
            passed: True for PASS, False for FAIL
        """
        # Simulation mode: no TCP client, skip hardware write
        if self.simulation_mode:
            logger.info(
                f"[Simulation] write_test_result skipped for station {self.station_id}: "
                f"{'PASS' if passed else 'FAIL'}"
            )
            self._testing = False
            self._testing_since = None
            return

        if not self.client or not self.client.connected:
            logger.warning(
                f"write_test_result: no connected client for station {self.station_id}, skipping"
            )
            self._testing = False
            self._testing_since = None
            return

        from pymodbus.exceptions import ModbusException

        test_result_address = self._str2hex(self.modbus_scheme["test_result_Add"])
        result_length = self._str2hex(self.modbus_scheme["test_result_Len"])

        test_status_address = self._str2hex(self.modbus_scheme["test_status_Add"])
        test_finished_value = self._str2hex(self.modbus_scheme["test_finished_Val"])

        try:
            # Write test status = "finished"
            wr1 = await self.client.write_register(
                address=test_status_address,
                value=test_finished_value,
                device_id=self.device_id
            )

            if wr1.isError():
                logger.warning("Failed to write test finished status.")

            # Write PASS/FAIL result
            if passed:
                result_value = self._str2hex(self.modbus_scheme["test_pass_Val"])
            else:
                result_value = self._str2hex(self.modbus_scheme["test_fail_Val"])

            wr2 = await self.client.write_register(
                address=test_result_address,
                value=result_value,
                device_id=self.device_id
            )

            if wr2.isError():
                logger.warning("Failed to write test result.")
            else:
                logger.info(f"Wrote test result {result_value} to register {test_result_address}")

            # Verify write
            rr = await self.client.read_holding_registers(
                address=test_result_address,
                count=result_length,
                device_id=self.device_id
            )

            if not rr.isError() and rr.registers:
                logger.info(f"Test Result = {rr.registers[0]}")
            else:
                logger.warning('Unable to read test result.')

        except ModbusException as e:
            logger.error(f'Modbus error in write_test_result: {e}')
        finally:
            # Clear testing flag so next SN can be accepted on next poll cycle
            self._testing = False
            self._testing_since = None

    async def reset_ready_status(self) -> None:
        """
        Reset ready status register (called after simulation mode)
        """
        from pymodbus.exceptions import ModbusException

        if not self.client or not self.client.connected:
            return

        ready_status_address = self._str2hex(self.modbus_scheme["ready_status_Add"])

        try:
            wr = await self.client.write_register(
                address=ready_status_address,
                value=0x0,
                device_id=self.device_id
            )
            if wr.isError():
                logger.warning("Failed to reset ready status.")
        except ModbusException as e:
            logger.error(f'Modbus error resetting ready status: {e}')

    def _str2hex(self, hex_str: str) -> int:
        """
        Convert address/value strings to pymodbus integers.

        Two formats stored in DB:
          - Register addresses: decimal ModbusTools notation, no '0x' prefix
              e.g. "400022" -> holding register 22 -> wire address 21 (400001-based)
          - Value fields: hex strings with '0x' prefix
              e.g. "0x01" -> 1 (returned as-is)

        Old code: int(hex_str, 16) on "400022" -> 0x400022 (wrong!)
        """
        # Hex value strings (e.g. "0x01", "0x00") — parse as hex, return as-is
        if hex_str.lower().startswith("0x"):
            return int(hex_str, 16)
        # Decimal ModbusTools register addresses (e.g. "400022") — convert to 0-based wire
        val = int(hex_str, 10)
        if val >= 400001:
            return val - 400001
        return val

    def _byte_offset(self, decimal_number: int) -> tuple:
        """
        Split 16-bit register into high and low bytes

        Args:
            decimal_number: 16-bit register value

        Returns:
            Tuple of (high_byte, low_byte)
        """
        high_byte = (decimal_number >> 8) & 0xFF
        low_byte = decimal_number & 0xFF
        return high_byte, low_byte

    def _decode_sn(self, registers: list) -> str:
        """
        Decode SN from Modbus register values

        Each 16-bit register contains 2 ASCII characters (high byte, low byte)

        Args:
            registers: List of register values

        Returns:
            Decoded ASCII string
        """
        ascii_string = ''.join(
            f"{chr(high_byte)}{chr(low_byte)}"
            for decimal_number in registers
            for high_byte, low_byte in [self._byte_offset(decimal_number)]
        )
        return ascii_string.replace('\0', '')

    def get_status(self) -> Dict[str, Any]:
        """
        Get current listener status

        Returns:
            Dictionary with status information
        """
        uptime = None
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "station_id": self.station_id,
            "running": self.running,
            "connected": self.connected,
            "last_sn": self.last_sn,
            "error_message": self.last_error,
            "cycle_count": self.cycle_count,
            "uptime_seconds": uptime
        }
