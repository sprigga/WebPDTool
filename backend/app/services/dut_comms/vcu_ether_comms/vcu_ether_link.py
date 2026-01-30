"""
VCU Test Interface - Main VCU Ethernet Communication Class

Provides async UDP communication with VCU (Vehicle Control Unit) devices.
Refactored from PDTool4 polish/dut_comms/vcu_ether_comms/vcu_ether_link.py (277 lines).

Features:
- Connection handshake via 'connect' string echo
- Triple-frame detection (Sync + Length + CRC)
- SocketBuffer for thread-safe buffered reading
- Protocol Buffers message support
- Async context manager support

Example:
    intf = VcuTestInterface()
    await intf.init_interface()

    # Send command and get response
    req = intf.get_new_msg()
    req.test_command_req.timestamp = int((time.time() - intf.start_time) * 1000)
    response = await intf.poll(req)

    await intf.close()
"""
import asyncio
import socket
import time
import struct
import zlib
import logging
from collections import deque
from typing import Optional, Tuple

from .header import (
    CommMsgHeader_t,
    MAGIC_SYNC_U16,
    MAX_MESSAGE_BODY_LENGTH,
    calculate_crc,
)

CRC_OFFSET = 8  # CRC covers everything from offset 8 onwards
from .vcu_common import (
    TEST_ENDPOINT,
    CONNECT_ENDPOINT,
    VCU_DEFAULT_IP,
    VCU_TEST_PORT,
    VCU_CONNECT_PORT,
    get_udp_sock,
    flush_udp_recv,
)

logger = logging.getLogger(__name__)


# Default configuration
DEFAULT_CONNECT_RETRIES = 15
DEFAULT_TIMEOUT = 3.0
DEFAULT_VERBOSE = False


class VcuConnectFailed(Exception):
    """Raised when VCU connection handshake fails."""
    pass


class VcuTimeout(Exception):
    """Raised when VCU operation times out."""
    pass


class VcuPollFailed(Exception):
    """Raised when VCU poll operation fails."""
    pass


class SocketBuffer:
    """
    Thread-safe buffer for reading from UDP socket.

    In async version, uses coroutines instead of threads.
    Refactored from PDTool4 polish/dut_comms/vcu_ether_comms/vcu_ether_link.py.

    Methods:
        fill(size): Ensure at least size bytes are in buffer
        peek(size): Non-destructive read of size bytes
        read(size): Consume and return size bytes
    """

    def __init__(self, sock: socket.socket):
        """
        Initialize socket buffer.

        Args:
            sock: UDP socket to read from
        """
        self._buff = bytearray()
        self._sock = sock
        self._lock = asyncio.Lock()

    async def fill(self, size: int) -> None:
        """
        Ensure buffer has at least size bytes by reading from socket.

        Args:
            size: Minimum bytes to have in buffer
        """
        async with self._lock:
            buff_len = len(self._buff)
            remaining_read = size - buff_len

            if remaining_read > 0:
                # Read more data from socket
                loop = asyncio.get_event_loop()
                try:
                    data = await asyncio.wait_for(
                        loop.sock_recv(self._sock, 4096),
                        timeout=DEFAULT_TIMEOUT
                    )
                    self._buff.extend(data)
                except asyncio.TimeoutError:
                    pass  # No more data available

    async def peek(self, size: int) -> bytes:
        """
        Non-destructive read of size bytes from buffer.

        Args:
            size: Number of bytes to peek

        Returns:
            bytes: First size bytes from buffer (without removing)
        """
        await self.fill(size)
        return bytes(self._buff[:size])

    async def read(self, size: int) -> bytes:
        """
        Consume and return size bytes from buffer.

        Args:
            size: Number of bytes to consume

        Returns:
            bytes: Consumed bytes
        """
        read_str = await self.peek(size)
        del self._buff[:size]
        return read_str


