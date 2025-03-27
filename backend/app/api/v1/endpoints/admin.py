"""
Admin API endpoints.

This module provides API endpoints for administrative operations
that require superuser privileges.
"""

from typing import List, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session

from backend.app.api import deps
from backend.app.models.user import User
from backend.app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)

router = APIRouter()


@router.get("/users", response_model=UserListResponse)
async def list_users(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> Any:
    """
    List all users.

    This endpoint is only accessible by superusers and returns a list of all users
    in the system with pagination.
    """
    # Query all users with pagination
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()

    return UserListResponse(items=users, total=total, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID = Path(..., description="The ID of the user to retrieve"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Get user details.

    This endpoint is only accessible by superusers and returns details
    of a specific user by ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_in: UserUpdate,
    user_id: uuid.UUID = Path(..., description="The ID of the user to update"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Update user.

    This endpoint is only accessible by superusers and allows updating
    user details, including superuser status.
    """
    # Get the user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update user attributes
    update_data = user_in.dict(exclude_unset=True)
    for field in update_data:
        if hasattr(user, field):
            setattr(user, field, update_data[field])

    db.commit()
    db.refresh(user)

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID = Path(..., description="The ID of the user to delete"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> None:
    """
    Delete user.

    This endpoint is only accessible by superusers and allows deleting users.
    It prevents superusers from deleting themselves.
    """
    # Get the user to delete
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent superusers from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own user account",
        )

    # Delete the user
    db.delete(user)
    db.commit()


@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> Any:
    """
    Get system statistics.

    This endpoint is only accessible by superusers and provides
    system-wide statistics like user counts, experiment counts, etc.
    """
    # Try to get from cache if enabled
    if cache_control["enabled"]:
        cache_key = "admin:system_stats"
        cached_data = cache_control["client"].get(cache_key)
        if cached_data:
            return json.loads(cached_data)

    # Count various entities
    from backend.app.models.experiment import Experiment, ExperimentStatus
    from backend.app.models.event import Event
    from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus

    user_count = db.query(User).count()
    active_user_count = db.query(User).filter(User.is_active == True).count()
    superuser_count = db.query(User).filter(User.is_superuser == True).count()

    experiment_count = db.query(Experiment).count()
    active_experiment_count = (
        db.query(Experiment)
        .filter(Experiment.status == ExperimentStatus.ACTIVE)
        .count()
    )

    event_count = db.query(Event).count()

    feature_flag_count = db.query(FeatureFlag).count()
    active_feature_flag_count = (
        db.query(FeatureFlag)
        .filter(FeatureFlag.status == FeatureFlagStatus.ACTIVE)
        .count()
    )

    # Calculate daily event rate (simplified)
    import datetime

    yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    daily_events = (
        db.query(Event).filter(Event.created_at >= yesterday.isoformat()).count()
    )

    # Compile stats
    stats = {
        "users": {
            "total": user_count,
            "active": active_user_count,
            "superusers": superuser_count,
        },
        "experiments": {"total": experiment_count, "active": active_experiment_count},
        "events": {"total": event_count, "daily_rate": daily_events},
        "feature_flags": {
            "total": feature_flag_count,
            "active": active_feature_flag_count,
        },
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }

    # Cache stats if enabled
    if cache_control["enabled"]:
        cache_control["client"].setex(
            cache_key, 60 * 5, json.dumps(stats)  # 5 minute TTL for stats
        )

    return stats


@router.post("/cache/clear", status_code=status.HTTP_200_OK)
async def clear_cache(
    current_user: User = Depends(deps.get_current_superuser),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> Dict[str, Any]:
    """
    Clear system cache.

    This endpoint is only accessible by superusers and clears all Redis cache entries
    for the application.
    """
    if not cache_control["enabled"]:
        return {"message": "Caching is not enabled"}

    # Clear all keys with the application prefix
    pattern = f"{settings.REDIS_PREFIX}:*"
    keys_deleted = 0

    for key in cache_control["client"].scan_iter(match=pattern):
        cache_control["client"].delete(key)
        keys_deleted += 1

    return {"message": "Cache cleared successfully", "keys_deleted": keys_deleted}
