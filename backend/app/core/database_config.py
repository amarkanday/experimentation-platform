# backend/app/core/database_config.py
"""
Dynamic schema configuration for database models.
"""
from functools import lru_cache
from backend.app.core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_schema_name():
    """
    Dynamically determine schema name based on database configuration.
    For unit tests, always use test_experimentation schema.
    For other environments, use normalized database name.

    Returns:
        str: Schema name
    """
    # Debug logging
    logger.info(f"Environment variables: {dict(os.environ)}")
    logger.info(f"PYTEST_CURRENT_TEST: {os.environ.get('PYTEST_CURRENT_TEST')}")
    logger.info(f"POSTGRES_DB: {settings.POSTGRES_DB}")

    # Check if we're running unit tests
    if "PYTEST_CURRENT_TEST" in os.environ:
        schema_name = "test_experimentation"
        logger.info(f"Running in test environment, using schema: {schema_name}")
    else:
        schema_name = settings.POSTGRES_DB.lower().replace("-", "_")
        logger.info(f"Running in non-test environment, using schema: {schema_name}")

    return schema_name
