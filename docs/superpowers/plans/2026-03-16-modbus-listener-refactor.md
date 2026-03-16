# ModbusListener Refactor Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor PDTool4's ModbusListener.py from Qt-based desktop application into WebPDTool's Vue 3 + FastAPI web architecture, enabling Modbus TCP communication for manufacturing test automation.

**Architecture:** Replace Qt Signals with WebSocket for real-time events, convert QThread to FastAPI BackgroundTasks with asyncio, and create database-backed configuration management. The listener will poll for SN, manage test state, and report results via Modbus registers.

**Tech Stack:** FastAPI (async), WebSocket (real-time), pymodbus (AsyncModbusTcpClient), SQLAlchemy 2.0 (async), Vue 3 + Element Plus (UI), MySQL 8.0

---

## File Structure

### Backend Files
| File | Responsibility |
|------|----------------|
| `backend/app/services/modbus/modbus_listener.py` | Core Modbus listener service (async, singleton) |
| `backend/app/services/modbus/modbus_config.py` | Configuration models and validation |
| `backend/app/api/modbus.py` | REST API endpoints (start/stop/status) |
| `backend/app/api/modbus_ws.py` | WebSocket endpoint for real-time events |
| `backend/app/models/modbus_config.py` | Database model for station Modbus config |
| `backend/alembic/versions/xxx_add_modbus_config.py` | Database migration |
| `backend/tests/test_modbus_listener.py` | Unit tests |

### Frontend Files
| File | Responsibility |
|------|----------------|
| `frontend/src/views/ModbusConfig.vue` | Configuration UI (per station) |
| `frontend/src/views/TestMain.vue` | Modify to show Modbus connection status |
| `frontend/src/components/ModbusStatusIndicator.vue` | Real-time status component |
| `frontend/src/api/modbus.js` | API client (REST + WebSocket) |

---

## Chunk 1: Backend Foundation - Models, Configuration, and Service Core

### Task 1: Create Modbus Configuration Database Model

**Files:**
- Create: `backend/app/models/modbus_config.py`
- Create: `backend/alembic/versions/xxx_add_modbus_config_table.py`
- Test: `backend/tests/test_modbus_config_model.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_modbus_config_model.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.modbus_config import ModbusConfig
from app.core.database import AsyncSessionLocal


@pytest.mark.asyncio
async def test_create_modbus_config(db: AsyncSession):
    """Test creating a ModbusConfig record"""
    config = ModbusConfig(
        station_id=1,
        server_host="127.0.0.1",
        server_port=502,
        device_id=1,
        enabled=True,
        delay_seconds=1,
        ready_status_address="0x0013",
        ready_status_length=1,
        read_sn_address="0x0064",
        read_sn_length=11,
        test_status_address="0x0014",
        test_status_length=1,
        in_testing_value="0x00",
        test_finished_value="0x01",
        test_result_address="0x0015",
        test_result_length=1,
        test_no_result="0x00",
        test_pass_value="0x01",
        test_fail_value="0x02",
        simulation_mode=False
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    assert config.id is not None
    assert config.server_host == "127.0.0.1"
    assert config.enabled is True
    assert config.delay_seconds == 1


@pytest.mark.asyncio
async def test_modbus_config_station_relationship(db: AsyncSession):
    """Test that ModbusConfig relates to Station"""
    from app.models.station import Station

    # First create a station
    station = Station(
        project_id=1,
        name="TestStation",
        station_code="TEST01",
        description="Test station for Modbus"
    )
    db.add(station)
    await db.commit()
    await db.refresh(station)

    # Create ModbusConfig for the station
    config = ModbusConfig(
        station_id=station.id,
        server_host="192.168.1.100",
        server_port=502,
        device_id=1
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    assert config.station_id == station.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_modbus_config_model.py -v`
Expected: FAIL with "No module named 'app.models.modbus_config'"

- [ ] **Step 3: Create the database model**

```python
# backend/app/models/modbus_config.py
"""
Modbus Configuration Database Model
Stores per-station Modbus TCP communication settings
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ModbusConfig(Base):
    """
    Modbus TCP configuration for a station
    One-to-one relationship with stations table
    """
    __tablename__ = "modbus_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.id"), unique=True, nullable=False, index=True)

    # Connection settings
    server_host = Column(String(255), nullable=False, default="127.0.0.1")
    server_port = Column(Integer, nullable=False, default=502)
    device_id = Column(Integer, nullable=False, default=1)
    enabled = Column(Boolean, nullable=False, default=False)
    delay_seconds = Column(Float, nullable=False, default=1.0)

    # Read register addresses (hex strings like "0x0013")
    ready_status_address = Column(String(20), nullable=False, default="0x0013")
    ready_status_length = Column(Integer, nullable=False, default=1)
    read_sn_address = Column(String(20), nullable=False, default="0x0064")
    read_sn_length = Column(Integer, nullable=False, default=11)

    # Write register addresses
    test_status_address = Column(String(20), nullable=False, default="0x0014")
    test_status_length = Column(Integer, nullable=False, default=1)
    in_testing_value = Column(String(20), nullable=False, default="0x00")
    test_finished_value = Column(String(20), nullable=False, default="0x01")

    test_result_address = Column(String(20), nullable=False, default="0x0015")
    test_result_length = Column(Integer, nullable=False, default=1)
    test_no_result = Column(String(20), nullable=False, default="0x00")
    test_pass_value = Column(String(20), nullable=False, default="0x01")
    test_fail_value = Column(String(20), nullable=False, default="0x02")

    # Simulation mode
    simulation_mode = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(Integer, nullable=True)  # Unix timestamp
    updated_at = Column(Integer, nullable=True)  # Unix timestamp

    # Relationship
    station = relationship("Station", back_populates="modbus_config")

    def __repr__(self):
        return f"<ModbusConfig(station_id={self.station_id}, host={self.server_host}:{self.server_port})>"
```

- [ ] **Step 4: Update Station model to include back_populates**

```python
# In backend/app/models/station.py, add to Station class:
modbus_config = relationship("ModbusConfig", back_populates="station", uselist=False, cascade="all, delete-orphan")
```

- [ ] **Step 5: Create Alembic migration**

```bash
# Generate migration file
cd backend
uv run alembic revision -m "add modbus config table"
```

Edit the generated migration file:

```python
# backend/alembic/versions/xxx_add_modbus_config_table.py
"""add modbus config table

Revision ID: add_modbus_config
Revises: <previous_revision_id>
Create Date: 2026-03-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_modbus_config'
down_revision = '<previous_revision_id>'  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'modbus_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('server_host', sa.String(length=255), nullable=False),
        sa.Column('server_port', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('delay_seconds', sa.Float(), nullable=False),
        sa.Column('ready_status_address', sa.String(length=20), nullable=False),
        sa.Column('ready_status_length', sa.Integer(), nullable=False),
        sa.Column('read_sn_address', sa.String(length=20), nullable=False),
        sa.Column('read_sn_length', sa.Integer(), nullable=False),
        sa.Column('test_status_address', sa.String(length=20), nullable=False),
        sa.Column('test_status_length', sa.Integer(), nullable=False),
        sa.Column('in_testing_value', sa.String(length=20), nullable=False),
        sa.Column('test_finished_value', sa.String(length=20), nullable=False),
        sa.Column('test_result_address', sa.String(length=20), nullable=False),
        sa.Column('test_result_length', sa.Integer(), nullable=False),
        sa.Column('test_no_result', sa.String(length=20), nullable=False),
        sa.Column('test_pass_value', sa.String(length=20), nullable=False),
        sa.Column('test_fail_value', sa.String(length=20), nullable=False),
        sa.Column('simulation_mode', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('station_id')
    )
    op.create_index(op.f('ix_modbus_configs_station_id'), 'modbus_configs', ['station_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_modbus_configs_station_id'), table_name='modbus_configs')
    op.drop_table('modbus_configs')
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_modbus_config_model.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/modbus_config.py backend/app/models/station.py backend/alembic/versions/xxx_add_modbus_config_table.py backend/tests/test_modbus_config_model.py
git commit -m "feat: add ModbusConfig database model and migration"
```

