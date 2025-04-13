import pytest

from backend.app.core.permissions import (
    ResourceType,
    Action,
    has_permission,
    check_permission,
    check_ownership,
    get_permission_error_message,
    get_required_role
)
from backend.app.models.user import UserRole


@pytest.fixture
def admin_user(mocker):
    """Create a mock admin user."""
    user = mocker.MagicMock()
    user.role = UserRole.ADMIN
    user.is_superuser = False
    user.id = "admin-id"
    return user


@pytest.fixture
def developer_user(mocker):
    """Create a mock developer user."""
    user = mocker.MagicMock()
    user.role = UserRole.DEVELOPER
    user.is_superuser = False
    user.id = "developer-id"
    return user


@pytest.fixture
def analyst_user(mocker):
    """Create a mock analyst user."""
    user = mocker.MagicMock()
    user.role = UserRole.ANALYST
    user.is_superuser = False
    user.id = "analyst-id"
    return user


@pytest.fixture
def viewer_user(mocker):
    """Create a mock viewer user."""
    user = mocker.MagicMock()
    user.role = UserRole.VIEWER
    user.is_superuser = False
    user.id = "viewer-id"
    return user


@pytest.fixture
def superuser(mocker):
    """Create a mock superuser."""
    user = mocker.MagicMock()
    user.role = UserRole.ADMIN
    user.is_superuser = True
    user.id = "superuser-id"
    return user


class TestHasPermission:
    """Tests for the has_permission function."""

    def test_admin_has_permission(self):
        """Test that admin has all permissions for all resources."""
        for resource in ResourceType:
            for action in Action:
                assert has_permission(UserRole.ADMIN, resource, action)

    def test_developer_permissions(self):
        """Test specific developer permissions."""
        # Developer can create experiments
        assert has_permission(UserRole.DEVELOPER, ResourceType.EXPERIMENT, Action.CREATE)
        # Developer can create feature flags
        assert has_permission(UserRole.DEVELOPER, ResourceType.FEATURE_FLAG, Action.CREATE)
        # Developer cannot create users
        assert not has_permission(UserRole.DEVELOPER, ResourceType.USER, Action.CREATE)

    def test_analyst_permissions(self):
        """Test specific analyst permissions."""
        # Analyst can read experiments but not create them
        assert has_permission(UserRole.ANALYST, ResourceType.EXPERIMENT, Action.READ)
        assert not has_permission(UserRole.ANALYST, ResourceType.EXPERIMENT, Action.CREATE)

        # Analyst can create reports
        assert has_permission(UserRole.ANALYST, ResourceType.REPORT, Action.CREATE)

    def test_viewer_permissions(self):
        """Test specific viewer permissions."""
        # Viewer can read experiments but not edit them
        assert has_permission(UserRole.VIEWER, ResourceType.EXPERIMENT, Action.READ)
        assert not has_permission(UserRole.VIEWER, ResourceType.EXPERIMENT, Action.UPDATE)


class TestCheckPermission:
    """Tests for the check_permission function."""

    def test_superuser_permission(self, superuser):
        """Test that superuser has all permissions."""
        for resource in ResourceType:
            for action in Action:
                assert check_permission(superuser, resource, action)

    def test_admin_permission(self, admin_user):
        """Test admin user permissions."""
        assert check_permission(admin_user, ResourceType.EXPERIMENT, Action.CREATE)
        assert check_permission(admin_user, ResourceType.USER, Action.CREATE)

    def test_developer_permission(self, developer_user):
        """Test developer user permissions."""
        assert check_permission(developer_user, ResourceType.EXPERIMENT, Action.CREATE)
        assert not check_permission(developer_user, ResourceType.USER, Action.CREATE)

    def test_analyst_permission(self, analyst_user):
        """Test analyst user permissions."""
        assert not check_permission(analyst_user, ResourceType.EXPERIMENT, Action.CREATE)
        assert check_permission(analyst_user, ResourceType.REPORT, Action.CREATE)

    def test_viewer_permission(self, viewer_user):
        """Test viewer user permissions."""
        assert check_permission(viewer_user, ResourceType.EXPERIMENT, Action.READ)
        assert not check_permission(viewer_user, ResourceType.EXPERIMENT, Action.CREATE)

    def test_user_with_no_role(self, mocker):
        """Test a user with no role defaults to viewer permissions."""
        # Create a simple object instead of MagicMock since MagicMock has special handling
        class SimpleUser:
            pass

        user = SimpleUser()
        user.is_superuser = False

        # Should have viewer permissions
        assert check_permission(user, ResourceType.EXPERIMENT, Action.READ)
        assert check_permission(user, ResourceType.FEATURE_FLAG, Action.READ)

        # Should not have higher permissions
        assert not check_permission(user, ResourceType.EXPERIMENT, Action.CREATE)
        assert not check_permission(user, ResourceType.FEATURE_FLAG, Action.UPDATE)


class TestCheckOwnership:
    """Tests for the check_ownership function."""

    def test_user_owns_resource(self, admin_user, mocker):
        """Test that a user owns a resource with their ID."""
        resource = mocker.MagicMock()
        resource.owner_id = "admin-id"

        assert check_ownership(admin_user, resource)

    def test_user_does_not_own_resource(self, admin_user, developer_user, mocker):
        """Test that a user does not own a resource with someone else's ID."""
        resource = mocker.MagicMock()
        resource.owner_id = developer_user.id

        assert not check_ownership(admin_user, resource)

    def test_resource_without_owner_id(self, admin_user, mocker):
        """Test handling resource without owner_id attribute."""
        resource = mocker.MagicMock(spec=[])
        # No owner_id attribute

        assert not check_ownership(admin_user, resource)


class TestGetPermissionErrorMessage:
    """Tests for the get_permission_error_message function."""

    def test_error_message_formatting(self):
        """Test that error messages are properly formatted."""
        message = get_permission_error_message(ResourceType.EXPERIMENT, Action.CREATE)
        assert message == "You don't have permission to create experiments"

        message = get_permission_error_message(ResourceType.FEATURE_FLAG, Action.UPDATE)
        assert message == "You don't have permission to update feature flags"

        message = get_permission_error_message(ResourceType.USER, Action.DELETE)
        assert message == "You don't have permission to delete users"


class TestGetRequiredRole:
    """Tests for the get_required_role function."""

    def test_get_required_role_for_experiment_create(self):
        """Test getting required role for creating experiments."""
        # Developer is the minimum role required to create experiments
        assert get_required_role(ResourceType.EXPERIMENT, Action.CREATE) == UserRole.DEVELOPER

    def test_get_required_role_for_report_create(self):
        """Test getting required role for creating reports."""
        # Analyst is the minimum role required to create reports
        assert get_required_role(ResourceType.REPORT, Action.CREATE) == UserRole.ANALYST

    def test_get_required_role_for_experiment_read(self):
        """Test getting required role for reading experiments."""
        # Viewer is the minimum role required to read experiments
        assert get_required_role(ResourceType.EXPERIMENT, Action.READ) == UserRole.VIEWER

    def test_get_required_role_for_user_create(self):
        """Test getting required role for creating users."""
        # Admin is the minimum role required to create users
        assert get_required_role(ResourceType.USER, Action.CREATE) == UserRole.ADMIN
