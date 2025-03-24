# models/event.py
from sqlalchemy import Column, String, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from sqlalchemy.orm import configure_mappers
# configure_mappers()


class Event(Base, BaseModel):
    """Event model for tracking user interactions and metric data."""

    __tablename__ = "events"

    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(
        String(255), nullable=False, index=True
    )  # External user identifier
    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experimentation.experiments.id", ondelete="SET NULL"),
    )
    feature_flag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experimentation.feature_flags.id", ondelete="SET NULL"),
    )
    variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experimentation.variants.id", ondelete="SET NULL"),
    )
    value = Column(Float)  # Numeric value if applicable
    event_metadata = Column(JSONB)  # Additional data
    created_at = Column(
        String, nullable=False, index=True
    )  # Timestamp for when the event was created

    # Relationships
    experiment = relationship("Experiment", back_populates="events")
    feature_flag = relationship("FeatureFlag", back_populates="events")

    __table_args__ = (
        # Composite index for querying events by user + event type
        Index("idx_event_user_type", user_id, event_type),
        # Composite index for experiment + event_type for quick metric calculations
        Index("idx_event_experiment_type", experiment_id, event_type),
        # Composite index for feature flag + event_type for quick metric calculations
        Index("idx_event_feature_flag_type", feature_flag_id, event_type),
        # Composite index for timestamp-based queries within an experiment
        Index("idx_event_experiment_timestamp", experiment_id, created_at),
        {"schema": "experimentation"},
    )
