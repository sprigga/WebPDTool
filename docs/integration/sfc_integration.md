# PDTool4 SFC Integration

## Overview

The Shop Floor Control (SFC) integration in PDTool4 enables connection to production tracking and control systems. It supports both web service and URL-based communication methods for different SFC implementations.

## SFCWebService.py

This module provides the interface to external SFC systems through a DLL library:

### Key Functions

- **GetConfigValue()**: Reads configuration parameters from SFC settings
- **webServiceSFC()**: Primary function for SFC communication with two steps:
  - STEP01: Initial device verification and setup
  - STEP02: Test result reporting

### Configuration Settings

The SFC configuration is managed through `EVApi.xml` and `test_xml.ini`:
- **API URL**: Web service endpoint for SFC communication
- **Database**: Target database name for the production line
- **Line Name**: Production line identifier
- **TI Type**: Test data type (typically "IMEI" or "TEST")

## SFCFunctions.py

Provides helper functions for SFC operations:
- **sfc_Web_step3_txt()**: Handles STEP03.4 communication via web service
- **sfc_url_step3_txt()**: Handles STEP03.4 communication via URL
- Manages pass/fail result reporting to SFC systems

## SFC Integration Process

The SFC integration follows a 3-step process:

### Step 1: Device Verification
- Validates device serial number against SFC records
- Confirms device presence in production system
- Retrieves work order information

### Step 2: Test Result Preparation
- Collects test results during the testing process
- Prepares data for SFC reporting
- Maintains correlation between physical device and work order

### Step 3.4: Final Result Reporting
- Reports final test result (PASS/FAIL) to SFC system
- Updates production database with test results
- Closes the work order cycle

## Configuration Parameters

The SFC behavior is controlled by parameters in `test_xml.ini`:
- `sfc_control`: ON/OFF switch for SFC integration
- `titype`: Test data type (IMEI or TEST)
- Various database and connection parameters

## SFC GONOGO Measurement

The `SFC_GONOGOMeasurement.py` module implements the actual SFC communication within the test sequence:
- Called based on ExecuteName='SFCtest' in the test plan
- Handles both WebService and URL communication methods
- Manages the STEP01/STEP02 sequence during testing
- Reports final results in STEP03.4

## Error Handling

The SFC integration includes comprehensive error handling:
- Retry mechanisms for communication failures
- Fallback behavior when SFC is unavailable
- Detailed error logging for troubleshooting
- Graceful degradation when SFC is disabled