# models/experiment.py (modified)
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
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum


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
        Enum(ExperimentStatus),
        default=ExperimentStatus.DRAFT,
        nullable=False,
        index=True,
    )
    experiment_type = Column(
        Enum(ExperimentType), default=ExperimentType.A_B, nullable=False
    )
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("experimentation.users.id", ondelete="SET NULL")
    )
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    targeting_rules = Column(JSONB)  # For user segmentation
    metrics = Column(JSONB)  # Metrics to track
    tags = Column(JSONB)  # For categorization

    # Use string references for relationships to avoid import cycles
    owner = relationship("User")
    variants = relationship(
        "Variant", back_populates="experiment", cascade="all, delete-orphan"
    )
    # Don't define the events and assignments relationships yet
    metric_definitions = relationship(
        "Metric", back_populates="experiment", cascade="all, delete-orphan"
    )

    # Create indexes for faster querying
    __table_args__ = (
        # Composite index for finding active experiments within a date range
        Index("idx_experiment_status_dates", status, start_date, end_date),
        # Owner + status index for quickly finding a user's active experiments
        Index("idx_experiment_owner_status", owner_id, status),
        # Ensure end_date is after start_date
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date > start_date",
            name="check_experiment_dates",
        ),
        {"schema": "experimentation"},
    )


class Metric(Base, BaseModel):
    """Metric model for experiment measurements."""

    __tablename__ = "metrics"

    name = Column(String(100), nullable=False)
    description = Column(Text)
    event_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(
        Enum(MetricType), default=MetricType.CONVERSION, nullable=False
    )
    is_primary = Column(Boolean, default=False)
    aggregation_method = Column(
        String(50), default="average"
    )  # average, sum, unique, etc.
    minimum_sample_size = Column(Integer, default=100)
    expected_effect = Column(Float)  # Expected effect size for power calculations
    event_value_path = Column(
        String(100)
    )  # JSON path to extract value from event payload
    lower_is_better = Column(Boolean, default=False)
    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experimentation.experiments.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    experiment = relationship("Experiment", back_populates="metric_definitions")

    __table_args__ = (
        # Composite index for experiment + event
        Index("idx_metric_experiment_event", experiment_id, event_name),
        # Ensure unique metric names within an experiment
        Index("idx_metric_experiment_name", experiment_id, name, unique=True),
        {"schema": "experimentation"},
    )


class Variant(Base, BaseModel):
    """Variant model for experiment variations."""

    __tablename__ = "variants"

    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experimentation.experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_control = Column(Boolean, default=False)
    traffic_allocation = Column(Integer, default=50)  # Percentage of traffic
    configuration = Column(JSONB)  # Settings specific to this variant

    # Relationships
    experiment = relationship("Experiment", back_populates="variants")
    # Use a string reference for the assignment relationship
    # assignments = relationship("Assignment")

    __table_args__ = (
        # Composite index for quickly finding variants of an experiment
        Index("idx_variant_experiment", experiment_id),
        # Check that traffic allocation is between 0 and 100
        CheckConstraint(
            "traffic_allocation >= 0 AND traffic_allocation <= 100",
            name="check_traffic_allocation",
        ),
        {"schema": "experimentation"},
    )
