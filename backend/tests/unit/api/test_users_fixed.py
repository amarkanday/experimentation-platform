# backend/tests/unit/api/test_users_fixed.py
import pytest
import uuid
from unittest.mock import MagicMock, patch
from fastapi import status, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pydantic import SecretStr
from datetime import datetime, timezone

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.api.deps import get_current_active_user, get_current_superuser, get_db
from backend.app.main import app
from backend.app.core.security import get_password_hash


@pytest.fixture
def mock_db():
    """Mock database session."""
    mock = MagicMock()
    # Ensure the mock is returned from get_db dependency
    app.dependency_overrides[get_db] = lambda: mock
    yield mock
    # Clean up dependency override
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture
def normal_user():
    """Create a normal (non-superuser) test user."""
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        preferences={},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def superuser():
    """Create a superuser test user."""
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=True,
        preferences={},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_db_query(mock_db):
    """Mock the database query functionality."""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    return mock_query


@pytest.fixture
def client():
    """Create a test client with mocked dependencies."""
    return TestClient(app)


@patch("backend.app.api.v1.endpoints.users.get_password_hash")
def test_update_user_superuser(
    mock_hash, client, mock_db, mock_db_query, superuser, normal_user
):
    """Test that superusers can update any user."""
    # Setup mocks
    mock_hash.return_value = "new_hashed_password"
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = normal_user

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: superuser
    app.dependency_overrides[get_current_superuser] = lambda: superuser
    app.dependency_overrides[get_db] = lambda: mock_db

    # Make request
    update_data = {
        "username": normal_user.username,
        "email": normal_user.email,
        "full_name": "Updated Name",
        "password": "Newpassword123",  # Must meet validator requirements
        "is_superuser": True,
    }
    response = client.put(f"/api/v1/users/{normal_user.id}", json=update_data)

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["is_superuser"] == update_data["is_superuser"]

    # Verify mock calls
    assert mock_hash.call_count == 1
    assert isinstance(mock_hash.call_args[0][0], SecretStr)
    mock_db.commit.assert_called_once()

    # Reset overrides
    app.dependency_overrides = {}


def test_update_user_self(client, mock_db, mock_db_query, normal_user):
    """Test that users can update their own non-privileged fields."""
    # Setup mocks
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = normal_user

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: normal_user
    app.dependency_overrides[get_db] = lambda: mock_db

    # Make request
    update_data = {
        "username": normal_user.username,
        "email": normal_user.email,
        "full_name": "Updated Name",
        "is_superuser": True,  # Should be ignored for normal users
    }
    response = client.put(f"/api/v1/users/{normal_user.id}", json=update_data)

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["is_superuser"] == False  # Should not be changed

    # Reset overrides
    app.dependency_overrides = {}


def test_create_user_existing_username(client, mock_db):
    # Setup the DB query mock to simulate the check for existing username
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value = mock_query

    # First return None for the email check, then return a user for the username check
    existing_user = MagicMock()
    existing_user.username = "testuser"
    mock_query.first.side_effect = [None, existing_user]

    # Setup superuser authentication
    superuser = MagicMock()
    superuser.is_superuser = True
    app.dependency_overrides[get_current_active_user] = lambda: superuser
    app.dependency_overrides[get_current_superuser] = lambda: superuser
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "email": "unique@example.com",
            "full_name": "Test User",
            "password": "StrongPass123",  # Plain password
        },
    )

    # Reset overrides
    app.dependency_overrides = {}

    assert response.status_code == 409, response.text


def test_create_user_existing_email(client, mock_db):
    # Setup the DB query mock to simulate the check for existing email
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value = mock_query

    # Return a user for the email check to simulate email already exists
    existing_user = MagicMock()
    existing_user.email = "test@example.com"
    mock_query.first.return_value = existing_user

    # Setup superuser authentication
    superuser = MagicMock()
    superuser.is_superuser = True
    app.dependency_overrides[get_current_active_user] = lambda: superuser
    app.dependency_overrides[get_current_superuser] = lambda: superuser
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.post(
        "/api/v1/users/",
        json={
            "username": "uniqueuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "StrongPass123",  # Plain password
        },
    )

    # Reset overrides
    app.dependency_overrides = {}

    assert response.status_code == 409, response.text
