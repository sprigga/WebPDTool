"""
Instrument Configuration Management
Replaces PDTool4's test_xml.ini with modern configuration system
"""
from typing import Dict, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
import os
import json


# ============================================================================
# Instrument Connection Models
# ============================================================================

class InstrumentAddress(BaseModel):
    """Base instrument address configuration"""
    type: str  # VISA, SERIAL, TCPIP, GPIB
    address: str
    timeout: int = 5000  # milliseconds


class VISAAddress(InstrumentAddress):
    """VISA instrument address (USB, LAN, GPIB)"""
    type: Literal["VISA"] = "VISA"
    address: str = Field(..., description="VISA resource string, e.g., TCPIP0::192.168.1.1::inst0::INSTR")


class SerialAddress(InstrumentAddress):
    """Serial/COM port instrument address"""
    type: Literal["SERIAL"] = "SERIAL"
    port: str = Field(..., description="COM port name, e.g., COM3 or /dev/ttyUSB0")
    baudrate: int = 115200
    stopbits: int = 1
    parity: str = "N"
    bytesize: int = 8

    @property
    def address(self) -> str:
        """Generate address string for compatibility"""
        return f"{self.port}/baud:{self.baudrate}/bits:{self.stopbits}"


class TCPIPSocketAddress(InstrumentAddress):
    """TCP/IP Socket instrument address"""
    type: Literal["TCPIP_SOCKET"] = "TCPIP_SOCKET"
    host: str
    port: int

    @property
    def address(self) -> str:
        """Generate VISA-style address"""
        return f"TCPIP0::{self.host}::{self.port}::SOCKET"


class GPIBAddress(InstrumentAddress):
    """GPIB instrument address"""
    type: Literal["GPIB"] = "GPIB"
    board: int = 0
    address: int = Field(..., ge=0, le=30)

    @property
    def address(self) -> str:
        """Generate VISA-style address"""
        return f"GPIB{self.board}::{self.address}::INSTR"


# ============================================================================
# Instrument Configuration
# ============================================================================

class InstrumentConfig(BaseModel):
    """Individual instrument configuration"""
    id: str = Field(..., description="Unique instrument identifier, e.g., 'DAQ973A_1'")
    type: str = Field(..., description="Instrument type, e.g., 'DAQ973A', 'MODEL2303'")
    name: str = Field(..., description="Human-readable name")
    connection: InstrumentAddress
    enabled: bool = True
    description: Optional[str] = None


# ============================================================================
# Instrument Settings (replaces test_xml.ini)
# ============================================================================

