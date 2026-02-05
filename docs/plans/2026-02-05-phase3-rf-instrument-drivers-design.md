# Phase 3 RF Instrument Drivers Design

**Date**: 2026-02-05
**Author**: Claude Code
**Status**: Approved

---

## Overview

Complete implementation of Phase 3 RF instrument drivers for CMW100 and MT8872A to replace stub implementations in WebPDTool.

---

## Architecture

### Two Separate Drivers

| Driver | Instrument | Library | Measurements |
|--------|-----------|---------|--------------|
| `CMW100Driver` | Rohde & Schwarz CMW100 | RsInstrument | BLE TX, WiFi TX/EVM |
| `MT8872ADriver` | Anritsu MT8872A | PyVISA/SCPI | LTE TX, LTE RX |

### Design Principles

- Inherit from `BaseInstrumentDriver`
- Include simulation mode for development
- Follow async/await patterns
- Standardized error handling
- Realistic mock values for simulation

---

## Class Structure

### CMW100Driver

```python
class CMW100Driver(BaseInstrumentDriver):
    # Connection
    async def initialize() -> None
    async def reset() -> None

    # Bluetooth LE
    async def measure_ble_tx_power(connector, frequency, expected_power) -> Dict
    async def configure_ble_measurement(connector, frequency, burst_type) -> None

    # WiFi
    async def measure_wifi_tx_power(connector, standard, channel, bandwidth) -> Dict
    async def configure_wifi_measurement(connector, standard, frequency, bandwidth) -> None

    # Helpers
    async def _init_rs_instrument() -> None
    async def _simulate_ble_measurement() -> Dict
    async def _simulate_wifi_measurement() -> Dict
```

### MT8872ADriver

```python
class MT8872ADriver(BaseInstrumentDriver):
    # Connection
    async def initialize() -> None
    async def reset() -> None

    # Signal Generation
    async def configure_signal_generator(frequency, level, standard) -> None
    async def set_generator_state(enabled) -> None

    # LTE TX
    async def measure_lte_tx_power(band, channel, bandwidth) -> Dict
    async def _configure_lte_measurement(band, channel, bandwidth) -> None
    async def _poll_measurement_complete() -> None

    # LTE RX
    async def measure_lte_rx_sensitivity(band, channel, test_power) -> Dict

    # Helpers
    async def _load_waveform(standard) -> None
    async def _simulate_lte_tx_measurement() -> Dict
    async def _simulate_lte_rx_measurement() -> Dict
```

---

## Data Flow

```
Test Plan (CSV)
    ↓
MeasurementService.execute_measurement()
    ↓
RF_Tool_LTE_TX_Measurement.execute()
    ↓
InstrumentManager.get_driver('RF_Tool_1')
    ↓
MT8872ADriver.measure_lte_tx_power(...)
    ↓
Returns: Dict with tx_power, frequency, status
    ↓
MeasurementResult created & validated
    ↓
Saved to test_results table
```

---

## Simulation Mode

### Detection

```python
self.simulation_mode = config.connection.address.startswith('sim://')
```

### Configuration

```yaml
instruments:
  CMW100_1:
    type: cmw100
    address: sim://cmw100  # Mock mode

  RF_Tool_1:
    type: mt8872a
    address: TCPIP0::192.168.1.1::inst0::INSTR  # Real hardware
```

### Mock Values

- BLE TX: -10 to +15 dBm
- WiFi TX: 5 to 25 dBm, EVM: -35 to -50 dB
- LTE TX: 15 to 30 dBm
- LTE RX: -100 to -50 dBm

---

## File Structure

```
backend/app/services/instruments/
├── cmw100.py          # NEW
├── mt8872a.py         # NEW

backend/app/measurements/implementations.py
└── Update to use real drivers

backend/app/services/instrument_manager.py
└── Add cmw100, mt8872a mappings

tests/test_instruments/
├── test_cmw100.py      # NEW
└── test_mt8872a.py     # NEW
```

---

## Dependencies

```txt
RsInstrument>=1.50.0
pyvisa>=1.13.0
pyvisa-py>=0.7.0
```

---

## Implementation Order

1. cmw100.py - RsInstrument driver
2. mt8872a.py - PyVISA driver
3. Update implementations.py
4. Update instrument_manager.py
5. Add unit tests

---

*Design approved - Proceeding with implementation*
