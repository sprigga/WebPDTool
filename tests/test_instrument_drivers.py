#!/usr/bin/env python3
"""
Test script for modern instrument drivers

Tests the refactored instrument architecture in simulation mode
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.instrument_config import get_instrument_settings
from app.services.instrument_executor import get_instrument_executor
from decimal import Decimal


async def test_daq973a():
    """Test DAQ973A driver"""
    print("\n" + "="*60)
    print("Testing DAQ973A Driver (Simulation Mode)")
    print("="*60)

    executor = get_instrument_executor()

    # Test 1: Channel switching
    print("\nTest 1: Open channels")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ973A_1",
            params={
                'Item': 'OPEN',
                'Channel': '101,102,103'
            },
            simulation=True
        )
        print(f"✓ Open channels result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: Close channels
    print("\nTest 2: Close channels")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ973A_1",
            params={
                'Item': 'CLOS',
                'Channel': '101'
            },
            simulation=True
        )
        print(f"✓ Close channels result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 3: Voltage measurement
    print("\nTest 3: Measure voltage (DC)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ973A_1",
            params={
                'Item': 'VOLT',
                'Channel': '101',
                'Type': 'DC'
            },
            simulation=True
        )
        print(f"✓ Voltage measurement: {result}V")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 4: Current measurement
    print("\nTest 4: Measure current (DC)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ973A_1",
            params={
                'Item': 'CURR',
                'Channel': '121',  # Current channel
                'Type': 'DC'
            },
            simulation=True
        )
        print(f"✓ Current measurement: {result}A")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 5: Temperature measurement
    print("\nTest 5: Measure temperature")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ973A_1",
            params={
                'Item': 'TEMP',
                'Channel': '105'
            },
            simulation=True
        )
        print(f"✓ Temperature measurement: {result}°C")
    except Exception as e:
        print(f"✗ Failed: {e}")


async def test_model2303():
    """Test MODEL2303 driver"""
    print("\n" + "="*60)
    print("Testing MODEL2303 Driver (Simulation Mode)")
    print("="*60)

    executor = get_instrument_executor()

    # Test 1: Set voltage and current
    print("\nTest 1: Set voltage and current")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MODEL2303_1",
            params={
                'SetVolt': '12.0',
                'SetCurr': '2.5'
            },
            simulation=True
        )
        print(f"✓ Power setting result: {result}")
        if result == '1':
            print("  Power supply configured successfully")
        else:
            print(f"  Warning: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: Different values
    print("\nTest 2: Set different values")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MODEL2303_1",
            params={
                'SetVolt': '5.0',
                'SetCurr': '1.0'
            },
            simulation=True
        )
        print(f"✓ Power setting result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")


async def test_parameter_validation():
    """Test parameter validation"""
    print("\n" + "="*60)
    print("Testing Parameter Validation")
    print("="*60)

    executor = get_instrument_executor()

    # Test 1: Missing required parameter
    print("\nTest 1: Missing required parameter (should fail)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ973A_1",
            params={
                'Item': 'VOLT',
                # Missing 'Channel' and 'Type'
            },
            simulation=True
        )
        print(f"✗ Should have failed but got: {result}")
    except ValueError as e:
        print(f"✓ Correctly caught error: {e}")
    except Exception as e:
        print(f"? Unexpected error: {e}")

    # Test 2: Invalid instrument ID
    print("\nTest 2: Invalid instrument ID (should fail)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="NONEXISTENT_1",
            params={'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'},
            simulation=True
        )
        print(f"✗ Should have failed but got: {result}")
    except Exception as e:
        print(f"✓ Correctly caught error: {e}")


async def test_configuration():
    """Test instrument configuration"""
    print("\n" + "="*60)
    print("Testing Instrument Configuration")
    print("="*60)

    settings = get_instrument_settings()

    # List all instruments
    print("\nConfigured Instruments:")
    instruments = settings.list_instruments()
    for inst_id, config in instruments.items():
        status = "✓ enabled" if config.enabled else "✗ disabled"
        print(f"  {inst_id:20} {config.type:15} {status:15} {config.connection.type}")

    # List enabled instruments only
    print("\nEnabled Instruments:")
    enabled = settings.list_enabled_instruments()
    print(f"  Total: {len(enabled)} instruments")


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("Modern Instrument Driver Test Suite")
    print("="*70)
    print("\nNote: All tests run in SIMULATION mode (no hardware required)")

    try:
        # Configuration test
        await test_configuration()

        # Driver tests
        await test_daq973a()
        await test_model2303()

        # Validation tests
        await test_parameter_validation()

        print("\n" + "="*70)
        print("Test suite completed successfully!")
        print("="*70)

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
