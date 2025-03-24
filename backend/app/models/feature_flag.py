# Feature flag database models
# models/feature_flag.py
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
from .base import Base, BaseModel
import enum
from .user import User
from sqlalchemy.orm import configure_mappers

# configure_mappers()
# At the bottom of the file, after FeatureFlag definition
User.feature_flags = relationship("FeatureFlag", back_populates="owner")


class FeatureFlagStatus(enum.Enum):
    """Feature flag status enum."""

    INACTIVE = "inactive"
    ACTIVE = "active"


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
        UUID(as_uuid=True), ForeignKey("experimentation.users.id", ondelete="SET NULL")
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
    events = relationship("Event", back_populates="feature_flag")

    __table_args__ = (
        # Composite index for owner + status
        Index("idx_feature_flag_owner_status", owner_id, status),
        # Check that rollout percentage is between 0 and 100
        CheckConstraint(
            "rollout_percentage >= 0 AND rollout_percentage <= 100",
            name="check_rollout_percentage",
        ),
        {"schema": "experimentation"},
    )


class FeatureFlagOverride(Base, BaseModel):
    """Override model for user-specific feature flag settings."""

    __tablename__ = "feature_flag_overrides"

    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experimentation.feature_flags.id", ondelete="CASCADE"),
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

    __table_args__ = (
        # Composite unique constraint on feature flag + user
        Index("idx_override_feature_user", feature_flag_id, user_id, unique=True),
        {"schema": "experimentation"},
    )
