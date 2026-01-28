"""
Modern Instrument Connection Manager
Refactored from PDTool4's remote_instrument.py with async support
"""
from typing import Optional, Dict, Any, Union
from abc import ABC, abstractmethod
import asyncio
import logging
from contextlib import asynccontextmanager

from app.core.instrument_config import (
    InstrumentConfig,
    VISAAddress,
    SerialAddress,
    TCPIPSocketAddress,
    GPIBAddress,
    get_instrument_settings
)

logger = logging.getLogger(__name__)


# ============================================================================
# Instrument Connection Exceptions
# ============================================================================

class InstrumentError(Exception):
    """Base exception for instrument errors"""
    pass


class InstrumentNotFoundError(InstrumentError):
    """Instrument not found or not configured"""
    pass


class InstrumentConnectionError(InstrumentError):
    """Failed to connect to instrument"""
    pass


class InstrumentCommandError(InstrumentError):
    """Failed to execute instrument command"""
    pass


# ============================================================================
# Base Instrument Connection
# ============================================================================

class BaseInstrumentConnection(ABC):
    """
    Abstract base class for instrument connections

    Replaces PDTool4's direct pyvisa/serial usage with async-compatible interface
    """

    def __init__(self, config: InstrumentConfig):
        self.config = config
        self.is_connected = False
        self.logger = logging.getLogger(f"Instrument.{config.id}")
        self._resource = None

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to instrument"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to instrument"""
        pass

    @abstractmethod
    async def write(self, command: str) -> None:
        """Write command to instrument"""
        pass

    @abstractmethod
    async def query(self, command: str) -> str:
        """Query instrument and return response"""
        pass

    @abstractmethod
    async def read(self) -> str:
        """Read response from instrument"""
        pass

    async def reset(self) -> None:
        """Reset instrument to default state"""
        try:
            await self.write("*RST")
            await asyncio.sleep(0.5)
            self.logger.info(f"Instrument {self.config.id} reset successfully")
        except Exception as e:
            self.logger.warning(f"Failed to reset instrument {self.config.id}: {e}")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.config.id}, connected={self.is_connected})>"


# ============================================================================
# VISA Instrument Connection
# ============================================================================

class VISAInstrumentConnection(BaseInstrumentConnection):
    """
    VISA-based instrument connection (USB, LAN, GPIB)

    Uses pyvisa with async wrappers
    """

    def __init__(self, config: InstrumentConfig):
        super().__init__(config)
        self._rm = None

    async def connect(self) -> bool:
        """Connect to VISA instrument"""
        try:
            # Import pyvisa only when needed (optional dependency)
            import pyvisa

            # Run blocking VISA operations in thread pool
            loop = asyncio.get_event_loop()

            def _connect():
                rm = pyvisa.ResourceManager()
                address = self.config.connection.address
                timeout = self.config.connection.timeout
                resource = rm.open_resource(address, timeout=timeout)

                # Configure VISA-specific settings
                if isinstance(self.config.connection, SerialAddress):
                    self._setup_serial(resource, self.config.connection)
                elif isinstance(self.config.connection, TCPIPSocketAddress):
                    self._setup_tcpip_socket(resource)

                return rm, resource

            self._rm, self._resource = await loop.run_in_executor(None, _connect)
            self.is_connected = True
            self.logger.info(f"Connected to {self.config.id} at {self.config.connection.address}")
            return True

        except ImportError:
            raise InstrumentConnectionError(
                f"pyvisa not installed. Install with: pip install pyvisa pyvisa-py"
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.config.id}: {e}")
            raise InstrumentConnectionError(f"Connection failed: {e}")

    async def disconnect(self) -> bool:
        """Disconnect from VISA instrument"""
        try:
            if self._resource:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._resource.close)
                self._resource = None

            if self._rm:
                self._rm = None

            self.is_connected = False
            self.logger.info(f"Disconnected from {self.config.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error disconnecting from {self.config.id}: {e}")
            return False

    async def write(self, command: str) -> None:
        """Write command to instrument"""
        if not self.is_connected or not self._resource:
            raise InstrumentConnectionError(f"Not connected to {self.config.id}")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._resource.write, command)
            self.logger.debug(f"Wrote to {self.config.id}: {command}")
        except Exception as e:
            raise InstrumentCommandError(f"Write failed: {e}")

    async def query(self, command: str) -> str:
        """Query instrument and return response"""
        if not self.is_connected or not self._resource:
            raise InstrumentConnectionError(f"Not connected to {self.config.id}")

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._resource.query, command)
            self.logger.debug(f"Queried {self.config.id}: {command} -> {response}")
            return response.strip()
        except Exception as e:
            raise InstrumentCommandError(f"Query failed: {e}")

    async def read(self) -> str:
        """Read response from instrument"""
        if not self.is_connected or not self._resource:
            raise InstrumentConnectionError(f"Not connected to {self.config.id}")

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._resource.read)
            return response.strip()
        except Exception as e:
            raise InstrumentCommandError(f"Read failed: {e}")

    def _setup_serial(self, resource, config: SerialAddress):
        """Configure serial port settings"""
        from pyvisa import constants

        self.logger.debug(f"Configuring serial port: {config.baudrate} baud, {config.stopbits} stop bits")
        resource.set_visa_attribute(constants.VI_ATTR_ASRL_BAUD, config.baudrate)

        if config.stopbits != 0:
            if config.stopbits == 1:
                resource.set_visa_attribute(constants.VI_ATTR_ASRL_STOP_BITS, constants.VI_ASRL_STOP_ONE)
            elif config.stopbits == 2:
                resource.set_visa_attribute(constants.VI_ATTR_ASRL_STOP_BITS, constants.VI_ASRL_STOP_TWO)

    def _setup_tcpip_socket(self, resource):
        """Configure TCP/IP socket settings"""
        from pyvisa import constants

        self.logger.debug("Configuring TCP/IP socket")
        resource.set_visa_attribute(constants.VI_ATTR_TERMCHAR_EN, constants.VI_TRUE)
        resource.set_visa_attribute(constants.VI_ATTR_TERMCHAR, 10)  # LF
        resource.set_visa_attribute(constants.VI_ATTR_SEND_END_EN, constants.VI_TRUE)


