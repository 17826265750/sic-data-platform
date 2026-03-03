"""
SiC Data Processing Platform - Configuration Management
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "sic-data-platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # Default to False for security

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database - No default credentials, must be set via environment
    DATABASE_URL: Optional[str] = None
    DATABASE_SYNC_URL: Optional[str] = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage Paths
    UPLOAD_DIR: str = "./storage/uploads"
    RESULT_DIR: str = "./storage/results"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # Allowed file extensions for upload
    ALLOWED_EXTENSIONS: str = ".xlsx,.xls,.docx,.png,.jpg,.jpeg,.pdf"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Chinese Font
    CHINESE_FONT_PATH: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("DATABASE_URL", "DATABASE_SYNC_URL", mode="before")
    @classmethod
    def validate_db_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate database URL if provided"""
        if v and "postgres:postgres@" in v:
            import warnings
            warnings.warn(
                "Using default credentials in DATABASE_URL is not recommended for production",
                UserWarning
            )
        return v

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

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed file extensions as list"""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()