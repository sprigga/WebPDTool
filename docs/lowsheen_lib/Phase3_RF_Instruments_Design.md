# Phase 3 RF Instruments Design Document

**Version**: 1.0
**Date**: 2026-02-05
**Author**: Claude Code
**Status**: Approved for Implementation

---

## Executive Summary

This document describes the design for Phase 3 wireless communication test instruments: **CMW100** (Bluetooth/WiFi tester) and **RF_Tool** (LTE TX/RX tester). The implementation follows Option B strategy: **Core Features + Extensible Architecture** with **Mock Testing + Optional Real Hardware**.

**Scope:**
- ✅ CMW100: Bluetooth LE + WiFi 802.11 measurements
- ✅ RF_Tool: LTE TX/RX measurements with MT8872A
- ✅ Mock mode for development without hardware
- ✅ Integration with existing WebPDTool architecture

**Estimated Effort:** 4-5 days

---

## System Architecture

### Overview Diagram

```
┌─────────────────────────────────────────────────────────┐
│           WebPDTool Backend (FastAPI)                   │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │     Instrument Drivers (Phase 3)               │    │
│  │                                                 │    │
│  │  ┌──────────────┐      ┌──────────────────┐   │    │
│  │  │ CMW100Driver │      │ RF_ToolDriver    │   │    │
│  │  │              │      │                  │   │    │
│  │  │ • BT LE      │      │ • MT8872A Gen    │   │    │
│  │  │ • WiFi       │      │ • LTE TX/RX      │   │    │
│  │  └──────┬───────┘      └────────┬─────────┘   │    │
│  │         │                       │             │    │
│  │         └───────┬───────────────┘             │    │
│  │                 │                             │    │
│  │         ┌───────▼────────────┐                │    │
│  │         │ InstrumentConnection│                │    │
│  │         │ (VISA/Socket/Mock) │                │    │
│  │         └────────────────────┘                │    │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴─────────────┐
        │                         │
┌───────▼────────┐      ┌─────────▼────────┐
│  CMW100 Mock   │      │  MT8872A Mock    │
│  (Development) │      │  (Development)   │
└────────────────┘      └──────────────────┘
        │                         │
        │      (Production)       │
┌───────▼────────┐      ┌─────────▼────────┐
│  R&S CMW100    │      │  Anritsu MT8872A │
│  (TCPIP/GPIB)  │      │  (VISA/TCPIP)    │
└────────────────┘      └──────────────────┘
```

### Core Components

1. **CMW100Driver** (`backend/app/services/instruments/cmw100.py`)
   - Rohde & Schwarz CMW100 wireless communications tester
   - Bluetooth LE and WiFi 802.11 measurements
   - TCPIP/GPIB connection support

2. **RF_ToolDriver** (`backend/app/services/instruments/rf_tool.py`)
   - Anritsu MT8872A universal wireless test set
   - Signal generation (CW/ARB modes)
   - LTE TX/RX measurements

3. **Connection Layer**
   - Utilizes existing `VisaConnection` for SCPI communication
   - New `MockRFConnection` for development testing

---

## CMW100 Driver Design

### Class Structure

```python
class CMW100Driver(BaseInstrumentDriver):
    """
    Rohde & Schwarz CMW100 Wireless Communications Tester Driver

    Supports:
    - Bluetooth LE measurements
    - WiFi 802.11 measurements (b/g/n/ac/ax)
    """

    # Bluetooth burst types
    BT_BURST_TYPES = {
        'BR': 0,   # Basic Rate
        'EDR': 1,  # Enhanced Data Rate
        'LE': 2    # Low Energy
    }

    # WiFi standards
    WIFI_STANDARDS = {
        'B': '11B',      # 802.11b
        'G': '11G',      # 802.11g
        'N': '11N',      # 802.11n
        'AC': '11AC',    # 802.11ac
        'AX': '11AX'     # 802.11ax (WiFi 6)
    }
```

### Core Methods

#### Initialization and Reset

```python
async def initialize(self):
    """Initialize CMW100 to known state"""
    await self.write_command('*RST')
    await self.write_command('SYST:LANG SCPI')

async def reset(self):
    """Reset to default state"""
    await self.write_command('*RST')
```