# ============================================================================
# Serial Instrument Connection (pyserial)
# ============================================================================

class SerialInstrumentConnection(BaseInstrumentConnection):
    """
    Direct serial port connection using pyserial

    For instruments that don't support VISA
    """

    async def connect(self) -> bool:
        """Connect to serial instrument"""
        try:
            import serial

            config = self.config.connection
            if not isinstance(config, SerialAddress):
                raise InstrumentConnectionError("Invalid configuration for serial connection")

            loop = asyncio.get_event_loop()

            def _connect():
                return serial.Serial(
                    port=config.port,
                    baudrate=config.baudrate,
                    timeout=config.timeout / 1000.0,  # Convert ms to seconds
                    stopbits=config.stopbits,
                    parity=config.parity,
                    bytesize=config.bytesize
                )

            self._resource = await loop.run_in_executor(None, _connect)
            self.is_connected = True
            self.logger.info(f"Connected to {self.config.id} on {config.port}")
            return True

        except ImportError:
            raise InstrumentConnectionError(
                "pyserial not installed. Install with: pip install pyserial"
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.config.id}: {e}")
            raise InstrumentConnectionError(f"Serial connection failed: {e}")

    async def disconnect(self) -> bool:
        """Disconnect from serial instrument"""
        try:
            if self._resource:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._resource.close)
                self._resource = None

            self.is_connected = False
            self.logger.info(f"Disconnected from {self.config.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error disconnecting from {self.config.id}: {e}")
            return False

    async def write(self, command: str) -> None:
        """Write command to instrument"""
        if not self.is_connected or not self._resource:
            raise InstrumentConnectionError(f"Not connected to {self.config.id}")

        try:
            loop = asyncio.get_event_loop()
            data = command.encode() + b'\n'
            await loop.run_in_executor(None, self._resource.write, data)
            self.logger.debug(f"Wrote to {self.config.id}: {command}")
        except Exception as e:
            raise InstrumentCommandError(f"Write failed: {e}")

    async def query(self, command: str) -> str:
        """Query instrument and return response"""
        await self.write(command)
        return await self.read()

    async def read(self) -> str:
        """Read response from instrument"""
        if not self.is_connected or not self._resource:
            raise InstrumentConnectionError(f"Not connected to {self.config.id}")

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._resource.readline)
            return response.decode().strip()
        except Exception as e:
            raise InstrumentCommandError(f"Read failed: {e}")


# ============================================================================
# Simulation Instrument Connection (for testing)
# ============================================================================

