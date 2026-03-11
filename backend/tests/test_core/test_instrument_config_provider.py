"""Tests for DB-backed InstrumentConfigProvider."""
import time
import pytest
from unittest.mock import MagicMock
from app.core.instrument_config import (
    InstrumentConfigProvider, InstrumentConfig, VISAAddress, SerialAddress
)


def _make_db_row(instrument_id="DAQ973A_1", conn_type="VISA",
                 conn_params=None, enabled=True):
    """Build a mock ORM Instrument row."""
    row = MagicMock()
    row.instrument_id = instrument_id
    row.instrument_type = "DAQ973A"
    row.name = "Test Instrument"
    row.conn_type = conn_type
    row.conn_params = conn_params or {"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000}
    row.enabled = enabled
    row.description = "A test instrument"
    return row


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.list_all.return_value = [_make_db_row()]
    repo.list_enabled.return_value = [_make_db_row()]
    repo.get_by_instrument_id.return_value = _make_db_row()
    return repo


def test_get_instrument_returns_instrument_config(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=30)
    config = provider.get_instrument("DAQ973A_1")
    assert isinstance(config, InstrumentConfig)
    assert config.id == "DAQ973A_1"
    assert config.type == "DAQ973A"


def test_get_instrument_not_found(mock_repo):
    mock_repo.get_by_instrument_id.return_value = None
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=30)
    assert provider.get_instrument("nonexistent") is None


def test_list_enabled_instruments(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=30)
    enabled = provider.list_enabled_instruments()
    assert "DAQ973A_1" in enabled
    assert isinstance(enabled["DAQ973A_1"], InstrumentConfig)


def test_cache_prevents_repeated_db_calls(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=60)
    provider.list_enabled_instruments()
    provider.list_enabled_instruments()
    # Should only hit DB once despite two calls
    assert mock_repo.list_enabled.call_count == 1


def test_cache_expires_after_ttl(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=0.01)  # 10ms TTL
    provider.list_enabled_instruments()
    time.sleep(0.02)
    provider.list_enabled_instruments()
    assert mock_repo.list_enabled.call_count == 2


def test_invalidate_cache(mock_repo):
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=60)
    provider.list_enabled_instruments()
    provider.invalidate_cache()
    provider.list_enabled_instruments()
    assert mock_repo.list_enabled.call_count == 2


def test_orm_row_to_instrument_config_visa(mock_repo):
    """Verify correct InstrumentAddress subtype is built."""
    provider = InstrumentConfigProvider(repo=mock_repo, cache_ttl=30)
    config = provider.get_instrument("DAQ973A_1")
    assert isinstance(config.connection, VISAAddress)
    assert "TCPIP0" in config.connection.address


def test_orm_row_to_instrument_config_serial():
    row = _make_db_row(
        instrument_id="MODEL2303_1",
        conn_type="SERIAL",
        conn_params={"port": "COM3", "baudrate": 115200, "stopbits": 1, "parity": "N", "bytesize": 8},
    )
    repo = MagicMock()
    repo.get_by_instrument_id.return_value = row
    provider = InstrumentConfigProvider(repo=repo, cache_ttl=30)
    config = provider.get_instrument("MODEL2303_1")
    assert isinstance(config.connection, SerialAddress)
