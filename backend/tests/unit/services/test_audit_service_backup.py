"""
Unit tests for AuditService.

This module tests the AuditService functionality including:
- Audit log creation
- Asynchronous logging
- Query methods with filtering
- Pagination
- Statistics generation
- Error handling
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.services.audit_service import AuditService
from backend.app.models.audit_log import AuditLog, ActionType, EntityType
from backend.app.models.user import User, UserRole


class TestAuditServiceLogging:
    """Test cases for audit logging functionality."""

    @pytest.mark.asyncio
    async def test_log_toggle_operation_success(self, db_session: Session):
        """Test successful toggle operation logging."""
        # Create a test user first
        user = User(
            username="toggleuser",
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.DEVELOPER,
        )
        db_session.add(user)
        db_session.commit()

        entity_id = uuid4()

        audit_log_id = await AuditService.log_toggle_operation(
            db=db_session,
            user_id=user.id,
            user_email="test@example.com",
            action_type="toggle_enable",
            entity_id=entity_id,
            entity_name="test_feature",
            old_value="inactive",
            new_value="active",
            reason="Testing toggle operation",
        )

        # Verify audit log was created
        assert audit_log_id is not None

        # Retrieve and verify the audit log
        audit_log = db_session.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
        assert audit_log is not None
        assert audit_log.user_id == user.id
        assert audit_log.user_email == "test@example.com"
        assert audit_log.action_type == "toggle_enable"
        assert audit_log.entity_type == EntityType.FEATURE_FLAG.value
        assert audit_log.entity_id == entity_id
        assert audit_log.entity_name == "test_feature"
        assert audit_log.old_value == "inactive"
        assert audit_log.new_value == "active"
        assert audit_log.reason == "Testing toggle operation"

    @pytest.mark.asyncio
    async def test_log_action_success(self, db_session: Session):
        """Test successful general action logging."""
        # Create a test user first
        user = User(
            username="actionuser",
            email="action@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.DEVELOPER,
        )
        db_session.add(user)
        db_session.commit()

        entity_id = uuid4()

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop

            # Mock the executor to call the sync method directly
            def mock_run_in_executor(executor, func, *args):
                return func(*args)

            mock_loop.run_in_executor = AsyncMock(side_effect=mock_run_in_executor)

            audit_log_id = await AuditService.log_action(
                db=db_session,
                user_id=user.id,
                user_email="action@example.com",
                action_type=ActionType.FEATURE_FLAG_CREATE,
                entity_type=EntityType.FEATURE_FLAG,
                entity_id=entity_id,
                entity_name="action_test_feature",
                old_value=None,
                new_value="created",
                reason="Testing action logging",
            )

            # Verify audit log was created
            assert audit_log_id is not None

            # Retrieve and verify the audit log
            audit_log = db_session.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
            assert audit_log is not None
            assert audit_log.user_id == user.id
            assert audit_log.user_email == "action@example.com"
            assert audit_log.action_type == ActionType.FEATURE_FLAG_CREATE.value
            assert audit_log.entity_type == EntityType.FEATURE_FLAG.value
            assert audit_log.new_value == "created"

    @pytest.mark.asyncio
    async def test_log_action_without_user_id(self, db_session: Session):
        """Test logging system actions without user_id."""
        entity_id = uuid4()

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop

            def mock_run_in_executor(executor, func, *args):
                return func(*args)

            mock_loop.run_in_executor = AsyncMock(side_effect=mock_run_in_executor)

            audit_log_id = await AuditService.log_action(
                db=db_session,
                user_id=None,
                user_email="system@example.com",
                action_type=ActionType.SAFETY_ROLLBACK,
                entity_type=EntityType.FEATURE_FLAG,
                entity_id=entity_id,
                entity_name="system_action_feature",
                reason="Automatic system rollback",
            )

            # Verify system audit log was created
            assert audit_log_id is not None

            audit_log = db_session.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
            assert audit_log is not None
            assert audit_log.user_id is None
            assert audit_log.user_email == "system@example.com"
            assert audit_log.action_type == ActionType.SAFETY_ROLLBACK.value

    @pytest.mark.asyncio
    async def test_log_toggle_operation_database_error(self, db_session: Session):
        """Test toggle operation logging with database error."""
        with patch.object(db_session, 'commit', side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(SQLAlchemyError):
                await AuditService.log_toggle_operation(
                    db=db_session,
                    user_id=uuid4(),
                    user_email="error@example.com",
                    action_type="toggle_enable",
                    entity_id=uuid4(),
                    entity_name="error_feature",
                    old_value="inactive",
                    new_value="active",
                )

    @pytest.mark.asyncio
    async def test_log_action_error_handling(self, db_session: Session):
        """Test that log_action handles errors gracefully without raising."""
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop

            # Mock executor to raise an exception
            mock_loop.run_in_executor = AsyncMock(side_effect=Exception("Logging failed"))

            # Should not raise exception, returns None on error
            result = await AuditService.log_action(
                db=db_session,
                user_id=uuid4(),
                user_email="error@example.com",
                action_type=ActionType.FEATURE_FLAG_CREATE,
                entity_type=EntityType.FEATURE_FLAG,
                entity_id=uuid4(),
                entity_name="error_feature",
            )

            assert result is None

    def test_create_audit_log_sync(self, db_session: Session):
        """Test the synchronous audit log creation method."""
        # Create a test user first
        user = User(
            username="syncuser",
            email="sync@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.DEVELOPER,
        )
        db_session.add(user)
        db_session.commit()

        entity_id = uuid4()

        audit_log_id = AuditService._create_audit_log_sync(
            db=db_session,
            user_id=user.id,
            user_email="sync@example.com",
            action_type=ActionType.EXPERIMENT_CREATE,
            entity_type=EntityType.EXPERIMENT,
            entity_id=entity_id,
            entity_name="sync_experiment",
            old_value=None,
            new_value="created",
            reason="Testing sync creation",
        )

        # Verify audit log was created
        assert audit_log_id is not None

        audit_log = db_session.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
        assert audit_log is not None
        assert audit_log.user_id == user.id
        assert audit_log.action_type == ActionType.EXPERIMENT_CREATE.value
        assert audit_log.entity_type == EntityType.EXPERIMENT.value


class TestAuditServiceQueries:
    """Test cases for audit log query functionality."""

    def setup_test_data(self, db_session: Session):
        """Set up test data for query tests."""
        # Create test users
        user1 = User(
            username="user1",
            email="user1@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.DEVELOPER,
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Create test audit logs
        entity1_id = uuid4()
        entity2_id = uuid4()

        base_time = datetime.now(timezone.utc)

        audit_logs = [
            AuditLog(
                user_id=user1.id,
                user_email=user1.email,
                action_type=ActionType.TOGGLE_ENABLE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=entity1_id,
                entity_name="feature1",
                timestamp=base_time - timedelta(minutes=30),
            ),
            AuditLog(
                user_id=user1.id,
                user_email=user1.email,
                action_type=ActionType.TOGGLE_DISABLE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=entity1_id,
                entity_name="feature1",
                timestamp=base_time - timedelta(minutes=20),
            ),
            AuditLog(
                user_id=user2.id,
                user_email=user2.email,
                action_type=ActionType.EXPERIMENT_CREATE.value,
                entity_type=EntityType.EXPERIMENT.value,
                entity_id=entity2_id,
                entity_name="experiment1",
                timestamp=base_time - timedelta(minutes=10),
            ),
            AuditLog(
                user_id=user2.id,
                user_email=user2.email,
                action_type=ActionType.FEATURE_FLAG_CREATE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name="feature2",
                timestamp=base_time,
            ),
        ]

        db_session.add_all(audit_logs)
        db_session.commit()

        return {
            "user1": user1,
            "user2": user2,
            "entity1_id": entity1_id,
            "entity2_id": entity2_id,
            "audit_logs": audit_logs,
        }

    def test_get_audit_logs_all(self, db_session: Session):
        """Test getting all audit logs without filters."""
        test_data = self.setup_test_data(db_session)

        logs, total_count = AuditService.get_audit_logs(db_session)

        assert len(logs) >= 4
        assert total_count >= 4
        # Logs should be ordered by timestamp descending (newest first)
        for i in range(len(logs) - 1):
            assert logs[i].timestamp >= logs[i + 1].timestamp

    def test_get_audit_logs_filter_by_user(self, db_session: Session):
        """Test filtering audit logs by user ID."""
        test_data = self.setup_test_data(db_session)

        logs, total_count = AuditService.get_audit_logs(
            db_session, user_id=test_data["user1"].id
        )

        assert len(logs) == 2
        assert total_count == 2
        for log in logs:
            assert log.user_id == test_data["user1"].id

    def test_get_audit_logs_filter_by_entity_type(self, db_session: Session):
        """Test filtering audit logs by entity type."""
        test_data = self.setup_test_data(db_session)

        logs, total_count = AuditService.get_audit_logs(
            db_session, entity_type=EntityType.FEATURE_FLAG
        )

        assert len(logs) == 3
        assert total_count == 3
        for log in logs:
            assert log.entity_type == EntityType.FEATURE_FLAG.value

    def test_get_audit_logs_filter_by_entity_id(self, db_session: Session):
        """Test filtering audit logs by entity ID."""
        test_data = self.setup_test_data(db_session)

        logs, total_count = AuditService.get_audit_logs(
            db_session, entity_id=test_data["entity1_id"]
        )

        assert len(logs) == 2
        assert total_count == 2
        for log in logs:
            assert log.entity_id == test_data["entity1_id"]

    def test_get_audit_logs_filter_by_action_type(self, db_session: Session):
        """Test filtering audit logs by action type."""
        test_data = self.setup_test_data(db_session)

        logs, total_count = AuditService.get_audit_logs(
            db_session, action_type=ActionType.TOGGLE_ENABLE
        )

        assert len(logs) == 1
        assert total_count == 1
        assert logs[0].action_type == ActionType.TOGGLE_ENABLE.value

    def test_get_audit_logs_filter_by_date_range(self, db_session: Session):
        """Test filtering audit logs by date range."""
        test_data = self.setup_test_data(db_session)

        # Filter to last 15 minutes
        from_date = datetime.now(timezone.utc) - timedelta(minutes=15)

        logs, total_count = AuditService.get_audit_logs(
            db_session, from_date=from_date
        )

        assert len(logs) == 2  # Should get the last 2 logs
        assert total_count == 2
        for log in logs:
            assert log.timestamp >= from_date

    def test_get_audit_logs_pagination(self, db_session: Session):
        """Test audit log pagination."""
        test_data = self.setup_test_data(db_session)

        # Test first page
        logs_page1, total_count = AuditService.get_audit_logs(
            db_session, page=1, limit=2
        )

        assert len(logs_page1) == 2
        assert total_count >= 4

        # Test second page
        logs_page2, _ = AuditService.get_audit_logs(
            db_session, page=2, limit=2
        )

        assert len(logs_page2) >= 1

        # Verify no overlap between pages
        page1_ids = {log.id for log in logs_page1}
        page2_ids = {log.id for log in logs_page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_audit_logs_invalid_pagination(self, db_session: Session):
        """Test invalid pagination parameters."""
        with pytest.raises(ValueError, match="Page number must be 1 or greater"):
            AuditService.get_audit_logs(db_session, page=0)

        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            AuditService.get_audit_logs(db_session, limit=0)

        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            AuditService.get_audit_logs(db_session, limit=1001)

    def test_get_entity_audit_history(self, db_session: Session):
        """Test getting audit history for a specific entity."""
        test_data = self.setup_test_data(db_session)

        logs = AuditService.get_entity_audit_history(
            db_session,
            entity_type=EntityType.FEATURE_FLAG,
            entity_id=test_data["entity1_id"],
        )

        assert len(logs) == 2
        for log in logs:
            assert log.entity_type == EntityType.FEATURE_FLAG.value
            assert log.entity_id == test_data["entity1_id"]

        # Verify ordering (newest first)
        assert logs[0].timestamp >= logs[1].timestamp

    def test_get_user_activity(self, db_session: Session):
        """Test getting user activity logs."""
        test_data = self.setup_test_data(db_session)

        logs = AuditService.get_user_activity(
            db_session, user_id=test_data["user1"].id
        )

        assert len(logs) == 2
        for log in logs:
            assert log.user_id == test_data["user1"].id

    def test_get_user_activity_with_date_range(self, db_session: Session):
        """Test getting user activity with date filtering."""
        test_data = self.setup_test_data(db_session)

        # Filter to last 25 minutes (should get 1 log for user1)
        from_date = datetime.now(timezone.utc) - timedelta(minutes=25)

        logs = AuditService.get_user_activity(
            db_session,
            user_id=test_data["user1"].id,
            from_date=from_date,
        )

        assert len(logs) == 1
        assert logs[0].timestamp >= from_date

    def test_get_audit_stats(self, db_session: Session):
        """Test getting audit log statistics."""
        test_data = self.setup_test_data(db_session)

        stats = AuditService.get_audit_stats(db_session)

        assert isinstance(stats, dict)
        assert "total_logs" in stats
        assert "action_counts" in stats
        assert "entity_counts" in stats
        assert "most_active_users" in stats
        assert "date_range" in stats

        assert stats["total_logs"] >= 4
        assert isinstance(stats["action_counts"], dict)
        assert isinstance(stats["entity_counts"], dict)
        assert isinstance(stats["most_active_users"], dict)

        # Verify some expected values
        assert stats["action_counts"].get(ActionType.TOGGLE_ENABLE.value, 0) >= 1
        assert stats["entity_counts"].get(EntityType.FEATURE_FLAG.value, 0) >= 3

    def test_get_audit_stats_with_date_range(self, db_session: Session):
        """Test getting audit statistics with date filtering."""
        test_data = self.setup_test_data(db_session)

        from_date = datetime.now(timezone.utc) - timedelta(minutes=15)
        to_date = datetime.now(timezone.utc)

        stats = AuditService.get_audit_stats(
            db_session, from_date=from_date, to_date=to_date
        )

        assert stats["total_logs"] >= 2
        assert stats["date_range"]["from_date"] == from_date.isoformat()
        assert stats["date_range"]["to_date"] == to_date.isoformat()