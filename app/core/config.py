"""
Application Configuration

Central configuration management using Pydantic Settings.
All settings are loaded from environment variables or .env file.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, EmailStr, Field, field_validator
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Environment variables can be set directly or via a .env file.
    All settings have sensible defaults for development.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # =========================================================================
    # APPLICATION
    # =========================================================================
    PROJECT_NAME: str = "Hena Books API"
    PROJECT_DESCRIPTION: str = "Christian/Biblical Book Platform API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "UTC"

    # =========================================================================
    # DATABASE
    # =========================================================================
    DATABASE_URL: AnyUrl
    SQLALCHEMY_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # =========================================================================
    # SECURITY / JWT
    # =========================================================================
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # =========================================================================
    # CORS
    # =========================================================================
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: List[str] = Field(default_factory=lambda: ["*"])

    # =========================================================================
    # FRONTEND
    # =========================================================================
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_HOSTS: List[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])

    # =========================================================================
    # EMAIL / SMTP
    # =========================================================================
    SMTP_EMAIL: Optional[EmailStr] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USE_TLS: bool = True

    # =========================================================================
    # CLOUDINARY
    # =========================================================================
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    # =========================================================================
    # MONITORING (Optional)
    # =========================================================================
    SENTRY_DSN: Optional[AnyUrl] = None

    # =========================================================================
    # VALIDATORS
    # =========================================================================
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept list OR comma-separated string."""
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Accept list OR comma-separated string."""
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Ensure log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.DEBUG

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic)."""
        url = str(self.DATABASE_URL)
        return url.replace("postgresql+asyncpg://", "postgresql://")

    @property
    def cloudinary_configured(self) -> bool:
        """Check if Cloudinary is configured."""
        return all([
            self.CLOUDINARY_CLOUD_NAME,
            self.CLOUDINARY_API_KEY,
            self.CLOUDINARY_API_SECRET
        ])

    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is configured."""
        return all([
            self.SMTP_EMAIL,
            self.SMTP_PASSWORD,
            self.SMTP_SERVER
        ])


# Global settings instance
settings = Settings()
