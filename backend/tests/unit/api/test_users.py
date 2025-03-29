# backend/tests/unit/api/test_users.py
import pytest
from unittest.mock import MagicMock, patch
import uuid
from fastapi import status, HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr
from datetime import datetime, timezone

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.api.deps import get_current_active_user, get_current_superuser, get_db
from backend.app.main import app


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


def test_list_users_superuser(client, mock_db, mock_db_query, superuser):
    """Test that superusers can list all users."""
    # Setup mocks
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.offset.return_value = mock_db_query
    # Important: Return a list directly, not something with .all() method
    mock_db_query.limit.return_value = [superuser]
    mock_db_query.count.return_value = 1

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: superuser
    app.dependency_overrides[get_current_superuser] = lambda: superuser
    app.dependency_overrides[get_db] = lambda: mock_db

    # Make request
    response = client.get("/api/v1/users/")

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["username"] == superuser.username
    assert data["total"] == 1

    # Reset overrides
    app.dependency_overrides = {}


def test_delete_self_superuser(client, mock_db, mock_db_query, superuser):
    """Test that superusers cannot delete themselves."""
    # Setup mocks
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = superuser

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: superuser
    app.dependency_overrides[get_current_superuser] = lambda: superuser
    app.dependency_overrides[get_db] = lambda: mock_db

    # Make request
    response = client.delete(f"/api/v1/users/{superuser.id}")

    # Verify response - should be bad request
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Verify mock calls - delete should not be called
    mock_db.delete.assert_not_called()

    # Reset overrides
    app.dependency_overrides = {}


def test_delete_self_normal(client, mock_db, mock_db_query, normal_user):
    """Test that normal users can delete themselves."""
    # Setup mocks
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = normal_user

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: normal_user
    app.dependency_overrides[get_db] = lambda: mock_db

    # Make request
    response = client.delete(f"/api/v1/users/{normal_user.id}")

    # Verify response
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify mock calls
    mock_db.delete.assert_called_once_with(normal_user)
    mock_db.commit.assert_called_once()

    # Reset overrides
    app.dependency_overrides = {}


def test_me_endpoint(client, normal_user):
    """Test the /me endpoint."""
    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: normal_user
    app.dependency_overrides[get_db] = lambda: MagicMock()

    # Make request
    response = client.get("/api/v1/users/me")

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == normal_user.username
    assert data["email"] == normal_user.email

    # Reset overrides
    app.dependency_overrides = {}


def test_list_users_normal_user(client, mock_db, normal_user):
    """Test that normal users can only see themselves."""
    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: normal_user

    # Make request
    response = client.get("/api/v1/users/")

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["username"] == normal_user.username
    assert data["total"] == 1

    # Reset overrides
    app.dependency_overrides = {}


@patch("backend.app.api.v1.endpoints.users.get_password_hash")
def test_create_user_superuser(mock_hash, client, mock_db, superuser):
    """Test that superusers can create new users."""
    # Setup mocks
    mock_hash.return_value = "hashed_password"
    mock_db_query = mock_db.query.return_value
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = None  # User doesn't exist

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: superuser
    app.dependency_overrides[get_current_superuser] = lambda: superuser

    # Make request with proper UserCreate model structure
    new_user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Password123",  # Must meet validator requirements
        "full_name": "New User",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/v1/users/", json=new_user_data)

    # Verify response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == new_user_data["username"]
    assert data["email"] == new_user_data["email"]
    assert "password" not in data  # Password should not be in response

    # Verify mock calls
    mock_hash.assert_called_once_with("Password123")
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

    # Reset overrides
    app.dependency_overrides = {}


def test_create_user_normal_user(client, mock_db, normal_user):
    """Test that normal users cannot create new users."""
    # Setup mocks - this is important to handle the forbidden case properly
    mock_db_query = mock_db.query.return_value
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = None  # User doesn't exist

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: normal_user
    # Important: Do NOT override get_current_superuser - it should fail naturally

    # Make request with proper UserCreate model structure
    new_user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Password123",  # Must meet validator requirements
        "full_name": "New User",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/v1/users/", json=new_user_data)

    # Verify response - should be forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Reset overrides
    app.dependency_overrides = {}


def test_get_user_superuser(client, mock_db, mock_db_query, superuser, normal_user):
    """Test that superusers can get any user."""
    # Setup mocks
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = normal_user

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: superuser
    app.dependency_overrides[get_db] = lambda: mock_db

    # Make request
    response = client.get(f"/api/v1/users/{normal_user.id}")

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == normal_user.username

    # Reset overrides
    app.dependency_overrides = {}


def test_get_user_self(client, mock_db, normal_user):
    """Test that users can get their own data."""
    # Setup mocks
    mock_db_query = mock_db.query.return_value
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = normal_user

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: normal_user
    app.dependency_overrides[get_db] = lambda: mock_db

    # Make request
    response = client.get(f"/api/v1/users/{normal_user.id}")

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == normal_user.username

    # Reset overrides
    app.dependency_overrides = {}


def test_get_user_other(client, mock_db, mock_db_query, normal_user):
    """Test that normal users cannot get other users' data."""
    # Setup other user
    other_user = User(
        id=uuid.uuid4(),
        username="otheruser",
        email="other@example.com",
        full_name="Other User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Setup mocks
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = other_user

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: normal_user

    # Make request
    response = client.get(f"/api/v1/users/{other_user.id}")

    # Verify response - should be forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Reset overrides
    app.dependency_overrides = {}


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
    app.dependency_overrides[get_db] = lambda: mock_db

    # Make request
    update_data = {
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
    mock_hash.assert_called_once_with("Newpassword123")
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


def test_delete_user_superuser(client, mock_db, mock_db_query, superuser, normal_user):
    """Test that superusers can delete other users."""
    # Setup mocks
    mock_db_query.filter.return_value = mock_db_query
    mock_db_query.first.return_value = normal_user

    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: superuser
    app.dependency_overrides[get_current_superuser] = lambda: superuser

    # Make request
    response = client.delete(f"/api/v1/users/{normal_user.id}")

    # Verify response
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify mock calls
    mock_db.delete.assert_called_once_with(normal_user)
    mock_db.commit.assert_called_once()
