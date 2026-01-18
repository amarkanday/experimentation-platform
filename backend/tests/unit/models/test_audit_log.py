"""
Unit tests for AuditLog model.

This module tests the AuditLog model functionality including:
- Model creation and validation
- Enum validation
- Property methods
- Database relationships
- Schema constraints
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog, ActionType, EntityType
from backend.app.models.user import User, UserRole


class TestAuditLogModel:
    """Test cases for AuditLog model."""

    def test_create_audit_log_with_required_fields(self, db_session: Session):
        """Test creating an audit log with only required fields."""
        # Create a test user first
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.DEVELOPER,
        )
        db_session.add(user)
        db_session.commit()

        # Create audit log
        audit_log = AuditLog(
            user_id=user.id,
            user_email=user.email,
            action_type=ActionType.TOGGLE_ENABLE.value,
            entity_type=EntityType.FEATURE_FLAG.value,
            entity_id=uuid4(),
            entity_name="test_feature",
        )

        db_session.add(audit_log)
        db_session.commit()

        # Verify audit log was created
        assert audit_log.id is not None
        assert audit_log.user_id == user.id
        assert audit_log.user_email == user.email
        assert audit_log.action_type == ActionType.TOGGLE_ENABLE.value
        assert audit_log.entity_type == EntityType.FEATURE_FLAG.value
        assert audit_log.entity_name == "test_feature"
        assert audit_log.timestamp is not None
        assert audit_log.created_at is not None
        assert audit_log.updated_at is not None

    def test_create_audit_log_with_all_fields(self, db_session: Session):
        """Test creating an audit log with all fields."""
        # Create a test user first
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        db_session.commit()

        entity_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        # Create audit log with all fields
        audit_log = AuditLog(
            user_id=user.id,
            user_email=user.email,
            action_type=ActionType.FEATURE_FLAG_UPDATE.value,
            entity_type=EntityType.FEATURE_FLAG.value,
            entity_id=entity_id,
            entity_name="comprehensive_feature",
            old_value="inactive",
            new_value="active",
            reason="Testing comprehensive functionality",
            timestamp=timestamp,
        )

        db_session.add(audit_log)
        db_session.commit()

        # Verify all fields
        assert audit_log.id is not None
        assert audit_log.user_id == user.id
        assert audit_log.user_email == user.email
        assert audit_log.action_type == ActionType.FEATURE_FLAG_UPDATE.value
        assert audit_log.entity_type == EntityType.FEATURE_FLAG.value
        assert audit_log.entity_id == entity_id
        assert audit_log.entity_name == "comprehensive_feature"
        assert audit_log.old_value == "inactive"
        assert audit_log.new_value == "active"
        assert audit_log.reason == "Testing comprehensive functionality"
        assert audit_log.timestamp == timestamp

    def test_create_audit_log_without_user_id(self, db_session: Session):
        """Test creating an audit log without user_id (system action)."""
        # Create audit log for system action
        audit_log = AuditLog(
            user_id=None,
            user_email="system@example.com",
            action_type=ActionType.SAFETY_ROLLBACK.value,
            entity_type=EntityType.FEATURE_FLAG.value,
            entity_id=uuid4(),
            entity_name="system_rollback_feature",
            reason="Automatic safety rollback",
        )

        db_session.add(audit_log)
        db_session.commit()

        # Verify system audit log
        assert audit_log.id is not None
        assert audit_log.user_id is None
        assert audit_log.user_email == "system@example.com"
        assert audit_log.action_type == ActionType.SAFETY_ROLLBACK.value
        assert audit_log.reason == "Automatic safety rollback"

    def test_audit_log_missing_required_fields(self, db_session: Session):
        """Test that audit log creation fails with missing required fields."""
        # Test missing user_email
        with pytest.raises(IntegrityError):
            audit_log = AuditLog(
                user_id=uuid4(),
                action_type=ActionType.TOGGLE_ENABLE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name="test_feature",
            )
            db_session.add(audit_log)
            db_session.commit()

        db_session.rollback()

        # Test missing action_type
        with pytest.raises(IntegrityError):
            audit_log = AuditLog(
                user_id=uuid4(),
                user_email="test@example.com",
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name="test_feature",
            )
            db_session.add(audit_log)
            db_session.commit()

        db_session.rollback()

        # Test missing entity_type
        with pytest.raises(IntegrityError):
            audit_log = AuditLog(
                user_id=uuid4(),
                user_email="test@example.com",
                action_type=ActionType.TOGGLE_ENABLE.value,
                entity_id=uuid4(),
                entity_name="test_feature",
            )
            db_session.add(audit_log)
            db_session.commit()

    def test_action_description_property(self, db_session: Session):
        """Test the action_description property for various action types."""
        test_cases = [
            (ActionType.TOGGLE_ENABLE, "enabled"),
            (ActionType.TOGGLE_DISABLE, "disabled"),
            (ActionType.FEATURE_FLAG_CREATE, "created"),
            (ActionType.FEATURE_FLAG_UPDATE, "updated"),
            (ActionType.FEATURE_FLAG_DELETE, "deleted"),
            (ActionType.EXPERIMENT_CREATE, "created"),
            (ActionType.USER_LOGIN, "logged in"),
            (ActionType.SAFETY_ROLLBACK, "rolled back"),
        ]

        for action_type, expected_description in test_cases:
            audit_log = AuditLog(
                user_email="test@example.com",
                action_type=action_type.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name="test_entity",
            )

            assert audit_log.action_description == expected_description

    def test_audit_log_to_dict_method(self, db_session: Session):
        """Test the to_dict method for converting audit log to dictionary."""
        # Create a test user first
        user = User(
            username="todictuser",
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.DEVELOPER,
        )
        db_session.add(user)
        db_session.commit()

        entity_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        audit_log = AuditLog(
            user_id=user.id,
            user_email="test@example.com",
            action_type=ActionType.TOGGLE_ENABLE.value,
            entity_type=EntityType.FEATURE_FLAG.value,
            entity_id=entity_id,
            entity_name="test_feature",
            old_value="inactive",
            new_value="active",
            reason="Testing to_dict method",
            timestamp=timestamp,
        )

        db_session.add(audit_log)
        db_session.commit()

        # Convert to dictionary
        audit_dict = audit_log.to_dict()

        # Verify dictionary structure and values
        assert isinstance(audit_dict, dict)
        assert audit_dict["id"] == str(audit_log.id)
        assert audit_dict["user_id"] == str(user.id)
        assert audit_dict["user_email"] == "test@example.com"
        assert audit_dict["action_type"] == ActionType.TOGGLE_ENABLE.value
        assert audit_dict["entity_type"] == EntityType.FEATURE_FLAG.value
        assert audit_dict["entity_id"] == str(entity_id)
        assert audit_dict["entity_name"] == "test_feature"
        assert audit_dict["old_value"] == "inactive"
        assert audit_dict["new_value"] == "active"
        assert audit_dict["reason"] == "Testing to_dict method"
        assert audit_dict["action_description"] == "enabled"
        assert audit_dict["timestamp"] == timestamp.isoformat()
        assert "created_at" in audit_dict
        assert "updated_at" in audit_dict

    def test_audit_log_to_dict_with_none_values(self, db_session: Session):
        """Test to_dict method with None values."""
        audit_log = AuditLog(
            user_id=None,
            user_email="system@example.com",
            action_type=ActionType.SAFETY_ROLLBACK.value,
            entity_type=EntityType.FEATURE_FLAG.value,
            entity_id=uuid4(),
            entity_name="test_feature",
            old_value=None,
            new_value=None,
            reason=None,
        )

        db_session.add(audit_log)
        db_session.commit()

        audit_dict = audit_log.to_dict()

        assert audit_dict["user_id"] is None
        assert audit_dict["old_value"] is None
        assert audit_dict["new_value"] is None
        assert audit_dict["reason"] is None

    def test_audit_log_user_relationship(self, db_session: Session):
        """Test the relationship between AuditLog and User."""
        # Create a test user
        user = User(
            username="relationshipuser",
            email="relationship@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.DEVELOPER,
        )
        db_session.add(user)
        db_session.commit()

        # Create audit log linked to user
        audit_log = AuditLog(
            user_id=user.id,
            user_email=user.email,
            action_type=ActionType.FEATURE_FLAG_CREATE.value,
            entity_type=EntityType.FEATURE_FLAG.value,
            entity_id=uuid4(),
            entity_name="relationship_test_feature",
        )

        db_session.add(audit_log)
        db_session.commit()

        # Test relationship from audit log to user
        assert audit_log.user is not None
        assert audit_log.user.id == user.id
        assert audit_log.user.email == user.email

        # Test relationship from user to audit logs
        assert len(user.audit_logs) >= 1
        assert audit_log in user.audit_logs

    def test_audit_log_repr_method(self, db_session: Session):
        """Test the __repr__ method for audit log."""
        entity_id = uuid4()
        audit_log = AuditLog(
            user_email="repr@example.com",
            action_type=ActionType.TOGGLE_ENABLE.value,
            entity_type=EntityType.FEATURE_FLAG.value,
            entity_id=entity_id,
            entity_name="repr_test_feature",
        )

        db_session.add(audit_log)
        db_session.commit()

        repr_str = repr(audit_log)

        # Check that key information is in the repr string
        assert "AuditLog" in repr_str
        assert str(audit_log.id) in repr_str
        assert ActionType.TOGGLE_ENABLE.value in repr_str
        assert EntityType.FEATURE_FLAG.value in repr_str
        assert str(entity_id) in repr_str
        assert "repr@example.com" in repr_str


class TestActionTypeEnum:
    """Test cases for ActionType enum."""

    def test_action_type_enum_values(self):
        """Test that all ActionType enum values are correctly defined."""
        expected_actions = [
            "toggle_enable",
            "toggle_disable",
            "feature_flag_create",
            "feature_flag_update",
            "feature_flag_delete",
            "feature_flag_activate",
            "feature_flag_deactivate",
            "experiment_create",
            "experiment_update",
            "experiment_delete",
            "experiment_start",
            "experiment_pause",
            "experiment_complete",
            "user_create",
            "user_update",
            "user_delete",
            "user_login",
            "user_logout",
            "permission_grant",
            "permission_revoke",
            "role_assign",
            "role_unassign",
            "safety_rollback",
            "safety_config_update",
        ]

        for action in expected_actions:
            assert hasattr(ActionType, action.upper())
            assert ActionType[action.upper()].value == action

    def test_action_type_string_conversion(self):
        """Test that ActionType enum values can be converted to strings."""
        assert ActionType.TOGGLE_ENABLE.value == "toggle_enable"
        assert ActionType.FEATURE_FLAG_CREATE.value == "feature_flag_create"
        assert ActionType.EXPERIMENT_START.value == "experiment_start"


class TestEntityTypeEnum:
    """Test cases for EntityType enum."""

    def test_entity_type_enum_values(self):
        """Test that all EntityType enum values are correctly defined."""
        expected_entities = [
            "feature_flag",
            "experiment",
            "user",
            "role",
            "permission",
            "safety_config",
            "rollout_schedule",
        ]

        for entity in expected_entities:
            assert hasattr(EntityType, entity.upper())
            assert EntityType[entity.upper()].value == entity

    def test_entity_type_string_conversion(self):
        """Test that EntityType enum values can be converted to strings."""
        assert EntityType.FEATURE_FLAG.value == "feature_flag"
        assert EntityType.EXPERIMENT.value == "experiment"
        assert EntityType.USER.value == "user"