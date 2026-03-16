"""
Simple Modbus TCP Simulator for Testing

Usage:
    python scripts/modbus_simulator.py [--host 127.0.0.1] [--port 5020]

Simulates a Modbus device that:
- Holds ready_status at 0x0013 (set to 0x01 to trigger SN read)
- Holds SN data at 0x0064-0x006E ("TEST12345678")
- Accepts writes to test_status (0x0014) and test_result (0x0015)
"""
import asyncio
import logging
import argparse
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


async def run_simulator(host: str = '127.0.0.1', port: int = 5020):
    """
    Run Modbus TCP simulator

    Args:
        host: Server host
        port: Server port
    """
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 200),
        co=ModbusSequentialDataBlock(0, [0] * 200),
        hr=ModbusSequentialDataBlock(0, [0] * 200),
        ir=ModbusSequentialDataBlock(0, [0] * 200)
    )

    # Ready status at 0x0013 (19) — set to 0x00 initially (not ready)
    store.store['h'].values[0x13] = 0x00

    # SN registers at 0x0064-0x006E (11 registers) — "TEST12345678\0\0\0\0"
    sn_data = [0x5445, 0x5354, 0x3132, 0x3334, 0x3536, 0x3738, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000]
    for i, val in enumerate(sn_data):
        store.store['h'].values[0x64 + i] = val

    context = ModbusServerContext(slaves=store, single=True)

    logger.info(f"Modbus simulator listening on {host}:{port}")
    logger.info("Set register 0x0013 = 0x01 to simulate 'SN ready' signal")
    await StartAsyncTcpServer(context=context, address=(host, port))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modbus TCP Simulator')
    parser.add_argument('--host', default='127.0.0.1', help='Server host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5020, help='Server port (default: 5020)')
    args = parser.parse_args()

    asyncio.run(run_simulator(args.host, args.port))