#### Bluetooth LE Measurement

```python
async def configure_bluetooth_le(
    self,
    connector: int,      # RF port (1-8)
    frequency: float,    # MHz (2402-2480)
    expected_power: float  # dBm
) -> None:
    """
    Configure Bluetooth LE measurement

    Args:
        connector: RF connector port (1-8 for RA1-RA8)
        frequency: RF frequency in MHz (2402-2480)
        expected_power: Expected nominal power in dBm

    SCPI Commands:
        CONFigure:BLUetooth:MEAS:RFSettings:CONNector RA{connector}
        CONFigure:BLUetooth:MEAS:RFSettings:FREQuency {frequency} MHz
        CONFigure:BLUetooth:MEAS:RFSettings:ENPower {expected_power}
        CONFigure:BLUetooth:MEAS:ISIGnal:BTYPe LE
        CONFigure:BLUetooth:MEAS:ISIGnal:REPetition SINGleshot
    """

async def measure_bluetooth_le(self) -> Dict[str, float]:
    """
    Execute BLE measurement and return results

    Returns:
        {
            'power': float,          # Average power (dBm)
            'freq_offset': float,    # Frequency offset (kHz)
            'modulation': float      # Modulation characteristic
        }

    SCPI Commands:
        INITiate:BLUetooth:MEAS:MEValuation
        FETCh:BLUetooth:MEAS:MEValuation:MODulation:AVERage?
        FETCh:BLUetooth:MEAS:MEValuation:POWer:AVERage?
        FETCh:BLUetooth:MEAS:MEValuation:FREQuency:OFFSet?
    """
```

#### WiFi Measurement

```python
async def configure_wifi(
    self,
    standard: str,       # '11B', '11G', '11N', '11AC', '11AX'
    channel: int,        # WiFi channel number
    expected_power: float  # dBm
) -> None:
    """
    Configure WiFi measurement

    Args:
        standard: WiFi standard ('11B', '11G', '11N', '11AC', '11AX')
        channel: WiFi channel number (1-165)
        expected_power: Expected nominal power in dBm

    SCPI Commands:
        CONFigure:WLAN:MEAS:RFSettings:FREQuency {frequency} MHz
        CONFigure:WLAN:MEAS:RFSettings:ENPower {expected_power}
        CONFigure:WLAN:MEAS:ISIGnal:STANdard {standard}
    """

async def measure_wifi(self) -> Dict[str, float]:
    """
    Execute WiFi measurement and return results

    Returns:
        {
            'power': float,          # Average power (dBm)
            'evm': float,           # Error Vector Magnitude (%)
            'freq_error': float,    # Frequency error (ppm)
            'spectrum_mask': str    # 'PASS'/'FAIL'
        }

    SCPI Commands:
        INITiate:WLAN:MEAS:MEValuation
        FETCh:WLAN:MEAS:MEValuation:POWer:AVERage?
        FETCh:WLAN:MEAS:MEValuation:EVM:AVERage?
        FETCh:WLAN:MEAS:MEValuation:FERRor?
        FETCh:WLAN:MEAS:MEValuation:SPECtrum:MASK?
    """
```

### Mock Mode Behavior

Development phase mock responses:
- **Bluetooth LE**: Returns simulated power (-5.2 dBm), freq offset (±2 kHz), modulation (0.95)
- **WiFi**: Returns simulated EVM (< 5%), power, freq error, spectrum mask PASS

---

## RF_Tool Driver Design

### Class Structure

```python
class RF_ToolDriver(BaseInstrumentDriver):
    """
    RF Testing Tool Driver for MT8872A Universal Wireless Test Set

    Supports:
    - Signal generation (CW/ARB modes)
    - LTE TX measurements (power, spectrum)
    - LTE RX measurements (sensitivity)
    """

    # Baseband modes
    BB_MODES = {
        'CW': 1,   # Continuous Wave
        'ARB': 2   # Arbitrary Waveform
    }

    # ARB waveform types
    ARB_TYPES = {
        'GSM': 0,
        'WCDMA': 1,
        'LTE': 2,
        'NR': 3
    }

    # LTE bands (common ones)
    LTE_BANDS = {
        'B1': 2140.0,   # 2100 MHz
        'B3': 1805.0,   # 1800 MHz
        'B7': 2655.0,   # 2600 MHz
        'B38': 2570.0,  # TDD 2600 MHz
        'B41': 2496.0   # TDD 2500 MHz
    }
```

