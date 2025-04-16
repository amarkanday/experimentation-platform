from typing import Generator, Optional, Union, Any, Dict
import asyncio
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, SecretStr
from jose import jwt

from backend.app.core.config import settings
from backend.app.core.pagination import Paginator
from backend.app.core.security import oauth2_scheme
from backend.app.core.permissions import ResourceType, Action, check_permission, check_ownership, get_permission_error_message
from backend.app.core.cognito import map_cognito_groups_to_role, should_be_superuser
from backend.app.db.session import SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.models.feature_flag import FeatureFlag
from backend.app.models.report import Report
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
    Syncs user role with Cognito groups on each authentication.

    Args:
        token (str): JWT access token
        db (Session): Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get user details and groups from Cognito
        user_data = auth_service.get_user_with_groups(token)

        # Get user from database
        username = user_data.get("username")
        user = db.query(User).filter(User.username == username).first()

        # Extract groups and map to role
        cognito_groups = user_data.get("groups", [])

        # Map Cognito groups to role
        role = map_cognito_groups_to_role(cognito_groups)

        # Determine superuser status from Cognito admin groups
        is_superuser = should_be_superuser(cognito_groups)

        # If superuser, ensure they have ADMIN role for full permissions
        if is_superuser and role != UserRole.ADMIN:
            role = UserRole.ADMIN
            logger.info(f"User {username} is a superuser, assigning ADMIN role")

        if not user:
            # Create user in database if not exists
            email = user_data.get("attributes", {}).get("email")
            full_name = (
                f"{user_data.get('attributes', {}).get('given_name', '')} "
                f"{user_data.get('attributes', {}).get('family_name', '')}"
            ).strip()

            user = User(
                username=username,
                email=email,
                full_name=full_name,
                is_active=True,
                role=role,
                is_superuser=is_superuser
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            logger.info(f"Created new user {username} with role {role} and superuser={is_superuser}")
        elif settings.SYNC_ROLES_ON_LOGIN:
            # Update user's role and superuser status if changed
            role_changed = user.role != role
            superuser_changed = user.is_superuser != is_superuser

            if role_changed or superuser_changed:
                # Update user properties
                if role_changed:
                    user.role = role
                    logger.info(f"User {username} role updated to {role} based on Cognito groups")

                if superuser_changed:
                    user.is_superuser = is_superuser
                    logger.info(f"User {username} superuser status updated to {is_superuser}")

                # Commit changes to database
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
    Check if user has access to the experiment.

    This function ensures the current user has permission to access
    the specified experiment, checking superuser status, permissions,
    and ownership as needed.

    Args:
        experiment: The experiment to check access for
        current_user: The current authenticated user

    Returns:
        The experiment if access is allowed

    Raises:
        HTTPException: If the user does not have permission to access the experiment
    """
    # Superusers always have access
    if current_user.is_superuser:
        return experiment

    # Check if user has permission to read experiments
    if not check_permission(current_user, ResourceType.EXPERIMENT, Action.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.EXPERIMENT, Action.READ),
        )

    # Check ownership for non-admin users for modification actions
    if not check_permission(current_user, ResourceType.EXPERIMENT, Action.UPDATE) and not check_ownership(current_user, experiment):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this experiment",
        )

    return experiment


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
    Get experiment by key or ID.

    Args:
        experiment_key (str): Experiment key or ID
        db (Session): Database session

    Returns:
        Experiment: Experiment with the given key or ID

    Raises:
        HTTPException: If experiment not found or inactive
    """
    experiment = None

    # First try to lookup by ID (UUID)
    try:
        from uuid import UUID
        experiment_id = UUID(experiment_key)
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    except (ValueError, TypeError):
        # Not a valid UUID, try the original lookup method
        pass

    # If not found by ID, try the original lookup method
    if not experiment:
        experiment = (
            db.query(Experiment)
            .filter(getattr(Experiment, "key", None) == experiment_key)
            .first()
        )

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Check if experiment is active
    if hasattr(experiment, 'status') and experiment.status != ExperimentStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive experiment")

    cache_enabled = getattr(settings, "CACHE_ENABLED", False)
    if cache_enabled:
        experiment_cache = RedisExperimentCache(settings)
        experiment_cache.clear_experiment_cache(str(experiment.id))

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


# Feature Flag permissions
async def get_feature_flag_by_key(
    key: str,
    db: Session = Depends(get_db),
) -> FeatureFlag:
    """Get a feature flag by key."""
    feature_flag = db.query(FeatureFlag).filter(FeatureFlag.key == key).first()
    if not feature_flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag with key {key} not found",
        )
    return feature_flag


