# backend/app/db/session.py
"""
Database session management.

This module provides SQLAlchemy session factories and engine configuration.
It also handles database connection setup and cleanup.
"""

import logging
import os
from typing import Generator
from urllib.parse import urlparse, urlunparse

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from backend.app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Clean up the DB URI to avoid malformed paths
parsed = urlparse(os.getenv("DATABASE_URI", str(settings.SQLALCHEMY_DATABASE_URI)))
clean_path = parsed.path.replace("//", "/")
database_url = urlunparse(parsed._replace(path=clean_path))

# Create the SQLAlchemy engine with appropriate pool settings
engine_args = {
    "pool_pre_ping": True,
    "echo": settings.DEBUG,
    "poolclass": QueuePool,
    "pool_size": settings.DB_POOL_SIZE,
    "max_overflow": settings.DB_MAX_OVERFLOW,
    "pool_timeout": settings.DB_POOL_TIMEOUT,
    "pool_recycle": settings.DB_POOL_RECYCLE,
}

# Create different engines based on environment
if settings.ENVIRONMENT == "test":
    # Use a smaller pool for testing
    engine_args.update({"pool_size": 2, "max_overflow": 0})
elif settings.ENVIRONMENT == "prod":
    # Disable echoing SQL in production for security
    engine_args["echo"] = False

# Create the SQLAlchemy engine
engine = create_engine(database_url, **engine_args)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI endpoints
def get_db() -> Generator[Session, None, None]:
    """
    Get a database session for dependency injection in FastAPI endpoints.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        ```
        @app.get("/items/")
        async def read_items(db: Session = Depends(get_db)):
            ...
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_db(create_schema: bool = True, recreate_tables: bool = False) -> None:
    """
    Initialize the database with schema and tables.

    Args:
        create_schema: Whether to create the schema if it doesn't exist
        recreate_tables: Whether to drop and recreate all tables (DANGEROUS in production)
    """
    # Ensure all models are loaded before table creation
    from backend.app import models  # noqa: F401

    # Only perform schema/table creation in development and testing
    if settings.ENVIRONMENT not in ["dev", "test"] and recreate_tables:
        logger.warning("Table recreation is disabled in non-development environments")
        return

    try:
        # Create schema if needed
        if create_schema:
            logger.info(
                f"Creating schema '{settings.POSTGRES_SCHEMA}' if it doesn't exist"
            )
            with engine.connect() as conn:
                conn.execute(
                    text(f"CREATE SCHEMA IF NOT EXISTS {settings.POSTGRES_SCHEMA}")
                )
                conn.commit()

        # Recreate tables if requested
        if recreate_tables:
            logger.info(f"Rebuilding all tables for {settings.POSTGRES_SCHEMA} schema")
            # Ensure search path is set correctly
            with engine.connect() as conn:
                conn.execute(text(f"SET search_path TO {settings.POSTGRES_SCHEMA}"))
                conn.commit()

            # Drop and recreate tables
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("All tables recreated successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


# Initialize the database only in development and testing environments
# For production, use Alembic migrations instead
if settings.ENVIRONMENT in ["dev", "test"] and os.getenv("SKIP_DB_INIT") != "1":
    # This will run when the module is imported - be careful!
    try:
        initialize_db(
            create_schema=True,
            # Only recreate tables automatically in test environment
            recreate_tables=(settings.ENVIRONMENT == "test"),
        )
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
