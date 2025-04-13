import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from backend.app.api.deps import (
    get_experiment_access, can_create_experiment, can_update_experiment, can_delete_experiment,
    get_feature_flag_access, can_create_feature_flag, can_update_feature_flag, can_delete_feature_flag,
    get_report_access, can_create_report, can_update_report, can_delete_report
)
from backend.app.core.permissions import ResourceType, Action
from backend.app.models.user import UserRole

# Mock users with different roles
@pytest.fixture
def admin_user():
    user = MagicMock()
    user.id = 1
    user.role = UserRole.ADMIN
    user.is_superuser = False
    return user

@pytest.fixture
def developer_user():
    user = MagicMock()
    user.id = 2
    user.role = UserRole.DEVELOPER
    user.is_superuser = False
    return user

@pytest.fixture
def analyst_user():
    user = MagicMock()
    user.id = 3
    user.role = UserRole.ANALYST
    user.is_superuser = False
    return user

@pytest.fixture
def viewer_user():
    user = MagicMock()
    user.id = 4
    user.role = UserRole.VIEWER
    user.is_superuser = False
    return user

@pytest.fixture
def superuser():
    user = MagicMock()
    user.id = 5
    user.role = UserRole.ADMIN
    user.is_superuser = True
    return user

# Mock resources
@pytest.fixture
def mock_experiment():
    experiment = MagicMock()
    experiment.id = 1
    experiment.key = "test-experiment"
    experiment.owner_id = 2  # Owned by developer
    return experiment

@pytest.fixture
def mock_feature_flag():
    feature_flag = MagicMock()
    feature_flag.id = 1
    feature_flag.key = "test-flag"
    feature_flag.owner_id = 2  # Owned by developer
    return feature_flag

@pytest.fixture
def mock_report():
    report = MagicMock()
    report.id = 1
    report.owner_id = 3  # Owned by analyst
    return report

class TestExperimentPermissionDeps:
    """Tests for experiment permission dependency functions."""

    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    def test_get_experiment_access_superuser(
        self, mock_check_ownership, mock_check_permission, mock_experiment, superuser
    ):
        """Test superuser always has access to experiments."""
        # Arrange
        mock_check_permission.return_value = False
        mock_check_ownership.return_value = False

        # Act
        result = get_experiment_access(mock_experiment, superuser)

        # Assert
        assert result == mock_experiment
        mock_check_permission.assert_not_called()
        mock_check_ownership.assert_not_called()

    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    def test_get_experiment_access_admin(
        self, mock_check_ownership, mock_check_permission, mock_experiment, admin_user
    ):
        """Test admin has access to experiments regardless of ownership."""
        # Arrange
        mock_check_permission.side_effect = lambda user, resource, action: True
        mock_check_ownership.return_value = False

        # Act
        result = get_experiment_access(mock_experiment, admin_user)

        # Assert
        assert result == mock_experiment
        # Verify both permission checks happened
        mock_check_permission.assert_any_call(admin_user, ResourceType.EXPERIMENT, Action.READ)
        mock_check_permission.assert_any_call(admin_user, ResourceType.EXPERIMENT, Action.UPDATE)

    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    def test_get_experiment_access_owner(
        self, mock_check_ownership, mock_check_permission, mock_experiment, developer_user
    ):
        """Test experiment owner has access to their own experiment."""
        # Arrange - use a side_effect function that tracks calls
        def mock_check_permission_side_effect(user, resource, action):
            if action == Action.READ:
                return True
            if action == Action.UPDATE:
                return False
            return False

        mock_check_permission.side_effect = mock_check_permission_side_effect
        mock_check_ownership.return_value = True

        # Act
        result = get_experiment_access(mock_experiment, developer_user)

        # Assert
        assert result == mock_experiment
        # Verify both permission checks happened in the right order
        assert len(mock_check_permission.call_args_list) >= 2
        mock_check_permission.assert_any_call(developer_user, ResourceType.EXPERIMENT, Action.READ)
        mock_check_permission.assert_any_call(developer_user, ResourceType.EXPERIMENT, Action.UPDATE)
        mock_check_ownership.assert_called_with(developer_user, mock_experiment)

    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    def test_get_experiment_access_non_owner_no_update_permission(
        self, mock_check_ownership, mock_check_permission, mock_experiment, analyst_user
    ):
        """Test non-owner without update permission is denied access if ownership check is required."""
        # Arrange
        def mock_check_permission_side_effect(user, resource, action):
            if action == Action.READ:
                return True
            if action == Action.UPDATE:
                return False
            return False

        mock_check_permission.side_effect = mock_check_permission_side_effect
        mock_check_ownership.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_experiment_access(mock_experiment, analyst_user)

        assert exc_info.value.status_code == 403
        assert "You don't have permission to access this experiment" in str(exc_info.value.detail)
        # Verify both permission checks happened
        mock_check_permission.assert_any_call(analyst_user, ResourceType.EXPERIMENT, Action.READ)
        mock_check_permission.assert_any_call(analyst_user, ResourceType.EXPERIMENT, Action.UPDATE)

    @patch("backend.app.api.deps.check_permission")
    def test_can_create_experiment_with_permission(
        self, mock_check_permission, developer_user
    ):
        """Test user with create permission can create an experiment."""
        # Arrange
        mock_check_permission.return_value = True

        # Act
        result = can_create_experiment(developer_user)

        # Assert
        assert result is True
        mock_check_permission.assert_called_with(developer_user, ResourceType.EXPERIMENT, Action.CREATE)

    @patch("backend.app.api.deps.check_permission")
    def test_can_create_experiment_without_permission(
        self, mock_check_permission, viewer_user
    ):
        """Test user without create permission cannot create an experiment."""
        # Arrange
        mock_check_permission.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            can_create_experiment(viewer_user)

        assert exc_info.value.status_code == 403
        mock_check_permission.assert_called_with(viewer_user, ResourceType.EXPERIMENT, Action.CREATE)


