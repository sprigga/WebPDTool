# Wait_test.py API Analysis

## Overview

`Wait_test.py` is a simple timing utility that provides programmable delays in test sequences. It's designed to insert precise wait periods between test steps, allowing for device stabilization, relay settling, or any timing-critical operations in automated manufacturing tests.

**File Location:** `src/lowsheen_lib/Wait_test.py`
**Module Type:** Command-line utility script
**Primary Function:** Programmable delay/sleep operation
**Precision:** Millisecond resolution
**Typical Use Case:** Test sequence timing control

---

## Core Functionality

### Main Features

1. **Millisecond-Precision Delays** - Accepts wait time in milliseconds for precise timing control
2. **Command-line Interface** - Integrates seamlessly with PDTool4's subprocess execution pattern
3. **Simple and Reliable** - Minimal code surface for maximum reliability
4. **JSON Parameter Parsing** - Consistent with PDTool4's parameter passing convention

---

## API Reference

### Command-Line Interface

#### Usage

```bash
python src/lowsheen_lib/Wait_test.py <test_name> <params_json>
```

#### Parameters

**sys.argv[1]:** Test name identifier (not used in current implementation)
**sys.argv[2]:** JSON-like dictionary string with the following key:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WaitmSec` | integer/string | Yes | Wait duration in milliseconds |

#### Parameter Parsing Logic

```python
# Line 10-13: Parameter extraction
args = sys.argv[2]
args = ast.literal_eval(args)  # Convert string to dictionary

wait_msec = int(args['WaitmSec']) if 'WaitmSec' in args else ''
wait_sec = wait_msec / 1000  # Convert to seconds
```

**Notes:**
- If `WaitmSec` is missing, sets `wait_msec` to empty string `''`
- Empty string will cause a TypeError when dividing by 1000 (not handled)

---

## Usage Examples

### Example 1: Basic Wait Command

```bash
python src/lowsheen_lib/Wait_test.py wait_delay "{'WaitmSec': '5000'}"
```

**Execution:**
- Waits for 5000 milliseconds (5 seconds)
- Outputs: `Waited for 5.0 secs`

### Example 2: Short Delay

```bash
python src/lowsheen_lib/Wait_test.py relay_settle "{'WaitmSec': '100'}"
```

**Execution:**
- Waits for 100 milliseconds (0.1 seconds)
- Outputs: `Waited for 0.1 secs`

### Example 3: From PDTool4 Test Plan

```python
# Typical invocation from CommandTestMeasurement.py or similar
import subprocess

params = {
    'WaitmSec': '2000',
    'ItemKey': 'WAIT-001',
    'ValueType': 'string',
    'LimitType': 'none'
}

result = subprocess.run(
    ['python', 'src/lowsheen_lib/Wait_test.py', 'wait_test', str(params)],
    capture_output=True,
    text=True
)

print(result.stdout)  # "Waited for 2.0 secs"
```

---

## Integration with PDTool4

### Test Plan CSV Configuration

This utility is typically configured in test plan CSV files with the following columns:

| Column | Example Value |
|--------|---------------|
| ExecuteName | `Wait_test` or `Other` |
| case | `wait` |
| WaitmSec | `1000` (wait 1 second) |

### Typical Use Cases

#### 1. Device Power-On Stabilization
```csv
項次,品名規格,下限值,上限值,ExecuteName,case,WaitmSec
1,Power On Wait,,,Other,wait,3000
```
Wait 3 seconds after powering on device for voltage stabilization.

#### 2. Relay Settling Time
```csv
項次,品名規格,下限值,上限值,ExecuteName,case,WaitmSec
5,Relay Settle,,,Other,wait,200
```
Wait 200ms for relay contacts to settle before measurement.

#### 3. Communication Timeout
```csv
項次,品名規格,下限值,上限值,ExecuteName,case,WaitmSec
8,SPI Wait,,,Other,wait,500
```
Wait 500ms for SPI communication to complete.

#### 4. Temperature Stabilization
```csv
項次,品名規格,下限值,上限值,ExecuteName,case,WaitmSec
12,Temp Stabilize,,,Other,wait,10000
```
Wait 10 seconds for temperature to stabilize after thermal load.

---

## Execution Flow

### Integration Pattern

```
Test Plan CSV → oneCSV_atlas_2.py → Test Measurement Class
                                            ↓
                                    subprocess.run()
                                            ↓
                            uv run python Wait_test.py <args>
                                            ↓
                                        time.sleep()
                                            ↓
                                    Print to stdout
                                            ↓
                        Measurement captures and validates
```

### Example Measurement Integration

```python
# Example from OtherMeasurement.py or similar
import subprocess
import ast

class WaitMeasurement:
    def execute(self, params):
        """Execute wait operation"""
        result = subprocess.run(
            ['uv', 'run', 'python', 'src/lowsheen_lib/Wait_test.py',
             'wait_test', str(params)],
            capture_output=True,
            text=True,
            timeout=params.get('Timeout', 60)
        )

        output = result.stdout.strip()
        # Output: "Waited for X secs"

        return {
            'status': 'PASS',
            'value': output,
            'message': f'Wait completed: {output}'
        }
