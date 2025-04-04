"""
Example of structured logging in background tasks.

This example demonstrates how to use the logging system in background tasks.
"""

import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime

from backend.app.core.logging import get_logger, LogContext

logger = get_logger(__name__)

class BackgroundTaskService:
    """Service for managing background tasks with structured logging."""

    def __init__(self):
        """Initialize the service."""
        self.tasks: Dict[str, asyncio.Task] = {}

    async def start_data_sync(
        self,
        user_id: str,
        sync_config: Dict[str, Any]
    ) -> str:
        """
        Start a data synchronization task with structured logging.

        Args:
            user_id: The ID of the user starting the sync
            sync_config: Configuration for the sync

        Returns:
            Task ID for tracking the sync
        """
        # Create log context with user information
        with LogContext(logger, user_id=user_id) as ctx:
            ctx.info(
                "Starting data sync",
                extra={
                    "operation": "start_data_sync",
                    "sync_config": {
                        "source": sync_config.get("source"),
                        "destination": sync_config.get("destination")
                    }
                }
            )

            try:
                # Generate task ID
                task_id = f"sync-{datetime.utcnow().isoformat()}"

                # Create and start the task
                task = asyncio.create_task(
                    self._run_data_sync(task_id, user_id, sync_config)
                )
                self.tasks[task_id] = task

                ctx.info(
                    "Data sync task started",
                    extra={
                        "operation": "start_data_sync",
                        "task_id": task_id,
                        "result": "success"
                    }
                )

                return task_id

            except Exception as e:
                ctx.error(
                    "Failed to start data sync",
                    exc_info=True,
                    extra={
                        "operation": "start_data_sync",
                        "error": str(e)
                    }
                )
                raise

    async def _run_data_sync(
        self,
        task_id: str,
        user_id: str,
        sync_config: Dict[str, Any]
    ) -> None:
        """
        Run the data synchronization task.

        Args:
            task_id: The ID of the task
            user_id: The ID of the user
            sync_config: Configuration for the sync
        """
        # Create log context with user and task information
        with LogContext(logger, user_id=user_id) as ctx:
            ctx.info(
                "Running data sync",
                extra={
                    "operation": "run_data_sync",
                    "task_id": task_id,
                    "sync_config": {
                        "source": sync_config.get("source"),
                        "destination": sync_config.get("destination")
                    }
                }
            )

            try:
                # Simulate sync process
                total_items = 1000
                processed_items = 0

                for i in range(total_items):
                    # Update progress
                    processed_items += 1
                    progress = (processed_items / total_items) * 100

                    # Log progress periodically
                    if i % 100 == 0:
                        ctx.info(
                            "Sync progress update",
                            extra={
                                "operation": "run_data_sync",
                                "task_id": task_id,
                                "progress": progress,
                                "processed_items": processed_items,
                                "total_items": total_items
                            }
                        )

                    # Simulate work
                    await asyncio.sleep(0.01)

                ctx.info(
                    "Data sync completed",
                    extra={
                        "operation": "run_data_sync",
                        "task_id": task_id,
                        "result": "success",
                        "processed_items": processed_items,
                        "total_items": total_items
                    }
                )

            except Exception as e:
                ctx.error(
                    "Data sync failed",
                    exc_info=True,
                    extra={
                        "operation": "run_data_sync",
                        "task_id": task_id,
                        "error": str(e),
                        "processed_items": processed_items,
                        "total_items": total_items
                    }
                )
                raise

    async def get_task_status(
        self,
        task_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get the status of a background task.

        Args:
            task_id: The ID of the task
            user_id: The ID of the user

        Returns:
            Task status information
        """
        # Create log context with user information
        with LogContext(logger, user_id=user_id) as ctx:
            ctx.info(
                "Getting task status",
                extra={
                    "operation": "get_task_status",
                    "task_id": task_id
                }
            )

            try:
                task = self.tasks.get(task_id)

                if not task:
                    ctx.warning(
                        "Task not found",
                        extra={
                            "operation": "get_task_status",
                            "task_id": task_id,
                            "result": "not_found"
                        }
                    )
                    return {"status": "not_found"}

                if task.done():
                    if task.exception():
                        ctx.error(
                            "Task failed",
                            exc_info=True,
                            extra={
                                "operation": "get_task_status",
                                "task_id": task_id,
                                "result": "failed"
                            }
                        )
                        return {"status": "failed"}
                    else:
                        ctx.info(
                            "Task completed successfully",
                            extra={
                                "operation": "get_task_status",
                                "task_id": task_id,
                                "result": "completed"
                            }
                        )
                        return {"status": "completed"}
                else:
                    ctx.info(
                        "Task in progress",
                        extra={
                            "operation": "get_task_status",
                            "task_id": task_id,
                            "result": "in_progress"
                        }
                    )
                    return {"status": "in_progress"}

            except Exception as e:
                ctx.error(
                    "Failed to get task status",
                    exc_info=True,
                    extra={
                        "operation": "get_task_status",
                        "task_id": task_id,
                        "error": str(e)
                    }
                )
                raise
