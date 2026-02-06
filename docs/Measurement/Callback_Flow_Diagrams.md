# Callback Flow Diagrams

## Overview

This document provides detailed callback flow diagrams for measurement execution in WebPDTool, showing the complete call chain from API request to hardware interaction.

```
★ Insight ─────────────────────────────────────
1. **Lazy Initialization**: Drivers are created only when first accessed, then cached in driver._initialized flag
2. **Context Manager Pattern**: connection_pool.get_connection() uses async context managers for automatic cleanup
3. **Result Propagation**: MeasurementResult flows through execute() → validate_result() → database → frontend
─────────────────────────────────────────────────
```

## 1. PowerRead Measurement Flow

### Complete Call Chain

```
┌─────────────────────────────────────────────────────────────┐
│ API Layer: POST /api/tests/sessions/start                   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ TestEngine.execute_test_session()                           │
│ - Creates test session                                       │
│ - Iterates through test plan items                          │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ MeasurementService.execute_single_measurement()              │
│ Parameters:                                                  │
│ - measurement_type: "PowerRead"                             │
│ - switch_mode: "DAQ973A"                                    │
│ - test_params: {Instrument, Channel, Item, Type}            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
         ┌─────────────┴──────────────┐
         │                            │
    [LEGACY PATH]               [MODERN PATH] ⭐
         │                            │
         ↓                            ↓
┌─────────────────────┐    ┌─────────────────────────────────┐
│ _execute_power_read │    │ implementations.py               │
│                     │    │ PowerReadMeasurement.execute()  │
└─────────┬───────────┘    └──────────────┬──────────────────┘
          │                              │
          ↓                              ↓
┌─────────────────────┐    ┌─────────────────────────────────────┐
│ validate_params()    │    │ # Line 167: Start of execute()    │
│ - Check required    │    │ from app.services.                 │
│   parameters        │    │     instrument_connection import   │
└─────────┬───────────┘    │     get_connection_pool            │
          │               │ from app.services.instruments import │
          ↓               │     get_driver_class               │
┌─────────────────────┐    │ from app.core.instrument_config    │
│ _execute_instrument_│    │     import get_instrument_settings │
│ command()           │    └──────────────┬──────────────────────┘
│ - subprocess.run()  │                   ↓
│ - script: DAQ973A_  │    ┌─────────────────────────────────────┐
│   test.py           │    │ # Line 175: Get parameters         │
└─────────┬───────────┘    │ instrument_name = get_param(      │
          │               │     test_params, "Instrument"     │
          ↓               │ channel = get_param(              │
┌─────────────────────┐    │     test_params, "Channel")       │
│ Parse response      │    │ item = get_param(                 │
│ - response.decode() │    │     test_params, "Item")          │
│ - strip()           │    └──────────────┬──────────────────────┘
│ - Decimal(float())  │                   ↓
└─────────┬───────────┘    ┌─────────────────────────────────────┐
          │               │ # Line 200: Get instrument config  │
          ↓               │ instrument_settings =               │
┌─────────────────────┐    │     get_instrument_settings()      │
│ Return              │    │ config = instrument_settings.      │
│ MeasurementResult   │    │     get_instrument(instrument_name)│
└─────────────────────┘    └──────────────┬──────────────────────┘
                                      ↓
                          ┌─────────────────────────────────────┐
                          │ # Line 209: Get driver class       │
                          │ driver_class = get_driver_class(   │
                          │     config.type)                    │
                          └──────────────┬──────────────────────┘
                                         ↓
                          ┌─────────────────────────────────────┐
                          │ # Line 217: Get connection         │
                          │ connection_pool =                  │
                          │     get_connection_pool()          │
                          │ async with connection_pool.         │
                          │     get_connection(instrument_name) │
                          │     as conn:                       │
                          └──────────────┬──────────────────────┘
                                         ↓
                          ┌─────────────────────────────────────┐
                          │ # Line 219: Create driver          │
                          │ driver = driver_class(conn)        │
                          └──────────────┬──────────────────────┘
                                         ↓
                          ┌─────────────────────────────────────┐
                          │ # Line 222-224: Initialize        │
                          │ if not hasattr(driver, '_initial… │
                          │     await driver.initialize()      │
                          │     driver._initialized = True     │
                          └──────────────┬──────────────────────┘
                                         ↓
                          ┌─────────────────────────────────────┐
                          │ # Line 227: Execute measurement    │
                          │ measured_value = await             │
                          │   _measure_with_driver(            │
                          │     driver, config.type,           │
                          │     measure_type, channel)         │
                          └──────────────┬──────────────────────┘
                                         ↓
                          ┌─────────────────────────────────────┐
                          │ # Line 263-277: DAQ973A specific  │
                          │ if instrument_type in ('DAQ973A', │
                          │                          'DAQ6510')│
                          │   channels = [str(channel)]        │
                          │   if measure_type == 'voltage':    │
                          │     return await driver.           │
                          │       measure_voltage(channels)    │
                          │   else:  # current                 │
                          │     return await driver.           │
                          │       measure_current(channels)    │
                          └──────────────┬──────────────────────┘
                                         ↓
                          ┌─────────────────────────────────────┐
                          │ # Line 232: Validate result        │
                          │ is_valid, error_msg =              │
                          │   self.validate_result(            │
                          │     measured_value)                │
                          └──────────────┬──────────────────────┘
                                         ↓
                          ┌─────────────────────────────────────┐
                          │ # Line 233-237: Create result      │
                          │ return self.create_result(         │
                          │   result="PASS" if is_valid        │
                          │          else "FAIL",              │
                          │   measured_value=measured_value,   │
                          │   error_message=error_msg          │
                          │     if not is_valid else None)     │
                          └──────────────┬──────────────────────┘
                                         ↓
                          ┌─────────────────────────────────────┐
                          │ Save to database via               │
                          │ _save_measurement_result()         │
                          └─────────────────────────────────────┘
```

