# backend/app/models/experiment.py
"""
Experiment-related database models for the experimentation platform.

This module defines models for experiments, variants, and metrics.
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    Enum as SQLAEnum,
    Text,
    Index,
    CheckConstraint,
    DateTime,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name
import enum
import uuid


class ExperimentStatus(enum.Enum):
    """Experiment status enum."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ExperimentType(enum.Enum):
    """Types of experiments."""

    A_B = "a_b"  # Simple A/B test
    MULTIVARIATE = "mv"  # Test with multiple variants
    SPLIT_URL = "split_url"  # Split test with different URLs
    BANDIT = "bandit"  # Multi-armed bandit


class MetricType(enum.Enum):
    """Types of metrics."""

    CONVERSION = "conversion"  # Binary conversion event
    REVENUE = "revenue"  # Revenue/monetary value
    COUNT = "count"  # Event count
    DURATION = "duration"  # Time duration
    CUSTOM = "custom"  # Custom metric


class Experiment(Base, BaseModel):
    """Experiment model for A/B testing."""

    __tablename__ = "experiments"

    name = Column(String(100), nullable=False)
    description = Column(Text)
    hypothesis = Column(Text)
    status = Column(
        SQLAEnum(ExperimentStatus),
        default=ExperimentStatus.DRAFT,
        nullable=False,
        index=True,
    )
    experiment_type = Column(
        SQLAEnum(ExperimentType),
        default=ExperimentType.A_B,
        nullable=False,
    )
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.users.id", ondelete="SET NULL"),
    )
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    targeting_rules = Column(JSONB)  # For user segmentation
    metrics = Column(JSONB)  # Metrics to track
    tags = Column(JSONB)  # For categorization

    # Relationships
    owner = relationship("User", back_populates="experiments")
    variants = relationship(
        "Variant", back_populates="experiment", cascade="all, delete-orphan"
    )
    metric_definitions = relationship(
        "Metric", back_populates="experiment", cascade="all, delete-orphan"
    )
    events = relationship(
        "Event", back_populates="experiment", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="experiment", cascade="all, delete"
    )

    # Add assignments relationship
    assignments = relationship(
        "Assignment", back_populates="experiment", cascade="all, delete-orphan"
    )

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite index for finding active experiments within a date range
            Index(
                f"{schema_name}_experiment_status_dates",
                "status",
                "start_date",
                "end_date",
            ),
            # Owner + status index for quickly finding a user's active experiments
            Index(f"{schema_name}_experiment_owner_status", "owner_id", "status"),
            # Ensure end_date is after start_date
            CheckConstraint(
                "end_date IS NULL OR start_date IS NULL OR end_date > start_date",
                name="check_experiment_dates",
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<Experiment {self.name}>"


class Variant(Base, BaseModel):
    """Variant model for experiment variations."""

    __tablename__ = "variants"

    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_control = Column(Boolean, default=False)
    traffic_allocation = Column(Integer, default=50)  # Percentage of traffic
    configuration = Column(JSONB)  # Settings specific to this variant

    # Relationships
    experiment = relationship("Experiment", back_populates="variants")
    assignments = relationship(
        "Assignment", back_populates="variant", cascade="all, delete-orphan"
    )
    # Add events relationship
    events = relationship(
        "Event", back_populates="variant", cascade="all, delete-orphan"
    )
    # Ensure assignments relationship is properly defined
    assignments = relationship(
        "Assignment", back_populates="variant", cascade="all, delete-orphan"
    )

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite index for quickly finding variants of an experiment
            Index(f"{schema_name}_variant_experiment", "experiment_id"),
            # Check that traffic allocation is between 0 and 100
            CheckConstraint(
                "traffic_allocation >= 0 AND traffic_allocation <= 100",
                name="check_traffic_allocation",
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<Variant {self.name}>"


class Metric(Base, BaseModel):
    """Metric model for experiment measurements."""

    __tablename__ = "metrics"

    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    description = Column(Text)
    event_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(
        SQLAEnum(MetricType), default=MetricType.CONVERSION, nullable=False
    )
    is_primary = Column(Boolean, default=False)
    aggregation_method = Column(String(50), default="average")
    minimum_sample_size = Column(Integer, default=100)
    expected_effect = Column(Float)
    event_value_path = Column(String(100))
    lower_is_better = Column(Boolean, default=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="metric_definitions")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite index for experiment + event
            Index(
                f"{schema_name}_metric_experiment_event", "experiment_id", "event_name"
            ),
            # Ensure unique metric names within an experiment
            Index(
                f"{schema_name}_metric_experiment_name",
                "experiment_id",
                "name",
                unique=True,
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<Metric {self.name}>"
