"""
SiC Data Processing Platform - Configuration Management
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "sic-data-platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sic_platform"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/sic_platform"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage Paths
    UPLOAD_DIR: str = "/app/storage/uploads"
    RESULT_DIR: str = "/app/storage/results"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Chinese Font
    CHINESE_FONT_PATH: str = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def upload_path(self) -> Path:
        """Get upload directory as Path object"""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def result_path(self) -> Path:
        """Get result directory as Path object"""
        path = Path(self.RESULT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()