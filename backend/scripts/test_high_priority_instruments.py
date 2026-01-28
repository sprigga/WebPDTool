#!/usr/bin/env python3
"""
Test script for high-priority instrument drivers

Tests the newly migrated instrument drivers in simulation mode:
- 34970A (Data Acquisition/Switch Unit)
- MODEL2306 (Dual Channel Power Supply)
- IT6723C (Programmable DC Power Supply)
- 2260B (Programmable DC Power Supply)
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.instrument_config import get_instrument_settings
from app.services.instrument_executor import get_instrument_executor


async def test_34970a():
    """Test 34970A driver"""
    print("\n" + "="*60)
    print("Testing 34970A Driver (Data Acquisition/Switch Unit)")
    print("="*60)

    executor = get_instrument_executor()

    # Test 1: Open channels
    print("\nTest 1: Open channels")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="34970A_1",
            params={
                'Item': 'OPEN',
                'Channel': '01,02,03'
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
            instrument_id="34970A_1",
            params={
                'Item': 'CLOS',
                'Channel': '01'
            },
            simulation=True
        )
        print(f"✓ Close channels result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 3: Voltage measurement (DC)
    print("\nTest 3: Measure voltage (DC)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="34970A_1",
            params={
                'Item': 'VOLT',
                'Channel': '01',
                'Type': 'DC'
            },
            simulation=True
        )
        print(f"✓ Voltage measurement: {result}V")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 4: Current measurement (DC) - special channels
    print("\nTest 4: Measure current (DC) - channel 21")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="34970A_1",
            params={
                'Item': 'CURR',
                'Channel': '21',
                'Type': 'DC'
            },
            simulation=True
        )
        print(f"✓ Current measurement: {result}A")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 5: Invalid current channel (should fail)
    print("\nTest 5: Measure current on invalid channel (should fail)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="34970A_1",
            params={
                'Item': 'CURR',
                'Channel': '01',  # Invalid for current
                'Type': 'DC'
            },
            simulation=True
        )
        print(f"✗ Should have failed but got: {result}")
    except ValueError as e:
        print(f"✓ Correctly caught error: {e}")
    except Exception as e:
        print(f"? Unexpected error: {e}")

    # Test 6: Temperature measurement
    print("\nTest 6: Measure temperature")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="34970A_1",
            params={
                'Item': 'TEMP',
                'Channel': '05'
            },
            simulation=True
        )
        print(f"✓ Temperature measurement: {result}°C")
    except Exception as e:
        print(f"✗ Failed: {e}")


async def test_model2306():
    """Test MODEL2306 driver"""
    print("\n" + "="*60)
    print("Testing MODEL2306 Driver (Dual Channel Power Supply)")
    print("="*60)

    executor = get_instrument_executor()

    # Test 1: Set voltage and current on channel 1
    print("\nTest 1: Set channel 1 voltage and current")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MODEL2306_1",
            params={
                'Channel': '1',
                'SetVolt': '12.0',
                'SetCurr': '2.5'
            },
            simulation=True
        )
        print(f"✓ Channel 1 setting result: {result}")
        if result == '1':
            print("  Power supply configured successfully")
        else:
            print(f"  Warning: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: Set voltage and current on channel 2
    print("\nTest 2: Set channel 2 voltage and current")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MODEL2306_1",
            params={
                'Channel': '2',
                'SetVolt': '5.0',
                'SetCurr': '1.0'
            },
            simulation=True
        )
        print(f"✓ Channel 2 setting result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 3: Turn off output (both zero)
    print("\nTest 3: Turn off channel 1 output")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MODEL2306_1",
            params={
                'Channel': '1',
                'SetVolt': '0',
                'SetCurr': '0'
            },
            simulation=True
        )
        print(f"✓ Channel 1 output OFF result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")


async def test_it6723c():
    """Test IT6723C driver"""
    print("\n" + "="*60)
    print("Testing IT6723C Driver (Programmable DC Power Supply)")
    print("="*60)

    executor = get_instrument_executor()

    # Test 1: Set voltage and current
    print("\nTest 1: Set voltage and current")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="IT6723C_1",
            params={
                'SetVolt': '24.0',
                'SetCurr': '5.0'
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
            instrument_id="IT6723C_1",
            params={
                'SetVolt': '48.0',
                'SetCurr': '2.0'
            },
            simulation=True
        )
        print(f"✓ Power setting result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")


async def test_2260b():
    """Test 2260B driver"""
    print("\n" + "="*60)
    print("Testing 2260B Driver (Programmable DC Power Supply)")
    print("="*60)

    executor = get_instrument_executor()

    # Test 1: Set voltage and current
    print("\nTest 1: Set voltage and current")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="2260B_1",
            params={
                'SetVolt': '36.0',
                'SetCurr': '3.0'
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

    # Test 2: Test 105% voltage capability
    print("\nTest 2: Set voltage at 105% of rated (example)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="2260B_1",
            params={
                'SetVolt': '52.5',  # Example: 50V * 1.05
                'SetCurr': '1.5'
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

    # Test 1: Missing required parameter for 34970A
    print("\nTest 1: Missing required parameter (34970A, should fail)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="34970A_1",
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

    # Test 2: Invalid channel for MODEL2306
    print("\nTest 2: Invalid channel for MODEL2306 (should fail)")
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MODEL2306_1",
            params={
                'Channel': '3',  # Invalid, only 1 or 2
                'SetVolt': '12.0',
                'SetCurr': '2.0'
            },
            simulation=True
        )
        print(f"✗ Should have failed but got: {result}")
    except ValueError as e:
        print(f"✓ Correctly caught error: {e}")
    except Exception as e:
        print(f"? Unexpected error: {e}")


async def test_configuration():
    """Test instrument configuration"""
    print("\n" + "="*60)
    print("Testing Instrument Configuration")
    print("="*60)

    settings = get_instrument_settings()

    # List high-priority instruments
    print("\nHigh-Priority Instruments:")
    high_priority_ids = ['34970A_1', 'MODEL2306_1', 'IT6723C_1', '2260B_1']
    instruments = settings.list_instruments()

    for inst_id in high_priority_ids:
        if inst_id in instruments:
            config = instruments[inst_id]
            status = "✓ enabled" if config.enabled else "✗ disabled"
            print(f"  {inst_id:20} {config.type:15} {status:15} {config.connection.type}")
        else:
            print(f"  {inst_id:20} {'N/A':15} {'✗ not configured':15}")


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("High-Priority Instrument Driver Test Suite")
    print("="*70)
    print("\nNote: All tests run in SIMULATION mode (no hardware required)")

    try:
        # Configuration test
        await test_configuration()

        # Driver tests
        await test_34970a()
        await test_model2306()
        await test_it6723c()
        await test_2260b()

        # Validation tests
        await test_parameter_validation()

        print("\n" + "="*70)
        print("Test suite completed successfully!")
        print("="*70)
        print("\nNext steps:")
        print("1. Update instruments.json with actual instrument addresses")
        print("2. Test with real hardware")
        print("3. Integrate into measurement_service.py")

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
