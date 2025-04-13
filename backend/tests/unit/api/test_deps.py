from typing import Generator, Optional, AsyncGenerator, Any, Dict

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.user import User
from backend.app.services.auth_service import auth_service
from backend.app.core.cognito import map_cognito_groups_to_role, should_be_superuser
from loguru import logger
import pytest
from backend.app.models.user import UserRole

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


async def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Session: Database session
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the provided JWT token.

    Args:
        token (str): JWT access token
        db (Session): Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get user details and groups from Cognito
        user_data = auth_service.get_user_with_groups(token)

        # Get user from database
        username = user_data.get("username")
        user = db.query(User).filter(User.username == username).first()

        # Extract groups and map to role
        cognito_groups = user_data.get("groups", [])

        # Map Cognito groups to role
        role = map_cognito_groups_to_role(cognito_groups)

        # Determine superuser status from Cognito admin groups
        is_superuser = should_be_superuser(cognito_groups)

        # If superuser, ensure they have ADMIN role for full permissions
        if is_superuser and role != UserRole.ADMIN:
            role = UserRole.ADMIN
            logger.info(f"User {username} is a superuser, assigning ADMIN role")

        if not user:
            # Create user in database if not exists
            email = user_data.get("attributes", {}).get("email")
            full_name = (
                f"{user_data.get('attributes', {}).get('given_name', '')} "
                f"{user_data.get('attributes', {}).get('family_name', '')}"
            ).strip()

            user = User(
                username=username,
                email=email,
                full_name=full_name,
                is_active=True,
                role=role,
                is_superuser=is_superuser
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            logger.info(f"Created new user {username} with role {role} and superuser={is_superuser}")
        elif settings.SYNC_ROLES_ON_LOGIN:
            # Update user's role and superuser status if changed
            role_changed = user.role != role
            superuser_changed = user.is_superuser != is_superuser

            if role_changed or superuser_changed:
                # Update user properties
                if role_changed:
                    user.role = role
                    logger.info(f"User {username} role updated to {role} based on Cognito groups")

                if superuser_changed:
                    user.is_superuser = is_superuser
                    logger.info(f"User {username} superuser status updated to {is_superuser}")

                # Commit changes to database
                db.commit()
                db.refresh(user)

        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@pytest.mark.asyncio
async def test_get_current_user_with_cognito_groups(
    mock_db, mock_settings, mock_auth_service, mock_user_repository
):
    """Test getting current user with Cognito groups."""
    # Mock Cognito user response with groups
    user_data = {
        "username": "test_user",
        "attributes": {
            "sub": "test_sub_id",
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User",
        },
        "groups": ["Developers", "Analysts"]
    }
    mock_auth_service.get_user_with_groups.return_value = user_data

    # Enable role sync on login
    mock_settings.SYNC_ROLES_ON_LOGIN = True

    # Mock user does not exist in DB
    mock_user_repository.get_user_by_id.return_value = None

    # Test the function
    user = await get_current_user("test_token", mock_db)

    # Verify auth service was called correctly
    mock_auth_service.get_user_with_groups.assert_called_once_with("test_token")

    # Verify user was created with correct role (DEVELOPER from the groups)
    mock_user_repository.create_user.assert_called_once()
    created_user = mock_user_repository.create_user.call_args[0][0]
    assert created_user.email == "test@example.com"
    assert created_user.user_id == "test_sub_id"
    assert created_user.role == UserRole.DEVELOPER
    assert created_user.is_superuser is False


@pytest.mark.asyncio
async def test_get_current_user_with_admin_group(
    mock_db, mock_settings, mock_auth_service, mock_user_repository
):
    """Test getting current user with admin Cognito group."""
    # Mock Cognito user response with admin group
    user_data = {
        "username": "admin_user",
        "attributes": {
            "sub": "admin_sub_id",
            "email": "admin@example.com",
            "given_name": "Admin",
            "family_name": "User",
        },
        "groups": ["Admins"]
    }
    mock_auth_service.get_user_with_groups.return_value = user_data

    # Enable role sync on login
    mock_settings.SYNC_ROLES_ON_LOGIN = True

    # Mock user does not exist in DB
    mock_user_repository.get_user_by_id.return_value = None

    # Test the function
    user = await get_current_user("test_token", mock_db)

    # Verify user was created with admin role and superuser status
    mock_user_repository.create_user.assert_called_once()
    created_user = mock_user_repository.create_user.call_args[0][0]
    assert created_user.role == UserRole.ADMIN
    assert created_user.is_superuser is True


@pytest.mark.asyncio
async def test_get_current_user_update_role(
    mock_db, mock_settings, mock_auth_service, mock_user_repository
):
    """Test updating existing user role when Cognito groups change."""
    # Mock Cognito user response with new group
    user_data = {
        "username": "existing_user",
        "attributes": {
            "sub": "existing_sub_id",
            "email": "existing@example.com",
            "given_name": "Existing",
            "family_name": "User",
        },
        "groups": ["Analysts"]
    }
    mock_auth_service.get_user_with_groups.return_value = user_data

    # Enable role sync on login
    mock_settings.SYNC_ROLES_ON_LOGIN = True

    # Mock existing user with different role
    existing_user = User(
        id=1,
        user_id="existing_sub_id",
        email="existing@example.com",
        first_name="Existing",
        last_name="User",
        role=UserRole.VIEWER,
        is_superuser=False
    )
    mock_user_repository.get_user_by_id.return_value = existing_user

    # Test the function
    user = await get_current_user("test_token", mock_db)

    # Verify user was updated with new role
    mock_user_repository.update_user.assert_called_once()
    assert existing_user.role == UserRole.ANALYST
    assert existing_user.is_superuser is False


@pytest.mark.asyncio
async def test_get_current_user_role_sync_disabled(
    mock_db, mock_settings, mock_auth_service, mock_user_repository
):
    """Test role sync is skipped when disabled in settings."""
    # Mock Cognito user response with groups
    user_data = {
        "username": "test_user",
        "attributes": {
            "sub": "test_sub_id",
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User",
        },
        "groups": ["Developers"]
    }
    mock_auth_service.get_user_with_groups.return_value = user_data

    # Disable role sync on login
    mock_settings.SYNC_ROLES_ON_LOGIN = False

    # Mock existing user with different role
    existing_user = User(
        id=1,
        user_id="test_sub_id",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        role=UserRole.VIEWER,  # Different from Cognito group
        is_superuser=False
    )
    mock_user_repository.get_user_by_id.return_value = existing_user

    # Test the function
    user = await get_current_user("test_token", mock_db)

    # Verify user role was not updated
    assert existing_user.role == UserRole.VIEWER
    mock_user_repository.update_user.assert_not_called()


@pytest.fixture
def db_session():
    mock_session = MagicMock()
    yield mock_session
    # Optional cleanup code would go here

@pytest.fixture
def cognito_token():
    # Mock Cognito token
    token = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "cognito:groups": ["developer"]
    }
    yield token
    # Optional cleanup code would go here


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    filter = MagicMock()
    query.filter.return_value = filter
    first = MagicMock()
    filter.first.return_value = first
    return db


