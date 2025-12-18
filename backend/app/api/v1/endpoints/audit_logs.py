"""
Audit Log API endpoints.

This module provides RESTful API endpoints for querying audit logs,
enabling administrators and authorized users to view the complete
audit trail of all system actions.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    status,
)
from sqlalchemy.orm import Session

from backend.app.api import deps
from backend.app.models.user import User
from backend.app.models.audit_log import ActionType, EntityType
from backend.app.schemas.audit_log import (
    AuditLogListResponse,
    AuditLogResponse,
    AuditLogFilterParams,
    AuditStatsResponse,
)
from backend.app.services.audit_service import AuditService
from backend.app.core.permissions import ResourceType, Action, check_permission

# Create router with tag for documentation grouping
router = APIRouter(
    tags=["Audit Logs"],
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
    response_model=AuditLogListResponse,
    summary="List audit logs",
    response_description="Returns a paginated list of audit logs with filtering options",
)
async def list_audit_logs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[UUID] = Query(None, description="Filter by entity ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    from_date: Optional[datetime] = Query(None, description="Filter logs from this date (ISO format)"),
    to_date: Optional[datetime] = Query(None, description="Filter logs until this date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records per page"),
) -> AuditLogListResponse:
    """
    Retrieve audit logs with filtering and pagination.

    This endpoint allows authorized users to query audit logs with various filters:
    - **user_id**: Filter by specific user
    - **entity_type**: Filter by entity type (feature_flag, experiment, user, etc.)
    - **entity_id**: Filter by specific entity
    - **action_type**: Filter by action type (toggle_enable, create, update, etc.)
    - **from_date**: Filter logs from this date
    - **to_date**: Filter logs until this date
    - **page**: Page number for pagination
    - **limit**: Number of records per page

    Only users with appropriate permissions can access audit logs.
    Regular users can only see their own actions, while administrators
    can see all audit logs.
    """
    # Check if user has permission to view audit logs
    # ADMIN and ANALYST roles can view all audit logs
    # DEVELOPER and VIEWER roles can only view their own audit logs
    can_view_all = check_permission(current_user, ResourceType.USER, Action.READ)

    # If user doesn't have permission to view all logs, restrict to their own actions
    # Override any user_id parameter they might have passed
    if not can_view_all and not current_user.is_superuser:
        user_id = current_user.id

    # Validate and convert enum parameters
    entity_type_enum = None
    if entity_type:
        try:
            entity_type_enum = EntityType(entity_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entity type: {entity_type}",
            )

    action_type_enum = None
    if action_type:
        try:
            action_type_enum = ActionType(action_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action type: {action_type}",
            )

    # Validate date range
    if from_date and to_date and to_date <= from_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="to_date must be after from_date",
        )

    try:
        # Get audit logs
        audit_logs, total_count = AuditService.get_audit_logs(
            db=db,
            user_id=user_id,
            entity_type=entity_type_enum,
            entity_id=entity_id,
            action_type=action_type_enum,
            from_date=from_date,
            to_date=to_date,
            page=page,
            limit=limit,
        )

        # Convert to response models
        audit_log_responses = [
            AuditLogResponse.model_validate(log) for log in audit_logs
        ]

        # Calculate total pages
        total_pages = (total_count + limit - 1) // limit

        return AuditLogListResponse(
            items=audit_log_responses,
            total=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        )


@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=list[AuditLogResponse],
    summary="Get audit history for a specific entity",
    response_description="Returns audit logs for a specific entity",
)
async def get_entity_audit_history(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    entity_type: str = Path(..., description="Type of entity (feature_flag, experiment, etc.)"),
    entity_id: UUID = Path(..., description="ID of the entity"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
) -> list[AuditLogResponse]:
    """
    Get audit history for a specific entity.

    This endpoint returns the complete audit trail for a specific entity,
    such as a feature flag or experiment. The logs are ordered by timestamp
    with the most recent first.

    Only users with appropriate permissions can access entity audit history.
    """
    # Check if user has permission to view audit logs
    can_view_all = check_permission(current_user, ResourceType.USER, Action.READ)

    if not can_view_all and not current_user.is_superuser:
        # For regular users, check if they own the entity
        # This would need to be expanded based on entity type
        # For now, allow access only to superusers and users with READ permission
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view entity audit history",
        )

    # Validate entity type
    try:
        entity_type_enum = EntityType(entity_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity type: {entity_type}",
        )

    try:
        # Get audit logs for the entity
        audit_logs = AuditService.get_entity_audit_history(
            db=db,
            entity_type=entity_type_enum,
            entity_id=entity_id,
            limit=limit,
        )

        # Convert to response models
        return [AuditLogResponse.model_validate(log) for log in audit_logs]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve entity audit history",
        )


@router.get(
    "/user/{user_id}",
    response_model=list[AuditLogResponse],
    summary="Get audit logs for a specific user",
    response_description="Returns audit logs for a specific user's activity",
)
async def get_user_activity(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    user_id: UUID = Path(..., description="ID of the user"),
    from_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter logs until this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
) -> list[AuditLogResponse]:
    """
    Get audit logs for a specific user's activity.

    This endpoint returns all audit logs for a specific user's actions.
    Regular users can only view their own activity, while administrators
    can view any user's activity.
    """
    # Check if user has permission to view all user activity
    can_view_all = check_permission(current_user, ResourceType.USER, Action.READ)

    # Users can view their own activity, superusers and those with READ permission can view any user's activity
    if not can_view_all and not current_user.is_superuser and str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user's activity",
        )

    # Validate date range
    if from_date and to_date and to_date <= from_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="to_date must be after from_date",
        )

    try:
        # Get user activity
        audit_logs = AuditService.get_user_activity(
            db=db,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )

        # Convert to response models
        return [AuditLogResponse.model_validate(log) for log in audit_logs]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity",
        )


@router.get(
    "/stats",
    response_model=AuditStatsResponse,
    summary="Get audit log statistics",
    response_description="Returns statistics about audit logs",
)
async def get_audit_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    from_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter logs until this date"),
) -> AuditStatsResponse:
    """
    Get audit log statistics.

    This endpoint returns statistical information about audit logs,
    including counts by action type, entity type, and most active users.

    Only administrators can access audit statistics.
    """
    # Check if user has permission to view audit statistics
    # Only ADMIN role can view audit statistics
    if not current_user.is_superuser and not check_permission(current_user, ResourceType.USER, Action.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view audit statistics",
        )

    # Validate date range
    if from_date and to_date and to_date <= from_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="to_date must be after from_date",
        )

    try:
        # Get audit statistics
        stats = AuditService.get_audit_stats(
            db=db,
            from_date=from_date,
            to_date=to_date,
        )

        return AuditStatsResponse.model_validate(stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit statistics",
        )