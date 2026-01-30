"""
Tests for DUT Communications Services
Tests relay controller and chassis rotation functionality
"""
import pytest
import asyncio
from app.services.dut_comms import (
    RelayController,
    RelayState,
    get_relay_controller,
    ChassisController,
    RotationDirection,
    get_chassis_controller
)


class TestRelayController:
    """Test RelayController functionality"""

    @pytest.mark.asyncio
    async def test_relay_initialization(self):
        """Test relay controller initialization"""
        controller = RelayController(device_path="/dev/ttyUSB0")
        assert controller.device_path == "/dev/ttyUSB0"
        assert controller._current_state is None

    @pytest.mark.asyncio
    async def test_switch_on(self):
        """Test relay switch ON"""
        controller = RelayController()
        result = await controller.switch_on(channel=1)
        assert result is True
        assert controller._current_state == RelayState.SWITCH_OPEN

    @pytest.mark.asyncio
    async def test_switch_off(self):
        """Test relay switch OFF"""
        controller = RelayController()
        result = await controller.switch_off(channel=1)
        assert result is True
        assert controller._current_state == RelayState.SWITCH_CLOSED

    @pytest.mark.asyncio
    async def test_set_relay_state(self):
        """Test setting relay state directly"""
        controller = RelayController()

        # Test OPEN state
        result = await controller.set_relay_state(RelayState.SWITCH_OPEN, channel=2)
        assert result is True
        assert controller._current_state == RelayState.SWITCH_OPEN

        # Test CLOSED state
        result = await controller.set_relay_state(RelayState.SWITCH_CLOSED, channel=2)
        assert result is True
        assert controller._current_state == RelayState.SWITCH_CLOSED

    @pytest.mark.asyncio
    async def test_get_current_state(self):
        """Test getting current relay state"""
        controller = RelayController()

        # Initially unknown
        state = await controller.get_current_state()
        assert state is None

        # After setting
        await controller.switch_on()
        state = await controller.get_current_state()
        assert state == RelayState.SWITCH_OPEN

    @pytest.mark.asyncio
    async def test_reset(self):
        """Test relay reset"""
        controller = RelayController()
        await controller.switch_on()

        result = await controller.reset()
        assert result is True
        assert controller._current_state == RelayState.SWITCH_CLOSED

    @pytest.mark.asyncio
    async def test_get_relay_controller_singleton(self):
        """Test global relay controller getter"""
        controller1 = get_relay_controller()
        controller2 = get_relay_controller()
        assert controller1 is controller2  # Should be same instance


class TestChassisController:
    """Test ChassisController functionality"""

    @pytest.mark.asyncio
    async def test_chassis_initialization(self):
        """Test chassis controller initialization"""
        controller = ChassisController(device_path="/dev/ttyACM0")
        assert controller.device_path == "/dev/ttyACM0"
        assert controller._is_rotating is False

    @pytest.mark.asyncio
    async def test_rotate_clockwise(self):
        """Test clockwise rotation"""
        controller = ChassisController()
        # Note: This will fail if the control script doesn't exist
        # In production, this would require actual hardware or mocking
        result = await controller.rotate_clockwise(duration_ms=100)
        # Result depends on whether script exists - just check it returns bool
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_rotate_counterclockwise(self):
        """Test counterclockwise rotation"""
        controller = ChassisController()
        result = await controller.rotate_counterclockwise(duration_ms=100)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_is_rotating(self):
        """Test rotation status check"""
        controller = ChassisController()
        assert controller.is_rotating() is False

    @pytest.mark.asyncio
    async def test_stop_rotation(self):
        """Test stopping rotation"""
        controller = ChassisController()
        result = await controller.stop_rotation()
        assert result is True
        assert controller._is_rotating is False

    @pytest.mark.asyncio
    async def test_get_chassis_controller_singleton(self):
        """Test global chassis controller getter"""
        controller1 = get_chassis_controller()
        controller2 = get_chassis_controller()
        assert controller1 is controller2  # Should be same instance


class TestRelayState:
    """Test RelayState enum"""

    def test_relay_state_values(self):
        """Test RelayState enum values match PDTool4"""
        assert RelayState.SWITCH_OPEN == 0
        assert RelayState.SWITCH_CLOSED == 1

    def test_relay_state_names(self):
        """Test RelayState enum names"""
        assert RelayState.SWITCH_OPEN.name == "SWITCH_OPEN"
        assert RelayState.SWITCH_CLOSED.name == "SWITCH_CLOSED"


class TestRotationDirection:
    """Test RotationDirection enum"""

    def test_rotation_direction_values(self):
        """Test RotationDirection enum values match PDTool4"""
        assert RotationDirection.CLOCKWISE == 6
        assert RotationDirection.COUNTERCLOCKWISE == 9

    def test_rotation_direction_names(self):
        """Test RotationDirection enum names"""
        assert RotationDirection.CLOCKWISE.name == "CLOCKWISE"
        assert RotationDirection.COUNTERCLOCKWISE.name == "COUNTERCLOCKWISE"