@pytest.fixture
def mock_auth_service():
    """Mock the auth service for testing."""
    with patch("backend.app.api.deps.auth_service") as mock_service:
        yield mock_service


@pytest.mark.asyncio
async def test_get_current_user_new_user(mock_db_session, mock_auth_service):
    """Test get_current_user creates a new user if not found."""
    # Setup
    mock_db_session.query().filter().first.return_value = None

    # Need to mock get_user_with_groups instead of get_user
    mock_auth_service.get_user_with_groups.return_value = {
        "username": "test_user",
        "attributes": {
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User"
        },
        "groups": ["Developers"]
    }

    # Mock settings
    with patch("backend.app.api.deps.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {"Developers": "developer"}
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins"]
        mock_settings.SYNC_ROLES_ON_LOGIN = True

        # Mock the core.cognito functions
        with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
            mock_map.return_value = UserRole.DEVELOPER
            with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                mock_super.return_value = False

                # Mock auth_service in deps module directly
                with patch("backend.app.api.deps.auth_service", mock_auth_service):
                    # Execute
                    user = get_current_user("test_token", mock_db_session)

                    # Verify
                    mock_auth_service.get_user_with_groups.assert_called_once_with("test_token")
                    assert mock_db_session.add.called
                    assert mock_db_session.commit.called
                    assert user.username == "test_user"
                    assert user.role == UserRole.DEVELOPER
                    assert user.is_superuser is False


@pytest.mark.asyncio
async def test_get_current_user_existing_user(mock_db_session, mock_auth_service):
    """Test get_current_user updates an existing user's role."""
    # Setup existing user
    existing_user = User(
        username="test_user",
        email="test@example.com",
        role=UserRole.VIEWER,
        is_superuser=False
    )
    mock_db_session.query().filter().first.return_value = existing_user

    # Mock Cognito response with groups
    mock_auth_service.get_user_with_groups.return_value = {
        "username": "test_user",
        "attributes": {
            "email": "test@example.com"
        },
        "groups": ["Developers"]
    }

    # Mock settings
    with patch("backend.app.api.deps.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {"Developers": "developer"}
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins"]
        mock_settings.SYNC_ROLES_ON_LOGIN = True

        # Mock the core.cognito functions
        with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
            mock_map.return_value = UserRole.DEVELOPER
            with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                mock_super.return_value = False

                # Mock auth_service in deps module directly
                with patch("backend.app.api.deps.auth_service", mock_auth_service):
                    # Execute
                    user = get_current_user("test_token", mock_db_session)

                    # Verify
                    mock_auth_service.get_user_with_groups.assert_called_once_with("test_token")
                    assert user.role == UserRole.DEVELOPER
                    assert user.is_superuser is False
                    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_get_current_user_superuser(mock_db_session, mock_auth_service):
    """Test get_current_user assigns superuser status correctly."""
    # Setup existing user
    existing_user = User(
        username="test_user",
        email="test@example.com",
        role=UserRole.VIEWER,
        is_superuser=False
    )
    mock_db_session.query().filter().first.return_value = existing_user

    # Mock Cognito response with admin groups
    mock_auth_service.get_user_with_groups.return_value = {
        "username": "test_user",
        "attributes": {
            "email": "test@example.com"
        },
        "groups": ["Admins"]
    }

    # Mock settings
    with patch("backend.app.api.deps.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {"Admins": "admin"}
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins"]
        mock_settings.SYNC_ROLES_ON_LOGIN = True

        # Mock the core.cognito functions
        with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
            mock_map.return_value = UserRole.ADMIN
            with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                mock_super.return_value = True

                # Mock auth_service in deps module directly
                with patch("backend.app.api.deps.auth_service", mock_auth_service):
                    # Execute
                    user = get_current_user("test_token", mock_db_session)

                    # Verify
                    mock_auth_service.get_user_with_groups.assert_called_once_with("test_token")
                    assert user.role == UserRole.ADMIN
                    assert user.is_superuser is True
                    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_get_current_user_superuser_role_override(mock_db_session, mock_auth_service):
    """Test superusers are assigned ADMIN role regardless of their groups."""
    # Setup existing user
    existing_user = User(
        username="test_user",
        email="test@example.com",
        role=UserRole.VIEWER,
        is_superuser=False
    )
    mock_db_session.query().filter().first.return_value = existing_user

    # Mock Cognito response with SuperUsers group that's defined as admin in COGNITO_ADMIN_GROUPS
    # but mapped to a different role in COGNITO_GROUP_ROLE_MAPPING
    mock_auth_service.get_user_with_groups.return_value = {
        "username": "test_user",
        "attributes": {
            "email": "test@example.com"
        },
        "groups": ["SuperUsers"]
    }

    # Mock settings
    with patch("backend.app.api.deps.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {"SuperUsers": "developer"}
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins", "SuperUsers"]
        mock_settings.SYNC_ROLES_ON_LOGIN = True

        # Mock the core.cognito functions
        with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
            mock_map.return_value = UserRole.DEVELOPER
            with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                mock_super.return_value = True

                # Mock auth_service in deps module directly
                with patch("backend.app.api.deps.auth_service", mock_auth_service):
                    # Execute
                    user = get_current_user("test_token", mock_db_session)

                    # Verify
                    mock_auth_service.get_user_with_groups.assert_called_once_with("test_token")
                    # User should be ADMIN despite SuperUsers mapping to developer
                    assert user.role == UserRole.ADMIN
                    assert user.is_superuser is True
                    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_get_current_user_auth_error(mock_db_session, mock_auth_service):
    """Test authentication error handling."""
    # Setup the mock to raise an exception
    mock_auth_service.get_user_with_groups.side_effect = Exception("Auth error")

    # Mock auth_service in deps module directly
    with patch("backend.app.api.deps.auth_service", mock_auth_service):
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("test_token", mock_db_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
        mock_auth_service.get_user_with_groups.assert_called_once_with("test_token")
