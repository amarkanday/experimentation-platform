# backend/app/core/database_config.py
"""
Dynamic schema configuration for database models.
"""
from functools import lru_cache
from backend.app.core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

# Add this to backend/app/core/database_config.py
def clear_schema_cache():
    """Clear the cached schema name."""
    get_schema_name.cache_clear()


@lru_cache(maxsize=1)
def get_schema_name() -> str:
    """Get the schema name based on the environment."""
    if os.environ.get("APP_ENV") == "test" or os.environ.get("TESTING") == "true":
        schema_name = "test_experimentation"
    else:
        schema_name = "experimentation"
    logger.debug(f"Using schema: {schema_name}")
    return schema_name