### Core Methods

#### Initialization and Reset

```python
async def initialize(self):
    """Initialize MT8872A to known state"""
    await self.write_command('*RST')
    await self.write_command('SYST:LANG SCPI')

async def reset(self):
    """Reset generator to default state"""
    await self.write_command(':SOURce:GPRF:GENerator:STATe OFF')
    await self.write_command('*RST')
```

#### Signal Generator Control

```python
async def configure_generator(
    self,
    frequency: float,    # MHz
    power: float,        # dBm
    mode: str = 'CW',    # 'CW' or 'ARB'
    waveform_type: str = 'LTE'  # For ARB mode
) -> None:
    """
    Configure MT8872A signal generator

    Args:
        frequency: Center frequency in MHz
        power: Output power in dBm
        mode: 'CW' (simple carrier) or 'ARB' (modulated)
        waveform_type: 'GSM', 'WCDMA', 'LTE', 'NR' (ARB only)

    SCPI Commands (CW mode):
        :SOURce:GPRF:GENerator:RFSettings:FREQuency {frequency} MHz
        :SOURce:GPRF:GENerator:RFSettings:LEVel {power}
        :SOURce:GPRF:GENerator:BBMode CW
        :SOURce:GPRF:GENerator:MODE NORMAL

    SCPI Commands (ARB mode):
        :SOURce:GPRF:GENerator:BBMode ARB
        :SOURce:GPRF:GENerator:ARB:FILE 'LTE_10M_TM31'
    """

async def set_generator_state(self, state: bool) -> None:
    """
    Turn generator ON/OFF

    Args:
        state: True for ON, False for OFF

    SCPI Commands:
        :SOURce:GPRF:GENerator:STATe ON/OFF
    """
```

#### LTE TX Measurement

```python
async def measure_lte_tx_power(
    self,
    band: str,           # 'B1', 'B3', 'B7', etc.
    channel: int,        # LTE channel number
    bandwidth: float = 10.0  # MHz (5, 10, 15, 20)
) -> Dict[str, float]:
    """
    Measure LTE transmit power

    Args:
        band: LTE band ('B1', 'B3', 'B7', etc.)
        channel: LTE channel number
        bandwidth: Channel bandwidth in MHz

    Returns:
        {
            'tx_power': float,       # dBm
            'channel_power': float,  # dBm
            'peak_power': float,     # dBm
            'occupied_bw': float     # MHz
        }

    SCPI Commands:
        :CONFigure:LTE:MEAS:RFSettings:FREQuency {frequency} MHz
        :CONFigure:LTE:MEAS:RFSettings:BANDwidth BW{bw}
        :INITiate:LTE:MEAS:POWer
        :FETCh:LTE:MEAS:POWer:AVERage?
        :FETCh:LTE:MEAS:POWer:CHANnel?
        :FETCh:LTE:MEAS:POWer:PEAK?
    """

async def measure_lte_spectrum(
    self,
    band: str,
    channel: int
) -> Dict[str, Any]:
    """
    Measure LTE spectrum characteristics

    Args:
        band: LTE band
        channel: LTE channel number

    Returns:
        {
            'aclr_lower': float,     # dB (Adjacent Channel Leakage Ratio)
            'aclr_upper': float,     # dB
            'spectrum_flatness': str,  # 'PASS'/'FAIL'
            'evm': float             # % (Error Vector Magnitude)
        }

    SCPI Commands:
        :INITiate:LTE:MEAS:SPECtrum
        :FETCh:LTE:MEAS:SPECtrum:ACLR:ADJacent:LOWer?
        :FETCh:LTE:MEAS:SPECtrum:ACLR:ADJacent:UPPer?
        :FETCh:LTE:MEAS:SPECtrum:FLATness?
        :FETCh:LTE:MEAS:MODulation:EVM?
    """
```

#### LTE RX Measurement

