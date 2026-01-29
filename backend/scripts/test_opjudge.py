#!/usr/bin/env python3
"""
OPjudge Integration Test Script
Tests terminal-based OPjudge scripts directly
"""

import subprocess
import sys
from pathlib import Path


def test_opjudge_confirm():
    """Test OPjudge confirm mode terminal script"""
    print("\n" + "="*60)
    print("TEST 1: OPjudge Confirm Mode (Terminal)")
    print("="*60)

    backend_dir = Path(__file__).parent.parent
    script_path = backend_dir / "src" / "lowsheen_lib" / "OPjudge_confirm_terminal.py"

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    # Test parameters
    test_point_id = "LED_Color_Check"
    test_params = "['ImagePath=/tmp/test_led.jpg', 'content=Check if LED is green']"

    print(f"\n📋 Test Point: {test_point_id}")
    print(f"📋 Test Params: {test_params}")
    print("\nExecuting script...")
    print("-"*60)

    try:
        result = subprocess.run(
            ["python3", str(script_path), test_point_id, test_params],
            capture_output=True,
            text=True,
            timeout=30,
            input="\n"  # Auto-confirm with Enter key
        )

        print("\n" + "-"*60)
        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"\nReturn Code: {result.returncode}")

        if result.returncode == 0:
            if "PASS" in result.stdout or "FAIL" in result.stdout:
                print("\n✅ Test PASSED - Script executed successfully")
                return True
            else:
                print("\n⚠️  Test WARNING - Script executed but unexpected output")
                return True
        else:
            print("\n❌ Test FAILED - Script returned non-zero exit code")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ Test FAILED - Script timed out")
        return False
    except Exception as e:
        print(f"\n❌ Test FAILED - Exception: {e}")
        return False


def test_opjudge_yorn():
    """Test OPjudge YorN mode terminal script"""
    print("\n" + "="*60)
    print("TEST 2: OPjudge YorN Mode (Terminal)")
    print("="*60)

    backend_dir = Path(__file__).parent.parent
    script_path = backend_dir / "src" / "lowsheen_lib" / "OPjudge_YorN_terminal.py"

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    # Test parameters
    test_point_id = "Display_Check"
    test_params = "['ImagePath=/tmp/display.png', 'content=Is the display showing correct image?']"

    print(f"\n📋 Test Point: {test_point_id}")
    print(f"📋 Test Params: {test_params}")
    print("\nExecuting script...")
    print("-"*60)

    try:
        result = subprocess.run(
            ["python3", str(script_path), test_point_id, test_params],
            capture_output=True,
            text=True,
            timeout=30,
            input="y\n"  # Auto-answer with 'y'
        )

        print("\n" + "-"*60)
        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"\nReturn Code: {result.returncode}")

        if result.returncode == 0:
            if "PASS" in result.stdout or "FAIL" in result.stdout:
                print("\n✅ Test PASSED - Script executed successfully")
                return True
            else:
                print("\n⚠️  Test WARNING - Script executed but unexpected output")
                return True
        else:
            print("\n❌ Test FAILED - Script returned non-zero exit code")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ Test FAILED - Script timed out")
        return False
    except Exception as e:
        print(f"\n❌ Test FAILED - Exception: {e}")
        return False


def test_opjudge_error_handling():
    """Test OPjudge error handling"""
    print("\n" + "="*60)
    print("TEST 3: OPjudge Error Handling")
    print("="*60)

    backend_dir = Path(__file__).parent.parent
    script_path = backend_dir / "src" / "lowsheen_lib" / "OPjudge_confirm_terminal.py"

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    # Test with invalid arguments
    print("\n📋 Testing with invalid arguments (missing TestParams)")
    print("-"*60)

    try:
        result = subprocess.run(
            ["python3", str(script_path), "Test_Point"],  # Missing TestParams argument
            capture_output=True,
            text=True,
            timeout=10
        )

        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn Code: {result.returncode}")

        if result.returncode != 0 and "ERROR" in result.stderr:
            print("\n✅ Test PASSED - Script correctly handles invalid arguments")
            return True
        else:
            print("\n❌ Test FAILED - Script should have returned error")
            return False

    except Exception as e:
        print(f"\n❌ Test FAILED - Exception: {e}")
        return False


def main():
    """Run all OPjudge tests"""
    print("\n" + "="*60)
    print("OPjudge Integration Test Suite")
    print("="*60)
    print("\nThis script tests the terminal-based OPjudge scripts")
    print("that are used in Docker/headless environments.")
    print("\nNote: Tests will auto-respond to prompts for non-interactive execution.")

    results = []

    # Run tests
    results.append(("OPjudge Confirm Mode", test_opjudge_confirm()))
    results.append(("OPjudge YorN Mode", test_opjudge_yorn()))
    results.append(("OPjudge Error Handling", test_opjudge_error_handling()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
