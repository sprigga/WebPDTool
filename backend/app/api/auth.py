"""Authentication API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.security import create_access_token
from app.config import settings
from app.schemas.user import LoginRequest, LoginResponse, Token, User as UserSchema
from app.services import auth as auth_service
from app.dependencies import get_current_active_user

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint

    Args:
        login_data: Login credentials (username and password)
        db: Database session

    Returns:
        LoginResponse with access token and user info
    """
    user = auth_service.authenticate_user(db, login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "id": user.id},
        expires_delta=access_token_expires,
    )

    # Convert user to schema
    user_schema = UserSchema.from_orm(user)

    return LoginResponse(
        access_token=access_token, token_type="bearer", user=user_schema
    )


@router.post("/login-form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Login endpoint for OAuth2 password flow
    (for Swagger UI authentication)
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "id": user.id},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_active_user)):
    """
    User logout endpoint

    Note: Since we're using JWT tokens, logout is handled client-side
    by removing the token from storage. This endpoint is mainly for
    consistency and future extensions (e.g., token blacklisting)
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get current authenticated user information
    """
    user = auth_service.get_user_by_username(db, current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserSchema.from_orm(user)


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_active_user)):
    """
    Refresh access token
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": current_user["username"],
            "role": current_user.get("role"),
            "id": current_user.get("id"),
        },
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")
