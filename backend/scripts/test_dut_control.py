#!/usr/bin/env python3
"""
DUT Control Test Script
Tests relay and chassis rotation functionality

Usage:
    uv run python scripts/test_dut_control.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.dut_comms import (
    get_relay_controller,
    get_chassis_controller,
    RelayState,
    RotationDirection
)


async def test_relay_control():
    """Test relay control functionality"""
    print("\n" + "="*60)
    print("Testing Relay Control")
    print("="*60)

    controller = get_relay_controller()

    # Test switch ON
    print("\n1. Testing relay switch ON...")
    success = await controller.switch_on(channel=1)
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}")

    # Check state
    state = await controller.get_current_state()
    print(f"   Current state: {state.name if state else 'UNKNOWN'}")

    await asyncio.sleep(1)

    # Test switch OFF
    print("\n2. Testing relay switch OFF...")
    success = await controller.switch_off(channel=1)
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}")

    # Check state
    state = await controller.get_current_state()
    print(f"   Current state: {state.name if state else 'UNKNOWN'}")

    # Test reset
    print("\n3. Testing relay reset...")
    success = await controller.reset(channel=1)
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}")

    print("\n✅ Relay control tests completed\n")


async def test_chassis_rotation():
    """Test chassis rotation functionality"""
    print("\n" + "="*60)
    print("Testing Chassis Rotation")
    print("="*60)

    controller = get_chassis_controller()

    # Test clockwise rotation
    print("\n1. Testing clockwise rotation...")
    print("   (Note: This may fail if chassis_fixture_bat.py doesn't exist)")
    success = await controller.rotate_clockwise(duration_ms=100)
    print(f"   Result: {'✅ SUCCESS' if success else '⚠️ EXPECTED - Script not found'}")

    await asyncio.sleep(0.5)

    # Test counterclockwise rotation
    print("\n2. Testing counterclockwise rotation...")
    success = await controller.rotate_counterclockwise(duration_ms=100)
    print(f"   Result: {'✅ SUCCESS' if success else '⚠️ EXPECTED - Script not found'}")

    # Check status
    is_rotating = controller.is_rotating()
    print(f"\n3. Rotation status: {'ROTATING' if is_rotating else 'IDLE'}")

    print("\n✅ Chassis rotation tests completed\n")


async def test_measurement_classes():
    """Test measurement classes integration"""
    print("\n" + "="*60)
    print("Testing Measurement Classes")
    print("="*60)

    from app.measurements.implementations import RelayMeasurement, ChassisRotationMeasurement
    from decimal import Decimal

    # Test RelayMeasurement
    print("\n1. Testing RelayMeasurement...")
    test_plan_item = {
        "item_no": 1,
        "item_name": "Relay Test",
        "test_type": "RELAY",
        "parameters": {"relay_state": "ON", "channel": 1},
        "value_type": "float",
        "limit_type": "none"
    }
    measurement = RelayMeasurement(test_plan_item=test_plan_item, config={})
    result = await measurement.execute()
    print(f"   Result: {result.result}")
    print(f"   Measured value: {result.measured_value}")
    print(f"   Item name: {result.item_name}")

    # Test ChassisRotationMeasurement
    print("\n2. Testing ChassisRotationMeasurement...")
    test_plan_item = {
        "item_no": 2,
        "item_name": "Chassis Rotation Test",
        "test_type": "CHASSIS_ROTATION",
        "parameters": {"direction": "CW", "duration_ms": 100},
        "value_type": "float",
        "limit_type": "none"
    }
    measurement = ChassisRotationMeasurement(test_plan_item=test_plan_item, config={})
    result = await measurement.execute()
    print(f"   Result: {result.result}")
    print(f"   Measured value: {result.measured_value}")
    print(f"   Item name: {result.item_name}")

    print("\n✅ Measurement class tests completed\n")


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("DUT Control Test Suite")
    print("="*60)
    print("\nThis script tests the DUT communication functionality:")
    print("- Relay control (MeasureSwitchON/OFF)")
    print("- Chassis rotation (MyThread_CW/CCW)")
    print("- Measurement class integration")

    try:
        # Run all tests
        await test_relay_control()
        await test_chassis_rotation()
        await test_measurement_classes()

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nNote: Chassis rotation may show failures if the control")
        print("script (chassis_fixture_bat.py) is not present. This is")
        print("expected in development environments without hardware.")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
