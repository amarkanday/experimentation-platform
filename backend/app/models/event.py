# models/event.py
from sqlalchemy import Column, String, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name
from enum import Enum


class EventType(str, Enum):
    """Event type enum."""

    EXPOSURE = "exposure"  # User was exposed to a variant
    CONVERSION = "conversion"  # User completed a desired action
    CLICK = "click"  # User clicked on a tracked element
    PAGE_VIEW = "page_view"  # User viewed a tracked page
    CUSTOM = "custom"  # Custom event type


class Event(Base, BaseModel):
    """Event model for tracking user interactions and metric data."""

    __tablename__ = "events"

    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(
        String(255), nullable=False, index=True
    )  # External user identifier
    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.feature_flags.id", ondelete="SET NULL"),
        nullable=True,
    )
    variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.variants.id", ondelete="SET NULL"),
        nullable=True,
    )
    value = Column(Float)  # Numeric value if applicable
    event_metadata = Column(JSONB)  # Additional data
    created_at = Column(
        String, nullable=False, index=True
    )  # Timestamp for when the event was created

    # Relationships
    experiment = relationship("Experiment", back_populates="events")
    feature_flag = relationship("FeatureFlag", back_populates="events")
    variant = relationship("Variant", back_populates="events")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite index for querying events by user + event type
            Index(f"{schema_name}_event_user_type", "user_id", "event_type"),
            # Composite index for experiment + event_type for quick metric calculations
            Index(
                f"{schema_name}_event_experiment_type", "experiment_id", "event_type"
            ),
            # Composite index for feature flag + event_type for quick metric calculations
            Index(
                f"{schema_name}_event_feature_flag_type",
                "feature_flag_id",
                "event_type",
            ),
            # Composite index for timestamp-based queries within an experiment
            Index(
                f"{schema_name}_event_experiment_timestamp",
                "experiment_id",
                "created_at",
            ),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<Event {self.id}: {self.event_type} for user {self.user_id}>"
