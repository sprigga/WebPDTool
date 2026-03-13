"""Database configuration and session management"""
# Original code: from sqlalchemy import create_engine
# Original code: from sqlalchemy.ext.declarative import declarative_base
# Original code: from sqlalchemy.orm import sessionmaker
# Modified: Removed sync imports (Wave 6 - Task 14) - fully async now
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from app.config import settings

# Original code: DATABASE_URL with pymysql (removed)
# Modified: Use asyncmy driver only (Wave 6 - Task 14)
ASYNC_DATABASE_URL = f"mysql+asyncmy://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Original code: Sync engine and SessionLocal (removed)
# Modified: Async engine only (Wave 6 - Task 14)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Original code: get_db() for sync sessions (removed)
# Modified: Use get_async_db() only (Wave 6 - Task 14)
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an AsyncSession, rolls back on exception."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

# Create Base class for declarative models
# Note: Using async_base from SQLAlchemy 2.0
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
