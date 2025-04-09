from typing import Generator, Optional, Union, Any, Dict
import asyncio
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.user import User
from backend.app.models.experiment import Experiment
from backend.app.services.auth_service import auth_service
from loguru import logger
from backend.app.models.api_key import APIKey

# Try to import Redis, handle gracefully if not installed
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

    # Create a dummy redis class to avoid None.Redis error
    class redis:
        class Redis:
            pass


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# API key header extraction
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


# Cache control model
class CacheControl(BaseModel):
    """Cache control settings."""

    enabled: bool = False
    skip: bool = False
    redis: Optional[object] = None


# Redis pool
_redis_pool = None


async def get_redis_pool():
    """Get Redis connection pool."""
    global _redis_pool
    if not REDIS_AVAILABLE:
        logger.warning("Redis not available, cache disabled")
        return None

    if _redis_pool is None:
        try:
            _redis_pool = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
            )
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            return None
    return _redis_pool


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


def get_token(request: Request) -> str:
    """
    Extract the access token from the Authorization header.

    Args:
        request (Request): FastAPI request object

    Returns:
        str: Access token

    Raises:
        HTTPException: If the token is not found
    """
    authorization = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


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


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.

    Args:
        current_user (User): Current user

    Returns:
        User: Current active user

    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current superuser.

    Args:
        current_user (User): Current active user

    Returns:
        User: Current superuser

    Raises:
        HTTPException: If the user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


def get_current_superuser_or_none(
    current_user: User = Depends(get_current_active_user),
) -> Optional[User]:
    """
    Get current superuser or None.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current user if they are a superuser, None otherwise
    """
    if current_user.is_superuser:
        return current_user
    return None


def get_experiment_access(
    experiment: Union[Experiment, Dict[str, Any]],
    current_user: User = Depends(get_current_active_user)
) -> Union[Experiment, Dict[str, Any]]:
    """
    Check if user has access to experiment.

    Args:
        experiment: Experiment object or dictionary
        current_user: Current authenticated user

    Returns:
        Union[Experiment, Dict[str, Any]]: The experiment if user has access

    Raises:
        HTTPException: If experiment is not found or user does not have access
    """
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )

    # Get owner_id based on input type
    owner_id = experiment.owner_id if isinstance(experiment, Experiment) else experiment.get("owner_id")

    # Superusers have full access
    if current_user.is_superuser:
        return experiment

    # Owners have full access to their own experiments
    if owner_id == current_user.id:
        return experiment

    # For non-superusers and non-owners, deny access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions"
    )


def get_api_key(
    db: Session = Depends(get_db), api_key_header: str = Depends(API_KEY_HEADER)
) -> Optional[User]:
    """
    Validate API key from header and return associated user if valid.

    Args:
        db: Database session
        api_key_header: API key from header

    Returns:
        User: User associated with the API key

    Raises:
        HTTPException: If API key is invalid or inactive
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
            headers={"WWW-Authenticate": "APIKey"},
        )

    # Get API key from database
    api_key = db.query(APIKey).filter(APIKey.key == api_key_header).first()
    if not api_key or not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    # Get associated user
    user = db.query(User).filter(User.id == api_key.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    return user


def get_experiment_by_key(
    experiment_key: str, db: Session = Depends(get_db)
) -> Experiment:
    """
    Get experiment by key.

    Args:
        experiment_key (str): Experiment key
        db (Session): Database session

    Returns:
        Experiment: Experiment with the given key

    Raises:
        HTTPException: If experiment not found or inactive
    """
    # experiment = db.query(Experiment).filter(Experiment.key == experiment_key).first()
    experiment = (
        db.query(Experiment)
        .filter(getattr(Experiment, "key", None) == experiment_key)
        .first()
    )
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    cache_enabled = getattr(settings, "CACHE_ENABLED", False)
    if not experiment.is_active:
        raise HTTPException(status_code=400, detail="Inactive experiment")

    return experiment


async def get_cache_control(skip_cache: bool = False) -> CacheControl:
    """
    Get cache control settings.

    Args:
        skip_cache (bool): Whether to skip cache

    Returns:
        CacheControl: Cache control settings
    """
    cache_control = CacheControl(skip=skip_cache)

    if skip_cache:
        return cache_control

    if not hasattr(settings, "CACHE_ENABLED") or not settings.CACHE_ENABLED:
        return cache_control

    if not REDIS_AVAILABLE:
        return cache_control

    try:
        redis_client = await get_redis_pool()
        if redis_client:
            # Test connection
            await redis_client.ping()
            cache_control.redis = redis_client
            cache_control.enabled = True
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    return cache_control