### DAQ973A Voltage Measurement Example

```python
# Input parameters
test_params = {
    "Instrument": "daq973a_1",
    "Channel": "101",
    "Item": "volt",
    "Type": "DC"
}

# Execution flow
1. get_param() extracts: instrument_name="daq973a_1", channel="101", item="volt"
2. item_lower = "volt" → measure_type = 'voltage'
3. get_instrument_settings().get_instrument("daq973a_1")
   → Returns InstrumentConfig(type="DAQ973A", address="TCPIP0::192.168.1.100::inst0::INSTR")
4. get_driver_class("DAQ973A")
   → Returns DAQ973ADriver class
5. connection_pool.get_connection("daq973a_1")
   → Returns TCPIPConnection instance
6. driver = DAQ973ADriver(conn)
7. await driver.initialize()
   → Sends *IDN? query, configures DAQ973A
8. await driver.measure_voltage(["101"])
   → Sends "MEAS:VOLT:DC? (@101)"
   → Returns Decimal("5.02")
9. validate_result(Decimal("5.02"), lower_limit=4.8, upper_limit=5.2)
   → Returns (True, None)
10. create_result(result="PASS", measured_value=Decimal("5.02"))
```

## 2. PowerSet Measurement Flow

### Complete Call Chain

```
┌─────────────────────────────────────────────────────────────┐
│ PowerSetMeasurement.execute() [Line 364]                    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 372-387: Get and validate parameters                 │
│ instrument_name = get_param(test_params, "Instrument")      │
│ voltage = get_param(test_params, "SetVolt", "Voltage")      │
│ current = get_param(test_params, "SetCurr", "Current")      │
│ channel = get_param(test_params, "Channel", "channel")      │
│                                                             │
│ # Convert to float                                          │
│ voltage_val = float(voltage)  # e.g., 5.0                   │
│ current_val = float(current)  # e.g., 2.0                   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 405-411: Get instrument configuration                │
│ instrument_settings = get_instrument_settings()             │
│ config = instrument_settings.get_instrument(instrument_name)│
│ driver_class = get_driver_class(config.type)                │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 422-424: Get connection and create driver            │
│ connection_pool = get_connection_pool()                     │
│ async with connection_pool.get_connection(instrument_name)  │
│     as conn:                                                │
│     driver = driver_class(conn)                             │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 427-429: Initialize if needed                        │
│ if not hasattr(driver, '_initialized'):                     │
│     await driver.initialize()                               │
│     driver._initialized = True                              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 432-434: Execute power set based on instrument type │
│ result_msg = await self._set_power_with_driver(            │
│     driver, config.type, voltage_val, current_val, channel) │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
         ┌─────────────┴───────────────────┐
         │                                 │
    [MODEL2303]                      [MODEL2306]
         │                                 │
         ↓                                 ↓
┌─────────────────────┐      ┌──────────────────────┐
│ # Line 476-482      │      │ # Line 485-496       │
│ result = await      │      │ channel_str =        │
│   driver.execute_   │      │   str(channel) or '1'│
│   command({         │      │ if channel_str not    │
│     'SetVolt':      │      │    in ['1', '2']:     │
│     voltage,        │      │   return error        │
│     'SetCurr':      │      │ result = await       │
│     current         │      │   driver.execute_     │
│   })                │      │   command({           │
│                     │      │     'Channel':        │
│ # Returns '1' on    │      │       channel_str,    │
│ # success, error    │      │     'SetVolt':        │
│ # message on fail   │      │       voltage,         │
└─────────────────────┘      │       'SetCurr':       │
                             │       current          │
                             │   })                  │
                             └──────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 437-448: Process result                              │
│ if result_msg == '1':                                       │
│     return self.create_result(                              │
│         result="PASS",                                      │
│         measured_value=Decimal("1.0")                       │
│     )                                                       │
│ else:                                                       │
│     return self.create_result(                              │
│         result="FAIL",                                      │
│         measured_value=Decimal("0.0"),                      │
│         error_message=result_msg                            │
│     )                                                       │
└─────────────────────────────────────────────────────────────┘
```

