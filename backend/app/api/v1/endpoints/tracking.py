"""
Tracking API endpoints.

This module provides API endpoints for experiment user assignment and event tracking.
These endpoints are designed to be called from client applications to participate
in experiments and record user interactions.
"""

from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session

from backend.app.api import deps
from backend.app.models.experiment import Experiment
from backend.app.models.assignment import Assignment
from backend.app.models.event import Event
from backend.app.schemas.tracking import (
    AssignmentRequest,
    AssignmentResponse,
    EventRequest,
    EventResponse,
    EventBatchRequest,
    EventBatchResponse,
)

# Create router with tag for documentation grouping
router = APIRouter(
    prefix="/tracking",
    tags=["Tracking"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid API key",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"status_code": 401, "message": "Invalid API key"}
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Experiment not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 404,
                            "message": "Experiment not found or not active",
                        }
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 500,
                            "message": "Internal server error",
                        }
                    }
                }
            },
        },
    },
)


@router.post(
    "/assign",
    response_model=AssignmentResponse,
    summary="Assign user to experiment variant",
    response_description="Returns the variant assignment for the user",
)
async def assign_user_to_experiment(
    request: AssignmentRequest = Body(..., description="Assignment request data"),
    experiment: Experiment = Depends(deps.get_experiment_by_key),
    api_key_info: Dict[str, Any] = Depends(deps.get_api_key),
    db: Session = Depends(deps.get_db),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> AssignmentResponse:
    """
    Assign a user to an experiment variant.

    This endpoint assigns a user to a variant of the specified experiment.
    It handles consistent assignment for returning users.

    The assignment is deterministic based on:
    - User ID
    - Experiment ID
    - Targeting rules
    - Traffic allocation percentages

    This means that the same user will always get the same variant assignment
    for a specific experiment, ensuring a consistent user experience.

    **Authentication**: Requires a valid API key in the X-API-Key header.

    Returns:
        AssignmentResponse: The variant assignment with configuration details

    Raises:
        HTTPException 401: If the API key is invalid
        HTTPException 404: If the experiment doesn't exist or is not active
        HTTPException 500: If there's an error during assignment
    """
    # Check for existing assignment
    existing_assignment = (
        db.query(Assignment)
        .filter(
            Assignment.experiment_id == experiment.id,
            Assignment.user_id == request.user_id,
        )
        .first()
    )

    if existing_assignment:
        # Return existing assignment
        variant = next(
            (v for v in experiment.variants if v.id == existing_assignment.variant_id),
            None,
        )

        if not variant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Assigned variant not found in experiment",
            )

        return AssignmentResponse(
            experiment_key=experiment.name,
            variant_name=variant.name,
            is_control=variant.is_control,
            configuration=variant.configuration,
        )

    # Implement assignment logic (simplified for example)
    # In a real implementation, consider:
    # 1. Traffic allocation percentages
    # 2. Targeting rules
    # 3. Consistent hashing for stable assignments

    # Simplified: Select first variant (in real code, use proper selection logic)
    if not experiment.variants:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Experiment has no variants",
        )

    selected_variant = experiment.variants[0]

    # Create assignment record
    new_assignment = Assignment(
        experiment_id=experiment.id,
        variant_id=selected_variant.id,
        user_id=request.user_id,
        context=request.context,
    )

    db.add(new_assignment)
    db.commit()

    return AssignmentResponse(
        experiment_key=experiment.name,
        variant_name=selected_variant.name,
        is_control=selected_variant.is_control,
        configuration=selected_variant.configuration,
    )


