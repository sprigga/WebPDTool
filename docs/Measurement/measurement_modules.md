# PDTool4 Measurement Modules

## Overview

The PDTool4 system uses a modular approach for different types of measurements and test operations. Each measurement module implements the `Measurement` base class and provides specific functionality for different test types.

## CommandTestMeasurement.py

Handles various command-based tests including console commands, serial port communication, and TCP/IP communication.

### Key Features
- **Console Commands**: Execute system commands and parse output
- **Serial Port Communication**: Connect to devices via COM ports with configurable baud rates
- **TCP/IP Communication**: Network-based device communication
- **PEAK API Integration**: Specialized communication for PEAK interfaces

### Supported Switch Types
- `comport`: Serial port communication with configurable parameters
- `console`: System console command execution
- `tcpip`: Network-based communication
- `PEAK`: PEAK CAN interface API

### Parameter Handling
- **Port**: Serial port specification (e.g., COM3)
- **Baud**: Baud rate for serial communication
- **Command**: The actual command to execute
- **keyWord**: Keyword for parsing specific results
- **spiltCount** and **splitLength**: For extracting specific substrings
- **EqLimit**: For finding specific lines containing certain terms

## PowerSetMeasurement.py and PowerReadMeasurement.py

These modules handle power supply control and measurement functions:
- PowerSetMeasurement: Set voltage, current, and power parameters
- PowerReadMeasurement: Read actual power measurements from instruments

## SFC_GONOGOMeasurement.py

Handles integration with Shop Floor Control systems:
- Web service integration (STEP01, STEP02, STEP03_4)
- URL-based communication methods
- Pass/fail result reporting to SFC systems

## Other Measurement Modules

### getSNMeasurement.py
- Extracts serial numbers from various sources
- Validates and processes device serial numbers

### OPjudgeMeasurement.py
- Handles operator judgment steps in the test process
- Provides manual test override capabilities

### OtherMeasurement.py
- Implements various other specialized test types
- Provides flexible framework for custom test implementations

## Measurement Execution Flow

1. **Test Plan Reading**: CSV test plan is parsed to determine test sequence
2. **Module Selection**: Appropriate measurement module is selected based on ExecuteName
3. **Parameter Passing**: Parameters from CSV are passed to the measurement module
4. **Execution**: Measurement module executes the specific test type
5. **Result Processing**: Results are validated against limits and stored
6. **Reporting**: Results are added to the test report