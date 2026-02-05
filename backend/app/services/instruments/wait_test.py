"""
Wait Test Instrument Driver

Programmable delay utility for test sequence timing control
Supports millisecond-precision delays with validation
"""
import asyncio
import logging
from typing import Dict, Any

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class WaitTestDriver(BaseInstrumentDriver):
    """
    Wait/delay utility driver for test sequence timing control

    Supports:
    - Millisecond-precision delays
    - Dynamic and fixed wait times
    - Wait cancellation support
    - Input validation
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize Wait test driver"""
        super().__init__(connection)
        self.default_wait_ms = 1000
        self.min_wait_ms = 0
        self.max_wait_ms = 3600000  # 1 hour
        self.cancel_event = None

    async def initialize(self):
        """Initialize Wait test driver"""
        # Get limits from config or connection object
        # Check both config and connection for compatibility with tests
        self.min_wait_ms = getattr(self.connection.config, 'min_wait_ms',
                                    getattr(self.connection, 'min_wait_ms', 0))
        self.max_wait_ms = getattr(self.connection.config, 'max_wait_ms',
                                    getattr(self.connection, 'max_wait_ms', 3600000))

        self.logger.info("Wait test driver initialized")

    async def reset(self):
        """Reset (cancel any pending wait)"""
        if self.cancel_event:
            self.cancel_event.set()
            self.cancel_event = None
        self.logger.debug("Wait test reset")

    def _validate_wait_time(self, wait_ms: int) -> tuple[bool, str]:
        """
        Validate wait time parameter

        Args:
            wait_ms: Wait time in milliseconds

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(wait_ms, (int, float)):
            return False, "WaitmSec must be numeric"

        wait_ms = int(wait_ms)

        if wait_ms < self.min_wait_ms:
            return False, f"WaitmSec cannot be less than {self.min_wait_ms}"

        if wait_ms > self.max_wait_ms:
            return False, f"WaitmSec exceeds maximum ({self.max_wait_ms}ms = {self.max_wait_ms/1000}s)"

        if wait_ms == 0:
            return False, "WaitmSec cannot be zero"

        return True, None

    async def _wait_with_cancel(self, wait_sec: float) -> bool:
        """
        Wait with cancellation support

        Args:
            wait_sec: Wait time in seconds

        Returns:
            True if wait completed, False if cancelled
        """
        if self.cancel_event is None:
            self.cancel_event = asyncio.Event()
        else:
            self.cancel_event.clear()

        try:
            await asyncio.wait_for(
                self.cancel_event.wait(),
                timeout=wait_sec
            )
            # Event was set (cancelled)
            return False
        except asyncio.TimeoutError:
            # Timeout completed (normal wait)
            return True

    async def send_command(self, params: Dict[str, Any]) -> str:
        """
        Execute wait operation

        Parameters in params dict:
            - WaitmSec (int, required): Wait duration in milliseconds
            - OutputFormat (str, optional): Format for output message
                - 'seconds': Show seconds only (default)
                - 'ms': Show milliseconds only
                - 'both': Show both seconds and ms

        Returns:
            Wait completion message
        """
        # Validate required parameters
        validate_required_params(params, ['WaitmSec'])

        # Get parameters
        wait_ms = get_param(params, 'WaitmSec', 'wait_ms', 'waitmsec', 'wait')
        output_format = get_param(params, 'OutputFormat', 'output_format', 'format', default='seconds')

        # Convert to integer
        try:
            wait_ms = int(wait_ms)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid WaitmSec value: {wait_ms}")

        # Validate wait time
        is_valid, error_msg = self._validate_wait_time(wait_ms)
        if not is_valid:
            raise ValueError(error_msg)

        # Convert to seconds
        wait_sec = wait_ms / 1000.0

        self.logger.info(f"Waiting {wait_ms}ms ({wait_sec}s)")

        # Perform non-blocking wait
        await asyncio.sleep(wait_sec)

        # Format output message
        if output_format == 'ms':
            response = f"Waited for {wait_ms} ms"
        elif output_format == 'both':
            response = f"Waited for {wait_sec} secs ({wait_ms} ms)"
        else:  # 'seconds' (default)
            response = f"Waited for {wait_sec} secs"

        self.logger.info(response)
        return response

    async def query_command(self, wait_ms: int) -> str:
        """
        Query command (execute wait)

        Args:
            wait_ms: Wait duration in milliseconds

        Returns:
            Wait completion message
        """
        params = {'WaitmSec': wait_ms}
        return await self.send_command(params)

    async def wait_dynamic(self, callback, max_wait_ms: int = 10000,
                          poll_interval_ms: int = 100) -> str:
        """
        Dynamic wait based on callback condition

        Waits until callback returns True or max_wait_ms is reached.

        Args:
            callback: Async function that returns bool
            max_wait_ms: Maximum wait time in milliseconds
            poll_interval_ms: Polling interval in milliseconds

        Returns:
            Wait completion message with actual wait time
        """
        import time
        start_time = time.time()
        max_wait_sec = max_wait_ms / 1000.0
        poll_interval_sec = poll_interval_ms / 1000.0

        self.logger.info(f"Dynamic wait started (max {max_wait_ms}ms)")

        while True:
            # Check callback condition
            if await callback():
                elapsed_ms = int((time.time() - start_time) * 1000)
                response = f"Condition met after {elapsed_ms} ms"
                self.logger.info(response)
                return response

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= max_wait_sec:
                response = f"Timeout after {max_wait_ms} ms (condition not met)"
                self.logger.warning(response)
                return response

            # Wait before next poll
            await asyncio.sleep(poll_interval_sec)

    async def wait_between(self, min_ms: int, max_ms: int) -> str:
        """
        Wait for random duration between min and max

        Useful for jitter/dither in test timing.

        Args:
            min_ms: Minimum wait time in milliseconds
            max_ms: Maximum wait time in milliseconds

        Returns:
            Wait completion message
        """
        import random

        if min_ms >= max_ms:
            raise ValueError(f"min_ms ({min_ms}) must be less than max_ms ({max_ms})")

        wait_ms = random.randint(min_ms, max_ms)
        self.logger.info(f"Random wait: {wait_ms}ms (range: {min_ms}-{max_ms}ms)")

        return await self.query_command(wait_ms)

    async def close(self):
        """Close Wait test driver"""
        if self.cancel_event:
            self.cancel_event.set()
            self.cancel_event = None
        self.logger.debug("Wait test driver closed")
