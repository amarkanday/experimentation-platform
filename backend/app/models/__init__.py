# models/__init__.py
from sqlalchemy.orm import relationship, configure_mappers

# Import base classes first
from .base import Base, BaseModel

# Import all model classes
from .user import (
    User,
    Role,
    Permission,
    user_role_association,
    role_permission_association,
)
from .experiment import (
    Experiment,
    Variant,
    ExperimentStatus,
    ExperimentType,
    Metric,
    MetricType,
)

from .assignment import Assignment
from .event import Event
from .feature_flag import FeatureFlag, FeatureFlagOverride, FeatureFlagStatus

# Now set up all bidirectional relationships
User.experiments = relationship("Experiment", back_populates="owner")
User.feature_flags = relationship("FeatureFlag", back_populates="owner")

# Add User-Role relationship
User.roles = relationship("Role", secondary=user_role_association, backref="users")

Variant.assignments = relationship("Assignment", back_populates="variant")
Experiment.assignments = relationship(
    "Assignment", back_populates="experiment", cascade="all, delete-orphan"
)
Experiment.events = relationship("Event", back_populates="experiment")

Assignment.experiment = relationship("Experiment", back_populates="assignments")
Assignment.variant = relationship("Variant", back_populates="assignments")


# Now configure all mappers
configure_mappers()

# All models for Alembic to discover
__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Role",
    "Permission",
    "Experiment",
    "Variant",
    "FeatureFlag",
    "FeatureFlagOverride",
    "Assignment",
    "Event",
    "ExperimentStatus",
    "ExperimentType",
    "FeatureFlagStatus",
    "Metric",
    "MetricType",
]
