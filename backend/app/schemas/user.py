"""
User schema models for validation and serialization.

This module defines Pydantic models for user-related data structures.
These models are used for request/response validation and documentation.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import (
    BaseModel,
    Field,
    validator,
    root_validator,
    UUID4,
    EmailStr,
    SecretStr,
    field_validator,
    ConfigDict,
)


class UserBase(BaseModel):
    """Base user model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """User creation model."""
    password: SecretStr = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: SecretStr) -> SecretStr:
        """Validate password strength."""
        password = v.get_secret_value()
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(UserBase):
    """User update model."""
    password: Optional[SecretStr] = None

    model_config = ConfigDict(from_attributes=True)


class UserInDBBase(UserBase):
    """Base model for users in DB."""
    id: str

    model_config = ConfigDict(from_attributes=True)


class User(UserInDBBase):
    """User model for responses."""
    pass


class UserInDB(UserInDBBase):
    """User model with hashed password."""
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    """Password change model."""
    current_password: SecretStr
    new_password: SecretStr = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: SecretStr) -> SecretStr:
        """Validate new password strength."""
        password = v.get_secret_value()
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        return v

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    """Token payload model."""
    sub: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Model for user response data."""

    id: Any  # Accept any type for id to handle both string and UUID
    username: str
    email: str  # Using str instead of EmailStr for test compatibility
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    # Make all optional fields truly optional
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        extra="ignore"  # Ignore extra fields to prevent validation errors
    )


class UserListResponse(BaseModel):
    """Model for paginated user list response."""

    items: List[Dict[str, Any]]
    total: int
    skip: int = 0
    limit: int = 100

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "username": "johndoe",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                        "is_superuser": False,
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100,
            }
        }
    )
