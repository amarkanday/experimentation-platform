# Experiment management service
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from backend.app.models.experiment import Experiment, Metric, Variant
from backend.app.schemas.experiment import ExperimentCreate, ExperimentUpdate
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session


class ExperimentService:
    def __init__(self, db: Session):
        self.db = db

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self.db.query(Experiment).filter(Experiment.id == experiment_id).first()

    def get_experiments(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> list[Experiment]:
        """Get all experiments with optional status filter."""
        query = self.db.query(Experiment)
        if status:
            query = query.filter(Experiment.status == status)
        return query.offset(skip).limit(limit).all()

    def create_experiment(self, obj_in: ExperimentCreate) -> Experiment:
        """Create a new experiment."""
        obj_data = jsonable_encoder(obj_in, exclude_unset=True)

        # Extract nested objects
        variants_data = obj_data.pop("variants", [])
        metrics_data = obj_data.pop("metrics", [])

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
        return experiment

    def update_experiment(
        self, experiment: Experiment, obj_in: Union[ExperimentUpdate, dict[str, Any]]
    ) -> Experiment:
        """Update an experiment."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        # Handle nested objects if present
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

        self.db.commit()
        self.db.refresh(experiment)
        return experiment

    def start_experiment(self, experiment: Experiment) -> Experiment:
        """Start an experiment."""
        if experiment.status not in ["DRAFT", "PAUSED"]:
            raise ValueError(
                f"Cannot start experiment with status: {experiment.status}"
            )

        experiment.status = "ACTIVE"
        experiment.start_date = datetime.utcnow()

        self.db.commit()
        self.db.refresh(experiment)
        return experiment
