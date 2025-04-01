# backend/app/models/base.py
from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, String, MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import configure_mappers
from backend.app.core.database_config import get_schema_name

# Create metadata with schema
metadata = MetaData()

# Create base with metadata
Base = declarative_base(metadata=metadata)

# Configure schema for all tables
@declared_attr
def __table_args__(cls):
    """Set schema for all tables."""
    return {'schema': get_schema_name()}

Base.__table_args__ = __table_args__

class BaseModel:
    """
    Abstract base model for common columns and methods.
    This is a mixin, not a table itself.
    """

    # Include common columns
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result


class BaseModelMixin(Base):
    """
    Mixin class providing common columns and methods for all models.
    """

    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__qualname__.lower()

    # Define common columns
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
