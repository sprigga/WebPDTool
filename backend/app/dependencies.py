"""Dependency injection functions"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# Original code: from sqlalchemy.orm import Session
# Modified: Use AsyncSession for async DB migration (Wave 6 - Task 14)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# Original code: from app.core.database import get_db
# Modified: Use async DB dependency
from app.core.database import get_async_db
from app.core.security import decode_access_token

security = HTTPBearer()


async def set_user_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    ✅ Added: Set user context for logging
    Extracts user_id from JWT token and stores in request.state
    This enables automatic user tracking in all logs
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload:
        user_id = payload.get("id")
        if user_id:
            request.state.user_id = user_id

    return payload  # Return payload for potential use


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database to ensure user still exists
    from app.models.user import User

    # Original code: user = db.query(User).filter(User.username == username).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return user info with JWT payload data
    return {"id": user.id, "username": username, "role": user.role.value, **payload}


async def get_current_active_user(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)
):
    """Get current active user"""
    # Check if user is active in database
    from app.models.user import User

    # Original code: user = db.query(User).filter(User.id == current_user["id"]).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(User).where(User.id == current_user["id"])
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user
