# core/config.py
import os
import secrets
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings  # Correct import for BaseSettings
from pydantic import PostgresDsn, field_validator, ValidationInfo


class Settings(BaseSettings):
    """Application settings using Pydantic for validation."""

    PROJECT_NAME: str = "Experimentation Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    CORS_ORIGINS: list[str] = [
        "*"
    ]  # Define allowed origins (e.g., ["http://localhost", "https://example.com"])
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # Database settings
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DATABASE_SCHEMA: str = "experimentation"

    # AWS/Cognito settings
    COGNITO_USER_POOL_ID: Optional[str] = None
    COGNITO_CLIENT_ID: Optional[str] = None
    AWS_REGION: Optional[str] = None

    # Database connection configuration
    DATABASE_URI: Optional[PostgresDsn] = None
    DB_ECHO_LOG: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        values = info.data
        if isinstance(v, str):
            return v

        port = values.get("POSTGRES_PORT")
        if port and isinstance(port, str):
            port = int(port)

        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=port,
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    class Config:
        case_sensitive = True
        env_file = ".env"
        # Allow extra fields to prevent validation errors
        extra = "allow"


# Create a settings instance
settings = Settings(
    POSTGRES_SERVER=os.getenv("POSTGRES_SERVER", "localhost"),
    POSTGRES_USER=os.getenv("POSTGRES_USER", "postgres"),
    POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", "postgres"),
    POSTGRES_DB=os.getenv("POSTGRES_DB", "experimentation"),
    COGNITO_USER_POOL_ID=os.getenv("COGNITO_USER_POOL_ID"),
    COGNITO_CLIENT_ID=os.getenv("COGNITO_CLIENT_ID"),
    AWS_REGION=os.getenv("AWS_REGION"),
)
