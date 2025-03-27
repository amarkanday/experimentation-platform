# conftest.py
"""
Test configuration for the experimentation platform.

This module sets up fixtures and configuration for pytest.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import configure_mappers

from backend.app.main import app
from backend.app.db.session import get_db, Base
from backend.app.api import deps
from backend.app.models.user import User
from backend.app.models.experiment import Experiment, ExperimentStatus


@pytest.fixture(scope="session", autouse=True)
def configure_all_mappers():
    """Configure all mappers before any tests run."""
    configure_mappers()


# Create test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a clean database for testing."""
    # Create an in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Override schema-qualified table names in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        # Intercept SQLite queries that use schema-qualified names
        # This is needed because SQLite doesn't support schemas
        cursor = dbapi_connection.cursor()
        cursor.execute("ATTACH DATABASE ':memory:' AS experimentation")
        cursor.close()

    # Create all tables without schema qualification
    # Remove schema prefix for SQLite compatibility
    @event.listens_for(Base.metadata, "before_create")
    def _remove_schemas(target, connection, **kw):
        for table in target.tables.values():
            # Remove schema qualification for SQLite
            if table.schema:
                table.schema = None

    # Create all tables
    Base.metadata.create_all(engine)

    # Create a session factory
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create a scoped session
    Session = scoped_session(session_factory)

    # Create a session
    session = Session()

    yield session

    # Clean up after the test
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client for the FastAPI application."""

    # Override the get_db dependency
    def override_get_db():
        try:
            yield db
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
def normal_user(db):
    """Create a normal user for testing."""
    user = User(
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def superuser(db):
    """Create a superuser for testing."""
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def mock_auth(normal_user):
    """Mock the authentication dependencies to return a normal user."""

    def override_get_current_user():
        return normal_user

    def override_get_current_active_user():
        return normal_user

    # Set up dependency overrides
    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_current_active_user] = (
        override_get_current_active_user
    )

    yield

    # Clean up dependency overrides
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
    app.dependency_overrides[deps.get_current_active_user] = (
        override_get_current_active_user
    )
    app.dependency_overrides[deps.get_current_superuser] = (
        override_get_current_superuser
    )

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
        experiment_type="a_b",
        status=ExperimentStatus.DRAFT,
        owner_id=normal_user.id,
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