async def get_feature_flag_access(
    feature_flag: FeatureFlag = Depends(get_feature_flag_by_key),
    current_user: User = Depends(get_current_user),
) -> FeatureFlag:
    """Check if user has access to the feature flag."""
    if current_user.is_superuser:
        return feature_flag

    # Check if user has permission to read feature flags
    if not check_permission(current_user, ResourceType.FEATURE_FLAG, Action.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.FEATURE_FLAG, Action.READ),
        )

    # Check ownership for non-admin users for modification actions
    if not check_permission(current_user, ResourceType.FEATURE_FLAG, Action.UPDATE) and not check_ownership(current_user, feature_flag):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this feature flag",
        )

    return feature_flag


async def can_create_feature_flag(
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can create a feature flag."""
    if not check_permission(current_user, ResourceType.FEATURE_FLAG, Action.CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.FEATURE_FLAG, Action.CREATE),
        )
    return True


async def can_update_feature_flag(
    feature_flag: FeatureFlag = Depends(get_feature_flag_access),
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can update a feature flag."""
    if not check_permission(current_user, ResourceType.FEATURE_FLAG, Action.UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.FEATURE_FLAG, Action.UPDATE),
        )
    return True


async def can_delete_feature_flag(
    feature_flag: FeatureFlag = Depends(get_feature_flag_access),
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can delete a feature flag."""
    if not check_permission(current_user, ResourceType.FEATURE_FLAG, Action.DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.FEATURE_FLAG, Action.DELETE),
        )
    return True


# Report permissions
async def get_report_by_id(
    report_id: int,
    db: Session = Depends(get_db),
) -> Report:
    """Get a report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id {report_id} not found",
        )
    return report


async def get_report_access(
    report: Report = Depends(get_report_by_id),
    current_user: User = Depends(get_current_user),
) -> Report:
    """Check if user has access to the report."""
    if current_user.is_superuser:
        return report

    # Check if user has permission to read reports
    if not check_permission(current_user, ResourceType.REPORT, Action.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.REPORT, Action.READ),
        )

    # Check ownership for non-admin users for modification actions
    if not check_permission(current_user, ResourceType.REPORT, Action.UPDATE) and not check_ownership(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this report",
        )

    return report


async def can_create_report(
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can create a report."""
    if not check_permission(current_user, ResourceType.REPORT, Action.CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.REPORT, Action.CREATE),
        )
    return True


async def can_update_report(
    report: Report = Depends(get_report_access),
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can update a report."""
    if not check_permission(current_user, ResourceType.REPORT, Action.UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.REPORT, Action.UPDATE),
        )
    return True


async def can_delete_report(
    report: Report = Depends(get_report_access),
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can delete a report."""
    if not check_permission(current_user, ResourceType.REPORT, Action.DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.REPORT, Action.DELETE),
        )
    return True


# Update experiment permissions to use the new permission system
def get_experiment_access(
    experiment: Experiment = Depends(get_experiment_by_key),
    current_user: User = Depends(get_current_user),
) -> Experiment:
    """Check if user has access to the experiment."""
    if current_user.is_superuser:
        return experiment

    # Check if user has permission to read experiments
    if not check_permission(current_user, ResourceType.EXPERIMENT, Action.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.EXPERIMENT, Action.READ),
        )

    # Check ownership for non-admin users for modification actions
    if not check_permission(current_user, ResourceType.EXPERIMENT, Action.UPDATE) and not check_ownership(current_user, experiment):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this experiment",
        )

    return experiment


def can_create_experiment(
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can create an experiment."""
    if not check_permission(current_user, ResourceType.EXPERIMENT, Action.CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.EXPERIMENT, Action.CREATE),
        )
    return True


def can_update_experiment(
    experiment: Union[Experiment, Dict[str, Any]] = Depends(get_experiment_access),
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can update an experiment."""
    if not check_permission(current_user, ResourceType.EXPERIMENT, Action.UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.EXPERIMENT, Action.UPDATE),
        )
    return True


def can_delete_experiment(
    experiment: Union[Experiment, Dict[str, Any]] = Depends(get_experiment_access),
    current_user: User = Depends(get_current_user),
) -> bool:
    """Check if user can delete an experiment."""
    # Check if user has permission to delete experiments
    if not check_permission(current_user, ResourceType.EXPERIMENT, Action.DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_permission_error_message(ResourceType.EXPERIMENT, Action.DELETE),
        )

    # If not a superuser, check ownership
    if not current_user.is_superuser:
        # For Dict objects, check owner_id field
        if isinstance(experiment, dict) and str(experiment.get("owner_id")) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be the owner to delete this experiment",
            )
        # For Experiment objects, check owner_id attribute
        elif hasattr(experiment, "owner_id") and str(experiment.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be the owner to delete this experiment",
            )

    return True
