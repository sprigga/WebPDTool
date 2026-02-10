"""
Instrument and Measurement Configuration

Based on PDTool4's instrument configuration patterns.
Extracted from hardcoded dictionaries in measurements.py to improve maintainability.

REFACTORING UPDATE (2026-02-09):
- Added MEASUREMENT_TYPE_DESCRIPTIONS for test type metadata
- Added helper functions for dynamic configuration access
- Enables /types API to be generated dynamically from MEASUREMENT_TEMPLATES
"""

from typing import Dict, List, Any, Optional

# Available instruments by category
AVAILABLE_INSTRUMENTS = {
    "power_supplies": [
        {"id": "DAQ973A", "type": "DAQ973A", "description": "Keysight DAQ973A"},
        {"id": "MODEL2303", "type": "MODEL2303", "description": "Keysight Model 2303"},
        {"id": "MODEL2306", "type": "MODEL2306", "description": "Keysight Model 2306"},
        {"id": "IT6723C", "type": "IT6723C", "description": "ITECH IT6723C"},
        {"id": "PSW3072", "type": "PSW3072", "description": "Rigol PSW3072"},
        {"id": "2260B", "type": "2260B", "description": "Keysight 2260B"},
        {"id": "APS7050", "type": "APS7050", "description": "Agilent APS7050"}
    ],
    "multimeters": [
        {"id": "34970A", "type": "34970A", "description": "Keysight 34970A"},
        {"id": "DAQ6510", "type": "DAQ6510", "description": "Keysight DAQ6510"},
        {"id": "KEITHLEY2015", "type": "KEITHLEY2015", "description": "Keithley 2015 Multimeter"}
    ],
    "communication": [
        {"id": "comport", "type": "serial", "description": "Serial Port Communication"},
        {"id": "tcpip", "type": "tcpip", "description": "TCP/IP Communication"},
        {"id": "console", "type": "console", "description": "Console Command Execution"},
        {"id": "android_adb", "type": "adb", "description": "Android ADB Communication"}
    ],
    "rf_analyzers": [
        {"id": "MDO34", "type": "MDO34", "description": "Tektronix MDO34"},
        {"id": "MT8870A_INF", "type": "MT8870A", "description": "Anritsu MT8870A"}
    ]
}

