from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.api import deps
from backend.app.models.user import User
from backend.app.models.api_key import APIKey

router = APIRouter()


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    scopes: Optional[str] = None
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """Schema for API key response."""

    id: str
    key: str
    name: str
    description: Optional[str] = None
    scopes: Optional[str] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class APIKeyList(BaseModel):
    """Schema for API key list response (without full key)."""

    id: str
    name: str
    description: Optional[str] = None
    scopes: Optional[str] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


@router.post("/", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_in: APIKeyCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new API key for the current user.

    This endpoint allows users to create personal API keys for programmatic access
    to the API.
    """
    # Calculate expiration date if specified
    expires_at = None
    if api_key_in.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_in.expires_in_days)

    # Create the API key
    api_key = APIKey.create_for_user(
        db_session=db,
        user_id=current_user.id,
        name=api_key_in.name,
        description=api_key_in.description,
        scopes=api_key_in.scopes,
        expires_at=expires_at,
    )

    return api_key


@router.get("/", response_model=List[APIKeyList])
def list_api_keys(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    List all API keys for the current user.

    Note that the full API key is not returned for security reasons.
    """
    api_keys = (
        db.query(APIKey)
        .filter(APIKey.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return api_keys


@router.get("/{api_key_id}", response_model=APIKeyList)
def get_api_key(
    api_key_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a specific API key by ID.

    Note that the full API key is not returned for security reasons.
    """
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == api_key_id, APIKey.user_id == current_user.id)
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return api_key


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    api_key_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete an API key.

    This permanently revokes the API key.
    """
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == api_key_id, APIKey.user_id == current_user.id)
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    db.delete(api_key)
    db.commit()

    return None