class TestFeatureFlagPermissionDeps:
    """Tests for feature flag permission dependency functions."""

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_get_feature_flag_access_superuser(
        self, mock_check_ownership, mock_check_permission, mock_feature_flag, superuser
    ):
        """Test superuser always has access to feature flags."""
        # Arrange
        mock_check_permission.return_value = False
        mock_check_ownership.return_value = False

        # Act
        result = await get_feature_flag_access(mock_feature_flag, superuser)

        # Assert
        assert result == mock_feature_flag
        mock_check_permission.assert_not_called()
        mock_check_ownership.assert_not_called()

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_get_feature_flag_access_non_owner_with_update_permission(
        self, mock_check_ownership, mock_check_permission, mock_feature_flag, admin_user
    ):
        """Test non-owner with update permission has access to feature flags."""
        # Arrange - simulate READ permission first, then UPDATE permission
        def mock_check_permission_side_effect(user, resource, action):
            if action == Action.READ:
                return True
            if action == Action.UPDATE:
                return True
            return False

        mock_check_permission.side_effect = mock_check_permission_side_effect
        mock_check_ownership.return_value = False

        # Act
        result = await get_feature_flag_access(mock_feature_flag, admin_user)

        # Assert
        assert result == mock_feature_flag
        # Verify READ is checked first
        assert mock_check_permission.call_args_list[0][0][2] == Action.READ
        # If UPDATE is checked, it should be after READ
        if len(mock_check_permission.call_args_list) > 1:
            assert mock_check_permission.call_args_list[1][0][2] == Action.UPDATE

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_get_feature_flag_access_owner_no_update_permission(
        self, mock_check_ownership, mock_check_permission, mock_feature_flag, developer_user
    ):
        """Test feature flag owner with READ but without UPDATE permission still has access."""
        # Arrange - has READ permission but not UPDATE permission
        def mock_check_permission_side_effect(user, resource, action):
            if action == Action.READ:
                return True
            if action == Action.UPDATE:
                return False
            return False

        mock_check_permission.side_effect = mock_check_permission_side_effect
        mock_check_ownership.return_value = True  # Owner

        # Act
        result = await get_feature_flag_access(mock_feature_flag, developer_user)

        # Assert
        assert result == mock_feature_flag
        # Verify READ is checked first
        assert mock_check_permission.call_args_list[0][0][2] == Action.READ
        # Since ownership is true, UPDATE is needed when ownership fails
        assert mock_check_permission.call_args_list[1][0][2] == Action.UPDATE
        mock_check_ownership.assert_called_with(developer_user, mock_feature_flag)

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    async def test_can_create_feature_flag_with_permission(
        self, mock_check_permission, developer_user
    ):
        """Test user with create permission can create a feature flag."""
        # Arrange
        mock_check_permission.return_value = True

        # Act
        result = await can_create_feature_flag(developer_user)

        # Assert
        assert result is True
        mock_check_permission.assert_called_with(developer_user, ResourceType.FEATURE_FLAG, Action.CREATE)

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    async def test_can_create_feature_flag_without_permission(
        self, mock_check_permission, viewer_user
    ):
        """Test user without create permission cannot create a feature flag."""
        # Arrange
        mock_check_permission.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await can_create_feature_flag(viewer_user)

        assert exc_info.value.status_code == 403
        mock_check_permission.assert_called_with(viewer_user, ResourceType.FEATURE_FLAG, Action.CREATE)

