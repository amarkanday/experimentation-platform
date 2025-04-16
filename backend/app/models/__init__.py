# Centralized model imports and initialization

from .base import Base, BaseModel, BaseModelMixin
from .user import (
    User,
    Role,
    Permission,
    user_role_association,
    role_permission_association,
    UserRole,
)
from .experiment import (
    Experiment,
    Variant,
    Metric,
    ExperimentStatus,
    ExperimentType,
    MetricType,
)
from .feature_flag import FeatureFlag, FeatureFlagOverride, FeatureFlagStatus
from .event import Event, EventType
from .assignment import Assignment
from .api_key import APIKey
from .segment import Segment
from .rollout_schedule import (
    RolloutSchedule,
    RolloutStage,
    RolloutScheduleStatus,
    RolloutStageStatus,
    TriggerType,
)
from .metrics.metric import (
    RawMetric,
    AggregatedMetric,
    ErrorLog,
    MetricType as MetricsMetricType,
    AggregationPeriod,
)

# Explicitly list all models that should be part of the base metadata
__all__ = [
    "Base",
    "BaseModel",
    "BaseModelMixin",
    "User",
    "Role",
    "Permission",
    "Experiment",
    "Variant",
    "Metric",
    "FeatureFlag",
    "FeatureFlagOverride",
    "Event",
    "Assignment",
    "APIKey",
    "Segment",
    "user_role_association",
    "role_permission_association",
    "ExperimentStatus",
    "ExperimentType",
    "MetricType",
    "FeatureFlagStatus",
    "EventType",
    "UserRole",
    "RolloutSchedule",
    "RolloutStage",
    "RolloutScheduleStatus",
    "RolloutStageStatus",
    "TriggerType",
    "RawMetric",
    "AggregatedMetric",
    "ErrorLog",
    "MetricsMetricType",
    "AggregationPeriod",
]

# Remove or comment out any premature configuration
# configure_mappers()
