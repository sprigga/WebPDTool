"""
Tests for ComPortMeasurement, ConSoleMeasurement, TCPIPMeasurement
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.measurements.implementations import ComPortMeasurement


def make_test_plan_item(parameters: dict, **kwargs) -> dict:
    return {
        "item_no": 1,
        "item_name": "CommandTest",
        "lower_limit": kwargs.get("lower_limit"),
        "upper_limit": kwargs.get("upper_limit"),
        "limit_type": kwargs.get("limit_type", "none"),
        "value_type": kwargs.get("value_type", "string"),
        "unit": "",
        "parameters": parameters,
    }


class TestComPortMeasurement:
    @pytest.mark.asyncio
    async def test_execute_returns_pass_on_response(self):
        """ComPortMeasurement calls driver.send_command and returns PASS"""
        test_plan_item = make_test_plan_item(
            {"Instrument": "ComPort_1", "Command": "0xAA\n", "Timeout": "3"},
        )
        measurement = ComPortMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.send_command = AsyncMock(return_value="OK")
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "comport"

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class") as mock_get_driver, \
             patch("app.measurements.implementations.get_connection_pool") as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

        assert result.result == "PASS"
        mock_driver.send_command.assert_called_once()
        # 修改: measured_value 現在應為 None (字串型別不傳入 create_result)
        assert result.measured_value is None  # string-type measurement: value stored as None per base contract

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_instrument_not_configured(self):
        """Returns ERROR when instrument is not found in config"""
        test_plan_item = make_test_plan_item(
            {"Instrument": "ComPort_MISSING", "Command": "TEST\n"},
        )
        measurement = ComPortMeasurement(test_plan_item, config={})

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class"), \
             patch("app.measurements.implementations.get_connection_pool"):

            mock_settings.return_value.get_instrument.return_value = None

            result = await measurement.execute()

        assert result.result == "ERROR"
        assert "not configured" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_missing_instrument_param(self):
        """Returns ERROR when Instrument parameter is absent"""
        test_plan_item = make_test_plan_item({"Command": "TEST\n"})
        measurement = ComPortMeasurement(test_plan_item, config={})

        with patch("app.measurements.implementations.get_instrument_settings"), \
             patch("app.measurements.implementations.get_driver_class"), \
             patch("app.measurements.implementations.get_connection_pool"):

            result = await measurement.execute()

        assert result.result == "ERROR"


from app.measurements.implementations import ConSoleMeasurement


class TestConSoleMeasurement:
    @pytest.mark.asyncio
    async def test_execute_returns_pass_on_response(self):
        """ConSoleMeasurement calls driver.send_command and returns PASS"""
        test_plan_item = make_test_plan_item(
            {"Instrument": "Console_1", "Command": "python ./scripts/check.py", "Timeout": "5"},
        )
        measurement = ConSoleMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.send_command = AsyncMock(return_value="PASS_OUTPUT")
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "console"

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class") as mock_get_driver, \
             patch("app.measurements.implementations.get_connection_pool") as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value is None  # string-type: stored as None
        mock_driver.send_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_instrument_not_configured(self):
        test_plan_item = make_test_plan_item(
            {"Instrument": "Console_MISSING", "Command": "echo ok"},
        )
        measurement = ConSoleMeasurement(test_plan_item, config={})

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class"), \
             patch("app.measurements.implementations.get_connection_pool"):

            mock_settings.return_value.get_instrument.return_value = None
            result = await measurement.execute()

        assert result.result == "ERROR"
        assert "not configured" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_missing_instrument_param(self):
        test_plan_item = make_test_plan_item({"Command": "echo ok"})
        measurement = ConSoleMeasurement(test_plan_item, config={})

        with patch("app.measurements.implementations.get_instrument_settings"), \
             patch("app.measurements.implementations.get_driver_class"), \
             patch("app.measurements.implementations.get_connection_pool"):

            result = await measurement.execute()

        assert result.result == "ERROR"
