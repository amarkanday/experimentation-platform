"""
Database model for audit logging.

This module defines the AuditLog model for tracking all user actions and changes
in the experimentation platform. It provides a comprehensive audit trail for
compliance, debugging, and analysis purposes.
"""

from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Index,
    ForeignKey,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from enum import Enum

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name


class ActionType(str, Enum):
    """Types of actions that can be audited."""
    # Feature Flag Actions
    TOGGLE_ENABLE = "toggle_enable"
    TOGGLE_DISABLE = "toggle_disable"
    FEATURE_FLAG_CREATE = "feature_flag_create"
    FEATURE_FLAG_UPDATE = "feature_flag_update"
    FEATURE_FLAG_DELETE = "feature_flag_delete"
    FEATURE_FLAG_ACTIVATE = "feature_flag_activate"
    FEATURE_FLAG_DEACTIVATE = "feature_flag_deactivate"

    # Experiment Actions
    EXPERIMENT_CREATE = "experiment_create"
    EXPERIMENT_UPDATE = "experiment_update"
    EXPERIMENT_DELETE = "experiment_delete"
    EXPERIMENT_START = "experiment_start"
    EXPERIMENT_PAUSE = "experiment_pause"
    EXPERIMENT_COMPLETE = "experiment_complete"

    # User Actions
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"

    # Permission Actions
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_ASSIGN = "role_assign"
    ROLE_UNASSIGN = "role_unassign"

    # Safety Actions
    SAFETY_ROLLBACK = "safety_rollback"
    SAFETY_CONFIG_UPDATE = "safety_config_update"


class EntityType(str, Enum):
    """Types of entities that can be audited."""
    FEATURE_FLAG = "feature_flag"
    EXPERIMENT = "experiment"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SAFETY_CONFIG = "safety_config"
    ROLLOUT_SCHEDULE = "rollout_schedule"


class AuditLog(Base, BaseModel):
    """Audit log model for tracking all user actions and changes."""
    __tablename__ = "audit_logs"

    # User information
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.users.id", ondelete="SET NULL"),
        nullable=True,  # Allow NULL for system actions
    )
    user_email = Column(String(255), nullable=False)

    # Action details
    action_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_name = Column(String(255), nullable=False)

    # Change tracking
    old_value = Column(String(50), nullable=True)
    new_value = Column(String(50), nullable=True)

    # Additional context
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Performance indexes
            Index(f"{schema_name}_audit_logs_timestamp_idx", "timestamp", postgresql_using="btree"),
            Index(f"{schema_name}_audit_logs_user_id_idx", "user_id"),
            Index(f"{schema_name}_audit_logs_entity_idx", "entity_type", "entity_id"),
            Index(f"{schema_name}_audit_logs_action_type_idx", "action_type"),
            # Composite index for common queries
            Index(f"{schema_name}_audit_logs_user_timestamp_idx", "user_id", "timestamp"),
            Index(f"{schema_name}_audit_logs_entity_timestamp_idx", "entity_type", "entity_id", "timestamp"),
            {"schema": schema_name},
        )

    def __repr__(self) -> str:
        """String representation of the audit log."""
        return (
            f"<AuditLog(id={self.id}, "
            f"action_type={self.action_type}, "
            f"entity_type={self.entity_type}, "
            f"entity_id={self.entity_id}, "
            f"user_email={self.user_email}, "
            f"timestamp={self.timestamp})>"
        )

    @property
    def action_description(self) -> str:
        """Human-readable description of the action."""
        action_descriptions = {
            ActionType.TOGGLE_ENABLE: "enabled",
            ActionType.TOGGLE_DISABLE: "disabled",
            ActionType.FEATURE_FLAG_CREATE: "created",
            ActionType.FEATURE_FLAG_UPDATE: "updated",
            ActionType.FEATURE_FLAG_DELETE: "deleted",
            ActionType.FEATURE_FLAG_ACTIVATE: "activated",
            ActionType.FEATURE_FLAG_DEACTIVATE: "deactivated",
            ActionType.EXPERIMENT_CREATE: "created",
            ActionType.EXPERIMENT_UPDATE: "updated",
            ActionType.EXPERIMENT_DELETE: "deleted",
            ActionType.EXPERIMENT_START: "started",
            ActionType.EXPERIMENT_PAUSE: "paused",
            ActionType.EXPERIMENT_COMPLETE: "completed",
            ActionType.USER_CREATE: "created",
            ActionType.USER_UPDATE: "updated",
            ActionType.USER_DELETE: "deleted",
            ActionType.USER_LOGIN: "logged in",
            ActionType.USER_LOGOUT: "logged out",
            ActionType.PERMISSION_GRANT: "granted permission",
            ActionType.PERMISSION_REVOKE: "revoked permission",
            ActionType.ROLE_ASSIGN: "assigned role",
            ActionType.ROLE_UNASSIGN: "unassigned role",
            ActionType.SAFETY_ROLLBACK: "rolled back",
            ActionType.SAFETY_CONFIG_UPDATE: "updated safety config",
        }
        return action_descriptions.get(self.action_type, self.action_type)

    def to_dict(self) -> dict:
        """Convert audit log to dictionary."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_email": self.user_email,
            "action_type": self.action_type,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "entity_name": self.entity_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "action_description": self.action_description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }