"""User schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    role: UserRole


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    # Note: role and username cannot be updated through this endpoint


class PasswordChange(BaseModel):
    """Password change request schema"""
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")


class UserInDB(UserBase):
    """User with database fields"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDB):
    """User response schema"""
    pass


class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data"""
    username: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str = "bearer"
    user: User
