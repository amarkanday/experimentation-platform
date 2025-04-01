from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import json
from backend.app.api import deps
from backend.app.models.user import User
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.schemas.feature_flag import (
    FeatureFlagCreate,
    FeatureFlagUpdate,
    FeatureFlagInDB,
)
from backend.app.services.feature_flag_service import FeatureFlagService

router = APIRouter()


@router.post("/", response_model=FeatureFlagInDB, status_code=status.HTTP_201_CREATED)
def create_feature_flag(
    flag_in: FeatureFlagCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new feature flag.
    """
    # Check if feature flag with this key already exists
    existing_flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_in.key).first()
    if existing_flag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feature flag with key '{flag_in.key}' already exists",
        )

    flag_service = FeatureFlagService(db)
    try:
        return flag_service.create_feature_flag(flag_in, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=List[FeatureFlagInDB])
def list_feature_flags(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
):
    """
    List all feature flags with optional status filter.
    """
    flag_service = FeatureFlagService(db)
    return flag_service.get_feature_flags(skip=skip, limit=limit, status=status_filter)


@router.get("/{flag_id}", response_model=FeatureFlagInDB)
def get_feature_flag(
    flag_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a specific feature flag by ID.
    """
    flag_service = FeatureFlagService(db)
    flag = flag_service.get_feature_flag(flag_id)

    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature flag not found",
        )

    return flag


@router.put("/{flag_id}", response_model=FeatureFlagInDB)
def update_feature_flag(
    flag_id: str,
    flag_in: FeatureFlagUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update a feature flag.
    """
    # First get the existing flag
    flag = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found"
        )

    # Check for key uniqueness if key is being updated
    if flag_in.key and flag_in.key != flag.key:
        existing_flag = (
            db.query(FeatureFlag)
            .filter(
                FeatureFlag.key == flag_in.key,
                FeatureFlag.id != flag_id,  # Exclude the current flag
            )
            .first()
        )
        if existing_flag:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Feature flag with key '{flag_in.key}' already exists",
            )

    # Proceed with the update
    flag_service = FeatureFlagService(db)
    updated_flag = flag_service.update_feature_flag(flag, flag_in)

    return updated_flag


@router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feature_flag(
    flag_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete a feature flag.
    """
    flag = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature flag not found",
        )

    flag_service = FeatureFlagService(db)
    flag_service.delete_feature_flag(flag)

    return None


@router.post("/{flag_id}/activate", response_model=FeatureFlagInDB)
def activate_feature_flag(
    flag_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Activate a feature flag.
    """
    flag = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature flag not found",
        )

    flag_service = FeatureFlagService(db)
    return flag_service.activate_feature_flag(flag)


@router.post("/{flag_id}/deactivate", response_model=FeatureFlagInDB)
def deactivate_feature_flag(
    flag_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Deactivate a feature flag.
    """
    flag = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature flag not found",
        )

    flag_service = FeatureFlagService(db)
    return flag_service.deactivate_feature_flag(flag)


@router.get("/evaluate/{flag_key}")
def evaluate_feature_flag(
    flag_key: str,
    user_id: str,
    db: Session = Depends(deps.get_db),
    context_json: Optional[str] = Query(
        None, description="JSON string of context data"
    ),
):
    """
    Evaluate a feature flag for a specific user.

    Args:
        flag_key: Key of the feature flag to evaluate
        user_id: ID of the user
        db: Database session
        context_json: Optional JSON string containing context data
    """
    # Parse context from JSON string if provided
    context = None
    if context_json:
        try:
            context = json.loads(context_json)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid context JSON format",
            )

    # Get the feature flag
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature flag not found",
        )

    # Evaluate the flag
    flag_service = FeatureFlagService(db)
    is_enabled = flag_service.evaluate_flag(flag, user_id, context)

    return {"enabled": is_enabled}


@router.get("/user/{user_id}")
def get_user_flags(
    user_id: str,
    db: Session = Depends(deps.get_db),
    context_json: Optional[str] = Query(
        None, description="JSON string of context data"
    ),
):
    """
    Get all feature flags evaluated for a specific user.

    Args:
        user_id: ID of the user
        db: Database session
        context_json: Optional JSON string containing context data
    """
    # Parse context from JSON string if provided
    context = None
    if context_json:
        try:
            context = json.loads(context_json)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid context JSON format",
            )

    flag_service = FeatureFlagService(db)
    return flag_service.get_user_flags(user_id, context)
