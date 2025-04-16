"""
API routes for managing feature flag rollout schedules.

This module provides endpoints for creating, updating, and monitoring
feature flag rollout schedules.
"""

from typing import Any, Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from sqlalchemy.orm import Session

from backend.app.api import deps
from backend.app.core.logging import get_logger
from backend.app.models.user import User
from backend.app.models.rollout_schedule import RolloutScheduleStatus, RolloutStageStatus
from backend.app.schemas.rollout_schedule import (
    RolloutScheduleCreate,
    RolloutScheduleUpdate,
    RolloutScheduleResponse,
    RolloutScheduleListResponse,
    RolloutStageCreate,
    RolloutStageUpdate,
    RolloutStageResponse
)
from backend.app.services.rollout_service import RolloutService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=RolloutScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new rollout schedule"
)
def create_rollout_schedule(
    *,
    db: Session = Depends(deps.get_db),
    data: RolloutScheduleCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new rollout schedule for a feature flag.

    This endpoint allows users to create a gradual rollout schedule for a feature flag.
    A schedule consists of multiple stages with defined criteria for progression.
    """
    try:
        schedule = RolloutService.create_rollout_schedule(
            db=db,
            data=data,
            owner_id=current_user.id
        )
        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating rollout schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the rollout schedule"
        )


@router.get(
    "/",
    response_model=RolloutScheduleListResponse,
    summary="Get list of rollout schedules"
)
def get_rollout_schedules(
    *,
    db: Session = Depends(deps.get_db),
    feature_flag_id: Optional[UUID] = Query(None, description="Filter by feature flag ID"),
    status: Optional[RolloutScheduleStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a list of rollout schedules with optional filtering.

    This endpoint returns a paginated list of rollout schedules.
    The results can be filtered by feature flag ID and status.
    """
    try:
        schedules, total = RolloutService.get_rollout_schedules(
            db=db,
            feature_flag_id=feature_flag_id,
            owner_id=None,  # Don't filter by owner - allow viewing all schedules
            status=status,
            skip=skip,
            limit=limit
        )

        return {
            "items": schedules,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting rollout schedules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving rollout schedules"
        )


@router.get(
    "/{schedule_id}",
    response_model=RolloutScheduleResponse,
    summary="Get a specific rollout schedule"
)
def get_rollout_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: UUID = Path(..., description="The ID of the rollout schedule"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific rollout schedule by ID.

    This endpoint returns detailed information about a rollout schedule,
    including all its stages and current status.
    """
    schedule = RolloutService.get_rollout_schedule(db=db, schedule_id=schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rollout schedule not found with ID: {schedule_id}"
        )

    return schedule


@router.put(
    "/{schedule_id}",
    response_model=RolloutScheduleResponse,
    summary="Update a rollout schedule"
)
def update_rollout_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: UUID = Path(..., description="The ID of the rollout schedule"),
    data: RolloutScheduleUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an existing rollout schedule.

    This endpoint allows updating the properties of a rollout schedule,
    including its stages and status transitions.
    """
    try:
        schedule = RolloutService.update_rollout_schedule(
            db=db,
            schedule_id=schedule_id,
            data=data
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout schedule not found with ID: {schedule_id}"
            )

        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating rollout schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the rollout schedule"
        )


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a rollout schedule"
)
def delete_rollout_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: UUID = Path(..., description="The ID of the rollout schedule"),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete a rollout schedule.

    This endpoint allows deletion of a rollout schedule. Active schedules
    cannot be deleted and must be paused or cancelled first.
    """
    try:
        success = RolloutService.delete_rollout_schedule(
            db=db,
            schedule_id=schedule_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout schedule not found with ID: {schedule_id}"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting rollout schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the rollout schedule"
        )


@router.post(
    "/{schedule_id}/activate",
    response_model=RolloutScheduleResponse,
    summary="Activate a rollout schedule"
)
def activate_rollout_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: UUID = Path(..., description="The ID of the rollout schedule"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Activate a rollout schedule.

    This endpoint transitions a schedule from DRAFT or PAUSED to ACTIVE status,
    which enables its automatic processing by the scheduler.
    """
    try:
        schedule = RolloutService.activate_rollout_schedule(
            db=db,
            schedule_id=schedule_id
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout schedule not found with ID: {schedule_id}"
            )

        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error activating rollout schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while activating the rollout schedule"
        )


