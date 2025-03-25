# core/config.py
# config.py
"""
Configuration settings for the experimentation platform.

This module defines settings classes using Pydantic for type validation
and environment-based configuration management.
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, validator, EmailStr
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Base settings class with common configuration for all environments."""

    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "experimentation"
    POSTGRES_PORT: int = 5432
    POSTGRES_SCHEMA: str = "experimentation"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    DATABASE_URI: Optional[PostgresDsn] = None  # Alias for backward compatibility

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Build database URI from components."""
        if isinstance(v, str):
            return v

        # Get component values safely
        postgres_server = values.get("POSTGRES_SERVER", "localhost")
        postgres_user = values.get("POSTGRES_USER", "postgres")
        postgres_password = values.get("POSTGRES_PASSWORD", "postgres")
        postgres_port = values.get("POSTGRES_PORT", 5432)
        postgres_db = values.get("POSTGRES_DB", "experimentation")

        # Convert port to int if it's a string
        if isinstance(postgres_port, str) and postgres_port.isdigit():
            postgres_port = int(postgres_port)

        # Build the PostgreSQL DSN
        return PostgresDsn.build(
            scheme="postgresql",
            user=postgres_user,
            password=postgres_password,
            host=postgres_server,
            port=str(postgres_port),  # Port needs to be a string for Pydantic v1
            path=f"/{postgres_db or ''}",
        )

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # Application settings
    PROJECT_NAME: str = "Experimentation Platform"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "A platform for managing experiments and feature flags"
    ENVIRONMENT: str = "dev"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # AWS settings - optional
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Admin user settings
    FIRST_SUPERUSER_EMAIL: Optional[EmailStr] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None

    # Performance settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    DB_ECHO_LOG: bool = False

    # Feature flag evaluation settings
    FEATURE_FLAG_CACHE_TTL: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **data: Any) -> None:
        """Initialize settings."""
        super().__init__(**data)
        # Ensure DATABASE_URI is set for backward compatibility
        if self.SQLALCHEMY_DATABASE_URI and not self.DATABASE_URI:
            self.DATABASE_URI = self.SQLALCHEMY_DATABASE_URI


class DevSettings(Settings):
    """Development environment settings."""

    LOG_LEVEL: str = "DEBUG"
    DEBUG: bool = True
    DB_ECHO_LOG: bool = True

    # Faster pool recycling in development
    DB_POOL_RECYCLE: int = 300  # 5 minutes

    # Shorter cache TTL for faster feedback
    FEATURE_FLAG_CACHE_TTL: int = 60  # 1 minute

    class Config:
        env_file = ".env.dev"
        env_file_encoding = "utf-8"
        case_sensitive = True


class TestSettings(Settings):
    """Testing environment settings."""

    POSTGRES_DB: str = "test_db"
    TESTING: bool = True
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    # Smaller pool for testing
    DB_POOL_SIZE: int = 2

    # No caching in tests
    FEATURE_FLAG_CACHE_TTL: int = 0

    class Config:
        env_file = ".env.test"
        env_file_encoding = "utf-8"
        case_sensitive = True


class ProdSettings(Settings):
    """Production environment settings."""

    SECRET_KEY: str
    LOG_LEVEL: str = "WARNING"
    DEBUG: bool = False
    ENVIRONMENT: str = "prod"

    # Larger pool for production
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Longer cache TTL for better performance
    FEATURE_FLAG_CACHE_TTL: int = 600  # 10 minutes

    class Config:
        env_file = ".env.prod"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_settings() -> Settings:
    """
    Get settings for the current environment.

    Returns:
        Settings: Environment-specific settings object
    """
    environment = os.getenv("ENVIRONMENT", "dev").lower()

    if environment == "prod":
        return ProdSettings()
    elif environment == "test":
        return TestSettings()
    else:
        return DevSettings()


# Create a global settings instance
settings = get_settings()
