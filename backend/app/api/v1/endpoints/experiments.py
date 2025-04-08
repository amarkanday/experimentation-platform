"""
Experiment API endpoints.

This module provides RESTful API endpoints for creating, reading, updating, and deleting
experiments in the experimentation platform. It implements the core functionality for
AB testing and feature experimentation.
"""

from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

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
from pydantic import BaseModel

from backend.app.api import deps
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentListResponse,
    ExperimentResults,
)
from backend.app.services.experiment import ExperimentService
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.cache import CacheService

# Create router with tag for documentation grouping
router = APIRouter(
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
    experiments = ExperimentService.list_experiments(
        db=db,
        user=current_user,
        skip=skip,
        limit=limit,
        status=status_filter,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total = ExperimentService.count_experiments(
        db=db,
        user=current_user,
        status=status_filter,
        search=search,
    )
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
        HTTPException 403: If the user doesn't have permission to create experiments
    """
    experiment = ExperimentService.create_experiment(
        db=db,
        user=current_user,
        experiment_in=experiment_in,
    )

    # Invalidate cache if enabled
    if cache_control.enabled and cache_control.redis:
        pattern = f"experiments:{current_user.id}:*"
        for key in cache_control.redis.scan_iter(match=pattern):
            cache_control.redis.delete(key)

    return experiment


@router.get(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Get experiment",
    response_description="Returns the experiment details",
)
async def get_experiment(
    experiment_id: UUID = Path(..., description="The ID of the experiment to retrieve"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Get experiment by ID.

    Retrieves the detailed information for a specific experiment.
    Users can only access experiments they own or have permission to view.

    Returns:
        ExperimentResponse: The experiment details

    Raises:
        HTTPException 404: If experiment not found
        HTTPException 403: If user doesn't have access to this experiment
    """
    # Check cache first if enabled
    if cache_control.enabled and cache_control.redis:
        cache_key = f"experiment:{experiment_id}"
        cached_data = cache_control.redis.get(cache_key)
        if cached_data:
            from pydantic import parse_raw_as

            return parse_raw_as(ExperimentResponse, cached_data)

    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

    # Cache result if enabled
    if cache_control.enabled and cache_control.redis:
        cache_control.redis.setex(
            f"experiment:{experiment_id}",
            3600,  # Cache for 1 hour
            ExperimentResponse.from_orm(experiment).json(),
        )

    return ExperimentResponse.from_orm(experiment)


@router.put(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Update experiment",
    response_description="Returns the updated experiment",
)
async def update_experiment(
    experiment_id: UUID = Path(..., description="The ID of the experiment to update"),
    experiment_in: ExperimentUpdate = Body(
        ..., description="Experiment data to update"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Update an existing experiment.

    This endpoint allows updating experiment details, including:
    - Basic information (name, description, hypothesis)
    - Variants (if the experiment is in draft status)
    - Metrics (if the experiment is in draft status)
    - Targeting rules
    - Tags

    Requires UPDATE permission on EXPERIMENT resource.

    Returns:
        ExperimentResponse: The updated experiment with all details
    """
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    # Check if variants or metrics are being updated
    if "variants" in experiment_in.dict(exclude_unset=True):
        if experiment.status != ExperimentStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update variants for experiments that are not in draft status",
            )

    if "metrics" in experiment_in.dict(exclude_unset=True):
        if experiment.status != ExperimentStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update metrics for experiments that are not in draft status",
            )

    # Update experiment
    updated_experiment = ExperimentService.update_experiment(
        db=db,
        user=current_user,
        experiment=experiment,
        experiment_in=experiment_in,
    )

    # Invalidate cache if enabled
    if cache_control.enabled and cache_control.redis:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control.redis.delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = updated_experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control.redis.scan_iter(match=pattern):
            cache_control.redis.delete(key)

    return ExperimentResponse.from_orm(updated_experiment)


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
    experiment_id: UUID = Path(..., description="The ID of the experiment to delete"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> None:
    """
    Delete an experiment.

    This endpoint allows users to delete an existing experiment.
    The user must have DELETE permission on the EXPERIMENT resource.

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
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

    ExperimentService.delete_experiment(db=db, experiment=experiment)

    # Invalidate cache if enabled
    if cache_control.enabled and cache_control.redis:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control.redis.delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control.redis.scan_iter(match=pattern):
            cache_control.redis.delete(key)

    # Return 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{experiment_id}/start",
    response_model=ExperimentResponse,
    summary="Start experiment",
    response_description="Returns the started experiment",
)
async def start_experiment(
    experiment_id: UUID = Path(..., description="The ID of the experiment to start"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Start an experiment.

    This endpoint activates an experiment, changing its status to ACTIVE
    and setting the start date if not already set.
    The user must have UPDATE permission on the EXPERIMENT resource.

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
        HTTPException 404: If the experiment is not found
    """
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

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
    started_experiment = ExperimentService.start_experiment(
        db=db,
        user=current_user,
        experiment=experiment,
    )

    # Invalidate cache if enabled
    if cache_control.enabled and cache_control.redis:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control.redis.delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = started_experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control.redis.scan_iter(match=pattern):
            cache_control.redis.delete(key)

    return ExperimentResponse.from_orm(started_experiment)


@router.post(
    "/{experiment_id}/pause",
    response_model=ExperimentResponse,
    summary="Pause experiment",
    response_description="Returns the paused experiment",
)
async def pause_experiment(
    experiment_id: UUID = Path(..., description="The ID of the experiment to pause"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
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
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

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
    if cache_control.enabled and cache_control.redis:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control.redis.delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control.redis.scan_iter(match=pattern):
            cache_control.redis.delete(key)

    return ExperimentResponse.from_orm(experiment)


@router.post(
    "/{experiment_id}/complete",
    response_model=ExperimentResponse,
    summary="Complete experiment",
    response_description="Returns the completed experiment",
)
async def complete_experiment(
    experiment_id: UUID = Path(..., description="The ID of the experiment to complete"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
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
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

    # Check if experiment is in a valid state to be completed
    if experiment.status not in [ExperimentStatus.ACTIVE, ExperimentStatus.PAUSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete experiment with status: {experiment.status.value}",
        )

    # Update experiment status
    experiment.status = ExperimentStatus.COMPLETED
    experiment.end_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(experiment)

    # Invalidate cache if enabled
    if cache_control.enabled and cache_control.redis:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control.redis.delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = experiment.owner_id
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control.redis.scan_iter(match=pattern):
            cache_control.redis.delete(key)

    return ExperimentResponse.from_orm(experiment)


@router.get(
    "/{experiment_id}/results",
    response_model=ExperimentResults,
    summary="Get experiment results",
    response_description="Returns the experiment results and analysis",
)
async def get_experiment_results(
    experiment_id: UUID = Path(
        ..., description="The ID of the experiment to get results for"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResults:
    """
    Get experiment results and analysis.

    This endpoint provides detailed results for an experiment, including:
    - Primary and secondary metric results
    - Statistical significance
    - Confidence intervals
    - Sample sizes and power analysis

    Requires READ permission on EXPERIMENT resource.

    Returns:
        ExperimentResults: Detailed experiment results and analysis
    """
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    # Check if experiment has results
    if experiment.status == ExperimentStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot get results for experiments in draft status",
        )

    # Try to get from cache if enabled
    if cache_control.enabled and cache_control.redis:
        cache_key = f"experiment_results:{experiment_id}"
        cached_data = cache_control.redis.get(cache_key)
        if cached_data:
            from pydantic import parse_raw_as

            return parse_raw_as(ExperimentResults, cached_data)

    # Calculate results
    results = ExperimentService.calculate_results(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )

    # Cache results if enabled
    if cache_control.enabled and cache_control.redis:
        cache_control.redis.setex(
            f"experiment_results:{experiment_id}",
            3600,  # Cache for 1 hour
            results.json(),
        )

    return results


# New endpoints


@router.post(
    "/{experiment_id}/archive",
    response_model=ExperimentResponse,
    summary="Archive experiment",
    response_description="Returns the archived experiment",
)
async def archive_experiment(
    experiment_id: UUID = Path(..., description="The ID of the experiment to archive"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Archive an experiment.

    This endpoint archives an experiment, changing its status to ARCHIVED.
    Archiving an experiment:
    - Makes it inactive for user assignments
    - Preserves all collected data for historical analysis
    - Moves it to the archive section in the UI

    This is the preferred alternative to deletion for experiments that are no longer
    active but whose data should be preserved.

    Returns:
        ExperimentResponse: The updated experiment with ARCHIVED status

    Raises:
        HTTPException 400: If the experiment is already archived
        HTTPException 403: If the user doesn't have permission to archive this experiment
    """
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

    # Check if experiment is already archived
    if experiment.status == ExperimentStatus.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment is already archived",
        )

    # Archive experiment
    archived_experiment = ExperimentService.archive_experiment(
        db=db,
        user=current_user,
        experiment=experiment,
    )

    # Invalidate cache if enabled
    if cache_control.enabled and cache_control.redis:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control.redis.delete(experiment_cache_key)

        # Delete experiment list caches
        owner_id = archived_experiment.get("owner_id")
        pattern = f"experiments:{owner_id}:*"
        for key in cache_control.redis.scan_iter(match=pattern):
            cache_control.redis.delete(key)

    return ExperimentResponse.from_orm(experiment)


@router.post(
    "/{experiment_id}/clone",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone experiment",
    response_description="Returns the cloned experiment",
)
async def clone_experiment(
    experiment_id: UUID = Path(..., description="The ID of the experiment to clone"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> ExperimentResponse:
    """
    Clone an experiment.

    This endpoint creates a new experiment that is a copy of an existing experiment.
    The cloned experiment will:
    - Have a name prefixed with "Copy of"
    - Be in DRAFT status
    - Have the same variants, metrics, and configuration as the original
    - Have the current user as the owner

    This is useful for creating variations of existing experiments or repeating
    successful experiments with minor modifications.

    Returns:
        ExperimentResponse: The newly created cloned experiment

    Raises:
        HTTPException 403: If the user doesn't have permission to view the source experiment
        HTTPException 404: If the source experiment doesn't exist
    """
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

    # Clone experiment
    cloned_experiment = ExperimentService.clone_experiment(
        db=db,
        user=current_user,
        experiment=experiment,
    )

    # Invalidate cache if enabled
    if cache_control.enabled and cache_control.redis:
        # Delete experiment list caches
        pattern = f"experiments:{current_user.id}:*"
        for key in cache_control.redis.scan_iter(match=pattern):
            cache_control.redis.delete(key)

    return cloned_experiment


@router.get(
    "/{experiment_id}/daily-results",
    response_model=List[Dict[str, Any]],
    summary="Get daily experiment results",
    response_description="Returns the experiment results by day",
)
async def get_daily_experiment_results(
    experiment_id: UUID = Path(
        ..., description="The ID of the experiment to get results for"
    ),
    metric_id: Optional[UUID] = Query(
        None, description="Optional ID of specific metric to analyze"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> List[Dict[str, Any]]:
    """
    Get daily experiment results.

    This endpoint provides experiment results broken down by day, including:
    - Daily conversion rates for each variant
    - Daily sample sizes
    - Cumulative metrics

    Requires READ permission on EXPERIMENT resource.

    Returns:
        List[Dict[str, Any]]: List of daily results
    """
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    # Check if experiment has results
    if experiment.status == ExperimentStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot get results for experiments in draft status",
        )

    # Try to get from cache if enabled
    if cache_control.enabled and cache_control.redis:
        metric_part = f":{metric_id}" if metric_id else ""
        cache_key = f"experiment_daily_results:{experiment_id}{metric_part}"
        cached_data = cache_control.redis.get(cache_key)
        if cached_data:
            import json

            return json.loads(cached_data)

    # Get daily results
    results = ExperimentService.get_daily_results(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
        metric_id=metric_id,
    )

    # Cache results if enabled
    if cache_control.enabled and cache_control.redis:
        import json

        metric_part = f":{metric_id}" if metric_id else ""
        cache_key = f"experiment_daily_results:{experiment_id}{metric_part}"
        cache_control.redis.setex(
            cache_key,
            3600,  # Cache for 1 hour
            json.dumps(results),
        )

    return results


@router.get(
    "/{experiment_id}/segmented-results/{segment_by}",
    response_model=Dict[str, Any],
    summary="Get segmented experiment results",
    response_description="Returns the experiment results segmented by a property",
)
async def get_segmented_experiment_results(
    experiment_id: UUID = Path(
        ..., description="The ID of the experiment to get results for"
    ),
    segment_by: str = Path(
        ..., description="Property to segment results by (e.g., 'country', 'device')"
    ),
    metric_id: Optional[UUID] = Query(
        None, description="Optional ID of specific metric to analyze"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> Dict[str, Any]:
    """
    Get experiment results segmented by a property.

    This endpoint provides experiment results broken down by a specific property such as
    country, device, browser, etc.

    Requires READ permission on EXPERIMENT resource.

    Returns:
        Dict[str, Any]: Segmented results for each value of the property
    """
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    # Check if experiment has results
    if experiment.status == ExperimentStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot get results for experiments in draft status",
        )

    # Try to get from cache if enabled
    if cache_control.enabled and cache_control.redis:
        metric_part = f":{metric_id}" if metric_id else ""
        cache_key = (
            f"experiment_segmented_results:{experiment_id}:{segment_by}{metric_part}"
        )
        cached_data = cache_control.redis.get(cache_key)
        if cached_data:
            import json

            return json.loads(cached_data)

    # Get segmented results
    results = ExperimentService.get_segmented_results(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
        segment_by=segment_by,
        metric_id=metric_id,
    )

    # Cache results if enabled
    if cache_control.enabled and cache_control.redis:
        import json

        metric_part = f":{metric_id}" if metric_id else ""
        cache_key = (
            f"experiment_segmented_results:{experiment_id}:{segment_by}{metric_part}"
        )
        cache_control.redis.setex(
            cache_key,
            3600,  # Cache for 1 hour
            json.dumps(results),
        )

    return results


@router.post(
    "/{experiment_id}/metadata",
    response_model=Dict[str, Any],
    summary="Update experiment metadata",
    response_description="Returns the updated experiment with metadata",
)
async def update_experiment_metadata(
    experiment_id: UUID = Path(..., description="The ID of the experiment to update"),
    metadata: Dict[str, Any] = Body(..., description="Metadata to update"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> Dict[str, Any]:
    """
    Update experiment metadata.

    This endpoint allows updating additional metadata associated with an experiment,
    such as notes, insights, learnings, and other custom fields.

    This metadata is separate from the core experiment configuration and can be
    updated regardless of the experiment's status.

    Returns:
        Dict[str, Any]: The updated experiment with metadata

    Raises:
        HTTPException 403: If the user doesn't have permission to update this experiment
        HTTPException 404: If the experiment doesn't exist
    """
    experiment = ExperimentService.get_experiment(
        db=db,
        user=current_user,
        experiment_id=experiment_id,
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

    # Update experiment metadata
    updated_experiment = ExperimentService.update_experiment_metadata(
        db=db,
        user=current_user,
        experiment=experiment,
        metadata=metadata,
    )

    # Invalidate cache if enabled
    if cache_control.enabled and cache_control.redis:
        # Delete specific experiment cache
        experiment_cache_key = f"experiment:{experiment_id}"
        cache_control.redis.delete(experiment_cache_key)

    return updated_experiment


@router.get(
    "/analysis/sample-size",
    response_model=Dict[str, Any],
    summary="Calculate required sample size",
    response_description="Returns the required sample size for an experiment",
)
async def calculate_experiment_sample_size(
    baseline_rate: float = Query(
        ..., gt=0, lt=1, description="Baseline conversion rate (0-1)"
    ),
    minimum_detectable_effect: float = Query(
        ...,
        gt=0,
        description="Minimum detectable effect (relative change, e.g. 0.1 for 10%)",
    ),
    statistical_power: float = Query(
        0.8, ge=0.5, le=0.99, description="Statistical power (0.5-0.99)"
    ),
    significance_level: float = Query(
        0.05, ge=0.01, le=0.1, description="Significance level (0.01-0.1)"
    ),
    is_one_sided: bool = Query(
        False, description="Whether the test is one-sided (default: two-sided)"
    ),
    daily_traffic: Optional[int] = Query(
        None, gt=0, description="Daily traffic to the experiment (optional)"
    ),
    traffic_allocation: Optional[float] = Query(
        None,
        gt=0,
        le=1,
        description="Fraction of traffic allocated to the experiment (0-1)",
    ),
    variant_count: int = Query(
        2, ge=2, description="Number of variants (including control)"
    ),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """
    Calculate the required sample size for an experiment.

    This endpoint calculates the number of samples needed per variant and in total
    to achieve the desired statistical power for detecting the minimum effect size.

    Optionally, if daily traffic and traffic allocation are provided, it also
    estimates how long the experiment will need to run to collect the required sample.

    Returns:
        Dict[str, Any]: Sample size calculation results
    """
    import math

    # Calculate z-scores for alpha and beta
    if is_one_sided:
        z_alpha = abs(stats_z_score(significance_level))
    else:
        z_alpha = abs(stats_z_score(significance_level / 2))  # Two-sided test

    z_beta = abs(stats_z_score(1 - statistical_power))

    # Calculate expected rate for treatment
    treatment_rate = baseline_rate * (1 + minimum_detectable_effect)

    # Calculate pooled standard error
    pooled_variance = baseline_rate * (1 - baseline_rate) + treatment_rate * (
        1 - treatment_rate
    )

    # Calculate required sample size per variant
    numerator = (z_alpha + z_beta) ** 2 * pooled_variance
    denominator = (treatment_rate - baseline_rate) ** 2

    samples_per_variant = math.ceil(numerator / denominator)

    # Calculate total sample size
    total_samples = samples_per_variant * variant_count

    # Calculate estimated duration if daily traffic and allocation are provided
    estimated_duration_days = None
    notes = None

    if daily_traffic is not None and traffic_allocation is not None:
        if traffic_allocation <= 0 or traffic_allocation > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Traffic allocation must be between 0 and 1",
            )

        # Calculate daily experiment traffic
        daily_experiment_traffic = daily_traffic * traffic_allocation

        # Calculate daily traffic per variant
        daily_variant_traffic = daily_experiment_traffic / variant_count

        # Calculate days needed
        days_needed = math.ceil(samples_per_variant / daily_variant_traffic)

        # Add estimates for different time periods
        estimated_duration_days = {
            "days": days_needed,
            "weeks": math.ceil(days_needed / 7),
            "months": math.ceil(days_needed / 30),
        }

        # Add notes for very long or very short experiments
        if days_needed < 7:
            notes = "This experiment is very short. Consider implementing proper guardrails to avoid data quality issues."
        elif days_needed > 90:
            notes = "This experiment will take a long time to complete. Consider increasing traffic allocation, reducing the number of variants, or adjusting the minimum detectable effect."

    # Return response
    return {
        "baseline_rate": baseline_rate,
        "minimum_detectable_effect": minimum_detectable_effect,
        "statistical_power": statistical_power,
        "significance_level": significance_level,
        "is_one_sided": is_one_sided,
        "samples_per_variant": samples_per_variant,
        "total_samples": total_samples,
        "estimated_duration_days": estimated_duration_days,
        "notes": notes,
    }


def stats_z_score(p: float) -> float:
    """
    Calculate the z-score for a given probability.

    This is an approximation of the inverse of the standard normal CDF.

    Args:
        p: Probability (0-1)

    Returns:
        float: Corresponding z-score
    """
    import math

    # Simple case for common values
    if p == 0.05:
        return 1.96
    if p == 0.01:
        return 2.58
    if p == 0.1:
        return 1.65
    if p == 0.2:
        return 1.28
    if p == 0.5:
        return 0.67

    # Constants for the approximation
    a1 = -39.6968302866538
    a2 = 220.946098424521
    a3 = -275.928510446969
    a4 = 138.357751867269
    a5 = -30.6647980661472
    a6 = 2.50662827745924

    b1 = -54.4760987982241
    b2 = 161.585836858041
    b3 = -155.698979859887
    b4 = 66.8013118877197
    b5 = -13.2806815528857

    c1 = -0.00778489400243029
    c2 = -0.322396458041136
    c3 = -2.40075827716184
    c4 = -2.54973253934373
    c5 = 4.37466414146497
    c6 = 2.93816398269878

    d1 = 0.00778469570904146
    d2 = 0.32246712907004
    d3 = 2.445134137143
    d4 = 3.75440866190742

    # Determine which approximation to use based on p
    if p <= 0 or p >= 1:
        raise ValueError("Probability must be between 0 and 1")

    if p < 0.02425:
        # Lower region
        q = math.sqrt(-2 * math.log(p))
        z = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / (
            (((d1 * q + d2) * q + d3) * q + d4) * q + 1
        )
    elif p < 0.97575:
        # Central region
        q = p - 0.5
        r = q * q
        z = (
            (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6)
            * q
            / (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1)
        )
    else:
        # Upper region
        q = math.sqrt(-2 * math.log(1 - p))
        z = -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / (
            (((d1 * q + d2) * q + d3) * q + d4) * q + 1
        )

    return z
