"""
Dependency injection module for FastAPI.

This module provides dependencies that can be injected into API endpoints
using FastAPI's dependency injection system.
"""

import logging
from typing import Generator, Optional, Dict, Any, Union
import uuid
import redis
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.services.auth_service import CognitoAuthService

# Configure logging
logger = logging.getLogger(__name__)

# OAuth2 token URL for password-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# Initialize auth service
auth_service = CognitoAuthService()

# Redis client for caching if enabled
redis_client = None
if hasattr(settings, "USE_REDIS") and settings.USE_REDIS:
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        logger.info("Redis client initialized for caching")
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {str(e)}")


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Yields:
        Generator[Session, None, None]: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis() -> Optional[redis.Redis]:
    """
    Redis client dependency for caching.

    Returns:
        Optional[redis.Redis]: Redis client or None if Redis is disabled
    """
    return redis_client


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


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.

    Args:
        current_user (User): Current authenticated user

    Returns:
        User: Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current superuser.

    Args:
        current_user (User): Current authenticated user

    Returns:
        User: Current superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return current_user


def get_experiment_access(
    experiment_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Experiment:
    """
    Check if the current user has access to the specified experiment.

    Args:
        experiment_id (uuid.UUID): Experiment ID
        current_user (User): Current authenticated user
        db (Session): Database session

    Returns:
        Experiment: The experiment if user has access

    Raises:
        HTTPException: If experiment not found or user doesn't have access
    """
    # Superusers have access to all experiments
    if current_user.is_superuser:
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )
        return experiment

    # Regular users can only access experiments they own
    experiment = (
        db.query(Experiment)
        .filter(Experiment.id == experiment_id, Experiment.owner_id == current_user.id)
        .first()
    )

    if not experiment:
        # Check if experiment exists but user doesn't have access
        exists = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this experiment",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )

    return experiment


def get_api_key(
    x_api_key: str = Header(..., description="API Key for tracking endpoints"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Validate the API key for tracking endpoints.

    Args:
        x_api_key (str): API key from header
        db (Session): Database session

    Returns:
        Dict[str, Any]: API key information

    Raises:
        HTTPException: If API key is invalid
    """
    # TODO: Implement actual API key validation against database
    # For now, just check against a configured key for simplicity
    if not hasattr(settings, "API_KEY") or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    # Return API key information (could include project ID, permissions, etc.)
    return {"key": x_api_key, "valid": True}


def get_experiment_by_key(
    experiment_key: str,
    api_key_info: Dict[str, Any] = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> Experiment:
    """
    Get an experiment by its key for tracking endpoints.

    Args:
        experiment_key (str): Experiment key
        api_key_info (Dict[str, Any]): API key information
        db (Session): Database session

    Returns:
        Experiment: The experiment

    Raises:
        HTTPException: If experiment not found
    """
    # Find experiment by key (assuming name is used as key in this implementation)
    experiment = (
        db.query(Experiment)
        .filter(Experiment.name == experiment_key)
        .filter(Experiment.status == ExperimentStatus.ACTIVE)
        .first()
    )

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found or not active",
        )

    return experiment


def get_cache_control(
    skip_cache: bool = False, redis: Optional[redis.Redis] = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Dependency for cache control settings.

    Args:
        skip_cache (bool): Whether to skip cache
        redis (Optional[redis.Redis]): Redis client

    Returns:
        Dict[str, Any]: Cache control settings
    """
    # Default TTL if not configured
    ttl = getattr(settings, "CACHE_TTL", 300)

    return {
        "enabled": redis is not None and not skip_cache,
        "ttl": ttl,
        "client": redis,
    }
