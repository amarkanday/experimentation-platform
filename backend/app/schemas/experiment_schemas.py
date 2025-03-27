from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# Base Experiment model
class ExperimentBase(BaseModel):
    """Base schema for experiment data."""

    key: str
    name: str
    description: Optional[str] = None
    is_active: bool = True


# Experiment create schema (used for creating new experiments)
class ExperimentCreate(ExperimentBase):
    """Schema for creating a new experiment."""

    pass


# Experiment update schema (all fields optional for partial updates)
class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""

    key: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# Experiment DB schema (used for responses, includes DB-generated fields)
class ExperimentInDB(ExperimentBase):
    """Schema for experiment data from database."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        orm_mode = True


# Public experiment schema (for API responses)
class ExperimentResponse(ExperimentInDB):
    """Schema for experiment API responses."""

    pass


# Simple experiment schema (minimal information)
class ExperimentSimple(BaseModel):
    """Simplified experiment schema."""

    id: UUID
    key: str
    name: str
    is_active: bool

    class Config:
        """Pydantic configuration."""

        orm_mode = True


# List of experiments response
class ExperimentListResponse(BaseModel):
    """Schema for listing experiments."""

    experiments: List[ExperimentSimple]
    total: int
