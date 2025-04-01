import uuid
import secrets
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name


def generate_api_key() -> str:
    """Generate a random API key with a prefix."""
    prefix = "eptk"  # Short for "experimentation toolkit"
    random_part = secrets.token_hex(16)
    return f"{prefix}_{random_part}"


class APIKey(Base, BaseModel):
    """API Key model for API authentication."""

    __tablename__ = "api_keys"

    key = Column(
        String(100), unique=True, nullable=False, index=True, default=generate_api_key
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)

    # Scopes for granular API access control
    scopes = Column(String(255), nullable=True)  # Comma-separated list of scopes

    # User relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{get_schema_name()}.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationship with explicit back_populates
    user = relationship("User", back_populates="api_keys")

    @declared_attr
    def __table_args__(cls):
        return ({"schema": get_schema_name()},)

    def __repr__(self):
        return f"<APIKey {self.name} ({self.key[:8]}...)>"

    @property
    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.utcnow()

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    def update_last_used(self, db_session) -> None:
        """Update the last_used_at timestamp."""
        self.last_used_at = func.now()
        db_session.add(self)
        db_session.commit()

    @classmethod
    def create_for_user(
        cls, db_session, user_id, name, description=None, scopes=None, expires_at=None
    ):
        """Create a new API key for a user."""
        api_key = cls(
            user_id=user_id,
            name=name,
            description=description,
            scopes=scopes,
            expires_at=expires_at,
        )
        db_session.add(api_key)
        db_session.commit()
        db_session.refresh(api_key)
        return api_key
