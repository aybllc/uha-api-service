"""
Configuration management for UHA API Service
"""
import os
from pathlib import Path
from typing import Optional

class Settings:
    """Application settings"""

    # API Information
    API_TITLE = "UHA API Service"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "Cosmological dataset aggregation and statistical analysis service"
    ORGANIZATION = "All Your Baseline LLC"

    # Server Configuration
    HOST = os.getenv("UHA_HOST", "127.0.0.1")
    PORT = int(os.getenv("UHA_PORT", "8000"))

    # Base directory
    BASE_DIR = Path("/opt/uha-api")
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = BASE_DIR / "logs"

    # Database
    DATABASE_PATH = DATA_DIR / "uha_api.db"

    # Security
    API_KEY_HEADER = "X-API-Key"
    SECRET_KEY = os.getenv("UHA_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")  # Used for JWT if needed

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("UHA_RATE_LIMIT_MIN", "60"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("UHA_RATE_LIMIT_HOUR", "1000"))
    RATE_LIMIT_PER_DAY = int(os.getenv("UHA_RATE_LIMIT_DAY", "10000"))

    # Logging
    LOG_LEVEL = os.getenv("UHA_LOG_LEVEL", "INFO")
    LOG_FILE = LOG_DIR / "api.log"

    # CORS (if needed)
    CORS_ORIGINS = os.getenv("UHA_CORS_ORIGINS", "").split(",") if os.getenv("UHA_CORS_ORIGINS") else []

    # Request limits
    MAX_REQUEST_SIZE = 1024 * 1024  # 1MB
    REQUEST_TIMEOUT = 30  # seconds

    # Development vs Production
    DEBUG = os.getenv("UHA_DEBUG", "false").lower() == "true"

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.SECRET_KEY == "CHANGE_ME_IN_PRODUCTION" and not cls.DEBUG:
            raise ValueError("SECRET_KEY must be set in production")

        if not cls.DATABASE_PATH.parent.exists():
            raise ValueError(f"Database directory does not exist: {cls.DATABASE_PATH.parent}")


settings = Settings()
