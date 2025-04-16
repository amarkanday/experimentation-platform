# Segmentation models
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name


class Segment(Base, BaseModel):
    """User segment model for targeting rules."""

    __tablename__ = "segments"

    name = Column(String(100), nullable=False)
    description = Column(Text)
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.users.id", ondelete="SET NULL"),
    )
    rules = Column(JSONB)  # Rules for segment membership

    # Relationships
    owner = relationship("User", back_populates="segments")
    raw_metrics = relationship(
        "RawMetric",
        back_populates="segment",
        cascade="all, delete-orphan",
    )
    aggregated_metrics = relationship(
        "AggregatedMetric",
        back_populates="segment",
        cascade="all, delete-orphan",
    )

    @declared_attr
    def __table_args__(cls):
        schema_name = get_schema_name()
        return ({"schema": schema_name},)

    def __repr__(self):
        return f"<Segment {self.id}: {self.name}>"
