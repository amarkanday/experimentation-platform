# Feature flag Pydantic schemas
"""
Feature flag schema models for validation and serialization.

This module defines Pydantic models for feature flag-related data structures.
These models are used for request/response validation and documentation.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator, UUID4, EmailStr


class FeatureFlagStatus(str, Enum):
    """Feature flag status enum."""

    INACTIVE = "inactive"
    ACTIVE = "active"


class FeatureFlagBase(BaseModel):
    """Base model for feature flag data."""

    key: str = Field(
        ...,
        min_length=1,
        max_length=100,
        regex="^[a-z0-9_-]+$",
        description="Unique feature flag key (slug format)",
    )
    name: str = Field(
        ..., min_length=1, max_length=100, description="Feature flag name"
    )
    description: Optional[str] = Field(None, description="Feature flag description")
    targeting_rules: Optional[Dict[str, Any]] = Field(
        None, description="Rules for flag enablement"
    )
    rollout_percentage: int = Field(
        0, ge=0, le=100, description="Gradual rollout percentage"
    )
    variants: Optional[Dict[str, Any]] = Field(
        None, description="Variant configurations for multivariate flags"
    )
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")

    class Config:
        schema_extra = {
            "example": {
                "key": "new-checkout-flow",
                "name": "New Checkout Flow",
                "description": "Enable the new streamlined checkout flow",
                "targeting_rules": {
                    "country": ["US", "CA"],
                    "user_segment": "beta_testers",
                },
                "rollout_percentage": 20,
                "variants": {"control": {"value": false}, "treatment": {"value": true}},
                "tags": ["checkout", "beta"],
            }
        }

    @validator("key")
    def validate_key(cls, v):
        """Validate feature flag key format."""
        if not v or not v.islower() or not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError(
                "Key must be lowercase alphanumeric characters, hyphens, or underscores"
            )
        return v


class FeatureFlagCreate(FeatureFlagBase):
    """Model for creating a new feature flag."""

    status: FeatureFlagStatus = Field(
        FeatureFlagStatus.INACTIVE, description="Initial feature flag status"
    )

    class Config:
        schema_extra = {
            "example": {
                "key": "new-checkout-flow",
                "name": "New Checkout Flow",
                "description": "Enable the new streamlined checkout flow",
                "status": "inactive",
                "targeting_rules": {
                    "country": ["US", "CA"],
                    "user_segment": "beta_testers",
                },
                "rollout_percentage": 20,
                "variants": {"control": {"value": false}, "treatment": {"value": true}},
                "tags": ["checkout", "beta"],
            }
        }


class FeatureFlagUpdate(BaseModel):
    """Model for updating a feature flag."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Feature flag name"
    )
    description: Optional[str] = Field(None, description="Feature flag description")
    status: Optional[FeatureFlagStatus] = Field(None, description="Feature flag status")
    targeting_rules: Optional[Dict[str, Any]] = Field(
        None, description="Rules for flag enablement"
    )
    rollout_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="Gradual rollout percentage"
    )
    variants: Optional[Dict[str, Any]] = Field(
        None, description="Variant configurations for multivariate flags"
    )
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")

    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Checkout Flow",
                "description": "Enable the new streamlined checkout flow with updates",
                "status": "active",
                "rollout_percentage": 50,
                "tags": ["checkout", "beta", "updated"],
            }
        }


class FeatureFlagOverrideBase(BaseModel):
    """Base model for feature flag override data."""

    user_id: str = Field(..., min_length=1, description="User identifier")
    value: Any = Field(..., description="Override value")
    reason: Optional[str] = Field(None, description="Reason for override")
    expires_at: Optional[datetime] = Field(
        None, description="Expiration date for override"
    )

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-123",
                "value": True,
                "reason": "Testing new feature",
                "expires_at": "2023-12-31T23:59:59Z",
            }
        }


class FeatureFlagOverrideCreate(FeatureFlagOverrideBase):
    """Model for creating a new feature flag override."""

    pass


class FeatureFlagOverrideUpdate(BaseModel):
    """Model for updating a feature flag override."""

    value: Optional[Any] = Field(None, description="Override value")
    reason: Optional[str] = Field(None, description="Reason for override")
    expires_at: Optional[datetime] = Field(
        None, description="Expiration date for override"
    )

    class Config:
        schema_extra = {
            "example": {
                "value": False,
                "reason": "Disabling feature due to issues",
                "expires_at": "2023-06-30T23:59:59Z",
            }
        }


class FeatureFlagOverrideInDB(FeatureFlagOverrideBase):
    """Model for feature flag override as stored in the database."""

    id: UUID4
    feature_flag_id: UUID4
    created_at: datetime
    updated_at: datetime


class FeatureFlagInDB(FeatureFlagBase):
    """Model for feature flag as stored in the database."""

    id: UUID4
    status: FeatureFlagStatus
    owner_id: UUID4
    created_at: datetime
    updated_at: datetime


class FeatureFlagOverrideResponse(FeatureFlagOverrideInDB):
    """Model for feature flag override response data."""

    pass


class FeatureFlagResponse(FeatureFlagInDB):
    """Model for feature flag response data."""

    overrides: Optional[List[FeatureFlagOverrideResponse]] = None


class FeatureFlagListResponse(BaseModel):
    """Model for paginated feature flag list response."""

    items: List[FeatureFlagResponse]
    total: int
    skip: int
    limit: int


class FeatureFlagEvaluationRequest(BaseModel):
    """Model for evaluating feature flags for a user."""

    user_id: str = Field(..., min_length=1, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(
        None, description="User context for targeting"
    )
    keys: Optional[List[str]] = Field(
        None, description="Specific feature flag keys to evaluate"
    )

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-123",
                "context": {
                    "country": "US",
                    "device": "mobile",
                    "is_beta_tester": True,
                },
                "keys": ["new-checkout-flow", "dark-mode"],
            }
        }


class FeatureFlagEvaluationResponse(BaseModel):
    """Model for feature flag evaluation response."""

    flags: Dict[str, Any] = Field(..., description="Evaluated feature flags")
    reason_map: Optional[Dict[str, str]] = Field(
        None, description="Reasons for evaluation decisions"
    )

    class Config:
        schema_extra = {
            "example": {
                "flags": {"new-checkout-flow": True, "dark-mode": False},
                "reason_map": {
                    "new-checkout-flow": "targeting_rule_match",
                    "dark-mode": "rollout_percentage",
                },
            }
        }
