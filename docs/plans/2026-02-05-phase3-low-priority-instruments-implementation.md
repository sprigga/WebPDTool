# Phase 3 Low Priority Instruments Implementation

**Document Version**: 1.0
**Date**: 2026-02-05
**Status**: ✅ Complete

## Overview

This document details the implementation of Phase 3 Low Priority instrument drivers from PDTool4's lowsheen_lib. These drivers complete the 100% instrument migration goal.

## Implemented Drivers

### 1. L6MPU SSH Driver (`l6mpu_ssh.py`)
- **Purpose**: SSH-based control for i.MX8MP embedded systems
- **Key Features**:
  - LTE module SIM card testing via microcom
  - PLC network connectivity (eth0/eth1) ping tests
  - General Linux command execution
  - Operator confirmation support
- **Connection**: SSH (paramiko)
- **File**: `backend/app/services/instruments/l6mpu_ssh.py`

### 2. L6MPU SSH+Serial Driver (`l6mpu_ssh_comport.py`)
- **Purpose**: Hybrid SSH and serial port communication
- **Key Features**:
  - AT command testing with local serial port
  - Remote SSH control for command execution
  - Supports `at_cmd_task` on remote device
- **Connection**: SSH + Serial (paramiko + pyserial)
- **File**: `backend/app/services/instruments/l6mpu_ssh_comport.py`

### 3. L6MPU Position SSH Driver (`l6mpu_pos_ssh.py`)
- **Purpose**: MPU position control for robot/AMR applications
- **Key Features**:
  - Position setting (x, y, angle, speed)
  - Position query
  - Calibration to origin
- **Connection**: SSH (paramiko)
- **File**: `backend/app/services/instruments/l6mpu_pos_ssh.py`

### 4. PEAK CAN Driver (`peak_can.py`)
- **Purpose**: CAN bus communication for PEAK-System PCAN hardware
- **Key Features**:
  - Standard CAN (11-bit) and Extended CAN (29-bit)
  - CAN-FD support (up to 64 bytes)
  - Message filtering
  - Configurable baud rates
- **Connection**: python-can library
- **File**: `backend/app/services/instruments/peak_can.py`

### 5. SMCV100B Driver (`smcv100b.py`)
- **Purpose**: Rohde & Schwarz SMCV100B vector signal generator
- **Key Features**:
  - DAB/TDMB modulation with transport stream playback
  - AM/FM radio generation
  - IQ baseband modulation
  - RF output control
- **Connection**: RsSmcv SDK or PyVISA fallback
- **File**: `backend/app/services/instruments/smcv100b.py`

## Measurement Implementations

### L6MPU LTE Check Measurement
- **Registry Key**: `L6MPU_LTE_CHECK`
- **Purpose**: Verify LTE module SIM card status
- **Returns**: PASS if SIM ready, FAIL otherwise

### L6MPU PLC Test Measurement
- **Registry Key**: `L6MPU_PLC_TEST`
- **Purpose**: Test PLC network connectivity via ping
- **Returns**: PASS if ping successful, FAIL on 100% packet loss

### SMCV100B RF Output Measurement
- **Registry Key**: `SMCV100B_RF`
- **Purpose**: Configure RF signal generation
- **Supports**: DAB, AM, FM, IQ, RF modes

### PEAK CAN Message Measurement
- **Registry Key**: `PEAK_CAN`
- **Purpose**: CAN message communication
- **Operations**: write, read, write_read

## Registry Updates

### Driver Registry (`__init__.py`)
```python
INSTRUMENT_DRIVERS = {
    # ... existing drivers ...
    "L6MPU_SSH": L6MPUSSHDriver,
    "L6MPU": L6MPUSSHDriver,
    "L6MPU_SSH_COMPORT": L6MPUSSHComPortDriver,
    "L6MPU_POS_SSH": L6MPUPOSSHDriver,
    "PEAK_CAN": PEAKCANDriver,
    "PCAN": PEAKCANDriver,
    "SMCV100B": SMCV100BDriver,
}
```

