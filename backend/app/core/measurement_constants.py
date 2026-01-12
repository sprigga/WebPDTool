"""
Measurement-related Constants and Configurations

Centralized measurement configurations from measurement_service.py
to reduce duplication and improve maintainability.
"""

from typing import Dict, List


# =============================================================================
# Instrument Script Mappings
# =============================================================================

INSTRUMENT_SCRIPTS: Dict[str, str] = {
    "DAQ973A": "DAQ973A_test.py",
    "MODEL2303": "2303_test.py",
    "MODEL2306": "2306_test.py",
    "IT6723C": "IT6723C.py",
    "PSW3072": "PSW3072.py",
    "2260B": "2260B.py",
    "APS7050": "APS7050.py",
    "34970A": "34970A.py",
    "KEITHLEY2015": "Keithley2015.py",
    "DAQ6510": "DAQ6510.py",
    "MDO34": "MDO34.py",
    "MT8872A_INF": "MT8872A_INF.py",
}


# =============================================================================
# Command Test Script Configurations
# =============================================================================

COMMAND_SCRIPT_CONFIGS: Dict[str, Dict[str, object]] = {
    "comport": {
        "script": "ComPortCommand.py",
        "required_params": ["Port", "Baud", "Command"],
    },
    "console": {
        "script": "ConSoleCommand.py",
        "required_params": ["Command"],
    },
    "tcpip": {
        "script": "TCPIPCommand.py",
        "required_params": ["Command"],
    },
    "PEAK": {
        "script": "PEAK_API/PEAK.py",
        "required_params": ["Command"],
    },
    "android_adb": {
        "script": "AndroidAdbCommand.py",
        "required_params": ["Command"],
    },
}


# =============================================================================
# Power Set Required Parameters
# =============================================================================

POWER_SET_PARAMS: Dict[str, List[str]] = {
    "DAQ973A": ["Instrument", "Channel", "Item"],
    "MODEL2303": ["Instrument", "SetVolt", "SetCurr"],
    "MODEL2306": ["Instrument", "Channel", "SetVolt", "SetCurr"],
    "IT6723C": ["Instrument", "SetVolt", "SetCurr"],
    "PSW3072": ["Instrument", "SetVolt", "SetCurr"],
    "2260B": ["Instrument", "SetVolt", "SetCurr"],
    "APS7050": ["Instrument", "Channel", "SetVolt", "SetCurr"],
    "34970A": ["Instrument", "Channel", "Item"],
    "KEITHLEY2015": ["Instrument", "Command"],
}


# =============================================================================
# Power Read Required Parameters
# =============================================================================

POWER_READ_PARAMS: Dict[str, List[str]] = {
    "DAQ973A": ["Instrument", "Channel", "Item", "Type"],
    "34970A": ["Instrument", "Channel", "Item"],
    "2015": ["Instrument", "Command"],
    "6510": ["Instrument", "Item"],
    "APS7050": ["Instrument", "Item"],
    "MDO34": ["Instrument", "Channel", "Item"],
    "MT8870A_INF": ["Instrument", "Item"],
    "KEITHLEY2015": ["Instrument", "Command"],
}


# =============================================================================
# SFC Test Switch Modes
# =============================================================================

SFC_SWITCH_MODES: List[str] = [
    "webStep1_2",
    "URLStep1_2",
    "skip",
    "WAIT_FIX_5sec",
]


# =============================================================================
# Serial Number Switch Modes
# =============================================================================

SN_SWITCH_MODES: List[str] = [
    "SN",
    "IMEI",
    "MAC",
]


# =============================================================================
# Operator Judgment Switch Modes
# =============================================================================

OP_JUDGE_SWITCH_MODES: List[str] = [
    "YorN",
    "confirm",
]


# =============================================================================
# Default Timeout Values
# =============================================================================

DEFAULT_COMMAND_TIMEOUT_MS = 30000  # 30 seconds
DEFAULT_WAIT_MSEC = 0


# =============================================================================
# Script Paths (relative to backend directory or lobsheen_lib)
# =============================================================================

LOWSHEEN_LIB_PATH = "./src/lowsheen_lib"
RF_TOOL_PATH = "./src/lowsheen_lib/RF_tool"


# =============================================================================
# Measurement Dispatch Configuration
# =============================================================================
# This maps measurement types to their handler method names
# Used in MeasurementService.measurement_dispatch

MEASUREMENT_DISPATCH_MAP: Dict[str, str] = {
    "PowerSet": "_execute_power_set",
    "PowerRead": "_execute_power_read",
    "CommandTest": "_execute_command_test",
    "command": "_execute_command_test",
    "SFCtest": "_execute_sfc_test",
    "URL": "_execute_sfc_test",
    "webStep1_2": "_execute_sfc_test",
    "comport": "_execute_command_test",
    "console": "_execute_command_test",
    "tcpip": "_execute_command_test",
    "android_adb": "_execute_command_test",
    "PEAK": "_execute_command_test",
    "getSN": "_execute_get_sn",
    "OPjudge": "_execute_op_judge",
    "wait": "_execute_wait",
    "Wait": "_execute_wait",
    "Other": "_execute_other",
    "Final": "_execute_final",
}
