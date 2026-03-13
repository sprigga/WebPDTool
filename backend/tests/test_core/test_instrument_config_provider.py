"""Tests for DB-backed InstrumentConfigProvider."""
import time
import pytest
from unittest.mock import MagicMock, patch
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


def _make_session_factory(mock_repo):
    """Build a session_factory that returns a mock session; patch InstrumentRepository to return mock_repo."""
    mock_db = MagicMock()
    mock_db.close = MagicMock()
    factory = MagicMock(return_value=mock_db)
    return factory, mock_db


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.list_all.return_value = [_make_db_row()]
    repo.list_enabled.return_value = [_make_db_row()]
    repo.get_by_instrument_id.return_value = _make_db_row()
    return repo


@pytest.fixture
def provider_and_repo(mock_repo):
    factory, _ = _make_session_factory(mock_repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=mock_repo):
        prov = InstrumentConfigProvider(session_factory=factory, cache_ttl=30)
        yield prov, mock_repo


def test_get_instrument_returns_instrument_config(provider_and_repo):
    provider, mock_repo = provider_and_repo
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=mock_repo):
        config = provider.get_instrument("DAQ973A_1")
    assert isinstance(config, InstrumentConfig)
    assert config.id == "DAQ973A_1"
    assert config.type == "DAQ973A"


def test_get_instrument_not_found(mock_repo):
    mock_repo.get_by_instrument_id.return_value = None
    factory, _ = _make_session_factory(mock_repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=mock_repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=30)
        assert provider.get_instrument("nonexistent") is None


def test_list_enabled_instruments(mock_repo):
    factory, _ = _make_session_factory(mock_repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=mock_repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=30)
        enabled = provider.list_enabled_instruments()
    assert "DAQ973A_1" in enabled
    assert isinstance(enabled["DAQ973A_1"], InstrumentConfig)


def test_cache_prevents_repeated_db_calls(mock_repo):
    factory, _ = _make_session_factory(mock_repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=mock_repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=60)
        provider.list_enabled_instruments()
        provider.list_enabled_instruments()
    # Should only hit DB once despite two calls
    assert mock_repo.list_enabled.call_count == 1


def test_cache_expires_after_ttl(mock_repo):
    factory, _ = _make_session_factory(mock_repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=mock_repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=0.01)  # 10ms TTL
        provider.list_enabled_instruments()
        time.sleep(0.02)
        provider.list_enabled_instruments()
    assert mock_repo.list_enabled.call_count == 2


def test_invalidate_cache(mock_repo):
    factory, _ = _make_session_factory(mock_repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=mock_repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=60)
        provider.list_enabled_instruments()
        provider.invalidate_cache()
        provider.list_enabled_instruments()
    assert mock_repo.list_enabled.call_count == 2


def test_orm_row_to_instrument_config_visa(mock_repo):
    """Verify correct InstrumentAddress subtype is built."""
    factory, _ = _make_session_factory(mock_repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=mock_repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=30)
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
    factory, _ = _make_session_factory(repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=30)
        config = provider.get_instrument("MODEL2303_1")
    assert isinstance(config.connection, SerialAddress)


def test_orm_row_to_instrument_config_tcpip_socket():
    row = _make_db_row(
        instrument_id="tcpip_sock_1",
        conn_type="TCPIP_SOCKET",
        conn_params={"host": "192.168.1.20", "port": 2268, "timeout": 5000},
    )
    from app.core.instrument_config import InstrumentConfigProvider, TCPIPSocketAddress
    repo = MagicMock()
    repo.get_by_instrument_id.return_value = row
    factory, _ = _make_session_factory(repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=30)
        config = provider.get_instrument("tcpip_sock_1")
    assert isinstance(config.connection, TCPIPSocketAddress)
    assert config.connection.host == "192.168.1.20"


def test_orm_row_to_instrument_config_gpib():
    row = _make_db_row(
        instrument_id="gpib_1",
        conn_type="GPIB",
        conn_params={"board": 0, "address": 16, "timeout": 5000},
    )
    from app.core.instrument_config import InstrumentConfigProvider, GPIBAddress
    repo = MagicMock()
    repo.get_by_instrument_id.return_value = row
    factory, _ = _make_session_factory(repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=30)
        config = provider.get_instrument("gpib_1")
    assert isinstance(config.connection, GPIBAddress)


def test_orm_row_to_instrument_config_local():
    row = _make_db_row(
        instrument_id="console_1",
        conn_type="LOCAL",
        conn_params={"address": "local://console", "timeout": 5000},
    )
    from app.core.instrument_config import InstrumentConfigProvider, InstrumentAddress
    repo = MagicMock()
    repo.get_by_instrument_id.return_value = row
    factory, _ = _make_session_factory(repo)
    with patch("app.repositories.instrument_repository.InstrumentRepository", return_value=repo):
        provider = InstrumentConfigProvider(session_factory=factory, cache_ttl=30)
        config = provider.get_instrument("console_1")
    assert isinstance(config.connection, InstrumentAddress)
    assert config.connection.type == "LOCAL"
