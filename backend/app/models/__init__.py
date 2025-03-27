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
if not hasattr(User, "experiments") or User.experiments is None:
    User.experiments = relationship("Experiment", back_populates="owner")

if not hasattr(User, "feature_flags") or User.feature_flags is None:
    User.feature_flags = relationship("FeatureFlag", back_populates="owner")

if not hasattr(User, "roles") or User.roles is None:
    User.roles = relationship("Role", secondary=user_role_association, backref="users")

# Variant relationships
if not hasattr(Variant, "assignments") or Variant.assignments is None:
    Variant.assignments = relationship("Assignment", back_populates="variant")

# Experiment relationships
if not hasattr(Experiment, "assignments") or Experiment.assignments is None:
    Experiment.assignments = relationship(
        "Assignment", back_populates="experiment", cascade="all, delete-orphan"
    )

if not hasattr(Experiment, "events") or Experiment.events is None:
    Experiment.events = relationship("Event", back_populates="experiment")

# Assignment relationships
if not hasattr(Assignment, "experiment") or Assignment.experiment is None:
    Assignment.experiment = relationship("Experiment", back_populates="assignments")

if not hasattr(Assignment, "variant") or Assignment.variant is None:
    Assignment.variant = relationship("Variant", back_populates="assignments")

# Feature Flag relationships
if not hasattr(FeatureFlag, "events") or FeatureFlag.events is None:
    FeatureFlag.events = relationship("Event", back_populates="feature_flag")


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
