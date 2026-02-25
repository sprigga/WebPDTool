"""Users API endpoints for user management"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Set

from app.core.database import get_db
from app.core.api_helpers import PermissionChecker, get_entity_or_404
from app.core.constants import ErrorMessages
from app.schemas.user import UserCreate, UserUpdate, UserInDB, PasswordChange
from app.models.user import User as UserModel, UserRole
from app.services import auth as auth_service
from app.dependencies import get_current_active_user

router = APIRouter()

# Fields allowed to be updated via UserUpdate endpoint
# Original code allowed any field from model_dump(), which could lead to unintended updates
# e.g., someone could send {"id": 999} and update the user's ID
USER_UPDATE_WHITELIST: Set[str] = {"full_name", "email", "is_active"}


@router.get("", response_model=List[UserInDB])
async def get_users(
    offset: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get list of all users with optional search and filtering"""
    query = db.query(UserModel)

    # Original code: Basic query with no filtering
    # Enhanced: Added search across username, full_name, and email fields
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                UserModel.username.like(search_pattern),
                UserModel.full_name.like(search_pattern),
                UserModel.email.like(search_pattern)
            )
        )

    # Original code: No role filtering
    # Enhanced: Added role filter using UserRole enum
    if role is not None:
        query = query.filter(UserModel.role == role)

    # Original code: No is_active filtering
    # Enhanced: Added is_active status filter
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)

    # Original code: No ordering
    # Enhanced: Order results by username ascending for consistent pagination
    query = query.order_by(UserModel.username.asc())

    users = query.offset(offset).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserInDB)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get user by ID"""
    # Refactored: Original code had manual query + if-not-found pattern (lines 36-42)
    # Now using centralized get_entity_or_404 helper from app/core/api_helpers.py
    return get_entity_or_404(db, UserModel, user_id, ErrorMessages.USER_NOT_FOUND)


@router.post("", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create new user (Admin only)"""
    # Refactored: Original code had hardcoded "admin" string, now using PermissionChecker.ADMIN constant
    PermissionChecker.check_admin(current_user, "create users")

    # Check if username already exists
    existing_user = db.query(UserModel).filter(
        UserModel.username == user.username
    ).first()
    if existing_user:
        # Refactored: Now using ErrorMessages.USERNAME_ALREADY_EXISTS constant
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.USERNAME_ALREADY_EXISTS
        )

    # Create user using service layer
    db_user = auth_service.create_user(db, user)
    return db_user


@router.put("/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update user (Admin only)"""
    # Refactored: Original code had hardcoded "admin" string, now using PermissionChecker.ADMIN constant
    PermissionChecker.check_admin(current_user, "update users")

    # Refactored: Original code had manual query + if-not-found pattern (lines 81-87)
    # Now using centralized get_entity_or_404 helper from app/core/api_helpers.py
    db_user = get_entity_or_404(db, UserModel, user_id, ErrorMessages.USER_NOT_FOUND)

    # Security fix: Original code allowed any field from model_dump() to be updated (lines 89-92)
    # This could lead to unintended updates like {"id": 999} or {"username": "hacked"}
    # Now using whitelist to only allow specific safe fields
    update_data = user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key not in USER_UPDATE_WHITELIST:
            # Skip fields not in whitelist to prevent unintended updates
            continue
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/{user_id}/password", response_model=UserInDB)
async def change_user_password(
    user_id: int,
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Change user password (Admin only or self)

    Security improvement: Original code used query parameter for new_password (line 102)
    which could be logged in server access logs. Now using request body with Pydantic schema
    that includes min_length=6 validation (PasswordChange schema in schemas/user.py)
    """
    # Refactored: Original code had hardcoded "admin" string, now using PermissionChecker.ADMIN constant
    # Allow admins or users changing their own password
    if current_user.get("role") != PermissionChecker.ADMIN and current_user.get("id") != user_id:
        # Refactored: Now using ErrorMessages.ONLY_CHANGE_OWN_PASSWORD constant
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.ONLY_CHANGE_OWN_PASSWORD
        )

    # Refactored: Original code had manual query + if-not-found pattern (lines 115-121)
    # Now using centralized get_entity_or_404 helper from app/core/api_helpers.py
    db_user = get_entity_or_404(db, UserModel, user_id, ErrorMessages.USER_NOT_FOUND)

    from app.core.security import get_password_hash
    db_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Delete user (Admin only) - prevents self-deletion"""
    # Refactored: Original code had hardcoded "admin" string, now using PermissionChecker.ADMIN constant
    PermissionChecker.check_admin(current_user, "delete users")

    # Prevent self-deletion
    if current_user.get("id") == user_id:
        # Refactored: Now using ErrorMessages.CANNOT_DELETE_SELF constant
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.CANNOT_DELETE_SELF
        )

    # Refactored: Original code had manual query + if-not-found pattern (lines 147-153)
    # Now using centralized get_entity_or_404 helper from app/core/api_helpers.py
    db_user = get_entity_or_404(db, UserModel, user_id, ErrorMessages.USER_NOT_FOUND)

    db.delete(db_user)
    db.commit()
    return None
