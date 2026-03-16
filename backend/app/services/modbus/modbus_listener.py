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

        # Statistics
        self.cycle_count = 0
        self.start_time: Optional[datetime] = None
        self.last_sn: Optional[str] = None
        self.last_error: Optional[str] = None

        # Callbacks (replace Qt Signals)
        self.on_sn_received: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None

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
        logger.info(f"Modbus listener stopped for station {self.station_id}")

    async def _run_async(self) -> None:
        """
        Main async listening loop

        Polls Modbus device for SN, handles connection errors
        """
        from pymodbus.client import AsyncModbusTcpClient
        from pymodbus.exceptions import ModbusException

        delay_time = int(self.modbus_scheme["Delay"])

        try:
            # Create client in async context
            if self.client is None:
                self.client = AsyncModbusTcpClient(
                    host=self.server_host,
                    port=self.server_port
                )

            # Connect to device
            if not self.client.connected:
                await self.client.connect()

            # Main polling loop
            while self.running:
                # Check connection
                if not self.client.connected:
                    errmsg = f"Cannot connect to Modbus server {self.server_host}:{self.server_port}"
                    self.last_error = errmsg
                    if self.on_error:
                        self.on_error(errmsg)
                    logger.error(errmsg)
                    # Try to reconnect
                    await self.client.connect()

                if self.client.connected:
                    self.connected = True

                    try:
                        # Read ready status
                        ready_status = await self._read_registers_async()

                        if ready_status == 0x01:
                            # SN ready, read it
                            await self._read_sn_async()

                        # Clear error on success
                        self.last_error = None

                        self.cycle_count += 1
                        logger.debug(f"Device {self.device_id} listening cycle {self.cycle_count}")

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
                slave=self.device_id
            )

            if rr.isError():
                logger.warning('Unable to read status data.')
                return None

            return rr.registers[0] if rr.registers else None

        except ModbusException as e:
            logger.error(f'Modbus error reading status: {e}')
            return None

    async def _read_sn_async(self) -> None:
        """
        Read SN from Modbus device and emit callback
        """
        from pymodbus.exceptions import ModbusException

        sn_address = self._str2hex(self.modbus_scheme["read_sn_Add"])
        sn_length = self._str2hex(self.modbus_scheme["read_sn_Len"])

        test_status_address = self._str2hex(self.modbus_scheme["test_status_Add"])
        in_testing_value = self._str2hex(self.modbus_scheme["in_testing_Val"])

        try:
            # Read SN registers
            rr = await self.client.read_holding_registers(
                address=sn_address,
                count=sn_length,
                slave=self.device_id
            )

            if rr.isError():
                logger.warning('Unable to read SN data.')
                return

            registers_sn = rr.registers

            # Write test status = "in testing"
            wr = await self.client.write_register(
                address=test_status_address,
                value=in_testing_value,
                slave=self.device_id
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
                slave=self.device_id
            )

            if wr2.isError():
                logger.warning("Failed to write test result.")

            if registers_sn:
                logger.info(f"SN Register values = {registers_sn}")

            # Decode SN from registers
            ascii_string = self._decode_sn(registers_sn or [])
            self.last_sn = ascii_string

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
                slave=self.device_id
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
                slave=self.device_id
            )

            if wr2.isError():
                logger.warning("Failed to write test result.")
            else:
                logger.info(f"Wrote test result {result_value} to register {test_result_address}")

            # Verify write
            rr = await self.client.read_holding_registers(
                address=test_result_address,
                count=result_length,
                slave=self.device_id
            )

            if not rr.isError() and rr.registers:
                logger.info(f"Test Result = {rr.registers[0]}")
            else:
                logger.warning('Unable to read test result.')

        except ModbusException as e:
            logger.error(f'Modbus error in write_test_result: {e}')

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
                slave=self.device_id
            )
            if wr.isError():
                logger.warning("Failed to reset ready status.")
        except ModbusException as e:
            logger.error(f'Modbus error resetting ready status: {e}')

    def _str2hex(self, hex_str: str) -> int:
        """Convert hex string to integer"""
        return int(hex_str, 16)

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
