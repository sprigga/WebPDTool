"""
Modbus Listener Manager
Singleton service that manages all active Modbus listeners
"""
import asyncio
import logging
from typing import Dict, Optional
from app.schemas.modbus import ModbusConfigCreate
from app.services.modbus.modbus_listener import ModbusListenerService


logger = logging.getLogger(__name__)


class ModbusManager:
    """
    Singleton manager for Modbus listeners

    Manages lifecycle of all ModbusListenerService instances.
    Provides centralized control and status monitoring.
    """

    def __init__(self):
        self.active_listeners: Dict[int, ModbusListenerService] = {}
        self._lock = asyncio.Lock()

    async def start_listener(
        self,
        config: ModbusConfigCreate,
        on_sn_received: Optional[callable] = None,
        on_error: Optional[callable] = None,
        on_connected: Optional[callable] = None,
        on_cycle: Optional[callable] = None,
    ) -> ModbusListenerService:
        """
        Start a Modbus listener for a station

        Args:
            config: Modbus configuration
            on_sn_received: Callback when SN is received
            on_error: Callback when error occurs
            on_connected: Callback when TCP connection state changes (bool)
            on_cycle: Callback each polling cycle with current cycle_count (int)

        Returns:
            ModbusListenerService instance
        """
        async with self._lock:
            # Check if already running
            if config.station_id in self.active_listeners:
                logger.warning(f"Listener for station {config.station_id} already running")
                return self.active_listeners[config.station_id]

            # Create listener
            listener = ModbusListenerService(config)

            # Set callbacks
            if on_sn_received:
                listener.on_sn_received = on_sn_received
            if on_error:
                listener.on_error = on_error
            if on_connected:
                listener.on_connected = on_connected
            if on_cycle:
                listener.on_cycle = on_cycle

            # Start listener
            await listener.start()

            # Store in active listeners
            self.active_listeners[config.station_id] = listener

            logger.info(f"Started Modbus listener for station {config.station_id}")

            return listener

    async def stop_listener(self, station_id: int) -> None:
        """
        Stop a Modbus listener

        Args:
            station_id: Station ID
        """
        async with self._lock:
            listener = self.active_listeners.get(station_id)
            if listener:
                await listener.stop()
                del self.active_listeners[station_id]
                logger.info(f"Stopped Modbus listener for station {station_id}")

    async def stop_all(self) -> None:
        """Stop all active listeners"""
        station_ids = list(self.active_listeners.keys())
        for station_id in station_ids:
            await self.stop_listener(station_id)

    def get_listener(self, station_id: int) -> Optional[ModbusListenerService]:
        """Get active listener for a station"""
        return self.active_listeners.get(station_id)

    def get_status(self, station_id: int) -> Optional[Dict]:
        """Get status of a listener"""
        listener = self.active_listeners.get(station_id)
        if listener:
            return listener.get_status()
        return None

    def get_all_statuses(self) -> Dict[int, Dict]:
        """Get status of all active listeners"""
        return {
            station_id: listener.get_status()
            for station_id, listener in self.active_listeners.items()
        }

    async def write_test_result(self, station_id: int, passed: bool) -> bool:
        """
        Write test result for a station

        Args:
            station_id: Station ID
            passed: True for PASS, False for FAIL

        Returns:
            True if successful, False otherwise
        """
        listener = self.active_listeners.get(station_id)
        if listener:
            await listener.write_test_result(passed)
            return True
        return False


# Singleton instance
modbus_manager = ModbusManager()
