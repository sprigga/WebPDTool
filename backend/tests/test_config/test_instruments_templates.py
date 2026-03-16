# backend/tests/test_config/test_instruments_templates.py
import pytest
from app.config.instruments import MEASUREMENT_TEMPLATES, validate_params, get_template


class TestCommandTestTemplates:
    def test_commandtest_comport_template_exists(self):
        assert "CommandTest" in MEASUREMENT_TEMPLATES
        assert "comport" in MEASUREMENT_TEMPLATES["CommandTest"]

    def test_commandtest_comport_required_params(self):
        tmpl = get_template("CommandTest", "comport")
        assert tmpl is not None
        assert set(["Port", "Baud", "Command"]).issubset(set(tmpl["required"]))

    def test_commandtest_tcpip_required_params(self):
        tmpl = get_template("CommandTest", "tcpip")
        assert tmpl is not None
        assert set(["Host", "Port", "Command"]).issubset(set(tmpl["required"]))

    def test_commandtest_console_required_params(self):
        tmpl = get_template("CommandTest", "console")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_commandtest_android_adb_required_params(self):
        tmpl = get_template("CommandTest", "android_adb")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_commandtest_peak_required_params(self):
        tmpl = get_template("CommandTest", "PEAK")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_commandtest_custom_no_required(self):
        tmpl = get_template("CommandTest", "custom")
        assert tmpl is not None
        assert tmpl["required"] == [] or "command" not in tmpl["required"]

    def test_command_alias_same_as_commandtest(self):
        """'command' measurement_type must mirror CommandTest: same modes and same required params."""
        assert "command" in MEASUREMENT_TEMPLATES
        for mode in ["comport", "tcpip", "console", "android_adb", "PEAK", "custom"]:
            assert mode in MEASUREMENT_TEMPLATES["command"], f"Missing mode: {mode}"
            ct_required = MEASUREMENT_TEMPLATES["CommandTest"][mode]["required"]
            cmd_required = MEASUREMENT_TEMPLATES["command"][mode]["required"]
            assert ct_required == cmd_required, (
                f"Mode '{mode}' required params differ: CommandTest={ct_required}, command={cmd_required}"
            )

    def test_validate_params_commandtest_comport_valid(self):
        result = validate_params("CommandTest", "comport", {
            "Port": "COM4", "Baud": "9600", "Command": "AT+VERSION"
        })
        assert result["valid"] is True

    def test_validate_params_commandtest_comport_missing(self):
        result = validate_params("CommandTest", "comport", {"Port": "COM4"})
        assert result["valid"] is False
        assert "Baud" in result["missing_params"] or "Command" in result["missing_params"]

    def test_validate_params_command_tcpip_valid(self):
        result = validate_params("command", "tcpip", {
            "Host": "192.168.1.1", "Port": "5025", "Command": "*IDN?"
        })
        assert result["valid"] is True


class TestAndroidAdbPeakTopLevel:
    def test_android_adb_top_level_exists(self):
        assert "android_adb" in MEASUREMENT_TEMPLATES

    def test_android_adb_mode_required(self):
        tmpl = get_template("android_adb", "android_adb")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_android_adb_validate_valid(self):
        result = validate_params("android_adb", "android_adb", {"Command": "adb shell ls"})
        assert result["valid"] is True

    def test_android_adb_validate_missing_command(self):
        result = validate_params("android_adb", "android_adb", {})
        assert result["valid"] is False

    def test_peak_top_level_exists(self):
        assert "PEAK" in MEASUREMENT_TEMPLATES

    def test_peak_mode_required(self):
        tmpl = get_template("PEAK", "PEAK")
        assert tmpl is not None
        assert "Command" in tmpl["required"]

    def test_peak_validate_valid(self):
        result = validate_params("PEAK", "PEAK", {"Command": "send:0x01"})
        assert result["valid"] is True

    def test_android_adb_custom_mode_exists(self):
        assert "custom" in MEASUREMENT_TEMPLATES["android_adb"]

    def test_peak_custom_mode_exists(self):
        assert "custom" in MEASUREMENT_TEMPLATES["PEAK"]


class TestSFCtestGetSNModes:
    def test_sfctest_webstep_mode_exists(self):
        assert "webStep1_2" in MEASUREMENT_TEMPLATES["SFCtest"]

    def test_sfctest_urlstep_mode_exists(self):
        assert "URLStep1_2" in MEASUREMENT_TEMPLATES["SFCtest"]

    def test_sfctest_skip_mode_exists(self):
        assert "skip" in MEASUREMENT_TEMPLATES["SFCtest"]

    def test_sfctest_wait_fix_mode_exists(self):
        assert "WAIT_FIX_5sec" in MEASUREMENT_TEMPLATES["SFCtest"]

    def test_sfctest_webstep_validate_no_required(self):
        result = validate_params("SFCtest", "webStep1_2", {})
        assert result["valid"] is True

    def test_getsn_sn_mode_exists(self):
        assert "SN" in MEASUREMENT_TEMPLATES["getSN"]

    def test_getsn_imei_mode_exists(self):
        assert "IMEI" in MEASUREMENT_TEMPLATES["getSN"]

    def test_getsn_mac_mode_exists(self):
        assert "MAC" in MEASUREMENT_TEMPLATES["getSN"]

    def test_getsn_sn_validate_no_required(self):
        result = validate_params("getSN", "SN", {})
        assert result["valid"] is True


class TestWaitAndOtherModes:
    def test_wait_lowercase_top_level_exists(self):
        assert "wait" in MEASUREMENT_TEMPLATES

    def test_wait_lowercase_mode_exists(self):
        assert "wait" in MEASUREMENT_TEMPLATES["wait"]

    def test_wait_lowercase_validate_no_required(self):
        result = validate_params("wait", "wait", {})
        assert result["valid"] is True

    def test_other_test123_mode_exists(self):
        assert "test123" in MEASUREMENT_TEMPLATES["Other"]

    def test_other_wait_fix_mode_exists(self):
        assert "WAIT_FIX_5sec" in MEASUREMENT_TEMPLATES["Other"]

    def test_other_test123_validate_no_required(self):
        result = validate_params("Other", "test123", {})
        assert result["valid"] is True

    def test_other_wait_fix_validate_no_required(self):
        result = validate_params("Other", "WAIT_FIX_5sec", {})
        assert result["valid"] is True


class TestValidateParamsEndToEnd:
    """Regression: validate_params() in instruments.py (primary path) handles all migrated types."""

    def test_commandtest_uses_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("CommandTest", "comport", {
            "Port": "COM4", "Baud": "9600", "Command": "AT"
        })
        assert result["valid"] is True
        assert not any("Legacy" in s for s in result.get("suggestions", []))

    def test_sfctest_webstep_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("SFCtest", "webStep1_2", {})
        assert result["valid"] is True
        assert not any("Legacy" in s for s in result.get("suggestions", []))

    def test_getsn_sn_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("getSN", "SN", {})
        assert result["valid"] is True

    def test_wait_lowercase_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("wait", "wait", {})
        assert result["valid"] is True

    def test_android_adb_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("android_adb", "android_adb", {"Command": "adb shell ls"})
        assert result["valid"] is True

    def test_peak_primary_path(self):
        from app.config.instruments import validate_params
        result = validate_params("PEAK", "PEAK", {"Command": "send:0x01"})
        assert result["valid"] is True
