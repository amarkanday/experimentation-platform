# Feature flag database models
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    Enum,
    Text,
    Index,
    CheckConstraint,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name
import enum



class FeatureFlagStatus(enum.Enum):
    """Feature flag status enum."""

    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class FeatureFlag(Base, BaseModel):
    """Feature flag model for feature toggles."""

    __tablename__ = "feature_flags"

    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(
        Enum(FeatureFlagStatus),
        default=FeatureFlagStatus.INACTIVE,
        nullable=False,
        index=True,
    )
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.users.id", ondelete="SET NULL"),
    )
    targeting_rules = Column(JSONB)  # Rules for flag enablement
    rollout_percentage = Column(Integer, default=0, nullable=False)  # Gradual rollout
    variants = Column(JSONB)  # For multivariate flags
    tags = Column(JSONB)  # For categorization

    # Relationships
    owner = relationship("User", back_populates="feature_flags")
    overrides = relationship(
        "FeatureFlagOverride",
        back_populates="feature_flag",
        cascade="all, delete-orphan",
    )
    events = relationship(
        "Event", back_populates="feature_flag", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="feature_flag", cascade="all, delete"
    )
    rollout_schedules = relationship(
        "RolloutSchedule",
        back_populates="feature_flag",
        cascade="all, delete-orphan",
    )
    raw_metrics = relationship(
        "RawMetric",
        back_populates="feature_flag",
        cascade="all, delete-orphan"
    )
    aggregated_metrics = relationship(
        "AggregatedMetric",
        back_populates="feature_flag",
        cascade="all, delete-orphan"
    )
    error_logs = relationship(
        "ErrorLog",
        back_populates="feature_flag",
        cascade="all, delete-orphan"
    )
    safety_config = relationship(
        "FeatureFlagSafetyConfig",
        back_populates="feature_flag",
        cascade="all, delete-orphan",
        uselist=False  # One-to-one relationship
    )

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite index for owner + status
            Index(f"{schema_name}_feature_flag_owner_status", "owner_id", "status"),
            # Check that rollout percentage is between 0 and 100
            CheckConstraint(
                "rollout_percentage >= 0 AND rollout_percentage <= 100",
                name="check_rollout_percentage",
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<FeatureFlag {self.key}>"


class FeatureFlagOverride(Base, BaseModel):
    """Override model for user-specific feature flag settings."""

    __tablename__ = "feature_flag_overrides"

    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(String(255), nullable=False)  # External user identifier
    value = Column(
        JSONB, nullable=False
    )  # Can be boolean or variant name for multivariate flags
    reason = Column(String(255))  # Optional explanation
    expires_at = Column(DateTime)  # Optional expiration

    # Relationships
    feature_flag = relationship("FeatureFlag", back_populates="overrides")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite unique constraint on feature flag + user
            Index(
                f"{schema_name}_override_feature_user",
                "feature_flag_id",
                "user_id",
                unique=True,
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<FeatureFlagOverride {self.feature_flag_id}:{self.user_id}>"
