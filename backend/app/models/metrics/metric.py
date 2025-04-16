"""
SQLAlchemy models for metrics collection and storage.

This module defines the database models for storing metrics data,
including flag evaluations, targeting rule matches, segment coverage,
and error tracking.
"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Index, DateTime, Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from enum import Enum
from datetime import datetime

from backend.app.models.base import Base, BaseModel
from backend.app.core.database_config import get_schema_name


class MetricType(str, Enum):
    """Types of metrics that can be collected."""

    FLAG_EVALUATION = "flag_evaluation"  # Feature flag was evaluated
    RULE_MATCH = "rule_match"  # Targeting rule was matched
    SEGMENT_MATCH = "segment_match"  # User segment was matched
    ERROR = "error"  # An error occurred during evaluation
    LATENCY = "latency"  # Time taken to evaluate a flag


class AggregationPeriod(str, Enum):
    """Time periods for metric aggregation."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    TOTAL = "total"  # Aggregate of all time


class RawMetric(Base, BaseModel):
    """
    Raw, unaggregated metrics collected during system operation.

    Used for high-resolution data that will later be aggregated.
    Rows in this table can be deleted after aggregation to save space.
    """

    __tablename__ = "raw_metrics"

    metric_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.feature_flags.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    targeting_rule_id = Column(String(255), nullable=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    segment_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.segments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    value = Column(Float, nullable=True)  # Numeric value (e.g., latency in ms)
    count = Column(Integer, nullable=False, default=1)  # Number of occurrences
    meta_data = Column(JSONB, nullable=True)  # Additional context data

    # Relationships
    feature_flag = relationship("FeatureFlag", back_populates="raw_metrics")
    segment = relationship("Segment", back_populates="raw_metrics")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite index for time-based queries for a specific flag
            Index(
                f"{schema_name}_raw_metric_flag_time",
                "feature_flag_id",
                "timestamp"
            ),
            # Composite index for user + flag evaluations
            Index(
                f"{schema_name}_raw_metric_user_flag",
                "user_id",
                "feature_flag_id"
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<RawMetric {self.id}: {self.metric_type} at {self.timestamp}>"


class AggregatedMetric(Base, BaseModel):
    """
    Aggregated metrics for efficient querying and analysis.

    This table stores pre-aggregated metrics based on different time periods
    to enable efficient dashboarding and analysis without scanning large
    amounts of raw data.
    """

    __tablename__ = "aggregated_metrics"

    metric_type = Column(String(50), nullable=False, index=True)
    period = Column(String(10), nullable=False, index=True)  # minute, hour, day, etc.
    period_start = Column(DateTime, nullable=False, index=True)  # Start of aggregation period
    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.feature_flags.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    targeting_rule_id = Column(String(255), nullable=True, index=True)
    segment_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.segments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    count = Column(Integer, nullable=False, default=0)  # Number of occurrences
    sum_value = Column(Float, nullable=True)  # Sum of values (for avg, etc.)
    min_value = Column(Float, nullable=True)  # Minimum value
    max_value = Column(Float, nullable=True)  # Maximum value
    distinct_users = Column(Integer, nullable=True)  # Count of distinct users
    meta_data = Column(JSONB, nullable=True)  # Additional aggregated data

    # Relationships
    feature_flag = relationship("FeatureFlag", back_populates="aggregated_metrics")
    segment = relationship("Segment", back_populates="aggregated_metrics")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Unique constraint for no duplicate aggregation rows
            Index(
                f"{schema_name}_agg_metric_unique",
                "metric_type",
                "period",
                "period_start",
                "feature_flag_id",
                "targeting_rule_id",
                "segment_id",
                unique=True
            ),
            # Composite index for time-based queries
            Index(
                f"{schema_name}_agg_metric_period_time",
                "period",
                "period_start"
            ),
            # Composite index for flag-specific queries
            Index(
                f"{schema_name}_agg_metric_flag_period",
                "feature_flag_id",
                "period",
                "period_start"
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<AggregatedMetric {self.id}: {self.metric_type} for {self.period} starting {self.period_start}>"


class ErrorLog(Base, BaseModel):
    """
    Detailed log of errors that occur during flag evaluation.

    This table stores detailed information about errors to enable
    debugging and monitoring of the system.
    """

    __tablename__ = "error_logs"

    error_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.feature_flags.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id = Column(String(255), nullable=True, index=True)
    message = Column(String(1000), nullable=False)
    stack_trace = Column(String, nullable=True)
    request_data = Column(JSONB, nullable=True)  # Context of the request
    meta_data = Column(JSONB, nullable=True)  # Additional debug data

    # Relationships
    feature_flag = relationship("FeatureFlag", back_populates="error_logs")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite index for querying errors by time and flag
            Index(
                f"{schema_name}_error_flag_time",
                "feature_flag_id",
                "timestamp"
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<ErrorLog {self.id}: {self.error_type} at {self.timestamp}>"
