# Phase 2 - 常用測試儀器 (擴充儀器庫) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 4 Phase 2 instruments (APS7050, Agilent N5182A, Analog Discovery 2, FTM_On) to expand the WebPDTool instrument library from 42.3% to ~58% completion, maintaining PDTool4 compatibility while modernizing the architecture.

**Architecture:** Follow existing BaseInstrumentDriver pattern with async/await, VISA/Serial/TCPIP connection abstraction, simulation mode for testing, and PDTool4-compatible parameter interfaces.

**Tech Stack:** Python 3.11+, asyncio, pyvisa, pyserial, ctypes (for AD2), pytest, Pydantic for configuration

---

## Task 1: Create APS7050 Instrument Driver

**Files:**
- Create: `backend/app/services/instruments/aps7050.py`
- Modify: `backend/app/services/instruments/__init__.py`
- Test: `backend/tests/test_services/test_aps7050.py`

**Context:** APS7050 is a GW Instek AC/DC Power Source with built-in DMM and relay control. It extends the 34970A driver pattern but adds raw SCPI command support. Key features: voltage/current/AC+DC measurements, relay switching, and raw command execution.

**Step 1: Write the failing test**

```python
# tests/test_services/test_aps7050.py

import pytest
from app.services.instruments.aps7050 import APS7050Driver
from app.services.instrument_connection import SimulationInstrumentConnection
from app.core.instrument_config import InstrumentConfig, VISAAddress

@pytest.fixture
def aps7050_driver():
    """Create APS7050 driver with simulation connection"""
    config = InstrumentConfig(
        id="APS7050_1",
        type="APS7050",
        name="GW Instek APS7050",
        connection=VISAAddress(address="TCPIP0::192.168.1.50::inst0::INSTR")
    )
    conn = SimulationInstrumentConnection(config)
    driver = APS7050Driver(conn)
    return driver

@pytest.mark.asyncio
async def test_aps7050_measure_dc_voltage(aps7050_driver):
    """Test DC voltage measurement on channel 101"""
    await aps7050_driver.initialize()
    result = await aps7050_driver.measure_voltage(['101'], 'DC')
    assert isinstance(result, float)
    await aps7050_driver.reset()

@pytest.mark.asyncio
async def test_aps7050_close_relay(aps7050_driver):
    """Test relay close operation"""
    await aps7050_driver.initialize()
    result = await aps7050_driver.close_channels(['205'])
    assert result is not None

@pytest.mark.asyncio
async def test_aps7050_raw_command(aps7050_driver):
    """Test raw SCPI command execution"""
    await aps7050_driver.initialize()
    result = await aps7050_driver.execute_raw_command('*IDN?\\n')
    assert 'GW' in result or 'Simulated' in result

@pytest.mark.asyncio
async def test_aps7050_execute_command_pdtool4_compatible(aps7050_driver):
    """Test PDTool4-compatible execute_command interface"""
    await aps7050_driver.initialize()
    result = await aps7050_driver.execute_command({
        'Item': 'VOLT',
        'Channel': '101',
        'Type': 'DC'
    })
    # Should return formatted string
    assert isinstance(result, str)
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_services/test_aps7050.py -v
```
Expected: FAIL with "APS7050Driver not found"

**Step 3: Write minimal implementation**

