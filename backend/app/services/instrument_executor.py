"""
Instrument Executor Service

Bridge between measurement_service and modern instrument drivers
Provides backward compatibility with PDTool4-style subprocess execution
while using new async instrument drivers internally
"""
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

from app.services.instrument_connection import get_connection_pool, InstrumentNotFoundError
from app.services.instruments import get_driver_class
from app.core.instrument_config import get_instrument_settings


logger = logging.getLogger(__name__)


class InstrumentExecutor:
    """
    Instrument command executor

    Provides two execution modes:
    1. Modern: Direct async driver calls (preferred)
    2. Legacy: Subprocess execution for backward compatibility
    """

    def __init__(self):
        self.connection_pool = get_connection_pool()
        self.instrument_settings = get_instrument_settings()
        self.logger = logging.getLogger(self.__class__.__name__)

    # ========================================================================
    # Modern Execution (using async drivers)
    # ========================================================================

    async def execute_instrument_command(
        self,
        instrument_id: str,
        params: Dict[str, Any],
        simulation: bool = False
    ) -> str:
        """
        Execute instrument command using modern async drivers

        Args:
            instrument_id: Instrument identifier (e.g., 'DAQ973A_1')
            params: Command parameters dictionary
            simulation: Force simulation mode

        Returns:
            Command result as string (for backward compatibility)

        Raises:
            InstrumentNotFoundError: Instrument not found in configuration
            ValueError: Invalid parameters
            Exception: Execution error
        """
        try:
            # Get instrument configuration
            config = self.instrument_settings.get_instrument(instrument_id)
            if config is None:
                raise InstrumentNotFoundError(
                    f"Instrument {instrument_id} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                # Fall back to legacy execution
                self.logger.warning(
                    f"No modern driver for {config.type}, falling back to legacy execution"
                )
                return await self._execute_legacy_script(
                    instrument_id=instrument_id,
                    instrument_type=config.type,
                    params=params
                )

            # Use connection pool to get connection
            async with self.connection_pool.get_connection(instrument_id, simulation=simulation) as conn:
                # Create driver instance
                driver = driver_class(conn)

                # Initialize if not already done
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute command
                result = await driver.execute_command(params)
                self.logger.info(f"Executed command on {instrument_id}: {result}")

                return result

        except InstrumentNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute command on {instrument_id}: {e}")
            raise

    async def reset_instrument(self, instrument_id: str):
        """
        Reset instrument (cleanup operation)

        Args:
            instrument_id: Instrument identifier
        """
        try:
            config = self.instrument_settings.get_instrument(instrument_id)
            if config is None:
                self.logger.warning(f"Instrument {instrument_id} not found for reset")
                return

            driver_class = get_driver_class(config.type)
            if driver_class is None:
                # Fall back to legacy reset
                self.logger.warning(
                    f"No modern driver for {config.type}, skipping reset"
                )
                return

            async with self.connection_pool.get_connection(instrument_id) as conn:
                driver = driver_class(conn)
                await driver.reset()
                self.logger.info(f"Reset instrument {instrument_id}")

        except Exception as e:
            self.logger.error(f"Failed to reset instrument {instrument_id}: {e}")

    # ========================================================================
    # Legacy Execution (subprocess for backward compatibility)
    # ========================================================================

    async def _execute_legacy_script(
        self,
        instrument_id: str,
        instrument_type: str,
        params: Dict[str, Any],
        test_point_id: str = "test",
        timeout: int = 30
    ) -> str:
        """
        Execute legacy instrument script via subprocess

        This is used for instruments that haven't been migrated to
        modern drivers yet, or as a fallback mechanism.

        Args:
            instrument_id: Instrument identifier
            instrument_type: Instrument type
            params: Command parameters
            test_point_id: Test point ID (for script compatibility)
            timeout: Execution timeout in seconds

        Returns:
            Script output
        """
        import subprocess
        import json

        # Map instrument types to script files
        script_map = {
            'DAQ973A': 'DAQ973A_test.py',
            '34970A': '34970A.py',
            'APS7050': 'APS7050.py',
            'MDO34': 'MDO34.py',
            'KEITHLEY2015': 'Keithley2015.py',
            'MT8870A_INF': 'RF_tool/MT8872A_INF.py',
            'MODEL2303': '2303_test.py',
            'MODEL2306': '2306_test.py',
            'DAQ6510': 'DAQ6510.py',
            '2260B': '2260B.py',
            'IT6723C': 'IT6723C.py',
            'PSW3072': 'PSW3072.py',
            'ComPort': 'ComPortCommand.py',
            'Console': 'ConSoleCommand.py',
            'TCPIP': 'TCPIPCommand.py',
        }

        script_file = script_map.get(instrument_type)
        if script_file is None:
            raise ValueError(f"Unknown instrument type: {instrument_type}")

        script_path = f"./src/lowsheen_lib/{script_file}"

        # Add Instrument parameter if not present
        if 'Instrument' not in params:
            params['Instrument'] = instrument_id

        # Convert params to string (PDTool4 format)
        params_str = str(params)

        self.logger.info(
            f"Executing legacy script: {script_path} with params: {params_str}"
        )

        try:
            # Execute subprocess
            result = subprocess.run(
                ['python3', script_path, test_point_id, params_str],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            # Check return code
            if result.returncode == 10:
                raise InstrumentNotFoundError(
                    f"Instrument {instrument_id} not found (exit code 10)"
                )
            elif result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else f"Exit code {result.returncode}"
                raise Exception(f"Script execution failed: {error_msg}")

            # Return stdout
            output = result.stdout.strip()
            self.logger.info(f"Legacy script output: {output}")
            return output

        except subprocess.TimeoutExpired:
            raise Exception(f"Script execution timeout after {timeout}s")
        except FileNotFoundError:
            raise Exception(f"Script not found: {script_path}")

    # ========================================================================
    # Batch Operations
    # ========================================================================

    async def cleanup_instruments(self, instrument_ids: list[str]):
        """
        Cleanup multiple instruments

        Args:
            instrument_ids: List of instrument IDs to cleanup
        """
        for inst_id in instrument_ids:
            try:
                await self.reset_instrument(inst_id)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {inst_id}: {e}")


# ============================================================================
# Global Executor Instance
# ============================================================================

_instrument_executor: Optional[InstrumentExecutor] = None


def get_instrument_executor() -> InstrumentExecutor:
    """Get global instrument executor instance"""
    global _instrument_executor
    if _instrument_executor is None:
        _instrument_executor = InstrumentExecutor()
    return _instrument_executor
