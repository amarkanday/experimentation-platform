"""
Shared data models for Lambda functions.

Provides Pydantic models for type safety and validation across all Lambda functions.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class ExperimentStatus(str, Enum):
    """Experiment status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Assignment(BaseModel):
    """
    Experiment assignment model.

    Represents a user's assignment to an experiment variant.
    """
    assignment_id: str = Field(..., description="Unique assignment identifier")
    user_id: str = Field(..., description="User identifier")
    experiment_id: str = Field(..., description="Experiment identifier")
    experiment_key: str = Field(..., description="Experiment key")
    variant: str = Field(..., description="Assigned variant key")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Assignment timestamp")
    context: Optional[Dict[str, Any]] = Field(default=None, description="User context at assignment")

    class Config:
        json_schema_extra = {
            "example": {
                "assignment_id": "assign_123",
                "user_id": "user_456",
                "experiment_id": "exp_789",
                "experiment_key": "checkout_redesign",
                "variant": "treatment",
                "timestamp": "2025-12-18T10:30:00Z",
                "context": {"country": "US", "platform": "web"}
            }
        }


class VariantConfig(BaseModel):
    """
    Variant configuration model.

    Represents a single variant in an experiment.
    """
    key: str = Field(..., description="Variant key")
    allocation: float = Field(..., ge=0.0, le=1.0, description="Traffic allocation (0.0-1.0)")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Variant configuration payload")


class ExperimentConfig(BaseModel):
    """
    Experiment configuration model.

    Contains all configuration needed for assignment logic.
    """
    experiment_id: str = Field(..., description="Unique experiment identifier")
    key: str = Field(..., description="Experiment key")
    status: ExperimentStatus = Field(..., description="Current status")
    variants: List[VariantConfig] = Field(..., min_length=2, description="List of variants")
    traffic_allocation: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall traffic allocation")
    targeting_rules: Optional[List[Dict[str, Any]]] = Field(default=None, description="Targeting rules")
    salt: Optional[str] = Field(default=None, description="Salt for hashing")

    @validator('variants')
    def validate_variant_allocations(cls, v):
        """Validate that variant allocations sum to ~1.0."""
        total = sum(variant.allocation for variant in v)
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Variant allocations must sum to 1.0, got {total}")
        return v

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "experiment_id": "exp_123",
                "key": "checkout_redesign",
                "status": "active",
                "variants": [
                    {"key": "control", "allocation": 0.5},
                    {"key": "treatment", "allocation": 0.5}
                ],
                "traffic_allocation": 1.0,
                "targeting_rules": [],
                "salt": None
            }
        }


class FeatureFlagConfig(BaseModel):
    """
    Feature flag configuration model.

    Contains all configuration needed for feature flag evaluation.
    """
    flag_id: str = Field(..., description="Unique flag identifier")
    key: str = Field(..., description="Flag key")
    enabled: bool = Field(default=False, description="Global enabled state")
    rollout_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Rollout percentage (0-100)")
    targeting_rules: Optional[List[Dict[str, Any]]] = Field(default=None, description="Targeting rules")
    default_variant: Optional[str] = Field(default=None, description="Default variant key")
    variants: Optional[List[VariantConfig]] = Field(default=None, description="List of variants")

    class Config:
        json_schema_extra = {
            "example": {
                "flag_id": "flag_123",
                "key": "new_checkout",
                "enabled": True,
                "rollout_percentage": 50.0,
                "targeting_rules": [],
                "default_variant": None,
                "variants": None
            }
        }


class EventData(BaseModel):
    """
    Event data model.

    Represents an incoming event from client applications.
    """
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type (e.g., 'conversion', 'page_view')")
    user_id: str = Field(..., description="User identifier")
    experiment_id: Optional[str] = Field(default=None, description="Associated experiment ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Event properties")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Event metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_123",
                "event_type": "conversion",
                "user_id": "user_456",
                "experiment_id": "exp_789",
                "timestamp": "2025-12-18T10:30:00Z",
                "properties": {"revenue": 99.99, "item_count": 3},
                "metadata": {"source": "mobile_app", "version": "1.2.3"}
            }
        }


class LambdaResponse(BaseModel):
    """
    Standard Lambda response model.

    Provides consistent response structure across all Lambda functions.
    """
    statusCode: int = Field(..., description="HTTP status code")
    body: Dict[str, Any] = Field(..., description="Response body")
    headers: Optional[Dict[str, str]] = Field(
        default={"Content-Type": "application/json"},
        description="Response headers"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "statusCode": 200,
                "body": {"variant": "treatment", "experiment_id": "exp_123"},
                "headers": {"Content-Type": "application/json"}
            }
        }
