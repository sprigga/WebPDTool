"""Unit tests for Instrument Pydantic schemas."""
import pytest
from pydantic import ValidationError
from app.schemas.instrument import InstrumentCreate, InstrumentUpdate, InstrumentResponse


def test_instrument_create_visa():
    data = InstrumentCreate(
        instrument_id="DAQ973A_1",
        instrument_type="DAQ973A",
        name="Keysight DAQ973A",
        conn_type="VISA",
        conn_params={"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000},
        enabled=True,
    )
    assert data.conn_type == "VISA"


def test_instrument_create_invalid_conn_type():
    with pytest.raises(ValidationError):
        InstrumentCreate(
            instrument_id="X",
            instrument_type="X",
            name="X",
            conn_type="INVALID_TYPE",
            conn_params={},
        )


def test_instrument_update_partial():
    upd = InstrumentUpdate(enabled=False)
    assert upd.enabled is False
    assert upd.name is None


def test_instrument_response_from_orm():
    from datetime import datetime

    class FakeOrm:
        id = 1
        instrument_id = "DAQ973A_1"
        instrument_type = "DAQ973A"
        name = "Test"
        conn_type = "VISA"
        conn_params = {"address": "TCPIP0::..."}
        enabled = True
        description = None
        created_at = datetime.now()
        updated_at = datetime.now()

    resp = InstrumentResponse.model_validate(FakeOrm())
    assert resp.instrument_id == "DAQ973A_1"
