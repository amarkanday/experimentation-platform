"""
Tracking schema models for validation and serialization.

This module defines Pydantic models for tracking-related data structures.
These models are used for experiment assignment and event tracking.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator, root_validator, UUID4, constr


class AssignmentRequest(BaseModel):
    """Model for requesting a variant assignment."""

    experiment_key: str = Field(..., min_length=1, description="Experiment identifier")
    user_id: str = Field(..., min_length=1, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(
        None, description="User context for targeting"
    )

    class Config:
        schema_extra = {
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


class AssignmentResponse(BaseModel):
    """Model for variant assignment response."""

    experiment_key: str = Field(..., description="Experiment identifier")
    variant_name: str = Field(..., description="Assigned variant name")
    is_control: bool = Field(
        ..., description="Whether the assigned variant is the control"
    )
    configuration: Optional[Dict[str, Any]] = Field(
        None, description="Variant configuration"
    )

    class Config:
        schema_extra = {
            "example": {
                "experiment_key": "button-color-test",
                "variant_name": "blue-button",
                "is_control": False,
                "configuration": {"button_color": "blue", "button_text": "Buy Now"},
            }
        }


class EventCreate(BaseModel):
    """Model for creating an event."""

    user_id: str = Field(..., min_length=1, description="User identifier")
    event_type: str = Field(..., min_length=1, description="Type of event")
    event_name: Optional[str] = Field(None, description="Name of the event")
    experiment_id: Optional[str] = Field(None, description="Experiment identifier")
    feature_flag_id: Optional[str] = Field(None, description="Feature flag identifier")
    variant_id: Optional[str] = Field(None, description="Variant identifier")
    value: Optional[float] = Field(None, description="Numeric value for the event")
    properties: Optional[Dict[str, Any]] = Field(
        None, description="Additional event data"
    )
    timestamp: Optional[str] = Field(None, description="Event timestamp")


class EventRequest(BaseModel):
    """Model for tracking an event."""

    event_type: str = Field(..., min_length=1, description="Type of event")
    user_id: str = Field(..., min_length=1, description="User identifier")
    experiment_key: Optional[str] = Field(None, description="Experiment identifier")
    feature_flag_key: Optional[str] = Field(None, description="Feature flag identifier")
    value: Optional[float] = Field(None, description="Numeric value for the event")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional event data"
    )
    timestamp: Optional[str] = Field(None, description="Event timestamp")

    class Config:
        schema_extra = {
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

    @root_validator
    def validate_experiment_or_feature_flag(cls, values):
        """Validate that at least one of experiment_key or feature_flag_key is provided."""
        experiment_key = values.get("experiment_key")
        feature_flag_key = values.get("feature_flag_key")

        if experiment_key is None and feature_flag_key is None:
            raise ValueError(
                "Either experiment_key or feature_flag_key must be provided"
            )

        return values


class EventResponse(BaseModel):
    """Model for event tracking response."""

    success: bool = Field(..., description="Whether the event was successfully tracked")
    event_id: Optional[str] = Field(None, description="Event identifier")
    message: Optional[str] = Field(None, description="Additional information")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "event_id": "evt-123456789",
                "message": "Event successfully tracked",
            }
        }


class EventBatchRequest(BaseModel):
    """Model for batch tracking multiple events."""

    events: List[EventRequest] = Field(
        ..., min_items=1, max_items=100, description="List of events to track"
    )

    class Config:
        schema_extra = {
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


class EventBatchResponse(BaseModel):
    """Model for batch event tracking response."""

    success_count: int = Field(..., description="Number of events successfully tracked")
    failure_count: int = Field(..., description="Number of events that failed to track")
    errors: Optional[List[Dict[str, Any]]] = Field(
        None, description="Details of failed events"
    )

    class Config:
        schema_extra = {
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


class EventQueryParams(BaseModel):
    """Model for querying events."""

    experiment_id: Optional[UUID4] = Field(None, description="Filter by experiment ID")
    feature_flag_id: Optional[UUID4] = Field(
        None, description="Filter by feature flag ID"
    )
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    start_date: Optional[datetime] = Field(
        None, description="Filter events after this date"
    )
    end_date: Optional[datetime] = Field(
        None, description="Filter events before this date"
    )
    limit: int = Field(
        100, ge=1, le=1000, description="Maximum number of events to return"
    )
    offset: int = Field(0, ge=0, description="Number of events to skip")

    class Config:
        schema_extra = {
            "example": {
                "experiment_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "purchase",
                "start_date": "2023-01-01T00:00:00Z",
                "end_date": "2023-01-31T23:59:59Z",
                "limit": 100,
                "offset": 0,
            }
        }

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        start_date = values.get("start_date")
        if start_date and v and v < start_date:
            raise ValueError("end_date must be after start_date")
        return v
