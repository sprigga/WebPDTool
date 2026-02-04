"""
Digilent WaveForms SDK Constants

WaveForms SDK ctypes integration for Digilent Analog Discovery 2
"""
from typing import Dict


# Function Name Mapping (WaveForms API indices to human-readable names)
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
}

FUNCTION_NAME_TO_INDEX: Dict[str, str] = {v: k for k, v in FUNCTION_NAMES.items()}


# Analog Output Channels
AOUT_CHANNELS = {
    '0': 'CH1',
    '1': 'CH2',
}

AOUT_CHANNEL_INDICES = {
    'CH1': 0,
    'CH2': 1,
}
