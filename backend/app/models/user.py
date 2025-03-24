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
from .base import Base, BaseModel
import typing

# Many-to-many relationship table for users and roles
user_role_association = Table(
    "user_role_association",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("experimentation.users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("experimentation.roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many relationship table for roles and permissions
role_permission_association = Table(
    "role_permission_association",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("experimentation.roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("experimentation.permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base, BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime)
    preferences = Column(JSONB, default={})

    __table_args__ = ({"schema": "experimentation"},)


class Role(Base, BaseModel):
    """Role model for grouping permissions."""

    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))

    __table_args__ = ({"schema": "experimentation"},)


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

    __table_args__ = ({"schema": "experimentation"},)
