"""
DUT Control API
Endpoints for controlling Device Under Test hardware (relay, chassis rotation)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal
import logging

from app.dependencies import get_current_user
from app.services.dut_comms import (
    get_relay_controller,
    get_chassis_controller,
    RelayState,
    RotationDirection
)

router = APIRouter(prefix="/dut-control", tags=["DUT Control"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================
class RelayControlRequest(BaseModel):
    """Request model for relay control"""
    state: Literal["ON", "OFF", "OPEN", "CLOSED"] = Field(
        ...,
        description="Relay state: ON/OPEN or OFF/CLOSED"
    )
    channel: int = Field(
        default=1,
        ge=1,
        le=16,
        description="Relay channel number (1-16)"
    )
    device_path: Optional[str] = Field(
        default=None,
        description="Device path (e.g., /dev/ttyUSB0)"
    )


class ChassisRotationRequest(BaseModel):
    """Request model for chassis rotation"""
    direction: Literal["CW", "CCW", "CLOCKWISE", "COUNTERCLOCKWISE"] = Field(
        ...,
        description="Rotation direction"
    )
    duration_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Rotation duration in milliseconds (optional)"
    )
    device_path: Optional[str] = Field(
        default=None,
        description="Device path (e.g., /dev/ttyACM0)"
    )


class ControlResponse(BaseModel):
    """Response model for control operations"""
    success: bool
    message: str
    current_state: Optional[str] = None


# ============================================================================
# Relay Control Endpoints
# ============================================================================
@router.post("/relay/set", response_model=ControlResponse)
async def set_relay_state(
    request: RelayControlRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Set relay to specified state.

    Maps to PDTool4's MeasureSwitchON/OFF functionality.

    Args:
        request: Relay control parameters
        current_user: Authenticated user (requires login)

    Returns:
        Control operation result
    """
    try:
        # Map state string to RelayState enum
        if request.state in ["ON", "OPEN"]:
            target_state = RelayState.SWITCH_OPEN
            state_name = "ON (OPEN)"
        else:  # OFF or CLOSED
            target_state = RelayState.SWITCH_CLOSED
            state_name = "OFF (CLOSED)"

        # Get relay controller
        relay_controller = get_relay_controller(device_path=request.device_path)

        # Set relay state
        logger.info(
            f"User {current_user.get('username')} setting relay channel {request.channel} "
            f"to {state_name}"
        )

        success = await relay_controller.set_relay_state(target_state, request.channel)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to set relay channel {request.channel} to {state_name}"
            )

        return ControlResponse(
            success=True,
            message=f"Relay channel {request.channel} set to {state_name}",
            current_state=state_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Relay control error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relay/on", response_model=ControlResponse)
async def switch_relay_on(
    channel: int = 1,
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Switch relay ON (OPEN state).

    Convenience endpoint mapping to PDTool4's MeasureSwitchON.

    Args:
        channel: Relay channel number (default: 1)
        device_path: Optional device path
        current_user: Authenticated user

    Returns:
        Control operation result
    """
    request = RelayControlRequest(state="ON", channel=channel, device_path=device_path)
    return await set_relay_state(request, current_user)


@router.post("/relay/off", response_model=ControlResponse)
async def switch_relay_off(
    channel: int = 1,
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Switch relay OFF (CLOSED state).

    Convenience endpoint mapping to PDTool4's MeasureSwitchOFF.

    Args:
        channel: Relay channel number (default: 1)
        device_path: Optional device path
        current_user: Authenticated user

    Returns:
        Control operation result
    """
    request = RelayControlRequest(state="OFF", channel=channel, device_path=device_path)
    return await set_relay_state(request, current_user)


@router.get("/relay/status", response_model=ControlResponse)
async def get_relay_status(
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get current relay status.

    Args:
        device_path: Optional device path
        current_user: Authenticated user

    Returns:
        Current relay state
    """
    try:
        relay_controller = get_relay_controller(device_path=device_path)
        current_state = await relay_controller.get_current_state()

        if current_state is None:
            state_str = "UNKNOWN"
        elif current_state == RelayState.SWITCH_OPEN:
            state_str = "ON (OPEN)"
        else:
            state_str = "OFF (CLOSED)"

        return ControlResponse(
            success=True,
            message="Relay status retrieved",
            current_state=state_str
        )

    except Exception as e:
        logger.error(f"Error getting relay status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Chassis Rotation Control Endpoints
# ============================================================================
@router.post("/chassis/rotate", response_model=ControlResponse)
async def rotate_chassis(
    request: ChassisRotationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Rotate chassis fixture in specified direction.

    Maps to PDTool4's MyThread_CW/CCW functionality.

    Args:
        request: Chassis rotation parameters
        current_user: Authenticated user

    Returns:
        Control operation result
    """
    try:
        # Map direction string to RotationDirection enum
        if request.direction in ["CW", "CLOCKWISE"]:
            target_direction = RotationDirection.CLOCKWISE
            direction_name = "CLOCKWISE"
        else:  # CCW or COUNTERCLOCKWISE
            target_direction = RotationDirection.COUNTERCLOCKWISE
            direction_name = "COUNTERCLOCKWISE"

        # Get chassis controller
        chassis_controller = get_chassis_controller(
            device_path=request.device_path,
            config={}
        )

        # Execute rotation
        logger.info(
            f"User {current_user.get('username')} rotating chassis {direction_name} "
            f"(duration: {request.duration_ms}ms)"
        )

        success = await chassis_controller.rotate(target_direction, request.duration_ms)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to rotate chassis {direction_name}"
            )

        return ControlResponse(
            success=True,
            message=f"Chassis rotated {direction_name}",
            current_state=direction_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chassis rotation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chassis/rotate-cw", response_model=ControlResponse)
async def rotate_chassis_clockwise(
    duration_ms: Optional[int] = None,
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Rotate chassis clockwise.

    Convenience endpoint mapping to PDTool4's MyThread_CW.

    Args:
        duration_ms: Optional rotation duration in milliseconds
        device_path: Optional device path
        current_user: Authenticated user

    Returns:
        Control operation result
    """
    request = ChassisRotationRequest(
        direction="CW",
        duration_ms=duration_ms,
        device_path=device_path
    )
    return await rotate_chassis(request, current_user)


@router.post("/chassis/rotate-ccw", response_model=ControlResponse)
async def rotate_chassis_counterclockwise(
    duration_ms: Optional[int] = None,
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Rotate chassis counterclockwise.

    Convenience endpoint mapping to PDTool4's MyThread_CCW.

    Args:
        duration_ms: Optional rotation duration in milliseconds
        device_path: Optional device path
        current_user: Authenticated user

    Returns:
        Control operation result
    """
    request = ChassisRotationRequest(
        direction="CCW",
        duration_ms=duration_ms,
        device_path=device_path
    )
    return await rotate_chassis(request, current_user)


@router.post("/chassis/stop", response_model=ControlResponse)
async def stop_chassis_rotation(
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Stop chassis rotation.

    Args:
        device_path: Optional device path
        current_user: Authenticated user

    Returns:
        Control operation result
    """
    try:
        chassis_controller = get_chassis_controller(device_path=device_path, config={})

        logger.info(f"User {current_user.get('username')} stopping chassis rotation")

        success = await chassis_controller.stop_rotation()

        if not success:
            raise HTTPException(status_code=500, detail="Failed to stop chassis rotation")

        return ControlResponse(
            success=True,
            message="Chassis rotation stopped",
            current_state="STOPPED"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping chassis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chassis/status", response_model=ControlResponse)
async def get_chassis_status(
    device_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get chassis rotation status.

    Args:
        device_path: Optional device path
        current_user: Authenticated user

    Returns:
        Current chassis status
    """
    try:
        chassis_controller = get_chassis_controller(device_path=device_path, config={})
        is_rotating = chassis_controller.is_rotating()

        return ControlResponse(
            success=True,
            message="Chassis status retrieved",
            current_state="ROTATING" if is_rotating else "IDLE"
        )

    except Exception as e:
        logger.error(f"Error getting chassis status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