@router.post(
    "/{schedule_id}/pause",
    response_model=RolloutScheduleResponse,
    summary="Pause a rollout schedule"
)
def pause_rollout_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: UUID = Path(..., description="The ID of the rollout schedule"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Pause an active rollout schedule.

    This endpoint transitions a schedule from ACTIVE to PAUSED status,
    which temporarily suspends its processing by the scheduler.
    """
    try:
        schedule = RolloutService.pause_rollout_schedule(
            db=db,
            schedule_id=schedule_id
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout schedule not found with ID: {schedule_id}"
            )

        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error pausing rollout schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while pausing the rollout schedule"
        )


@router.post(
    "/{schedule_id}/cancel",
    response_model=RolloutScheduleResponse,
    summary="Cancel a rollout schedule"
)
def cancel_rollout_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: UUID = Path(..., description="The ID of the rollout schedule"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cancel a rollout schedule.

    This endpoint transitions a schedule to CANCELLED status,
    which permanently stops its processing by the scheduler.
    """
    try:
        schedule = RolloutService.cancel_rollout_schedule(
            db=db,
            schedule_id=schedule_id
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout schedule not found with ID: {schedule_id}"
            )

        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cancelling rollout schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while cancelling the rollout schedule"
        )


@router.post(
    "/{schedule_id}/stages",
    response_model=RolloutStageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a stage to a rollout schedule"
)
def add_rollout_stage(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: UUID = Path(..., description="The ID of the rollout schedule"),
    data: RolloutStageCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add a new stage to a rollout schedule.

    This endpoint allows adding a new stage to an existing rollout schedule.
    The stage defines a target percentage and criteria for activation.
    """
    try:
        stage = RolloutService.add_rollout_stage(
            db=db,
            schedule_id=schedule_id,
            data=data
        )

        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout schedule not found with ID: {schedule_id}"
            )

        return stage
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding rollout stage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while adding the rollout stage"
        )


@router.put(
    "/stages/{stage_id}",
    response_model=RolloutStageResponse,
    summary="Update a rollout stage"
)
def update_rollout_stage(
    *,
    db: Session = Depends(deps.get_db),
    stage_id: UUID = Path(..., description="The ID of the rollout stage"),
    data: RolloutStageUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an existing rollout stage.

    This endpoint allows updating the properties of a rollout stage,
    including its target percentage and trigger criteria.
    """
    try:
        stage = RolloutService.update_rollout_stage(
            db=db,
            stage_id=stage_id,
            data=data
        )

        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout stage not found with ID: {stage_id}"
            )

        return stage
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating rollout stage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the rollout stage"
        )


@router.delete(
    "/stages/{stage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a rollout stage"
)
def delete_rollout_stage(
    *,
    db: Session = Depends(deps.get_db),
    stage_id: UUID = Path(..., description="The ID of the rollout stage"),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete a rollout stage.

    This endpoint allows deletion of a pending rollout stage.
    Stages that are already in progress or completed cannot be deleted.
    """
    try:
        success = RolloutService.delete_rollout_stage(
            db=db,
            stage_id=stage_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout stage not found with ID: {stage_id}"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting rollout stage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the rollout stage"
        )


@router.post(
    "/stages/{stage_id}/advance",
    response_model=RolloutStageResponse,
    summary="Manually advance a stage"
)
def manually_advance_stage(
    *,
    db: Session = Depends(deps.get_db),
    stage_id: UUID = Path(..., description="The ID of the rollout stage"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Manually advance a stage with manual trigger type.

    This endpoint allows manually triggering a stage transition
    for stages with manual trigger types.
    """
    try:
        stage = RolloutService.manually_advance_stage(
            db=db,
            stage_id=stage_id
        )

        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollout stage not found with ID: {stage_id}"
            )

        return stage
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error advancing rollout stage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while advancing the rollout stage"
        )
