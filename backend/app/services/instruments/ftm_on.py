"""
FTM_On Instrument Driver

WiFi Factory Test Mode automation for Qualcomm chipsets
Uses ADB to communicate with Android device
"""
from typing import Dict, Any
import asyncio
import subprocess
from app.services.instruments.base import BaseInstrumentDriver, get_param


class FTMOnDriver(BaseInstrumentDriver):
    """
    Driver for WiFi FTM (Factory Test Mode) testing

    Supports:
    - Opening FTM mode (load FTM driver)
    - Closing FTM mode
    - TX power testing (Chain 1/2)

    Note: Requires ADB connection and Qualcomm device
    """

    async def initialize(self):
        """Initialize the driver"""
        self.logger.info("FTM_On driver initialized")
        # Note: Does NOT open FTM mode automatically
        # FTM mode should be opened via explicit command

    async def reset(self):
        """Reset - close FTM mode if open"""
        await self.close_ftm_mode()

    async def _run_adb_command(self, command: list[str]) -> str:
        """
        Run ADB command and return output

        Args:
            command: ADB command as list of strings

        Returns:
            Command output
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            return result.stdout.strip()
        except FileNotFoundError:
            self.logger.error("ADB not found in PATH")
            raise RuntimeError("ADB not found. Please install Android SDK platform-tools.")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"ADB command timed out: {' '.join(command)}")

    async def open_ftm_mode(self) -> str:
        """
        Open FTM mode on device

        Process:
        1. adb root
        2. adb remount
        3. adb shell rmmod qca6390
        4. adb shell insmod qca_cld3_*.ko con_mode_ftm=5
        5. adb shell ifconfig wlan0 up
        """
        steps = [
            ['adb', 'root'],
            ['adb', 'remount'],
            ['adb', 'shell', 'rmmod', 'qca6390'],
            ['adb', 'shell', 'insmod', 'vendor/lib/modules/qca_cld3_qca6390.ko', 'con_mode_ftm=5'],
            ['adb', 'shell', 'ifconfig', 'wlan0', 'up'],
        ]

        results = []
        for step in steps:
            output = await self._run_adb_command(step)
            results.append(output)
            self.logger.debug(f"FTM step: {' '.join(step)} -> {output}")

        self.logger.info("FTM mode opened")
        return "\n".join(results)

    async def close_ftm_mode(self) -> None:
        """
        Close FTM mode

        Note: Original PDTool4 implementation does NOT restore normal mode
        Device remains in FTM mode until reboot
        """
        self.logger.info("FTM mode close requested (device remains in FTM until reboot)")

    async def run_tx_test(self, chain: int = 1) -> str:
        """
        Run TX power test on specified chain

        Args:
            chain: TX chain (1 or 2)

        Returns:
            Test output
        """
        exe_path = f"./src/lowsheen_lib/RF_tool/FTM_On/API_WIFI_TxOn_chain{chain}_AutoDetect.exe"

        try:
            result = subprocess.run(
                [exe_path],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
                shell=True
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"TX test chain {chain} timed out")
        except FileNotFoundError:
            raise RuntimeError(f"TX test executable not found: {exe_path}")

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute instrument command with PDTool4-compatible interface

        Args:
            params: Command parameters
                - Command: Command to execute (script path)
                - Chain: TX chain (1 or 2)

        Returns:
            Command output
        """
        command = get_param(params, 'Command')

        if command:
            # Execute external command (PDTool4 pattern)
            self.logger.info(f"Executing FTM command: {command}")

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    shell=True,
                    check=False
                )
                return result.stdout.strip()
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"FTM command timed out: {command}")

        # Check for chain-specific TX test
        chain = get_param(params, 'Chain')
        if chain:
            return await self.run_tx_test(int(chain))

        raise ValueError("Missing required parameter: Command or Chain")
