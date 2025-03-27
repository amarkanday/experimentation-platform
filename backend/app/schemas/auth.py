"""
Pydantic schemas for authentication.

This module defines the request and response schemas for authentication operations.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    """Schema for user registration request."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    email: EmailStr
    given_name: str = Field(..., min_length=1, max_length=50)
    family_name: str = Field(..., min_length=1, max_length=50)


class SignUpResponse(BaseModel):
    """Schema for user registration response."""

    user_id: str
    confirmed: bool
    message: str


class ConfirmSignUpRequest(BaseModel):
    """Schema for confirming user registration."""

    username: str
    confirmation_code: str


class ConfirmSignUpResponse(BaseModel):
    """Schema for confirmation response."""

    message: str
    confirmed: bool


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    id_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    username: str


class ForgotPasswordResponse(BaseModel):
    """Schema for forgot password response."""

    message: str


class ConfirmForgotPasswordRequest(BaseModel):
    """Schema for confirming forgot password."""

    username: str
    confirmation_code: str
    new_password: str = Field(..., min_length=8, max_length=100)


class ConfirmForgotPasswordResponse(BaseModel):
    """Schema for confirm forgot password response."""

    message: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class UserInfoResponse(BaseModel):
    """Schema for user information response."""

    username: str
    attributes: Dict[str, Any]