```python
async def measure_lte_rx_sensitivity(
    self,
    band: str,
    channel: int,
    test_power: float = -90.0  # dBm
) -> Dict[str, Any]:
    """
    Measure LTE receiver sensitivity

    Process:
    1. Generate LTE downlink signal at test_power
    2. DUT reports received signal quality
    3. Return RSSI, SINR, throughput

    Args:
        band: LTE band
        channel: LTE channel number
        test_power: Test signal power in dBm

    Returns:
        {
            'rssi': float,           # dBm (Received Signal Strength)
            'sinr': float,           # dB (Signal to Interference Ratio)
            'throughput': float,     # Mbps
            'bler': float            # % (Block Error Rate)
        }

    Note: Requires DUT to be in FTM mode and report measurements
    """
```

### Mock Mode Behavior

Development phase mock responses:
- **LTE TX Power**: Returns simulated TX power (23 dBm), channel power, peak power
- **LTE Spectrum**: Returns simulated ACLR (> 30 dB), EVM (< 8%), spectrum flatness PASS
- **LTE RX Sensitivity**: Returns simulated RSSI (-90 dBm), SINR (10 dB), throughput

---

## Error Handling

### Exception Hierarchy

```python
class RFInstrumentError(Exception):
    """Base exception for RF instruments"""
    pass

class CMW100ConnectionError(RFInstrumentError):
    """CMW100 connection failed"""
    pass

class MT8872AConnectionError(RFInstrumentError):
    """MT8872A connection failed"""
    pass

class RFMeasurementError(RFInstrumentError):
    """Measurement execution failed"""
    pass
```

### Timeout and Retry Mechanism

```python
async def measure_with_timeout(
    self,
    measure_func,
    timeout: float = 30.0  # seconds
):
    """Execute measurement with timeout"""
    try:
        result = await asyncio.wait_for(
            measure_func(),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        raise RFMeasurementError(
            f"Measurement timeout after {timeout}s"
        )
```

### Instrument Status Check

```python
async def check_instrument_ready(self) -> bool:
    """Check if instrument is ready for measurement"""
    try:
        idn = await self.query_command('*IDN?')
        return len(idn) > 0
    except Exception:
        return False
```

---

## Testing Strategy

### Test Structure

```
backend/tests/test_services/test_instruments/
├── test_cmw100.py           # CMW100 driver tests
├── test_rf_tool.py          # RF_Tool driver tests
└── fixtures/
    ├── mock_cmw100.py       # CMW100 Mock implementation
    └── mock_mt8872a.py      # MT8872A Mock implementation
```

### Test Cases

#### CMW100 Tests

```python
@pytest.mark.asyncio
async def test_cmw100_bluetooth_le_measurement():
    """Test Bluetooth LE measurement"""
    driver = CMW100Driver(MockCMW100Connection())
    await driver.initialize()

    await driver.configure_bluetooth_le(
        connector=1,
        frequency=2440.0,
        expected_power=-5.0
    )

    result = await driver.measure_bluetooth_le()

    assert 'power' in result
    assert 'freq_offset' in result
    assert -10.0 < result['power'] < 0.0

@pytest.mark.asyncio
async def test_cmw100_wifi_measurement():
    """Test WiFi measurement"""
    driver = CMW100Driver(MockCMW100Connection())
    await driver.initialize()

    await driver.configure_wifi(
        standard='11AC',
        channel=36,
        expected_power=15.0
    )

    result = await driver.measure_wifi()

    assert 'evm' in result
    assert 'power' in result
    assert result['spectrum_mask'] in ['PASS', 'FAIL']
```

#### RF_Tool Tests

```python
@pytest.mark.asyncio
async def test_rf_tool_generator_control():
    """Test MT8872A generator control"""
    driver = RF_ToolDriver(MockMT8872AConnection())
    await driver.initialize()

    await driver.configure_generator(
        frequency=2140.0,
        power=-18.0,
        mode='ARB',
        waveform_type='LTE'
    )

    await driver.set_generator_state(True)

    # Verify state (Mock mode records commands)
    assert driver.connection.last_command_contains('STATe ON')

@pytest.mark.asyncio
async def test_rf_tool_lte_tx_measurement():
    """Test LTE TX power measurement"""
    driver = RF_ToolDriver(MockMT8872AConnection())
    await driver.initialize()

    result = await driver.measure_lte_tx_power(
        band='B1',
        channel=100,
        bandwidth=10.0
    )

    assert 'tx_power' in result
    assert 'channel_power' in result
    assert 0.0 < result['tx_power'] < 30.0
```

