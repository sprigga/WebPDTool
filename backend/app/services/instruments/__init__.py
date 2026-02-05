"""
Modern Instrument Drivers Package

Refactored from PDTool4's src/lowsheen_lib/ scripts
Each instrument now uses object-oriented design with async support
"""
from app.services.instruments.base import BaseInstrumentDriver
from app.services.instruments.daq973a import DAQ973ADriver
from app.services.instruments.model2303 import MODEL2303Driver
from app.services.instruments.a34970a import A34970ADriver
from app.services.instruments.model2306 import MODEL2306Driver
from app.services.instruments.it6723c import IT6723CDriver
from app.services.instruments.a2260b import A2260BDriver
from app.services.instruments.daq6510 import DAQ6510Driver
from app.services.instruments.psw3072 import PSW3072Driver
from app.services.instruments.keithley2015 import KEITHLEY2015Driver
from app.services.instruments.mdo34 import MDO34Driver
from app.services.instruments.aps7050 import APS7050Driver
from app.services.instruments.n5182a import N5182ADriver
from app.services.instruments.analog_discovery_2 import AnalogDiscovery2Driver
from app.services.instruments.ftm_on import FTMOnDriver
# Phase 3 RF Instrument Drivers
from app.services.instruments.cmw100 import CMW100Driver
from app.services.instruments.mt8872a import MT8872ADriver
# Phase 3 Low Priority Instrument Drivers
from app.services.instruments.l6mpu_ssh import L6MPUSSHDriver
from app.services.instruments.l6mpu_ssh_comport import L6MPUSSHComPortDriver
from app.services.instruments.l6mpu_pos_ssh import L6MPUPOSSHDriver
from app.services.instruments.peak_can import PEAKCANDriver
from app.services.instruments.smcv100b import SMCV100BDriver

__all__ = [
    "BaseInstrumentDriver",
    "DAQ973ADriver",
    "MODEL2303Driver",
    "A34970ADriver",
    "MODEL2306Driver",
    "IT6723CDriver",
    "A2260BDriver",
    "DAQ6510Driver",
    "PSW3072Driver",
    "KEITHLEY2015Driver",
    "MDO34Driver",
    "APS7050Driver",
    "N5182ADriver",
    "AnalogDiscovery2Driver",
    "FTMOnDriver",
    # Phase 3 RF drivers
    "CMW100Driver",
    "MT8872ADriver",
    # Phase 3 Low Priority drivers
    "L6MPUSSHDriver",
    "L6MPUSSHComPortDriver",
    "L6MPUPOSSHDriver",
    "PEAKCANDriver",
    "SMCV100BDriver",
]


# Instrument driver registry
INSTRUMENT_DRIVERS = {
    "DAQ973A": DAQ973ADriver,
    "MODEL2303": MODEL2303Driver,
    "34970A": A34970ADriver,
    "MODEL2306": MODEL2306Driver,
    "IT6723C": IT6723CDriver,
    "2260B": A2260BDriver,
    "DAQ6510": DAQ6510Driver,
    "PSW3072": PSW3072Driver,
    "KEITHLEY2015": KEITHLEY2015Driver,
    "MDO34": MDO34Driver,
    "APS7050": APS7050Driver,
    "N5182A": N5182ADriver,
    "ANALOG_DISCOVERY_2": AnalogDiscovery2Driver,
    "AD2": AnalogDiscovery2Driver,
    "FTM_ON": FTMOnDriver,
    # Phase 3 RF Instrument Drivers
    "CMW100": CMW100Driver,
    "MT8872A": MT8872ADriver,
    "RF_TOOL": MT8872ADriver,  # Alternative naming for MT8872A
    # Phase 3 Low Priority Instrument Drivers
    "L6MPU_SSH": L6MPUSSHDriver,
    "L6MPU": L6MPUSSHDriver,  # Short name
    "L6MPU_SSH_COMPORT": L6MPUSSHComPortDriver,
    "L6MPU_POS_SSH": L6MPUPOSSHDriver,
    "PEAK_CAN": PEAKCANDriver,
    "PCAN": PEAKCANDriver,  # Alternative naming
    "SMCV100B": SMCV100BDriver,
    # Add more as they are migrated
}


def get_driver_class(instrument_type: str):
    """Get driver class by instrument type"""
    return INSTRUMENT_DRIVERS.get(instrument_type)
