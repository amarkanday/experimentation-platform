# models/assignment.py
from sqlalchemy import Column, String, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base, BaseModel


class Assignment(Base, BaseModel):
    """Assignment model for tracking user experiment assignments."""

    __tablename__ = "assignments"

    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experimentation.experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experimentation.variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(String(255), nullable=False)  # External user identifier
    context = Column(JSONB)  # User attributes used for targeting

    # Use string references for relationships
    experiment = relationship("Experiment")
    variant = relationship("Variant")

    __table_args__ = (
        # Composite unique constraint on experiment + user
        Index("idx_assignment_experiment_user", experiment_id, user_id, unique=True),
        # Index for querying all assignments for a user
        Index("idx_assignment_user", user_id),
        {"schema": "experimentation"},
    )
