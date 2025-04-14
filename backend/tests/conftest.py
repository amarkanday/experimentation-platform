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
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.orm import configure_mappers

from backend.app.main import app
from backend.app.db.session import get_db, Base, init_db
from backend.app.api import deps
from backend.app.models.user import User, UserRole
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.core.database_config import get_schema_name
from backend.app.core.config import settings, TestSettings
from backend.app.models.base import set_schema
from backend.app.api.deps import CacheControl
from unittest.mock import patch, MagicMock, AsyncMock

logger = logging.getLogger(__name__)

# Default test database URL
DEFAULT_TEST_DB_URL = "postgresql://postgres:postgres@localhost:5432/experimentation_test"

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
    os.environ["POSTGRES_DB"] = "experimentation_test"
    os.environ["POSTGRES_SCHEMA"] = "test_experimentation"
    os.environ["POSTGRES_SERVER"] = "localhost"  # Changed from experimentation-postgres to localhost
    os.environ["DATABASE_URI"] = DEFAULT_TEST_DB_URL

    # Initialize test settings
    global settings
    settings = TestSettings()

    # Set schema for all tables
    set_schema()

    yield

    # Clean up
    os.environ.pop("APP_ENV", None)
    os.environ.pop("TESTING", None)
    os.environ.pop("POSTGRES_DB", None)
    os.environ.pop("POSTGRES_SCHEMA", None)
    os.environ.pop("POSTGRES_SERVER", None)
    os.environ.pop("DATABASE_URI", None)