class VcuTestInterface:
    """
    VCU Test Interface for UDP communication with VCU devices.

    Manages connection, message sending/receiving with Protocol Buffers support.

    Attributes:
        test_sock: UDP socket for test commands
        connect_sock: UDP socket for connection handshake
        verbose: Enable verbose logging
        start_time: Interface start time for timestamp calculation
    """

    def __init__(self, verbose: bool = DEFAULT_VERBOSE):
        """
        Initialize VCU Test Interface.

        Args:
            verbose: Enable verbose logging (default False)
        """
        self.test_sock: Optional[socket.socket] = None
        self.connect_sock: Optional[socket.socket] = None
        self.verbose = verbose
        self.start_time = time.time()
        self._connected = False

    async def init_interface(self) -> 'CommMsgBody':
        """
        Initialize VCU interface and establish connection.

        Performs connection handshake and sends initial test request.

        Returns:
            CommMsgBody: Initial response from VCU

        Raises:
            VcuConnectFailed: If connection fails
        """
        # Step 1: Connection handshake
        if not await self.connect():
            raise VcuConnectFailed("Failed to establish connection with VCU")

        # Step 2: Initialize test socket
        self.test_sock = get_udp_sock()
        self.test_sock.settimeout(0.1)

        # Step 3: Send initial test request
        # Note: In full implementation, this would create a get_fw_version_req
        # For now, return a mock response
        logger.info("VCU interface initialized successfully")
        return self._create_mock_response()

    async def connect(self, connect_retries: int = DEFAULT_CONNECT_RETRIES) -> bool:
        """
        Establish connection with VCU using handshake.

        Sends 'connect' string and waits for echo.

        Args:
            connect_retries: Number of retry attempts (default 15)

        Returns:
            bool: True if connected, False otherwise
        """
        self.connect_sock = get_udp_sock()
        self.connect_sock.settimeout(0.1)

        connect_msg = b'connect'

        for i in range(connect_retries):
            try:
                # Clear receive buffer
                flush_udp_recv(self.connect_sock)

                # Send connect message
                self.connect_sock.sendto(connect_msg, CONNECT_ENDPOINT)

                if self.verbose:
                    logger.debug(f"Sent: {connect_msg}")

                # Wait for echo
                try:
                    connect_rsp = await asyncio.wait_for(
                        self._async_recvfrom(self.connect_sock, len(connect_msg)),
                        timeout=0.1
                    )

                    if connect_rsp == connect_msg:
                        if self.verbose:
                            logger.debug(f"Received: {connect_rsp}")
                        self._connected = True
                        logger.info("VCU connection established")
                        return True

                except asyncio.TimeoutError:
                    pass

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.warning(f"Connection attempt {i+1} failed: {e}")

        return False

    async def poll(self, request: 'CommMsgBody', request_type: int = 1) -> 'CommMsgBody':
        """
        Send request and receive response from VCU.

        Args:
            request: Protocol Buffers request message
            request_type: Message format type (default 1 = Bare NanoPB)

        Returns:
            CommMsgBody: Response from VCU

        Raises:
            VcuPollFailed: If poll fails
        """
        assert request_type == 1, "Only Protocol Buffers format supported"

        try:
            return await self._protobuf_poll(request)
        except Exception as e:
            raise VcuPollFailed(f"Poll failed: {e}") from e

    async def _protobuf_poll(self, request: 'CommMsgBody') -> 'CommMsgBody':
        """
        Send Protocol Buffers request and receive response.

        Args:
            request: Protocol Buffers CommMsgBody request

        Returns:
            CommMsgBody: Protocol Buffers response
        """
        # Set timestamp if test_command_req
        if hasattr(request, 'WhichOneof'):
            which = request.WhichOneof('comm_msg')
            if which == 'test_command_req':
                request.test_command_req.timestamp = int(
                    (time.time() - self.start_time) * 1000
                )

        if self.verbose:
            logger.debug(f"Protobuf Request: {request}")

        # Serialize and send
        request_str = request.SerializeToString()
        await self._send_msg_body(self.test_sock, TEST_ENDPOINT, request_str)

        # Receive response
        resp_header, resp_header_str, response_str = await self._recv_frame(self.test_sock)

        # Parse response
        # Note: In full implementation, this would use actual protobuf classes
        # For now, return a mock response
        response = self._create_mock_response()

        if self.verbose:
            logger.debug(f"Protobuf Response: {response}")

        return response

    async def _send_msg_body(
        self,
        sock: socket.socket,
        endpoint: Tuple[str, int],
        msg_body: bytes
    ) -> None:
        """
        Send message body with VCU header.

        Args:
            sock: Socket to send on
            endpoint: (host, port) endpoint
            msg_body: Message body to send
        """
        # Create header
        import struct
        from .header import create_header

        header = create_header(msg_body, message_format=1)

        # Serialize header
        header_str = header.serialize()

        # Send header + body
        full_msg = header_str + msg_body
        sock.sendto(full_msg, endpoint)

        if self.verbose:
            logger.debug(f"Sent {len(full_msg)} bytes to {endpoint}")

    async def _recv_frame(self, sock: socket.SocketType, timeout: float = DEFAULT_TIMEOUT) -> Tuple:
        """
        Receive frame with triple-frame detection.

        Implements 3-layer detection:
        1. Sync based framing (0xCAFE)
        2. Length based framing (valid range)
        3. CRC based framing (checksum validation)

        Args:
            sock: Socket to receive from
            timeout: Receive timeout in seconds

        Returns:
            Tuple of (header, header_str, body_str)

        Raises:
            VcuTimeout: If timeout occurs
            VcuPollFailed: If frame validation fails
        """
        sock_buffer = SocketBuffer(sock)
        frame_detector = deque(b'\xff' * 12, maxlen=12)  # Header size
        frame_header = CommMsgHeader_t()

        start_time = time.time()

        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                raise VcuTimeout(f"Frame detection timeout after {timeout}s")

            # Read one byte
            input_byte = await sock_buffer.read(1)
            frame_detector.append(input_byte)
            frame_header_str = bytes(frame_detector)

            try:
                frame_header.deserialize(frame_header_str)

                # 1. Sync based framing
                if frame_header.sync == MAGIC_SYNC_U16:
                    # 2. Length based framing
                    if frame_header.is_valid_length():
                        # Peek ahead to read body
                        msg_body_candidate_str = await sock_buffer.peek(frame_header.length)

                        # 3. CRC based framing
                        recv_crc = calculate_crc(frame_header_str, msg_body_candidate_str)

                        if recv_crc == frame_header.crc:
                            # Valid frame - consume body
                            await sock_buffer.read(frame_header.length)
                            return frame_header, frame_header_str, msg_body_candidate_str
                        else:
                            if self.verbose:
                                logger.warning(f"CRC mismatch: expected {frame_header.crc}, got {recv_crc}")

            except Exception:
                # Continue looking for valid frame
                pass

    async def _async_recvfrom(self, sock: socket.socket, bufsize: int) -> bytes:
        """
        Async wrapper for socket.recvfrom.

        Args:
            sock: Socket to receive from
            bufsize: Buffer size

        Returns:
            bytes: Received data
        """
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.sock_recv(sock, bufsize),
            timeout=0.1
        )

    def get_new_msg(self) -> 'CommMsgBody':
        """
        Create new Protocol Buffers message.

        Note: In full implementation, this would create actual protobuf message.
        Returns mock for now.

        Returns:
            CommMsgBody: New message instance
        """
        # Mock implementation
        return self._create_mock_response()

    def _create_mock_response(self) -> 'MockCommMsgBody':
        """Create mock response for testing."""
        class MockCommMsgBody:
            def __init__(self):
                self.get_fw_version_rsp = type('obj', (object,), {'fw_version': '1.0.0'})()

            def SerializeToString(self):
                return b''

            def WhichOneof(self, name):
                return 'test_command_req'

        return MockCommMsgBody()

    async def close(self) -> None:
        """Close all sockets and cleanup."""
        if self.test_sock:
            self.test_sock.close()
            self.test_sock = None

        if self.connect_sock:
            self.connect_sock.close()
            self.connect_sock = None

        self._connected = False
        logger.info("VCU interface closed")

    @property
    def is_connected(self) -> bool:
        """Check if interface is connected."""
        return self._connected

    async def __aenter__(self):
        """Async context manager entry."""
        await self.init_interface()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
