from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    Table,
    Enum,
    Text,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
import enum

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name
import typing

# Define UserRole enum for direct role assignment
class UserRole(str, enum.Enum):
    """User roles in the system."""
    ADMIN = "admin"
    ANALYST = "analyst"
    DEVELOPER = "developer"
    VIEWER = "viewer"

# Many-to-many relationship table for users and roles
def _get_users_table_name():
    return f"{get_schema_name()}.users"


def _get_roles_table_name():
    return f"{get_schema_name()}.roles"


def _get_permissions_table_name():
    return f"{get_schema_name()}.permissions"


user_role_association = Table(
    "user_role_association",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey(f"{_get_users_table_name()}.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey(f"{_get_roles_table_name()}.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema=get_schema_name(),
)

# Many-to-many relationship table for roles and permissions
role_permission_association = Table(
    "role_permission_association",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey(f"{_get_roles_table_name()}.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey(f"{_get_permissions_table_name()}.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema=get_schema_name(),
)


class User(Base, BaseModel):
    """User model for authentication and ownership."""

    __tablename__ = "users"

    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    external_id = Column(String(255), unique=True, nullable=True)  # Cognito ID
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    settings = Column(JSONB, default={})
    preferences = Column(JSONB, default={})

    # Relationships
    experiments = relationship("Experiment", back_populates="owner")
    feature_flags = relationship("FeatureFlag", back_populates="owner")
    reports = relationship("Report", back_populates="owner")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="owner", cascade="all, delete-orphan")
    rollout_schedules = relationship("RolloutSchedule", back_populates="owner", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize a user with proper handling of full_name and preferences."""
        # Extract full_name if present and not None
        full_name = kwargs.pop('full_name', None)

        # Extract preferences if present or set to default empty dict
        preferences = kwargs.pop('preferences', {})

        # Make sure we handle the case where full_name is passed but is None
        if 'full_name' in kwargs:
            kwargs.pop('full_name')

        # Initialize using parent class
        super().__init__(**kwargs)

        # Set preferences
        self.preferences = preferences

        # Set the full_name using the property setter if provided
        if full_name is not None:
            self.full_name = full_name

    @property
    def full_name(self):
        """Return the full name by combining first and last name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return None

    @full_name.setter
    def full_name(self, value):
        """Set first_name based on the full name provided."""
        if value:
            parts = value.split(' ', 1)
            self.first_name = parts[0]
            self.last_name = parts[1] if len(parts) > 1 else None
        else:
            self.first_name = None
            self.last_name = None

    @declared_attr
    def __table_args__(cls):
        return ({"schema": get_schema_name()},)

    def __repr__(self):
        return f"<User {self.username}>"


class Role(Base, BaseModel):
    """Role model for grouping permissions."""

    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))

    @declared_attr
    def __table_args__(cls):
        return ({"schema": get_schema_name()},)

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base, BaseModel):
    """Permission model for defining granular access controls."""

    __tablename__ = "permissions"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    resource = Column(
        String(50), nullable=False, index=True
    )  # e.g., 'experiment', 'feature_flag'
    action = Column(
        String(50), nullable=False
    )  # e.g., 'create', 'read', 'update', 'delete'

    @declared_attr
    def __table_args__(cls):
        return ({"schema": get_schema_name()},)

    def __repr__(self):
        return f"<Permission {self.name}>"