```python
# app/services/instruments/aps7050.py

"""
APS7050 Instrument Driver

GW Instek APS-7000 Series Programmable AC/DC Power Source
with built-in DMM and relay control
"""
from typing import Dict, Any, Literal, List
from decimal import Decimal
import asyncio
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class APS7050Driver(BaseInstrumentDriver):
    """
    Driver for GW Instek APS-7000 Series Power Source with DMM

    Supports:
    - AC/DC voltage/current measurements
    - Relay switching (OPEN/CLOSE)
    - Resistance, capacitance, frequency, period measurements
    - Diode and temperature measurements
    - Raw SCPI command execution (unique to APS7050)
    """

    # Channel validation rules
    CURRENT_CHANNELS = ['21', '22']  # Only channels 21, 22 support current measurement
    VALID_CHANNELS = [f'{i:02d}' for i in range(1, 21)]  # Channels 01-20
    RELAY_CHANNELS = [f'{i:02d}' for i in range(1, 21)]  # Relay channels 01-20

    async def initialize(self):
        """Initialize the instrument"""
        await self.reset()
        self.logger.info("APS7050 initialized")

    async def reset(self):
        """Reset the instrument to default state"""
        await self.write_command('*RST')
        await asyncio.sleep(0.5)
        self.logger.debug("APS7050 reset")

    def _validate_channels(self, channels: List[str], command: str) -> None:
        """Validate channel numbers for specific commands"""
        if command == 'CURR':
            invalid = [ch for ch in channels if ch not in self.CURRENT_CHANNELS]
            if invalid:
                raise ValueError(
                    f"Current measurement only on channels {self.CURRENT_CHANNELS}, "
                    f"got invalid: {invalid}"
                )

    def _parse_channel_spec(self, channel_spec: Any) -> List[str]:
        """Parse channel specification to list of channel strings"""
        if isinstance(channel_spec, str):
            channels = [ch.strip() for ch in channel_spec.split(',')]
        elif isinstance(channel_spec, (tuple, list)):
            channels = [str(ch) for ch in channel_spec]
        else:
            channels = [str(channel_spec)]

        normalized = []
        for ch in channels:
            ch = ch.strip()
            if len(ch) == 3 and ch.startswith('1'):
                ch = ch[1:]  # "101" -> "01"
            normalized.append(ch.zfill(2))
        return normalized

    async def open_channels(self, channels: List[str]) -> str:
        """Open (disconnect) specified relay channels"""
        channel_list = ','.join(channels)
        cmd = f"ROUT:OPEN (@{channel_list})"
        await self.write_command(cmd)
        response = await self.query_command(f"ROUT:OPEN? (@{channel_list})")
        self.logger.debug(f"Opened channels {channel_list}: {response}")
        return response

    async def close_channels(self, channels: List[str]) -> str:
        """Close (connect) specified relay channels"""
        channel_list = ','.join(channels)
        cmd = f"ROUT:CLOS (@{channel_list})"
        await self.write_command(cmd)
        response = await self.query_command(f"ROUT:CLOS? (@{channel_list})")
        self.logger.debug(f"Closed channels {channel_list}: {response}")
        return response

    async def measure_voltage(
        self,
        channels: List[str],
        type: Literal['AC', 'DC'] = 'DC'
    ) -> Decimal:
        """Measure voltage on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:VOLT:{type}? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_current(
        self,
        channels: List[str],
        type: Literal['AC', 'DC'] = 'DC'
    ) -> Decimal:
        """Measure current on specified channels (channels 21/22 only)"""
        self._validate_channels(channels, 'CURR')
        channel_list = ','.join(channels)
        cmd = f"MEAS:CURR:{type}? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_resistance(
        self,
        channels: List[str],
        four_wire: bool = False
    ) -> Decimal:
        """Measure resistance on specified channels"""
        channel_list = ','.join(channels)
        cmd_type = 'FRES' if four_wire else 'RES'
        cmd = f"MEAS:{cmd_type}? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_capacitance(self, channels: List[str]) -> Decimal:
        """Measure capacitance on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:CAP? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def measure_frequency(self, channels: List[str]) -> Decimal:
        """Measure frequency on specified channels"""
        channel_list = ','.join(channels)
        cmd = f"MEAS:FREQ? (@{channel_list})"
        return await self.query_decimal(cmd)

    async def execute_raw_command(self, command: str) -> str:
        """
        Execute raw SCPI command (APS7050 unique feature)

        Args:
            command: Raw SCPI command string (supports \\n escape sequences)

        Returns:
            Instrument response
        """
        # Convert escape sequences
        processed_cmd = command.replace('\\n', '\n').replace('\\r', '\r')
        return await self.query_command(processed_cmd)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Item: Command type (OPEN, CLOS, VOLT, CURR, etc.)
                - Channel: Channel specification
                - Type: AC/DC type (for VOLT/CURR)
                - Command: Raw SCPI command (optional, takes priority)

        Returns:
            String result (for backward compatibility)
        """
        # Check for raw command first (APS7050 unique feature)
        raw_cmd = get_param(params, 'Command')
        if raw_cmd:
            return await self.execute_raw_command(raw_cmd)

        # Standard command processing
        validate_required_params(params, ['Item', 'Channel'])

        item = params['Item'].upper()
        channel_spec = params['Channel']
        type_ = get_param(params, 'Type', 'DC', default='DC').upper()

        channels = self._parse_channel_spec(channel_spec)

        # Execute command based on item type
        if item == 'OPEN':
            result = await self.open_channels(channels)
            return str(result) if result is not None else '0'

        elif item == 'CLOS':
            result = await self.close_channels(channels)
            return str(result) if result is not None else '0'

        elif item == 'VOLT':
            value = await self.measure_voltage(channels, type_)
            return f'{value:.3f}'

        elif item == 'CURR':
            value = await self.measure_current(channels, type_)
            return f'{value:.3f}'

        elif item == 'RES':
            value = await self.measure_resistance(channels, four_wire=False)
            return f'{value:.3f}'

        elif item == 'FRES':
            value = await self.measure_resistance(channels, four_wire=True)
            return f'{value:.3f}'

        else:
            raise ValueError(f"Unknown command: {item}")
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/test_services/test_aps7050.py -v
```
Expected: PASS

**Step 5: Update __init__.py to register driver**

```python
# app/services/instruments/__init__.py

# ... existing imports ...
from .aps7050 import APS7050Driver

# Update INSTRUMENT_DRIVERS registry
INSTRUMENT_DRIVERS = {
    # ... existing entries ...
    'APS7050': APS7050Driver,
}
```

**Step 6: Commit**

```bash
git add backend/app/services/instruments/aps7050.py \
        backend/app/services/instruments/__init__.py \
        backend/tests/test_services/test_aps7050.py
git commit -m "feat: add APS7050 instrument driver

- GW Instek APS-7000 Series AC/DC Power Source with DMM
- Supports voltage/current/AC+DC measurements
- Relay switching (OPEN/CLOSE)
- Raw SCPI command execution (unique feature)
- PDTool4-compatible execute_command interface
- Full test coverage with simulation mode"
```

