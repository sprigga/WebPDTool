# PDTool4 Modbus Communication

## Overview

The Modbus communication system in PDTool4 enables integration with PLCs and other industrial automation equipment. It uses Modbus TCP/IP protocol for real-time communication with external systems.

## ModbusListener.py

The main module for handling Modbus communication, built on the pyModbusTCP library.

### Key Classes

#### ModbusListener (QThread)
- Inherits from QThread for background operation
- Handles continuous Modbus communication without blocking the UI
- Manages connection to Modbus server

### Key Functions

#### run()
- Main execution loop that continuously monitors Modbus registers
- Handles connection management and error recovery
- Implements configurable delay between polling cycles

#### read_registers()
- Reads status registers to check if the system is ready for testing
- Uses configurable address and length parameters

#### read_sn()
- Reads serial number from Modbus registers
- Initiates the testing process when a serial number is detected
- Updates test status registers to indicate testing in progress

#### write_pf_registers() and sent_pf_result()
- Reports test results (PASS/FAIL) back to the Modbus system
- Updates result registers with appropriate status values

#### write_test_status()
- Updates the test status register during the testing process
- Indicates when testing is in progress or finished

### Configuration Parameters

Modbus settings are defined in the `[ModbusConfig]` section of `test_xml.ini`:

- `server_host`: IP address of the Modbus server
- `server_port`: TCP port for Modbus communication (typically 502)
- `device_id`: Modbus device/unit ID
- `r_ready_status_address`: Address of the ready status register
- `r_readsn_address`: Address of the serial number register
- `w_test_status_address`: Address of the test status register
- `w_test_result_address`: Address of the test result register
- `w_test_pass_value`: Value to write for a PASS result
- `w_test_fail_value`: Value to write for a FAIL result
- `enabled`: Flag to enable/disable Modbus functionality
- `lp_switch`: Switch to use laser printer addresses instead of standard ones

### Communication Flow

1. **Initialization**: Modbus listener connects to the configured server
2. **Status Monitoring**: Continuously reads the ready status register
3. **SN Detection**: When ready status is detected, reads the serial number
4. **Test Initiation**: Updates test status to indicate testing has started
5. **Result Reporting**: Updates result registers with PASS/FAIL status
6. **Status Update**: Updates test status to indicate testing completion

### Laser Printer Support

The system includes special support for laser printer systems with alternate register addresses controlled by the `lp_switch` parameter.

### Error Handling

- Connection error detection and logging
- Automatic retry mechanisms
- Detailed logging of all Modbus operations
- Simulation mode for testing without hardware

### Simulation Mode

When `simulation_mode` is enabled, the system can operate without actual hardware for testing purposes.