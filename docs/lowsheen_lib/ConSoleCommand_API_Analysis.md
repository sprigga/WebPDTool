# ConSoleCommand API Analysis

## Overview

`ConSoleCommand.py` provides a subprocess-based command execution utility with timeout support. It enables PDTool4 to execute external commands (Python scripts, system commands) and capture their output with configurable timeouts.

**Location:** `src/lowsheen_lib/ConSoleCommand.py`

**Primary Use Cases:**
- Execute external Python scripts for instrument control
- Run system commands with timeout protection
- Capture stdout/stderr from subprocess execution
- Integrate with SSH-based remote command execution

---

## Core Functions

### `console_send(command, timeout)`

Executes a command as a subprocess with timeout control and returns the stdout output.

**Parameters:**
- `command` (str or list): Command to execute. Can be:
  - String: Single command
  - List: Command with arguments (e.g., `['python', 'script.py', 'arg1']`)
- `timeout` (float): Maximum execution time in seconds

**Returns:**
- `str`: Decoded stdout output (UTF-8, ignoring errors)
- Empty string if no output or on error

**Behavior:**
1. Creates subprocess with `shell=False` for security
2. Redirects stderr to stdout for combined output capture
3. Waits for process completion or timeout
4. If timeout expires, kills the process and returns partial output
5. Decodes output as UTF-8, replacing invalid characters

**Error Handling:**
- `subprocess.TimeoutExpired`: Kills process, returns captured output
- Decoding errors: Uses `errors='ignore'` to skip invalid UTF-8 bytes

**Example Usage:**
```python
# Execute Python script with 5-second timeout
result = console_send(['python', './src/lowsheen_lib/L6MPU/ssh_cmd.py',
                      '192.168.5.1', 'command="gpioget gpiochip1 17"'], 5)
print(result)  # Output from the script
```

**Security Notes:**
- `shell=False` prevents shell injection attacks
- Command must be provided as list for proper argument parsing
- Timeout prevents runaway processes

---

## Command-Line Interface

### Main Block (`__main__`)

When executed as a script, parses command-line arguments and executes a command.

**Argument Format:**
```bash
python ConSoleCommand.py <test_name> <args_dict>
```

**Arguments:**
- `sys.argv[1]`: Test name (unused, reserved for compatibility)
- `sys.argv[2]`: JSON-like dictionary string containing:
  - `Command` (required): Command to execute
  - `Timeout` (optional): Timeout in milliseconds (default: 1000ms)

**Example:**
```bash
python ConSoleCommand.py eth_test "{'ItemKey': 'TT00-00', 'ValueType': 'string', 'LimitType': 'partial', 'EqLimit': 'end', 'ExecuteName': 'CommandTest', 'case': 'console', 'Command': 'python ./src/lowsheen_lib/testUTF/delay.py', 'Timeout': '5000'}"
```

**Processing Flow:**
1. Parse `sys.argv[2]` using `ast.literal_eval()` (safely evaluates Python literals)
2. Extract `Command` from dictionary
3. Extract `Timeout` (convert ms to seconds, default 1.0s)
4. Call `console_send(console_command, timeout)`
5. Print result to stdout

**Output:**
- Prints the command output to stdout
- Parent process can capture this output for result validation

---

## Integration with PDTool4

### Usage Pattern

ConSoleCommand is typically called by measurement modules (e.g., `CommandTestMeasurement.py`) to execute external commands:

```python
# In CommandTestMeasurement.py
command_args = {
    'Command': 'python ./src/lowsheen_lib/instrument_script.py',
    'Timeout': '3000'
}
process = subprocess.Popen(
    ['python', './src/lowsheen_lib/ConSoleCommand.py', 'test', str(command_args)],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
stdout, stderr = process.communicate()
result = stdout.decode('utf-8')
```

### Typical Command Examples

**1. SSH Remote Command:**
```python
console_send([
    'python', './src/lowsheen_lib/L6MPU/ssh_cmd.py',
    '192.168.5.1',
    'command="cat /dev/ttymxc0 > /output &"'
], timeout=2)
```