---

## Task 2: Create Agilent N5182A Signal Generator Driver

**Files:**
- Create: `backend/app/services/instruments/n5182a.py`
- Modify: `backend/app/services/instruments/__init__.py`
- Test: `backend/tests/test_services/test_n5182a.py`

**Context:** N5182A is an MXG signal generator with CW (continuous wave) and ARB (arbitrary waveform) modes. Uses GPIB address format, requires frequency/amplitude/power settings, and supports output state control.

**Step 1: Write the failing test**

```python
# tests/test_services/test_n5182a.py

import pytest
from app.services.instruments.n5182a import N5182ADriver
from app.services.instrument_connection import SimulationInstrumentConnection
from app.core.instrument_config import InstrumentConfig, GPIBAddress

@pytest.fixture
def n5182a_driver():
    """Create N5182A driver with simulation connection"""
    config = InstrumentConfig(
        id="N5182A_1",
        type="N5182A",
        name="Agilent N5182A MXG",
        connection=GPIBAddress(board=0, address=16)
    )
    conn = SimulationInstrumentConnection(config)
    driver = N5182ADriver(conn)
    return driver

@pytest.mark.asyncio
async def test_n5182a_set_cw_mode(n5182a_driver):
    """Test setting CW mode with frequency and amplitude"""
    await n5182a_driver.initialize()
    await n5182a_driver.set_frequency('100K')
    await n5182a_driver.set_amplitude('-10')
    await n5182a_driver.set_output_state('ON')
    # Verify commands were sent
    freq = await n5182a_driver.query_frequency()
    assert freq is not None

@pytest.mark.asyncio
async def test_n5182a_set_arb_mode(n5182a_driver):
    """Test setting ARB mode with waveform"""
    await n5182a_driver.initialize()
    await n5182a_driver.set_arb_waveform('SINE')
    await n5182a_driver.set_output_state('ON')

@pytest.mark.asyncio
async def test_n5182a_translate_frequency(n5182a_driver):
    """Test frequency string translation"""
    assert n5182a_driver._translate_frequency('100K') == '100 k'
    assert n5182a_driver._translate_frequency('50M') == '50 m'
    assert n5182a_driver._translate_frequency('1G') == '1 g'
    assert n5182a_driver._translate_frequency('1000') == '1000 '

@pytest.mark.asyncio
async def test_n5182a_reset(n5182a_driver):
    """Test reset functionality"""
    await n5182a_driver.reset()
    # Verify *RST was sent
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_services/test_n5182a.py::test_n5182a_translate_frequency -v
```
Expected: FAIL with "N5182ADriver not found"

**Step 3: Write minimal implementation**

