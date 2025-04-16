"""
Rollout schedule schema models for validation and serialization.

This module defines Pydantic models for rollout schedule-related data structures.
These models are used for request/response validation and documentation.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)


class TriggerType(str, Enum):
    """Types of triggers for rollout schedule stages."""
    TIME_BASED = "time_based"
    METRIC_BASED = "metric_based"
    MANUAL = "manual"


class RolloutStageStatus(str, Enum):
    """Status of a rollout schedule stage."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RolloutScheduleStatus(str, Enum):
    """Status of a rollout schedule."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MetricTrigger(BaseModel):
    """Configuration for a metric-based trigger."""
    metric_name: str = Field(..., description="Name of the metric to track")
    threshold: float = Field(..., description="Threshold value to trigger the stage")
    comparison: str = Field(..., description="Comparison operator (gt, lt, eq, etc.)")
    duration: Optional[int] = Field(None, description="Duration in hours the metric should meet the threshold")


class TimeTrigger(BaseModel):
    """Configuration for a time-based trigger."""
    scheduled_date: datetime = Field(..., description="Date and time for the trigger")
    time_zone: Optional[str] = Field("UTC", description="Time zone for the trigger")


class RolloutStageBase(BaseModel):
    """Base model for rollout stage data."""
    name: str = Field(..., min_length=1, max_length=100, description="Stage name")
    description: Optional[str] = Field(None, description="Stage description")
    stage_order: int = Field(..., ge=0, description="Order of the stage in the schedule")
    target_percentage: int = Field(
        ..., ge=0, le=100, description="Target rollout percentage"
    )
    trigger_type: TriggerType = Field(..., description="Type of trigger for this stage")
    trigger_configuration: Optional[Dict[str, Any]] = Field(
        None, description="Configuration for the trigger"
    )
    start_date: Optional[datetime] = Field(None, description="For time-based triggers")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Initial Rollout",
                "description": "First stage of rollout to 10% of users",
                "stage_order": 1,
                "target_percentage": 10,
                "trigger_type": "time_based",
                "trigger_configuration": {
                    "scheduled_date": "2023-12-01T00:00:00Z",
                    "time_zone": "UTC"
                },
                "start_date": "2023-12-01T00:00:00Z"
            }
        }
    )

    @field_validator("target_percentage")
    @classmethod
    def validate_percentage(cls, v: int) -> int:
        """Validate percentage is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v


class RolloutStageCreate(RolloutStageBase):
    """Model for creating a new rollout stage."""
    pass


class RolloutStageUpdate(BaseModel):
    """Model for updating a rollout stage."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Stage name")
    description: Optional[str] = Field(None, description="Stage description")
    stage_order: Optional[int] = Field(None, ge=0, description="Order of the stage in the schedule")
    target_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="Target rollout percentage"
    )
    trigger_type: Optional[TriggerType] = Field(None, description="Type of trigger for this stage")
    trigger_configuration: Optional[Dict[str, Any]] = Field(
        None, description="Configuration for the trigger"
    )
    start_date: Optional[datetime] = Field(None, description="For time-based triggers")


class RolloutStageResponse(RolloutStageBase):
    """Model for rollout stage response data."""
    id: UUID
    rollout_schedule_id: UUID
    status: RolloutStageStatus
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RolloutScheduleBase(BaseModel):
    """Base model for rollout schedule data."""
    name: str = Field(..., min_length=1, max_length=100, description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    feature_flag_id: UUID = Field(..., description="ID of the feature flag")
    start_date: Optional[datetime] = Field(
        None, description="Date when the schedule should start"
    )
    end_date: Optional[datetime] = Field(
        None, description="Date when the schedule should end"
    )
    config_data: Optional[Dict[str, Any]] = Field(
        None, description="Additional configuration data"
    )
    max_percentage: int = Field(
        100, ge=0, le=100, description="Maximum rollout percentage"
    )
    min_stage_duration: Optional[int] = Field(
        None, description="Minimum time (hours) between stages"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Gradual Rollout",
                "description": "Gradually roll out new feature to users",
                "feature_flag_id": "123e4567-e89b-12d3-a456-426614174000",
                "start_date": "2023-12-01T00:00:00Z",
                "end_date": "2023-12-31T23:59:59Z",
                "config_data": {
                    "owner_email": "product@example.com",
                    "target_user_segment": "beta_users"
                },
                "max_percentage": 100,
                "min_stage_duration": 24
            }
        }
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "RolloutScheduleBase":
        """Validate date relationships."""
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self


class RolloutScheduleCreate(RolloutScheduleBase):
    """Model for creating a new rollout schedule."""
    stages: List[RolloutStageCreate] = Field(
        ..., min_length=1, description="Rollout stages"
    )

    @model_validator(mode="after")
    def validate_stages(self) -> "RolloutScheduleCreate":
        """Validate stages in the schedule."""
        if not self.stages:
            raise ValueError("At least one stage is required")

        # Check that stages have increasing percentages
        stage_percentages = [stage.target_percentage for stage in self.stages]
        if not all(a <= b for a, b in zip(stage_percentages, stage_percentages[1:])):
            raise ValueError("Stage percentages must be non-decreasing")

        # Check that max stage percentage doesn't exceed the schedule max
        if max(stage_percentages) > self.max_percentage:
            raise ValueError(f"Stage percentages cannot exceed the maximum of {self.max_percentage}%")

        # Check that stage orders are correct
        stage_orders = [stage.stage_order for stage in self.stages]
        if sorted(stage_orders) != list(range(min(stage_orders), max(stage_orders) + 1)):
            raise ValueError("Stage orders must be sequential without gaps")

        return self


class RolloutScheduleUpdate(BaseModel):
    """Model for updating a rollout schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    start_date: Optional[datetime] = Field(
        None, description="Date when the schedule should start"
    )
    end_date: Optional[datetime] = Field(
        None, description="Date when the schedule should end"
    )
    config_data: Optional[Dict[str, Any]] = Field(
        None, description="Additional configuration data"
    )
    max_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="Maximum rollout percentage"
    )
    min_stage_duration: Optional[int] = Field(
        None, description="Minimum time (hours) between stages"
    )
    status: Optional[RolloutScheduleStatus] = Field(
        None, description="Status of the schedule"
    )
    stages: Optional[List[RolloutStageUpdate]] = Field(
        None, description="Updated rollout stages"
    )


class RolloutScheduleResponse(RolloutScheduleBase):
    """Model for rollout schedule response data."""
    id: UUID
    owner_id: Optional[UUID]
    status: RolloutScheduleStatus
    stages: List[RolloutStageResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RolloutScheduleListResponse(BaseModel):
    """Paginated response model for rollout schedules."""
    items: List[RolloutScheduleResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Gradual Rollout",
                        "description": "Gradually roll out new feature to users",
                        "feature_flag_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "active",
                        "start_date": "2023-12-01T00:00:00Z",
                        "end_date": "2023-12-31T23:59:59Z",
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
