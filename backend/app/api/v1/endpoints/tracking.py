"""
Tracking API endpoints.

This module provides API endpoints for experiment user assignment and event tracking.
These endpoints are designed to be called from client applications to participate
in experiments and record user interactions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session

from backend.app.api import deps
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.models.assignment import Assignment
from backend.app.models.event import Event, EventType
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.schemas.tracking import (
    AssignmentRequest,
    AssignmentResponse,
    EventCreate,
    EventRequest,
    EventResponse,
    EventBatchRequest,
    EventBatchResponse,
)
from backend.app.services.assignment_service import AssignmentService
from backend.app.services.event_service import EventService

# Create router
router = APIRouter()


@router.get("/")
def get_tracking():
    """
    Tracking API information endpoint.

    Returns general information about the tracking API endpoints.
    """
    return {"message": "Tracking API Endpoints"}


@router.post(
    "/assign",
    response_model=AssignmentResponse,
    summary="Assign user to experiment variant",
    response_description="Returns the variant assignment for the user",
)
async def assign_user_to_experiment(
    request: AssignmentRequest = Body(..., description="Assignment request data"),
    db: Session = Depends(deps.get_db),
    api_key_info: Dict[str, Any] = Depends(deps.get_api_key),
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
    # Get experiment by key
    experiment = (
        db.query(Experiment)
        .filter(
            Experiment.key == request.experiment_key,
            Experiment.status == ExperimentStatus.ACTIVE,
        )
        .first()
    )

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active experiment with key '{request.experiment_key}' not found",
        )

    # Create assignment service
    assignment_service = AssignmentService(db)

    try:
        # Attempt to assign the user
        assignment_data = assignment_service.assign_user(
            user_id=request.user_id,
            experiment_id=str(experiment.id),
            context=request.context,
        )

        # Get the variant
        variant_id = assignment_data.get("variant_id")
        variant = next(
            (v for v in experiment.variants if str(v.id) == variant_id),
            None,
        )

        if not variant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Assigned variant not found in experiment",
            )

        # Create response
        return AssignmentResponse(
            experiment_key=request.experiment_key,
            variant_name=variant.name,
            is_control=variant.is_control,
            configuration=variant.configuration,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning user to experiment: {str(e)}",
        )


@router.post(
    "/track",
    response_model=EventResponse,
    summary="Track event",
    response_description="Returns confirmation of event tracking",
)
async def track_event(
    request: EventRequest = Body(..., description="Event data to track"),
    db: Session = Depends(deps.get_db),
    api_key_info: Dict[str, Any] = Depends(deps.get_api_key),
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
    # Find experiment ID if specified
    experiment_id = None
    variant_id = None
    if request.experiment_key:
        experiment = (
            db.query(Experiment)
            .filter(Experiment.key == request.experiment_key)
            .first()
        )

        if experiment:
            experiment_id = experiment.id

            # Find variant if user has an assignment
            assignment = (
                db.query(Assignment)
                .filter(
                    Assignment.experiment_id == experiment_id,
                    Assignment.user_id == request.user_id,
                )
                .order_by(Assignment.created_at.desc())
                .first()
            )

            if assignment:
                variant_id = assignment.variant_id

    # Find feature flag ID if specified
    feature_flag_id = None
    if request.feature_flag_key:
        feature_flag = (
            db.query(FeatureFlag)
            .filter(FeatureFlag.key == request.feature_flag_key)
            .first()
        )

        if feature_flag:
            feature_flag_id = feature_flag.id

    # If neither found, return error
    if not experiment_id and not feature_flag_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Neither experiment key '{request.experiment_key}' nor feature flag key '{request.feature_flag_key}' found",
        )

    try:
        # Create event data
        event_data = EventCreate(
            user_id=request.user_id,
            event_type=request.event_type,
            event_name=request.event_type,  # Default to type if no name provided
            experiment_id=str(experiment_id) if experiment_id else None,
            feature_flag_id=str(feature_flag_id) if feature_flag_id else None,
            variant_id=str(variant_id) if variant_id else None,
            value=request.value,
            properties=request.metadata,
            timestamp=request.timestamp or datetime.now(timezone.utc).isoformat(),
        )

        # Create event service
        event_service = EventService(db)

        # Track the event
        event = event_service.track_event(event_data.dict())

        # Return success response
        return EventResponse(
            success=True,
            event_id=event.get("id"),
            message="Event successfully tracked",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking event: {str(e)}",
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
    db: Session = Depends(deps.get_db),
    api_key_info: Dict[str, Any] = Depends(deps.get_api_key),
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
    # Check batch size
    if len(request.events) > 100:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Batch size exceeds the limit of 100 events",
        )

    # Create event service
    event_service = EventService(db)

    # Initialize counters
    success_count = 0
    failure_count = 0
    errors = []

    # Process each event
    for index, event_request in enumerate(request.events):
        try:
            # Find experiment ID if specified
            experiment_id = None
            variant_id = None
            if event_request.experiment_key:
                experiment = (
                    db.query(Experiment)
                    .filter(Experiment.key == event_request.experiment_key)
                    .first()
                )

                if experiment:
                    experiment_id = experiment.id

                    # Find variant if user has an assignment
                    assignment = (
                        db.query(Assignment)
                        .filter(
                            Assignment.experiment_id == experiment_id,
                            Assignment.user_id == event_request.user_id,
                        )
                        .order_by(Assignment.created_at.desc())
                        .first()
                    )

                    if assignment:
                        variant_id = assignment.variant_id

            # Find feature flag ID if specified
            feature_flag_id = None
            if event_request.feature_flag_key:
                feature_flag = (
                    db.query(FeatureFlag)
                    .filter(FeatureFlag.key == event_request.feature_flag_key)
                    .first()
                )

                if feature_flag:
                    feature_flag_id = feature_flag.id

            # Skip if neither found
            if not experiment_id and not feature_flag_id:
                failure_count += 1
                errors.append(
                    {
                        "index": index,
                        "event_type": event_request.event_type,
                        "user_id": event_request.user_id,
                        "error": f"Neither experiment key '{event_request.experiment_key}' nor feature flag key '{event_request.feature_flag_key}' found",
                    }
                )
                continue

            # Create event data
            event_data = EventCreate(
                user_id=event_request.user_id,
                event_type=event_request.event_type,
                event_name=event_request.event_type,  # Default to type if no name provided
                experiment_id=str(experiment_id) if experiment_id else None,
                feature_flag_id=str(feature_flag_id) if feature_flag_id else None,
                variant_id=str(variant_id) if variant_id else None,
                value=event_request.value,
                properties=event_request.metadata,
                timestamp=event_request.timestamp
                or datetime.now(timezone.utc).isoformat(),
            )

            # Track the event
            event_service.track_event(event_data.dict())
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

    # Return batch response
    return EventBatchResponse(
        success_count=success_count,
        failure_count=failure_count,
        errors=errors if errors else None,
    )


@router.get(
    "/assignments/{user_id}",
    response_model=List[Dict[str, Any]],
    summary="Get user's experiment assignments",
    response_description="Returns all active experiment assignments for a user",
)
async def get_user_assignments(
    user_id: str = Path(..., description="ID of the user"),
    db: Session = Depends(deps.get_db),
    api_key_info: Dict[str, Any] = Depends(deps.get_api_key),
    active_only: bool = Query(
        True, description="Only return active experiment assignments"
    ),
) -> List[Dict[str, Any]]:
    """
    Get all experiment assignments for a user.

    This endpoint retrieves all experiment variants assigned to a specific user.
    By default, it only returns assignments for active experiments.

    **Authentication**: Requires a valid API key in the X-API-Key header.

    Returns:
        List[Dict[str, Any]]: List of assignment details for the user

    Raises:
        HTTPException 401: If the API key is invalid
        HTTPException 404: If user has no assignments
    """
    # Create assignment service
    assignment_service = AssignmentService(db)

    # Get user assignments
    assignments = assignment_service.get_user_assignments(
        user_id=user_id, active_only=active_only
    )

    if not assignments:
        return []

    return assignments