@pytest.fixture(scope="session")
def test_db():
    """Create test database and schema."""
    # Update to use the local PostgreSQL port
    db_url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB_URL)
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Connect to default database to create test database
            temp_engine = create_engine(
                db_url.replace("experimentation_test", "postgres"),
                pool_pre_ping=True  # Add connection health check
            )

            # Test the connection
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.execute(text("COMMIT"))

                # Force close all connections to the test database
                conn.execute(text("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = 'experimentation_test'
                    AND pid <> pg_backend_pid()
                """))
                conn.execute(text("COMMIT"))

                # Now drop and recreate the database
                conn.execute(text("DROP DATABASE IF EXISTS experimentation_test"))
                conn.execute(text("CREATE DATABASE experimentation_test"))
                conn.execute(text("COMMIT"))

            # Create engine for test database with health check
            engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Add connection health check
                pool_size=5,  # Limit pool size for tests
                max_overflow=10
            )

            # Test the connection to the new database
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            # Initialize database with schema and tables
            os.environ["DATABASE_URI"] = db_url
            os.environ["APP_ENV"] = "test"
            os.environ["TESTING"] = "true"

            schema_name = "test_experimentation"

            # Create schema and tables
            with engine.connect() as conn:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                conn.execute(text(f"CREATE SCHEMA {schema_name}"))
                conn.execute(text(f"SET search_path TO {schema_name}"))
                conn.execute(text("COMMIT"))

                # Import all models to ensure they are registered with the metadata
                from backend.app.models import user, experiment, feature_flag, event, assignment

                # Set schema for all tables
                Base.metadata.schema = schema_name

                # Make sure all tables use the correct schema
                for table in Base.metadata.tables.values():
                    table.schema = schema_name

                # Create tables
                Base.metadata.create_all(bind=engine)

            # If we get here, the database is ready
            break

        except Exception as e:
            retry_count += 1
            logger.error(f"Attempt {retry_count} failed to set up test database: {e}")
            if retry_count == max_retries:
                pytest.fail(f"Failed to set up test database after {max_retries} attempts: {e}")
            import time
            time.sleep(2)  # Wait before retrying

    yield engine

    try:
        # Cleanup after all tests
        with temp_engine.connect() as conn:
            conn.execute(text("COMMIT"))

            # Force close all connections again before final cleanup
            conn.execute(text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'experimentation_test'
                AND pid <> pg_backend_pid()
            """))
            conn.execute(text("COMMIT"))

            conn.execute(text("DROP DATABASE IF EXISTS experimentation_test"))
            conn.execute(text("COMMIT"))

    except Exception as e:
        logger.error(f"Error during test database cleanup: {e}")
        # Don't fail the tests if cleanup fails


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
def client(db_session, monkeypatch):
    """Create a test client for the FastAPI application."""
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Mock Cognito auth service
    def mock_get_user_with_groups(*args, **kwargs):
        return {
            "username": "test_user",
            "attributes": {"email": "test@example.com"},
            "groups": ["admin-group"]
        }

    monkeypatch.setattr(
        "backend.app.services.auth_service.CognitoAuthService.get_user_with_groups",
        mock_get_user_with_groups
    )

    # Mock security token decoder
    def mock_decode_token(*args, **kwargs):
        return {
            "sub": "test_user_id",
            "username": "test_user",
            "email": "test@example.com"
        }

    monkeypatch.setattr(
        "backend.app.core.security.decode_token",
        mock_decode_token
    )

    # Create a superuser for authentication
    user = User(
        username="test_user",
        email="test@example.com",
        full_name="Test User",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        is_active=True,
        is_superuser=True,
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create both sync and async return functions for user
    async def override_get_current_user():
        """Override get_current_user to return a test user."""
        return user

    def override_get_current_active_user():
        """Override get_current_active_user to return a test user."""
        return user

    def override_get_current_superuser():
        """Override get_current_superuser to return a superuser."""
        return user

    async def override_get_cache_control():
        """Override cache control to disable caching in tests."""
        return CacheControl(enabled=False, skip=True)

    def override_get_api_key():
        """Override API key authentication to return a test user."""
        return user

    # Set up dependency overrides
    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[deps.get_current_superuser] = override_get_current_superuser
    app.dependency_overrides[deps.get_cache_control] = override_get_cache_control
    app.dependency_overrides[deps.get_api_key] = override_get_api_key

    # Create test client
    test_client = TestClient(app)

    yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def normal_user(db_session):
    """Create a normal user for testing."""
    user = User(
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        is_active=True,
        is_superuser=False,
        role=UserRole.DEVELOPER,
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
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        is_active=True,
        is_superuser=True,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_auth(normal_user, monkeypatch):
    """Mock the authentication dependencies."""
    async def override_get_current_user():
        return normal_user

    def override_get_current_active_user():
        return normal_user

    # Mock Cognito auth service
    def mock_get_user_with_groups(*args, **kwargs):
        return {
            "username": normal_user.username,
            "attributes": {"email": normal_user.email},
            "groups": ["developer-group"]
        }

    monkeypatch.setattr(
        "backend.app.services.auth_service.CognitoAuthService.get_user_with_groups",
        mock_get_user_with_groups
    )

    # Mock security token decoder
    def mock_decode_token(*args, **kwargs):
        return {
            "sub": str(normal_user.id),
            "username": normal_user.username,
            "email": normal_user.email
        }

    monkeypatch.setattr(
        "backend.app.core.security.decode_token",
        mock_decode_token
    )

    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_current_active_user] = override_get_current_active_user

    yield

    app.dependency_overrides.pop(deps.get_current_user, None)
    app.dependency_overrides.pop(deps.get_current_active_user, None)


@pytest.fixture
def mock_auth_superuser(superuser, monkeypatch):
    """Mock the authentication dependencies to return a superuser."""
    async def override_get_current_user():
        return superuser

    def override_get_current_active_user():
        return superuser

    def override_get_current_superuser():
        return superuser

    # Mock Cognito auth service
    def mock_get_user_with_groups(*args, **kwargs):
        return {
            "username": superuser.username,
            "attributes": {"email": superuser.email},
            "groups": ["admin-group"]
        }

    monkeypatch.setattr(
        "backend.app.services.auth_service.CognitoAuthService.get_user_with_groups",
        mock_get_user_with_groups
    )

    # Mock security token decoder
    def mock_decode_token(*args, **kwargs):
        return {
            "sub": str(superuser.id),
            "username": superuser.username,
            "email": superuser.email
        }

    monkeypatch.setattr(
        "backend.app.core.security.decode_token",
        mock_decode_token
    )

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
def test_experiment(db_session, normal_user):
    """Create a test experiment for testing."""
    experiment = Experiment(
        name="Test Experiment",
        description="A test experiment",
        hypothesis="Test hypothesis",
        owner_id=normal_user.id,
        status=ExperimentStatus.DRAFT.value,
    )
    db_session.add(experiment)
    db_session.commit()
    db_session.refresh(experiment)
    return experiment


@pytest.fixture
def active_experiment(db_session, normal_user):
    """Create an active test experiment for testing."""
    experiment = Experiment(
        name="Active Experiment",
        description="An active test experiment",
        experiment_type="a_b",
        status=ExperimentStatus.ACTIVE,
        owner_id=normal_user.id,
    )
    db_session.add(experiment)
    db_session.commit()
    db_session.refresh(experiment)
    return experiment


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock the API key dependency."""
    user = User(
        username="api_user",
        email="api@example.com",
        full_name="API User",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        is_active=True,
        is_superuser=False,
        role=UserRole.DEVELOPER,
    )

    def override_get_api_key(**kwargs):
        return user

    # Set up dependency override
    app.dependency_overrides[deps.get_api_key] = override_get_api_key

    yield

    # Clean up dependency override
    app.dependency_overrides.pop(deps.get_api_key, None)