### MODEL2306 Special Behavior

```python
# MODEL2306: If SetVolt=0 AND SetCurr=0, turn OFF output
# Line 490-496 in implementations.py

if voltage_val == 0 and current_val == 0:
    # Special case: turn off output
    result = await driver.execute_command({
        'Channel': channel_str,
        'SetVolt': 0,
        'SetCurr': 0,
        'Output': 'OFF'
    })
else:
    # Normal operation: set values and enable output
    result = await driver.execute_command({
        'Channel': channel_str,
        'SetVolt': voltage_val,
        'SetCurr': current_val
    })
```

## 3. CommandTest Measurement Flow

### Complete Call Chain

```
┌─────────────────────────────────────────────────────────────┐
│ CommandTestMeasurement.execute() [Line 68]                  │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 71-79: Get parameters                                │
│ command = get_param(test_params, "command")                 │
│ timeout = get_param(test_params, "timeout", default=5000)   │
│ wait_msec = get_param(test_params, "wait_msec",            │
│                   "WaitmSec")                               │
│                                                             │
│ if not command:                                             │
│     return ERROR("Missing command parameter")               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 84-85: Wait if specified                             │
│ if wait_msec:                                               │
│     await asyncio.sleep(wait_msec / 1000.0)                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 89-100: Execute command                              │
│ timeout_seconds = timeout / 1000.0                          │
│ process = await asyncio.create_subprocess_shell(            │
│     command,                                                 │
│     stdout=asyncio.subprocess.PIPE,                         │
│     stderr=asyncio.subprocess.PIPE,                         │
│     cwd="/app"                                               │
│ )                                                           │
│                                                             │
│ try:                                                        │
│     stdout, stderr = await asyncio.wait_for(               │
│         process.communicate(),                              │
│         timeout=timeout_seconds                             │
│     )                                                       │
│ except asyncio.TimeoutError:                                │
│     process.kill()                                          │
│     return ERROR("Command timeout")                         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 109-114: Check execution result                      │
│ output = stdout.decode().strip()                            │
│ error_output = stderr.decode().strip()                      │
│                                                             │
│ if process.returncode != 0:                                 │
│     return ERROR(                                           │
│         f"Command failed with exit code {process.returncode}"│
│     )                                                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 117-124: Convert output based on value_type          │
│ measured_value = output                                     │
│ if self.value_type is not StringType:                       │
│     try:                                                    │
│         measured_value = Decimal(output) if output else None│
│     except (ValueError, TypeError):                         │
│         measured_value = None                               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Line 129-134: Validate and return result                  │
│ is_valid, error_msg = self.validate_result(measured_value)  │
│ return self.create_result(                                  │
│     result="PASS" if is_valid else "FAIL",                  │
│     measured_value=measured_value,                          │
│     error_message=error_msg if not is_valid else None       │
│ )                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Console Command Example

```python
# Input parameters
test_params = {
    "command": "echo 'Hello World'",
    "timeout": 5000,
    "value_type": "string"
}

