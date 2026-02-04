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
    # Add more as they are migrated
}


def get_driver_class(instrument_type: str):
    """Get driver class by instrument type"""
    return INSTRUMENT_DRIVERS.get(instrument_type)