### Mock Implementation

```python
class MockCMW100Connection(BaseInstrumentConnection):
    """Mock CMW100 connection for testing"""

    def __init__(self):
        self.last_command = ""

    async def write(self, command: str) -> None:
        self.last_command = command

    async def query(self, command: str) -> str:
        # Simulate responses
        if '*IDN?' in command:
            return 'Rohde&Schwarz,CMW100,Mock,1.0'
        elif 'FETCh:BLUetooth:MEAS' in command:
            return '-5.2,1.5,0.95'  # power, freq_offset, modulation
        elif 'FETCh:WLAN:MEAS' in command:
            return '15.3,3.2,0.5,PASS'  # power, evm, freq_err, mask
        return 'OK'
```

---

## Integration with WebPDTool

### Test Plan CSV Integration

New test types in CSV:

```csv
項次,品名規格,測試項目,test_type,儀器,參數
1,BLE Module,BLE TX Power,CMW100_BLE,CMW100_1,{"connector":1,"frequency":2440,"expected_power":-5}
2,WiFi Module,WiFi EVM Test,CMW100_WIFI,CMW100_1,{"standard":"11AC","channel":36,"expected_power":15}
3,LTE Module,LTE TX Power,RF_TOOL_LTE_TX,MT8872A_1,{"band":"B1","channel":100,"bandwidth":10}
4,LTE Module,LTE RX Sensitivity,RF_TOOL_LTE_RX,MT8872A_1,{"band":"B1","channel":100,"test_power":-90}
```

### Measurement Registry

Register new measurement types in `backend/app/measurements/registry.py`:

```python
from app.measurements.implementations import (
    CMW100_BLE_Measurement,
    CMW100_WiFi_Measurement,
    RF_Tool_LTE_TX_Measurement,
    RF_Tool_LTE_RX_Measurement
)

MEASUREMENT_REGISTRY.register('CMW100_BLE', CMW100_BLE_Measurement)
MEASUREMENT_REGISTRY.register('CMW100_WIFI', CMW100_WiFi_Measurement)
MEASUREMENT_REGISTRY.register('RF_TOOL_LTE_TX', RF_Tool_LTE_TX_Measurement)
MEASUREMENT_REGISTRY.register('RF_TOOL_LTE_RX', RF_Tool_LTE_RX_Measurement)
```

### Measurement Implementation Example

```python
class CMW100_BLE_Measurement(BaseMeasurement):
    """Bluetooth LE measurement using CMW100"""

    async def prepare(self, params: Dict[str, Any]) -> None:
        """Prepare BLE measurement"""
        self.instrument = await self.instrument_manager.get_instrument(
            params.get('instrument', 'CMW100_1')
        )

        connector = int(params.get('connector', 1))
        frequency = float(params.get('frequency', 2440.0))
        expected_power = float(params.get('expected_power', -5.0))

        await self.instrument.configure_bluetooth_le(
            connector=connector,
            frequency=frequency,
            expected_power=expected_power
        )

    async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
        """Execute BLE measurement"""
        result = await self.instrument.measure_bluetooth_le()

        measured_power = result['power']

        is_valid, message = self.validate_result(
            measured_value=measured_power,
            lower_limit=params.get('lower_limit'),
            upper_limit=params.get('upper_limit'),
            limit_type=params.get('limit_type', 'both'),
            value_type='float'
        )

        return MeasurementResult(
            success=is_valid,
            measured_value=str(measured_power),
            message=message,
            details={
                'power': result['power'],
                'freq_offset': result['freq_offset'],
                'modulation': result['modulation']
            }
        )

    async def cleanup(self) -> None:
        """Cleanup after measurement"""
        pass  # CMW100 maintains connection state
```

---

## Configuration Management

### Instrument Configuration

`config/instruments.yaml`:

