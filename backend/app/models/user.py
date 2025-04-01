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

from .base import Base, BaseModel
from backend.app.core.database_config import get_schema_name
import typing


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

    # Relationships with explicit back_populates
    feature_flags = relationship(
        "FeatureFlag", back_populates="owner", cascade="all, delete-orphan"
    )
    experiments = relationship(
        "Experiment", back_populates="owner", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )

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