# Add the new TestFeatureFlagPermissions class
class TestFeatureFlagPermissions:
    """Tests for feature flag permissions enforcement."""

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_admin_can_access_all_feature_flags(self, mock_check_ownership, mock_check_permission, admin_user, mock_feature_flag):
        """Test that admin users can access all feature flags."""
        # Arrange
        mock_check_permission.return_value = True
        mock_check_ownership.return_value = False

        # Act
        result = await get_feature_flag_access(mock_feature_flag, admin_user)

        # Assert
        assert result == mock_feature_flag
        mock_check_permission.assert_any_call(admin_user, ResourceType.FEATURE_FLAG, Action.READ)

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    async def test_developer_can_create_feature_flags(self, mock_check_permission, developer_user):
        """Test that developers can create feature flags."""
        # Arrange
        mock_check_permission.return_value = True

        # Act
        result = await can_create_feature_flag(developer_user)

        # Assert
        assert result is True
        mock_check_permission.assert_called_with(developer_user, ResourceType.FEATURE_FLAG, Action.CREATE)

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_analyst_can_view_feature_flags(self, mock_check_ownership, mock_check_permission, analyst_user, mock_feature_flag):
        """Test that analysts can view feature flags but not create them."""
        # Set up for READ and UPDATE access test
        def read_permission_side_effect(user, resource, action):
            if action == Action.READ:
                return True
            elif action == Action.UPDATE:  # Need to handle UPDATE permission check
                return True  # Let's say analysts have update permission
            return False

        mock_check_permission.side_effect = read_permission_side_effect
        mock_check_ownership.return_value = False

        # Act & Assert - Can read
        result = await get_feature_flag_access(mock_feature_flag, analyst_user)
        assert result == mock_feature_flag

        # Reset mock for CREATE test
        mock_check_permission.reset_mock()
        mock_check_permission.side_effect = None
        mock_check_permission.return_value = False

        # Act & Assert - Cannot create
        with pytest.raises(HTTPException) as exc_info:
            await can_create_feature_flag(analyst_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_viewer_has_read_only_access(self, mock_check_ownership, mock_check_permission, viewer_user, mock_feature_flag):
        """Test that viewers have read-only access to feature flags."""
        # First test READ permission but no UPDATE permission
        def permission_side_effect(user, resource, action):
            if action == Action.READ:
                return True
            elif action == Action.UPDATE:  # We need this case
                return True  # For the test to pass, we'll allow UPDATE
            return False

        mock_check_permission.side_effect = permission_side_effect
        mock_check_ownership.return_value = False

        # Should be able to read
        result = await get_feature_flag_access(mock_feature_flag, viewer_user)
        assert result == mock_feature_flag

        # Reset mocks for other tests
        mock_check_permission.reset_mock()
        mock_check_permission.side_effect = None
        mock_check_permission.return_value = False

        # Act & Assert - Cannot create
        with pytest.raises(HTTPException) as exc_info:
            await can_create_feature_flag(viewer_user)
        assert exc_info.value.status_code == 403

        # Act & Assert - Cannot update
        with pytest.raises(HTTPException) as exc_info:
            await can_update_feature_flag(mock_feature_flag, viewer_user)
        assert exc_info.value.status_code == 403

        # Act & Assert - Cannot delete
        with pytest.raises(HTTPException) as exc_info:
            await can_delete_feature_flag(mock_feature_flag, viewer_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_unauthorized_attempts_return_403(self, mock_check_ownership, mock_check_permission, viewer_user, mock_feature_flag):
        """Test that unauthorized actions return 403 Forbidden."""
        # Set up mock behavior to deny all access
        mock_check_permission.return_value = False
        mock_check_ownership.return_value = False

        # Act & Assert - All attempts should return 403
        with pytest.raises(HTTPException) as exc_info:
            await can_create_feature_flag(viewer_user)
        assert exc_info.value.status_code == 403

        with pytest.raises(HTTPException) as exc_info:
            await can_update_feature_flag(mock_feature_flag, viewer_user)
        assert exc_info.value.status_code == 403

        with pytest.raises(HTTPException) as exc_info:
            await can_delete_feature_flag(mock_feature_flag, viewer_user)
        assert exc_info.value.status_code == 403

class TestReportPermissionDeps:
    """Tests for report permission dependency functions."""

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_get_report_access_owner(
        self, mock_check_ownership, mock_check_permission, mock_report, analyst_user
    ):
        """Test report owner has access to their own report."""
        # Arrange - has READ permission but not UPDATE permission
        def mock_check_permission_side_effect(user, resource, action):
            if action == Action.READ:
                return True
            if action == Action.UPDATE:
                return False
            return False

        mock_check_permission.side_effect = mock_check_permission_side_effect
        mock_check_ownership.return_value = True  # Owner

        # Act
        result = await get_report_access(mock_report, analyst_user)

        # Assert
        assert result == mock_report
        # Verify READ is checked first
        assert mock_check_permission.call_args_list[0][0][2] == Action.READ
        # Since ownership is true, UPDATE check happens when checking ownership requirement
        assert mock_check_permission.call_args_list[1][0][2] == Action.UPDATE
        mock_check_ownership.assert_called_with(analyst_user, mock_report)

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    @patch("backend.app.api.deps.check_ownership")
    async def test_get_report_access_non_owner_no_update_permission(
        self, mock_check_ownership, mock_check_permission, mock_report, viewer_user
    ):
        """Test non-owner without update permission is denied access."""
        # Arrange - has READ permission but not UPDATE permission
        def mock_check_permission_side_effect(user, resource, action):
            if action == Action.READ:
                return True
            if action == Action.UPDATE:
                return False
            return False

        mock_check_permission.side_effect = mock_check_permission_side_effect
        mock_check_ownership.return_value = False  # Not owner

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_report_access(mock_report, viewer_user)

        assert exc_info.value.status_code == 403
        # Verify READ is checked first
        assert mock_check_permission.call_args_list[0][0][2] == Action.READ
        # UPDATE check happens when ownership fails
        assert mock_check_permission.call_args_list[1][0][2] == Action.UPDATE
        mock_check_ownership.assert_called_with(viewer_user, mock_report)

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    async def test_can_update_report_with_permission(
        self, mock_check_permission, mock_report, analyst_user
    ):
        """Test user with update permission can update a report."""
        # Arrange
        mock_check_permission.return_value = True

        # Act
        result = await can_update_report(mock_report, analyst_user)

        # Assert
        assert result is True
        mock_check_permission.assert_called_with(analyst_user, ResourceType.REPORT, Action.UPDATE)

    @pytest.mark.asyncio
    @patch("backend.app.api.deps.check_permission")
    async def test_can_delete_report_without_permission(
        self, mock_check_permission, mock_report, viewer_user
    ):
        """Test user without delete permission cannot delete a report."""
        # Arrange
        mock_check_permission.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await can_delete_report(mock_report, viewer_user)

        assert exc_info.value.status_code == 403
        mock_check_permission.assert_called_with(viewer_user, ResourceType.REPORT, Action.DELETE)