```python
# app/services/instruments/n5182a.py

"""
Agilent N5182A Instrument Driver

Agilent N5182A MXG X-Series Signal Generator
Supports CW and ARB modes
"""
from typing import Dict, Any, Literal
from decimal import Decimal
import asyncio
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class N5182ADriver(BaseInstrumentDriver):
    """
    Driver for Agilent N5182A MXG Signal Generator

    Supports:
    - CW (Continuous Wave) mode
    - ARB (Arbitrary Waveform) mode
    - Frequency, amplitude, output state control
    """

    # Output state mapping
    OUTPUT_STATES = {
        '0': 'RST',    # Reset
        '1': 'OFF',
        '2': 'ON',
    }

    # Waveform shapes for ARB mode
    WAVEFORMS = {
        '1': 'SINE_TEST_WFM',
        '2': 'RAMP_TEST_WFM',
    }

    async def initialize(self):
        """Initialize the instrument"""
        await self.write_command('*RST')
        await asyncio.sleep(0.5)
        self.logger.info("N5182A initialized")

    async def reset(self):
        """Reset the instrument to default state"""
        identification = await self.query_command('*IDN?')
        self.logger.info(f"Resetting N5182A: {identification}")
        await self.write_command('*RST')
        await asyncio.sleep(0.5)

    def _translate_frequency(self, freq: str) -> str:
        """
        Translate frequency string from compact format to SCPI format

        Args:
            freq: Frequency string like "100K", "50M", "1G"

        Returns:
            SCPI format like "100 k", "50 m", "1 g"
        """
        if not freq:
            return '0 '

        freq = freq.strip()
        unit = freq[-1].upper()

        if unit in ('K', 'M', 'G'):
            # Remove last char and add space + lowercase unit
            return f"{freq[:-1]} {unit.lower()}"
        else:
            # No unit suffix, add space
            return f"{freq} "

    async def set_frequency(self, frequency: str) -> None:
        """
        Set output frequency

        Args:
            frequency: Frequency string (e.g., "100K", "50M")
        """
        freq_scpi = self._translate_frequency(frequency)
        cmd = f'FREQ {freq_scpi}Hz'
        await self.write_command(cmd)
        self.logger.debug(f"Set frequency to {frequency}")

    async def set_amplitude(self, amplitude: str) -> None:
        """
        Set power amplitude

        Args:
            amplitude: Amplitude in dBm (e.g., "-10")
        """
        cmd = f'POW:AMPL {amplitude} dBm'
        await self.write_command(cmd)
        self.logger.debug(f"Set amplitude to {amplitude} dBm")

    async def set_output_state(self, state: Literal['ON', 'OFF', 'RST']) -> None:
        """
        Set RF output state

        Args:
            state: Output state ('ON', 'OFF', or 'RST')
        """
        if state == 'RST':
            await self.reset()
        else:
            cmd = f'OUTP:STAT {state}'
            await self.write_command(cmd)
            self.logger.debug(f"Set output state to {state}")

    async def set_arb_waveform(self, shape: str) -> None:
        """
        Set ARB waveform

        Args:
            shape: Waveform shape key ('1' for SINE, '2' for RAMP)
        """
        if shape not in self.WAVEFORMS:
            raise ValueError(f"Invalid waveform shape: {shape}")

        waveform = self.WAVEFORMS[shape]
        cmd = f':SOURce:RADio:ARB:WAVeform "WFM1:{waveform}"'
        await self.write_command(cmd)

        # Configure trigger to free run
        await self.write_command(':PULM:SOUR:INT FRUN')
        await self.write_command(':SOURce:RADio:ARB:STATe ON')
        await self.write_command(':OUTPut:MODulation:STATe ON')
        self.logger.debug(f"Set ARB waveform to {waveform}")

    async def query_frequency(self) -> str:
        """Query current frequency setting"""
        return await self.query_command('FREQ:CW?')

    async def query_amplitude(self) -> str:
        """Query current power amplitude"""
        return await self.query_command('POW:AMPL?')

    async def query_output_state(self) -> bool:
        """Query RF output state"""
        response = await self.query_command('OUTP?')
        return int(response.strip()) > 0

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Output: '0'=RST, '1'=OFF, '2'=ON
                - Frequency: Frequency string (e.g., "100K")
                - Amplitude: Amplitude in dBm
                - Mode: '1'=CW, '2'=ARB
                - Shape: Waveform shape (for ARB mode)

        Returns:
            Status confirmation string
        """
        # Map output state
        output_key = get_param(params, 'Output', '0', default='0')
        output = self.OUTPUT_STATES.get(output_key, 'OFF')

        if output == 'RST':
            identification = await self.query_command('*IDN?')
            await self.write_command('*RST')
            return identification

        # Set frequency and amplitude
        frequency = get_param(params, 'Frequency')
        if frequency:
            await self.set_frequency(frequency)

        amplitude = get_param(params, 'Amplitude')
        if amplitude:
            await self.set_amplitude(amplitude)

        # Configure ARB mode if specified
        mode = get_param(params, 'Mode', '1')
        if mode == '2':  # ARB mode
            shape = get_param(params, 'Shape', '1')
            await self.set_arb_waveform(shape)

        # Set output state
        if output in ('ON', 'OFF'):
            await self.set_output_state(output)

        # Return status confirmation
        freq = await self.query_frequency()
        power = await self.query_command('POW:AMPL?')
        rf_state = 'on' if await self.query_output_state() else 'off'

        return f"FREQ:{freq.strip()}, POWER:{power.strip()}, RF:{rf_state}"
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/test_services/test_n5182a.py -v
```
Expected: PASS

**Step 5: Update __init__.py**

```python
# app/services/instruments/__init__.py
from .n5182a import N5182ADriver

INSTRUMENT_DRIVERS = {
    # ... existing entries ...
    'N5182A': N5182ADriver,
}
```

**Step 6: Commit**

```bash
git add backend/app/services/instruments/n5182a.py \
        backend/app/services/instruments/__init__.py \
        backend/tests/test_services/test_n5182a.py
git commit -m "feat: add N5182A signal generator driver

- Agilent N5182A MXG X-Series Signal Generator
- CW and ARB mode support
- Frequency/amplitude/output state control
- GPIB address format support
- PDTool4-compatible command interface"
```

---

## Task 3: Create Analog Discovery 2 Driver (Analog Functions)

**Files:**
- Create: `backend/app/services/instruments/analog_discovery_2.py`
- Create: `backend/app/services/instruments/dwf_constants.py` (WaveForms SDK constants)
- Modify: `backend/app/services/instruments/__init__.py`
- Test: `backend/tests/test_services/test_analog_discovery_2.py`

**Context:** AD2 is a USB oscilloscope/function generator using Digilent WaveForms SDK. Requires ctypes FFI to C API, supports analog I/O, digital I/O, and impedance measurements. This is the most complex driver due to SDK integration.

**Step 1: Create constants file**

