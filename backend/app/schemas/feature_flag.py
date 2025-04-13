# backend/app/schemas/feature_flag.py
"""
Feature flag schema models for validation and serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class FeatureFlagBase(BaseModel):
    """Base model for feature flag data."""
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)
    targeting_rules: Optional[Dict[str, Any]] = None
    default_value: Any = False
    tags: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate feature flag key format."""
        if v != v.lower():
            raise ValueError("Key must be lowercase")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Key must be lowercase alphanumeric characters, hyphens, or underscores")
        return v


class FeatureFlagCreate(FeatureFlagBase):
    """Model for creating a new feature flag."""
    pass


class FeatureFlagUpdate(FeatureFlagBase):
    """Model for updating a feature flag."""
    key: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    default_value: Optional[Any] = None


class FeatureFlagInDBBase(FeatureFlagBase):
    """Base model for feature flags in DB."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureFlag(FeatureFlagInDBBase):
    """Feature flag model for responses."""
    pass


class FeatureFlagInDB(FeatureFlagInDBBase):
    """Feature flag model with additional DB fields."""
    pass


class FeatureFlagEvaluation(BaseModel):
    """Model for feature flag evaluation results."""
    key: str
    value: Any
    reason: str
    rule_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class FeatureFlagReadExtended(FeatureFlagInDBBase):
    """
    Extended feature flag read model with additional information.
    Used for detailed feature flag reads.
    """
    owner_id: Optional[int] = None
    metrics: Optional[List[Dict[str, Any]]] = None
    variants: Optional[List[Dict[str, Any]]] = None
    last_evaluated: Optional[datetime] = None


class FeatureFlagListResponse(BaseModel):
    """
    Paginated response model for feature flags.
    """
    items: List[FeatureFlagReadExtended]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "key": "new_feature",
                        "name": "New Feature Flag",
                        "description": "Controls access to new feature",
                        "is_active": True,
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100
            }
        },
        from_attributes=True
    )
