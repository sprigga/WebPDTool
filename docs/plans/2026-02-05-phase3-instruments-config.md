# Phase 3 RF Instruments - Configuration Examples

This document provides configuration examples for Phase 3 RF instruments (CMW100 and RF_Tool/MT8872A) in WebPDTool.

## Overview

Phase 3 RF instruments include:
- **CMW100** (Rohde & Schwarz): Compact wireless communications tester for BLE and WiFi
- **MT8872A** (Anritsu): Universal wireless test set with LTE and cellular capabilities (RF_Tool in code)

## Configuration File Location

Instrument configurations are stored in `backend/app/core/instrument_config.py` and loaded from the database via `InstrumentConfig` model.

## CMW100 Configuration Example

### Basic Configuration

```yaml
# Example: config/instruments/cmw100.yaml
instruments:
  - id: CMW100_1
    type: CMW100
    name: "Rohde & Schwarz CMW100"
    connection:
      type: TCPIP
      address: "192.168.1.100"
      port: 5025
    settings:
      visa_resource: "TCPIP0::192.168.1.100::inst0::INSTR"
      timeout: 10000
      retry_count: 3
      simulation_mode: false  # Set to true for testing without hardware
```

### Python Configuration

```python
from app.core.instrument_config import InstrumentConfig, TCPIPAddress

cmw100_config = InstrumentConfig(
    id="CMW100_1",
    type="CMW100",
    name="Rohde & Schwarz CMW100",
    connection=TCPIPAddress(
        address="192.168.1.100",
        port=5025
    ),
    settings={
        "visa_resource": "TCPIP0::192.168.1.100::inst0::INSTR",
        "timeout": 10000,
        "retry_count": 3,
        "simulation_mode": False
    }
)
```

### Test Plan Usage (BLE Measurement)

```csv
項次,品名規格,TestType,下限值,上限值,limit_type,value_type,單位,TestParams
1,BLE TX Power,CMW100_BLE,-10.0,0.0,both,float,dBm,"instrument=CMW100_1;connector=1;frequency=2440.0;expected_power=-5.0"
2,BLE Frequency Deviation,CMW100_BLE,-50.0,50.0,both,float,kHz,"instrument=CMW100_1;connector=1;frequency=2402.0"
3,BLE LE Coded PHY,CMW100_BLE,-20.0,10.0,both,float,dBm,"instrument=CMW100_1;connector=2;frequency=2480.0"
```

### Test Plan Usage (WiFi Measurement)

```csv
項次,品名規格,TestType,下限值,上限值,limit_type,value_type,單位,TestParams
1,WiFi TX Power 11ac,CMW100_WiFi,10.0,20.0,both,float,dBm,"instrument=CMW100_1;connector=1;standard=11ac;channel=36;bandwidth=20"
2,WiFi TX Power 11ax,CMW100_WiFi,10.0,20.0,both,float,dBm,"instrument=CMW100_1;connector=1;standard=11ax;channel=40;bandwidth=40"
3,WiFi EVM,CMW100_WiFi,-35.0,0.0,lower,float,dB,"instrument=CMW100_1;connector=1;standard=11n;channel=6"
```

## MT8872A (RF_Tool) Configuration Example

### Basic Configuration

```yaml
# Example: config/instruments/mt8872a.yaml
instruments:
  - id: RF_Tool_1
    type: MT8872A
    name: "Anritsu MT8872A Universal Wireless Test Set"
    connection:
      type: TCPIP
      address: "192.168.1.101"
      port: 5025
    settings:
      visa_resource: "TCPIP0::192.168.1.101::inst0::INSTR"
      timeout: 30000  # Longer timeout for LTE measurements
      retry_count: 3
      simulation_mode: false
```

### Python Configuration

```python
from app.core.instrument_config import InstrumentConfig, TCPIPAddress

mt8872a_config = InstrumentConfig(
    id="RF_Tool_1",
    type="MT8872A",
    name="Anritsu MT8872A",
    connection=TCPIPAddress(
        address="192.168.1.101",
        port=5025
    ),
    settings={
        "visa_resource": "TCPIP0::192.168.1.101::inst0::INSTR",
        "timeout": 30000,
        "retry_count": 3,
        "simulation_mode": False
    }
)
```

### Test Plan Usage (LTE TX Measurement)

```csv
項次,品名規格,TestType,下限值,上限值,limit_type,value_type,單位,TestParams
1,LTE TX Power B1,RF_Tool_LTE_TX,20.0,25.0,both,float,dBm,"instrument=RF_Tool_1;band=B1;channel=100;bandwidth=10.0"
2,LTE TX Power B3,RF_Tool_LTE_TX,20.0,25.0,both,float,dBm,"instrument=RF_Tool_1;band=B3;channel=200;bandwidth=20.0"
3,LTE ACLR Lower,RF_Tool_LTE_TX,-100.0,-40.0,both,float,dBc,"instrument=RF_Tool_1;band=B41;channel=500;bandwidth=10.0"
```

