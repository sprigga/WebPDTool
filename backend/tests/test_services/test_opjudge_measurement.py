"""
Unit tests for OPjudge measurement functionality
Tests the _execute_op_judge method in measurement_service.py
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
import asyncio

from app.services.measurement_service import measurement_service
from app.measurements.base import MeasurementResult


class TestOPjudgeMeasurement:
    """Test suite for OPjudge measurement execution"""

    @pytest.mark.asyncio
    async def test_opjudge_confirm_mode_pass(self):
        """Test OPjudge confirm mode with PASS response"""

        # Mock subprocess execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"PASS\n", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="LED_Color_Check",
                    switch_mode="confirm",
                    test_params={
                        "TestParams": ["ImagePath=/images/green_led.jpg", "content=Check LED is green"],
                    },
                    run_all_test=False
                )

        assert result.result == "PASS"
        assert result.measured_value == Decimal("1")
        assert result.error_message is None
        assert result.item_name == "LED_Color_Check"

    @pytest.mark.asyncio
    async def test_opjudge_yorn_mode_fail(self):
        """Test OPjudge YorN mode with FAIL response"""

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"FAIL\n", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="Display_Check",
                    switch_mode="YorN",
                    test_params={
                        "TestParams": ["ImagePath=/images/display.png", "content=Is display correct?"],
                    },
                    run_all_test=False
                )

        assert result.result == "FAIL"
        assert result.measured_value == Decimal("0")
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_opjudge_invalid_switch_mode(self):
        """Test OPjudge with invalid switch mode"""

        result = await measurement_service._execute_op_judge(
            test_point_id="Test_01",
            switch_mode="invalid_mode",
            test_params={
                "TestParams": ["ImagePath=/test.jpg", "content=Test"],
            },
            run_all_test=False
        )

        assert result.result == "ERROR"
        assert "Invalid OPjudge mode" in result.error_message
        assert "Expected 'confirm' or 'YorN'" in result.error_message

    @pytest.mark.asyncio
    async def test_opjudge_missing_test_params(self):
        """Test OPjudge with missing TestParams"""

        result = await measurement_service._execute_op_judge(
            test_point_id="Test_02",
            switch_mode="confirm",
            test_params={},
            run_all_test=False
        )

        assert result.result == "ERROR"
        assert "Missing required parameters" in result.error_message
        assert "ImagePath" in result.error_message or "content" in result.error_message

    @pytest.mark.asyncio
    async def test_opjudge_subprocess_timeout(self):
        """Test OPjudge with subprocess timeout"""

        # Mock process that never completes
        mock_process = AsyncMock()

        async def never_complete():
            await asyncio.sleep(1000)  # Never returns
            return (b"", b"")

        mock_process.communicate = never_complete
        mock_process.kill = AsyncMock()
        mock_process.wait = AsyncMock()

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="Timeout_Test",
                    switch_mode="confirm",
                    test_params={
                        "TestParams": ["ImagePath=/test.jpg", "content=Test"],
                        "Timeout": 100  # 100ms timeout
                    },
                    run_all_test=False
                )

        assert result.result == "ERROR"
        assert "timeout" in result.error_message.lower()
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_opjudge_script_not_found_fallback(self):
        """Test OPjudge fallback when script not found"""

        with patch('os.path.exists', return_value=False):
            result = await measurement_service._execute_op_judge(
                test_point_id="Fallback_Test",
                switch_mode="YorN",
                test_params={
                    "TestParams": ["ImagePath=/test.jpg", "content=Test"],
                    "operator_judgment": "PASS"
                },
                run_all_test=False
            )

        assert result.result == "PASS"
        assert result.measured_value == Decimal("1")
        assert "fallback" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_opjudge_script_execution_error(self):
        """Test OPjudge with script execution error"""

        mock_process = AsyncMock()
        mock_process.returncode = 1  # Non-zero exit code
        mock_process.communicate = AsyncMock(return_value=(b"", b"ImagePath file not found\n"))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="Error_Test",
                    switch_mode="confirm",
                    test_params={
                        "TestParams": ["ImagePath=/nonexistent.jpg", "content=Test"],
                    },
                    run_all_test=False
                )

        assert result.result == "ERROR"
        assert "ImagePath file not found" in result.error_message

    @pytest.mark.asyncio
    async def test_opjudge_empty_response(self):
        """Test OPjudge with empty subprocess response"""

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="Empty_Response_Test",
                    switch_mode="confirm",
                    test_params={
                        "TestParams": ["ImagePath=/test.jpg", "content=Test"],
                    },
                    run_all_test=False
                )

        assert result.result == "ERROR"
        assert "empty response" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_opjudge_unknown_response_format(self):
        """Test OPjudge with unexpected response format"""

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"MAYBE\n", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="Unknown_Response_Test",
                    switch_mode="YorN",
                    test_params={
                        "TestParams": ["ImagePath=/test.jpg", "content=Test"],
                    },
                    run_all_test=False
                )

        assert result.result == "ERROR"
        assert result.measured_value is None

    @pytest.mark.asyncio
    async def test_opjudge_pre_execution_wait(self):
        """Test OPjudge with pre-execution wait"""

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"PASS\n", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                    result = await measurement_service._execute_op_judge(
                        test_point_id="Wait_Test",
                        switch_mode="confirm",
                        test_params={
                            "TestParams": ["ImagePath=/test.jpg", "content=Test"],
                            "WaitmSec": 2000  # 2 seconds
                        },
                        run_all_test=False
                    )

        # Verify sleep was called with 2.0 seconds
        mock_sleep.assert_called_once_with(2.0)
        assert result.result == "PASS"

    @pytest.mark.asyncio
    async def test_opjudge_case_insensitive_params(self):
        """Test OPjudge with case-insensitive parameter names"""

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"PASS\n", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="CaseInsensitive_Test",
                    switch_mode="confirm",
                    test_params={
                        "testparams": ["ImagePath=/test.jpg", "content=Test"],  # lowercase
                        "waitmSec": 500  # mixed case
                    },
                    run_all_test=False
                )

        assert result.result == "PASS"

    @pytest.mark.asyncio
    async def test_opjudge_dict_format_test_params(self):
        """Test OPjudge with dict-format TestParams"""

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"PASS\n", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('os.path.exists', return_value=True):
                result = await measurement_service._execute_op_judge(
                    test_point_id="Dict_Params_Test",
                    switch_mode="YorN",
                    test_params={
                        "TestParams": {
                            "ImagePath": "/test.jpg",
                            "content": "Test content"
                        },
                    },
                    run_all_test=False
                )

        assert result.result == "PASS"

    @pytest.mark.asyncio
    async def test_opjudge_response_case_insensitive(self):
        """Test OPjudge handles case-insensitive responses (pass, PASS, Pass)"""

        test_cases = [
            (b"pass\n", "PASS"),
            (b"PASS\n", "PASS"),
            (b"Pass\n", "PASS"),
            (b"fail\n", "FAIL"),
            (b"FAIL\n", "FAIL"),
            (b"Fail\n", "FAIL"),
        ]

        for response_bytes, expected_result in test_cases:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(response_bytes, b""))

            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                with patch('os.path.exists', return_value=True):
                    result = await measurement_service._execute_op_judge(
                        test_point_id="CaseInsensitive_Response_Test",
                        switch_mode="confirm",
                        test_params={
                            "TestParams": ["ImagePath=/test.jpg", "content=Test"],
                        },
                        run_all_test=False
                    )

            assert result.result == expected_result


class TestOPjudgeValidation:
    """Test parameter validation for OPjudge"""

    @pytest.mark.asyncio
    async def test_validation_confirm_mode(self):
        """Test validation accepts confirm mode with TestParams"""

        validation = await measurement_service.validate_params(
            measurement_type="OPjudge",
            switch_mode="confirm",
            test_params={
                "TestParams": ["ImagePath=/test.jpg", "content=Test"]
            }
        )

        assert validation["valid"] is True
        assert len(validation["missing_params"]) == 0

    @pytest.mark.asyncio
    async def test_validation_yorn_mode(self):
        """Test validation accepts YorN mode with TestParams"""

        validation = await measurement_service.validate_params(
            measurement_type="OPjudge",
            switch_mode="YorN",
            test_params={
                "TestParams": ["ImagePath=/test.jpg", "content=Test"]
            }
        )

        assert validation["valid"] is True
        assert len(validation["missing_params"]) == 0

    @pytest.mark.asyncio
    async def test_validation_missing_test_params(self):
        """Test validation rejects missing TestParams"""

        validation = await measurement_service.validate_params(
            measurement_type="OPjudge",
            switch_mode="confirm",
            test_params={}
        )

        assert validation["valid"] is False
        assert "TestParams" in validation["missing_params"]

    @pytest.mark.asyncio
    async def test_validation_invalid_switch_mode(self):
        """Test validation rejects invalid switch mode"""

        validation = await measurement_service.validate_params(
            measurement_type="OPjudge",
            switch_mode="invalid",
            test_params={
                "TestParams": ["ImagePath=/test.jpg", "content=Test"]
            }
        )

        assert validation["valid"] is False