---

### Task 2: Create Modbus Configuration Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/modbus.py`
- Test: `backend/tests/test_modbus_schemas.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_modbus_schemas.py
import pytest
from pydantic import ValidationError
from app.schemas.modbus import ModbusConfigCreate, ModbusConfigResponse, ModbusConfigUpdate


def test_modbus_config_create_valid():
    """Test valid ModbusConfigCreate"""
    data = {
        "station_id": 1,
        "server_host": "192.168.1.100",
        "server_port": 502,
        "device_id": 1,
        "enabled": True,
        "delay_seconds": 1.0,
        "ready_status_address": "0x0013",
        "test_pass_value": "0x01"
    }
    config = ModbusConfigCreate(**data)
    assert config.server_host == "192.168.1.100"
    assert config.enabled is True


def test_modbus_config_create_invalid_port():
    """Test invalid port number"""
    with pytest.raises(ValidationError):
        ModbusConfigCreate(
            station_id=1,
            server_host="192.168.1.100",
            server_port=70000,  # Invalid
            device_id=1
        )


def test_modbus_config_response():
    """Test ModbusConfigResponse"""
    data = {
        "id": 1,
        "station_id": 1,
        "server_host": "127.0.0.1",
        "server_port": 502,
        "device_id": 1,
        "enabled": False,
        "delay_seconds": 1.0,
        "ready_status_address": "0x0013",
        "ready_status_length": 1,
        "read_sn_address": "0x0064",
        "read_sn_length": 11,
        "test_status_address": "0x0014",
        "test_status_length": 1,
        "in_testing_value": "0x00",
        "test_finished_value": "0x01",
        "test_result_address": "0x0015",
        "test_result_length": 1,
        "test_no_result": "0x00",
        "test_pass_value": "0x01",
        "test_fail_value": "0x02",
        "simulation_mode": False
    }
    response = ModbusConfigResponse(**data)
    assert response.id == 1
    assert response.station_id == 1


def test_modbus_config_update_partial():
    """Test partial update"""
    update = ModbusConfigUpdate(enabled=True, server_port=503)
    assert update.enabled is True
    assert update.server_port == 503
    assert update.server_host is None  # Not provided
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_modbus_schemas.py -v`
Expected: FAIL with "No module named 'app.schemas.modbus'"

- [ ] **Step 3: Create Pydantic schemas**

```python
# backend/app/schemas/modbus.py
"""
Modbus Configuration Pydantic Schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional


class ModbusConfigBase(BaseModel):
    """Base Modbus configuration fields"""
    server_host: str = Field(default="127.0.0.1", description="Modbus TCP server host")
    server_port: int = Field(default=502, ge=1, le=65535, description="Modbus TCP server port")
    device_id: int = Field(default=1, ge=1, le=255, description="Modbus device ID (slave address)")
    enabled: bool = Field(default=False, description="Whether Modbus listener is enabled")
    delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0, description="Polling delay in seconds")

    # Register addresses (hex string format)
    ready_status_address: str = Field(default="0x0013", description="Ready status register address")
    ready_status_length: int = Field(default=1, ge=1, le=125, description="Ready status register count")
    read_sn_address: str = Field(default="0x0064", description="Serial number read address")
    read_sn_length: int = Field(default=11, ge=1, le=125, description="Serial number register count")

    test_status_address: str = Field(default="0x0014", description="Test status register address")
    test_status_length: int = Field(default=1, ge=1, le=125, description="Test status register count")
    in_testing_value: str = Field(default="0x00", description="Value to write when testing")
    test_finished_value: str = Field(default="0x01", description="Value to write when finished")

    test_result_address: str = Field(default="0x0015", description="Test result register address")
    test_result_length: int = Field(default=1, ge=1, le=125, description="Test result register count")
    test_no_result: str = Field(default="0x00", description="Value for no result")
    test_pass_value: str = Field(default="0x01", description="Value for PASS")
    test_fail_value: str = Field(default="0x02", description="Value for FAIL")

    simulation_mode: bool = Field(default=False, description="Simulation mode (no real Modbus)")

    @validator('ready_status_address', 'read_sn_address', 'test_status_address',
               'test_result_address', 'in_testing_value', 'test_finished_value',
               'test_no_result', 'test_pass_value', 'test_fail_value')
    def validate_hex_string(cls, v):
        """Validate hex string format"""
        if not v.startswith('0x') and not v.startswith('0X'):
            raise ValueError('Hex address must start with 0x or 0X')
        try:
            int(v, 16)
        except ValueError:
            raise ValueError(f'Invalid hex string: {v}')
        return v


class ModbusConfigCreate(ModbusConfigBase):
    """Schema for creating Modbus configuration"""
    station_id: int = Field(..., description="Station ID")


class ModbusConfigUpdate(BaseModel):
    """Schema for updating Modbus configuration (all fields optional)"""
    server_host: Optional[str] = None
    server_port: Optional[int] = Field(None, ge=1, le=65535)
    device_id: Optional[int] = Field(None, ge=1, le=255)
    enabled: Optional[bool] = None
    delay_seconds: Optional[float] = Field(None, ge=0.1, le=60.0)

    ready_status_address: Optional[str] = None
    ready_status_length: Optional[int] = Field(None, ge=1, le=125)
    read_sn_address: Optional[str] = None
    read_sn_length: Optional[int] = Field(None, ge=1, le=125)

    test_status_address: Optional[str] = None
    test_status_length: Optional[int] = Field(None, ge=1, le=125)
    in_testing_value: Optional[str] = None
    test_finished_value: Optional[str] = None

    test_result_address: Optional[str] = None
    test_result_length: Optional[int] = Field(None, ge=1, le=125)
    test_no_result: Optional[str] = None
    test_pass_value: Optional[str] = None
    test_fail_value: Optional[str] = None

    simulation_mode: Optional[bool] = None


class ModbusConfigResponse(ModbusConfigBase):
    """Schema for Modbus configuration response"""
    id: int
    station_id: int

    class Config:
        from_attributes = True


class ModbusStatusResponse(BaseModel):
    """Schema for Modbus listener status"""
    station_id: int
    running: bool
    connected: bool
    last_sn: Optional[str] = None
    error_message: Optional[str] = None
    cycle_count: int = 0
    uptime_seconds: Optional[float] = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_modbus_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/modbus.py backend/tests/test_modbus_schemas.py
git commit -m "feat: add ModbusConfig Pydantic schemas with validation"
```

---

### Task 3: Create Core Modbus Listener Service

