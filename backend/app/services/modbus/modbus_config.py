"""
Modbus Configuration Helper
Converts between database models and service configuration
"""
from typing import Dict, Any


def modbus_config_to_dict(config) -> Dict[str, Any]:
    """
    Convert ModbusConfig (model or schema) to dictionary format expected by listener

    Args:
        config: ModbusConfig database model or ModbusConfigResponse schema

    Returns:
        Dictionary with modbus_scheme keys (matching PDTool4 format)
    """
    return {
        "ready_status_Add": config.ready_status_address,
        "ready_status_Len": hex(config.ready_status_length),
        "read_sn_Add": config.read_sn_address,
        "read_sn_Len": hex(config.read_sn_length),
        "test_status_Add": config.test_status_address,
        "test_status_Len": hex(config.test_status_length),
        "in_testing_Val": config.in_testing_value,
        "test_finished_Val": config.test_finished_value,
        "test_result_Add": config.test_result_address,
        "test_result_Len": hex(config.test_result_length),
        "test_no_Result": config.test_no_result,
        "test_pass_Val": config.test_pass_value,
        "test_fail_Val": config.test_fail_value,
        "simulation_Mode": "1" if config.simulation_mode else "0",
        "Delay": str(int(config.delay_seconds))
    }


def str2hex(hex_str: str) -> int:
    """Convert hex string to integer"""
    return int(hex_str, 16)
