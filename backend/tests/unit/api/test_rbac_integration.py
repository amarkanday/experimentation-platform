"""
Tests for RBAC integration with Cognito groups.

This module tests how Cognito groups map to application roles and permissions.
"""

import pytest  # noqa: F401
from unittest.mock import patch, MagicMock

from fastapi import HTTPException  # noqa: F401

from backend.app.api.deps import get_current_user
from backend.app.models.user import User, UserRole
from backend.app.core.permissions import ResourceType, Action, check_permission, check_ownership


class TestRBACIntegration:
    """Test class for RBAC integration with Cognito groups."""

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

    def test_admin_role_has_all_permissions(self, mock_settings):
        """Test that ADMIN role has all permissions for all resources."""
        # Create a user with ADMIN role
        user = User(
            username="admin_user",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_superuser=False  # Even without superuser flag, ADMIN role should have all permissions
        )

        # Test all resource types
        for resource_type in ResourceType:
            # Test all actions
            for action in Action:
                # Admin should have permission for all resources and actions
                assert check_permission(user, resource_type, action) is True

    def test_developer_role_permissions(self, mock_settings):
        """Test that DEVELOPER role has appropriate permissions."""
        # Create a user with DEVELOPER role
        user = User(
            username="developer_user",
            email="developer@example.com",
            role=UserRole.DEVELOPER,
            is_superuser=False
        )

        # Experiment permissions - should have all
        assert check_permission(user, ResourceType.EXPERIMENT, Action.CREATE) is True
        assert check_permission(user, ResourceType.EXPERIMENT, Action.READ) is True
        assert check_permission(user, ResourceType.EXPERIMENT, Action.UPDATE) is True
        assert check_permission(user, ResourceType.EXPERIMENT, Action.DELETE) is True
        assert check_permission(user, ResourceType.EXPERIMENT, Action.LIST) is True

        # Feature flag permissions - should have all
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.CREATE) is True
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.READ) is True
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.UPDATE) is True
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.DELETE) is True
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.LIST) is True

        # User permissions - should have READ and LIST only
        assert check_permission(user, ResourceType.USER, Action.READ) is True
        assert check_permission(user, ResourceType.USER, Action.LIST) is True
        assert check_permission(user, ResourceType.USER, Action.CREATE) is False
        assert check_permission(user, ResourceType.USER, Action.UPDATE) is False
        assert check_permission(user, ResourceType.USER, Action.DELETE) is False

    def test_analyst_role_permissions(self, mock_settings):
        """Test that ANALYST role has appropriate permissions."""
        # Create a user with ANALYST role
        user = User(
            username="analyst_user",
            email="analyst@example.com",
            role=UserRole.ANALYST,
            is_superuser=False
        )

        # Experiment permissions - should have READ and LIST only
        assert check_permission(user, ResourceType.EXPERIMENT, Action.READ) is True
        assert check_permission(user, ResourceType.EXPERIMENT, Action.LIST) is True
        assert check_permission(user, ResourceType.EXPERIMENT, Action.CREATE) is False
        assert check_permission(user, ResourceType.EXPERIMENT, Action.UPDATE) is False
        assert check_permission(user, ResourceType.EXPERIMENT, Action.DELETE) is False

        # Feature flag permissions - should have READ and LIST only
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.READ) is True
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.LIST) is True
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.CREATE) is False
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.UPDATE) is False
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.DELETE) is False

        # Report permissions - should have all
        assert check_permission(user, ResourceType.REPORT, Action.CREATE) is True
        assert check_permission(user, ResourceType.REPORT, Action.READ) is True
        assert check_permission(user, ResourceType.REPORT, Action.UPDATE) is True
        assert check_permission(user, ResourceType.REPORT, Action.DELETE) is True
        assert check_permission(user, ResourceType.REPORT, Action.LIST) is True

    def test_viewer_role_permissions(self, mock_settings):
        """Test that VIEWER role has appropriate permissions."""
        # Create a user with VIEWER role
        user = User(
            username="viewer_user",
            email="viewer@example.com",
            role=UserRole.VIEWER,
            is_superuser=False
        )

        # For most resources, VIEWER should have READ and LIST permissions only
        for resource_type in ResourceType:
            # VIEWERs can READ all resources
            assert check_permission(user, resource_type, Action.READ) is True, f"VIEWER should have READ permission for {resource_type}"

            # VIEWERs cannot CREATE, UPDATE, or DELETE any resources
            assert check_permission(user, resource_type, Action.CREATE) is False, f"VIEWER should NOT have CREATE permission for {resource_type}"
            assert check_permission(user, resource_type, Action.UPDATE) is False, f"VIEWER should NOT have UPDATE permission for {resource_type}"
            assert check_permission(user, resource_type, Action.DELETE) is False, f"VIEWER should NOT have DELETE permission for {resource_type}"

            # Special handling for LIST permission based on actual RBAC configuration
            if resource_type in [ResourceType.USER, ResourceType.ROLE, ResourceType.PERMISSION]:
                # According to RBAC configuration, VIEWERs can READ these resources but not LIST them
                assert check_permission(user, resource_type, Action.LIST) is False, f"VIEWER should NOT have LIST permission for {resource_type}"
            else:
                # For other resources (EXPERIMENT, FEATURE_FLAG, REPORT), VIEWERs should have LIST permission
                assert check_permission(user, resource_type, Action.LIST) is True, f"VIEWER should have LIST permission for {resource_type}"

    def test_superuser_overrides_role_permissions(self, mock_settings):
        """Test that superuser flag overrides role-based permissions."""
        # Create a user with VIEWER role but superuser flag
        user = User(
            username="super_viewer",
            email="super_viewer@example.com",
            role=UserRole.VIEWER,  # Lowest privilege role
            is_superuser=True      # But superuser flag is set
        )

        # Should have all permissions regardless of role
        for resource_type in ResourceType:
            for action in Action:
                assert check_permission(user, resource_type, action) is True, f"Superuser should have {action} permission for {resource_type}"

    def test_ownership_check(self, mock_settings):
        """Test that ownership check works correctly."""
        # Create a user
        user = User(
            id=1,  # Use a simple ID for testing
            username="owner_user",
            email="owner@example.com",
            role=UserRole.VIEWER,  # Limited permissions
            is_superuser=False
        )

        # Create a resource the user owns
        owned_resource = MagicMock()
        owned_resource.owner_id = 1  # Same as user ID

        # Create a resource the user doesn't own
        other_resource = MagicMock()
        other_resource.owner_id = 2  # Different ID

        # Check ownership
        assert check_ownership(user, owned_resource) is True
        assert check_ownership(user, other_resource) is False

    def test_cognito_groups_to_permissions_flow(self, mock_db_session, mock_auth_service, mock_settings):
        """Test the complete flow from Cognito groups to application permissions."""
        # Mock the Cognito response with developer group
        mock_auth_service.get_user_with_groups.return_value = {
            "username": "dev_user",
            "attributes": {
                "email": "dev@example.com"
            },
            "groups": ["Developers"]
        }

        # Also mock the get_user method which is called first
        mock_auth_service.get_user.return_value = {
            "username": "dev_user",
            "attributes": {
                "email": "dev@example.com"
            }
        }

        # Create a new user (not in DB)
        mock_db_session.query().filter().first.return_value = None

        # Call get_current_user to create the user based on Cognito groups
        with patch("backend.app.api.deps.settings", mock_settings):
            with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
                mock_map.return_value = UserRole.DEVELOPER
                with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                    mock_super.return_value = False

                    # Call the function
                    user = get_current_user("test-token", mock_db_session)

                    # Verify user was created with correct role
                    assert user.role == UserRole.DEVELOPER

                    # Verify permissions based on the role
                    assert check_permission(user, ResourceType.EXPERIMENT, Action.CREATE) is True
                    assert check_permission(user, ResourceType.FEATURE_FLAG, Action.UPDATE) is True
                    assert check_permission(user, ResourceType.USER, Action.CREATE) is False
                    assert check_permission(user, ResourceType.REPORT, Action.READ) is True

    def test_coginto_admin_group_to_superuser(self, mock_db_session, mock_auth_service, mock_settings):
        """Test that users in Cognito admin groups get superuser status."""
        # Mock the Cognito response with admin group
        mock_auth_service.get_user_with_groups.return_value = {
            "username": "admin_user",
            "attributes": {
                "email": "admin@example.com"
            },
            "groups": ["Admins"]  # In COGNITO_ADMIN_GROUPS
        }

        # Also mock the get_user method which is called first
        mock_auth_service.get_user.return_value = {
            "username": "admin_user",
            "attributes": {
                "email": "admin@example.com"
            }
        }

        # Create a new user (not in DB)
        mock_db_session.query().filter().first.return_value = None

        # Call get_current_user to create the user based on Cognito groups
        with patch("backend.app.api.deps.settings", mock_settings):
            with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
                mock_map.return_value = UserRole.ADMIN
                with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                    mock_super.return_value = True

                    # Call the function
                    user = get_current_user("test-token", mock_db_session)

                    # Verify user was created with admin role and superuser status
                    assert user.role == UserRole.ADMIN
                    assert user.is_superuser is True

                    # Verify all permissions are granted
                    for resource_type in ResourceType:
                        for action in Action:
                            assert check_permission(user, resource_type, action) is True

    def test_role_changes_with_cognito_group_changes(self, mock_db_session, mock_auth_service, mock_settings):
        """Test that user roles update when Cognito groups change."""
        # Create existing user with VIEWER role
        existing_user = User(
            username="changing_user",
            email="changing@example.com",
            role=UserRole.VIEWER,
            is_superuser=False
        )
        mock_db_session.query().filter().first.return_value = existing_user

        # Mock the Cognito response with new role (developer)
        mock_auth_service.get_user_with_groups.return_value = {
            "username": "changing_user",
            "attributes": {
                "email": "changing@example.com"
            },
            "groups": ["Developers"]  # Now in Developers group
        }

        # Also mock the get_user method which is called first
        mock_auth_service.get_user.return_value = {
            "username": "changing_user",
            "attributes": {
                "email": "changing@example.com"
            }
        }

        # Call get_current_user to update the user based on new Cognito groups
        with patch("backend.app.api.deps.settings", mock_settings):
            with patch("backend.app.api.deps.map_cognito_groups_to_role") as mock_map:
                mock_map.return_value = UserRole.DEVELOPER
                with patch("backend.app.api.deps.should_be_superuser") as mock_super:
                    mock_super.return_value = False

                    # Call the function
                    user = get_current_user("test-token", mock_db_session)

                    # Verify user was updated with new role
                    assert user.role == UserRole.DEVELOPER

                    # Verify permissions reflect the new role
                    assert check_permission(user, ResourceType.EXPERIMENT, Action.CREATE) is True  # Developer can create
                    assert check_permission(user, ResourceType.USER, Action.CREATE) is False  # But can't create users