**2. Python Script Execution:**
```python
console_send(['python', './src/lowsheen_lib/testUTF/delay.py'], timeout=5)
```

**3. System Command:**
```python
console_send(['ls', '-la', '/path/to/dir'], timeout=1)
```

---

## Technical Details

### Process Management

**Subprocess Configuration:**
- `shell=False`: Prevents shell interpretation (secure)
- `stdout=subprocess.PIPE`: Captures standard output
- `stderr=subprocess.STDOUT`: Redirects errors to stdout

**Timeout Handling:**
```python
try:
    stdout_data, stderr_data = process.communicate(timeout=timeout)
except subprocess.TimeoutExpired:
    process.kill()  # Force terminate
    stdout_data, stderr_data = process.communicate()  # Collect partial output
```

### Encoding Handling

**UTF-8 with Error Tolerance:**
```python
return stdout_data.decode('utf-8', errors='ignore')
```
- Primary encoding: UTF-8
- `errors='ignore'`: Skips invalid byte sequences
- Ensures function always returns a string (no exceptions)

### Argument Parsing

**Dictionary Evaluation:**
```python
args = ast.literal_eval(sys.argv[2])  # Safe evaluation
console_command = args['Command']
timeout = float(args['Timeout']) if 'Timeout' in args else 1.0
```
- `ast.literal_eval()`: Safely parses Python literal structures
- No `eval()` usage (security best practice)
- Timeout converted from milliseconds string to float seconds

---

## Best Practices

### Security
1. **Always use list format for commands:**
   ```python
   # Good: Arguments properly escaped
   console_send(['python', 'script.py', user_input], timeout=5)

   # Bad: Shell injection risk
   console_send(f'python script.py {user_input}', timeout=5)
   ```

2. **Validate timeout values:**
   ```python
   timeout = max(1.0, float(args.get('Timeout', 1000)) / 1000)
   ```

3. **Handle command not found:**
   ```python
   try:
       result = console_send(command, timeout)
   except FileNotFoundError:
       print("Error: Command not found")
   ```

### Timeout Selection
- **Short operations (GPIO read):** 1-2 seconds
- **Network operations (SSH):** 3-5 seconds
- **Complex measurements:** 10-30 seconds
- **Long-running tests:** 60+ seconds

### Error Detection
```python
result = console_send(command, timeout)
if "Error" in result or "No instrument found" in result:
    # Handle error condition
    pass
```

---

## Limitations

1. **No Real-Time Output:** Cannot stream output during execution (buffered until completion)
2. **No Interactive Commands:** Cannot handle commands requiring user input
3. **Process Cleanup:** Killed processes may leave resources in inconsistent state
4. **Error Granularity:** stderr merged into stdout, hard to distinguish error types

---

## Related Files

- `CommandTestMeasurement.py` - Primary consumer of ConSoleCommand
- `src/lowsheen_lib/L6MPU/ssh_cmd.py` - SSH command execution (uses ConSoleCommand)
- `oneCSV_atlas_2.py` - Test orchestrator that calls measurement modules

---

## Version History

- Current implementation supports timeout-based command execution
- UTF-8 decoding with error tolerance added for international character support
- `ast.literal_eval()` used for secure argument parsing

---

## Testing

### Manual Test Example

```bash
# Test with short delay
python src/lowsheen_lib/ConSoleCommand.py test "{'Command': 'echo Hello World', 'Timeout': '1000'}"

# Test with timeout expiration
python src/lowsheen_lib/ConSoleCommand.py test "{'Command': 'sleep 10', 'Timeout': '2000'}"

# Test with Python script
python src/lowsheen_lib/ConSoleCommand.py test "{'Command': 'python -c \"print(123)\"', 'Timeout': '1000'}"
```

### Expected Output
- Successful execution: Command output string
- Timeout: Partial output before termination
- Error: Empty string or error message from subprocess
