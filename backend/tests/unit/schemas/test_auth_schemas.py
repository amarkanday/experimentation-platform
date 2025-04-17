"""
Test Authentication Schemas.

This module contains tests for the Pydantic v2 authentication schema validation.
"""

import pytest
from pydantic import ValidationError

from backend.app.schemas.auth import (
    TokenResponse,
    SignUpRequest,
    SignUpResponse,
    ConfirmSignUpRequest,
    RefreshTokenRequest
)


class TestAuthSchemasValidation:
    """Tests for authentication schemas with Pydantic v2 patterns."""

    def test_token_response(self):
        """Test TokenResponse schema with valid data."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "id_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "expires_in": 3600,
            "token_type": "bearer"
        }

        token = TokenResponse(**data)

        assert token.access_token == data["access_token"]
        assert token.id_token == data["id_token"]
        assert token.refresh_token == data["refresh_token"]
        assert token.expires_in == data["expires_in"]
        assert token.token_type == data["token_type"]

        # Test model_config is properly set
        assert hasattr(TokenResponse, "model_config")

    def test_signup_request(self):
        """Test SignUpRequest schema with valid data."""
        data = {
            "username": "testuser",
            "password": "securepassword123",
            "email": "user@example.com",
            "given_name": "Test",
            "family_name": "User"
        }

        signup_request = SignUpRequest(**data)

        assert signup_request.username == data["username"]
        assert signup_request.password == data["password"]
        assert signup_request.email == data["email"]
        assert signup_request.given_name == data["given_name"]
        assert signup_request.family_name == data["family_name"]

        # Test model_config is properly set
        assert hasattr(SignUpRequest, "model_config")

    def test_signup_response(self):
        """Test SignUpResponse schema with valid data."""
        data = {
            "user_id": "12345",
            "confirmed": False,
            "message": "User registration successful"
        }

        signup_response = SignUpResponse(**data)

        assert signup_response.user_id == data["user_id"]
        assert signup_response.confirmed == data["confirmed"]
        assert signup_response.message == data["message"]

        # Test model_config is properly set
        assert hasattr(SignUpResponse, "model_config")

    def test_confirm_signup_request(self):
        """Test ConfirmSignUpRequest schema with valid data."""
        data = {
            "username": "testuser",
            "confirmation_code": "123456"
        }

        confirm_signup = ConfirmSignUpRequest(**data)

        assert confirm_signup.username == data["username"]
        assert confirm_signup.confirmation_code == data["confirmation_code"]

        # Test model_config is properly set
        assert hasattr(ConfirmSignUpRequest, "model_config")

    def test_refresh_token_request(self):
        """Test RefreshTokenRequest schema with valid data."""
        data = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }

        refresh_request = RefreshTokenRequest(**data)

        assert refresh_request.refresh_token == data["refresh_token"]

        # Test model_config is properly set
        assert hasattr(RefreshTokenRequest, "model_config")
