# models/assignment.py
from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name


class Assignment(Base, BaseModel):
    """Assignment model for tracking user experiment assignments."""

    __tablename__ = "assignments"

    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(String(255), nullable=False)  # External user identifier
    context = Column(JSONB)  # User attributes used for targeting

    # Relationships with explicit back_populates
    experiment = relationship("Experiment", back_populates="assignments")
    variant = relationship("Variant", back_populates="assignments")

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return (
            # Composite unique constraint on experiment + user
            Index(
                f"{schema_name}_assignment_experiment_user",
                "experiment_id",
                "user_id",
                unique=True,
            ),
            # Index for querying all assignments for a user
            Index(f"{schema_name}_assignment_user", "user_id"),
            {"schema": schema_name},
        )

    def __repr__(self):
        return f"<Assignment user={self.user_id} experiment={self.experiment_id} variant={self.variant_id}>"
