# PDTool4 Application Documentation

## Overview

PDTool4 is a comprehensive production testing application built with PySide2 for testing power delivery devices. The application provides a GUI interface for operators to run various tests on devices under test (DUT) and integrates with Shop Floor Control (SFC) systems for production tracking and process control.

## Architecture

The application follows a modular architecture with different components handling specific functions:

- **GUI Layer**: PySide2-based user interface with login and measurement screens
- **Test Execution Engine**: Core testing logic that executes various test types based on CSV test plans
- **Communication Layer**: Modbus TCP/IP integration for connecting with external systems
- **SFC Integration**: Shop Floor Control integration via web services and URL interfaces
- **Reporting**: Detailed logging and reporting functionality

## Main Components

### Core Application Files
- `PDtool.py`: Main application entry point with GUI logic
- `login_stretch.py` / `measure_stretch.py`: UI definition files
- `oneCSV_atlas_2.py`: Main test execution engine
- `ModbusListener.py`: Modbus TCP/IP communication handler

### Test Measurement Modules
- `CommandTestMeasurement.py`: Handles console, serial port, and TCP/IP commands
- `PowerSetMeasurement.py`: Power supply control functions
- `PowerReadMeasurement.py`: Power measurement functions
- `SFC_GONOGOMeasurement.py`: SFC integration functions
- `getSNMeasurement.py`: Serial number handling
- `OPjudgeMeasurement.py`: Operator judgment functions

### Configuration and Settings
- `test_xml.ini`: Main configuration file
- `EVApi.xml`: SFC configuration file

## Features

1. **User Authentication**: Separate engineer and operator access levels
2. **Test Plan Management**: CSV-based test plan configuration
3. **Modbus Integration**: Real-time communication with external systems
4. **SFC Integration**: Shop Floor Control system integration
5. **Logging and Reporting**: Comprehensive test result logging
6. **Serial Number Validation**: Customizable SN format checking
7. **Loop Testing**: Ability to run tests multiple times