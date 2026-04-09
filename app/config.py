"""
VC-LMS Configuration Module
Reads settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "sqlite:///./vc_lms.db"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CAS Storage
    CAS_STORAGE_PATH: str = "./cas_storage"

    # File Upload Limits
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = ".py,.txt,.pdf,.docx,.zip,.tar.gz,.md,.java,.c,.cpp,.h,.js,.ts,.html,.css,.json,.xml,.csv,.ipynb"

    # Rate Limiting
    RATE_LIMIT: str = "100/minute"

    # CI/CD Webhook
    WEBHOOK_SECRET: str = "dev-webhook-secret"

    # App
    APP_NAME: str = "VC-LMS"
    DEBUG: bool = True

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Parse comma-separated file types into a list."""
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB limit to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton settings instance
settings = Settings()

# Ensure CAS storage directory exists
os.makedirs(settings.CAS_STORAGE_PATH, exist_ok=True)