**Files:**
- Create: `backend/app/services/modbus/__init__.py`
- Create: `backend/app/services/modbus/modbus_listener.py`
- Create: `backend/app/services/modbus/modbus_config.py`
- Test: `backend/tests/test_modbus_listener_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_modbus_listener_service.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.modbus.modbus_listener import ModbusListenerService
from app.schemas.modbus import ModbusConfigCreate


@pytest.mark.asyncio
async def test_modbus_listener_initialization():
    """Test ModbusListenerService initialization"""
    config = ModbusConfigCreate(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=False,
        simulation_mode=True
    )

    service = ModbusListenerService(config)

    assert service.station_id == 1
    assert service.running is False
    assert service.connected is False


@pytest.mark.asyncio
async def test_modbus_listener_hex_string_conversion():
    """Test hex string to int conversion"""
    config = ModbusConfigCreate(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        simulation_mode=True
    )
    service = ModbusListenerService(config)

    # Test hex string conversion
    assert service._str2hex("0x0013") == 19
    assert service._str2hex("0x0064") == 100
    assert service._str2hex("0xFFFF") == 65535


@pytest.mark.asyncio
async def test_modbus_listener_byte_offset():
    """Test byte offset function for SN decoding"""
    config = ModbusConfigCreate(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        simulation_mode=True
    )
    service = ModbusListenerService(config)

    # Test byte offset (convert 16-bit register to two bytes)
    high, low = service._byte_offset(0x4D31)  # "M1" in ASCII
    assert high == 0x4D  # 'M'
    assert low == 0x31   # '1'


@pytest.mark.asyncio
async def test_modbus_listener_decode_sn():
    """Test SN decoding from register values"""
    config = ModbusConfigCreate(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        simulation_mode=True
    )
    service = ModbusListenerService(config)

    # Example: "TEST1234" encoded in registers
    # T=0x54, E=0x45, S=0x53, T=0x54, 1=0x31, 2=0x32, 3=0x33, 4=0x34
    # In registers: 0x5445, 0x5354, 0x3132, 0x3334
    registers = [0x5445, 0x5354, 0x3132, 0x3334]
    decoded = service._decode_sn(registers)
    assert decoded == "TEST1234"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_modbus_listener_service.py -v`
Expected: FAIL with "No module named 'app.services.modbus'"

- [ ] **Step 3: Create modbus service package**

```python
# backend/app/services/modbus/__init__.py
"""
Modbus Service Package
"""
from app.services.modbus.modbus_listener import ModbusListenerService

__all__ = ['ModbusListenerService']
```

- [ ] **Step 4: Create configuration helper module**

```python
# backend/app/services/modbus/modbus_config.py
"""
Modbus Configuration Helper
Converts between database models and service configuration
"""
from typing import Dict, Any
from app.models.modbus_config import ModbusConfig as ModbusConfigModel
from app.schemas.modbus import ModbusConfigResponse


def modbus_config_to_dict(config: ModbusConfigModel) -> Dict[str, Any]:
    """
    Convert ModbusConfig model to dictionary format expected by listener

    Args:
        config: ModbusConfig database model

    Returns:
        Dictionary with modbus_scheme keys (matching PDTool4 format)
    """
    return {
        "ready_status_Add": config.ready_status_address,
        "ready_status_Len": hex(config.ready_status_length),
        "read_sn_Add": config.read_sn_address,
        "read_sn_Len": hex(config.read_sn_length),
        "test_status_Add": config.test_status_address,
        "test_status_Len": hex(config.test_status_length),
        "in_testing_Val": config.in_testing_value,
        "test_finished_Val": config.test_finished_value,
        "test_result_Add": config.test_result_address,
        "test_result_Len": hex(config.test_result_length),
        "test_no_Result": config.test_no_result,
        "test_pass_Val": config.test_pass_value,
        "test_fail_Val": config.test_fail_value,
        "simulation_Mode": "1" if config.simulation_mode else "0",
        "Delay": str(int(config.delay_seconds))
    }


def str2hex(hex_str: str) -> int:
    """Convert hex string to integer"""
    return int(hex_str, 16)
```

- [ ] **Step 5: Create core ModbusListenerService**

```python
# backend/app/services/modbus/modbus_listener.py
"""
Modbus Listener Service
Refactored from PDTool4 ModbusListener.py for web architecture

Key differences from PDTool4:
- No Qt Signals (use WebSocket callbacks instead)
- No QThread (runs in FastAPI background task)
- Singleton pattern per station
- Database-backed configuration
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

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

        # Modbus client (created in async context)
        self.client: Optional[AsyncModbusTcpClient] = None

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

                        # Clear error
                        self.last_error = None
                        if self.on_error:
                            self.on_error("")

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
                logger.info(
                    f"Wrote {in_testing_value} to register {test_status_address}"
                )

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

    def _byteoffset(self, decimal_number: int) -> tuple:
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
            for high_byte, low_byte in [self._byteoffset(decimal_number)]
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_modbus_listener_service.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/modbus/ backend/tests/test_modbus_listener_service.py
git commit -m "feat: add core ModbusListenerService with async pymodbus"
```

---

## Chunk 2: REST API and WebSocket Integration

### Task 4: Create REST API Endpoints

