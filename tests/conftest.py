"""
Shared pytest fixtures and configuration for WebPDTool tests

This file provides common fixtures used across all test modules:
- Async test client for FastAPI testing
- Database fixtures for testing
- Mock instrument configurations
- Test data helpers
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


# =============================================================================
# Application Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests (session scope for efficiency)"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration override"""
    return {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-minimum-32-characters",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 60,
        "DEBUG": True,
        "REDIS_URL": None,  # Disable Redis in tests
    }


@pytest.fixture
async def async_client(test_config):
    """
    Async HTTP client for testing FastAPI endpoints

    Usage:
        async def test_get_users(async_client):
            response = await async_client.get("/api/users")
            assert response.status_code == 200
    """
    from app.main import app

    # Override config for testing
    with patch.dict(os.environ, test_config):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="function")
async def db_session():
    """
    Create a test database session (in-memory SQLite)

    Usage:
        async def test_user_creation(db_session):
            user = User(name="Test")
            db_session.add(user)
            await db_session.commit()
            assert user.id is not None
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.database import Base

    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session
    async with async_session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()


# =============================================================================
# Instrument Fixtures
# =============================================================================

@pytest.fixture
def mock_instrument_config():
    """
    Mock instrument configuration for testing

    Returns a dict with common instrument configurations
    """
    return {
        "34970A_1": {
            "type": "34970A",
            "enabled": True,
            "connection": {
                "type": "TCPIP",
                "address": "192.168.1.100",
                "timeout": 30000
            }
        },
        "MODEL2306_1": {
            "type": "MODEL2306",
            "enabled": True,
            "connection": {
                "type": "USB",
                "address": "0x05E6:0x2636",
                "timeout": 10000
            }
        },
        "IT6723C_1": {
            "type": "IT6723C",
            "enabled": True,
            "connection": {
                "type": "TCPIP",
                "address": "192.168.1.101",
                "timeout": 15000
            }
        },
        "2260B_1": {
            "type": "2260B",
            "enabled": True,
            "connection": {
                "type": "SERIAL",
                "address": "/dev/ttyUSB0",
                "timeout": 10000
            }
        },
        "CMW100_1": {
            "type": "CMW100",
            "enabled": True,
            "connection": {
                "type": "TCPIP",
                "address": "192.168.1.102",
                "timeout": 30000
            }
        },
    }


@pytest.fixture
def sim_connection():
    """
    Create a mock simulation connection

    Usage:
        def test_driver(sim_connection):
            driver = Driver34970A(sim_connection)
            assert driver.simulation_mode is True
    """
    conn = MagicMock()
    conn.config = MagicMock()
    conn.config.id = "SIM_INSTRUMENT"
    conn.config.type = "SIMULATION"
    conn.config.connection = MagicMock()
    conn.config.connection.address = "sim://test"
    conn.config.connection.timeout = 30000
    conn.config.options = {}
    return conn


@pytest.fixture
async def instrument_executor():
    """
    Get instrument executor instance for testing

    Usage:
        async def test_instrument_command(instrument_executor):
            result = await instrument_executor.execute_instrument_command(
                instrument_id="34970A_1",
                params={'Item': 'OPEN', 'Channel': '01'},
                simulation=True
            )
    """
    from app.services.instrument_executor import get_instrument_executor
    return get_instrument_executor()


# =============================================================================
# Measurement Fixtures
# =============================================================================

@pytest.fixture
def sample_test_plan():
    """
    Sample test plan data for testing measurements

    Usage:
        def test_measurement(sample_test_plan):
            measurement = PowerSet(sample_test_plan, {})
            result = await measurement.execute()
    """
    return {
        "item_no": 1,
        "item_name": "Test Voltage",
        "test_type": "PowerSet",
        "limit_type": "both",
        "value_type": "float",
        "lower_limit": 3.0,
        "upper_limit": 5.0,
        "parameters": {
            "Instrument": "IT6723C_1",
            "SetVolt": "12.0",
            "SetCurr": "2.5"
        }
    }


@pytest.fixture
def sample_test_session():
    """
    Sample test session for testing

    Usage:
        async def test_session_results(sample_test_session):
            results = await get_session_results(sample_test_session["id"])
    """
    return {
        "id": 1,
        "project_id": 1,
        "station_id": 1,
        "user_id": 1,
        "status": "RUNNING",
        "start_time": "2024-01-01T00:00:00",
    }


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture
def test_user_data():
    """Test user data for authentication tests"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "engineer",
        "is_active": True,
    }


@pytest.fixture
def test_admin_data():
    """Test admin user data"""
    return {
        "id": 2,
        "username": "testadmin",
        "email": "admin@example.com",
        "full_name": "Test Admin",
        "role": "admin",
        "is_active": True,
    }


@pytest.fixture
async def auth_token(async_client, test_user_data):
    """
    Get authentication token for API testing

    Usage:
        async def test_protected_endpoint(async_client, auth_token):
            response = await async_client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
    """
    # Create user and login to get token
    # This is a simplified version - you'd need to implement actual auth
    # For now, return a mock JWT token
    import jwt
    from datetime import datetime, timedelta

    token_data = {
        "sub": str(test_user_data["id"]),
        "username": test_user_data["username"],
        "role": test_user_data["role"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    secret = "test-secret-key-minimum-32-characters"
    return jwt.encode(token_data, secret, algorithm="HS256")


# =============================================================================
# Test Data Helpers
# =============================================================================

@pytest.fixture
def csv_test_data():
    """
    Sample CSV test plan data for testing CSV import

    Usage:
        def test_csv_parser(csv_test_data):
            parsed = parse_csv(csv_test_data)
            assert len(parsed) == 3
    """
    return """項次,品名規格,測試項目,測試類型,下限值,上限值,單位,LimitType,ValueType
1,Power Supply,Voltage,PowerSet,3.0,5.0,V,both,float
2,Power Supply,Current,PowerSet,0.5,2.5,A,both,float
3,Communication,TX Power,Other,,,-,-,none,string"""


@pytest.fixture
def mock_hardware_response():
    """
    Mock hardware response for instrument tests

    Usage:
        def test_hardware_communication(mock_hardware_response):
            with patch('driver.query', return_value=mock_hardware_response):
                result = await driver.measure()
    """
    return {
        "status": "success",
        "value": "12.5",
        "unit": "V",
        "error": None
    }


# =============================================================================
# Skip/Skipif decorators helper
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "hardware: marks tests that require physical hardware"
    )


def pytest_collection_modifyitems(config, items):
    """
    Auto-mark tests based on their characteristics

    - Tests in test_instruments/ directory -> @pytest.mark.instruments
    - Tests with 'hardware' in name -> @pytest.mark.hardware (and skip if no hardware)
    - Tests with 'async' in function name -> @pytest.mark.asyncio
    """
    for item in items:
        # Mark based on directory
        if "/test_instruments/" in str(item.fspath):
            item.add_marker(pytest.mark.instruments)
            item.add_marker(pytest.mark.simulation)  # Default to simulation mode

        # Auto-mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Auto-mark hardware tests (and skip if hardware not available)
        if "hardware" in item.name.lower():
            item.add_marker(pytest.mark.hardware)
            # Skip hardware tests unless explicitly enabled
            if not config.getoption("--run-hardware", default=False):
                item.add_marker(
                    pytest.mark.skip(
                        reason="Hardware test (use --run-hardware to enable)"
                    )
                )


# =============================================================================
# Custom pytest options
# =============================================================================

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-hardware",
        action="store_true",
        default=False,
        help="Run tests that require physical hardware"
    )
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip tests marked as slow"
    )