```python
# app/services/instruments/dwf_constants.py

"""
Digilent WaveForms SDK Constants
Extracted from dwfconstants.h for Python ctypes
"""

# Device IDs
DEVID_EEXPLORER = 1
DEVID_DISCOVERY = 2
DEVID_DISCOVERY2 = 3
DEVID_DDISCOVERY = 4

# Acquisition states
STATE_READY = 0
STATE_CONFIG = 4
STATE_ARMED = 1
STATE_RUNNING = 3
STATE_DONE = 2

# Analog out function types
FUNC_DC = 0
FUNC_SINE = 1
FUNC_SQUARE = 2
FUNC_TRIANGLE = 3
FUNC_RAMP_UP = 4
FUNC_RAMP_DOWN = 5
FUNC_NOISE = 6
FUNC_PULSE = 7
FUNC_CUSTOM = 30
FUNC_PLAY = 31

# Analog out node types
ANALOG_OUT_NODE_CARRIER = 0
ANALOG_OUT_NODE_FM = 1
ANALOG_OUT_NODE_AM = 2

# Parameters
PARAM_ON_CLOSE = 4
PARAM_ANALOG_OUT = 7
```

**Step 2: Write the failing test**

```python
# tests/test_services/test_analog_discovery_2.py

import pytest
from app.services.instruments.analog_discovery_2 import AnalogDiscovery2Driver
from app.services.instrument_connection import SimulationInstrumentConnection
from app.core.instrument_config import InstrumentConfig

@pytest.fixture
def ad2_driver():
    """Create AD2 driver with simulation connection"""
    config = InstrumentConfig(
        id="AD2_1",
        type="ANALOG_DISCOVERY_2",
        name="Digilent Analog Discovery 2",
        connection=...  # USB connection type
    )
    conn = SimulationInstrumentConnection(config)
    driver = AnalogDiscovery2Driver(conn)
    return driver

@pytest.mark.asyncio
async def test_ad2_str_to_num(ad2_driver):
    """Test unit string conversion"""
    assert ad2_driver._str_to_num('100K') == 100000
    assert ad2_driver._str_to_num('10M') == 10000000
    assert ad2_driver._str_to_num('100u') == 0.0001

@pytest.mark.asyncio
async def test_ad2_select_function(ad2_driver):
    """Test function name selection"""
    assert ad2_driver._select_function('1') == 'Sine'
    assert ad2_driver._select_function('2') == 'Square'

@pytest.mark.asyncio
async def test_ad2_analog_out_simulation(ad2_driver):
    """Test analog output in simulation mode"""
    await ad2_driver.initialize()
    await ad2_driver.set_analog_out(
        channel=0,
        function='Sine',
        frequency=10000,
        amplitude=2.0,
        offset=0
    )
```

**Step 3: Write minimal implementation**