```

---

## Code Quality Analysis

### Strengths

✅ **Simplicity** - Minimal code reduces failure modes
✅ **Clear Purpose** - Single responsibility (timing delay)
✅ **PDTool4 Compatible** - Follows standard parameter passing pattern
✅ **Human-Readable Output** - Clear status message for debugging

### Areas for Improvement

#### 1. Missing Error Handling

**Current Code:**
```python
wait_msec = int(args['WaitmSec']) if 'WaitmSec' in args else ''
wait_sec = wait_msec / 1000  # TypeError if wait_msec is ''
```

**Issue:** If `WaitmSec` is missing, `wait_msec` becomes empty string `''`, causing:
```
TypeError: unsupported operand type(s) for /: 'str' and 'int'
```

**Recommended Fix:**
```python
wait_msec = int(args.get('WaitmSec', 0))
if wait_msec <= 0:
    print("Error: WaitmSec must be positive integer")
    sys.exit(1)

wait_sec = wait_msec / 1000
```

#### 2. No Input Validation

**Missing Checks:**
- Negative values (would cause no wait)
- Zero values (valid but might be unintentional)
- Extremely large values (could cause confusion or timeout)
- Non-numeric input (handled by int() but with cryptic error)

**Recommended Validation:**
```python
try:
    wait_msec = int(args.get('WaitmSec', 0))
except (ValueError, TypeError):
    print("Error: WaitmSec must be an integer")
    sys.exit(1)

if wait_msec < 0:
    print("Error: WaitmSec cannot be negative")
    sys.exit(1)

if wait_msec > 3600000:  # 1 hour
    print("Warning: Wait time exceeds 1 hour")

wait_sec = wait_msec / 1000
```

#### 3. Commented-Out Code

```python
# Lines 7-8: Old parameter parsing method (commented out)
# args = dict(arg.split('=') for arg in sys.argv[2:])
# wait_msec = int(args.get('WaitmSec', ''))
```

**Recommendation:** Remove commented code for cleaner codebase.

#### 4. Hardcoded Output Format

The output format is hardcoded:
```python
response = f"Waited for {wait_sec} secs"
```

**Enhancement Suggestion:**
```python
# More informative output
response = f"Waited for {wait_sec} secs ({wait_msec} ms)"
# Output: "Waited for 2.5 secs (2500 ms)"
```

#### 5. No Precision Control

Python's `time.sleep()` precision varies by platform:
- **Windows:** ~15ms resolution
- **Linux:** ~1ms resolution
- **Real-time OS:** <1ms resolution

For critical timing, consider documenting expected precision or using high-resolution timers.

---

## Improved Implementation Example

Here's an enhanced version with better error handling:

```python
import sys
import time
import ast

def validate_wait_time(wait_msec):
    """Validate wait time parameter"""
    if not isinstance(wait_msec, (int, float)):
        return False, "WaitmSec must be numeric"

    if wait_msec < 0:
        return False, "WaitmSec cannot be negative"

    if wait_msec > 3600000:  # 1 hour
        return False, "WaitmSec exceeds maximum (1 hour)"

    return True, None

if __name__ == "__main__":
    try:
        # Parse arguments
        args = ast.literal_eval(sys.argv[2])

        # Extract and validate wait time
        wait_msec = int(args.get('WaitmSec', 0))
        is_valid, error_msg = validate_wait_time(wait_msec)

        if not is_valid:
            print(f"Error: {error_msg}")
            sys.exit(1)

        # Perform wait
        wait_sec = wait_msec / 1000
        time.sleep(wait_sec)

        # Output result
        response = f"Waited for {wait_sec} secs ({wait_msec} ms)"
        print(response)

    except (IndexError, SyntaxError, ValueError) as e:
        print(f"Error: Invalid parameters - {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Error: Wait interrupted by user")
        sys.exit(1)
```

**Improvements:**
- ✅ Comprehensive error handling
- ✅ Input validation with clear error messages
- ✅ Handles keyboard interrupts gracefully
- ✅ More informative output format
- ✅ Exit codes for error detection

---

## Timing Precision Considerations

### Platform-Specific Sleep Behavior

#### Windows
```python
time.sleep(0.001)  # Actual: ~15ms (OS scheduler tick)
time.sleep(0.100)  # Actual: ~100-115ms
time.sleep(1.000)  # Actual: ~1000-1015ms
```

#### Linux
```python
time.sleep(0.001)  # Actual: ~1-2ms
time.sleep(0.100)  # Actual: ~100-101ms
time.sleep(1.000)  # Actual: ~1000-1001ms
```

### High-Precision Alternative

For critical timing on Windows, consider:
```python
import time
import platform

def precise_sleep(seconds):
    """High-precision sleep using busy-wait for short durations"""
    if platform.system() == 'Windows' and seconds < 0.050:
        # Use busy-wait for <50ms on Windows
        target = time.perf_counter() + seconds
        while time.perf_counter() < target:
            pass
    else:
        time.sleep(seconds)
```

**Caution:** Busy-wait consumes 100% CPU for the duration.

---

## Testing Recommendations

### Unit Tests

```python
import subprocess
import time
import pytest

