from typing import List, Optional, Union, Any
from pydantic import AnyHttpUrl, field_validator, SecretStr
from pydantic_settings import BaseSettings
from pydantic_core.core_schema import ValidationInfo
from pydantic import ConfigDict
import os
from dotenv import load_dotenv

load_dotenv()  # This loads the variables from .env


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Experimentation Platform"

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Invalid CORS_ORIGINS format: {v}")

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: SecretStr = SecretStr(
        "password"
    )  # Use SecretStr for sensitive data
    POSTGRES_DB: str = "database"
    DATABASE_URI: Optional[str] = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        values = info.data
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD').get_secret_value() if isinstance(values.get('POSTGRES_PASSWORD'), SecretStr) else (values.get('POSTGRES_PASSWORD') or '')}"
            f"@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @field_validator("REDIS_PORT")
    def validate_redis_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Redis port must be between 1 and 65535")
        return v

    # AWS
    AWS_REGION: str = "us-west-2"
    COGNITO_USER_POOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "")
    COGNITO_CLIENT_ID: str = os.getenv("COGNITO_CLIENT_ID", "")

    # Security
    SECRET_KEY: SecretStr = SecretStr(
        "defaultsecret"
    )  # Use SecretStr for sensitive data
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    model_config = {
        "extra": "allow",
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "",
        "env_nested_delimiter": "__",
        "secrets_dir": None,
    }


# Create settings instance using environment variables
settings = Settings()
