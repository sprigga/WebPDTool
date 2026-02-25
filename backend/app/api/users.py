"""Users API endpoints for user management"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.api_helpers import PermissionChecker
from app.core.constants import ErrorMessages
from app.schemas.user import UserCreate, UserUpdate, UserInDB
from app.models.user import User as UserModel
from app.services import auth as auth_service
from app.dependencies import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[UserInDB])
async def get_users(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get list of all users"""
    users = db.query(UserModel).offset(offset).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserInDB)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get user by ID"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        # TODO: Use ErrorMessages.USER_NOT_FOUND when available
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create new user (Admin only)"""
    PermissionChecker.check_admin(current_user, "create users")

    # Check if username already exists
    existing_user = db.query(UserModel).filter(
        UserModel.username == user.username
    ).first()
    if existing_user:
        # TODO: Use ErrorMessages.USERNAME_ALREADY_EXISTS when available
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
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
    PermissionChecker.check_admin(current_user, "update users")

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        # TODO: Use ErrorMessages.USER_NOT_FOUND when available
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields using model_dump for Pydantic v2
    update_data = user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/{user_id}/password", response_model=UserInDB)
async def change_user_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Change user password (Admin only or self)"""
    # Allow admins or users changing their own password
    if current_user.get("role") != "admin" and current_user.get("id") != user_id:
        # TODO: Use ErrorMessages.ONLY_CHANGE_OWN_PASSWORD when available
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password"
        )

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        # TODO: Use ErrorMessages.USER_NOT_FOUND when available
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    from app.core.security import get_password_hash
    db_user.password_hash = get_password_hash(new_password)
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
    PermissionChecker.check_admin(current_user, "delete users")

    # Prevent self-deletion
    if current_user.get("id") == user_id:
        # TODO: Use ErrorMessages.CANNOT_DELETE_SELF when available
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        # TODO: Use ErrorMessages.USER_NOT_FOUND when available
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(db_user)
    db.commit()
    return None
