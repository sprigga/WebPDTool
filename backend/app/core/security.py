"""Security utilities for authentication and authorization"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from app.config import settings


def _truncate_password(password: str, max_bytes: int = 72) -> str:
    """Truncate password to max bytes (default 72 for bcrypt)"""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > max_bytes:
        password_bytes = password_bytes[:max_bytes]
        password = password_bytes.decode('utf-8', errors='ignore')
    return password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Truncate password to 72 bytes max (bcrypt limitation)
    plain_password = _truncate_password(plain_password)
    
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    # Truncate password to 72 bytes max (bcrypt limitation)
    password = _truncate_password(password)
    try:
        salt = bcrypt.gensalt()
        hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hash_bytes.decode('utf-8')
    except ValueError as e:
        if "password cannot be longer than 72 bytes" in str(e):
            # Final fallback: use character truncation
            password = password[:72]
            salt = bcrypt.gensalt()
            hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hash_bytes.decode('utf-8')
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify JWT access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
