"""
Experiment API endpoints.

This module provides RESTful API endpoints for creating, reading, updating, and deleting
experiments in the experimentation platform. It implements the core functionality for
AB testing and feature experimentation.
"""

import uuid
from typing import List, Dict, Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    Body,
    status,
    Response,
)
from sqlalchemy.orm import Session

from backend.app.api import deps
from backend.app.models.user import User
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentListResponse,
    ExperimentResults,
)
from backend.app.services.experiment_service import ExperimentService

# Create router with tag for documentation grouping
router = APIRouter(
    prefix="/experiments",
    tags=["Experiments"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 401,
                            "message": "Could not validate credentials",
                        }
                    }
                }
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 403,
                            "message": "Not enough permissions",
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


@router.get(
    "/",
    response_model=ExperimentListResponse,
    summary="List experiments",
    response_description="Returns a paginated list of experiments",
)
async def list_experiments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
    status_filter: Optional[str] = Query(
        None,
        description="Filter by experiment status (draft, active, paused, completed, archived)",
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(
        100, ge=1, le=500, description="Maximum number of records to return"
    ),
    search: Optional[str] = Query(
        None, description="Search term to filter experiment names and descriptions"
    ),
    sort_by: Optional[str] = Query(
        "created_at",
        description="Field to sort by (created_at, updated_at, name, status)",
    ),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
) -> ExperimentListResponse:
    """
    List experiments with filtering and pagination.

    This endpoint retrieves a list of experiments based on the provided filters.
    Regular users only see their own experiments, while superusers can see all experiments.

    The results are paginated and can be sorted by various fields.

    - **status_filter**: Filter experiments by their current status
    - **skip/limit**: Pagination parameters
    - **search**: Filter experiments by name or description
    - **sort_by/sort_order**: Control the ordering of results

    Returns:
        ExperimentListResponse: Paginated list of experiments with total count
    """
    # Create experiment service
    experiment_service = ExperimentService(db)

    # Query experiments based on user permissions
    if current_user.is_superuser:
        experiments = experiment_service.get_experiments(
            skip=skip,
            limit=limit,
            status=status_filter,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = experiment_service.count_experiments(
            status=status_filter, search=search
        )
    else:
        # Filter by owner for regular users
        experiments = experiment_service.get_experiments_by_owner(
            owner_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status_filter,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = experiment_service.count_experiments_by_owner(
            owner_id=current_user.id, status=status_filter, search=search
        )

    # Create response
    return ExperimentListResponse(
        items=experiments, total=total, skip=skip, limit=limit
    )


@router.post(
    "/",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create experiment",
    response_description="Returns the created experiment",
)
async def create_experiment(
    experiment_in: ExperimentCreate = Body(
        ..., description="Experiment data to create"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Create a new experiment.

    This endpoint allows users to create a new experiment. The current user
    is automatically set as the owner of the experiment.

    The request must include:
    - Basic experiment information (name, description, hypothesis)
    - At least two variants (one must be marked as control)
    - At least one metric to track

    The experiment is created in DRAFT status by default.

    Returns:
        ExperimentResponse: The newly created experiment with all details

    Raises:
        HTTPException: If the experiment data is invalid or creation fails
    """
    # Create experiment service
    experiment_service = ExperimentService(db)

    # Set owner_id to current user
    experiment_data = experiment_in.dict()
    experiment_data["owner_id"] = current_user.id

    # Create experiment
    try:
        experiment = experiment_service.create_experiment(
            ExperimentCreate(**experiment_data)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Invalidate cache if enabled
    if cache_control["enabled"]:
        pattern = f"experiments:{current_user.id}:*"
        for key in cache_control["client"].scan_iter(match=pattern):
            cache_control["client"].delete(key)

    return experiment


@router.get(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Get experiment",
    response_description="Returns the experiment details",
)
async def get_experiment(
    experiment_id: uuid.UUID = Path(
        ..., description="The ID of the experiment to retrieve"
    ),
    db: Session = Depends(deps.get_db),
    experiment: Experiment = Depends(deps.get_experiment_access),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Get experiment details.

    This endpoint retrieves the complete details of a specific experiment by ID.
    The user must have access to the experiment (be the owner or have permission).

    The response includes:
    - Basic experiment information
    - All variants
    - All metrics
    - Current status and dates

    Returns:
        ExperimentResponse: Complete experiment details

    Raises:
        HTTPException 404: If the experiment doesn't exist
        HTTPException 403: If the user doesn't have access to this experiment
    """
    # We already have the experiment from the dependency
    return experiment


@router.put(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Update experiment",
    response_description="Returns the updated experiment",
)
async def update_experiment(
    experiment_in: ExperimentUpdate = Body(
        ..., description="Experiment data to update"
    ),
    experiment_id: uuid.UUID = Path(
        ..., description="The ID of the experiment to update"
    ),
    db: Session = Depends(deps.get_db),
    experiment: Experiment = Depends(deps.get_experiment_access),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Update an experiment.

    This endpoint allows users to update an existing experiment.
    The user must have access to the experiment (be the owner or have permission).

    Fields that can be updated include:
    - Basic information (name, description, hypothesis)
    - Variants (if the experiment is in DRAFT status)
    - Metrics (if the experiment is in DRAFT status)
    - Status (with certain transitions restricted)

    Returns:
        ExperimentResponse: The updated experiment with all details

    Raises:
        HTTPException 400: If the update data is invalid
        HTTPException 403: If updating a running experiment with restricted changes
    """
    # Create experiment service
    experiment_service = ExperimentService(db)

    # Restrict certain updates based on experiment status
    if experiment.status != ExperimentStatus.DRAFT:
        if "variants" in experiment_in.dict(exclude_unset=True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update variants for experiments that are not in DRAFT status",
            )
        if "metrics" in experiment_in.dict(exclude_unset=True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update metrics for experiments that are not in DRAFT status",
            )

    # Update experiment
    try:
        updated_experiment = experiment_service.update_experiment(
            experiment, experiment_in
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Invalidate cache if enabled
    if cache_control["enabled"]:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control["client"].delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = updated_experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control["client"].scan_iter(match=pattern):
            cache_control["client"].delete(key)

    return updated_experiment


@router.delete(
    "/{experiment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete experiment",
    response_description="No content, experiment successfully deleted",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Experiment successfully deleted",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not enough permissions to delete this experiment",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 403,
                            "message": "Not enough permissions",
                        }
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Experiment not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"status_code": 404, "message": "Experiment not found"}
                    }
                }
            },
        },
    },
)
async def delete_experiment(
    experiment_id: uuid.UUID = Path(
        ..., description="The ID of the experiment to delete"
    ),
    db: Session = Depends(deps.get_db),
    experiment: Experiment = Depends(deps.get_experiment_access),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete an experiment.

    This endpoint allows users to delete an existing experiment.
    The user must have access to the experiment (be the owner or have permission).

    Deleting an experiment has the following effects:
    - The experiment and all its related data (variants, metrics) are permanently removed
    - Any cached data related to the experiment is invalidated

    **Note**: This operation cannot be undone. For active experiments, consider
    using the archive operation instead.

    Returns:
        None: No content, experiment was successfully deleted

    Raises:
        HTTPException 403: If the user doesn't have permission to delete this experiment
        HTTPException 404: If the experiment doesn't exist
    """
    # Check if the user is either the owner or a superuser
    if experiment.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be the owner or a superuser to delete this experiment",
        )

    # Delete experiment
    db.delete(experiment)
    db.commit()

    # Invalidate cache if enabled
    if cache_control["enabled"]:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control["client"].delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control["client"].scan_iter(match=pattern):
            cache_control["client"].delete(key)

    # Return 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{experiment_id}/start",
    response_model=ExperimentResponse,
    summary="Start experiment",
    response_description="Returns the started experiment",
)
async def start_experiment(
    experiment_id: uuid.UUID = Path(
        ..., description="The ID of the experiment to start"
    ),
    db: Session = Depends(deps.get_db),
    experiment: Experiment = Depends(deps.get_experiment_access),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Start an experiment.

    This endpoint activates an experiment, changing its status to ACTIVE
    and setting the start date if not already set.

    Starting an experiment makes it eligible for:
    - User traffic assignment
    - Event tracking and analysis
    - Results calculation

    Prerequisites for starting an experiment:
    - The experiment must be in DRAFT or PAUSED status
    - The experiment must have at least one control and one non-control variant
    - The experiment must have at least one metric defined

    Returns:
        ExperimentResponse: The updated experiment with ACTIVE status

    Raises:
        HTTPException 400: If the experiment cannot be started
        HTTPException 403: If the user doesn't have permission to start this experiment
    """
    # Create experiment service
    experiment_service = ExperimentService(db)

    # Check if experiment can be started
    if (
        experiment.status != ExperimentStatus.DRAFT
        and experiment.status != ExperimentStatus.PAUSED
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start experiment with status: {experiment.status.value}",
        )

    # Check for required components
    if not experiment.variants or len(experiment.variants) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment must have at least two variants (one control and one test)",
        )

    has_control = any(variant.is_control for variant in experiment.variants)
    if not has_control:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment must have at least one control variant",
        )

    if not experiment.metric_definitions or len(experiment.metric_definitions) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment must have at least one metric defined",
        )

    # Start experiment
    try:
        started_experiment = experiment_service.start_experiment(experiment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Invalidate cache if enabled
    if cache_control["enabled"]:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control["client"].delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = started_experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control["client"].scan_iter(match=pattern):
            cache_control["client"].delete(key)

    return started_experiment


@router.post(
    "/{experiment_id}/pause",
    response_model=ExperimentResponse,
    summary="Pause experiment",
    response_description="Returns the paused experiment",
)
async def pause_experiment(
    experiment_id: uuid.UUID = Path(
        ..., description="The ID of the experiment to pause"
    ),
    db: Session = Depends(deps.get_db),
    experiment: Experiment = Depends(deps.get_experiment_access),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Pause an experiment.

    This endpoint pauses an active experiment, changing its status to PAUSED.
    Pausing an experiment temporarily stops:
    - New user assignments (existing assignments remain in effect)
    - Data collection and analysis

    The experiment can later be resumed by using the start endpoint.

    Returns:
        ExperimentResponse: The updated experiment with PAUSED status

    Raises:
        HTTPException 400: If the experiment cannot be paused
        HTTPException 403: If the user doesn't have permission to pause this experiment
    """
    # Check if experiment can be paused
    if experiment.status != ExperimentStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause experiment with status: {experiment.status.value}",
        )

    # Update experiment status
    experiment.status = ExperimentStatus.PAUSED
    db.commit()
    db.refresh(experiment)

    # Invalidate cache if enabled
    if cache_control["enabled"]:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control["client"].delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control["client"].scan_iter(match=pattern):
            cache_control["client"].delete(key)

    return experiment


@router.post(
    "/{experiment_id}/complete",
    response_model=ExperimentResponse,
    summary="Complete experiment",
    response_description="Returns the completed experiment",
)
async def complete_experiment(
    experiment_id: uuid.UUID = Path(
        ..., description="The ID of the experiment to complete"
    ),
    db: Session = Depends(deps.get_db),
    experiment: Experiment = Depends(deps.get_experiment_access),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Complete an experiment.

    This endpoint marks an experiment as completed, changing its status to COMPLETED
    and setting the end date if not already set.

    Completing an experiment:
    - Stops new user assignments
    - Finalizes data collection
    - Makes results available for final analysis

    **Note**: This operation is typically performed when an experiment has
    gathered sufficient data to make a decision.

    Returns:
        ExperimentResponse: The updated experiment with COMPLETED status

    Raises:
        HTTPException 400: If the experiment cannot be completed
        HTTPException 403: If the user doesn't have permission to complete this experiment
    """
    # Check if experiment is in a valid state to be completed
    if experiment.status not in [ExperimentStatus.ACTIVE, ExperimentStatus.PAUSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete experiment with status: {experiment.status.value}",
        )

    # Update experiment status
    experiment.status = ExperimentStatus.COMPLETED
    from datetime import datetime, timezone

    experiment.end_date = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(experiment)

    # Invalidate cache if enabled
    if cache_control["enabled"]:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control["client"].delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control["client"].scan_iter(match=pattern):
            cache_control["client"].delete(key)

    return experiment


@router.get(
    "/{experiment_id}/results",
    response_model=ExperimentResults,
    summary="Get experiment results",
    response_description="Returns the experiment results and analysis",
)
async def get_experiment_results(
    experiment_id: uuid.UUID = Path(
        ..., description="The ID of the experiment to get results for"
    ),
    db: Session = Depends(deps.get_db),
    experiment: Experiment = Depends(deps.get_experiment_access),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResults:
    """
    Get experiment results and statistical analysis.

    This endpoint retrieves the analytical results of an experiment, including:
    - Metric values for control and treatment variants
    - Statistical significance calculations
    - Sample sizes
    - Recommendations based on the data

    The results are calculated in real-time based on the latest data.
    For experiments with insufficient data, the statistical significance
    may be inconclusive.

    Returns:
        ExperimentResults: Complete analysis of the experiment results

    Raises:
        HTTPException 400: If the experiment has no data or is in DRAFT status
        HTTPException 403: If the user doesn't have permission to view this experiment
    """
    # Check if experiment has results
    if experiment.status == ExperimentStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot get results for experiments in DRAFT status",
        )

    # Try to get from cache if enabled
    if cache_control["enabled"]:
        cache_key = f"experiment_results:{experiment_id}"
        cached_data = cache_control["client"].get(cache_key)
        if cached_data:
            from pydantic import parse_raw_as

            return parse_raw_as(ExperimentResults, cached_data)

    # Create experiment service
    experiment_service = ExperimentService(db)

    # Calculate results
    try:
        results = experiment_service.calculate_results(experiment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Cache results if enabled
    if cache_control["enabled"]:
        cache_control["client"].setex(
            f"experiment_results:{experiment_id}",
            3600,  # Cache for 1 hour
            results.json(),
        )

    return results
