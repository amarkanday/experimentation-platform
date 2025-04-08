# conftest.py
"""
Test configuration for the experimentation platform.

This module sets up fixtures and configuration for pytest.
"""
import os
import logging
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, configure_mappers
from sqlalchemy.exc import ProgrammingError

from backend.app.core.config import settings, TestSettings
from backend.app.core.database_config import get_schema_name
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.api.deps import get_db
from backend.app.api import deps  # Added for mock fixtures
from backend.app.models.user import User
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.models.base import set_schema

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def configure_all_mappers() -> None:
    """Configure all mappers before any database operations."""
    configure_mappers()


@pytest.fixture(scope="session")
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "1"
    os.environ["POSTGRES_DB"] = "test_db"
    os.environ["POSTGRES_USER"] = "test_user"
    os.environ["POSTGRES_PASSWORD"] = "test_password"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"


@pytest.fixture(scope="session")
def test_db(setup_test_environment):
    """Create a test database and set up tables."""
    schema_name = get_schema_name()
    database_url = f"postgresql://test_user:test_password@localhost:5432/test_db"
    engine = create_engine(database_url, isolation_level="AUTOCOMMIT")

    try:
        # Try to connect first
        with engine.connect() as conn:
            # Create schema if it doesn't exist
            try:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
            except ProgrammingError as e:
                logger.warning(f"Schema creation error (may already exist): {e}")

        # Create all tables
        Base.metadata.create_all(bind=engine)

        yield engine

        # Cleanup - Drop the entire schema with CASCADE to handle all dependencies
        with engine.connect() as conn:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            conn.commit()
            # Recreate empty schema for next test run
            conn.execute(text(f"CREATE SCHEMA {schema_name}"))
            conn.commit()

    except Exception as e:
        logger.error(f"Error in test database setup/cleanup: {e}")
        raise


@pytest.fixture(scope="function")
def db_session(test_db) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    connection = test_db.connect()
    transaction = connection.begin()

    # Create session with specific schema
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    # Set schema globally
    set_schema()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def normal_user(db_session):
    """Create a normal user for testing."""
    # First clean up any existing test user
    try:
        existing_user = db_session.query(User).filter(User.username == "testuser").first()
        if existing_user:
            db_session.delete(existing_user)
            db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.warning(f"Error cleaning up existing test user: {e}")

    # Create new test user
    user = User(
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    # Cleanup after test
    try:
        db_session.delete(user)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.warning(f"Error cleaning up test user: {e}")


@pytest.fixture
def superuser(db_session):
    """Create a superuser for testing."""
    # First clean up any existing admin user
    try:
        existing_user = db_session.query(User).filter(User.username == "admin").first()
        if existing_user:
            db_session.delete(existing_user)
            db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.warning(f"Error cleaning up existing admin user: {e}")

    # Create new admin user
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    # Cleanup after test
    try:
        db_session.delete(user)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.warning(f"Error cleaning up admin user: {e}")


@pytest.fixture
def mock_auth(normal_user):
    """Mock the authentication dependencies."""
    def override_get_current_user():
        return normal_user

    def override_get_current_active_user():
        return normal_user

    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_current_active_user] = override_get_current_active_user

    yield

    app.dependency_overrides.pop(deps.get_current_user, None)
    app.dependency_overrides.pop(deps.get_current_active_user, None)


@pytest.fixture
def mock_auth_superuser(superuser):
    """Mock the authentication dependencies to return a superuser."""
    def override_get_current_user():
        return superuser

    def override_get_current_active_user():
        return superuser

    def override_get_current_superuser():
        return superuser

    # Set up dependency overrides
    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[deps.get_current_superuser] = override_get_current_superuser

    yield

    # Clean up dependency overrides
    app.dependency_overrides.pop(deps.get_current_user, None)
    app.dependency_overrides.pop(deps.get_current_active_user, None)
    app.dependency_overrides.pop(deps.get_current_superuser, None)


@pytest.fixture
def test_experiment(db, normal_user):
    """Create a test experiment for testing."""
    experiment = Experiment(
        name="Test Experiment",
        description="A test experiment",
        hypothesis="Test hypothesis",
        owner_id=normal_user.id,
        status=ExperimentStatus.DRAFT.value,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@pytest.fixture
def active_experiment(db, normal_user):
    """Create an active test experiment for testing."""
    experiment = Experiment(
        name="Active Experiment",
        description="An active test experiment",
        experiment_type="a_b",
        status=ExperimentStatus.ACTIVE,
        owner_id=normal_user.id,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@pytest.fixture
def mock_api_key():
    """Mock the API key dependency."""

    def override_get_api_key(**kwargs):
        return {"key": "test_api_key", "valid": True}

    # Set up dependency override
    app.dependency_overrides[deps.get_api_key] = override_get_api_key

    yield

    # Clean up dependency override
    app.dependency_overrides.pop(deps.get_api_key, None)
