"""
Database models for feature flag safety monitoring.

This module defines the models for storing safety settings, feature flag safety configurations,
and rollback history for the safety monitoring system.
"""

from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    Text,
    Index,
    DateTime,
    Enum as SQLAEnum,
    func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from enum import Enum

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name


class RollbackTriggerType(str, Enum):
    """Types of rollback triggers."""
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    CUSTOM_METRIC = "custom_metric"


class SafetySettings(Base, BaseModel):
    """Global safety settings for feature flag rollouts."""
    __tablename__ = "safety_settings"

    enable_automatic_rollbacks = Column(Boolean, default=False, nullable=False)
    default_metrics = Column(JSONB, nullable=True)  # Dictionary of metric names to threshold configs

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return ({"schema": schema_name},)


class FeatureFlagSafetyConfig(Base, BaseModel):
    """Safety configuration for specific feature flags."""
    __tablename__ = "feature_flag_safety_configs"

    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )
    enabled = Column(Boolean, default=True, nullable=False)
    metrics = Column(JSONB, nullable=False, default={})  # Dictionary of metric names to threshold configs
    rollback_percentage = Column(Integer, default=0, nullable=False)

    # Relationships
    feature_flag = relationship("FeatureFlag", back_populates="safety_config")
    rollback_records = relationship(
        "SafetyRollbackRecord",
        back_populates="safety_config",
        cascade="all, delete-orphan",
    )

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Unique constraint on feature flag ID
            Index(f"{schema_name}_safety_config_feature_flag_id_idx", "feature_flag_id", unique=True),
            {"schema": schema_name},
        )


class SafetyRollbackRecord(Base, BaseModel):
    """Record of a safety-triggered rollback."""
    __tablename__ = "safety_rollback_records"

    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )
    safety_config_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.feature_flag_safety_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_type = Column(String, nullable=False)  # Type of trigger that caused rollback
    trigger_reason = Column(Text, nullable=False)  # Description of the reason for rollback
    previous_percentage = Column(Integer, nullable=False)  # Rollout percentage before rollback
    target_percentage = Column(Integer, nullable=False)  # Target rollout percentage after rollback
    success = Column(Boolean, default=False, nullable=False)  # Whether the rollback was successful
    executed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    feature_flag = relationship("FeatureFlag")
    safety_config = relationship("FeatureFlagSafetyConfig", back_populates="rollback_records")
    executed_by = relationship("User")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Index for querying by feature flag
            Index(f"{schema_name}_rollback_feature_flag_id_idx", "feature_flag_id"),
            # Index for querying by date
            Index(f"{schema_name}_rollback_created_at_idx", "created_at"),
            {"schema": schema_name},
        )
