# Authentication and authorization
"""
Security utilities for authentication and authorization.

This module provides functions for password hashing, token generation,
and other security-related operations.
"""

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from backend.app.core.config import settings

# Create password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def decode_token(token: str) -> dict:
    """
    Decode a JWT token and return the claims.
    This is a placeholder implementation for testing purposes.
    In production, this would validate the token against Cognito or another auth provider.

    Args:
        token: JWT token to decode

    Returns:
        Dict containing token claims
    """
    # This is a mock implementation for testing
    # In a real implementation, you would use a JWT library to decode and verify the token
    return {
        "sub": "user_id",
        "username": "username",
        "exp": 0,
        "iat": 0,
        "email": "user@example.com"
    }
