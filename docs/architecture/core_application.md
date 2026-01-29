# PDTool4 Core Application

## PDtool.py

This is the main application file that implements the GUI and core application logic. It uses PySide2 for the user interface and follows a multi-window approach with login and measurement windows.

### Key Classes

#### MainWindow_Login
- Handles user authentication with different user types (Engineer/Operator)
- Manages project code and station selection
- Provides password validation and test plan selection

#### MainWindow_Measure
- Main measurement interface with test table display
- Handles barcode input and test execution
- Manages Modbus communication if enabled
- Provides real-time status updates and test results

#### SFCMainWindow
- Configuration window for SFC settings
- Allows modification of SFC parameters and logging paths

#### testThread and testThread3
- Background threads for test execution and result monitoring
- Handles subprocess communication with test execution modules

### Functionality

- **User Management**: Supports different access levels with distinct permissions
- **Test Plan Selection**: Dynamically loads test plans based on project/station selection
- **Modbus Communication**: Supports Modbus TCP/IP integration with configurable parameters
- **Result Tracking**: Real-time display of test results with color-coded pass/fail indication
- **Logging**: Comprehensive logging with automatic file naming and backup

## Configuration

The application uses `test_xml.ini` for configuration, which contains multiple sections:
- `[testspec]`: Test specifications and limits
- `[checkSN]`: Serial number format validation rules
- `[testMode]`: Operation mode and password settings  
- `[SfcConfig]`: Shop Floor Control configuration
- `[loopTest]`: Loop testing parameters
- `[ModbusConfig]`: Modbus communication settings