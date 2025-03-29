"""
Application settings and configuration.

This module defines settings for the application based on environment variables
and sensible defaults.
"""

import os
import secrets
from typing import Dict, List, Union, Optional
from pydantic import BaseSettings, PostgresDsn, validator, AnyHttpUrl


class Settings(BaseSettings):
    """Base settings class."""

    # API configuration
    API_V1_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    PROJECT_NAME: str = "Experimentation Platform"
    PROJECT_DESCRIPTION: str = "A platform for managing experiments and feature flags"
    PROJECT_VERSION: str = "1.0.0"

    # CORS settings
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "experimentation"
    POSTGRES_PORT: str = "5432"
    DATABASE_URI: Optional[PostgresDsn] = None
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    # Redis configuration (optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PREFIX: str = "expt"
    CACHE_ENABLED: bool = False

    # Environment
    ENVIRONMENT: str = "dev"

    # Authentication
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"

    # Elasticsearch configuration (optional)
    ELASTICSEARCH_HOST: Optional[str] = None
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None

    # AWS configuration (optional)
    AWS_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: Optional[str] = None
    COGNITO_CLIENT_ID: Optional[str] = None

    # Logging configuration
    LOG_LEVEL: str = "INFO"

    @validator("DATABASE_URI", pre=True, allow_reuse=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, any]) -> any:
        """
        Assemble database connection string if not provided directly.

        Args:
            v: Optional provided DATABASE_URI
            values: Other setting values

        Returns:
            Assembled database URI
        """
        if isinstance(v, str):
            return v

        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    @validator("SQLALCHEMY_DATABASE_URI", pre=True, allow_reuse=True)
    def assemble_sqlalchemy_connection(cls, v: Optional[str], values: Dict[str, any]) -> any:
        """
        Assemble SQLAlchemy database connection string if not provided directly.

        Args:
            v: Optional provided SQLALCHEMY_DATABASE_URI
            values: Other setting values

        Returns:
            Assembled database URI
        """
        if isinstance(v, str):
            return v

        # If DATABASE_URI is set, use that
        database_uri = values.get("DATABASE_URI")
        if database_uri:
            return database_uri

        # Otherwise build from components
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    @validator("CORS_ORIGINS", pre=True, allow_reuse=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parse CORS origins from string or list.

        Args:
            v: String or list of CORS origins

        Returns:
            List of allowed origins
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]

        if isinstance(v, (list, str)):
            return v

        raise ValueError(v)

    class Config:
        """Pydantic config."""

        case_sensitive = True
        env_file = ".env"


class DevSettings(Settings):
    """Development environment settings."""

    # Add development-specific settings
    ENVIRONMENT: str = "dev"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CACHE_ENABLED: bool = False

    # Project information
    PROJECT_NAME: str = "Experimentation Platform (Development)"
    PROJECT_DESCRIPTION: str = "A platform for managing experiments and feature flags (Development Environment)"

    # Override database settings for local development
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "experimentation"

    class Config:
        """Pydantic config for development."""

        env_file = ".env.dev"


class TestSettings(Settings):
    """Test environment settings."""

    # Add test-specific settings
    ENVIRONMENT: str = "test"
    TESTING: bool = True
    LOG_LEVEL: str = "DEBUG"

    # Project information
    PROJECT_NAME: str = "Experimentation Platform (Testing)"
    PROJECT_DESCRIPTION: str = "A platform for managing experiments and feature flags (Test Environment)"

    # Override database settings for testing
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "test_experimentation"

    class Config:
        """Pydantic config for testing."""

        env_file = ".env.test"


class ProdSettings(Settings):
    """Production environment settings."""

    # Add production-specific settings
    ENVIRONMENT: str = "prod"

    # Project information
    PROJECT_NAME: str = "Experimentation Platform"
    PROJECT_DESCRIPTION: str = "A platform for managing experiments and feature flags"

    # Enable caching in production
    CACHE_ENABLED: bool = True

    # More strict security in production
    CORS_ORIGINS: List[str] = ["https://app.example.com"]

    class Config:
        """Pydantic config for production."""

        env_file = ".env.prod"


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
