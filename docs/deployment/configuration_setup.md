# PDTool4 Configuration and Setup

## Overview

PDTool4 uses multiple configuration files to manage application settings, test parameters, and integration options. The configuration system is designed to be flexible and support different test setups and production environments.

## test_xml.ini

This is the primary configuration file that controls most aspects of the application.

### [testspec] Section
- `limits_atlas`: Path to the CSV test plan file
- `projectcode`: Code identifying the current project
- `station`: Station identifier for the current test setup

### [checkSN] Section
- Defines regular expressions for validating serial number formats
- Each entry named after the station (e.g., `f503_l6mpu_clearemmc`, `map_mpubft1`)
- Uses regex patterns to validate serial number formats for different product types

### [testMode] Section
- `test_mode`: 0 for operator mode, 1 for engineer mode
- `rd_password`: Engineer password for advanced functions
- `op_id`: Operator ID (currently unused)

### [SfcConfig] Section
- `path`: Path for SFC log data
- `stationid`: Station identifier for SFC system
- `linename`: Production line name for SFC
- `fixtureid`: Fixture identifier
- `logpath`: Path for main log files
- `backuplogpath`: Path for backup log files
- `titype`: Test data type (IMEI or TEST)
- `database`: SFC database name
- `sfc_control`: ON/OFF switch for SFC integration

### [loopTest] Section
- `loop_control`: True/False to enable loop testing
- `loop_count`: Number of times to repeat the test sequence

### [Setting] Section
- Defines instrument addresses and connection parameters
- Includes settings for various types of test equipment:
  - GPIB instruments
  - TCP/IP connected instruments
  - Serial port devices
  - Power supplies
  - Oscilloscopes
  - Data acquisition systems

### [ModbusConfig] Section
- Server connection settings
- Register addresses for different functions
- Test status and result values
- Simulation and delay parameters

## EVApi.xml

SFC configuration file that stores connection parameters for the SFC web service:
- Database connection information
- Group name (station ID)
- Line name for production tracking

## Logging Configuration

The application uses a custom logger implementation:
- Rotating file logger in `logger.py`
- Configurable log levels (NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL)
- Automatic log rotation at 10MB with 5 backup files

## Test Plan Files

CSV files located in the `testPlan/` directory that define test sequences:
- Each row represents a test item
- Columns define test parameters (ID, ExecuteName, limits, etc.)
- The format is processed by `polish.mfg_config_readers.limits_table_reader`

## Dependencies

The application requires specific Python packages listed in `requirement.txt`:
- PySide2 for GUI
- pyModbusTCP for Modbus communication
- Various instrument control libraries
- Standard Python packages for configuration, logging, and subprocess management

## Build and Deployment

The application includes batch files for building with Nuitka:
- `Nuitka_2Set.bat`: Build configuration script
- `Nuitka_PDSet.bat`: Main build script
- Creates executable files for distribution

## Test Execution Flow

1. Application reads configuration from `test_xml.ini`
2. Loads appropriate test plan based on configuration
3. Initializes instruments based on `[Setting]` section
4. Starts Modbus listener if enabled
5. Waits for serial number input (manual or via Modbus)
6. Executes test sequence as defined in CSV test plan
7. Reports results to SFC if enabled
8. Logs results to appropriate directories
9. Resets instruments after test completion