class InstrumentSettings(BaseSettings):
    """
    Instrument configuration settings

    Can be configured via:
    1. Environment variables (INSTRUMENTS_CONFIG_FILE, INSTRUMENTS_CONFIG_JSON)
    2. JSON configuration file
    3. Database (future enhancement)
    """

    # Configuration source
    INSTRUMENTS_CONFIG_FILE: Optional[str] = Field(
        default=None,
        description="Path to JSON configuration file"
    )

    INSTRUMENTS_CONFIG_JSON: Optional[str] = Field(
        default=None,
        description="Direct JSON configuration string"
    )

    # Loaded instruments
    _instruments: Dict[str, InstrumentConfig] = {}

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

    def model_post_init(self, __context):
        """Load instruments after initialization"""
        self.load_instruments()

    def load_instruments(self):
        """Load instrument configurations from configured source"""
        # Priority 1: JSON string from environment
        if self.INSTRUMENTS_CONFIG_JSON:
            try:
                config_data = json.loads(self.INSTRUMENTS_CONFIG_JSON)
                self._load_from_dict(config_data)
                return
            except json.JSONDecodeError as e:
                print(f"Error parsing INSTRUMENTS_CONFIG_JSON: {e}")

        # Priority 2: JSON file
        if self.INSTRUMENTS_CONFIG_FILE and os.path.exists(self.INSTRUMENTS_CONFIG_FILE):
            try:
                with open(self.INSTRUMENTS_CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                self._load_from_dict(config_data)
                return
            except Exception as e:
                print(f"Error loading config file {self.INSTRUMENTS_CONFIG_FILE}: {e}")

        # Priority 3: Default development configuration
        self._load_default_config()

    def _load_from_dict(self, config_data: dict):
        """Load instruments from dictionary"""
        self._instruments = {}
        for inst_id, inst_data in config_data.get("instruments", {}).items():
            try:
                # Parse connection based on type
                conn_data = inst_data["connection"]
                if conn_data["type"] == "SERIAL":
                    connection = SerialAddress(**conn_data)
                elif conn_data["type"] == "TCPIP_SOCKET":
                    connection = TCPIPSocketAddress(**conn_data)
                elif conn_data["type"] == "GPIB":
                    connection = GPIBAddress(**conn_data)
                else:
                    connection = VISAAddress(**conn_data)

                inst_config = InstrumentConfig(
                    id=inst_id,
                    type=inst_data.get("type", inst_id.split("_")[0]),
                    name=inst_data.get("name", inst_id),
                    connection=connection,
                    enabled=inst_data.get("enabled", True),
                    description=inst_data.get("description")
                )
                self._instruments[inst_id] = inst_config
            except Exception as e:
                print(f"Error loading instrument {inst_id}: {e}")

    def _load_default_config(self):
        """Load default development configuration (simulation mode)"""
        print("Loading default instrument configuration (simulation mode)")
        self._instruments = {
            "DAQ973A_1": InstrumentConfig(
                id="DAQ973A_1",
                type="DAQ973A",
                name="Keysight DAQ973A #1",
                connection=VISAAddress(address="TCPIP0::192.168.1.10::inst0::INSTR"),
                enabled=False,  # Disabled by default in dev
                description="Development simulation instrument"
            ),
            "MODEL2303_1": InstrumentConfig(
                id="MODEL2303_1",
                type="MODEL2303",
                name="Keysight 2303 Power Supply #1",
                connection=VISAAddress(address="TCPIP0::192.168.1.11::inst0::INSTR"),
                enabled=False,
                description="Development simulation instrument"
            ),
            # 新增: 虛擬 command-type 儀器 — 對應 ConSoleMeasurement/ComPortMeasurement/TCPIPMeasurement
            # 這些儀器不需要實體連線，type 欄位用於 get_driver_class() 查找對應 Driver
            # 注意: connection.type 使用 "LOCAL" (非 VISA/SERIAL/TCPIP_SOCKET)
            #       → create_connection() 的 else 分支回傳 SimulationInstrumentConnection
            #       → Driver.initialize() 為 no-op，不需要實體連線
            "console_1": InstrumentConfig(
                id="console_1",
                type="console",
                name="Console Command (default)",
                connection=InstrumentAddress(type="LOCAL", address="local://console"),
                enabled=True,
                description="Virtual instrument for OS subprocess command execution"
            ),
            "comport_1": InstrumentConfig(
                id="comport_1",
                type="comport",
                name="COM Port Command (default)",
                connection=InstrumentAddress(type="LOCAL", address="local://comport"),
                enabled=True,
                description="Virtual instrument for serial port command execution"
            ),
            "tcpip_1": InstrumentConfig(
                id="tcpip_1",
                type="tcpip",
                name="TCP/IP Command (default)",
                connection=InstrumentAddress(type="LOCAL", address="local://tcpip"),
                enabled=True,
                description="Virtual instrument for TCP/IP socket command execution"
            ),
        }

    def get_instrument(self, instrument_id: str) -> Optional[InstrumentConfig]:
        """Get instrument configuration by ID"""
        return self._instruments.get(instrument_id)

    def list_instruments(self) -> Dict[str, InstrumentConfig]:
        """List all configured instruments"""
        return self._instruments.copy()

    def list_enabled_instruments(self) -> Dict[str, InstrumentConfig]:
        """List only enabled instruments"""
        return {
            inst_id: inst
            for inst_id, inst in self._instruments.items()
            if inst.enabled
        }

    def add_instrument(self, config: InstrumentConfig):
        """Add or update instrument configuration"""
        self._instruments[config.id] = config

    def remove_instrument(self, instrument_id: str) -> bool:
        """Remove instrument configuration"""
        if instrument_id in self._instruments:
            del self._instruments[instrument_id]
            return True
        return False

    def save_to_file(self, filepath: str):
        """Save current configuration to JSON file"""
        config_data = {
            "instruments": {
                inst_id: {
                    "type": inst.type,
                    "name": inst.name,
                    "connection": inst.connection.model_dump(),
                    "enabled": inst.enabled,
                    "description": inst.description
                }
                for inst_id, inst in self._instruments.items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)


# ============================================================================
# Global Settings Instance
# ============================================================================

# Singleton instance
_instrument_settings: Optional[InstrumentSettings] = None


def get_instrument_settings() -> InstrumentSettings:
    """Get global instrument settings instance"""
    global _instrument_settings
    if _instrument_settings is None:
        _instrument_settings = InstrumentSettings()
    return _instrument_settings


# 修改: 全域 DB-backed provider singleton，供 ConSoleMeasurement 等 lazy-import 使用
# 原有程式碼: get_instrument_settings() 只回傳 hardcoded InstrumentSettings，無法讀 DB
# 新增: set_global_instrument_provider() 讓 lifespan / startup 注入 DB provider
_global_instrument_provider = None  # type: Optional["InstrumentConfigProvider"]


def set_global_instrument_provider(provider: "InstrumentConfigProvider") -> None:
    """Set the global DB-backed instrument provider (called at app startup)."""
    global _global_instrument_provider
    _global_instrument_provider = provider


def get_global_instrument_provider() -> Optional["InstrumentConfigProvider"]:
    """Return the global DB-backed provider if set, else None."""
    return _global_instrument_provider


# ============================================================================
# Configuration Example JSON Format
# ============================================================================

# ============================================================================
# DB-Backed Instrument Config Provider
# Replaces InstrumentSettings singleton for production use.
# Keeps the same interface: get_instrument(), list_enabled_instruments()
# ============================================================================

import threading
import time as _time


class InstrumentConfigProvider:
    """
    DB-backed instrument configuration provider with in-memory cache.

    Drop-in replacement for InstrumentSettings. Consumers call:
        provider.get_instrument(instrument_id)
        provider.list_enabled_instruments()
        provider.list_instruments()
        provider.invalidate_cache()   # call after CRUD mutations

    cache_ttl: seconds until the full list is refreshed from DB (default 30).
    """

    # Original code: session_factory returning sync Session
    # Modified: Use InstrumentRepository directly (Wave 6 - Task 14)
    def __init__(self, session_factory, cache_ttl: float = 30.0):
        # session_factory: callable returning a new AsyncSession (e.g. AsyncSessionLocal)
        self._session_factory = session_factory
        self._cache_ttl = cache_ttl
        self._cache: Optional[Dict[str, InstrumentConfig]] = None
        self._cache_time: float = 0.0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface (same as InstrumentSettings)
    # ------------------------------------------------------------------

    async def get_instrument(self, instrument_id: str) -> Optional[InstrumentConfig]:
        """Lookup by logical ID. Uses cache; falls back to direct DB query on miss."""
        cached = self._get_cache()
        if cached is not None and instrument_id in cached:
            return cached[instrument_id]
        # Direct DB lookup for a single instrument (avoids full-list refresh)
        db = self._session_factory()
        try:
            from app.repositories.instrument_repository import InstrumentRepository
            repo = InstrumentRepository(db)
            row = await repo.get_by_instrument_id(instrument_id)
            return self._row_to_config(row) if row else None
        finally:
            await db.close()

    async def list_instruments(self) -> Dict[str, InstrumentConfig]:
        """Return all instruments (enabled + disabled). Always fetches fresh from DB
        (intentional — used by admin interfaces that need current state)."""
        return await self._build_all_map()

    async def list_enabled_instruments(self) -> Dict[str, InstrumentConfig]:
        """Return only enabled instruments, using cache."""
        cache = self._get_cache()
        if cache is not None:
            return cache
        return await self._refresh_cache()

    def invalidate_cache(self):
        """Force next call to re-fetch from DB. Call after any CRUD mutation."""
        with self._lock:
            self._cache = None
            self._cache_time = 0.0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_cache(self) -> Optional[Dict[str, InstrumentConfig]]:
        """Return cache copy if still valid, else None. Thread-safe (returns copy while holding lock)."""
        with self._lock:
            if (self._cache is not None and
                    (_time.monotonic() - self._cache_time) < self._cache_ttl):
                return dict(self._cache)  # return a copy while holding lock
        return None

    async def _refresh_cache(self) -> Dict[str, InstrumentConfig]:
        """Fetch enabled instruments from DB, populate cache."""
        with self._lock:
            if (self._cache is not None and
                    (_time.monotonic() - self._cache_time) < self._cache_ttl):
                return dict(self._cache)
        # Open a short-lived session for this refresh (outside lock to avoid blocking other threads during I/O)
        db = self._session_factory()
        try:
            from app.repositories.instrument_repository import InstrumentRepository
            repo = InstrumentRepository(db)
            rows = await repo.list_enabled()
            result = {row.instrument_id: self._row_to_config(row) for row in rows}
        finally:
            await db.close()
        # Two threads may race here if both passed the TTL check above — last writer wins (harmless)
        with self._lock:
            self._cache = result
            self._cache_time = _time.monotonic()
            return dict(result)

    async def _build_all_map(self) -> Dict[str, InstrumentConfig]:
        db = self._session_factory()
        try:
            from app.repositories.instrument_repository import InstrumentRepository
            repo = InstrumentRepository(db)
            rows = await repo.list_all()
            return {row.instrument_id: self._row_to_config(row) for row in rows}
        finally:
            await db.close()

    @staticmethod
    def _row_to_config(row) -> InstrumentConfig:
        """Convert an ORM Instrument row to the existing InstrumentConfig Pydantic model."""
        params = row.conn_params or {}
        conn_type = row.conn_type

        if conn_type == "SERIAL":
            connection = SerialAddress(
                port=params.get("port", "COM1"),
                baudrate=params.get("baudrate", 115200),
                stopbits=params.get("stopbits", 1),
                parity=params.get("parity", "N"),
                bytesize=params.get("bytesize", 8),
                timeout=params.get("timeout", 5000),
            )
        elif conn_type == "TCPIP_SOCKET":
            connection = TCPIPSocketAddress(
                host=params.get("host", "localhost"),
                port=params.get("port", 2268),
                timeout=params.get("timeout", 5000),
            )
        elif conn_type == "GPIB":
            connection = GPIBAddress(
                board=params.get("board", 0),
                address=params.get("address", 0),
                timeout=params.get("timeout", 5000),
            )
        elif conn_type == "LOCAL":
            connection = InstrumentAddress(
                type="LOCAL",
                address=params.get("address", "local://unknown"),
                timeout=params.get("timeout", 5000),
            )
        else:
            # Default: VISA
            connection = VISAAddress(
                address=params.get("address", ""),
                timeout=params.get("timeout", 5000),
            )

        return InstrumentConfig(
            id=row.instrument_id,
            type=row.instrument_type,
            name=row.name,
            connection=connection,
            enabled=row.enabled,
            description=row.description,
        )



# ============================================================================
# Configuration Example JSON Format
# ============================================================================

EXAMPLE_CONFIG = """
{
  "instruments": {
    "DAQ973A_1": {
      "type": "DAQ973A",
      "name": "Keysight DAQ973A Primary",
      "connection": {
        "type": "VISA",
        "address": "TCPIP0::192.168.1.10::inst0::INSTR",
        "timeout": 5000
      },
      "enabled": true,
      "description": "Main data acquisition system"
    },
    "MODEL2303_1": {
      "type": "MODEL2303",
      "name": "Keysight 2303 Power Supply",
      "connection": {
        "type": "SERIAL",
        "port": "COM3",
        "baudrate": 115200,
        "stopbits": 1,
        "timeout": 5000
      },
      "enabled": true
    },
    "IT6723C_1": {
      "type": "IT6723C",
      "name": "ITECH IT6723C Power Supply",
      "connection": {
        "type": "TCPIP_SOCKET",
        "host": "192.168.1.20",
        "port": 2268,
        "timeout": 5000
      },
      "enabled": true
    },
    "KEITHLEY2015_1": {
      "type": "KEITHLEY2015",
      "name": "Keithley 2015 Multimeter",
      "connection": {
        "type": "GPIB",
        "board": 0,
        "address": 16,
        "timeout": 5000
      },
      "enabled": true
    }
  }
}
"""
