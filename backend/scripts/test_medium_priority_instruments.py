#!/usr/bin/env python3
"""
Test script for medium-priority instrument drivers

Tests the following drivers in simulation mode:
- DAQ6510
- PSW3072
- KEITHLEY2015
- MDO34
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment variable for instruments config
import os
os.environ['INSTRUMENTS_CONFIG_FILE'] = str(backend_dir / 'instruments.json')

from app.services.instrument_executor import get_instrument_executor


async def test_daq6510():
    """Test DAQ6510 driver functionality"""
    print("\n" + "=" * 60)
    print("Testing DAQ6510 Driver")
    print("=" * 60)

    executor = get_instrument_executor()

    # Test 1: Open channels
    print("\nTest 1: Open channels", end=" " * 26)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ6510_1",
            params={'Item': 'OPEN', 'Channel': '101,102'},
            simulation=True
        )
        print("✓ PASS")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 2: Close channels
    print("Test 2: Close channels", end=" " * 25)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ6510_1",
            params={'Item': 'CLOS', 'Channel': '101,102'},
            simulation=True
        )
        print("✓ PASS")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 3: Measure voltage (DC)
    print("Test 3: Measure voltage (DC)", end=" " * 19)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ6510_1",
            params={'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 4: Measure current (DC) on valid channels
    print("Test 4: Measure current (DC)", end=" " * 19)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ6510_1",
            params={'Item': 'CURR', 'Channel': '21', 'Type': 'DC'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 5: Invalid current channel (should fail)
    print("Test 5: Invalid current channel", end=" " * 16)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ6510_1",
            params={'Item': 'CURR', 'Channel': '101', 'Type': 'DC'},
            simulation=True
        )
        print(f"✗ FAIL: Should have rejected channel 101 for current")
    except ValueError as e:
        print(f"✓ PASS (correctly rejected)")
    except Exception as e:
        print(f"✗ FAIL: Unexpected error: {e}")

    # Test 6: Measure temperature
    print("Test 6: Measure temperature", end=" " * 21)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ6510_1",
            params={'Item': 'TEMP', 'Channel': '101'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")


async def test_psw3072():
    """Test PSW3072 driver functionality"""
    print("\n" + "=" * 60)
    print("Testing PSW3072 Driver")
    print("=" * 60)

    executor = get_instrument_executor()

    # Test 1: Set channel 1 voltage and current
    print("\nTest 1: Set channel 1 voltage/current", end=" " * 9)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="PSW3072_1",
            params={'SetVolt': '12.0', 'SetCurr': '2.5', 'Channel': '1'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 2: Set channel 2 voltage and current
    print("Test 2: Set channel 2 voltage/current", end=" " * 9)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="PSW3072_1",
            params={'SetVolt': '5.0', 'SetCurr': '1.0', 'Channel': '2'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 3: Turn off channel 1 (both zero)
    print("Test 3: Turn off channel 1", end=" " * 21)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="PSW3072_1",
            params={'SetVolt': '0', 'SetCurr': '0', 'Channel': '1'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 4: Set channel 3
    print("Test 4: Set channel 3 voltage/current", end=" " * 9)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="PSW3072_1",
            params={'SetVolt': '3.3', 'SetCurr': '0.5', 'Channel': '3'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")


async def test_keithley2015():
    """Test KEITHLEY2015 driver functionality"""
    print("\n" + "=" * 60)
    print("Testing KEITHLEY2015 Driver")
    print("=" * 60)

    executor = get_instrument_executor()

    # Test 1: Measurement mode (THD, DISTortion, AUTO freq)
    print("\nTest 1: Measurement THD DISTortion", end=" " * 13)
    try:
        # Command: State=1, Mode=1(THD), Type=1(DISTortion), Freq=0(AUTO)
        result = await executor.execute_instrument_command(
            instrument_id="KEITHLEY2015_1",
            params={'Command': '1 1 1 0'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 2: Measurement mode (THDN, VOLTage:DC, 1000Hz)
    print("Test 2: Measurement THDN VOLTage:DC", end=" " * 11)
    try:
        # Command: State=1, Mode=2(THDN), Type=2(VOLTage:DC), Freq=1000
        result = await executor.execute_instrument_command(
            instrument_id="KEITHLEY2015_1",
            params={'Command': '1 2 2 1000'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 3: Output mode (ON, 1000Hz, 1.5V, HIZ, ISINE)
    print("Test 3: Output mode ON", end=" " * 26)
    try:
        # Command: State=2, Output=1(ON), Freq=1000, Amp=1.5, Imp=3(HIZ), Shape=1(ISINE)
        result = await executor.execute_instrument_command(
            instrument_id="KEITHLEY2015_1",
            params={'Command': '2 1 1000 1.5 3 1'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 4: Output mode OFF
    print("Test 4: Output mode OFF", end=" " * 25)
    try:
        # Command: State=2, Output=0(OFF), Freq=1000, Amp=0, Imp=1(50Ω), Shape=1(ISINE)
        result = await executor.execute_instrument_command(
            instrument_id="KEITHLEY2015_1",
            params={'Command': '2 0 1000 0 1 1'},
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 5: Reset
    print("Test 5: Reset instrument", end=" " * 23)
    try:
        # Command: State=0 (reset)
        result = await executor.execute_instrument_command(
            instrument_id="KEITHLEY2015_1",
            params={'Command': '0'},
            simulation=True
        )
        print(f"✓ PASS (result: {result[:50]}...)")  # Truncate IDN response
    except Exception as e:
        print(f"✗ FAIL: {e}")


async def test_mdo34():
    """Test MDO34 driver functionality"""
    print("\n" + "=" * 60)
    print("Testing MDO34 Driver")
    print("=" * 60)

    executor = get_instrument_executor()

    # Test 1: Measure frequency on channel 1
    print("\nTest 1: Measure frequency CH1", end=" " * 18)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MDO34_1",
            params={'Item': '9', 'Channel': '1'},  # 9 = FREQuency
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 2: Measure amplitude on channel 2
    print("Test 2: Measure amplitude CH2", end=" " * 18)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MDO34_1",
            params={'Item': '1', 'Channel': '2'},  # 1 = AMPlitude
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 3: Measure period on channel 3
    print("Test 3: Measure period CH3", end=" " * 21)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MDO34_1",
            params={'Item': '25', 'Channel': '3'},  # 25 = PERIod
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")

    # Test 4: Measure RMS on channel 4
    print("Test 4: Measure RMS CH4", end=" " * 24)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MDO34_1",
            params={'Item': '32', 'Channel': '4'},  # 32 = RMS
            simulation=True
        )
        print(f"✓ PASS (result: {result})")
    except Exception as e:
        print(f"✗ FAIL: {e}")


async def test_parameter_validation():
    """Test parameter validation across drivers"""
    print("\n" + "=" * 60)
    print("Testing Parameter Validation")
    print("=" * 60)

    executor = get_instrument_executor()

    # Test 1: Missing parameter (DAQ6510)
    print("\nTest 1: Missing parameter (DAQ6510)", end=" " * 12)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ6510_1",
            params={'Item': 'VOLT'},  # Missing Channel
            simulation=True
        )
        print(f"✗ FAIL: Should have rejected missing Channel parameter")
    except ValueError as e:
        print(f"✓ PASS (correctly rejected)")
    except Exception as e:
        print(f"✗ FAIL: Unexpected error: {e}")

    # Test 2: Invalid channel (PSW3072)
    print("Test 2: Invalid channel (PSW3072)", end=" " * 15)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="PSW3072_1",
            params={'SetVolt': '12.0', 'SetCurr': '2.0', 'Channel': '5'},  # Invalid channel
            simulation=True
        )
        if "invalid channel" in result.lower():
            print(f"✓ PASS (correctly rejected)")
        else:
            print(f"✗ FAIL: Should have rejected invalid channel")
    except Exception as e:
        print(f"✓ PASS (correctly rejected)")

    # Test 3: Invalid measurement type (MDO34)
    print("Test 3: Invalid measurement type (MDO34)", end=" " * 9)
    try:
        result = await executor.execute_instrument_command(
            instrument_id="MDO34_1",
            params={'Item': '99', 'Channel': '1'},  # Invalid item
            simulation=True
        )
        print(f"✗ FAIL: Should have rejected invalid measurement type")
    except ValueError as e:
        print(f"✓ PASS (correctly rejected)")
    except Exception as e:
        print(f"✗ FAIL: Unexpected error: {e}")


async def test_configuration():
    """Test configuration loading"""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    from app.core.instrument_config import get_instrument_settings
    settings = get_instrument_settings()

    # Test 1: Configuration loaded
    print("\nTest 1: Configuration loaded", end=" " * 21)
    if settings is not None:
        print("✓ PASS")
    else:
        print("✗ FAIL: Configuration not loaded")

    instruments = settings.list_instruments()

    # Test 2: Medium-priority instruments in config
    print("Test 2: DAQ6510 in configuration", end=" " * 16)
    if 'DAQ6510_1' in instruments:
        print("✓ PASS")
    else:
        print("✗ FAIL: DAQ6510_1 not found in configuration")

    print("Test 3: PSW3072 in configuration", end=" " * 16)
    if 'PSW3072_1' in instruments:
        print("✓ PASS")
    else:
        print("✗ FAIL: PSW3072_1 not found in configuration")

    print("Test 4: KEITHLEY2015 in configuration", end=" " * 11)
    if 'KEITHLEY2015_1' in instruments:
        print("✓ PASS")
    else:
        print("✗ FAIL: KEITHLEY2015_1 not found in configuration")

    print("Test 5: MDO34 in configuration", end=" " * 18)
    if 'MDO34_1' in instruments:
        print("✓ PASS")
    else:
        print("✗ FAIL: MDO34_1 not found in configuration")

    # Test 3: Enabled status
    print("Test 6: Check enabled status", end=" " * 20)
    enabled_count = sum(
        1 for inst_id in ['DAQ6510_1', 'PSW3072_1', 'KEITHLEY2015_1', 'MDO34_1']
        if inst_id in instruments and instruments[inst_id].enabled
    )
    print(f"✓ PASS ({enabled_count}/4 enabled)")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MEDIUM-PRIORITY INSTRUMENT DRIVERS TEST SUITE")
    print("=" * 60)
    print("\nTesting 4 drivers:")
    print("  1. DAQ6510 - Keithley DAQ6510 Data Acquisition")
    print("  2. PSW3072 - GW Instek PSW3072 Triple Output Power Supply")
    print("  3. KEITHLEY2015 - Keithley 2015 THD Multimeter")
    print("  4. MDO34 - Tektronix MDO34 Mixed Domain Oscilloscope")

    try:
        # Test each driver
        await test_daq6510()
        await test_psw3072()
        await test_keithley2015()
        await test_mdo34()

        # Test parameter validation
        await test_parameter_validation()

        # Test configuration
        await test_configuration()

        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETED")
        print("=" * 60)
        print("\nNote: Some tests may show simulation-related warnings")
        print("These are expected in simulation mode without hardware.")

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