class SimulationInstrumentConnection(BaseInstrumentConnection):
    """
    Simulated instrument connection for testing without hardware
    """

    def __init__(self, config: InstrumentConfig):
        super().__init__(config)
        self._command_history: list[str] = []

    async def connect(self) -> bool:
        """Simulate connection"""
        await asyncio.sleep(0.1)  # Simulate connection delay
        self.is_connected = True
        self.logger.info(f"[SIMULATION] Connected to {self.config.id}")
        return True

    async def disconnect(self) -> bool:
        """Simulate disconnection"""
        self.is_connected = False
        self.logger.info(f"[SIMULATION] Disconnected from {self.config.id}")
        return True

    async def write(self, command: str) -> None:
        """Simulate write"""
        if not self.is_connected:
            raise InstrumentConnectionError(f"Not connected to {self.config.id}")

        self._command_history.append(command)
        self.logger.debug(f"[SIMULATION] Wrote to {self.config.id}: {command}")

    async def query(self, command: str) -> str:
        """Simulate query with dummy response"""
        await self.write(command)

        # Simulate responses based on command
        if "*IDN?" in command:
            return f"Simulated,{self.config.type},SN12345,v1.0"
        elif "MEAS" in command or "?" in command:
            return "1.234"
        elif command == "*RST":
            return ""
        else:
            return "OK"

    async def read(self) -> str:
        """Simulate read"""
        return "1.234"


# ============================================================================
# Connection Factory
# ============================================================================

def create_instrument_connection(config: InstrumentConfig, simulation: bool = False) -> BaseInstrumentConnection:
    """
    Factory function to create appropriate connection type

    Args:
        config: Instrument configuration
        simulation: Force simulation mode (for testing)

    Returns:
        Appropriate instrument connection instance
    """
    if simulation or not config.enabled:
        return SimulationInstrumentConnection(config)

    conn_type = config.connection.type

    if conn_type == "SERIAL":
        return SerialInstrumentConnection(config)
    elif conn_type in ["VISA", "TCPIP_SOCKET", "GPIB"]:
        return VISAInstrumentConnection(config)
    else:
        logger.warning(f"Unknown connection type {conn_type}, using simulation")
        return SimulationInstrumentConnection(config)


# ============================================================================
# Connection Pool Manager
# ============================================================================

class InstrumentConnectionPool:
    """
    Connection pool for managing multiple instrument connections

    Replaces PDTool4's manual connection tracking with async-safe pool
    """

    def __init__(self):
        self._connections: Dict[str, BaseInstrumentConnection] = {}
        self._usage_count: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)

    @asynccontextmanager
    async def get_connection(self, instrument_id: str, simulation: bool = False):
        """
        Get or create instrument connection (context manager)

        Usage:
            async with pool.get_connection('DAQ973A_1') as conn:
                result = await conn.query('MEAS:VOLT:DC?')
        """
        async with self._lock:
            # Get or create connection
            if instrument_id not in self._connections:
                settings = get_instrument_settings()
                config = settings.get_instrument(instrument_id)

                if config is None:
                    raise InstrumentNotFoundError(
                        f"Instrument {instrument_id} not found in configuration"
                    )

                conn = create_instrument_connection(config, simulation=simulation)
                await conn.connect()
                self._connections[instrument_id] = conn
                self._usage_count[instrument_id] = 0
                self.logger.info(f"Created new connection for {instrument_id}")

            # Increment usage
            conn = self._connections[instrument_id]
            self._usage_count[instrument_id] += 1

        try:
            yield conn
        finally:
            async with self._lock:
                # Decrement usage
                self._usage_count[instrument_id] -= 1

                # Optional: disconnect if no longer in use
                # (commented out to keep connections alive for reuse)
                # if self._usage_count[instrument_id] == 0:
                #     await conn.disconnect()
                #     del self._connections[instrument_id]
                #     del self._usage_count[instrument_id]

    async def disconnect_all(self):
        """Disconnect all instruments"""
        async with self._lock:
            for inst_id, conn in self._connections.items():
                try:
                    await conn.disconnect()
                    self.logger.info(f"Disconnected {inst_id}")
                except Exception as e:
                    self.logger.error(f"Error disconnecting {inst_id}: {e}")

            self._connections.clear()
            self._usage_count.clear()

    async def reset_instrument(self, instrument_id: str):
        """Reset specific instrument"""
        async with self._lock:
            if instrument_id in self._connections:
                conn = self._connections[instrument_id]
                await conn.reset()


# Global connection pool
_connection_pool: Optional[InstrumentConnectionPool] = None


def get_connection_pool() -> InstrumentConnectionPool:
    """Get global connection pool instance"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = InstrumentConnectionPool()
    return _connection_pool
