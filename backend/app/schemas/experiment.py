# Experiment Pydantic schemas
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Variant schemas
class VariantBase(BaseModel):
    name: str
    description: Optional[str] = None
    allocation: int = Field(50, ge=0, le=100)


class VariantCreate(VariantBase):
    pass


class VariantUpdate(VariantBase):
    name: Optional[str] = None
    allocation: Optional[int] = None


class VariantInDBBase(VariantBase):
    id: UUID
    experiment_id: UUID

    class Config:
        orm_mode = True


class Variant(VariantInDBBase):
    pass


# Metric schemas
class MetricBase(BaseModel):
    name: str
    description: Optional[str] = None
    event_name: str


class MetricCreate(MetricBase):
    pass


class MetricUpdate(MetricBase):
    name: Optional[str] = None
    event_name: Optional[str] = None


class MetricInDBBase(MetricBase):
    id: UUID
    experiment_id: UUID

    class Config:
        orm_mode = True


class Metric(MetricInDBBase):
    pass


# Experiment schemas
class ExperimentBase(BaseModel):
    name: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    status: str = "DRAFT"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ExperimentCreate(ExperimentBase):
    variants: Optional[List[VariantCreate]] = None
    metrics: Optional[List[MetricCreate]] = None


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    variants: Optional[List[VariantCreate]] = None
    metrics: Optional[List[MetricCreate]] = None


class ExperimentInDBBase(ExperimentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ExperimentResponse(ExperimentInDBBase):
    variants: List[Variant] = []
    metrics: List[Metric] = []
