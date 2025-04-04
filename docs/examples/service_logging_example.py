"""
Example of structured logging in service layer.

This example demonstrates how to use the logging system in service layer code.
"""

import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger, LogContext
from backend.app.models.user import User
from backend.app.models.experiment import Experiment

logger = get_logger(__name__)

class ExperimentService:
    """Service for managing experiments with structured logging."""

    def __init__(self, db: Session):
        """Initialize the service."""
        self.db = db

    def create_experiment(
        self,
        experiment_data: Dict[str, Any],
        current_user: User
    ) -> Experiment:
        """
        Create a new experiment with structured logging.

        Args:
            experiment_data: The experiment data to create
            current_user: The user creating the experiment

        Returns:
            The created experiment

        Raises:
            ValueError: If experiment creation fails
        """
        # Create log context with user information
        with LogContext(logger, user_id=current_user.id) as ctx:
            ctx.info(
                "Creating new experiment",
                extra={
                    "operation": "create_experiment",
                    "experiment_data": {
                        "name": experiment_data.get("name"),
                        "description": experiment_data.get("description")
                    }
                }
            )

            try:
                # Start timing the operation
                start_time = time.time()

                # Create experiment
                experiment = Experiment(
                    name=experiment_data["name"],
                    description=experiment_data.get("description"),
                    owner_id=current_user.id
                )
                self.db.add(experiment)
                self.db.commit()

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                ctx.info(
                    "Experiment created successfully",
                    extra={
                        "operation": "create_experiment",
                        "experiment_id": str(experiment.id),
                        "duration_ms": duration_ms,
                        "result": "success"
                    }
                )

                return experiment

            except Exception as e:
                ctx.error(
                    "Failed to create experiment",
                    exc_info=True,
                    extra={
                        "operation": "create_experiment",
                        "error": str(e)
                    }
                )
                raise ValueError("Failed to create experiment")

    def get_experiment(
        self,
        experiment_id: str,
        current_user: User
    ) -> Optional[Experiment]:
        """
        Get an experiment with structured logging.

        Args:
            experiment_id: The ID of the experiment to retrieve
            current_user: The user requesting the experiment

        Returns:
            The experiment if found, None otherwise
        """
        # Create log context with user information
        with LogContext(logger, user_id=current_user.id) as ctx:
            ctx.info(
                "Fetching experiment",
                extra={
                    "operation": "get_experiment",
                    "experiment_id": experiment_id
                }
            )

            try:
                # Start timing the operation
                start_time = time.time()

                # Get experiment
                experiment = self.db.query(Experiment).filter(
                    Experiment.id == experiment_id
                ).first()

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                if experiment:
                    ctx.info(
                        "Experiment found",
                        extra={
                            "operation": "get_experiment",
                            "experiment_id": experiment_id,
                            "duration_ms": duration_ms,
                            "result": "success"
                        }
                    )
                else:
                    ctx.warning(
                        "Experiment not found",
                        extra={
                            "operation": "get_experiment",
                            "experiment_id": experiment_id,
                            "duration_ms": duration_ms,
                            "result": "not_found"
                        }
                    )

                return experiment

            except Exception as e:
                ctx.error(
                    "Failed to fetch experiment",
                    exc_info=True,
                    extra={
                        "operation": "get_experiment",
                        "experiment_id": experiment_id,
                        "error": str(e)
                    }
                )
                raise

    def list_experiments(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100
    ) -> List[Experiment]:
        """
        List experiments with structured logging.

        Args:
            current_user: The user requesting the experiments
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of experiments
        """
        # Create log context with user information
        with LogContext(logger, user_id=current_user.id) as ctx:
            ctx.info(
                "Listing experiments",
                extra={
                    "operation": "list_experiments",
                    "skip": skip,
                    "limit": limit
                }
            )

            try:
                # Start timing the operation
                start_time = time.time()

                # Get experiments
                experiments = self.db.query(Experiment).filter(
                    Experiment.owner_id == current_user.id
                ).offset(skip).limit(limit).all()

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                ctx.info(
                    "Experiments listed successfully",
                    extra={
                        "operation": "list_experiments",
                        "count": len(experiments),
                        "duration_ms": duration_ms,
                        "result": "success"
                    }
                )

                return experiments

            except Exception as e:
                ctx.error(
                    "Failed to list experiments",
                    exc_info=True,
                    extra={
                        "operation": "list_experiments",
                        "error": str(e)
                    }
                )
                raise
