# User Pydantic schemas
"""
User schema models for validation and serialization.

This module defines Pydantic models for user-related data structures.
These models are used for request/response validation and documentation.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
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

    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "password": "SecurePassword123",
            }
        }

    @validator("password")
    def password_strength(cls, v):
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
    password: Optional[SecretStr] = Field(
        None, min_length=8, description="User's password"
    )
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
                "password": "NewSecurePassword123",
                "is_active": True,
                "preferences": {
                    "theme": "dark",
                    "notifications": {"email": True, "push": False},
                },
            }
        }

    @validator("password")
    def password_strength(cls, v):
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
                "current_password": "CurrentSecurePassword123",
                "new_password": "NewSecurePassword456",
            }
        }

    @validator("new_password")
    def password_strength(cls, v):
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


class UserInDB(UserBase):
    """Model for user as stored in the database."""

    id: UUID4
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class UserResponse(UserInDB):
    """Model for user response data."""

    pass


class UserListResponse(BaseModel):
    """Model for paginated user list response."""

    items: List[UserResponse]
    total: int
    skip: int
    limit: int


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
