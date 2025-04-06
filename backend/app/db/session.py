"""
Database session and connection management.

This module provides database session functionality and connection pooling
for the application.
"""

import os
from typing import Generator
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.models.base import Base
from backend.app.core.database_config import get_schema_name

# Check for DATABASE_URI environment variable, otherwise use settings
database_uri = os.getenv("DATABASE_URI")
if not database_uri:
    # Fall back to SQLALCHEMY_DATABASE_URI if set
    if hasattr(settings, "SQLALCHEMY_DATABASE_URI") and settings.SQLALCHEMY_DATABASE_URI:
        database_uri = str(settings.SQLALCHEMY_DATABASE_URI)
    # Fall back to DATABASE_URI if set
    elif hasattr(settings, "DATABASE_URI") and settings.DATABASE_URI:
        database_uri = str(settings.DATABASE_URI)
    # Fall back to constructing from components
    else:
        database_uri = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Create engine with appropriate configuration
engine = create_engine(
    database_uri,
    pool_pre_ping=True,  # Test connections before using them
    pool_size=5,  # Reasonable default for most applications
    max_overflow=10,  # Allow up to 10 additional connections
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_db() -> Generator:
    """
    Get a database session.

    Yields:
        Generator: A SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    # Import all models here to ensure they are registered with the metadata
    from backend.app.models import user, experiment, feature_flag, event, assignment

    # Get schema name
    schema_name = get_schema_name()

    # Create schema if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        conn.execute(text("COMMIT"))

        # Set search path
        conn.execute(text(f"SET search_path TO {schema_name}"))
        conn.execute(text("COMMIT"))

    # Set schema for all tables
    Base.metadata.schema = schema_name

    # Create tables
    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    """Reset the database by dropping and recreating all tables."""
    # Import all models here to ensure they are registered with the metadata
    from backend.app.models import user, experiment, feature_flag, event, assignment

    # Get schema name
    schema_name = get_schema_name()

    # Set schema for all tables
    Base.metadata.schema = schema_name

    # Drop and recreate tables
    Base.metadata.drop_all(bind=engine)

    # Create schema if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        conn.execute(text("COMMIT"))

        # Set search path
        conn.execute(text(f"SET search_path TO {schema_name}"))
        conn.execute(text("COMMIT"))

    # Create tables
    Base.metadata.create_all(bind=engine)