```python
# app/services/instruments/analog_discovery_2.py

"""
Analog Discovery 2 Instrument Driver

Digilent Analog Discovery 2 USB Oscilloscope/Function Generator
Uses WaveForms SDK via ctypes
"""
from typing import Dict, Any, Literal, Optional
from decimal import Decimal
import asyncio
import re
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param
from app.services.instruments.dwf_constants import (
    FUNC_SINE, FUNC_SQUARE, FUNC_TRIANGLE,
    ANALOG_OUT_NODE_CARRIER
)


class AnalogDiscovery2Driver(BaseInstrumentDriver):
    """
    Driver for Digilent Analog Discovery 2

    Supports:
    - Analog output (function generator)
    - Analog input (oscilloscope)
    - Digital I/O (16 channels)
    - Impedance measurement

    Note: Requires WaveForms SDK installation
    Uses ctypes for FFI to C API
    """

    # Function name mapping
    FUNCTION_NAMES = {
        '0': 'DC',
        '1': 'Sine',
        '2': 'Square',
        '3': 'Triangle',
        '4': 'RampUp',
        '5': 'RampDown',
        '6': 'Pulse',
        '7': 'SinePower',
        '8': 'Noise',
        '9': 'Custom',
        '10': 'Play',
    }

    def __init__(self, connection):
        super().__init__(connection)
        self._dwf = None
        self._hdwf = None

    async def initialize(self):
        """Initialize the instrument and load SDK"""
        try:
            # Try to load WaveForms SDK
            import sys
            if sys.platform.startswith("win"):
                from ctypes import cdll
                self._dwf = cdll.LoadLibrary("dwf.dll")
            elif sys.platform.startswith("darwin"):
                from ctypes import cdll
                self._dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
            else:
                from ctypes import cdll
                self._dwf = cdll.LoadLibrary("libdwf.so")

            self._open_device()
            self.logger.info("Analog Discovery 2 initialized")

        except (ImportError, OSError) as e:
            self.logger.warning(f"WaveForms SDK not available, using simulation mode: {e}")
            self._dwf = None

    async def reset(self):
        """Reset the instrument"""
        if self._hdwf:
            await self.write_command('*RST')
            self.logger.debug("AD2 reset")

    def _open_device(self):
        """Open first available AD2 device"""
        if not self._dwf:
            return

        from ctypes import c_int, byref

        hdwf = c_int()
        result = self._dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

        if result != 0:
            self._hdwf = hdwf
        else:
            self.logger.error("Failed to open Analog Discovery 2 device")

    def _str_to_num(self, num_str: str) -> float:
        """
        Convert string with unit suffix to float value

        Args:
            num_str: String like "100K", "10M", "100u"

        Returns:
            Numeric value
        """
        if not num_str:
            return 0.0

        num_str = num_str.strip()
        unit = num_str[-1].upper()

        multipliers = {
            'U': 1e-6,
            'μ': 1e-6,
            'M': 1e6,
            'K': 1e3,
        }

        if unit in multipliers:
            return float(num_str[:-1]) * multipliers[unit]

        # Try regex extraction
        match = re.findall(r'-?\d+\.?\d*', num_str)
        return float(match[0]) if match else 0.0

    def _select_function(self, index: str) -> str:
        """Convert function index to name"""
        return self.FUNCTION_NAMES.get(index, 'Sine')

    async def set_analog_out(
        self,
        channel: int,
        function: str,
        frequency: float,
        amplitude: float,
        offset: float
    ) -> None:
        """
        Configure analog output (function generator)

        Args:
            channel: Channel number (0 or 1)
            function: Waveform function name
            frequency: Frequency in Hz
            amplitude: Amplitude in V
            offset: DC offset in V
        """
        if not self._dwf or not self._hdwf:
            self.logger.debug(f"[SIMULATION] Set analog out CH{channel}: {function} {frequency}Hz {amplitude}V")
            return

        from ctypes import c_double

        # Set node and function
        self._dwf.FDwfAnalogOutNodeEnableSet(
            self._hdwf, channel, ANALOG_OUT_NODE_CARRIER, 1
        )

        func_code = getattr(self, f'FUNC_{function.upper()}', FUNC_SINE)
        self._dwf.FDwfAnalogOutNodeFunctionSet(
            self._hdwf, channel, ANALOG_OUT_NODE_CARRIER, func_code
        )

        # Set parameters
        self._dwf.FDwfAnalogOutNodeFrequencySet(
            self._hdwf, channel, ANALOG_OUT_NODE_CARRIER, c_double(frequency)
        )
        self._dwf.FDwfAnalogOutNodeAmplitudeSet(
            self._hdwf, channel, ANALOG_OUT_NODE_CARRIER, c_double(amplitude)
        )
        self._dwf.FDwfAnalogOutNodeOffsetSet(
            self._hdwf, channel, ANALOG_OUT_NODE_CARRIER, c_double(offset)
        )

        # Start output
        self._dwf.FDwfAnalogOutConfigure(self._hdwf, channel, 1)
        self.logger.debug(f"Set analog out CH{channel}: {function} {frequency}Hz {amplitude}V")

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Mode: 0=input, 1=output
                - Channel: Channel number
                - Function: Waveform function (for output)
                - Frequency: Frequency string
                - Amplitude: Amplitude string
                - Offset: Offset string

        Returns:
            Measurement result or status
        """
        mode = get_param(params, 'Mode', '0')

        if mode == '1':  # Output mode
            channel = int(get_param(params, 'Channel', '1')) - 1  # Convert to 0-based
            func_index = get_param(params, 'Function', '1')
            function = self._select_function(func_index)
            frequency = self._str_to_num(get_param(params, 'Frequency', '1K'))
            amplitude = self._str_to_num(get_param(params, 'Amplitude', '1'))
            offset = self._str_to_num(get_param(params, 'Offset', '0'))

            await self.set_analog_out(channel, function, frequency, amplitude, offset)
            return f"CH{channel + 1}: {function} {frequency}Hz {amplitude}V"

        else:
            # Input mode (oscilloscope) - not implemented in Phase 2
            raise NotImplementedError("Oscilloscope mode not implemented in Phase 2")
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/test_services/test_analog_discovery_2.py -v
```
Expected: PASS (simulation mode tests)

**Step 5: Update __init__.py**

```python
# app/services/instruments/__init__.py
from .analog_discovery_2 import AnalogDiscovery2Driver

INSTRUMENT_DRIVERS = {
    # ... existing entries ...
    'ANALOG_DISCOVERY_2': AnalogDiscovery2Driver,
}
```

**Step 6: Commit**

```bash
git add backend/app/services/instruments/analog_discovery_2.py \
        backend/app/services/instruments/dwf_constants.py \
        backend/app/services/instruments/__init__.py \
        backend/tests/test_services/test_analog_discovery_2.py
git commit -m "feat: add Analog Discovery 2 driver

- Digilent Analog Discovery 2 USB instrument
- Function generator support (Phase 2)
- Oscilloscope support (future phase)
- WaveForms SDK ctypes integration
- Simulation mode for testing"
```

---

## Task 4: Create FTM_On Driver (Factory Test Mode)

**Files:**
- Create: `backend/app/services/instruments/ftm_on.py`
- Modify: `backend/app/services/instruments/__init__.py`
- Test: `backend/tests/test_services/test_ftm_on.py`

**Context:** FTM_On is a WiFi RF testing module for Qualcomm chipsets. Uses ADB to communicate with Android device, loads FTM driver, and runs RF tests. This is a special-purpose instrument for manufacturing test.

**Step 1: Write the failing test**

