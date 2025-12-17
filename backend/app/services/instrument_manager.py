"""
Instrument Manager Service
Manages instrument connections and communication
"""
from typing import Dict, Any, Optional
import asyncio
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class InstrumentConnection:
    """Base class for instrument connections"""
    
    def __init__(self, instrument_id: str, config: Dict[str, Any]):
        self.instrument_id = instrument_id
        self.config = config
        self.is_connected = False
        self.logger = logging.getLogger(f"Instrument.{instrument_id}")
    
    async def connect(self):
        """Connect to instrument"""
        self.logger.info(f"Connecting to instrument: {self.instrument_id}")
        # To be implemented by specific instrument types
        self.is_connected = True
    
    async def disconnect(self):
        """Disconnect from instrument"""
        self.logger.info(f"Disconnecting from instrument: {self.instrument_id}")
        self.is_connected = False
    
    async def send_command(self, command: str) -> str:
        """Send command to instrument and get response"""
        raise NotImplementedError("Subclass must implement send_command")


class InstrumentManager:
    """
    Singleton Instrument Manager
    Manages all instrument connections and ensures proper resource management
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.instruments: Dict[str, InstrumentConnection] = {}
        self.usage_count: Dict[str, int] = defaultdict(int)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_instrument(
        self,
        instrument_id: str,
        instrument_type: str,
        config: Dict[str, Any]
    ) -> InstrumentConnection:
        """
        Get or create instrument connection
        
        Args:
            instrument_id: Unique instrument identifier
            instrument_type: Type of instrument (e.g., 'DAQ973A', 'MODEL2303')
            config: Instrument configuration
            
        Returns:
            InstrumentConnection instance
        """
        async with self._lock:
            if instrument_id not in self.instruments:
                # Create new instrument connection based on type
                instrument = self._create_instrument(instrument_id, instrument_type, config)
                await instrument.connect()
                self.instruments[instrument_id] = instrument
                self.logger.info(f"Created new instrument connection: {instrument_id}")
            
            self.usage_count[instrument_id] += 1
            return self.instruments[instrument_id]
    
    def _create_instrument(
        self,
        instrument_id: str,
        instrument_type: str,
        config: Dict[str, Any]
    ) -> InstrumentConnection:
        """
        Factory method to create specific instrument types
        
        Args:
            instrument_id: Instrument ID
            instrument_type: Type of instrument
            config: Configuration
            
        Returns:
            InstrumentConnection instance
        """
        # Map instrument types to their connection classes
        # For now, return base connection (to be extended with specific implementations)
        self.logger.info(f"Creating instrument: {instrument_type} with ID: {instrument_id}")
        return InstrumentConnection(instrument_id, config)
    
    async def release_instrument(self, instrument_id: str):
        """
        Release instrument (decrement usage count)
        
        Args:
            instrument_id: Instrument ID to release
        """
        async with self._lock:
            if instrument_id in self.usage_count:
                self.usage_count[instrument_id] -= 1
                
                # If no longer in use, optionally disconnect
                if self.usage_count[instrument_id] <= 0:
                    self.logger.info(f"Instrument {instrument_id} no longer in use")
                    # Keep connection for reuse, but can be configured to disconnect
    
    async def disconnect_all(self):
        """Disconnect all instruments"""
        async with self._lock:
            self.logger.info("Disconnecting all instruments")
            for instrument_id, instrument in self.instruments.items():
                try:
                    await instrument.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting {instrument_id}: {e}")
            
            self.instruments.clear()
            self.usage_count.clear()
    
    async def reset_instrument(self, instrument_id: str):
        """
        Reset specific instrument
        
        Args:
            instrument_id: Instrument ID to reset
        """
        async with self._lock:
            if instrument_id in self.instruments:
                instrument = self.instruments[instrument_id]
                try:
                    await instrument.disconnect()
                    await instrument.connect()
                    self.logger.info(f"Reset instrument: {instrument_id}")
                except Exception as e:
                    self.logger.error(f"Error resetting {instrument_id}: {e}")
                    raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all instruments
        
        Returns:
            Dictionary with instrument status information
        """
        return {
            "instruments": {
                inst_id: {
                    "connected": inst.is_connected,
                    "usage_count": self.usage_count.get(inst_id, 0),
                    "type": inst.__class__.__name__
                }
                for inst_id, inst in self.instruments.items()
            },
            "total_instruments": len(self.instruments)
        }


# Global instrument manager instance
instrument_manager = InstrumentManager()