def test_wait_1_second():
    """Test 1 second wait"""
    start = time.perf_counter()

    result = subprocess.run(
        ['python', 'src/lowsheen_lib/Wait_test.py', 'test', "{'WaitmSec': '1000'}"],
        capture_output=True,
        text=True
    )

    elapsed = time.perf_counter() - start

    assert result.returncode == 0
    assert "Waited for 1.0 secs" in result.stdout
    assert 0.95 < elapsed < 1.10  # Allow 5-10% variance

def test_wait_100_milliseconds():
    """Test 100ms wait"""
    start = time.perf_counter()

    result = subprocess.run(
        ['python', 'src/lowsheen_lib/Wait_test.py', 'test', "{'WaitmSec': '100'}"],
        capture_output=True,
        text=True
    )

    elapsed = time.perf_counter() - start

    assert result.returncode == 0
    assert "Waited for 0.1 secs" in result.stdout
    assert 0.08 < elapsed < 0.15  # More variance for short waits

def test_missing_parameter():
    """Test missing WaitmSec parameter"""
    result = subprocess.run(
        ['python', 'src/lowsheen_lib/Wait_test.py', 'test', "{}"],
        capture_output=True,
        text=True
    )

    # Current behavior: crashes with TypeError
    # Expected behavior: graceful error message
    assert result.returncode != 0  # Should fail

def test_invalid_parameter():
    """Test invalid WaitmSec value"""
    result = subprocess.run(
        ['python', 'src/lowsheen_lib/Wait_test.py', 'test', "{'WaitmSec': 'abc'}"],
        capture_output=True,
        text=True
    )

    assert result.returncode != 0  # Should fail
```

### Integration Tests

```python
def test_wait_in_test_sequence():
    """Test wait as part of measurement sequence"""
    from oneCSV_atlas_2 import execute_test_plan

    # Test plan with wait steps
    test_plan = [
        {'ExecuteName': 'PowerSet', 'params': {'voltage': 12.0}},
        {'ExecuteName': 'Wait_test', 'params': {'WaitmSec': 2000}},
        {'ExecuteName': 'PowerRead', 'params': {'expected': 12.0}},
    ]

    start = time.perf_counter()
    results = execute_test_plan(test_plan)
    elapsed = time.perf_counter() - start

    assert elapsed >= 2.0  # At least 2 seconds elapsed
    assert results['Wait_test']['status'] == 'PASS'
```

---

## Common Use Patterns

### 1. Power Supply Stabilization

```python
# After setting power supply voltage
params = {'WaitmSec': '3000'}  # Wait 3 seconds for stabilization
# Voltage settles within 3s before measurement
```

### 2. Relay Contact Settling

```python
# After switching relay
params = {'WaitmSec': '200'}  # Wait 200ms for relay to settle
# Prevents contact bounce affecting measurements
```

### 3. Device Boot Wait

```python
# After device reset
params = {'WaitmSec': '10000'}  # Wait 10 seconds for boot
# Ensures device firmware is fully loaded
```

### 4. Communication Protocol Timing

```python
# Between command and response
params = {'WaitmSec': '500'}  # Wait 500ms for protocol timeout
# Allows slow devices to process command
```

### 5. Thermal Stabilization

```python
# After thermal load application
params = {'WaitmSec': '30000'}  # Wait 30 seconds for thermal equilibrium
# Temperature-sensitive measurements need stable conditions
```

---

## Related Files

- **OtherMeasurement.py** - Measurement class that commonly uses Wait_test
- **CommandTestMeasurement.py** - Alternative measurement class for wait operations
- **oneCSV_atlas_2.py** - Test execution engine that orchestrates wait timing

---

## Best Practices

### Choosing Wait Durations

| Scenario | Recommended Duration | Notes |
|----------|---------------------|-------|
| Relay settling | 50-200ms | Mechanical contact stabilization |
| Power supply settling | 1-5s | Voltage regulation stabilization |
| Device boot | 5-30s | Depends on firmware complexity |
| I2C/SPI timing | 10-100ms | Protocol-specific delays |
| Temperature stabilization | 30-300s | Thermal mass dependent |

### Performance Optimization

```python
# ❌ Bad: Multiple small waits
Wait_test({'WaitmSec': '100'})
some_operation()
Wait_test({'WaitmSec': '100'})
another_operation()
Wait_test({'WaitmSec': '100'})

# ✅ Good: Single consolidated wait
some_operation()
another_operation()
Wait_test({'WaitmSec': '300'})  # Combined wait after operations
```

---

## Conclusion

`Wait_test.py` provides essential timing control for PDTool4's automated test sequences. While the implementation is simple and effective, it would benefit from:

1. **Error handling** for missing or invalid parameters
2. **Input validation** to prevent negative or excessive wait times
3. **Better documentation** of platform-specific timing precision
4. **Enhanced output** showing both seconds and milliseconds

The utility is reliable for its core purpose but should include defensive programming practices for production environments where parameter errors could cause test failures or confusion.

**Recommendation:** Implement the improved version with comprehensive error handling to make the utility more robust and user-friendly.
