from typing import Generator, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.user import User
from backend.app.services.auth_service import auth_service
from loguru import logger

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


async def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Session: Database session
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the provided JWT token.

    Args:
        token (str): JWT access token
        db (Session): Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get user details from Cognito
        user_data = auth_service.get_user(token)

        # Get user from database
        username = user_data.get("username")
        user = db.query(User).filter(User.username == username).first()

        if not user:
            # Create user in database if not exists
            email = user_data.get("attributes", {}).get("email")
            full_name = (
                f"{user_data.get('attributes', {}).get('given_name', '')} "
                f"{user_data.get('attributes', {}).get('family_name', '')}"
            ).strip()

            user = User(
                username=username, email=email, full_name=full_name, is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
