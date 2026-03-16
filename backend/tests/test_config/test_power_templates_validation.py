"""
Test PowerSet and PowerRead validation rules in MEASUREMENT_TEMPLATES.
Ensures all migrated instruments validate correctly via validate_params_config().
"""
import pytest
from app.config.instruments import validate_params, MEASUREMENT_TEMPLATES


class TestPowerSetTemplates:
    """Test PowerSet MEASUREMENT_TEMPLATES validation."""

    @pytest.mark.parametrize("instrument", [
        "DAQ973A", "MODEL2303", "MODEL2306", "IT6723C", "PSW3072",
        "2260B", "APS7050", "34970A", "KEITHLEY2015"
    ])
    def test_powerset_instrument_exists(self, instrument):
        """All PowerSet instruments should exist in MEASUREMENT_TEMPLATES."""
        assert "PowerSet" in MEASUREMENT_TEMPLATES
        assert instrument in MEASUREMENT_TEMPLATES["PowerSet"]

    def test_powerset_daq973a_valid_params(self):
        """DAQ973A PowerSet requires Instrument, Channel, Item."""
        result = validate_params("PowerSet", "DAQ973A", {
            "Instrument": "daq973a_1",
            "Channel": "101",
            "Item": "volt"
        })
        assert result["valid"] is True
        assert result["missing_params"] == []

    def test_powerset_daq973a_missing_required(self):
        """DAQ973A PowerSet with missing Channel should fail."""
        result = validate_params("PowerSet", "DAQ973A", {
            "Instrument": "daq973a_1",
            "Item": "volt"
        })
        assert result["valid"] is False
        assert "Channel" in result["missing_params"]

    @pytest.mark.parametrize("instrument", [
        "IT6723C", "PSW3072", "2260B"
    ])
    def test_powerset_volt_curr_instruments(self, instrument):
        """IT6723C, PSW3072, 2260B require Instrument, SetVolt, SetCurr."""
        result = validate_params("PowerSet", instrument, {
            "Instrument": f"{instrument.lower()}_1",
            "SetVolt": "5.0",
            "SetCurr": "1.0"
        })
        assert result["valid"] is True

    def test_powerset_aps7050_valid_params(self):
        """APS7050 PowerSet requires Instrument, Channel, SetVolt, SetCurr."""
        result = validate_params("PowerSet", "APS7050", {
            "Instrument": "aps7050_1",
            "Channel": "1",
            "SetVolt": "5.0",
            "SetCurr": "1.0"
        })
        assert result["valid"] is True

    def test_powerset_keithley2015_valid_params(self):
        """KEITHLEY2015 PowerSet requires Instrument, Command."""
        result = validate_params("PowerSet", "KEITHLEY2015", {
            "Instrument": "keithley2015_1",
            "Command": "SOURCE:VOLTAGE 5.0"
        })
        assert result["valid"] is True


class TestPowerReadTemplates:
    """Test PowerRead MEASUREMENT_TEMPLATES validation."""

    @pytest.mark.parametrize("instrument", [
        "DAQ973A", "34970A", "KEITHLEY2015", "2015", "6510",
        "APS7050", "MDO34", "MT8870A_INF"
    ])
    def test_powerread_instrument_exists(self, instrument):
        """All PowerRead instruments should exist in MEASUREMENT_TEMPLATES."""
        assert "PowerRead" in MEASUREMENT_TEMPLATES
        assert instrument in MEASUREMENT_TEMPLATES["PowerRead"]

    def test_powerread_daq973a_valid_params(self):
        """DAQ973A PowerRead requires Instrument, Channel, Item, Type."""
        result = validate_params("PowerRead", "DAQ973A", {
            "Instrument": "daq973a_1",
            "Channel": "101",
            "Item": "volt",
            "Type": "DC"
        })
        assert result["valid"] is True

    def test_powerread_2015_valid_params(self):
        """2015 PowerRead requires Instrument, Command."""
        result = validate_params("PowerRead", "2015", {
            "Instrument": "2015_1",
            "Command": "MEASURE:VOLTAGE?"
        })
        assert result["valid"] is True

    def test_powerread_6510_valid_params(self):
        """6510 PowerRead requires Instrument, Item."""
        result = validate_params("PowerRead", "6510", {
            "Instrument": "daq6510_1",
            "Item": "volt"
        })
        assert result["valid"] is True

    def test_powerread_aps7050_valid_params(self):
        """APS7050 PowerRead requires Instrument, Item."""
        result = validate_params("PowerRead", "APS7050", {
            "Instrument": "aps7050_1",
            "Item": "current"
        })
        assert result["valid"] is True

    def test_powerread_mdo34_valid_params(self):
        """MDO34 PowerRead requires Instrument, Channel, Item."""
        result = validate_params("PowerRead", "MDO34", {
            "Instrument": "mdo34_1",
            "Channel": "1",
            "Item": "volt"
        })
        assert result["valid"] is True

    def test_powerread_mt8870a_inf_valid_params(self):
        """MT8870A_INF PowerRead requires Instrument, Item."""
        result = validate_params("PowerRead", "MT8870A_INF", {
            "Instrument": "mt8870a_1",
            "Item": "power"
        })
        assert result["valid"] is True


class TestTemplateStructure:
    """Test MEASUREMENT_TEMPLATES structure completeness."""

    @pytest.mark.parametrize("instrument_type", ["PowerSet", "PowerRead"])
    def test_template_has_required_keys(self, instrument_type):
        """Each template should have required, optional, and example keys."""
        for instrument, template in MEASUREMENT_TEMPLATES[instrument_type].items():
            assert "required" in template
            assert "optional" in template
            assert "example" in template
            assert isinstance(template["required"], list)
            assert isinstance(template["optional"], list)
            assert isinstance(template["example"], dict)

    def test_powerset_all_instruments_accounted_for(self):
        """Verify all PowerSet instruments from legacy dict are now in MEASUREMENT_TEMPLATES."""
        # These were in the legacy validation_rules dict
        expected_instruments = [
            "DAQ973A", "MODEL2303", "MODEL2306", "IT6723C", "PSW3072",
            "2260B", "APS7050", "34970A", "KEITHLEY2015"
        ]
        actual_instruments = set(MEASUREMENT_TEMPLATES["PowerSet"].keys())
        assert set(expected_instruments) == actual_instruments

    def test_powerread_all_instruments_accounted_for(self):
        """Verify all PowerRead instruments from legacy dict are now in MEASUREMENT_TEMPLATES."""
        expected_instruments = [
            "DAQ973A", "34970A", "2015", "6510", "APS7050",
            "MDO34", "MT8870A_INF", "KEITHLEY2015"
        ]
        actual_instruments = set(MEASUREMENT_TEMPLATES["PowerRead"].keys())
        assert set(expected_instruments) == actual_instruments