# Measurement templates based on PDTool4's measurement module patterns
MEASUREMENT_TEMPLATES = {
    "PowerSet": {
        "DAQ973A": {
            "required": ["Instrument", "Channel", "Item"],
            "optional": ["Volt", "Curr", "Sense", "Range"],
            "example": {
                "Instrument": "daq973a_1",
                "Channel": "101",
                "Item": "volt",
                "Volt": "5.0",
                "Curr": "1.0"
            }
        },
        "MODEL2303": {
            "required": ["Instrument", "SetVolt", "SetCurr"],
            "optional": ["Channel", "OVP", "OCP"],
            "example": {
                "Instrument": "model2303_1",
                "SetVolt": "5.0",
                "SetCurr": "2.0"
            }
        },
        "MODEL2306": {
            "required": ["Instrument", "Channel", "SetVolt", "SetCurr"],
            "optional": ["OVP", "OCP", "Delay"],
            "example": {
                "Instrument": "model2306_1",
                "Channel": "1",
                "SetVolt": "5.0",
                "SetCurr": "2.0"
            }
        }
    },
    "PowerRead": {
        "DAQ973A": {
            "required": ["Instrument", "Channel", "Item", "Type"],
            "optional": ["Range", "NPLC"],
            "example": {
                "Instrument": "daq973a_1",
                "Channel": "101",
                "Item": "volt",
                "Type": "DC"
            }
        },
        "34970A": {
            "required": ["Instrument", "Channel", "Item"],
            "optional": ["Range", "NPLC"],
            "example": {
                "Instrument": "34970a_1",
                "Channel": "101",
                "Item": "volt"
            }
        },
        "KEITHLEY2015": {
            "required": ["Instrument", "Command"],
            "optional": ["Range", "NPLC"],
            "example": {
                "Instrument": "keithley2015_1",
                "Command": "READ?",
            }
        }
    },
    "CommandTest": {
        "comport": {
            "required": ["Port", "Baud", "Command"],
            "optional": ["keyWord", "spiltCount", "splitLength", "EqLimit"],
            "example": {
                "Port": "COM4",
                "Baud": "9600",
                "Command": "AT+VERSION",
                "keyWord": "VERSION",
                "spiltCount": "1",
                "splitLength": "10"
            }
        },
        "tcpip": {
            "required": ["Host", "Port", "Command"],
            "optional": ["keyWord", "spiltCount", "splitLength", "Timeout"],
            "example": {
                "Host": "192.168.1.100",
                "Port": "5025",
                "Command": "*IDN?",
                "Timeout": "5"
            }
        }
    },
    "SFCtest": {
        "default": {
            "required": ["Mode"],
            "optional": [],
            "example": {
                "Mode": "webStep1_2"
            }
        }
    },
    "getSN": {
        "default": {
            "required": ["Type"],
            "optional": ["SerialNumber"],
            "example": {
                "Type": "SN"
            }
        }
    },
    "OPjudge": {
        "default": {
            "required": ["Type"],
            "optional": ["Expected", "Result"],
            "example": {
                "Type": "YorN",
                "Expected": "PASS"
            }
        }
    },
    "Other": {
        # 修正方案 A: 加入特殊測試類型作為 switch_mode 選項
        # 這些選項原本散落在 case_type 欄位,現在統一到 switch_mode
        "script": {
            # 自訂腳本模式 (預設)
            "required": [],
            "optional": [],
            "example": {}
        },
        "wait": {
            # 等待測試類型
            "required": [],
            "optional": ["wait_msec", "WaitmSec"],
            "example": {"wait_msec": "1000"}
        },
        "relay": {
            # 繼電器控制
            "required": ["RelayName", "Action"],
            "optional": [],
            "example": {"RelayName": "RELAY_1", "Action": "ON"}
        },
        "chassis_rotation": {
            # 底盤旋轉控制
            "required": ["Action"],
            "optional": ["Angle", "Speed"],
            "example": {"Action": "ROTATE", "Angle": "90"}
        },
        "console": {
            # 控制台命令執行
            "required": ["Command"],
            "optional": ["keyWord", "spiltCount", "splitLength", "Timeout"],
            "example": {"Command": "echo test", "Timeout": "5"}
        },
        "comport": {
            # 串口通訊 (作為 Other 的一種模式)
            "required": ["Port", "Baud", "Command"],
            "optional": ["keyWord", "spiltCount", "splitLength"],
            "example": {"Port": "COM4", "Baud": "9600", "Command": "AT+VERSION"}
        },
        "tcpip": {
            # TCP/IP 通訊 (作為 Other 的一種模式)
            "required": ["Host", "Port", "Command"],
            "optional": ["keyWord", "Timeout"],
            "example": {"Host": "192.168.1.100", "Port": "5025", "Command": "*IDN?"}
        }
    },
    "Wait": {
        "default": {
            "required": ["wait_msec"],
            "optional": ["WaitmSec"],
            "example": {
                "wait_msec": "1000"
            }
        }
    },
    "Relay": {
        "default": {
            "required": ["RelayName", "Action"],
            "optional": [],
            "example": {
                "RelayName": "RELAY_1",
                "Action": "ON"
            }
        }
    }
}

# Measurement type descriptions (used for API documentation and UI display)
# 原有程式碼: 這些描述散落在 measurements.py 的硬編碼中
# 修改: 集中管理測試類型的元數據
MEASUREMENT_TYPE_DESCRIPTIONS = {
    "PowerSet": {
        "name": "PowerSet",
        "description": "Power supply voltage/current setting",
        "category": "power"
    },
    "PowerRead": {
        "name": "PowerRead",
        "description": "Voltage/current measurement reading",
        "category": "power"
    },
    "CommandTest": {
        "name": "CommandTest",
        "description": "Serial/network command execution",
        "category": "communication"
    },
    "SFCtest": {
        "name": "SFCtest",
        "description": "SFC integration testing",
        "category": "integration"
    },
    "getSN": {
        "name": "getSN",
        "description": "Serial number acquisition",
        "category": "identification"
    },
    "OPjudge": {
        "name": "OPjudge",
        "description": "Operator judgment/confirmation",
        "category": "manual"
    },
    "Other": {
        "name": "Other",
        "description": "Custom measurement implementations",
        "category": "custom"
    },
    "Wait": {
        "name": "Wait",
        "description": "Wait/delay operation",
        "category": "utility"
    },
    "Relay": {
        "name": "Relay",
        "description": "Relay control operation",
        "category": "utility"
    }
}


