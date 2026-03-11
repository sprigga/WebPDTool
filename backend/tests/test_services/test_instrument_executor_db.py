"""Test InstrumentExecutor uses DB-backed provider when injected."""
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Mock the paramiko import to avoid ModuleNotFoundError
sys.modules["paramiko"] = MagicMock()

from app.core.instrument_config import InstrumentConfig, VISAAddress, InstrumentConfigProvider
from app.services.instrument_executor import InstrumentExecutor


def _make_visa_config(inst_id="DAQ973A_1"):
    return InstrumentConfig(
        id=inst_id,
        type="DAQ973A",
        name="Test",
        connection=VISAAddress(address="TCPIP0::192.168.1.10::inst0::INSTR"),
        enabled=True,
    )


@pytest.fixture
def mock_provider():
    provider = MagicMock(spec=InstrumentConfigProvider)
    provider.get_instrument.return_value = _make_visa_config()
    return provider


def test_executor_uses_injected_provider(mock_provider):
    """Executor should call provider.get_instrument, not get_instrument_settings."""
    executor = InstrumentExecutor(config_provider=mock_provider)
    # Simulate a lookup (we don't actually connect hardware in this test)
    config = executor.get_instrument_config("DAQ973A_1")
    mock_provider.get_instrument.assert_called_once_with("DAQ973A_1")
    assert config is not None
    assert config.id == "DAQ973A_1"


def test_executor_falls_back_to_legacy_when_no_provider():
    """Without injection, executor falls back to get_instrument_settings()."""
    with patch("app.services.instrument_executor.get_instrument_settings") as mock_settings:
        mock_settings.return_value.get_instrument.return_value = _make_visa_config()
        executor = InstrumentExecutor()  # no provider injected
        config = executor.get_instrument_config("DAQ973A_1")
        assert config is not None
        assert config.id == "DAQ973A_1"
