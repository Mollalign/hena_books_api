from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, EmailStr, Field, field_validator
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # -------------------------
    # Database
    # -------------------------
    DATABASE_URL: AnyUrl

    # -------------------------
    # Security / Auth
    # -------------------------
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -------------------------
    # Email / SMTP
    # -------------------------
    SMTP_EMAIL: Optional[EmailStr] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None

    # -------------------------
    # Application
    # -------------------------
    PROJECT_NAME: str = "Finance Tracker"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "UTC"

    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    FRONTEND_URL: Optional[str] = None
    ALLOWED_HOSTS: List[str] = Field(default_factory=lambda: ["localhost"])

    SQLALCHEMY_ECHO: bool = False
    DB_POOL_MIN_SIZE: Optional[int] = None
    DB_POOL_MAX_SIZE: Optional[int] = None

    SENTRY_DSN: Optional[AnyUrl] = None

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # -------------------------
    # Validators (Pydantic V2)
    # -------------------------

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        """
        Accept list OR comma-separated string:
        "http://a, http://b"
        """
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("ALGORITHM")
    def validate_algorithm(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("ALGORITHM must be a non-empty string.")
        return v


settings = Settings()