```python
# tests/test_services/test_ftm_on.py

import pytest
from app.services.instruments.ftm_on import FTMOnDriver
from app.services.instrument_connection import SimulationInstrumentConnection
from app.core.instrument_config import InstrumentConfig

@pytest.fixture
def ftm_driver():
    """Create FTM driver with simulation connection"""
    config = InstrumentConfig(
        id="FTM_1",
        type="FTM_ON",
        name="WiFi FTM Test",
        connection=...  # Special connection type
    )
    conn = SimulationInstrumentConnection(config)
    driver = FTMOnDriver(conn)
    return driver

@pytest.mark.asyncio
async def test_ftm_open_mode(ftm_driver):
    """Test opening FTM mode"""
    await ftm_driver.initialize()
    result = await ftm_driver.open_ftm_mode()
    assert result is not None

@pytest.mark.asyncio
async def test_ftm_close_mode(ftm_driver):
    """Test closing FTM mode"""
    await ftm_driver.close_ftm_mode()

@pytest.mark.asyncio
async def test_ftm_execute_command(ftm_driver):
    """Test PDTool4-compatible command execution"""
    result = await ftm_driver.execute_command({
        'Command': 'python ./src/lowsheen_lib/RF_tool/FTM_On/PythonSubprocess_FTM_Entrance.py'
    })
    # In simulation mode, should return success
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_services/test_ftm_on.py -v
```
Expected: FAIL with "FTMOnDriver not found"

**Step 3: Write minimal implementation**

```python
# app/services/instruments/ftm_on.py

"""
FTM_On Instrument Driver

WiFi Factory Test Mode automation for Qualcomm chipsets
Uses ADB to communicate with Android device
"""
from typing import Dict, Any, Optional
import asyncio
import subprocess
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class FTMOnDriver(BaseInstrumentDriver):
    """
    Driver for WiFi FTM (Factory Test Mode) testing

    Supports:
    - Opening FTM mode (load FTM driver)
    - Closing FTM mode
    - TX power testing (Chain 1/2)

    Note: Requires ADB connection and Qualcomm device
    """

    async def initialize(self):
        """Initialize the driver"""
        self.logger.info("FTM_On driver initialized")
        # Note: Does NOT open FTM mode automatically
        # FTM mode should be opened via explicit command

    async def reset(self):
        """Reset - close FTM mode if open"""
        await self.close_ftm_mode()

    async def _run_adb_command(self, command: list[str]) -> str:
        """
        Run ADB command and return output

        Args:
            command: ADB command as list of strings

        Returns:
            Command output
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            return result.stdout.strip()
        except FileNotFoundError:
            self.logger.error("ADB not found in PATH")
            raise RuntimeError("ADB not found. Please install Android SDK platform-tools.")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"ADB command timed out: {' '.join(command)}")

    async def open_ftm_mode(self) -> str:
        """
        Open FTM mode on device

        Process:
        1. adb root
        2. adb remount
        3. adb shell rmmod qca6390
        4. adb shell insmod qca_cld3_*.ko con_mode_ftm=5
        5. adb shell ifconfig wlan0 up
        """
        steps = [
            ['adb', 'root'],
            ['adb', 'remount'],
            ['adb', 'shell', 'rmmod', 'qca6390'],
            ['adb', 'shell', 'insmod', 'vendor/lib/modules/qca_cld3_qca6390.ko', 'con_mode_ftm=5'],
            ['adb', 'shell', 'ifconfig', 'wlan0', 'up'],
        ]

        results = []
        for step in steps:
            output = await self._run_adb_command(step)
            results.append(output)
            self.logger.debug(f"FTM step: {' '.join(step)} -> {output}")

        self.logger.info("FTM mode opened")
        return "\n".join(results)

    async def close_ftm_mode(self) -> None:
        """
        Close FTM mode

        Note: Original PDTool4 implementation does NOT restore normal mode
        Device remains in FTM mode until reboot
        """
        self.logger.info("FTM mode close requested (device remains in FTM until reboot)")

    async def run_tx_test(self, chain: int = 1) -> str:
        """
        Run TX power test on specified chain

        Args:
            chain: TX chain (1 or 2)

        Returns:
            Test output
        """
        exe_path = f"./src/lowsheen_lib/RF_tool/FTM_On/API_WIFI_TxOn_chain{chain}_AutoDetect.exe"

        try:
            result = subprocess.run(
                [exe_path],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
                shell=True
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"TX test chain {chain} timed out")
        except FileNotFoundError:
            raise RuntimeError(f"TX test executable not found: {exe_path}")

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Command: Command to execute (script path)
                - Chain: TX chain (1 or 2)

        Returns:
            Command output
        """
        command = get_param(params, 'Command')

        if command:
            # Execute external command (PDTool4 pattern)
            self.logger.info(f"Executing FTM command: {command}")

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    shell=True,
                    check=False
                )
                return result.stdout.strip()
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"FTM command timed out: {command}")

        # Check for chain-specific TX test
        chain = get_param(params, 'Chain')
        if chain:
            return await self.run_tx_test(int(chain))

        raise ValueError("Missing required parameter: Command or Chain")
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/test_services/test_ftm_on.py -v
```
Expected: PASS (simulation mode)

**Step 5: Update __init__.py**

