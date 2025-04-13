"""
Application settings and configuration.

This module defines settings for the application based on environment variables
and sensible defaults.
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import field_validator, AnyHttpUrl, EmailStr, PostgresDsn, RedisDsn, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Base settings class."""

    PROJECT_NAME: str = "Experimentation Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "default-secret-key-for-testing"  # Default for testing
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    ENVIRONMENT: str = "dev"
    DEBUG: bool = False

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "experimentation"
    POSTGRES_PORT: str = "5432"
    POSTGRES_SCHEMA: Optional[str] = None
    DATABASE_URI: Optional[PostgresDsn] = None
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URI: Optional[RedisDsn] = None

    # User settings
    FIRST_SUPERUSER: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin"

    # Cognito settings
    COGNITO_GROUP_ROLE_MAPPING: Dict[str, str] = {
        "Admins": "admin",
        "Developers": "developer",
        "Analysts": "analyst",
        "Viewers": "viewer"
    }
    COGNITO_ADMIN_GROUPS: List[str] = ["Admins", "SuperUsers"]
    SYNC_ROLES_ON_LOGIN: bool = True

    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="allow"  # Allow extra fields
    )

    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("DATABASE_URI", mode="before")
    @classmethod
    def assemble_database_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Assemble database connection string if not provided directly."""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            port=int(info.data.get("POSTGRES_PORT", 5432)),
            path=f"/{info.data.get('POSTGRES_DB', '')}",
        )

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Assemble database connection string if not provided directly."""
        if isinstance(v, str):
            return v
        # If DATABASE_URI is set, use that
        database_uri = info.data.get("DATABASE_URI")
        if database_uri:
            return database_uri
        # Otherwise build from components
        return PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            port=int(info.data.get("POSTGRES_PORT", 5432)),
            path=f"/{info.data.get('POSTGRES_DB', '')}",
        )

    @field_validator("REDIS_URI", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Assemble Redis connection string if not provided directly."""
        if isinstance(v, str):
            return v

        # Build Redis URI components
        host = info.data.get("REDIS_HOST", "localhost")
        port = int(info.data.get("REDIS_PORT", 6379))
        password = info.data.get("REDIS_PASSWORD")

        # Construct the Redis URI
        if password:
            return f"redis://:{password}@{host}:{port}"
        return f"redis://{host}:{port}"


class DevSettings(Settings):
    """Development environment settings."""

    ENVIRONMENT: str = "dev"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CACHE_ENABLED: bool = False
    CACHE_CONTROL: Dict[str, Any] = {"enabled": False, "redis": None, "ttl": 3600}
    PROJECT_NAME: str = "Experimentation Platform (Development)"
    PROJECT_DESCRIPTION: str = "A platform for managing experiments and feature flags (Development Environment)"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "experimentation"

    model_config = SettingsConfigDict(env_file=".env.dev", case_sensitive=True, extra="allow")


class TestSettings(Settings):
    """Test environment settings."""

    ENV: str = "test"
    TESTING: bool = True
    LOG_LEVEL: str = "DEBUG"
    PROJECT_NAME: str = "Experimentation Platform"
    PROJECT_DESCRIPTION: str = "API for managing experiments and feature flags in test environment"
    DEBUG: bool = True
    POSTGRES_SERVER: str = "localhost"  # Use localhost for testing
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "experimentation_test"
    POSTGRES_SCHEMA: str = "test_experimentation"
    CACHE_ENABLED: bool = False
    CACHE_CONTROL: Dict[str, Any] = {"enabled": False, "redis": None, "ttl": 3600}

    model_config = SettingsConfigDict(env_file=".env.test", case_sensitive=True, extra="allow")


class ProdSettings(Settings):
    """Production environment settings."""

    ENVIRONMENT: str = "prod"
    PROJECT_NAME: str = "Experimentation Platform"
    PROJECT_DESCRIPTION: str = "A platform for managing experiments and feature flags"
    CACHE_ENABLED: bool = True
    CACHE_CONTROL: Dict[str, Any] = {"enabled": True, "redis": None, "ttl": 3600}

    model_config = SettingsConfigDict(env_file=".env.prod", case_sensitive=True, extra="allow")


# Select settings based on environment
environment = os.getenv("APP_ENV", "dev").lower()

if environment == "prod":
    settings = ProdSettings()
elif environment == "test":
    settings = TestSettings()
else:
    settings = DevSettings()

# Make settings accessible at module level
__all__ = ["settings", "Settings", "DevSettings", "TestSettings", "ProdSettings"]