# Execution flow
1. command = "echo 'Hello World'"
2. timeout = 5000 ms
3. No wait_msec specified
4. asyncio.create_subprocess_shell("echo 'Hello World'")
   → process created
5. await process.communicate(timeout=5.0)
   → stdout=b"Hello World", stderr=b""
6. returncode = 0 (success)
7. output = "Hello World"
8. value_type = "string" → measured_value = "Hello World"
9. validate_result("Hello World", limit_type="none")
   → Returns (True, None)
10. create_result(result="PASS", measured_value="Hello World")
```

## 4. Validation Flow

### BaseMeasurement.validate_result()

```
┌─────────────────────────────────────────────────────────────┐
│ validate_result(measured_value, lower_limit, upper_limit,    │
│                limit_type='both', value_type='float')        │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Handle None measured_value                                │
│ if measured_value is None:                                  │
│     if limit_type == 'none':                                │
│         return (True, None)                                 │
│     else:                                                   │
│         return (False, "No measured value")                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Type conversion based on value_type                       │
│ if value_type == 'string':                                  │
│     value = str(measured_value)                              │
│ elif value_type == 'integer':                               │
│     value = int(measured_value)                              │
│ else:  # float                                              │
│     value = float(measured_value)                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
         ┌─────────────┴───────────────────┐
         │                                 │
    [limit_type decisions]         [value_type checks]
         │                                 │
         ↓                                 ↓
┌─────────────────────────────────────────────────────────────┐
│ # Limit type validation                                     │
│ if limit_type == 'lower':                                   │
│     valid = value >= lower_limit                             │
│ elif limit_type == 'upper':                                 │
│     valid = value <= upper_limit                             │
│ elif limit_type == 'both':                                  │
│     valid = lower_limit <= value <= upper_limit             │
│ elif limit_type == 'equality':                              │
│     valid = str(value) == str(self.eq_limit)                │
│ elif limit_type == 'inequality':                            │
│     valid = str(value) != str(self.eq_limit)                │
│ elif limit_type == 'partial':                               │
│     valid = str(self.eq_limit) in str(value)                │
│ else:  # none                                               │
│     valid = True                                             │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ # Generate error message if invalid                         │
│ if not valid and not error_msg:                             │
│     if limit_type == 'both':                                │
│         error_msg = f"Value {value} outside range"          │
│     elif limit_type == 'lower':                             │
│         error_msg = f"Value {value} < lower limit"          │
│     # ... other cases                                       │
│                                                             │
│ return (valid, error_msg)                                   │
└─────────────────────────────────────────────────────────────┘
```

### Validation Example

```python
# Test case: Voltage measurement
measured_value = Decimal("5.05")
lower_limit = Decimal("4.8")
upper_limit = Decimal("5.2")
limit_type = "both"
value_type = "float"

# Validation flow
1. measured_value is not None → continue
2. value_type = 'float' → value = 5.05
3. limit_type = 'both' → valid = (4.8 <= 5.05 <= 5.2) → True
4. return (True, None)

# Result: PASS
```

## 5. Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Exception occurs during execute()                           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ try-except in execute() method                             │
│ except Exception as e:                                      │
│     self.logger.error(f"{measurement_type} error: {e}")     │
│     return self.create_result(                              │
│         result="ERROR",                                     │
│         error_message=str(e)                                │
│     )                                                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Error propagation                                           │
│ ├── MeasurementService receives ERROR result                │
│ ├── runAllTest mode: Continue execution, collect error      │
│ └── Normal mode: Stop execution immediately                 │
└─────────────────────────────────────────────────────────────┘
```

## Summary

Key callback patterns in WebPDTool:

1. **Lazy Imports**: Drivers imported only when needed (line ~170 in implementations.py)
2. **Context Managers**: Connections managed via async with statements
3. **Initialization Cache**: driver._initialized flag prevents re-initialization
4. **Result Standardization**: All paths return MeasurementResult via create_result()
5. **Error Propagation**: Exceptions caught and converted to ERROR results

---

**Related Documents**:
- [Architecture_Callback_Dependencies.md](Architecture_Callback_Dependencies.md) - High-level dependency analysis
- [Power_Set_Read_Measurement.md](Power_Set_Read_Measurement.md) - Power measurement details
