import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.middleware.auth import require_permission, require_admin
from backend.app.core.permissions import UserRole, ResourceType, Action
from backend.app.models.user import User

def create_mock_user(role: UserRole = UserRole.USER, is_superuser: bool = False) -> Mock:
    """Helper function to create a mock user with specified role and superuser status."""
    user = Mock(spec=User)
    user.role = role
    user.is_superuser = is_superuser
    return user

@pytest.mark.parametrize(
    "user_role,resource,action,expected_allowed",
    [
        # Test regular user permissions
        (UserRole.USER, ResourceType.EXPERIMENT, Action.READ, True),
        (UserRole.USER, ResourceType.EXPERIMENT, Action.CREATE, True),
        (UserRole.USER, ResourceType.EXPERIMENT, Action.UPDATE, True),
        (UserRole.USER, ResourceType.EXPERIMENT, Action.DELETE, False),

        # Test admin permissions
        (UserRole.ADMIN, ResourceType.EXPERIMENT, Action.READ, True),
        (UserRole.ADMIN, ResourceType.EXPERIMENT, Action.CREATE, True),
        (UserRole.ADMIN, ResourceType.EXPERIMENT, Action.UPDATE, True),
        (UserRole.ADMIN, ResourceType.EXPERIMENT, Action.DELETE, True),

        # Test viewer permissions
        (UserRole.VIEWER, ResourceType.EXPERIMENT, Action.READ, True),
        (UserRole.VIEWER, ResourceType.EXPERIMENT, Action.CREATE, False),
        (UserRole.VIEWER, ResourceType.EXPERIMENT, Action.UPDATE, False),
        (UserRole.VIEWER, ResourceType.EXPERIMENT, Action.DELETE, False),
    ]
)
def test_require_permission(user_role: UserRole, resource: ResourceType, action: Action, expected_allowed: bool):
    """Test permission requirements for different user roles."""
    # Create mock user with specified role
    user = create_mock_user(role=user_role)

    # Create the permission checker
    permission_checker = require_permission(resource, action)

    if expected_allowed:
        # Should succeed without raising an exception
        assert permission_checker(current_user=user) is True
    else:
        # Should raise HTTPException with 403 status
        with pytest.raises(HTTPException) as exc_info:
            permission_checker(current_user=user)
        assert exc_info.value.status_code == 403
        assert "Permission denied" in str(exc_info.value.detail)

def test_superuser_override():
    """Test that superusers have all permissions regardless of role."""
    # Create superuser with basic role
    superuser = create_mock_user(role=UserRole.USER, is_superuser=True)

    # Test various permissions that would normally be denied
    for action in [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE]:
        permission_checker = require_permission(ResourceType.EXPERIMENT, action)
        assert permission_checker(current_user=superuser) is True

def test_require_admin_with_admin_role():
    """Test that users with ADMIN role pass the admin check."""
    admin_user = create_mock_user(role=UserRole.ADMIN)
    assert require_admin(current_user=admin_user) is True

def test_require_admin_with_superuser():
    """Test that superusers pass the admin check."""
    superuser = create_mock_user(is_superuser=True)
    assert require_admin(current_user=superuser) is True

def test_require_admin_with_regular_user():
    """Test that regular users fail the admin check."""
    regular_user = create_mock_user(role=UserRole.USER)
    with pytest.raises(HTTPException) as exc_info:
        require_admin(current_user=regular_user)
    assert exc_info.value.status_code == 403
    assert "Admin access required" in str(exc_info.value.detail)

def test_require_admin_with_viewer():
    """Test that viewers fail the admin check."""
    viewer = create_mock_user(role=UserRole.VIEWER)
    with pytest.raises(HTTPException) as exc_info:
        require_admin(current_user=viewer)
    assert exc_info.value.status_code == 403
    assert "Admin access required" in str(exc_info.value.detail)

def test_missing_role_defaults_to_user():
    """Test that missing role defaults to USER role."""
    user = Mock(spec=User)
    user.is_superuser = False
    # Note: no role attribute set

    # Should have basic user permissions
    permission_checker = require_permission(ResourceType.EXPERIMENT, Action.READ)
    assert permission_checker(current_user=user) is True

    # But not admin permissions
    permission_checker = require_permission(ResourceType.EXPERIMENT, Action.DELETE)
    with pytest.raises(HTTPException) as exc_info:
        permission_checker(current_user=user)
    assert exc_info.value.status_code == 403