```yaml
instruments:
  CMW100_1:
    type: cmw100
    connection_type: visa  # or 'mock'
    address: TCPIP::192.168.1.100::INSTR
    timeout: 30000

  MT8872A_1:
    type: rf_tool
    connection_type: visa  # or 'mock'
    address: TCPIP::192.168.1.101::5025::SOCKET
    timeout: 30000

# Development mode uses Mock
development:
  CMW100_1:
    connection_type: mock
  MT8872A_1:
    connection_type: mock
```

---

## Extension Strategy

### Phase 3.1 (This Implementation)

- ✅ CMW100: Bluetooth LE + WiFi
- ✅ RF_Tool: LTE TX/RX

### Phase 3.2 (Future Extensions - Reserved Interfaces)

**CMW100 Extensions:**
- Bluetooth BR/EDR modes
- LTE measurement module integration
- 5G NR measurement support

**RF_Tool Extensions:**
- GSM TX/RX measurements
- WCDMA TX/RX measurements
- 5G NR TX/RX measurements
- QMSL DLL integration (requires Windows)

**Extension Example:**
```python
# Future: CMW100 LTE measurement
async def configure_lte_measurement(
    self,
    band: str,
    channel: int,
    bandwidth: float
) -> None:
    """Configure LTE measurement (Phase 3.2)"""
    pass

async def measure_lte(self) -> Dict[str, float]:
    """Execute LTE measurement (Phase 3.2)"""
    pass
```

---

## Dependency Management

### requirements.txt Update

```txt
# Existing dependencies
pyvisa>=1.13.0
pyvisa-py>=0.7.0

# Phase 3 optional (for real hardware)
# RsInstrument>=1.50.0  # CMW100 real hardware (pip install RsInstrument)
# python-can>=4.2.0     # Future CAN Bus support

# Development dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

### Optional Dependency Installation Script

`scripts/install_rf_deps.sh`:

```bash
#!/bin/bash
# Install RF instrument real dependencies (production environment)

echo "Installing RF instrument dependencies..."

# CMW100 - Rohde & Schwarz
pip install RsInstrument>=1.50.0

# VISA backend
pip install pyvisa-py>=0.7.0

echo "RF dependencies installed successfully!"
echo "To use real hardware, update config/instruments.yaml:"
echo "  connection_type: visa  # Change from 'mock' to 'visa'"
```

---

## Documentation Updates

Files to be updated:
1. **README.md** - Add Phase 3 instruments description
2. **Instrument_Implementation_Status.md** - Update progress to 65.4% (17/26)
3. **New configuration examples** - This document

---

## Implementation Summary

### Scope

✅ **CMW100 Driver**
- Bluetooth LE measurement (power, freq offset, modulation)
- WiFi measurement (EVM, power, spectrum mask)
- Mock mode development support

✅ **RF_Tool Driver**
- MT8872A signal generation (CW/ARB modes)
- LTE TX measurement (power, spectrum, ACLR)
- LTE RX measurement (sensitivity, SINR, throughput)
- Mock mode development support

✅ **Integration**
- Inherits existing BaseInstrumentDriver architecture
- Integrates into Measurement Registry
- Supports test plan CSV import
- Complete error handling and unit tests

### Estimated Effort

- CMW100 driver: 2 days
- RF_Tool driver: 2 days
- Integration & testing: 1 day
- **Total: 4-5 days**

### Technical Advantages

- 🚀 **Fast Development** - Mock mode without physical hardware
- 🔧 **Easy Testing** - Complete unit test coverage
- 📈 **Easy Extension** - Reserved interfaces for BR/EDR/GSM/WCDMA/NR
- 🔄 **Environment Switching** - Toggle Mock/Real hardware via config

---

## Next Steps

1. **Create git worktree** for isolated development
2. **Implement CMW100Driver** with BLE + WiFi support
3. **Implement RF_ToolDriver** with LTE TX/RX support
4. **Create Mock connections** for testing
5. **Implement Measurement classes** for integration
6. **Write unit tests** for all components
7. **Update configuration** files and documentation
8. **Integration testing** with WebPDTool backend

---

**Document Status**: ✅ Approved for Implementation
**Ready for**: Implementation Phase