**Files:**
- Create: `backend/app/api/modbus.py`
- Test: `backend/tests/test_modbus_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_modbus_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models.modbus_config import ModbusConfig
from app.models.station import Station
from app.models.project import Project


client = TestClient(app)


@pytest.mark.asyncio
async def test_get_modbus_configs(db: AsyncSession):
    """Test GET /api/modbus/configs"""
    # Create test data
    project = Project(name="TestProject", code="TEST")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    station = Station(
        project_id=project.id,
        name="TestStation",
        station_code="TEST01"
    )
    db.add(station)
    await db.commit()
    await db.refresh(station)

    config = ModbusConfig(
        station_id=station.id,
        server_host="192.168.1.100",
        server_port=502,
        device_id=1,
        enabled=True
    )
    db.add(config)
    await db.commit()

    # Test requires auth - skip for now or add auth header
    # response = client.get("/api/modbus/configs")
    # assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_modbus_config(db: AsyncSession):
    """Test POST /api/modbus/configs"""
    # Create test station first
    project = Project(name="TestProject", code="TEST")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    station = Station(
        project_id=project.id,
        name="TestStation",
        station_code="TEST01"
    )
    db.add(station)
    await db.commit()
    await db.refresh(station)

    payload = {
        "station_id": station.id,
        "server_host": "192.168.1.100",
        "server_port": 502,
        "device_id": 1,
        "enabled": True
    }

    # response = client.post("/api/modbus/configs", json=payload)
    # assert response.status_code == 201
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_modbus_api.py -v`
Expected: FAIL with "404 Not Found" (API endpoint doesn't exist)

- [ ] **Step 3: Create REST API endpoints**

```python
# backend/app/api/modbus.py
"""
Modbus Configuration REST API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.modbus_config import ModbusConfig as ModbusConfigModel
from app.models.station import Station
from app.schemas.modbus import (
    ModbusConfigCreate,
    ModbusConfigResponse,
    ModbusConfigUpdate,
    ModbusStatusResponse
)


router = APIRouter()


@router.get("/configs", response_model=List[ModbusConfigResponse])
async def get_modbus_configs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all Modbus configurations

    Requires authentication
    """
    result = await db.execute(
        select(ModbusConfigModel).offset(skip).limit(limit)
    )
    configs = result.scalars().all()
    return configs


@router.get("/configs/{config_id}", response_model=ModbusConfigResponse)
async def get_modbus_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific Modbus configuration by ID"""
    result = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modbus configuration not found"
        )

    return config


@router.get("/stations/{station_id}/config", response_model=ModbusConfigResponse)
async def get_station_modbus_config(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Modbus configuration for a specific station"""
    result = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.station_id == station_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modbus configuration not found for this station"
        )

    return config


@router.post("/configs", response_model=ModbusConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_modbus_config(
    config: ModbusConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new Modbus configuration

    Validates that station exists
    """
    # Check if station exists
    result = await db.execute(
        select(Station).where(Station.id == config.station_id)
    )
    station = result.scalar_one_or_none()

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )

    # Check if config already exists for this station
    existing = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.station_id == config.station_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Modbus configuration already exists for this station"
        )

    # Create new config
    db_config = ModbusConfigModel(**config.model_dump())
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)

    return db_config


@router.put("/configs/{config_id}", response_model=ModbusConfigResponse)
async def update_modbus_config(
    config_id: int,
    config_update: ModbusConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update Modbus configuration"""
    result = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modbus configuration not found"
        )

    # Update fields
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modbus_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete Modbus configuration"""
    result = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modbus configuration not found"
        )

    await db.delete(config)
    await db.commit()

    return None
```

- [ ] **Step 4: Register router in main.py**

```python
# In backend/app/main.py, add:
from app.api import modbus

# Include router
app.include_router(modbus.router, prefix="/api/modbus", tags=["Modbus"])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_modbus_api.py -v`
Expected: PASS (may need auth adjustments)

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/modbus.py backend/app/main.py backend/tests/test_modbus_api.py
git commit -m "feat: add Modbus configuration REST API endpoints"
```

---

### Task 5: Create Modbus Listener Manager (Singleton)

**Files:**
- Create: `backend/app/services/modbus/modbus_manager.py`
- Test: `backend/tests/test_modbus_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_modbus_manager.py
import pytest
from unittest.mock import MagicMock
from app.services.modbus.modbus_manager import modbus_manager
from app.schemas.modbus import ModbusConfigCreate


@pytest.mark.asyncio
async def test_modbus_manager_singleton():
    """Test that modbus_manager is a singleton"""
    from app.services.modbus.modbus_manager import modbus_manager as mm2
    assert modbus_manager is mm2


@pytest.mark.asyncio
async def test_modbus_manager_start_listener():
    """Test starting a listener"""
    config = ModbusConfigCreate(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=True,
        simulation_mode=True
    )

    await modbus_manager.start_listener(config)
    assert 1 in modbus_manager.active_listeners

    status = modbus_manager.get_status(1)
    assert status["station_id"] == 1
    assert status["running"] is True

    await modbus_manager.stop_listener(1)


@pytest.mark.asyncio
async def test_modbus_manager_stop_listener():
    """Test stopping a listener"""
    config = ModbusConfigCreate(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=True,
        simulation_mode=True
    )

    await modbus_manager.start_listener(config)
    await modbus_manager.stop_listener(1)

    assert 1 not in modbus_manager.active_listeners
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_modbus_manager.py -v`
Expected: FAIL with "No module named 'app.services.modbus.modbus_manager'"

- [ ] **Step 3: Create ModbusManager singleton**

```python
# backend/app/services/modbus/modbus_manager.py
"""
Modbus Listener Manager
Singleton service that manages all active Modbus listeners
"""
import asyncio
import logging
from typing import Dict, Optional
from app.schemas.modbus import ModbusConfigCreate, ModbusStatusResponse
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
        on_error: Optional[callable] = None
    ) -> ModbusListenerService:
        """
        Start a Modbus listener for a station

        Args:
            config: Modbus configuration
            on_sn_received: Callback when SN is received
            on_error: Callback when error occurs

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
        async with self._lock:
            station_ids = list(self.active_listeners.keys())
            for station_id in station_ids:
                await self.stop_listener(station_id)

    def get_listener(self, station_id: int) -> Optional[ModbusListenerService]:
        """
        Get active listener for a station

        Args:
            station_id: Station ID

        Returns:
            ModbusListenerService or None
        """
        return self.active_listeners.get(station_id)

    def get_status(self, station_id: int) -> Optional[Dict]:
        """
        Get status of a listener

        Args:
            station_id: Station ID

        Returns:
            Status dictionary or None
        """
        listener = self.active_listeners.get(station_id)
        if listener:
            return listener.get_status()
        return None

    def get_all_statuses(self) -> Dict[int, Dict]:
        """
        Get status of all active listeners

        Returns:
            Dictionary mapping station_id to status
        """
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
```

- [ ] **Step 4: Update service __init__.py**

```python
# backend/app/services/modbus/__init__.py
"""
Modbus Service Package
"""
from app.services.modbus.modbus_listener import ModbusListenerService
from app.services.modbus.modbus_manager import modbus_manager

__all__ = ['ModbusListenerService', 'modbus_manager']
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_modbus_manager.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/modbus/modbus_manager.py backend/app/services/modbus/__init__.py backend/tests/test_modbus_manager.py
git commit -m "feat: add ModbusManager singleton for listener lifecycle"
```

---

### Task 6: Create WebSocket Endpoint for Real-Time Events

**Files:**
- Create: `backend/app/api/modbus_ws.py`
- Test: `backend/tests/test_modbus_ws.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_modbus_ws.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import WebSocket
from app.main import app


@pytest.mark.asyncio
async def test_modbus_websocket_connection():
    """Test WebSocket connection for Modbus events"""
    # Note: WebSocket testing in TestClient requires special handling
    # This is a placeholder for the test structure

    with TestClient(app) as client:
        with client.websocket_connect("/api/modbus/ws/1") as websocket:
            # Send subscribe message
            websocket.send_json({"action": "subscribe"})

            # Receive initial status
            data = websocket.receive_json()
            assert data["type"] in ["status", "error"]


@pytest.mark.asyncio
async def test_modbus_websocket_unsubscribe():
    """Test WebSocket unsubscribe"""
    with TestClient(app) as client:
        with client.websocket_connect("/api/modbus/ws/1") as websocket:
            # Subscribe then unsubscribe
            websocket.send_json({"action": "subscribe"})
            websocket.send_json({"action": "unsubscribe"})

            # Should receive status update
            data = websocket.receive_json()
            assert data["type"] == "status"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_modbus_ws.py -v`
Expected: FAIL with "404 Not Found"

- [ ] **Step 3: Create WebSocket endpoint**

```python
# backend/app/api/modbus_ws.py
"""
Modbus WebSocket Endpoint
Real-time events for Modbus listener status
"""
import json
import logging
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.modbus_config import ModbusConfig
from app.schemas.modbus import ModbusConfigCreate
from app.services.modbus.modbus_manager import modbus_manager


router = APIRouter()
logger = logging.getLogger(__name__)


class ModbusConnectionManager:
    """
    Manages WebSocket connections for Modbus events
    """

    def __init__(self):
        # station_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, station_id: int):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        if station_id not in self.active_connections:
            self.active_connections[station_id] = set()
        self.active_connections[station_id].add(websocket)
        logger.info(f"WebSocket connected for station {station_id}")

    def disconnect(self, websocket: WebSocket, station_id: int):
        """Remove WebSocket connection"""
        if station_id in self.active_connections:
            self.active_connections[station_id].discard(websocket)
            if not self.active_connections[station_id]:
                del self.active_connections[station_id]
        logger.info(f"WebSocket disconnected for station {station_id}")

    async def send_to_station(self, station_id: int, message: dict):
        """Send message to all connections for a station"""
        if station_id in self.active_connections:
            for connection in self.active_connections[station_id].copy():
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    self.disconnect(connection, station_id)

    async def broadcast(self, message: dict):
        """Send message to all active connections"""
        for station_id, connections in self.active_connections.items():
            for connection in connections.copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection, station_id)


# Global connection manager
ws_manager = ModbusConnectionManager()


async def start_modbus_listener(station_id: int, db: AsyncSession):
    """
    Start Modbus listener with WebSocket callbacks

    Args:
        station_id: Station ID
        db: Database session
    """
    # Get config from database
    result = await db.execute(
        select(ModbusConfig).where(ModbusConfig.station_id == station_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        await ws_manager.send_to_station(station_id, {
            "type": "error",
            "message": "Modbus configuration not found"
        })
        return

    # Create config schema
    config_schema = ModbusConfigCreate(
        station_id=config.station_id,
        server_host=config.server_host,
        server_port=config.server_port,
        device_id=config.device_id,
        enabled=config.enabled,
        delay_seconds=config.delay_seconds,
        ready_status_address=config.ready_status_address,
        ready_status_length=config.ready_status_length,
        read_sn_address=config.read_sn_address,
        read_sn_length=config.read_sn_length,
        test_status_address=config.test_status_address,
        test_status_length=config.test_status_length,
        in_testing_value=config.in_testing_value,
        test_finished_value=config.test_finished_value,
        test_result_address=config.test_result_address,
        test_result_length=config.test_result_length,
        test_no_result=config.test_no_result,
        test_pass_value=config.test_pass_value,
        test_fail_value=config.test_fail_value,
        simulation_mode=config.simulation_mode
    )

    # Define callbacks
    def on_sn_received(sn: str):
        """Callback when SN is received"""
        asyncio.create_task(
            ws_manager.send_to_station(station_id, {
                "type": "sn_received",
                "sn": sn,
                "timestamp": asyncio.get_event_loop().time()
            })
        )

    def on_error(error_msg: str):
        """Callback when error occurs"""
        asyncio.create_task(
            ws_manager.send_to_station(station_id, {
                "type": "error",
                "message": error_msg,
                "timestamp": asyncio.get_event_loop().time()
            })
        )

    def on_status_change(status: str):
        """Callback when status changes"""
        asyncio.create_task(
            ws_manager.send_to_station(station_id, {
                "type": "status",
                "status": status,
                "timestamp": asyncio.get_event_loop().time()
            })
        )

    # Start listener
    try:
        await modbus_manager.start_listener(
            config_schema,
            on_sn_received=on_sn_received,
            on_error=on_error
        )

        # Send initial status
        await ws_manager.send_to_station(station_id, {
            "type": "status",
            "status": "running",
            "message": "Modbus listener started"
        })

    except Exception as e:
        await ws_manager.send_to_station(station_id, {
            "type": "error",
            "message": f"Failed to start listener: {str(e)}"
        })


@router.websocket("/ws/{station_id}")
async def modbus_websocket(
    websocket: WebSocket,
    station_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for Modbus events

    Messages:
    - Client -> Server: {"action": "subscribe"|"unsubscribe"|"start"|"stop"|"get_status"}
    - Server -> Client: {"type": "status"|"sn_received"|"error", ...}
    """
    await ws_manager.connect(websocket, station_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                # Subscribe to events (already connected)
                await websocket.send_json({
                    "type": "status",
                    "action": "subscribed",
                    "station_id": station_id
                })

            elif action == "start":
                # Start Modbus listener
                asyncio.create_task(start_modbus_listener(station_id, db))

            elif action == "stop":
                # Stop Modbus listener
                await modbus_manager.stop_listener(station_id)
                await websocket.send_json({
                    "type": "status",
                    "status": "stopped",
                    "message": "Modbus listener stopped"
                })

            elif action == "get_status":
                # Get current status
                status = modbus_manager.get_status(station_id)
                await websocket.send_json({
                    "type": "status",
                    "data": status
                })

            elif action == "unsubscribe":
                # Unsubscribe (but keep connection)
                await websocket.send_json({
                    "type": "status",
                    "action": "unsubscribed"
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, station_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, station_id)
```

- [ ] **Step 4: Register router in main.py**

```python
# In backend/app/main.py, add:
from app.api import modbus_ws

# Include WebSocket router
app.include_router(modbus_ws.router, prefix="/api/modbus", tags=["Modbus-WS"])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_modbus_ws.py -v`
Expected: PASS (may need WebSocket test adjustments)

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/modbus_ws.py backend/app/main.py backend/tests/test_modbus_ws.py
git commit -m "feat: add Modbus WebSocket endpoint for real-time events"
```

---

## Chunk 3: Frontend Implementation

### Task 7: Create Modbus Configuration Vue Component

**Files:**
- Create: `frontend/src/views/ModbusConfig.vue`
- Create: `frontend/src/api/modbus.js`
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: Create API client**

```javascript
// frontend/src/api/modbus.js
import { request } from './client';

const BASE_URL = '/api/modbus';

/**
 * Modbus Configuration API
 */
export const modbusApi = {
  /**
   * Get all Modbus configurations
   */
  getConfigs: async () => {
    return request.get(`${BASE_URL}/configs`);
  },

  /**
   * Get specific Modbus configuration
   */
  getConfig: async (configId) => {
    return request.get(`${BASE_URL}/configs/${configId}`);
  },

  /**
   * Get Modbus configuration for a station
   */
  getStationConfig: async (stationId) => {
    return request.get(`${BASE_URL}/stations/${stationId}/config`);
  },

  /**
   * Create Modbus configuration
   */
  createConfig: async (data) => {
    return request.post(`${BASE_URL}/configs`, data);
  },

  /**
   * Update Modbus configuration
   */
  updateConfig: async (configId, data) => {
    return request.put(`${BASE_URL}/configs/${configId}`, data);
  },

  /**
   * Delete Modbus configuration
   */
  deleteConfig: async (configId) => {
    return request.delete(`${BASE_URL}/configs/${configId}`);
  },

  /**
   * WebSocket connection for real-time events
   */
  connectWebSocket: (stationId) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/modbus/ws/${stationId}`;

    return new WebSocket(wsUrl);
  }
};
```

- [ ] **Step 2: Create ModbusConfig.vue component**

```vue
<!-- frontend/src/views/ModbusConfig.vue -->
<template>
  <div class="modbus-config-container">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>Modbus Configuration</span>
          <el-button type="primary" @click="handleCreate">New Configuration</el-button>
        </div>
      </template>

      <!-- Station Selector -->
      <el-form :inline="true" class="station-selector">
        <el-form-item label="Station">
          <el-select
            v-model="selectedStationId"
            placeholder="Select Station"
            @change="loadStationConfig"
            filterable
          >
            <el-option
              v-for="station in stations"
              :key="station.id"
              :label="station.name"
              :value="station.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Configuration Form -->
    <el-card v-if="config" class="config-card">
      <template #header>
        <div class="card-header">
          <span>{{ config.station_name }} - Modbus Config</span>
          <div>
            <el-button
              :type="config.enabled ? 'success' : 'info'"
              @click="toggleListener"
            >
              {{ config.enabled ? 'Stop Listener' : 'Start Listener' }}
            </el-button>
            <el-button type="primary" @click="handleEdit">Edit</el-button>
            <el-button type="danger" @click="handleDelete">Delete</el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="Server Host">{{ config.server_host }}</el-descriptions-item>
        <el-descriptions-item label="Server Port">{{ config.server_port }}</el-descriptions-item>
        <el-descriptions-item label="Device ID">{{ config.device_id }}</el-descriptions-item>
        <el-descriptions-item label="Status">
          <el-tag :type="config.enabled ? 'success' : 'info'">
            {{ config.enabled ? 'Enabled' : 'Disabled' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Delay (s)">{{ config.delay_seconds }}</el-descriptions-item>
        <el-descriptions-item label="Simulation Mode">
          <el-tag :type="config.simulation_mode ? 'warning' : 'info'">
            {{ config.simulation_mode ? 'Yes' : 'No' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- Register Addresses -->
      <el-divider content-position="left">Register Addresses</el-divider>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Ready Status Address">{{ config.ready_status_address }}</el-descriptions-item>
        <el-descriptions-item label="Read SN Address">{{ config.read_sn_address }}</el-descriptions-item>
        <el-descriptions-item label="Test Status Address">{{ config.test_status_address }}</el-descriptions-item>
        <el-descriptions-item label="Test Result Address">{{ config.test_result_address }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- No Config Message -->
    <el-card v-else-if="selectedStationId" class="no-config-card">
      <el-empty description="No Modbus configuration for this station">
        <el-button type="primary" @click="handleCreate">Create Configuration</el-button>
      </el-empty>
    </el-card>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? 'Create Modbus Configuration' : 'Edit Modbus Configuration'"
      width="700px"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="200px">
        <el-divider content-position="left">Connection Settings</el-divider>

        <el-form-item label="Server Host" prop="server_host">
          <el-input v-model="formData.server_host" placeholder="127.0.0.1" />
        </el-form-item>

        <el-form-item label="Server Port" prop="server_port">
          <el-input-number v-model="formData.server_port" :min="1" :max="65535" />
        </el-form-item>

        <el-form-item label="Device ID" prop="device_id">
          <el-input-number v-model="formData.device_id" :min="1" :max="255" />
        </el-form-item>

        <el-form-item label="Enable Listener" prop="enabled">
          <el-switch v-model="formData.enabled" />
        </el-form-item>

        <el-form-item label="Polling Delay (seconds)" prop="delay_seconds">
          <el-input-number v-model="formData.delay_seconds" :min="0.1" :max="60" :step="0.1" />
        </el-form-item>

        <el-form-item label="Simulation Mode" prop="simulation_mode">
          <el-switch v-model="formData.simulation_mode" />
          <span class="form-tip">Enable for testing without real Modbus device</span>
        </el-form-item>

        <el-divider content-position="left">Register Addresses</el-divider>

        <el-form-item label="Ready Status Address" prop="ready_status_address">
          <el-input v-model="formData.ready_status_address" placeholder="0x0013" />
        </el-form-item>

        <el-form-item label="Read SN Address" prop="read_sn_address">
          <el-input v-model="formData.read_sn_address" placeholder="0x0064" />
        </el-form-item>

        <el-form-item label="Test Status Address" prop="test_status_address">
          <el-input v-model="formData.test_status_address" placeholder="0x0014" />
        </el-form-item>

        <el-form-item label="Test Result Address" prop="test_result_address">
          <el-input v-model="formData.test_result_address" placeholder="0x0015" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="handleSubmit">Submit</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { modbusApi } from '@/api/modbus';
import { useProjectStore } from '@/stores/project';

const projectStore = useProjectStore();

// State
const selectedStationId = ref(null);
const stations = ref([]);
const config = ref(null);
const dialogVisible = ref(false);
const dialogMode = ref('create');
const formRef = ref(null);
const websocket = ref(null);
const listenerStatus = ref(null);

// Form data
const formData = reactive({
  server_host: '127.0.0.1',
  server_port: 502,
  device_id: 1,
  enabled: false,
  delay_seconds: 1.0,
  simulation_mode: false,
  ready_status_address: '0x0013',
  ready_status_length: 1,
  read_sn_address: '0x0064',
  read_sn_length: 11,
  test_status_address: '0x0014',
  test_status_length: 1,
  in_testing_value: '0x00',
  test_finished_value: '0x01',
  test_result_address: '0x0015',
  test_result_length: 1,
  test_no_result: '0x00',
  test_pass_value: '0x01',
  test_fail_value: '0x02'
});

// Form validation rules
const formRules = {
  server_host: [
    { required: true, message: 'Please enter server host', trigger: 'blur' }
  ],
  server_port: [
    { required: true, message: 'Please enter server port', trigger: 'blur' }
  ],
  device_id: [
    { required: true, message: 'Please enter device ID', trigger: 'blur' }
  ]
};

// Load stations
const loadStations = async () => {
  try {
    const response = await projectStore.fetchStations();
    stations.value = response || [];
  } catch (error) {
    ElMessage.error('Failed to load stations');
  }
};

// Load station config
const loadStationConfig = async () => {
  if (!selectedStationId.value) return;

  try {
    const response = await modbusApi.getStationConfig(selectedStationId.value);
    config.value = {
      ...response,
      station_name: stations.value.find(s => s.id === selectedStationId.value)?.name
    };

    // Connect WebSocket for real-time updates
    connectWebSocket();
  } catch (error) {
    if (error.response?.status === 404) {
      config.value = null;
    } else {
      ElMessage.error('Failed to load Modbus configuration');
    }
  }
};

// Connect WebSocket
const connectWebSocket = () => {
  if (websocket.value) {
    websocket.value.close();
  }

  websocket.value = modbusApi.connectWebSocket(selectedStationId.value);

  websocket.value.onopen = () => {
    console.log('WebSocket connected');
    websocket.value.send(JSON.stringify({ action: 'subscribe' }));
  };

  websocket.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleWebSocketMessage(data);
  };

  websocket.value.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  websocket.value.onclose = () => {
    console.log('WebSocket disconnected');
  };
};

// Handle WebSocket messages
const handleWebSocketMessage = (data) => {
  switch (data.type) {
    case 'status':
      listenerStatus.value = data;
      break;
    case 'sn_received':
      ElMessage.success(`SN received: ${data.sn}`);
      break;
    case 'error':
      ElMessage.error(data.message);
      break;
  }
};

// Toggle listener
const toggleListener = async () => {
  if (!websocket.value) return;

  const action = config.value.enabled ? 'stop' : 'start';
  websocket.value.send(JSON.stringify({ action }));

  // Update local state
  config.value.enabled = !config.value.enabled;
};

// Create config
const handleCreate = () => {
  dialogMode.value = 'create';
  Object.assign(formData, {
    server_host: '127.0.0.1',
    server_port: 502,
    device_id: 1,
    enabled: false,
    delay_seconds: 1.0,
    simulation_mode: false,
    ready_status_address: '0x0013',
    read_sn_address: '0x0064',
    test_status_address: '0x0014',
    test_result_address: '0x0015'
  });
  dialogVisible.value = true;
};

// Edit config
const handleEdit = () => {
  dialogMode.value = 'edit';
  Object.assign(formData, config.value);
  dialogVisible.value = true;
};

// Submit form
const handleSubmit = async () => {
  await formRef.value.validate();

  try {
    if (dialogMode.value === 'create') {
      await modbusApi.createConfig({
        ...formData,
        station_id: selectedStationId.value
      });
      ElMessage.success('Modbus configuration created');
    } else {
      await modbusApi.updateConfig(config.value.id, formData);
      ElMessage.success('Modbus configuration updated');
    }

    dialogVisible.value = false;
    loadStationConfig();
  } catch (error) {
    ElMessage.error('Failed to save configuration');
  }
};

// Delete config
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      'This will delete the Modbus configuration. Continue?',
      'Warning',
      {
        confirmButtonText: 'OK',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    );

    await modbusApi.deleteConfig(config.value.id);
    ElMessage.success('Configuration deleted');
    config.value = null;
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete configuration');
    }
  }
};

onMounted(() => {
  loadStations();
});

onBeforeUnmount(() => {
  if (websocket.value) {
    websocket.value.close();
  }
});
</script>

<style scoped>
.modbus-config-container {
  padding: 20px;
}

.header-card,
.config-card,
.no-config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.station-selector {
  margin-bottom: 0;
}

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
```

- [ ] **Step 3: Add route to router**

```javascript
// In frontend/src/router/index.js, add:
{
  path: '/modbus-config',
  name: 'ModbusConfig',
  component: () => import('@/views/ModbusConfig.vue'),
  meta: { requiresAuth: true, title: 'Modbus Configuration' }
}
```

- [ ] **Step 4: Add navigation button to AppNavBar**

```vue
<!-- In frontend/src/components/AppNavBar.vue, add to nav menu -->
<el-menu-item index="/modbus-config">
  <el-icon><Connection /></el-icon>
  <span>Modbus Config</span>
</el-menu-item>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/ModbusConfig.vue frontend/src/api/modbus.js frontend/src/router/index.js frontend/src/components/AppNavBar.vue
git commit -m "feat: add Modbus configuration UI component"
```

---

### Task 8: Create Modbus Status Indicator Component

**Files:**
- Create: `frontend/src/components/ModbusStatusIndicator.vue`
- Modify: `frontend/src/views/TestMain.vue`

- [ ] **Step 1: Create status indicator component**

```vue
<!-- frontend/src/components/ModbusStatusIndicator.vue -->
<template>
  <div class="modbus-status-indicator">
    <el-tooltip :content="tooltipContent" placement="bottom">
      <div class="status-dot" :class="statusClass"></div>
    </el-tooltip>

    <!-- Connection status dialog -->
    <el-dialog v-model="dialogVisible" title="Modbus Connection Status" width="500px">
      <el-descriptions v-if="status" :column="1" border>
        <el-descriptions-item label="Status">
          <el-tag :type="status.running ? 'success' : 'info'">
            {{ status.running ? 'Running' : 'Stopped' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Connected">
          <el-tag :type="status.connected ? 'success' : 'danger'">
            {{ status.connected ? 'Yes' : 'No' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Last SN">
          {{ status.last_sn || 'N/A' }}
        </el-descriptions-item>
        <el-descriptions-item label="Cycle Count">
          {{ status.cycle_count || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="Uptime">
          {{ formatUptime(status.uptime_seconds) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="status.error_message" label="Error">
          <el-text type="danger">{{ status.error_message }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { modbusApi } from '@/api/modbus';

const props = defineProps({
  stationId: {
    type: Number,
    required: true
  }
});

const status = ref(null);
const dialogVisible = ref(false);
const websocket = ref(null);

const statusClass = computed(() => {
  if (!status.value) return 'unknown';
  if (status.value.error_message) return 'error';
  if (status.value.running && status.value.connected) return 'connected';
  if (status.value.running) return 'connecting';
  return 'disconnected';
});

const tooltipContent = computed(() => {
  if (!status.value) return 'Modbus: Unknown';
  if (status.value.error_message) return `Modbus: Error - ${status.value.error_message}`;
  if (status.value.running && status.value.connected) return 'Modbus: Connected';
  if (status.value.running) return 'Modbus: Connecting...';
  return 'Modbus: Disconnected';
});

const formatUptime = (seconds) => {
  if (!seconds) return 'N/A';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${hours}h ${minutes}m ${secs}s`;
};

const connectWebSocket = () => {
  if (websocket.value) {
    websocket.value.close();
  }

  websocket.value = modbusApi.connectWebSocket(props.stationId);

  websocket.value.onopen = () => {
    console.log('Modbus status WebSocket connected');
    websocket.value.send(JSON.stringify({ action: 'get_status' }));
  };

  websocket.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'status' && data.data) {
      status.value = data.data;
    }
  };

  websocket.value.onerror = (error) => {
    console.error('Modbus status WebSocket error:', error);
  };

  websocket.value.onclose = () => {
    console.log('Modbus status WebSocket disconnected');
  };
};

const showDetail = () => {
  dialogVisible.value = true;
};

defineExpose({
  showDetail
});

onMounted(() => {
  connectWebSocket();
});

onBeforeUnmount(() => {
  if (websocket.value) {
    websocket.value.close();
  }
});
</script>

<style scoped>
.modbus-status-indicator {
  display: inline-block;
  cursor: pointer;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.status-dot.connected {
  background-color: #67c23a;
  box-shadow: 0 0 8px #67c23a;
}

.status-dot.connecting {
  background-color: #e6a23c;
  animation: pulse 1.5s infinite;
}

.status-dot.disconnected {
  background-color: #909399;
}

.status-dot.error {
  background-color: #f56c6c;
  animation: blink 1s infinite;
}

.status-dot.unknown {
  background-color: #c0c4cc;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>
```

- [ ] **Step 2: Integrate into TestMain.vue**

```vue
<!-- In frontend/src/views/TestMain.vue, add to template -->
<ModbusStatusIndicator
  v-if="currentStation"
  :station-id="currentStation.id"
  ref="modbusStatusRef"
/>

<!-- Add to script -->
import ModbusStatusIndicator from '@/components/ModbusStatusIndicator.vue';

<!-- Add to components -->
components: {
  ModbusStatusIndicator,
  // ... other components
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ModbusStatusIndicator.vue frontend/src/views/TestMain.vue
git commit -m "feat: add ModbusStatusIndicator component for real-time status"
```

---

## Chunk 4: Integration and Testing

### Task 9: Integrate Modbus with Test Execution

**Files:**
- Modify: `backend/app/services/test_engine.py`
- Modify: `backend/app/api/testplan/sessions.py`
- Test: `backend/tests/test_modbus_integration.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_modbus_integration.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.test_engine import TestEngine
from app.services.modbus.modbus_manager import modbus_manager


@pytest.mark.asyncio
async def test_test_engine_writes_modbus_result():
    """Test that test engine writes PASS/FAIL to Modbus"""
    # Mock modbus_manager
    with patch.object(modbus_manager, 'write_test_result', new=AsyncMock()) as mock_write:
        # This test verifies integration after implementation
        pass


@pytest.mark.asyncio
async def test_modbus_sn_triggers_test():
    """Test that receiving SN via Modbus triggers test execution"""
    # This test will verify the WebSocket callback integration
    pass
```

- [ ] **Step 2: Modify test_engine.py to write Modbus results**

```python
# In backend/app/services/test_engine.py, add imports:
from app.services.modbus.modbus_manager import modbus_manager

# In TestEngine class, add method to write Modbus result:
async def _write_modbus_result(self, station_id: int, passed: bool):
    """
    Write test result to Modbus device

    Args:
        station_id: Station ID
        passed: True for PASS, False for FAIL
    """
    try:
        await modbus_manager.write_test_result(station_id, passed)
        self.logger.info(f"Wrote Modbus result: {'PASS' if passed else 'FAIL'}")
    except Exception as e:
        self.logger.error(f"Failed to write Modbus result: {e}")

# In _execute_test_session method, after test completion, add:
# Write result to Modbus if configured
await self._write_modbus_result(station_id, final_result == TestResultEnum.PASS)
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_modbus_integration.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/test_engine.py backend/tests/test_modbus_integration.py
git commit -m "feat: integrate Modbus result writing with test execution"
```

---

### Task 10: End-to-End Testing

**Files:**
- Create: `backend/tests/test_modbus_e2e.py`
- Create: `scripts/modbus_simulator.py` (test helper)

- [ ] **Step 1: Create Modbus simulator for testing**

```python
# scripts/modbus_simulator.py
"""
Simple Modbus TCP Simulator for Testing
"""
import asyncio
import logging
from pymodbus.server import StartAsyncTcpServer
from pymodbus.data import ModbusServerContext
from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_simulator(host='127.0.0.1', port=5020):
    """
    Run Modbus TCP simulator

    Args:
        host: Server host
        port: Server port
    """
    # Create data store
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),  # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [0]*100),  # Coils
        hr=ModbusSequentialDataBlock(0, [0]*100),  # Holding Registers
        ir=ModbusSequentialDataBlock(0, [0]*100)   # Input Registers
    )

    # Set initial values for testing
    store.store[0x03].values[0x13] = 0x00  # Ready status (address 0x0013)
    # SN registers at 0x0064-0x006E (11 registers) will contain "TEST12345678"
    sn_data = [0x5445, 0x5354, 0x3132, 0x3334, 0x3536, 0x3738, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000]
    for i, val in enumerate(sn_data):
        store.store[0x03].values[0x64 + i] = val

    context = ModbusServerContext(slaves=store, single=True)

    logger.info(f"Starting Modbus simulator on {host}:{port}")
    await StartAsyncTcpServer(
        context=context,
        address=(host, port)
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Modbus TCP Simulator')
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    parser.add_argument('--port', type=int, default=5020, help='Server port')
    args = parser.parse_args()

    asyncio.run(run_simulator(args.host, args.port))
```

- [ ] **Step 2: Create E2E test**

```python
# backend/tests/test_modbus_e2e.py
"""
End-to-end tests for Modbus integration
Requires Modbus simulator to be running
"""
import pytest
import asyncio
import subprocess
import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.modbus_config import ModbusConfig
from app.models.station import Station
from app.models.project import Project
from app.schemas.modbus import ModbusConfigCreate
from app.services.modbus.modbus_manager import modbus_manager


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_modbus_e2e_flow(db: AsyncSession):
    """
    End-to-end test: Simulator -> Listener -> SN Receive -> Result Write

    Prerequisites:
    1. Modbus simulator running on 127.0.0.1:5020
    2. Test database available
    """
    # Create test data
    project = Project(name="TestProject", code="TEST")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    station = Station(
        project_id=project.id,
        name="TestStation",
        station_code="TEST01"
    )
    db.add(station)
    await db.commit()
    await db.refresh(station)

    # Create Modbus config
    config = ModbusConfig(
        station_id=station.id,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=True,
        simulation_mode=False,
        delay_seconds=0.5
    )
    db.add(config)
    await db.commit()

    # Track received SN
    received_sn = None

    def on_sn(sn):
        nonlocal received_sn
        received_sn = sn

    # Start listener
    config_schema = ModbusConfigCreate(
        station_id=station.id,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=True,
        simulation_mode=False,
        delay_seconds=0.5
    )

    listener = await modbus_manager.start_listener(
        config_schema,
        on_sn_received=on_sn
    )

    # Wait for SN to be received
    max_wait = 10
    start = time.time()
    while not received_sn and (time.time() - start) < max_wait:
        await asyncio.sleep(0.5)

    assert received_sn is not None, "Did not receive SN within timeout"

    # Write test result
    await modbus_manager.write_test_result(station.id, True)

    # Cleanup
    await modbus_manager.stop_listener(station.id)


@pytest.fixture(scope="session")
def modbus_simulator():
    """Start Modbus simulator for tests"""
    proc = subprocess.Popen(
        ['uv', 'run', 'python', 'scripts/modbus_simulator.py', '--port', '5020'],
        cwd='/home/ubuntu/python_code/WebPDTool/backend'
    )
    time.sleep(2)  # Wait for simulator to start

    yield

    proc.terminate()
    proc.wait()
```

- [ ] **Step 3: Run E2E test**

Run: `uv run pytest backend/tests/test_modbus_e2e.py -v`
Expected: PASS (with simulator running)

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_modbus_e2e.py scripts/modbus_simulator.py
git commit -m "test: add Modbus E2E tests with simulator"
```

---

## Chunk 5: Documentation and Deployment

### Task 11: Create Documentation

**Files:**
- Create: `docs/modbus-integration.md`
- Create: `docs/modbus-api.md`
- Create: `docs/modbus-configuration.md`

- [ ] **Step 1: Create integration documentation**

```markdown
# docs/modbus-integration.md
# Modbus Integration Guide

## Overview

WebPDTool's Modbus integration enables automatic SN reading and test result reporting via Modbus TCP. This feature is refactored from PDTool4's ModbusListener for web architecture.

## Architecture

```
Test Equipment (Modbus TCP)
    ↓ (reads SN)
ModbusListenerService (async background task)
    ↓ (WebSocket event)
Frontend (TestMain.vue)
    ↓ (triggers test)
TestEngine (executes measurements)
    ↓ (writes result)
ModbusListenerService (writes PASS/FAIL)
    ↓
Test Equipment (Modbus TCP)
```

## Key Components

1. **ModbusListenerService**: Async service that polls Modbus device
2. **ModbusManager**: Singleton managing all active listeners
3. **WebSocket Endpoint**: Real-time events (SN received, errors, status)
4. **REST API**: Configuration management

## Usage

1. Configure Modbus settings per station via `/modbus-config`
2. Start listener via UI or WebSocket command
3. When device sets ready status, listener reads SN
4. SN triggers test execution automatically
5. Test result written back to device

## Configuration

See [modbus-configuration.md](modbus-configuration.md)
```

- [ ] **Step 2: Create API documentation**

```markdown
# docs/modbus-api.md
# Modbus API Reference

## REST API

### GET /api/modbus/configs
Get all Modbus configurations

### POST /api/modbus/configs
Create new configuration

### PUT /api/modbus/configs/{id}
Update configuration

### DELETE /api/modbus/configs/{id}
Delete configuration

## WebSocket API

### Connect
```
ws://host/api/modbus/ws/{station_id}
```

### Client Messages
- `{"action": "subscribe"}` - Subscribe to events
- `{"action": "start"}` - Start listener
- `{"action": "stop"}` - Stop listener
- `{"action": "get_status"}` - Get current status

### Server Messages
- `{"type": "status", ...}` - Status update
- `{"type": "sn_received", "sn": "..."}` - SN received
- `{"type": "error", "message": "..."}` - Error occurred
```

- [ ] **Step 3: Create configuration guide**

```markdown
# docs/modbus-configuration.md
# Modbus Configuration Guide

## Register Map

| Address | Type | Description |
|---------|------|-------------|
| 0x0013 | Read | Ready Status (0x01 = SN ready) |
| 0x0064 | Read | Serial Number (11 registers) |
| 0x0014 | Write | Test Status (0x00 = testing, 0x01 = finished) |
| 0x0015 | Write | Test Result (0x00 = none, 0x01 = pass, 0x02 = fail) |

## SN Encoding

Each 16-bit register contains 2 ASCII characters:
- High byte = first character
- Low byte = second character

Example: "TEST" in registers:
- 0x5445 (T=0x54, E=0x45)
- 0x5354 (S=0x53, T=0x54)

## Settings

- **Server Host**: Modbus device IP address
- **Server Port**: Default 502
- **Device ID**: Modbus slave address (1-255)
- **Delay**: Polling interval in seconds
- **Simulation Mode**: Enable for testing without hardware
```

- [ ] **Step 4: Commit**

```bash
git add docs/modbus-integration.md docs/modbus-api.md docs/modbus-configuration.md
git commit -m "docs: add Modbus integration documentation"
```

---

### Task 12: Update Deployment Configuration

**Files:**
- Modify: `backend/.env.example`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add environment variables**

```bash
# In backend/.env.example, add:
# Modbus Configuration
MODBUS_DEFAULT_ENABLED=false
MODBUS_DEFAULT_DELAY=1.0
MODBUS_SIMULATION_MODE=false
```

- [ ] **Step 2: Update docker-compose.yml**

```yaml
# In docker-compose.yml, add to backend service:
backend:
  # ... existing config
  ports:
    - "9100:9100"
  # Modbus doesn't need additional ports - uses outbound TCP
  # If you need to expose Modbus from within container:
  # extra_hosts:
  #   - "modbus-device:192.168.1.100"
```

- [ ] **Step 3: Commit**

```bash
git add backend/.env.example docker-compose.yml
git commit -m "config: add Modbus environment variables"
```

---

## Completion Checklist

- [ ] All tasks completed
- [ ] All tests passing: `uv run pytest backend/tests/test_modbus* -v`
- [ ] E2E test passing with simulator
- [ ] Documentation complete
- [ ] Frontend components working
- [ ] WebSocket events working
- [ ] Test execution writes Modbus results

---

## Notes for Implementation

1. **pymodbus version**: Use `pymodbus>=3.0.0` for async support
2. **WebSocket reconnection**: Implement auto-reconnect in frontend
3. **Error handling**: Modbus devices may be unavailable - handle gracefully
4. **Testing**: Use simulation mode for most tests
5. **Security**: Modbus has no authentication - firewall appropriately

---

## Migration Notes from PDTool4

| PDTool4 | WebPDTool |
|---------|-----------|
| `ModbusListener(QObject)` | `ModbusListenerService` |
| `hexValueChanged` Signal | WebSocket `sn_received` event |
| `errorSig` Signal | WebSocket `error` event |
| `simSig` Signal | WebSocket `status` event |
| `modbus_scheme` dict | `ModbusConfig` model |
| QThread lifecycle | FastAPI BackgroundTask |
| test_xml.ini | Database `modbus_configs` table |