# ============================================================================
# Helper Functions for Dynamic Configuration Access
# ============================================================================

def get_measurement_types() -> List[Dict[str, Any]]:
    """
    Get all measurement types with their supported instruments.

    動態從 MEASUREMENT_TEMPLATES 生成測試類型清單，
    替代原本在 API 層的硬編碼實作。

    Returns:
        List of measurement type dictionaries with structure:
        {
            "name": str,
            "description": str,
            "category": str,
            "supported_switches": List[str]
        }
    """
    measurement_types = []

    for test_type, instruments in MEASUREMENT_TEMPLATES.items():
        # Get metadata from MEASUREMENT_TYPE_DESCRIPTIONS
        metadata = MEASUREMENT_TYPE_DESCRIPTIONS.get(test_type, {
            "name": test_type,
            "description": f"{test_type} measurement",
            "category": "unknown"
        })

        measurement_types.append({
            "name": metadata["name"],
            "description": metadata["description"],
            "category": metadata.get("category", "unknown"),
            "supported_switches": list(instruments.keys())
        })

    return measurement_types


def get_template(measurement_type: str, switch_mode: str) -> Optional[Dict[str, Any]]:
    """
    Get measurement template for specific type and switch mode.

    Args:
        measurement_type: Test type (PowerSet, PowerRead, etc.)
        switch_mode: Instrument/switch mode (DAQ973A, MODEL2303, etc.)

    Returns:
        Template dictionary with 'required', 'optional', 'example' keys,
        or None if combination not found
    """
    return MEASUREMENT_TEMPLATES.get(measurement_type, {}).get(switch_mode)


def validate_params(
    measurement_type: str,
    switch_mode: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate measurement parameters against template.

    Args:
        measurement_type: Test type
        switch_mode: Instrument mode
        params: Parameters to validate

    Returns:
        Validation result dictionary:
        {
            "valid": bool,
            "missing_params": List[str],
            "invalid_params": List[str],
            "suggestions": List[str]
        }
    """
    template = get_template(measurement_type, switch_mode)

    if not template:
        return {
            "valid": False,
            "missing_params": [],
            "invalid_params": [],
            "suggestions": [
                f"Unsupported combination: {measurement_type} + {switch_mode}",
                f"Available switches for {measurement_type}: {list(MEASUREMENT_TEMPLATES.get(measurement_type, {}).keys())}"
            ]
        }

    # Check required parameters
    required = template.get("required", [])
    missing = [param for param in required if param not in params or params[param] in (None, "")]

    # Check for unknown parameters (not in required or optional)
    optional = template.get("optional", [])
    valid_params = set(required + optional)
    invalid = [param for param in params.keys() if param not in valid_params]

    # Generate suggestions
    suggestions = []
    if missing:
        example = template.get("example", {})
        for param in missing:
            if param in example:
                suggestions.append(f"Parameter '{param}' example: {example[param]}")

    return {
        "valid": len(missing) == 0,
        "missing_params": missing,
        "invalid_params": invalid,
        "suggestions": suggestions
    }


def get_all_instruments() -> Dict[str, List[Dict[str, str]]]:
    """
    Get all available instruments grouped by category.

    Returns:
        AVAILABLE_INSTRUMENTS dictionary
    """
    return AVAILABLE_INSTRUMENTS


def get_instruments_by_category(category: str) -> List[Dict[str, str]]:
    """
    Get instruments for a specific category.

    Args:
        category: Category name (power_supplies, multimeters, communication, rf_analyzers)

    Returns:
        List of instrument dictionaries
    """
    return AVAILABLE_INSTRUMENTS.get(category, [])
