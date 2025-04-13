"""
Report model for storing analytics reports and visualizations.
"""
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
import enum
from uuid import uuid4

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name


class ReportType(str, enum.Enum):
    """Types of reports that can be created."""
    EXPERIMENT_RESULT = "experiment_result"
    FEATURE_FLAG_USAGE = "feature_flag_usage"
    USER_ACTIVITY = "user_activity"
    CUSTOM = "custom"


class Report(Base, BaseModel):
    """Model for analytics reports and visualizations."""

    __tablename__ = "reports"

    title = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(Enum(ReportType), nullable=False, default=ReportType.CUSTOM)
    data = Column(JSON, nullable=True)  # Stored report data/results
    query_definition = Column(JSON, nullable=True)  # Definition of data query
    visualization_config = Column(JSON, nullable=True)  # Visualization settings
    is_public = Column(Boolean, default=False)  # Whether report is viewable by all users

    # Foreign keys
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.users.id", ondelete="CASCADE"),
        nullable=False,
    )
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

    # Relationships
    owner = relationship("User", back_populates="reports")
    experiment = relationship("Experiment", back_populates="reports")
    feature_flag = relationship("FeatureFlag", back_populates="reports")

    @declared_attr
    def __table_args__(cls):
        return ({"schema": get_schema_name()},)

    def __repr__(self):
        return f"<Report {self.title}>"
