# backend/app/services/experiment_service.py
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from uuid import UUID

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload
from fastapi.encoders import jsonable_encoder

from backend.app.models.experiment import Experiment, Variant, Metric, ExperimentStatus, ExperimentType, MetricType
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
            .options(joinedload(Experiment.variants), joinedload(Experiment.metric_definitions))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            return None

        return self._experiment_to_dict(experiment)

    def get_experiments(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "created_at",
        sort_order: Optional[str] = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Get all experiments with optional status filter.

        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            status: Optional status filter
            search: Optional search term to filter experiments
            sort_by: Field to sort by (created_at, updated_at, name, status)
            sort_order: Sort order (asc, desc)

        Returns:
            List of experiment dictionaries
        """
        query = self.db.query(Experiment).options(
            joinedload(Experiment.variants), joinedload(Experiment.metric_definitions)
        )

        if status:
            query = query.filter(Experiment.status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Experiment.name.ilike(search_pattern),
                    Experiment.description.ilike(search_pattern),
                    Experiment.tags.contains([search]),  # For JSON array search
                )
            )

        # Apply sorting
        if sort_by and hasattr(Experiment, sort_by):
            sort_field = getattr(Experiment, sort_by)
            if sort_order and sort_order.lower() == "asc":
                query = query.order_by(sort_field.asc())
            else:
                query = query.order_by(sort_field.desc())

        experiments = query.offset(skip).limit(limit).all()
        return [self._experiment_to_dict(exp) for exp in experiments]

    def get_experiments_by_owner(
        self,
        owner_id: Union[str, UUID],
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "created_at",
        sort_order: Optional[str] = "desc",
    ) -> List[Dict[str, Any]]:
        """
        Get experiments owned by a specific user.

        Args:
            owner_id: User ID of the experiment owner
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            status: Optional status filter
            search: Optional search term to filter experiments
            sort_by: Field to sort by (created_at, updated_at, name, status)
            sort_order: Sort order (asc, desc)

        Returns:
            List of experiment dictionaries
        """
        query = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants), joinedload(Experiment.metric_definitions))
            .filter(Experiment.owner_id == owner_id)
        )

        if status:
            query = query.filter(Experiment.status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Experiment.name.ilike(search_pattern),
                    Experiment.description.ilike(search_pattern),
                    Experiment.tags.contains([search]),  # For JSON array search
                )
            )

        # Apply sorting
        if sort_by and hasattr(Experiment, sort_by):
            sort_field = getattr(Experiment, sort_by)
            if sort_order and sort_order.lower() == "asc":
                query = query.order_by(sort_field.asc())
            else:
                query = query.order_by(sort_field.desc())

        experiments = query.offset(skip).limit(limit).all()
        return [self._experiment_to_dict(exp) for exp in experiments]

    def count_experiments_by_owner(
        self, owner_id: Union[str, UUID], status: Optional[str] = None, search: Optional[str] = None
    ) -> int:
        """
        Count experiments owned by a specific user.

        Args:
            owner_id: User ID of the experiment owner
            status: Optional status filter
            search: Optional search term to filter experiments

        Returns:
            Count of experiments matching the criteria
        """
        query = self.db.query(func.count(Experiment.id)).filter(
            Experiment.owner_id == owner_id
        )

        if status:
            query = query.filter(Experiment.status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Experiment.name.ilike(search_pattern),
                    Experiment.description.ilike(search_pattern),
                    Experiment.tags.contains([search]),  # For JSON array search
                )
            )

        return query.scalar()

    def create_experiment(
        self,
        obj_in: Union[ExperimentCreate, Dict[str, Any]],
        user_id: UUID,
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
        # Handle string status values by converting to enum
        if "status" in obj_data and isinstance(obj_data["status"], str):
            try:
                # Convert string status (e.g., "draft") to enum (e.g., ExperimentStatus.DRAFT)
                obj_data["status"] = ExperimentStatus[obj_data["status"].upper()]
            except (KeyError, ValueError):
                # Fallback to default if conversion fails
                obj_data["status"] = ExperimentStatus.DRAFT
        else:
            obj_data["status"] = ExperimentStatus.DRAFT

        # Handle string experiment type values by converting to enum
        if "experiment_type" in obj_data and isinstance(obj_data["experiment_type"], str):
            try:
                # Convert string type (e.g., "a_b") to enum (e.g., ExperimentType.A_B)
                obj_data["experiment_type"] = ExperimentType[obj_data["experiment_type"].upper()]
            except (KeyError, ValueError):
                # Fallback to default if conversion fails
                obj_data["experiment_type"] = ExperimentType.A_B
        else:
            obj_data["experiment_type"] = ExperimentType.A_B

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
            # Handle string metric type values by converting to enum
            if "metric_type" in metric_data and isinstance(metric_data["metric_type"], str):
                try:
                    # Convert string type (e.g., "conversion") to enum (e.g., MetricType.CONVERSION)
                    # Note: We use lowercase since that's how the enum is defined
                    metric_data["metric_type"] = MetricType[metric_data["metric_type"].lower()]
                except (KeyError, ValueError):
                    # Fallback to default if conversion fails
                    metric_data["metric_type"] = MetricType.CONVERSION
            else:
                metric_data["metric_type"] = MetricType.CONVERSION

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

        # Handle string status values by converting to enum
        if "status" in update_data and isinstance(update_data["status"], str):
            try:
                # Convert string status (e.g., "draft") to enum (e.g., ExperimentStatus.DRAFT)
                update_data["status"] = ExperimentStatus[update_data["status"].upper()]
            except (KeyError, ValueError):
                # If conversion fails, keep the existing status
                del update_data["status"]

        # Handle string experiment type values by converting to enum
        if "experiment_type" in update_data and isinstance(update_data["experiment_type"], str):
            try:
                # Convert string type (e.g., "a_b") to enum (e.g., ExperimentType.A_B)
                update_data["experiment_type"] = ExperimentType[update_data["experiment_type"].upper()]
            except (KeyError, ValueError):
                # If conversion fails, keep the existing type
                del update_data["experiment_type"]

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
                # Handle string metric type values by converting to enum
                if "metric_type" in metric_data and isinstance(metric_data["metric_type"], str):
                    try:
                        # Convert string type (e.g., "conversion") to enum (e.g., MetricType.CONVERSION)
                        # Note: We use lowercase since that's how the enum is defined
                        metric_data["metric_type"] = MetricType[metric_data["metric_type"].lower()]
                    except (KeyError, ValueError):
                        # Fallback to default if conversion fails
                        metric_data["metric_type"] = MetricType.CONVERSION
                else:
                    metric_data["metric_type"] = MetricType.CONVERSION

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

    def update_experiment_schedule(
        self,
        experiment: Experiment,
        schedule: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update experiment scheduling configuration.

        Args:
            experiment: Experiment model to update
            schedule: Scheduling configuration containing start_date, end_date, and time_zone

        Returns:
            Dictionary containing the updated experiment data

        Raises:
            ValueError: If scheduling parameters are invalid
        """
        # Validate experiment status
        if experiment.status not in [ExperimentStatus.DRAFT, ExperimentStatus.PAUSED]:
            raise ValueError(
                f"Cannot schedule experiment with status {experiment.status}. "
                f"Experiment must be in DRAFT or PAUSED status."
            )

        # Update experiment schedule
        if "start_date" in schedule:
            experiment.start_date = schedule["start_date"]

        if "end_date" in schedule:
            experiment.end_date = schedule["end_date"]

        # Validate date relationships
        if experiment.start_date and experiment.end_date:
            if experiment.end_date <= experiment.start_date:
                raise ValueError("End date must be after start date")

            # Minimum duration check
            min_duration = timedelta(hours=1)
            if experiment.end_date - experiment.start_date < min_duration:
                raise ValueError(f"Experiment must run for at least {min_duration}")

        # Add timezone metadata if not using UTC
        if "time_zone" in schedule and schedule["time_zone"] != "UTC":
            if not hasattr(experiment, 'metadata') or not experiment.metadata:
                experiment.metadata = {}
            experiment.metadata["time_zone"] = schedule["time_zone"]

        experiment.updated_at = datetime.now(timezone.utc)

        # Save changes
        self.db.commit()
        self.db.refresh(experiment)

        logger.info(
            f"Updated schedule for experiment {experiment.id}: "
            f"start={experiment.start_date}, end={experiment.end_date}"
        )

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
            joinedload(Experiment.variants), joinedload(Experiment.metric_definitions)
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
        Validate that an experiment meets requirements to start.

        Args:
            experiment: Experiment to validate

        Returns:
            Boolean indicating if experiment can be started
        """
        # Check if experiment has variants
        if not experiment.variants or len(experiment.variants) < 2:
            logger.warning(
                f"Experiment {experiment.id} does not have enough variants to start"
            )
            return False

        # Check if experiment has at least one control variant
        has_control = any(variant.is_control for variant in experiment.variants)
        if not has_control:
            logger.warning(
                f"Experiment {experiment.id} does not have a control variant"
            )
            return False

        # Check if experiment has metrics
        if not experiment.metric_definitions or len(experiment.metric_definitions) < 1:
            logger.warning(
                f"Experiment {experiment.id} does not have any metrics defined"
            )
            return False

        # All checks passed
        return True

    def _parse_datetime(self, date_str: str, time_zone: str = "UTC") -> datetime:
        """
        Parse datetime string with time zone awareness.

        Args:
            date_str: Date string in ISO format
            time_zone: Time zone name (default: UTC)

        Returns:
            Timezone-aware datetime object

        Raises:
            ValueError: If the date string is invalid or time zone is unknown
        """
        try:
            # Parse the date string
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            # Convert to UTC for storage
            if time_zone != "UTC":
                import pytz
                try:
                    tz = pytz.timezone(time_zone)
                    dt = tz.localize(dt.replace(tzinfo=None))
                    dt = dt.astimezone(pytz.UTC)
                except Exception as e:
                    logger.warning(f"Unknown time zone: {time_zone}, using UTC. Error: {str(e)}")

            return dt
        except ValueError as e:
            logger.error(f"Error parsing date: {date_str}, {str(e)}")
            raise ValueError(f"Invalid date format: {date_str}")

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
        else:
            result["variants"] = []

        # Add metrics if loaded
        if hasattr(experiment, "metric_definitions") and experiment.metric_definitions is not None:
            result["metrics"] = [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "description": m.description,
                    "event_name": m.event_name,
                    "metric_type": m.metric_type.value if hasattr(m.metric_type, "value") else m.metric_type,
                    "is_primary": m.is_primary,
                    "aggregation_method": m.aggregation_method,
                    "minimum_sample_size": m.minimum_sample_size,
                    "expected_effect": m.expected_effect,
                    "event_value_path": m.event_value_path,
                    "lower_is_better": m.lower_is_better,
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
                for m in experiment.metric_definitions
            ]
        else:
            result["metrics"] = []

        return result

    def count_experiments(
        self, status: Optional[str] = None, search: Optional[str] = None
    ) -> int:
        """
        Count all experiments with optional filters.

        Args:
            status: Optional status filter
            search: Optional search term to filter experiments

        Returns:
            Count of experiments matching the criteria
        """
        query = self.db.query(func.count(Experiment.id))

        if status:
            query = query.filter(Experiment.status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Experiment.name.ilike(search_pattern),
                    Experiment.description.ilike(search_pattern),
                    Experiment.tags.contains([search]),  # For JSON array search
                )
            )

        return query.scalar()
