# backend/app/schemas/feature_flag.py
"""
Feature flag schemas.

This module contains Pydantic models for feature flag data validation.
"""
import re
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class FeatureFlagStatus(str, Enum):
    """Feature flag status enum."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class FeatureFlagBase(BaseModel):
    """Base feature flag schema."""

    key: str = Field(..., description="Unique key for the feature flag")
    name: str = Field(..., description="Display name for the feature flag")
    description: Optional[str] = Field(
        None, description="Description of the feature flag"
    )
    status: Optional[FeatureFlagStatus] = Field(
        FeatureFlagStatus.INACTIVE, description="Status of the feature flag"
    )
    rollout_percentage: int = Field(
        0, description="Percentage of users to enable the flag for", ge=0, le=100
    )
    targeting_rules: Optional[Dict[str, Any]] = Field(
        None, description="Rules for targeting users"
    )
    value: Optional[Dict[str, Any]] = Field(
        None, description="Default value configuration for the feature flag"
    )

    @validator("key")
    def validate_key(cls, v):
        """Validate feature flag key format."""
        if not v.islower():
            raise ValueError("Key must be lowercase")
        if not re.match(r"^[a-z0-9_\-]+$", v):
            raise ValueError(
                "Key must be lowercase alphanumeric characters, hyphens, or underscores"
            )
        return v

    class Config:
        """Pydantic model configuration."""

        schema_extra = {
            "example": {
                "key": "new-checkout-flow",
                "name": "New Checkout Flow",
                "description": "Enables the new checkout experience for users",
                "status": "inactive",
                "rollout_percentage": 10,
                "targeting_rules": {"country": ["US", "CA"], "user_group": "beta"},
                "value": {
                    "variants": {
                        "control": {"value": False},
                        "treatment": {"value": True},
                    },
                    "default": "control",
                },
            }
        }


class FeatureFlagCreate(FeatureFlagBase):
    """Feature flag creation schema."""

    pass


class FeatureFlagUpdate(FeatureFlagBase):
    """Feature flag update schema."""

    key: Optional[str] = None
    name: Optional[str] = None


class FeatureFlagInDB(FeatureFlagBase):
    """Feature flag database schema."""

    id: str
    owner_id: str
    created_at: str
    updated_at: str

    class Config:
        """Pydantic model configuration."""

        orm_mode = True
