#!/usr/bin/env python3
"""
Test script to verify custom test scripts validation fix
"""
import sys
import asyncio
sys.path.insert(0, 'backend')

from app.services.measurement_service import MeasurementService


async def test_validation():
    """Test that custom script names are now accepted"""
    service = MeasurementService()

    test_cases = [
        # (measurement_type, switch_mode, expected_valid, description)
        ('Other', '123_1', True, 'Custom script 123_1'),
        ('Other', '123_2', True, 'Custom script 123_2'),
        ('Other', 'WAIT_FIX_5sec', True, 'Custom script WAIT_FIX_5sec'),
        ('Other', 'test123', True, 'Custom script test123'),
        ('wait', 'wait', True, 'Wait test type'),
        ('Wait', 'wait', True, 'Wait test type (uppercase)'),
        ('Other', 'any_custom_name', True, 'Any custom script name'),

        # Standard measurement types should still work
        ('PowerSet', 'DAQ973A', False, 'PowerSet missing params (should fail)'),
        ('PowerRead', 'DAQ973A', False, 'PowerRead missing params (should fail)'),
        ('CommandTest', 'comport', False, 'CommandTest missing params (should fail)'),

        # CommandTest with custom script should work
        ('CommandTest', 'my_script', True, 'CommandTest with command param'),
    ]

    print("Running validation tests...\n")
    passed = 0
    failed = 0

    for measurement_type, switch_mode, expected_valid, description in test_cases:
        # For custom scripts, provide command parameter
        test_params = {}
        if 'custom' in description.lower() or 'CommandTest with command' in description:
            test_params = {'command': 'python test.py'}

        result = await service.validate_params(measurement_type, switch_mode, test_params)

        actual_valid = result['valid']
        status = '✓' if actual_valid == expected_valid else '✗'

        if actual_valid == expected_valid:
            passed += 1
            print(f"{status} PASS: {description}")
            print(f"   {measurement_type}/{switch_mode} → valid={actual_valid}")
        else:
            failed += 1
            print(f"{status} FAIL: {description}")
            print(f"   {measurement_type}/{switch_mode} → expected {expected_valid}, got {actual_valid}")
            if result.get('suggestions'):
                print(f"   Suggestions: {result['suggestions']}")
        print()

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        print("\n❌ Some tests failed!")
        return False
    else:
        print("\n✅ All tests passed!")
        return True


if __name__ == '__main__':
    success = asyncio.run(test_validation())
    sys.exit(0 if success else 1)
