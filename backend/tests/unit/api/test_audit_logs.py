"""
Unit tests for audit log API endpoints.

This module tests the audit log API endpoints including:
- List audit logs with filtering and pagination
- Get entity audit history
- Get user activity
- Get audit statistics
- Permission validation
- Error handling
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import patch, Mock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.models.audit_log import AuditLog, ActionType, EntityType
from backend.app.models.user import User, UserRole
from backend.app.services.audit_service import AuditService


class TestAuditLogsAPI:
    """Test cases for audit logs API endpoints."""

    def setup_test_user(self, role: UserRole = UserRole.ADMIN):
        """Setup a test user with specified role."""
        return User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=role,
            is_superuser=(role == UserRole.ADMIN),
        )

    def setup_test_audit_logs(self, db_session: Session, count: int = 5):
        """Setup test audit logs for testing."""
        user = self.setup_test_user()
        db_session.add(user)
        db_session.commit()

        audit_logs = []
        base_time = datetime.now(timezone.utc)

        for i in range(count):
            audit_log = AuditLog(
                user_id=user.id,
                user_email=user.email,
                action_type=ActionType.TOGGLE_ENABLE.value if i % 2 == 0 else ActionType.TOGGLE_DISABLE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name=f"test_feature_{i}",
                old_value="inactive" if i % 2 == 0 else "active",
                new_value="active" if i % 2 == 0 else "inactive",
                reason=f"Test reason {i}",
                timestamp=base_time - timedelta(minutes=i * 10),
            )
            audit_logs.append(audit_log)

        db_session.add_all(audit_logs)
        db_session.commit()

        return user, audit_logs

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_list_audit_logs_success(self, mock_get_db, mock_get_user):
        """Test successful audit logs listing."""
        client = TestClient(app)

        # Setup mocks
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        # Mock audit service response
        mock_audit_logs = [
            Mock(
                id=uuid4(),
                timestamp=datetime.now(timezone.utc),
                user_id=mock_user.id,
                user_email=mock_user.email,
                action_type=ActionType.TOGGLE_ENABLE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name="test_feature",
                old_value="inactive",
                new_value="active",
                reason="Test reason",
                action_description="enabled",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]

        with patch.object(AuditService, 'get_audit_logs', return_value=(mock_audit_logs, 1)):
            with patch("backend.app.core.permissions.check_permission", return_value=True):
                response = client.get(
                    "/api/v1/audit-logs/",
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "total_pages" in data
        assert data["total"] == 1
        assert len(data["items"]) == 1

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_list_audit_logs_with_filters(self, mock_get_db, mock_get_user):
        """Test audit logs listing with various filters."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        with patch.object(AuditService, 'get_audit_logs', return_value=([], 0)) as mock_get_logs:
            with patch("backend.app.core.permissions.check_permission", return_value=True):
                response = client.get(
                    "/api/v1/audit-logs/",
                    params={
                        "user_id": str(uuid4()),
                        "entity_type": "feature_flag",
                        "action_type": "toggle_enable",
                        "page": 2,
                        "limit": 25,
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 200
        # Verify the service was called with correct parameters
        mock_get_logs.assert_called_once()
        call_args = mock_get_logs.call_args
        assert call_args.kwargs['page'] == 2
        assert call_args.kwargs['limit'] == 25
        assert call_args.kwargs['entity_type'] == EntityType.FEATURE_FLAG
        assert call_args.kwargs['action_type'] == ActionType.TOGGLE_ENABLE

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_list_audit_logs_permission_restricted(self, mock_get_db, mock_get_user):
        """Test that regular users can only see their own logs."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.VIEWER)
        mock_get_user.return_value = mock_user

        with patch.object(AuditService, 'get_audit_logs', return_value=([], 0)) as mock_get_logs:
            with patch("backend.app.core.permissions.check_permission", return_value=False):
                response = client.get(
                    "/api/v1/audit-logs/",
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 200
        # Verify the service was called with user's ID restriction
        call_args = mock_get_logs.call_args
        assert call_args.kwargs['user_id'] == mock_user.id

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_list_audit_logs_invalid_entity_type(self, mock_get_db, mock_get_user):
        """Test error handling for invalid entity type."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        with patch("backend.app.core.permissions.check_permission", return_value=True):
            response = client.get(
                "/api/v1/audit-logs/",
                params={"entity_type": "invalid_entity_type"},
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 400
        assert "Invalid entity type" in response.json()["detail"]

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_list_audit_logs_invalid_date_range(self, mock_get_db, mock_get_user):
        """Test error handling for invalid date range."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        from_date = datetime.now(timezone.utc)
        to_date = from_date - timedelta(days=1)  # Invalid: to_date before from_date

        with patch("backend.app.core.permissions.check_permission", return_value=True):
            response = client.get(
                "/api/v1/audit-logs/",
                params={
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(),
                },
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 400
        assert "to_date must be after from_date" in response.json()["detail"]

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_get_entity_audit_history_success(self, mock_get_db, mock_get_user):
        """Test successful entity audit history retrieval."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        entity_id = uuid4()
        mock_audit_logs = [
            Mock(
                id=uuid4(),
                timestamp=datetime.now(timezone.utc),
                user_id=mock_user.id,
                user_email=mock_user.email,
                action_type=ActionType.TOGGLE_ENABLE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=entity_id,
                entity_name="test_feature",
                old_value="inactive",
                new_value="active",
                reason="Test reason",
                action_description="enabled",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]

        with patch.object(AuditService, 'get_entity_audit_history', return_value=mock_audit_logs):
            with patch("backend.app.core.permissions.check_permission", return_value=True):
                response = client.get(
                    f"/api/v1/audit-logs/entity/feature_flag/{entity_id}",
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_get_entity_audit_history_permission_denied(self, mock_get_db, mock_get_user):
        """Test permission denial for entity audit history."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.VIEWER)
        mock_get_user.return_value = mock_user

        entity_id = uuid4()

        with patch("backend.app.core.permissions.check_permission", return_value=False):
            response = client.get(
                f"/api/v1/audit-logs/entity/feature_flag/{entity_id}",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_get_user_activity_success(self, mock_get_db, mock_get_user):
        """Test successful user activity retrieval."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        target_user_id = uuid4()
        mock_audit_logs = [
            Mock(
                id=uuid4(),
                timestamp=datetime.now(timezone.utc),
                user_id=target_user_id,
                user_email="target@example.com",
                action_type=ActionType.FEATURE_FLAG_CREATE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name="target_feature",
                old_value=None,
                new_value="created",
                reason="Created by target user",
                action_description="created",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]

        with patch.object(AuditService, 'get_user_activity', return_value=mock_audit_logs):
            with patch("backend.app.core.permissions.check_permission", return_value=True):
                response = client.get(
                    f"/api/v1/audit-logs/user/{target_user_id}",
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_get_user_activity_own_data(self, mock_get_db, mock_get_user):
        """Test that users can access their own activity."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.VIEWER)
        mock_get_user.return_value = mock_user

        mock_audit_logs = []

        with patch.object(AuditService, 'get_user_activity', return_value=mock_audit_logs):
            with patch("backend.app.core.permissions.check_permission", return_value=False):
                response = client.get(
                    f"/api/v1/audit-logs/user/{mock_user.id}",
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 200

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_get_user_activity_permission_denied(self, mock_get_db, mock_get_user):
        """Test permission denial for other user's activity."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.VIEWER)
        mock_get_user.return_value = mock_user

        other_user_id = uuid4()

        with patch("backend.app.core.permissions.check_permission", return_value=False):
            response = client.get(
                f"/api/v1/audit-logs/user/{other_user_id}",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_get_audit_stats_success(self, mock_get_db, mock_get_user):
        """Test successful audit statistics retrieval."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        mock_stats = {
            "total_logs": 100,
            "action_counts": {
                "toggle_enable": 30,
                "toggle_disable": 25,
                "feature_flag_create": 20,
            },
            "entity_counts": {
                "feature_flag": 75,
                "experiment": 25,
            },
            "most_active_users": {
                "user1@example.com": 40,
                "user2@example.com": 35,
            },
            "date_range": {
                "from_date": None,
                "to_date": None,
            },
        }

        with patch.object(AuditService, 'get_audit_stats', return_value=mock_stats):
            with patch("backend.app.core.permissions.check_permission", return_value=True):
                response = client.get(
                    "/api/v1/audit-logs/stats",
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["total_logs"] == 100
        assert "action_counts" in data
        assert "entity_counts" in data
        assert "most_active_users" in data

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_get_audit_stats_permission_denied(self, mock_get_db, mock_get_user):
        """Test permission denial for audit statistics."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.VIEWER)
        mock_get_user.return_value = mock_user

        with patch("backend.app.core.permissions.check_permission", return_value=False):
            response = client.get(
                "/api/v1/audit-logs/stats",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_audit_logs_service_error_handling(self, mock_get_db, mock_get_user):
        """Test error handling when audit service raises exceptions."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        with patch.object(AuditService, 'get_audit_logs', side_effect=Exception("Service error")):
            with patch("backend.app.core.permissions.check_permission", return_value=True):
                response = client.get(
                    "/api/v1/audit-logs/",
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 500
        assert "Failed to retrieve audit logs" in response.json()["detail"]

    @patch("backend.app.api.deps.get_current_active_user")
    @patch("backend.app.api.deps.get_db")
    def test_audit_logs_value_error_handling(self, mock_get_db, mock_get_user):
        """Test handling of ValueError from audit service."""
        client = TestClient(app)

        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = self.setup_test_user(UserRole.ADMIN)
        mock_get_user.return_value = mock_user

        with patch.object(AuditService, 'get_audit_logs', side_effect=ValueError("Invalid parameter")):
            with patch("backend.app.core.permissions.check_permission", return_value=True):
                response = client.get(
                    "/api/v1/audit-logs/",
                    headers={"Authorization": "Bearer test-token"}
                )

        assert response.status_code == 400
        assert "Invalid parameter" in response.json()["detail"]

    def test_audit_logs_unauthorized_access(self):
        """Test unauthorized access to audit logs endpoints."""
        client = TestClient(app)

        # Test without authentication header
        response = client.get("/api/v1/audit-logs/")
        assert response.status_code == 401

        # Test with invalid token
        response = client.get(
            "/api/v1/audit-logs/",
            headers={"Authorization": "Bearer invalid-token"}
        )
        # This would depend on your authentication implementation
        # but should result in 401 or 403