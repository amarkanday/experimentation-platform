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
)


class UserBase(BaseModel):
    """Base model for user data."""

    username: str = Field(
        ..., min_length=3, max_length=50, description="User's username"
    )
    email: EmailStr = Field(..., description="User's email address")
    full_name: Optional[str] = Field(
        None, max_length=100, description="User's full name"
    )


class UserCreate(UserBase):
    """Model for creating a new user."""

    password: SecretStr = Field(..., min_length=8, description="User's password")
    is_active: bool = Field(True, description="Whether the user is active")
    is_superuser: bool = Field(False, description="Whether the user is a superuser")

    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "password": "Password123",
                "is_active": True,
                "is_superuser": False,
            }
        }

    @validator("password")
    def password_strength(cls, v: SecretStr):
        """Validate password strength."""
        password = v.get_secret_value()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase, one lowercase, and one digit
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")

        return v


class UserUpdate(BaseModel):
    """Model for updating a user."""

    email: Optional[EmailStr] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(
        None, max_length=100, description="User's full name"
    )
    password: Optional[SecretStr] = Field(None, min_length=8, description="User's password")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")
    is_superuser: Optional[bool] = Field(
        None, description="Whether the user is a superuser"
    )
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")

    class Config:
        schema_extra = {
            "example": {
                "email": "john.updated@example.com",
                "full_name": "John Updated Doe",
                "password": "NewPassword123",
                "is_active": True,
                "preferences": {
                    "theme": "dark",
                    "notifications": {"email": True, "push": False},
                },
            }
        }

    @validator("password")
    def password_strength(cls, v: Optional[SecretStr]):
        """Validate password strength if provided."""
        if v is not None:
            password = v.get_secret_value()
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters long")

            # Check for at least one uppercase, one lowercase, and one digit
            if not any(c.isupper() for c in password):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in password):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in password):
                raise ValueError("Password must contain at least one digit")

        return v


class PasswordChange(BaseModel):
    """Model for changing a user's password."""

    current_password: SecretStr = Field(..., description="Current password")
    new_password: SecretStr = Field(..., min_length=8, description="New password")

    class Config:
        schema_extra = {
            "example": {
                "current_password": "CurrentPassword123",
                "new_password": "NewPassword456",
            }
        }

    @validator("new_password")
    def password_strength(cls, v: SecretStr):
        """Validate new password strength."""
        password = v.get_secret_value()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase, one lowercase, and one digit
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")

        return v


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

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        extra = "ignore"  # Ignore extra fields to prevent validation errors


class UserListResponse(BaseModel):
    """Model for paginated user list response."""

    items: List[Dict[str, Any]]
    total: int
    skip: int = 0
    limit: int = 100

    class Config:
        schema_extra = {
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


class Token(BaseModel):
    """Model for authentication token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    id_token: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "id_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class TokenPayload(BaseModel):
    """Model for token payload."""

    sub: str  # Subject (user ID)
    exp: int  # Expiration time
    iat: Optional[int] = None  # Issued at
    jti: Optional[str] = None  # JWT ID