```python
# app/services/instruments/__init__.py
from .ftm_on import FTMOnDriver

INSTRUMENT_DRIVERS = {
    # ... existing entries ...
    'FTM_ON': FTMOnDriver,
}
```

**Step 6: Commit**

```bash
git add backend/app/services/instruments/ftm_on.py \
        backend/app/services/instruments/__init__.py \
        backend/tests/test_services/test_ftm_on.py
git commit -m "feat: add FTM_On driver for WiFi RF testing

- Factory Test Mode automation for Qualcomm chipsets
- ADB-based device communication
- TX power testing support (Chain 1/2)
- PDTool4-compatible command interface
- Special-purpose instrument for manufacturing test"
```

---

## Task 5: Update Documentation

**Files:**
- Modify: `docs/lowsheen_lib/Instrument_Implementation_Status.md`

**Step 1: Update status document**

Edit `docs/lowsheen_lib/Instrument_Implementation_Status.md` to reflect Phase 2 completion:

```markdown
# Update the statistics section
**統計資訊:**
- ✅ **已實現**: 15 個儀器服務 (新增 4 個)
- ❌ **待實現**: 11 個儀器/模組
- 📋 **特殊模組**: 3 個通訊協定文檔
- 📈 **完成度**: 57.7% (15/26)

# Update milestones section
- [x] **M4** - 通用介面層 (4/4) ✅ 已完成
- [x] **M5** - 常用測試儀器 (4/4) ✅ Phase 2 完成
- [ ] **M6** - 特殊應用儀器 (0/5) ⏳ Phase 3
```

**Step 2: Commit**

```bash
git add docs/lowsheen_lib/Instrument_Implementation_Status.md
git commit -m "docs: update instrument implementation status to 57.7%

- Phase 2 complete: 4 new instrument drivers
- APS7050, N5182A, Analog Discovery 2, FTM_On
- Updated progress tracking and milestones"
```

---

## Task 6: Update Configuration Examples

**Files:**
- Create: `backend/config/instruments_phase2_example.json`

**Step 1: Create example configuration**

```json
{
  "instruments": {
    "APS7050_1": {
      "type": "APS7050",
      "name": "GW Instek APS7050 AC/DC Power Source",
      "connection": {
        "type": "VISA",
        "address": "TCPIP0::192.168.1.50::inst0::INSTR",
        "timeout": 5000
      },
      "enabled": true,
      "description": "AC/DC power with built-in DMM and relay control"
    },
    "N5182A_1": {
      "type": "N5182A",
      "name": "Agilent N5182A MXG Signal Generator",
      "connection": {
        "type": "GPIB",
        "board": 0,
        "address": 16,
        "timeout": 5000
      },
      "enabled": true,
      "description": "RF signal generator with CW and ARB modes"
    },
    "AD2_1": {
      "type": "ANALOG_DISCOVERY_2",
      "name": "Digilent Analog Discovery 2",
      "connection": {
        "type": "USB",
        "address": "USB::0x03EB::0x2401::SN12345",
        "timeout": 5000
      },
      "enabled": false,
      "description": "USB oscilloscope and function generator"
    },
    "FTM_1": {
      "type": "FTM_ON",
      "name": "WiFi FTM Test Interface",
      "connection": {
        "type": "ADB",
        "address": "adb",
        "timeout": 30000
      },
      "enabled": false,
      "description": "WiFi RF testing via ADB"
    }
  }
}
```

**Step 2: Commit**

```bash
git add backend/config/instruments_phase2_example.json
git commit -m "docs: add Phase 2 instrument configuration examples

- APS7050 AC/DC power source configuration
- N5182A signal generator configuration
- Analog Discovery 2 USB configuration
- FTM_On ADB configuration"
```

---

## Verification Steps

After completing all tasks, run these verification commands:

```bash
# Run all Phase 2 tests
cd backend
pytest tests/test_services/test_aps7050.py \
       tests/test_services/test_n5182a.py \
       tests/test_services/test_analog_discovery_2.py \
       tests/test_services/test_ftm_on.py -v

# Run all instrument tests to ensure no regressions
pytest tests/test_services/ -k "instrument" -v

# Check import works
python -c "from app.services.instruments import APS7050Driver, N5182ADriver, AnalogDiscovery2Driver, FTMOnDriver; print('All imports OK')"
```

---

## Notes

1. **Simulation Mode**: All drivers support simulation mode for testing without hardware

2. **WaveForms SDK**: Analog Discovery 2 requires Digilent WaveForms SDK installation. The driver gracefully falls back to simulation mode if SDK is not available.

3. **ADB Dependency**: FTM_On requires Android SDK platform-tools (ADB) in system PATH

4. **Future Enhancements**:
   - AD2: Add oscilloscope mode (analog input)
   - AD2: Add digital I/O support
   - AD2: Add impedance measurement
   - N5182A: Add more waveform types

5. **Performance**: All operations use async/await to avoid blocking the event loop

---

**Total Estimated Tasks**: 6 main tasks
**Total Estimated Time**: 3-4 days (per original status document)
**Completion Milestone**: Phase 2 - 常用測試儀器 (擴充儀器庫) complete
**Progress Update**: 42.3% → 57.7%
