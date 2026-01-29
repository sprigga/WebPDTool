# PDTool4 Architecture and Workflow

## System Architecture

PDTool4 follows a modular architecture with clear separation of concerns:

### Presentation Layer
- **GUI Interface**: PySide2-based with login and measurement screens
- **User Interaction Management**: Handles user input, authentication, and workflow control

### Business Logic Layer
- **Test Execution Engine**: Orchestrates the testing process
- **Configuration Management**: Handles app settings and test parameters
- **Communication Layer**: Manages Modbus and SFC integrations

### Data Layer
- **CSV Test Plans**: Defines test sequences and parameters
- **Logging System**: Comprehensive result and event logging
- **Configuration Files**: Persistent settings storage

## Application Flow

### Startup Sequence
1. **Initialization**: `PDtool.py` initializes the main application
2. **Login Screen**: Shows login window with project/station selection
3. **Configuration Loading**: Reads `test_xml.ini` and sets up parameters
4. **UI Setup**: Configures the measurement interface with test plan
5. **Modbus Start**: Starts Modbus listener if enabled in configuration

### Test Execution Workflow

#### 1. Authentication and Setup
- User selects project code and station
- System loads appropriate test plan CSV file
- Engineer mode allows full configuration access
- Operator mode restricts configuration changes

#### 2. Serial Number Entry
- Manual entry via barcode input field
- OR automatic entry via Modbus communication
- SN format validation against regex rules
- Ready status check via Modbus (if enabled)

#### 3. Test Plan Processing
- CSV file is parsed to extract test sequence
- Each row represents a test item with parameters
- System determines which measurement module to use
- Parameters are extracted and validated

#### 4. Test Execution Engine
- `oneCSV_atlas_2.py` orchestrates the entire process
- Iterates through test plan items
- Dynamically instantiates appropriate measurement modules
- Manages instrument initialization and cleanup

#### 5. Measurement Module Execution
- Each test item calls the appropriate measurement class
- Measurement modules execute specific test types:
  - CommandTestMeasurement: System commands and communications
  - PowerSet/PowerRead: Power supply control and measurement
  - SFC_GONOGOMeasurement: SFC system communication
  - Other specialized modules

#### 6. Result Processing
- Measurement results are validated against limits
- Pass/fail determination based on test parameters
- Results stored in test results dictionary
- Real-time update of GUI test table

#### 7. Integration Communication
- **SFC Communication**: If enabled, reports results to SFC system
- **Modbus Updates**: Test status and results sent to Modbus registers
- **Logging**: Results written to log files with appropriate naming

#### 8. Cleanup and Reset
- Instruments reset to default state
- File handles closed
- Temporary files cleaned up
- System prepared for next test cycle

## Module Dependencies

### Core Dependencies
- `polish` library: Main test framework
- `PySide2`: GUI implementation
- `pyModbusTCP`: Modbus communication

### Measurement Modules Dependencies
- `test_info`: Test information handling
- `SFCFunctions`: SFC integration
- `csv`: Test plan parsing
- `subprocess`: External command execution

## Error Handling Strategy

### Test Execution Errors
- Graceful handling of instrument communication failures
- Comprehensive logging of all errors
- Recovery mechanisms for various failure modes

### Communication Errors
- Retry mechanisms for Modbus connections
- SFC fallback options when unavailable
- Detailed error reporting to operators

### Configuration Errors
- Validation of configuration parameters
- Default values for missing settings
- Clear error messages for invalid configurations

## Integration Points

### Modbus TCP/IP
- Real-time communication with PLCs
- Automatic test initiation on device arrival
- Status updates during and after testing

### Shop Floor Control (SFC)
- Production tracking and work order management
- Quality data collection and reporting
- Step-by-step process control

### Instrument Control
- Support for various test equipment via GPIB, TCP/IP, and serial
- Dynamic instrument initialization based on test requirements
- Automatic reset after test completion

## Data Flow

1. **Input**: Serial number from user input or Modbus
2. **Processing**: Test plan execution with measurement modules
3. **Integration**: SFC and Modbus communication
4. **Output**: Pass/fail results to user interface
5. **Storage**: Logging to files with structured naming

## Performance Considerations

- Threading for non-blocking UI updates
- Efficient CSV parsing for test plans
- Connection pooling for instrument communication
- Asynchronous operations where appropriate