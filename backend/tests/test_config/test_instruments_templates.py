# backend/tests/test_config/test_instruments_templates.py
import pytest
from app.config.instruments import MEASUREMENT_TEMPLATES, validate_params, get_template


class TestCommandTestTemplates:
    # 已移除: CommandTest/command 的 custom switch_mode 與 console test_type 功能完全相同，
    # 已從 MEASUREMENT_TEMPLATES 移除以避免 UI 下拉選單出現無意義選項。
    # 後端 MEASUREMENT_REGISTRY 仍保留向下相容映射（不影響 CSV 匯入）。

    def test_commandtest_not_in_templates(self):
        """CommandTest 已從 MEASUREMENT_TEMPLATES 移除，不應出現在 UI 測試類型下拉選單中。"""
        assert "CommandTest" not in MEASUREMENT_TEMPLATES

    def test_command_not_in_templates(self):
        """command 已從 MEASUREMENT_TEMPLATES 移除，不應出現在 UI 測試類型下拉選單中。"""
        assert "command" not in MEASUREMENT_TEMPLATES


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

    # 方案 A: test123/WAIT_FIX_5sec/chassis_rotation 已從 Other switch_mode 移除
    def test_other_only_script_mode(self):
        """Other 只保留 script switch_mode，其餘已移除。"""
        assert set(MEASUREMENT_TEMPLATES["Other"].keys()) == {"script"}

    def test_other_test123_not_in_templates(self):
        """test123 是客製腳本名稱，不應出現在 Other switch_mode 中。"""
        assert "test123" not in MEASUREMENT_TEMPLATES["Other"]

    def test_other_wait_fix_not_in_templates(self):
        """WAIT_FIX_5sec 是客製腳本名稱且與 Wait 重複，不應出現在 Other switch_mode 中。"""
        assert "WAIT_FIX_5sec" not in MEASUREMENT_TEMPLATES["Other"]

    def test_other_chassis_rotation_not_in_templates(self):
        """chassis_rotation 已是獨立頂層 test_type，不應出現在 Other switch_mode 中。"""
        assert "chassis_rotation" not in MEASUREMENT_TEMPLATES["Other"]

    def test_other_script_mode_exists(self):
        """script 是 Other 唯一保留的 switch_mode。"""
        assert "script" in MEASUREMENT_TEMPLATES["Other"]

    def test_other_script_validate_no_required(self):
        result = validate_params("Other", "script", {})
        assert result["valid"] is True


class TestValidateParamsEndToEnd:
    """Regression: validate_params() in instruments.py (primary path) handles all migrated types."""

    def test_console_uses_primary_path(self):
        from app.config.instruments import validate_params
        # 修正: CommandTest/command 已從 MEASUREMENT_TEMPLATES 移除，改用 console 驗證主要路徑
        result = validate_params("console", "console", {"Instrument": "console_1", "Command": "echo test"})
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
