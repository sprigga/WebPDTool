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
