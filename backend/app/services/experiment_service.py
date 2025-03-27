# backend/app/services/experiment_service.py
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
from uuid import UUID

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload
from fastapi.encoders import jsonable_encoder

from backend.app.models.experiment import Experiment, Variant, Metric, ExperimentStatus
from backend.app.models.user import User
from backend.app.schemas.experiment import ExperimentCreate, ExperimentUpdate


logger = logging.getLogger(__name__)


class ExperimentService:
    """
    Service for managing experiments, including creation, retrieval, updates, and status changes.

    This service provides the business logic for experiment operations, including:
    - Creating new experiments with variants and metrics
    - Retrieving experiments with filtering options
    - Updating experiment details and components
    - Managing experiment lifecycle (start, pause, complete, archive)
    - Access control and permission handling
    """

    def __init__(self, db: Session):
        """Initialize with a database session."""
        self.db = db

    def get_experiment_by_id(
        self, experiment_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        Get an experiment by ID with its variants and metrics.

        Args:
            experiment_id: The unique identifier of the experiment

        Returns:
            Dict containing the experiment data or None if not found
        """
        experiment = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants), joinedload(Experiment.metrics))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            return None

        return self._experiment_to_dict(experiment)

    def get_experiments(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all experiments with optional status filter.

        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of experiment dictionaries
        """
        query = self.db.query(Experiment).options(
            joinedload(Experiment.variants), joinedload(Experiment.metrics)
        )

        if status:
            query = query.filter(Experiment.status == status)

        experiments = query.offset(skip).limit(limit).all()
        return [self._experiment_to_dict(exp) for exp in experiments]

    def get_experiments_by_owner(
        self,
        owner_id: Union[str, UUID],
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get experiments owned by a specific user.

        Args:
            owner_id: User ID of the experiment owner
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of experiment dictionaries
        """
        query = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants), joinedload(Experiment.metrics))
            .filter(Experiment.owner_id == owner_id)
        )

        if status:
            query = query.filter(Experiment.status == status)

        experiments = query.offset(skip).limit(limit).all()
        return [self._experiment_to_dict(exp) for exp in experiments]

    def count_experiments_by_owner(
        self, owner_id: Union[str, UUID], status: Optional[str] = None
    ) -> int:
        """
        Count experiments owned by a specific user.

        Args:
            owner_id: User ID of the experiment owner
            status: Optional status filter

        Returns:
            Count of experiments matching the criteria
        """
        query = self.db.query(func.count(Experiment.id)).filter(
            Experiment.owner_id == owner_id
        )

        if status:
            query = query.filter(Experiment.status == status)

        return query.scalar()

    def create_experiment(
        self, obj_in: ExperimentCreate, user_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """
        Create a new experiment with variants and metrics.

        Args:
            obj_in: Experiment creation data schema
            user_id: ID of the user creating the experiment

        Returns:
            Dictionary containing the created experiment data
        """
        # Extract data from the schema, excluding unset values
        obj_data = jsonable_encoder(obj_in, exclude_unset=True)

        # Extract nested objects
        variants_data = obj_data.pop("variants", [])
        metrics_data = obj_data.pop("metrics", [])

        # Set default values and owner
        obj_data["status"] = ExperimentStatus.DRAFT.value
        obj_data["owner_id"] = str(user_id)

        # Create experiment
        experiment = Experiment(**obj_data)
        self.db.add(experiment)
        self.db.flush()  # Flush to get the experiment ID

        # Create variants
        for variant_data in variants_data:
            variant = Variant(**variant_data, experiment_id=experiment.id)
            self.db.add(variant)

        # Create metrics
        for metric_data in metrics_data:
            metric = Metric(**metric_data, experiment_id=experiment.id)
            self.db.add(metric)

        self.db.commit()
        self.db.refresh(experiment)

        logger.info(f"Created experiment {experiment.id}: {experiment.name}")
        return self._experiment_to_dict(experiment)

    def update_experiment(
        self,
        experiment: Experiment,
        experiment_in: Union[ExperimentUpdate, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Update an existing experiment.

        Args:
            experiment: Experiment model object to update
            experiment_in: Update data schema or dictionary

        Returns:
            Dictionary containing the updated experiment data
        """
        # Convert to dict if it's a schema
        if isinstance(experiment_in, dict):
            update_data = experiment_in
        else:
            update_data = experiment_in.dict(exclude_unset=True)

        # Extract nested objects if present
        variants_data = update_data.pop("variants", None)
        metrics_data = update_data.pop("metrics", None)

        # Update experiment attributes
        for field in update_data:
            if hasattr(experiment, field):
                setattr(experiment, field, update_data[field])

        # Handle variants update if provided
        if variants_data is not None:
            # Remove existing variants
            for variant in experiment.variants:
                self.db.delete(variant)

            # Create new variants
            for variant_data in variants_data:
                variant = Variant(**variant_data, experiment_id=experiment.id)
                self.db.add(variant)

        # Handle metrics update if provided
        if metrics_data is not None:
            # Remove existing metrics
            for metric in experiment.metrics:
                self.db.delete(metric)

            # Create new metrics
            for metric_data in metrics_data:
                metric = Metric(**metric_data, experiment_id=experiment.id)
                self.db.add(metric)

        # Update timestamp
        experiment.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(experiment)

        logger.info(f"Updated experiment {experiment.id}: {experiment.name}")
        return self._experiment_to_dict(experiment)

    def start_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """
        Start an experiment by changing its status to ACTIVE.

        Args:
            experiment: Experiment model object to start

        Returns:
            Dictionary containing the updated experiment data

        Raises:
            ValueError: If the experiment cannot be started
        """
        # Validate experiment status
        if experiment.status not in [ExperimentStatus.DRAFT, ExperimentStatus.PAUSED]:
            raise ValueError(
                f"Cannot start experiment with status: {experiment.status}"
            )

        # Validate experiment has required components
        if not self._validate_experiment_for_start(experiment):
            raise ValueError("Experiment does not meet requirements to start")

        # Update status and start date
        experiment.status = ExperimentStatus.ACTIVE
        if not experiment.start_date:
            experiment.start_date = datetime.now(timezone.utc).isoformat()

        experiment.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(experiment)

        logger.info(f"Started experiment {experiment.id}: {experiment.name}")
        return self._experiment_to_dict(experiment)

    def pause_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """
        Pause an active experiment.

        Args:
            experiment: Experiment model object to pause

        Returns:
            Dictionary containing the updated experiment data

        Raises:
            ValueError: If the experiment cannot be paused
        """
        if experiment.status != ExperimentStatus.ACTIVE:
            raise ValueError(
                f"Cannot pause experiment with status: {experiment.status}"
            )

        experiment.status = ExperimentStatus.PAUSED
        experiment.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(experiment)

        logger.info(f"Paused experiment {experiment.id}: {experiment.name}")
        return self._experiment_to_dict(experiment)

    def complete_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """
        Mark an experiment as completed.

        Args:
            experiment: Experiment model object to complete

        Returns:
            Dictionary containing the updated experiment data

        Raises:
            ValueError: If the experiment cannot be completed
        """
        if experiment.status not in [ExperimentStatus.ACTIVE, ExperimentStatus.PAUSED]:
            raise ValueError(
                f"Cannot complete experiment with status: {experiment.status}"
            )

        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_date = datetime.now(timezone.utc).isoformat()
        experiment.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(experiment)

        logger.info(f"Completed experiment {experiment.id}: {experiment.name}")
        return self._experiment_to_dict(experiment)

    def archive_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """
        Archive an experiment.

        Args:
            experiment: Experiment model object to archive

        Returns:
            Dictionary containing the updated experiment data
        """
        experiment.status = ExperimentStatus.ARCHIVED
        experiment.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(experiment)

        logger.info(f"Archived experiment {experiment.id}: {experiment.name}")
        return self._experiment_to_dict(experiment)

    def delete_experiment(self, experiment: Experiment) -> None:
        """
        Delete an experiment and all related data.

        Args:
            experiment: Experiment model object to delete
        """
        # Get experiment ID for logging
        experiment_id = str(experiment.id)
        experiment_name = experiment.name

        # Delete the experiment (cascades to variants and metrics)
        self.db.delete(experiment)
        self.db.commit()

        logger.info(f"Deleted experiment {experiment_id}: {experiment_name}")

    def clone_experiment(
        self, experiment: Experiment, user_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """
        Create a clone of an existing experiment.

        Args:
            experiment: Experiment model object to clone
            user_id: ID of the user creating the clone

        Returns:
            Dictionary containing the cloned experiment data
        """
        # Create new experiment object with copied data
        new_experiment = Experiment(
            name=f"Copy of {experiment.name}",
            description=experiment.description,
            hypothesis=experiment.hypothesis,
            experiment_type=experiment.experiment_type,
            targeting_rules=experiment.targeting_rules,
            status=ExperimentStatus.DRAFT,
            owner_id=str(user_id),
            tags=experiment.tags,
        )

        self.db.add(new_experiment)
        self.db.flush()  # Flush to get the new experiment ID

        # Clone variants
        for variant in experiment.variants:
            new_variant = Variant(
                name=variant.name,
                description=variant.description,
                is_control=variant.is_control,
                traffic_allocation=variant.traffic_allocation,
                configuration=variant.configuration,
                experiment_id=new_experiment.id,
            )
            self.db.add(new_variant)

        # Clone metrics
        for metric in experiment.metrics:
            new_metric = Metric(
                name=metric.name,
                description=metric.description,
                event_name=metric.event_name,
                event_type=metric.event_type,
                experiment_id=new_experiment.id,
            )
            self.db.add(new_metric)

        self.db.commit()
        self.db.refresh(new_experiment)

        logger.info(
            f"Cloned experiment {experiment.id} to {new_experiment.id}: {new_experiment.name}"
        )
        return self._experiment_to_dict(new_experiment)

    def check_experiment_access(
        self, experiment_id: Union[str, UUID], user_id: Union[str, UUID]
    ) -> Tuple[bool, Optional[Experiment]]:
        """
        Check if a user has access to an experiment.

        Args:
            experiment_id: Experiment ID to check
            user_id: User ID to check access for

        Returns:
            Tuple containing (has_access, experiment)
        """
        experiment = (
            self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
        )

        if not experiment:
            return False, None

        # Check if user is owner or has access rights
        has_access = str(experiment.owner_id) == str(user_id)

        return has_access, experiment

    def search_experiments(
        self,
        search_term: str,
        owner_id: Optional[Union[str, UUID]] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search experiments by name, description, or tags.

        Args:
            search_term: Text to search for
            owner_id: Optional filter by owner
            status: Optional filter by status
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            List of matching experiment dictionaries
        """
        # Basic search query
        query = self.db.query(Experiment).options(
            joinedload(Experiment.variants), joinedload(Experiment.metrics)
        )

        # Add search conditions
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Experiment.name.ilike(search_pattern),
                    Experiment.description.ilike(search_pattern),
                    Experiment.tags.contains([search_term]),  # For JSON array search
                )
            )

        # Add optional filters
        if owner_id:
            query = query.filter(Experiment.owner_id == owner_id)

        if status:
            query = query.filter(Experiment.status == status)

        # Execute query with pagination
        experiments = query.offset(skip).limit(limit).all()
        return [self._experiment_to_dict(exp) for exp in experiments]

    def count_search_results(
        self,
        search_term: str,
        owner_id: Optional[Union[str, UUID]] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Count search results for pagination.

        Args:
            search_term: Text to search for
            owner_id: Optional filter by owner
            status: Optional filter by status

        Returns:
            Count of matching experiments
        """
        # Basic count query
        query = self.db.query(func.count(Experiment.id))

        # Add search conditions
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Experiment.name.ilike(search_pattern),
                    Experiment.description.ilike(search_pattern),
                    Experiment.tags.contains([search_term]),  # For JSON array search
                )
            )

        # Add optional filters
        if owner_id:
            query = query.filter(Experiment.owner_id == owner_id)

        if status:
            query = query.filter(Experiment.status == status)

        return query.scalar()

    def _validate_experiment_for_start(self, experiment: Experiment) -> bool:
        """
        Validate that an experiment meets requirements to be started.

        Args:
            experiment: Experiment model object to validate

        Returns:
            True if experiment is valid to start, False otherwise
        """
        # Ensure experiment has variants
        if not experiment.variants or len(experiment.variants) < 2:
            logger.warning(
                f"Experiment {experiment.id} cannot start: needs at least 2 variants"
            )
            return False

        # Ensure experiment has a control variant
        has_control = any(v.is_control for v in experiment.variants)
        if not has_control:
            logger.warning(
                f"Experiment {experiment.id} cannot start: needs a control variant"
            )
            return False

        # Ensure experiment has metrics
        if not experiment.metrics or len(experiment.metrics) < 1:
            logger.warning(
                f"Experiment {experiment.id} cannot start: needs at least 1 metric"
            )
            return False

        # Ensure total traffic allocation adds up to 100%
        total_allocation = sum(v.traffic_allocation for v in experiment.variants)
        if total_allocation != 100:
            logger.warning(
                f"Experiment {experiment.id} cannot start: traffic allocation {total_allocation}% ≠ 100%"
            )
            return False

        return True

    def _experiment_to_dict(self, experiment: Experiment) -> Dict[str, Any]:
        """
        Convert an experiment model to a dictionary for API responses.

        Args:
            experiment: Experiment model object

        Returns:
            Dictionary representation of the experiment
        """
        # Convert the experiment to a dictionary
        result = {
            "id": str(experiment.id),
            "name": experiment.name,
            "description": experiment.description,
            "hypothesis": experiment.hypothesis,
            "status": (
                experiment.status.value
                if hasattr(experiment.status, "value")
                else experiment.status
            ),
            "experiment_type": experiment.experiment_type,
            "targeting_rules": experiment.targeting_rules,
            "owner_id": str(experiment.owner_id),
            "created_at": (
                experiment.created_at.isoformat()
                if hasattr(experiment.created_at, "isoformat")
                else experiment.created_at
            ),
            "updated_at": (
                experiment.updated_at.isoformat()
                if hasattr(experiment.updated_at, "isoformat")
                else experiment.updated_at
            ),
            "start_date": experiment.start_date,
            "end_date": experiment.end_date,
            "tags": experiment.tags or [],
        }

        # Add variants if loaded
        if hasattr(experiment, "variants") and experiment.variants is not None:
            result["variants"] = [
                {
                    "id": str(v.id),
                    "name": v.name,
                    "description": v.description,
                    "is_control": v.is_control,
                    "traffic_allocation": v.traffic_allocation,
                    "configuration": v.configuration,
                    "experiment_id": str(v.experiment_id),
                    "created_at": (
                        v.created_at.isoformat()
                        if hasattr(v.created_at, "isoformat")
                        else v.created_at
                    ),
                    "updated_at": (
                        v.updated_at.isoformat()
                        if hasattr(v.updated_at, "isoformat")
                        else v.updated_at
                    ),
                }
                for v in experiment.variants
            ]

        # Add metrics if loaded
        if hasattr(experiment, "metrics") and experiment.metrics is not None:
            result["metrics"] = [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "description": m.description,
                    "event_name": m.event_name,
                    "event_type": m.event_type,
                    "experiment_id": str(m.experiment_id),
                    "created_at": (
                        m.created_at.isoformat()
                        if hasattr(m.created_at, "isoformat")
                        else m.created_at
                    ),
                    "updated_at": (
                        m.updated_at.isoformat()
                        if hasattr(m.updated_at, "isoformat")
                        else m.updated_at
                    ),
                }
                for m in experiment.metrics
            ]

        return result
