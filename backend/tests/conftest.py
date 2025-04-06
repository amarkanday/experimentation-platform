# conftest.py
"""
Test configuration for the experimentation platform.

This module sets up fixtures and configuration for pytest.
"""
import pytest
import os
import logging
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm import configure_mappers

from backend.app.main import app
from backend.app.db.session import get_db, Base, init_db
from backend.app.api import deps
from backend.app.models.user import User
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.core.database_config import get_schema_name
from backend.app.core.config import settings, TestSettings
from backend.app.models.base import set_schema

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def configure_all_mappers():
    """Configure all mappers before any tests run."""
    configure_mappers()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment before any tests run."""
    # Set environment variables for testing
    os.environ["APP_ENV"] = "test"
    os.environ["TESTING"] = "true"

    # Initialize test settings
    global settings
    settings = TestSettings()

    # Set schema for all tables
    set_schema()

    yield

    # Clean up
    os.environ.pop("APP_ENV", None)
    os.environ.pop("TESTING", None)


@pytest.fixture(scope="session")
def test_db():
    """Create test database and schema."""
    # Use PostgreSQL instead of SQLite to handle JSON columns properly
    db_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/experimentation_test_models",
    )

    # Create the test database
    try:
        # Connect to default database to create test database
        temp_engine = create_engine(
            db_url.replace("experimentation_test_models", "postgres")
        )
        with temp_engine.connect() as conn:
            conn.execute(text("COMMIT"))

            # Force close all connections to the test database
            conn.execute(text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'experimentation_test_models'
                AND pid <> pg_backend_pid()
            """))
            conn.execute(text("COMMIT"))

            # Now drop and recreate the database
            conn.execute(text("DROP DATABASE IF EXISTS experimentation_test_models"))
            conn.execute(text("CREATE DATABASE experimentation_test_models"))
            conn.execute(text("COMMIT"))

        # Create engine for test database
        engine = create_engine(db_url)

        # Initialize database with schema and tables
        os.environ["DATABASE_URI"] = db_url
        os.environ["APP_ENV"] = "test"
        os.environ["TESTING"] = "true"

        # Create schema and tables
        with engine.connect() as conn:
            schema_name = "test_experimentation"
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema_name}"))
            conn.execute(text(f"SET search_path TO {schema_name}"))
            conn.execute(text("COMMIT"))

            # Import all models to ensure they are registered with the metadata
            from backend.app.models import user, experiment, feature_flag, event, assignment

            # Set schema for all tables
            Base.metadata.schema = schema_name

            # Create tables
            Base.metadata.create_all(bind=engine)

        yield engine

        # Cleanup after all tests
        with temp_engine.connect() as conn:
            conn.execute(text("COMMIT"))

            # Force close all connections again before final cleanup
            conn.execute(text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'experimentation_test_models'
                AND pid <> pg_backend_pid()
            """))
            conn.execute(text("COMMIT"))

            conn.execute(text("DROP DATABASE IF EXISTS experimentation_test_models"))
            conn.execute(text("COMMIT"))

    except Exception as e:
        print(f"Error setting up test database: {e}")
        raise


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a fresh database session for a test."""
    connection = test_db.connect()
    transaction = connection.begin()

    # Create session bound to this connection
    Session = sessionmaker(bind=connection)
    session = Session()

    # Set schema for the session
    session.execute(text("SET search_path TO test_experimentation"))
    session.commit()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client for the FastAPI application."""
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Set up dependency overrides
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_db] = override_get_db

    # Create a test client
    with TestClient(app) as client:
        yield client

    # Clean up dependency overrides
    app.dependency_overrides = {}


@pytest.fixture
def normal_user(db_session):
    """Create a normal user for testing."""
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
    return user


@pytest.fixture
def superuser(db_session):
    """Create a superuser for testing."""
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
    return user


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
