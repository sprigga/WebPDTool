"""
Instrument and Measurement Configuration

Based on PDTool4's instrument configuration patterns.
Extracted from hardcoded dictionaries in measurements.py to improve maintainability.
"""

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
    }
}
