"""
Example of structured logging in API endpoints.

This example demonstrates how to use the logging system in FastAPI endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from backend.app.core.logging import get_logger, LogContext
from backend.app.models.user import User
from backend.app.api import deps

router = APIRouter()
logger = get_logger(__name__)

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """
    Get user details with structured logging.

    Args:
        user_id: The ID of the user to retrieve
        current_user: The currently authenticated user

    Returns:
        User details

    Raises:
        HTTPException: If user not found or unauthorized
    """
    # Create log context with user information
    with LogContext(logger, user_id=current_user.id) as ctx:
        ctx.info(
            "Fetching user details",
            extra={
                "target_user_id": user_id,
                "operation": "get_user"
            }
        )

        try:
            # Simulate user lookup
            user = {"id": user_id, "name": "John Doe"}

            ctx.info(
                "User found",
                extra={
                    "user_id": user_id,
                    "operation": "get_user",
                    "result": "success"
                }
            )

            return user

        except Exception as e:
            ctx.error(
                "Failed to fetch user",
                exc_info=True,
                extra={
                    "user_id": user_id,
                    "operation": "get_user",
                    "error": str(e)
                }
            )
            raise HTTPException(status_code=404, detail="User not found")

@router.post("/users")
async def create_user(
    user_data: Dict[str, Any],
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new user with structured logging.

    Args:
        user_data: The user data to create
        current_user: The currently authenticated user

    Returns:
        Created user details

    Raises:
        HTTPException: If creation fails
    """
    # Create log context with user information
    with LogContext(logger, user_id=current_user.id) as ctx:
        ctx.info(
            "Creating new user",
            extra={
                "operation": "create_user",
                "user_data": {
                    "email": user_data.get("email"),
                    "name": user_data.get("name")
                }
            }
        )

        try:
            # Simulate user creation
            new_user = {
                "id": "new-user-id",
                "email": user_data.get("email"),
                "name": user_data.get("name")
            }

            ctx.info(
                "User created successfully",
                extra={
                    "operation": "create_user",
                    "user_id": new_user["id"],
                    "result": "success"
                }
            )

            return new_user

        except Exception as e:
            ctx.error(
                "Failed to create user",
                exc_info=True,
                extra={
                    "operation": "create_user",
                    "error": str(e)
                }
            )
            raise HTTPException(status_code=400, detail="Failed to create user")
