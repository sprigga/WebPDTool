# XCU Control Board CAN/LIN Test Plan Analysis

**Test Plan File:** `XCU_ControlBoard_CANLIN_testPlan.csv`
**Project:** Magpie
**Analysis Date:** 2025-02-06

## Table of Contents

1. [Column Definitions](#column-definitions)
2. [Test Flow Analysis](#test-flow-analysis)
3. [Code Mapping](#code-mapping)
4. [Test Cases Breakdown](#test-cases-breakdown)

---

## 1. Column Definitions

| Column | Type | Description | Example Value | Required |
|--------|------|-------------|---------------|----------|
| **ID** | string | Unique test step identifier | `Power_3072_1_on`, `SOC_CAN1` | Yes |
| **ItemKey** | string | Test item specification code (e.g., FT00-075) | `FT00-075`, `FT00-07` | Yes |
| **ValueType** | string | Data type for validation: `string`, `integer`, `float` | `string`, `none` | Yes |
| **LimitType** | string | Validation rule type | See [Limit Types](#limit-types) | Yes |
| **EqLimit** | string | Expected value for equality/inequality checks | `1`, `ID:001h` | No |
| **LL** | float | Lower limit value | - | No |
| **UL** | float | Upper limit value | - | No |
| **PassOrFail** | string | Test result status (auto-filled) | - | No |
| **measureValue** | string | Actual measured value (auto-filled) | - | No |
| **ExecuteName** | string | Measurement class to execute | `PowerSet`, `CommandTest`, `Other` | Yes |
| **case** | string | Execution target/console | `PSW3072`, `console` | No |
| **Command** | string | Command string to execute | `python .\\src\\lowsheen_lib\\XCU\\UART.py...` | No |
| **Timeout** | integer | Maximum execution time in seconds | `60`, `180` | No |
| **UseResult** | string | How to use execution result | - | No |
| **WaitmSec** | integer | Wait time after execution (milliseconds) | `2000`, `500` | No |
| **Instrument** | string | Target instrument identifier | `PSW3072`, `34970A` | No |
| **SetVolt** | float | Voltage to set (PowerSet) | `12` | No |
| **SetCurr** | float | Current to set (PowerSet) | `2` | No |
| **Channel** | string | Instrument channel number | `101`, `102`, `103` | No |
| **Item** | string | Sub-item identifier | `clos`, `open` | No |
| **keyWord** | string | Additional keyword parameter | - | No |
| **spiltCount** | integer | Split count parameter | - | No |
| **splitLength** | integer | Split length parameter | - | No |

### Limit Types

| Limit Type | Description | Validation Logic |
|------------|-------------|------------------|
| `equality` | Exact match required | `measured_value == EqLimit` |
| `inequality` | Must NOT equal | `measured_value != EqLimit` |
| `partial` | Substring match (strings) | `EqLimit in measured_value` |
| `lower` | Lower bound only | `measured_value >= LL` |
| `upper` | Upper bound only | `measured_value <= UL` |
| `both` | Range check | `LL <= measured_value <= UL` |
| `none` | No validation | Always passes |

### ExecuteName Types

| ExecuteName | Purpose | Example Usage |
|-------------|---------|---------------|
| `PowerSet` | Set power supply voltage/current | PSW3072 power initialization |
| `Other` / `wait` | Wait/delay operation | `WaitmSec` specifies delay |
| `CommandTest` | Execute command and validate output | CAN/LIN communication tests |

---

## 2. Test Flow Analysis

### Phase 1: Power Initialization (Steps 1-2)

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Power_3072_1_on                                      │
│   - ExecuteName: PowerSet                                    │
│   - Instrument: PSW3072                                      │
│   - SetVolt: 12V                                             │
│   - SetCurr: 2A                                              │
├─────────────────────────────────────────────────────────────┤
│ Step 2: WAIT_DUT_ON                                         │
│   - ExecuteName: Other (wait)                                │
│   - WaitmSec: 2000ms                                         │
└─────────────────────────────────────────────────────────────┘
```

**Purpose:** Power up the Device Under Test (DUT) and allow stabilization.

### Phase 2: CAN Communication Test (Steps 3-26)

**Pattern for Each CAN Channel (1-8):**

```
┌─────────────────────────────────────────────────────────────┐
│ SOC_CAN<x>: Send enable command via UART                    │
│   - Command: llcecan <x> 150                                 │
│   - LimitType: partial (expect "llcecan <x> 150" in output)  │
├─────────────────────────────────────────────────────────────┤
│ WAIT<x>: Brief delay                                        │
│   - WaitmSec: 500ms                                         │
├─────────────────────────────────────────────────────────────┤
│ CAN<x>: Verify CAN communication                            │
│   - Command: consolePEAK.py (channel-specific)              │
│   - LimitType: partial (expect "ID:00<x>h")                  │
│   - Timeout: 60 seconds                                     │
└─────────────────────────────────────────────────────────────┘
```

**CAN Channel Variations:**
- **CAN1, CAN2:** Channel 1 & 2, standard `consolePEAK.py`
- **CAN3:** Uses `consolePEAK_channel3_250k.py` (250k baud rate)
- **CAN4, CAN5, CAN6:** Channels 4-6 on bus 2
- **CAN7, CAN8:** Uses `consolePEAK34.py` (PEAK CAN 3-4 hardware)

### Phase 3: LIN Communication Test (Steps 27-38)

**Pattern for Each LIN Channel (1-3):**

```
┌─────────────────────────────────────────────────────────────┐
│ relay_lin<x>_clos: Close relay for LIN test                 │
│   - Instrument: 34970A                                       │
│   - Channel: 10<x> (101, 102, 103)                          │
│   - Item: clos (close relay)                                │
├─────────────────────────────────────────────────────────────┤
│ SOC_LIN<x>: Send LIN enable command                         │
│   - Command: llcelin <x> 150                                 │
├─────────────────────────────────────────────────────────────┤
│ LIN<x>: Verify LIN communication                            │
│   - Command: consolePEAK.py LIN mode                        │
│   - Expect: 0x3<x> (LIN ID)                                 │
│   - Timeout: 180 seconds (longer than CAN)                  │
├─────────────────────────────────────────────────────────────┤
│ relay_lin<x>_open: Open relay after test                    │
│   - Channel: 10<x>                                          │
│   - Item: open                                              │
└─────────────────────────────────────────────────────────────┘
```

### Test Flow Summary

```
Power On (12V/2A) → Wait 2s
    ↓
┌───────────────────────────────────────────────┐
│ CAN Test Loop (8 channels)                     │
│  For each channel:                             │
│    1. Send enable command (UART)               │
│    2. Wait 500ms                               │
│    3. Verify CAN ID (PEAK CAN tool)            │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│ LIN Test Loop (3 channels)                     │
│  For each channel:                             │
│    1. Close relay                              │
│    2. Send enable command (UART)               │
│    3. Verify LIN ID (PEAK CAN tool)            │
│    4. Open relay                               │
└───────────────────────────────────────────────┘
```

---

## 3. Code Mapping

### Backend Implementation Files

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **CSV Parser** | `backend/app/utils/csv_parser.py` | Parses CSV into database models |
| **Measurement Base** | `backend/app/measurements/base.py` | Validation logic (LimitType) |
| **PowerSet** | `backend/app/measurements/implementations.py` | Power supply control |
| **CommandTest** | `backend/app/measurements/implementations.py` | Command execution |
| **Other (wait)** | `backend/app/measurements/implementations.py` | Delay operations |
| **Test Engine** | `backend/app/services/test_engine.py` | Orchestrates execution |
| **Instrument Manager** | `backend/app/services/instrument_manager.py` | Hardware connection pool |

### Mapping: CSV → Backend

#### PowerSet Mapping

```python
# CSV Row 1: Power_3072_1_on
{
    "ExecuteName": "PowerSet",
    "Instrument": "PSW3072",
    "SetVolt": 12,
    "SetCurr": 2,
    "case": "PSW3072_1"
}

# Maps to backend/app/measurements/implementations.py:
class PowerSet(BaseMeasurement):
    async def execute(self, params):
        instrument = params.get('Instrument')  # "PSW3072"
        voltage = params.get('SetVolt')        # 12
        current = params.get('SetCurr')        # 2
        channel = params.get('case')           # "PSW3072_1"

        # Instrument Manager resolves to actual hardware
        driver = await self.instrument_manager.get_driver(instrument)
        await driver.set_voltage(voltage)
        await driver.set_current(current)
```

#### CommandTest Mapping

```python
# CSV Row 4: SOC_CAN1
{
    "ExecuteName": "CommandTest",
    "Command": "python .\\src\\lowsheen_lib\\XCU\\UART.py COM3 command:[llcecan 1 150]",
    "Timeout": 60,
    "LimitType": "partial",
    "EqLimit": "llcecan 1 150"
}

# Maps to validation in base.py:
def validate_result(self, measured_value, limit_type='partial', eq_limit):
    if limit_type == 'partial':
        return eq_limit in measured_value
```

#### Relay Control (34970A)

```python
# CSV Row 27: relay_lin1_clos
{
    "ExecuteName": "PowerSet",
    "Instrument": "34970A",
    "Channel": "101",
    "Item": "clos"  # or "open"
}

# This uses the same PowerSet measurement but with relay-specific params
# The 34970A is a multiplexer/relay switch instrument
```

### Database Schema Mapping

```sql
-- Test Plan Structure
test_plans
├── id (primary key)
├── project_id → projects
├── station_id → stations
├── name (e.g., "XCU_ControlBoard_CANLIN")
└── created_at

-- Test Items (each CSV row)
test_items
├── id
├── test_plan_id → test_plans
├── item_key (ItemKey: FT00-075)
├── execute_name (ExecuteName: PowerSet)
├── parameters (JSON: {SetVolt: 12, SetCurr: 2})
├── value_type (ValueType: string)
├── limit_type (LimitType: equality)
├── eq_limit (EqLimit: 1)
├── lower_limit (LL)
├── upper_limit (UL)
└── timeout (Timeout: 60)

-- Test Results (execution output)
test_results
├── id
├── session_id → test_sessions
├── test_item_id → test_items
├── measured_value (measureValue)
├── pass_fail (PassOrFail)
├── executed_at
└── error_message
```

---

## 4. Test Cases Breakdown

### Summary Statistics

| Category | Count | Notes |
|----------|-------|-------|
| **Total Test Steps** | 38 | 2 power + 26 CAN + 9 LIN |
| **CAN Channels** | 8 | CAN1-CAN8 |
| **LIN Channels** | 3 | LIN1-LIN3 |
| **Power Supplies** | 1 | PSW3072 (12V/2A) |
| **Relay Modules** | 1 | 34970A (3 channels) |
| **Total Execution Time** | ~10 min | Including timeouts and waits |

### Test Step Details

| Step | ID | Description | Timeout | Wait |
|------|-----|-------------|---------|------|
| 1 | Power_3072_1_on | Initialize power supply | - | - |
| 2 | WAIT_DUT_ON | DUT stabilization | - | 2000ms |
| 3-26 | SOC_CAN<x>, CAN<x> | CAN communication test | 60s | 500ms |
| 27-38 | relay_lin<x>, LIN<x> | LIN communication test | 180s | - |

### Expected Outputs

| Test Type | Expected Pattern | Example |
|-----------|------------------|---------|
| CAN Enable | `llcecan <ch> 150` | "llcecan 1 150" |
| CAN Verify | `ID:00<ch>h` | "ID:001h" for CAN1 |
| LIN Enable | `llcelin <ch> 150` | "llcelin 1 150" |
| LIN Verify | `0x3<ch>` | "0x31" for LIN1 |

---

## Appendix: CSV Structure Reference

### Complete CSV Header
```csv
ID,ItemKey,ValueType,LimitType,EqLimit,LL,UL,PassOrFail,measureValue,ExecuteName,case,Command,Timeout,UseResult,WaitmSec,Instrument,SetVolt,SetCurr,Channel,Item,keyWord,spiltCount,splitLength
```

### Sample Row (PowerSet)
```csv
Power_3072_1_on,FT00-075,string,equality,1,,,,,PowerSet,PSW3072,,,,,PSW3072_1,12,2,,,,,
```

### Sample Row (CommandTest - CAN)
```csv
SOC_CAN1,,string,partial,llcecan 1 150,,,,,CommandTest,console,python .\\src\\lowsheen_lib\\XCU\\UART.py COM3 command:[llcecan 1 150],60,,,,,,,,,,
```

### Sample Row (Relay Control)
```csv
relay_lin1_clos,,string,equality,1,,,,,PowerSet,34970A,,,,,34970A_1,,,101,clos,,,
```

---

*Generated from: `backend/testplans/Magpie/XCU_ControlBoard_CANLIN_testPlan.csv`*
