# Experiment management endpoints
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.experiment import Experiment
from app.schemas.experiment import ExperimentCreate, ExperimentResponse, ExperimentUpdate
from app.services.experiment_service import ExperimentService

router = APIRouter()


@router.get("/", response_model=List[ExperimentResponse])
def get_experiments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve experiments.
    """
    service = ExperimentService(db)
    experiments = service.get_experiments(skip=skip, limit=limit)
    return experiments


@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    *,
    db: Session = Depends(deps.get_db),
    experiment_in: ExperimentCreate,
) -> Any:
    """
    Create new experiment.
    """
    service = ExperimentService(db)
    experiment = service.create_experiment(obj_in=experiment_in)
    return experiment


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    *,
    db: Session = Depends(deps.get_db),
    experiment_id: str,
) -> Any:
    """
    Get experiment by ID.
    """
    service = ExperimentService(db)
    experiment = service.get_experiment(experiment_id=experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )
    return experiment


@router.put("/{experiment_id}", response_model=ExperimentResponse)
def update_experiment(
    *,
    db: Session = Depends(deps.get_db),
    experiment_id: str,
    experiment_in: ExperimentUpdate,
) -> Any:
    """
    Update experiment.
    """
    service = ExperimentService(db)
    experiment = service.get_experiment(experiment_id=experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )
    experiment = service.update_experiment(
        experiment=experiment, obj_in=experiment_in
    )
    return experiment


@router.post("/{experiment_id}/start", response_model=ExperimentResponse)
def start_experiment(
    *,
    db: Session = Depends(deps.get_db),
    experiment_id: str,
) -> Any:
    """
    Start an experiment.
    """
    service = ExperimentService(db)
    experiment = service.get_experiment(experiment_id=experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )
    experiment = service.start_experiment(experiment=experiment)
    return experiment
