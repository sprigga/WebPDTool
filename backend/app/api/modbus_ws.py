"""
Modbus WebSocket Endpoint
Real-time events for Modbus listener status
"""
import asyncio
import logging
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db as get_db
from app.models.modbus_config import ModbusConfig
from app.schemas.modbus import ModbusConfigCreate
from app.services.modbus.modbus_manager import modbus_manager


router = APIRouter()
logger = logging.getLogger(__name__)


class ModbusConnectionManager:
    """
    Manages WebSocket connections for Modbus events
    """

    def __init__(self):
        # station_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, station_id: int):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        if station_id not in self.active_connections:
            self.active_connections[station_id] = set()
        self.active_connections[station_id].add(websocket)
        logger.info(f"WebSocket connected for station {station_id}")

    def disconnect(self, websocket: WebSocket, station_id: int):
        """Remove WebSocket connection"""
        if station_id in self.active_connections:
            self.active_connections[station_id].discard(websocket)
            if not self.active_connections[station_id]:
                del self.active_connections[station_id]
        logger.info(f"WebSocket disconnected for station {station_id}")

    async def send_to_station(self, station_id: int, message: dict):
        """Send message to all connections for a station"""
        if station_id in self.active_connections:
            for connection in self.active_connections[station_id].copy():
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    self.disconnect(connection, station_id)

    async def broadcast(self, message: dict):
        """Send message to all active connections"""
        for station_id, connections in self.active_connections.items():
            for connection in connections.copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection, station_id)


# Global connection manager
ws_manager = ModbusConnectionManager()


async def start_modbus_listener_ws(station_id: int, db: AsyncSession):
    """
    Start Modbus listener with WebSocket callbacks

    Args:
        station_id: Station ID
        db: Database session
    """
    # Get config from database
    result = await db.execute(
        select(ModbusConfig).where(ModbusConfig.station_id == station_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        await ws_manager.send_to_station(station_id, {
            "type": "error",
            "message": "Modbus configuration not found"
        })
        return

    # Create config schema
    config_schema = ModbusConfigCreate(
        station_id=config.station_id,
        server_host=config.server_host,
        server_port=config.server_port,
        device_id=config.device_id,
        enabled=config.enabled,
        delay_seconds=config.delay_seconds,
        ready_status_address=config.ready_status_address,
        ready_status_length=config.ready_status_length,
        read_sn_address=config.read_sn_address,
        read_sn_length=config.read_sn_length,
        test_status_address=config.test_status_address,
        test_status_length=config.test_status_length,
        in_testing_value=config.in_testing_value,
        test_finished_value=config.test_finished_value,
        test_result_address=config.test_result_address,
        test_result_length=config.test_result_length,
        test_no_result=config.test_no_result,
        test_pass_value=config.test_pass_value,
        test_fail_value=config.test_fail_value,
        simulation_mode=config.simulation_mode
    )

    # Define callbacks
    def on_sn_received(sn: str):
        """Callback when SN is received"""
        asyncio.create_task(
            ws_manager.send_to_station(station_id, {
                "type": "sn_received",
                "sn": sn,
            })
        )

    def on_error(error_msg: str):
        """Callback when error occurs"""
        asyncio.create_task(
            ws_manager.send_to_station(station_id, {
                "type": "error",
                "message": error_msg,
            })
        )

    # Start listener
    try:
        await modbus_manager.start_listener(
            config_schema,
            on_sn_received=on_sn_received,
            on_error=on_error
        )

        await ws_manager.send_to_station(station_id, {
            "type": "status",
            "status": "running",
            "message": "Modbus listener started"
        })

    except Exception as e:
        await ws_manager.send_to_station(station_id, {
            "type": "error",
            "message": f"Failed to start listener: {str(e)}"
        })


@router.websocket("/ws/{station_id}")
async def modbus_websocket(
    websocket: WebSocket,
    station_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for Modbus events

    Messages:
    - Client -> Server: {"action": "subscribe"|"unsubscribe"|"start"|"stop"|"get_status"}
    - Server -> Client: {"type": "status"|"sn_received"|"error", ...}
    """
    await ws_manager.connect(websocket, station_id)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                await websocket.send_json({
                    "type": "status",
                    "action": "subscribed",
                    "station_id": station_id
                })

            elif action == "start":
                asyncio.create_task(start_modbus_listener_ws(station_id, db))

            elif action == "stop":
                await modbus_manager.stop_listener(station_id)
                await websocket.send_json({
                    "type": "status",
                    "status": "stopped",
                    "message": "Modbus listener stopped"
                })

            elif action == "get_status":
                status = modbus_manager.get_status(station_id)
                await websocket.send_json({
                    "type": "status",
                    "data": status
                })

            elif action == "unsubscribe":
                await websocket.send_json({
                    "type": "status",
                    "action": "unsubscribed"
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, station_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, station_id)
