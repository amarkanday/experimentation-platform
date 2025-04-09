"""
Tracking schema models for validation and serialization.

This module defines Pydantic models for tracking-related data structures.
These models are used for experiment assignment and event tracking.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, UUID4


class EventBase(BaseModel):
    """Base model for event data."""
    event_name: str = Field(..., min_length=1, max_length=100)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    experiment_id: Optional[str] = None
    feature_flag_id: Optional[str] = None
    variant_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_experiment_or_feature_flag(self) -> "EventBase":
        """Validate that either experiment_id or feature_flag_id is provided."""
        if not self.experiment_id and not self.feature_flag_id:
            raise ValueError("Either experiment_id or feature_flag_id must be provided")
        return self


class EventCreate(EventBase):
    """Model for creating a new event."""
    pass


class EventResponse(EventBase):
    """Model for event responses."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentBase(BaseModel):
    """Base model for assignment data."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    experiment_id: Optional[str] = None
    feature_flag_id: Optional[str] = None
    variant_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_experiment_or_feature_flag(self) -> "AssignmentBase":
        """Validate that either experiment_id or feature_flag_id is provided."""
        if not self.experiment_id and not self.feature_flag_id:
            raise ValueError("Either experiment_id or feature_flag_id must be provided")
        return self


class AssignmentCreate(AssignmentBase):
    """Model for creating a new assignment."""
    pass


class AssignmentResponse(AssignmentBase):
    """Model for assignment responses."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentMetrics(BaseModel):
    """Model for experiment metrics."""
    experiment_id: str
    start_date: datetime
    end_date: datetime
    metrics: List[str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime, values: Dict[str, Any]) -> datetime:
        """Validate that end_date is after start_date."""
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class MetricResult(BaseModel):
    """Model for metric results."""
    metric_name: str
    variant_id: str
    value: float
    confidence_interval: Optional[List[float]] = None
    p_value: Optional[float] = None
    sample_size: int

    model_config = ConfigDict(from_attributes=True)


class ExperimentResults(BaseModel):
    """Model for experiment results."""
    experiment_id: str
    start_date: datetime
    end_date: datetime
    metrics: List[MetricResult]

    model_config = ConfigDict(from_attributes=True)


class AssignmentRequest(BaseModel):
    """Model for requesting a variant assignment."""
    experiment_key: str = Field(..., min_length=1, description="Experiment identifier")
    user_id: str = Field(..., min_length=1, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="User context for targeting")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_key": "button-color-test",
                "user_id": "user-123",
                "context": {
                    "country": "US",
                    "device": "mobile",
                    "browser": "chrome",
                    "is_returning": True,
                },
            }
        }
    )


class EventRequest(BaseModel):
    """Model for tracking an event."""
    experiment_id: Optional[UUID4] = None
    feature_flag_id: Optional[UUID4] = None
    event_type: str
    event_data: Optional[Dict] = None
    timestamp: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_experiment_or_feature_flag(cls, values):
        experiment_id = values.experiment_id
        feature_flag_id = values.feature_flag_id

        if experiment_id is None and feature_flag_id is None:
            raise ValueError("Either experiment_id or feature_flag_id must be provided")
        if experiment_id is not None and feature_flag_id is not None:
            raise ValueError("Only one of experiment_id or feature_flag_id should be provided")
        return values

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "purchase",
                "user_id": "user-123",
                "experiment_key": "button-color-test",
                "value": 49.99,
                "metadata": {
                    "product_id": "prod-456",
                    "category": "electronics",
                    "currency": "USD",
                },
            }
        }
    )


class EventBatchRequest(BaseModel):
    """Model for batch tracking multiple events."""
    events: List[EventRequest] = Field(
        ..., min_length=1, max_length=100, description="List of events to track"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "events": [
                    {
                        "event_type": "page_view",
                        "user_id": "user-123",
                        "experiment_key": "button-color-test",
                        "metadata": {
                            "page": "/product/456",
                            "referrer": "/category/electronics",
                        },
                    },
                    {
                        "event_type": "add_to_cart",
                        "user_id": "user-123",
                        "experiment_key": "button-color-test",
                        "value": 49.99,
                        "metadata": {"product_id": "prod-456", "quantity": 1},
                    },
                ]
            }
        }
    )


class EventBatchResponse(BaseModel):
    """Model for batch event tracking response."""
    success_count: int = Field(..., description="Number of events successfully tracked")
    failure_count: int = Field(..., description="Number of events that failed to track")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Details of failed events")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success_count": 1,
                "failure_count": 1,
                "errors": [
                    {
                        "index": 1,
                        "event_type": "add_to_cart",
                        "user_id": "user-123",
                        "error": "Invalid experiment key",
                    }
                ],
            }
        }
    )


class EventQueryParams(BaseModel):
    """Model for querying events."""
    experiment_id: Optional[UUID4] = Field(None, description="Filter by experiment ID")
    feature_flag_id: Optional[UUID4] = Field(None, description="Filter by feature flag ID")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    start_date: Optional[datetime] = Field(None, description="Filter events after this date")
    end_date: Optional[datetime] = Field(None, description="Filter events before this date")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of events to return")
    offset: int = Field(0, ge=0, description="Number of events to skip")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "purchase",
                "start_date": "2023-01-01T00:00:00Z",
                "end_date": "2023-01-31T23:59:59Z",
                "limit": 100,
                "offset": 0,
            }
        }
    )

    @field_validator("end_date")
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        start_date = values.get("start_date")
        if start_date and v and v < start_date:
            raise ValueError("end_date must be after start_date")
        return v
