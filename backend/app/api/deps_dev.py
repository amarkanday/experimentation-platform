"""
Development authentication dependencies that bypass Cognito.
Use these ONLY in local development, never in production!
"""

import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.models.user import User, UserRole
from backend.app.api.deps import get_db

oauth2_scheme_dev = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user_dev(
    token: str = Depends(oauth2_scheme_dev),
    db: Session = Depends(get_db)
) -> User:
    """
    Development-only authentication bypass.
    Returns a test admin user without Cognito validation.

    SECURITY WARNING: This bypasses all authentication!
    Use ONLY in local development with ENVIRONMENT=development
    """
    environment = os.environ.get("ENVIRONMENT", "production")

    if environment != "development":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Development auth bypass is only available in development mode"
        )

    # Check if the token is a special dev token
    if token != "dev-token-admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid development token"
        )

    # Get or create development admin user
    dev_user = db.query(User).filter(User.username == "dev_admin").first()

    if not dev_user:
        dev_user = User(
            username="dev_admin",
            email="admin@example.com",
            full_name="Development Admin",
            role=UserRole.ADMIN,
            is_superuser=True,
            is_active=True,
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "admin123"
        )
        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)

    return dev_user


def get_current_active_user_dev(
    current_user: User = Depends(get_current_user_dev)
) -> User:
    """Get the current active user (dev mode)."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_superuser_dev(
    current_user: User = Depends(get_current_active_user_dev),
) -> User:
    """Get the current superuser (dev mode)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges"
        )
    return current_user
