"""
VCU Common UDP Socket Utilities

Provides UDP socket creation and buffer management utilities.
Refactored from PDTool4 polish/dut_comms/vcu_ether_comms/vcu_common.py (17 lines).
"""
import socket
import asyncio
from typing import Optional


def get_udp_sock() -> socket.socket:
    """
    Create and configure a UDP socket.

    Returns:
        socket.socket: Configured UDP socket
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return sock


def flush_udp_recv(sock: socket.socket, byte_size_to_flush: int = 2**16) -> None:
    """
    Clear socket receive buffer by reading all available data.

    Useful before sending new commands to avoid receiving stale data.

    Args:
        sock: Socket to flush
        byte_size_to_flush: Maximum bytes to flush (default 65536)
    """
    try:
        # Set very short timeout
        timeout = sock.gettimeout()
        sock.settimeout(0.0001)

        try:
            # Read and discard all available data
            while True:
                trash = sock.recv(byte_size_to_flush)
                if not trash:
                    break
        except socket.timeout:
            # Expected - no more data
            pass
        finally:
            # Restore original timeout
            sock.settimeout(timeout)

    except Exception:
        # Ignore errors during flush
        pass


async def async_flush_udp_recv(sock: socket.socket) -> None:
    """
    Async version of UDP socket buffer flushing.

    Args:
        sock: Socket to flush
    """
    try:
        loop = asyncio.get_event_loop()
        sock.settimeout(0.0001)

        try:
            while True:
                # Use loop.sock_recv for async operation
                data = await asyncio.wait_for(
                    loop.sock_recv(sock, 65536),
                    timeout=0.001
                )
                if not data:
                    break
        except (asyncio.TimeoutError, socket.timeout):
            pass
        finally:
            sock.settimeout(None)  # Reset to blocking

    except Exception:
        pass


def create_udp_endpoint(host: str, port: int) -> tuple:
    """
    Create UDP endpoint tuple for socket operations.

    Args:
        host: IP address or hostname
        port: Port number

    Returns:
        tuple: (host, port) endpoint tuple
    """
    return (host, port)


# Default VCU endpoints
VCU_DEFAULT_IP = '192.168.3.100'
VCU_TEST_PORT = 8156
VCU_CONNECT_PORT = 8124

TEST_ENDPOINT = create_udp_endpoint(VCU_DEFAULT_IP, VCU_TEST_PORT)
CONNECT_ENDPOINT = create_udp_endpoint(VCU_DEFAULT_IP, VCU_CONNECT_PORT)
