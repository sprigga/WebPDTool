"""Application Configuration"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings"""

    # Database configuration
    DB_HOST: str = "db"
    DB_PORT: int = 3306
    DB_USER: str = "pdtool"
    DB_PASSWORD: str = "pdtool123"
    DB_NAME: str = "webpdtool"
    DATABASE_ECHO: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 原本設定: 30 分鐘
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 修改為: 8 小時 (480 分鐘)

    # Application
    APP_NAME: str = "WebPDTool"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # CORS
    # 修改: 支援從環境變數讀取逗號分隔的字串
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost",
        "http://localhost:9080",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://0.0.0.0",
        "http://127.0.0.1",
    ]

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS_ORIGINS 環境變數 (支援逗號分隔的字串)"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 9100

    # Model config for Pydantic v2
    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


# Global settings instance
settings = Settings()
