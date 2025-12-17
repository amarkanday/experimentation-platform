"""
Unit tests for feature flag toggle API endpoints.

This module tests the new toggle endpoints including:
- POST /api/v1/feature-flags/{id}/toggle
- POST /api/v1/feature-flags/{id}/enable
- POST /api/v1/feature-flags/{id}/disable
- Audit logging integration
- Permission validation
- Error handling
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.models.user import User, UserRole
from backend.app.models.audit_log import ActionType, EntityType
from backend.app.api import deps


class TestFeatureFlagToggleEndpoints:
    """Test cases for feature flag toggle endpoints."""

    def setup_method(self):
        """Setup for each test."""
        # Clear any existing overrides
        app.dependency_overrides.clear()

    def teardown_method(self):
        """Cleanup after each test."""
        # Clear dependency overrides
        app.dependency_overrides.clear()

    def setup_test_user(self, role: UserRole = UserRole.DEVELOPER, is_superuser: bool = False):
        """Setup a test user with specified role."""
        return User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=role,
            is_superuser=is_superuser,
        )

    def setup_test_feature_flag(self, owner_id: uuid4, status: FeatureFlagStatus = FeatureFlagStatus.INACTIVE):
        """Setup a test feature flag."""
        return FeatureFlag(
            id=uuid4(),
            key="test_feature_flag",
            name="Test Feature Flag",
            description="A test feature flag",
            status=status.value,
            owner_id=owner_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def test_toggle_feature_flag_inactive_to_active(self):
        """Test toggling feature flag from inactive to active."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Setup feature flag
        feature_flag = self.setup_test_feature_flag(
            owner_id=mock_user.id,
            status=FeatureFlagStatus.INACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create async mock for audit service
        async def mock_log_action(*args, **kwargs):
            return uuid4()

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        # Mock audit service
        with patch("backend.app.services.audit_service.AuditService.log_action", side_effect=mock_log_action):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/feature-flags/{feature_flag.id}/toggle",
                json={"reason": "Testing toggle functionality"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["id"] == str(feature_flag.id)
        assert data["name"] == feature_flag.name
        assert data["key"] == feature_flag.key
        assert data["status"] == FeatureFlagStatus.ACTIVE.value
        assert "audit_log_id" in data
        assert "updated_at" in data

        # Verify feature flag was updated
        assert feature_flag.status == FeatureFlagStatus.ACTIVE.value

        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(feature_flag)

    def test_toggle_feature_flag_active_to_inactive(self):
        """Test toggling feature flag from active to inactive."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Setup feature flag
        feature_flag = self.setup_test_feature_flag(
            owner_id=mock_user.id,
            status=FeatureFlagStatus.ACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create async mock for audit service
        async def mock_log_action(*args, **kwargs):
            return uuid4()

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        # Mock audit service
        with patch("backend.app.services.audit_service.AuditService.log_action", side_effect=mock_log_action):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/feature-flags/{feature_flag.id}/toggle",
                json={"reason": "Testing toggle off"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert data["status"] == FeatureFlagStatus.INACTIVE.value

        # Verify feature flag was updated
        assert feature_flag.status == FeatureFlagStatus.INACTIVE.value

    def test_enable_feature_flag(self):
        """Test enabling a feature flag."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Setup inactive feature flag
        feature_flag = self.setup_test_feature_flag(
            owner_id=mock_user.id,
            status=FeatureFlagStatus.INACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create async mock for audit service
        async def mock_log_action(*args, **kwargs):
            return uuid4()

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        # Mock audit service
        with patch("backend.app.services.audit_service.AuditService.log_action", side_effect=mock_log_action):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/feature-flags/{feature_flag.id}/enable",
                json={"reason": "Enabling for testing"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert data["status"] == FeatureFlagStatus.ACTIVE.value
        assert feature_flag.status == FeatureFlagStatus.ACTIVE.value

    def test_disable_feature_flag(self):
        """Test disabling a feature flag."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Setup active feature flag
        feature_flag = self.setup_test_feature_flag(
            owner_id=mock_user.id,
            status=FeatureFlagStatus.ACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create async mock for audit service
        async def mock_log_action(*args, **kwargs):
            return uuid4()

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        # Mock audit service
        with patch("backend.app.services.audit_service.AuditService.log_action", side_effect=mock_log_action):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/feature-flags/{feature_flag.id}/disable",
                json={"reason": "Disabling for testing"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert data["status"] == FeatureFlagStatus.INACTIVE.value
        assert feature_flag.status == FeatureFlagStatus.INACTIVE.value

    def test_toggle_feature_flag_not_found(self):
        """Test toggling non-existent feature flag."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Mock database query to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        client = TestClient(app)
        non_existent_id = uuid4()
        response = client.post(
            f"/api/v1/feature-flags/{non_existent_id}/toggle",
            json={"reason": "Test"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_toggle_feature_flag_permission_denied(self):
        """Test toggling feature flag without permission."""
        # Setup mocks
        mock_user = self.setup_test_user(is_superuser=False)
        mock_db = Mock(spec=Session)

        # Setup feature flag owned by different user
        different_user_id = uuid4()
        feature_flag = self.setup_test_feature_flag(
            owner_id=different_user_id,  # Different owner
            status=FeatureFlagStatus.INACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        client = TestClient(app)
        response = client.post(
            f"/api/v1/feature-flags/{feature_flag.id}/toggle",
            json={"reason": "Test"}
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    def test_toggle_feature_flag_superuser_access(self):
        """Test superuser can toggle any feature flag."""
        # Setup mocks
        mock_superuser = self.setup_test_user(is_superuser=True)
        mock_db = Mock(spec=Session)

        # Setup feature flag owned by different user
        different_user_id = uuid4()
        feature_flag = self.setup_test_feature_flag(
            owner_id=different_user_id,
            status=FeatureFlagStatus.INACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create async mock for audit service
        async def mock_log_action(*args, **kwargs):
            return uuid4()

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_superuser
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        # Mock audit service
        with patch("backend.app.services.audit_service.AuditService.log_action", side_effect=mock_log_action):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/feature-flags/{feature_flag.id}/toggle",
                json={"reason": "Superuser toggle"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FeatureFlagStatus.ACTIVE.value

    def test_toggle_with_cache_invalidation(self):
        """Test that toggle invalidates cache when enabled."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)
        mock_redis = Mock()

        # Setup feature flag
        feature_flag = self.setup_test_feature_flag(
            owner_id=mock_user.id,
            status=FeatureFlagStatus.INACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create async mock for audit service
        async def mock_log_action(*args, **kwargs):
            return uuid4()

        # Override dependencies with cache enabled
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": True, "redis": mock_redis}

        # Mock audit service and cache service
        with patch("backend.app.services.audit_service.AuditService.log_action", side_effect=mock_log_action):
            with patch("backend.app.services.cache.CacheService.invalidate_feature_flag_cache") as mock_invalidate:
                client = TestClient(app)
                response = client.post(
                    f"/api/v1/feature-flags/{feature_flag.id}/toggle",
                    json={"reason": "Test cache invalidation"}
                )

        assert response.status_code == 200

        # Verify cache was invalidated
        mock_invalidate.assert_called_once_with(str(feature_flag.id))

    def test_toggle_without_reason(self):
        """Test toggling feature flag without providing a reason."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Setup feature flag
        feature_flag = self.setup_test_feature_flag(
            owner_id=mock_user.id,
            status=FeatureFlagStatus.INACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create async mock for audit service
        async def mock_log_action(*args, **kwargs):
            # Verify no reason is passed
            assert kwargs.get("reason") is None
            return uuid4()

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        # Mock audit service
        with patch("backend.app.services.audit_service.AuditService.log_action", side_effect=mock_log_action):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/feature-flags/{feature_flag.id}/toggle",
                json={}  # No reason provided
            )

        assert response.status_code == 200

    def test_toggle_database_error(self):
        """Test handling of database errors during toggle."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Setup feature flag
        feature_flag = self.setup_test_feature_flag(
            owner_id=mock_user.id,
            status=FeatureFlagStatus.INACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit.side_effect = Exception("Database error")

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        client = TestClient(app)
        response = client.post(
            f"/api/v1/feature-flags/{feature_flag.id}/toggle",
            json={"reason": "Test error handling"}
        )

        assert response.status_code == 500

    def test_toggle_audit_logging_error(self):
        """Test that toggle continues even if audit logging fails."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Setup feature flag
        feature_flag = self.setup_test_feature_flag(
            owner_id=mock_user.id,
            status=FeatureFlagStatus.INACTIVE
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = feature_flag
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create async mock that raises exception
        async def mock_log_action_error(*args, **kwargs):
            raise Exception("Audit logging error")

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        # Mock audit service to raise exception
        with patch("backend.app.services.audit_service.AuditService.log_action", side_effect=mock_log_action_error):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/feature-flags/{feature_flag.id}/toggle",
                json={"reason": "Test audit error handling"}
            )

        # Should still succeed (audit logging is non-blocking)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FeatureFlagStatus.ACTIVE.value
        assert "audit_log_id" in data  # May be None

    def test_toggle_invalid_request_body(self):
        """Test toggle with invalid request body."""
        # Setup mocks
        mock_user = self.setup_test_user()
        mock_db = Mock(spec=Session)

        # Override dependencies
        app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
        app.dependency_overrides[deps.get_db] = lambda: mock_db
        app.dependency_overrides[deps.get_cache_control] = lambda: {"enabled": False, "redis": None}

        client = TestClient(app)
        feature_flag_id = uuid4()

        # Test with invalid JSON
        response = client.post(
            f"/api/v1/feature-flags/{feature_flag_id}/toggle",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable Entity