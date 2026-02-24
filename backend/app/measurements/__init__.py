"""
Measurement Modules Package
Exports base classes and implementations
"""
from app.measurements.base import (
    BaseMeasurement,
    MeasurementResult,
)
from app.measurements.implementations import (
    DummyMeasurement,
    # CommandTestMeasurement,  # 已棄用，由 ComPortMeasurement/ConSoleMeasurement/TCPIPMeasurement 取代
    PowerReadMeasurement,
    PowerSetMeasurement,
    get_measurement_class,
    MEASUREMENT_REGISTRY
)

__all__ = [
    "BaseMeasurement",
    "MeasurementResult",
    "DummyMeasurement",
    # "CommandTestMeasurement",  # 已棄用
    "PowerReadMeasurement",
    "PowerSetMeasurement",
    "get_measurement_class",
    "MEASUREMENT_REGISTRY"
]