@router.post(
    "/track",
    response_model=EventResponse,
    summary="Track event",
    response_description="Returns confirmation of event tracking",
)
async def track_event(
    request: EventRequest = Body(..., description="Event data to track"),
    api_key_info: Dict[str, Any] = Depends(deps.get_api_key),
    db: Session = Depends(deps.get_db),
) -> EventResponse:
    """
    Track an event for an experiment.

    This endpoint records a user interaction event associated with an experiment.
    Events are used to measure experiment metrics and outcomes.

    Event tracking can be associated with:
    - A specific experiment (using experiment_key)
    - A feature flag (using feature_flag_key)
    - Or both

    Additional data can be included:
    - Numeric value (for revenue, durations, counts)
    - Metadata (additional contextual information)
    - Custom timestamp (defaults to server time if not provided)

    **Authentication**: Requires a valid API key in the X-API-Key header.

    Returns:
        EventResponse: Confirmation of successful event tracking with event ID

    Raises:
        HTTPException 401: If the API key is invalid
        HTTPException 422: If the event data is invalid
    """
    # Find the experiment if specified
    experiment_id = None
    if request.experiment_key:
        experiment = (
            db.query(Experiment)
            .filter(Experiment.name == request.experiment_key)
            .first()
        )

        if experiment:
            experiment_id = experiment.id

    # Find variant if user has an assignment
    variant_id = None
    if experiment_id and request.user_id:
        assignment = (
            db.query(Assignment)
            .filter(
                Assignment.experiment_id == experiment_id,
                Assignment.user_id == request.user_id,
            )
            .first()
        )

        if assignment:
            variant_id = assignment.variant_id

    # Create event record
    event = Event(
        event_type=request.event_type,
        user_id=request.user_id,
        experiment_id=experiment_id,
        variant_id=variant_id,
        value=request.value,
        event_metadata=request.metadata,
        created_at=request.timestamp or None,  # Use current time if not specified
    )

    db.add(event)
    db.commit()

    return EventResponse(
        success=True, event_id=str(event.id), message="Event successfully tracked"
    )


@router.post(
    "/batch",
    response_model=EventBatchResponse,
    summary="Track multiple events in batch",
    response_description="Returns batch processing results",
)
async def track_events_batch(
    request: EventBatchRequest = Body(
        ...,
        description="Batch of events to track",
        example={
            "events": [
                {
                    "event_type": "page_view",
                    "user_id": "user-123",
                    "experiment_key": "homepage-redesign",
                    "metadata": {"page": "/products", "referrer": "google"},
                },
                {
                    "event_type": "click",
                    "user_id": "user-123",
                    "experiment_key": "homepage-redesign",
                    "metadata": {"element": "buy-button"},
                },
            ]
        },
    ),
    api_key_info: Dict[str, Any] = Depends(deps.get_api_key),
    db: Session = Depends(deps.get_db),
) -> EventBatchResponse:
    """
    Track multiple events in a single batch operation.

    This endpoint allows tracking multiple events in a single request,
    improving performance for high-volume event tracking.

    The batch can contain up to 100 events. If any events fail validation,
    the response will include details about which events failed and why.

    **Authentication**: Requires a valid API key in the X-API-Key header.

    Returns:
        EventBatchResponse: Results of the batch processing operation

    Raises:
        HTTPException 401: If the API key is invalid
        HTTPException 413: If the batch size exceeds the limit
        HTTPException 422: If the batch request format is invalid
    """
    if len(request.events) > 100:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Batch size exceeds the limit of 100 events",
        )

    success_count = 0
    failure_count = 0
    errors = []

    # Process each event in the batch
    for index, event_request in enumerate(request.events):
        try:
            # Find the experiment if specified
            experiment_id = None
            if event_request.experiment_key:
                experiment = (
                    db.query(Experiment)
                    .filter(Experiment.name == event_request.experiment_key)
                    .first()
                )

                if experiment:
                    experiment_id = experiment.id

            # Find variant if user has an assignment
            variant_id = None
            if experiment_id and event_request.user_id:
                assignment = (
                    db.query(Assignment)
                    .filter(
                        Assignment.experiment_id == experiment_id,
                        Assignment.user_id == event_request.user_id,
                    )
                    .first()
                )

                if assignment:
                    variant_id = assignment.variant_id

            # Create event record
            event = Event(
                event_type=event_request.event_type,
                user_id=event_request.user_id,
                experiment_id=experiment_id,
                variant_id=variant_id,
                value=event_request.value,
                event_metadata=event_request.metadata,
                created_at=event_request.timestamp or None,
            )

            db.add(event)
            success_count += 1

        except Exception as e:
            failure_count += 1
            errors.append(
                {
                    "index": index,
                    "event_type": event_request.event_type,
                    "user_id": event_request.user_id,
                    "error": str(e),
                }
            )

    # Commit all successful events
    if success_count > 0:
        db.commit()

    return EventBatchResponse(
        success_count=success_count,
        failure_count=failure_count,
        errors=errors if errors else None,
    )