### Test Plan Usage (LTE RX Sensitivity)

```csv
項次,品名規格,TestType,下限值,上限值,limit_type,value_type,單位,TestParams
1,LTE RX Sensitivity B1,RF_Tool_LTE_RX,-95.0,-80.0,both,float,dBm,"instrument=RF_Tool_1;band=B1;channel=100;test_power=-90.0;min_throughput=10.0"
2,LTE RX Sensitivity B3,RF_Tool_LTE_RX,-95.0,-80.0,both,float,dBm,"instrument=RF_Tool_1;band=B3;channel=200;test_power=-85.0;min_throughput=10.0"
3,LTE RX Sensitivity B41,RF_Tool_LTE_RX,-95.0,-80.0,both,float,dBm,"instrument=RF_Tool_1;band=B41;channel=500;test_power=-95.0;min_throughput=1.0"
```

## Supported LTE Bands (MT8872A)

The RF_Tool driver supports the following LTE bands:

| Band | Frequency (MHz) | Channel Range |
|------|-----------------|---------------|
| B1   | 2140.0          | 0-599        |
| B3   | 1805.0          | 1200-1949    |
| B7   | 2655.0          | 5000-5499    |
| B38  | 2570.0          | 37750-38249  |
| B41  | 2496.0          | 51260-53729  |

## Connection Settings Reference

### TCPIP Connection Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| address   | IP address of instrument | - | "192.168.1.100" |
| port      | Port number (usually 5025 for SCPI) | 5025 | 5025 |
| timeout   | Connection timeout in ms | 10000 | 30000 |
| retry_count | Number of connection retries | 3 | 3 |

### Instrument-Specific Settings

| Instrument | Recommended Timeout | Notes |
|------------|-------------------|-------|
| CMW100     | 10000 ms          | Faster measurements |
| MT8872A    | 30000 ms          | LTE measurements take longer |

## Simulation Mode

For testing without hardware, enable simulation mode:

```python
# In instrument_config.py or database
config = InstrumentConfig(
    id="CMW100_1_SIM",
    type="CMW100",
    name="CMW100 Simulation",
    connection=TCPIPAddress(address="127.0.0.1", port=5025),
    settings={"simulation_mode": True}
)
```

When simulation_mode is True:
- The instrument driver returns simulated results
- No actual hardware connection is attempted
- Useful for test plan validation and development

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Increase timeout value in configuration
   - Check network connectivity to instrument
   - Verify instrument is powered on

2. **Invalid Band/Channel**
   - Ensure LTE band and channel are compatible
   - Refer to supported bands table above

3. **Measurement Timeout**
   - LTE measurements take longer than other instruments
   - Use timeout >= 30000ms for MT8872A LTE tests

4. **Port Already in Use**
   - Ensure no other application is using the instrument
   - Check VISA resource manager for conflicting connections

## Example Complete Configuration

```python
# backend/app/core/instrument_config.py

from app.core.instrument_config import InstrumentConfig, TCPIPAddress

# Production configurations
INSTRUMENT_CONFIGS = [
    # CMW100 for BLE/WiFi testing
    InstrumentConfig(
        id="CMW100_1",
        type="CMW100",
        name="Rohde & Schwarz CMW100",
        connection=TCPIPAddress(address="192.168.1.100", port=5025),
        settings={
            "visa_resource": "TCPIP0::192.168.1.100::inst0::INSTR",
            "timeout": 10000,
            "retry_count": 3,
            "simulation_mode": False
        }
    ),
    # MT8872A for LTE testing
    InstrumentConfig(
        id="RF_Tool_1",
        type="MT8872A",
        name="Anritsu MT8872A",
        connection=TCPIPAddress(address="192.168.1.101", port=5025),
        settings={
            "visa_resource": "TCPIP0::192.168.1.101::inst0::INSTR",
            "timeout": 30000,
            "retry_count": 3,
            "simulation_mode": False
        }
    )
]
```

## Database Configuration (Alternative)

Instruments can also be configured via the database:

```sql
INSERT INTO instrument_configs (id, type, name, connection_type, connection_address, settings)
VALUES
('CMW100_1', 'CMW100', 'Rohde & Schwarz CMW100', 'TCPIP', '192.168.1.100:5025',
 '{"visa_resource": "TCPIP0::192.168.1.100::inst0::INSTR", "timeout": 10000, "simulation_mode": false}'),
('RF_Tool_1', 'MT8872A', 'Anritsu MT8872A', 'TCPIP', '192.168.1.101:5025',
 '{"visa_resource": "TCPIP0::192.168.1.101::inst0::INSTR", "timeout": 30000, "simulation_mode": false}');
```

## Next Steps

1. Add instrument configurations to your test environment
2. Import test plans with CMW100 and RF_Tool measurement types
3. Run test sessions to verify measurements work correctly
4. Update measurement implementations to use real drivers (currently placeholder)
