"""
Integration tests for Cognito authentication and role mapping.

These tests verify the complete integration flow for Cognito authentication,
including user creation, role mapping, and superuser status assignment.
"""

import pytest  # noqa: F401
from unittest.mock import patch, MagicMock

from backend.app.core.cognito import map_cognito_groups_to_role, should_be_superuser
from backend.app.models.user import User, UserRole
from backend.app.api.deps import get_current_user


class TestCognitoIntegration:
    """Test class for Cognito integration features."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session for testing."""
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        filter = MagicMock()
        query.filter.return_value = filter
        filter.first = MagicMock()
        return db

    @pytest.fixture
    def mock_auth_service(self):
        """Mock the auth service for testing."""
        with patch("backend.app.api.deps.auth_service") as mock_service:
            yield mock_service

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("backend.app.api.deps.settings") as mock_settings:
            mock_settings.COGNITO_GROUP_ROLE_MAPPING = {
                "Admins": "admin",
                "Developers": "developer",
                "Analysts": "analyst",
                "Viewers": "viewer"
            }
            mock_settings.COGNITO_ADMIN_GROUPS = ["Admins", "SuperUsers"]
            mock_settings.SYNC_ROLES_ON_LOGIN = True
            yield mock_settings

    def test_map_cognito_groups_to_admin_role(self, mock_settings):
        """Test mapping Admin Cognito group to ADMIN role."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            role = map_cognito_groups_to_role(["Admins"])
            assert role == UserRole.ADMIN

    def test_map_cognito_groups_to_developer_role(self, mock_settings):
        """Test mapping Developer Cognito group to DEVELOPER role."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            role = map_cognito_groups_to_role(["Developers"])
            assert role == UserRole.DEVELOPER

    def test_map_cognito_groups_to_analyst_role(self, mock_settings):
        """Test mapping Analyst Cognito group to ANALYST role."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            role = map_cognito_groups_to_role(["Analysts"])
            assert role == UserRole.ANALYST

    def test_map_cognito_groups_to_viewer_role(self, mock_settings):
        """Test mapping Viewer Cognito group to VIEWER role."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            role = map_cognito_groups_to_role(["Viewers"])
            assert role == UserRole.VIEWER

    def test_map_multiple_cognito_groups_to_highest_role(self, mock_settings):
        """Test mapping multiple groups to highest privilege role."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            # Mix of roles - should get highest (DEVELOPER)
            role = map_cognito_groups_to_role(["Viewers", "Analysts", "Developers"])
            assert role == UserRole.DEVELOPER

            # Mix including admin - should get ADMIN
            role = map_cognito_groups_to_role(["Viewers", "Analysts", "Admins"])
            assert role == UserRole.ADMIN

    def test_map_unknown_cognito_group_defaults_to_viewer(self, mock_settings):
        """Test unknown groups default to VIEWER role."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            role = map_cognito_groups_to_role(["UnknownGroup"])
            assert role == UserRole.VIEWER

            # Empty groups list
            role = map_cognito_groups_to_role([])
            assert role == UserRole.VIEWER

    def test_should_be_superuser_true(self, mock_settings):
        """Test superuser detection for admin groups."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            # Admin group
            assert should_be_superuser(["Admins"]) is True

            # SuperUsers group (also in admin groups)
            assert should_be_superuser(["SuperUsers"]) is True

            # Mix including admin group
            assert should_be_superuser(["Viewers", "SuperUsers", "Developers"]) is True

    def test_should_be_superuser_false(self, mock_settings):
        """Test superuser detection for non-admin groups."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            # Non-admin groups
            assert should_be_superuser(["Developers"]) is False
            assert should_be_superuser(["Analysts", "Viewers"]) is False
            assert should_be_superuser([]) is False

    def test_admin_group_override(self, mock_settings):
        """Test admin groups always map to ADMIN role regardless of mapping."""
        with patch("backend.app.core.cognito.settings", mock_settings):
            # Update mapping to make SuperUsers map to developer
            mock_settings.COGNITO_GROUP_ROLE_MAPPING["SuperUsers"] = "developer"

            # But it's in admin groups, so should still return ADMIN
            role = map_cognito_groups_to_role(["SuperUsers"])
            assert role == UserRole.ADMIN

    def test_create_new_user_from_cognito(self, mock_db_session, mock_auth_service, mock_settings):
        """Test creating a new user from Cognito authentication."""
        # Setup user not in database
        mock_db_session.query().filter().first.return_value = None

        # Mock Cognito response
        mock_auth_service.get_user_with_groups.return_value = {
            "username": "newuser",
            "attributes": {
                "email": "newuser@example.com",
                "given_name": "New",
                "family_name": "User"
            },
            "groups": ["Developers"]
        }

        # Setup patching the required components
        with patch("backend.app.api.deps.settings", mock_settings):
            with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
                mock_map.return_value = UserRole.DEVELOPER
                with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                    mock_super.return_value = False

                    # Call the function
                    user = get_current_user("test_token", mock_db_session)

                    # Verify a new user was created
                    assert mock_db_session.add.called
                    assert mock_db_session.commit.called
                    assert user.username == "newuser"
                    assert user.email == "newuser@example.com"
                    assert user.full_name == "New User"
                    assert user.role == UserRole.DEVELOPER
                    assert user.is_superuser is False

    def test_update_existing_user_role(self, mock_db_session, mock_auth_service, mock_settings):
        """Test updating an existing user's role from Cognito groups."""
        # Create existing user with different role
        existing_user = User(
            username="existinguser",
            email="existing@example.com",
            full_name="Existing User",
            role=UserRole.VIEWER,
            is_superuser=False
        )
        mock_db_session.query().filter().first.return_value = existing_user

        # Mock Cognito response with different role
        mock_auth_service.get_user_with_groups.return_value = {
            "username": "existinguser",
            "attributes": {
                "email": "existing@example.com"
            },
            "groups": ["Developers"]  # Different role than currently assigned
        }

        # Setup patching
        with patch("backend.app.api.deps.settings", mock_settings):
            with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
                mock_map.return_value = UserRole.DEVELOPER
                with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                    mock_super.return_value = False

                    # Call the function
                    user = get_current_user("test_token", mock_db_session)

                    # Verify user was updated
                    assert user.role == UserRole.DEVELOPER
                    assert user.is_superuser is False
                    assert mock_db_session.commit.called

    def test_update_user_to_superuser(self, mock_db_session, mock_auth_service, mock_settings):
        """Test updating an existing user to superuser status."""
        # Create existing regular user
        existing_user = User(
            username="regularuser",
            email="regular@example.com",
            full_name="Regular User",
            role=UserRole.DEVELOPER,
            is_superuser=False
        )
        mock_db_session.query().filter().first.return_value = existing_user

        # Mock Cognito response with admin group
        mock_auth_service.get_user_with_groups.return_value = {
            "username": "regularuser",
            "attributes": {
                "email": "regular@example.com"
            },
            "groups": ["Admins"]  # Admin group should make them superuser
        }

        # Setup patching
        with patch("backend.app.api.deps.settings", mock_settings):
            with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
                mock_map.return_value = UserRole.ADMIN
                with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                    mock_super.return_value = True

                    # Call the function
                    user = get_current_user("test_token", mock_db_session)

                    # Verify user was updated to superuser with admin role
                    assert user.role == UserRole.ADMIN
                    assert user.is_superuser is True
                    assert mock_db_session.commit.called

    def test_no_role_update_when_sync_disabled(self, mock_db_session, mock_auth_service, mock_settings):
        """Test that roles aren't updated when sync is disabled."""
        # Create existing user
        existing_user = User(
            username="nochange",
            email="nochange@example.com",
            full_name="No Change",
            role=UserRole.VIEWER,  # Will remain this even though Cognito has Developer
            is_superuser=False
        )
        mock_db_session.query().filter().first.return_value = existing_user

        # Mock Cognito response with different role
        mock_auth_service.get_user_with_groups.return_value = {
            "username": "nochange",
            "attributes": {
                "email": "nochange@example.com"
            },
            "groups": ["Developers"]  # Different from current VIEWER role
        }

        # Disable role sync
        mock_settings.SYNC_ROLES_ON_LOGIN = False

        # Setup patching
        with patch("backend.app.api.deps.settings", mock_settings):
            with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
                mock_map.return_value = UserRole.DEVELOPER
                with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                    mock_super.return_value = False

                    # Call the function
                    user = get_current_user("test_token", mock_db_session)

                    # Verify user was NOT updated (role remains VIEWER)
                    assert user.role == UserRole.VIEWER
                    assert user.is_superuser is False
                    # commit should not be called when no changes
                    assert not mock_db_session.commit.called

    def test_superuser_always_gets_admin_role(self, mock_db_session, mock_auth_service, mock_settings):
        """Test that superusers always get ADMIN role regardless of their group mapping."""
        # Create existing user
        existing_user = User(
            username="superuser",
            email="super@example.com",
            full_name="Super User",
            role=UserRole.DEVELOPER,  # Current role
            is_superuser=False  # Will be changed to True
        )
        mock_db_session.query().filter().first.return_value = existing_user

        # Mock Cognito response with SuperUsers group (admin group but mapped as developer)
        mock_auth_service.get_user_with_groups.return_value = {
            "username": "superuser",
            "attributes": {
                "email": "super@example.com"
            },
            "groups": ["SuperUsers"]  # In COGNITO_ADMIN_GROUPS but mapped as developer
        }

        # Make SuperUsers map to developer role, but still in admin groups
        mock_settings.COGNITO_GROUP_ROLE_MAPPING["SuperUsers"] = "developer"

        # Execute with real map_cognito_groups_to_role and should_be_superuser
        with patch("backend.app.api.deps.settings", mock_settings):
            # Call the function with the actual implementations
            user = get_current_user("test_token", mock_db_session)

            # Verify user was updated to ADMIN role because they're a superuser,
            # even though the group normally maps to developer
            assert user.role == UserRole.ADMIN
            assert user.is_superuser is True
            assert mock_db_session.commit.called