### Measurement Registry (`implementations.py`)
```python
MEASUREMENT_REGISTRY = {
    # ... existing measurements ...
    "L6MPU_LTE_CHECK": L6MPU_LTE_Check_Measurement,
    "L6MPU_PLC_TEST": L6MPU_PLC_Test_Measurement,
    "SMCV100B_RF": SMCV100B_RF_Output_Measurement,
    "PEAK_CAN": PEAK_CAN_Message_Measurement,
}
```

## Dependencies

### Required Packages
```txt
# Existing
paramiko>=2.12.0       # SSH for L6MPU drivers
pyserial>=3.5          # Serial for L6MPU+Serial

# New (optional - install as needed)
python-can>=4.0.0      # PEAK CAN driver
RsSmcv>=1.50.0         # SMCV100B (proprietary, optional)
```

### Installation
```bash
# For L6MPU drivers
uv pip install paramiko pyserial

# For PEAK CAN
uv pip install python-can

# For SMCV100B (if using RsSmcv SDK)
uv pip install RsSmcv
```

## Unit Tests

### Test Files
- `tests/test_instruments/test_l6mpu.py` - L6MPU driver tests
- `tests/test_instruments/test_peak_and_smcv.py` - PEAK CAN and SMCV100B tests

### Running Tests
```bash
cd backend
pytest tests/test_instruments/test_l6mpu.py -v
pytest tests/test_instruments/test_peak_and_smcv.py -v
```

## Usage Examples

### L6MPU SSH LTE Check
```python
# In test plan CSV:
# test_type: L6MPU_LTE_CHECK
# extra_params: {"instrument": "L6MPU_1", "timeout": 5.0}
```

### L6MPU PLC Test
```python
# In test plan CSV:
# test_type: L6MPU_PLC_TEST
# extra_params: {"instrument": "L6MPU_1", "interface": "eth0", "count": 4}
```

### PEAK CAN Communication
```python
# In test plan CSV:
# test_type: PEAK_CAN
# extra_params: {"instrument": "PEAK_CAN_1", "operation": "write", "can_id": "0x100", "data": "01,02,03,04"}
```

### SMCV100B Signal Generation
```python
# In test plan CSV:
# test_type: SMCV100B_RF
# extra_params: {"instrument": "SMCV100B_1", "mode": "FM", "frequency": 98.5, "power": -15}
```

## Architecture Notes

### Async Design
All drivers use async/await pattern for non-blocking operations:
- SSH commands run in thread pool via `run_in_executor`
- Serial operations run in thread pool
- CAN operations use python-can's synchronous interface in thread pool

### Error Handling
Consistent error handling across all drivers:
- Connection errors raise `ConnectionError`
- Command execution errors return status dict with 'ERROR' status
- Timeout handling for all long-running operations

### Simulation Mode
Drivers support simulation via mock connections:
- Use `sim://` prefix in address for simulator mode
- Implement mock responses for testing without hardware

## Completion Status

| Driver | Status | Tests | Documentation |
|--------|--------|-------|---------------|
| L6MPU SSH | ✅ Complete | ✅ Added | ✅ Complete |
| L6MPU SSH+Serial | ✅ Complete | ✅ Added | ✅ Complete |
| L6MPU Position | ✅ Complete | ✅ Added | ✅ Complete |
| PEAK CAN | ✅ Complete | ✅ Added | ✅ Complete |
| SMCV100B | ✅ Complete | ✅ Added | ✅ Complete |

## Final Statistics

- **Total Instruments**: 26
- **Completion**: 100% (26/26)
- **Total Lines of Code**: ~8,000+ lines across all drivers
- **Test Coverage**: Unit tests for all new drivers

## Migration Complete! 🎉

With the completion of Phase 3 Low Priority instruments, all PDTool4 instrument drivers have been successfully migrated to WebPDTool with:
- Modern async/await architecture
- Unified BaseInstrument interface
- Comprehensive error handling
- Full measurement integration
- Unit test coverage

---

**Document History**:
- v1.0 (2026-02-05): Initial version - Phase 3 Low Priority implementation complete
