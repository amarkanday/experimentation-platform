"""
Report schemas for the API.

This module contains Pydantic models for reports and analytics.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from .user import UserBase


class ReportBase(BaseModel):
    """Base model for reports."""
    title: str = Field(..., description="Report title")
    description: Optional[str] = Field(None, description="Detailed description")
    report_type: str = Field(..., description="Type of report (experiment_result, feature_flag_usage, user_activity, custom)")
    is_public: bool = Field(False, description="Whether the report is publicly viewable")
    data: Optional[Dict[str, Any]] = Field(None, description="Stored report data/results")
    query_definition: Optional[Dict[str, Any]] = Field(None, description="Definition of data query")
    visualization_config: Optional[Dict[str, Any]] = Field(None, description="Visualization settings")
    experiment_id: Optional[UUID] = Field(None, description="Associated experiment ID")
    feature_flag_id: Optional[UUID] = Field(None, description="Associated feature flag ID")


class ReportCreate(ReportBase):
    """Model for report creation."""
    pass


class ReportUpdate(BaseModel):
    """Model for report updates."""
    title: Optional[str] = Field(None, description="Report title")
    description: Optional[str] = Field(None, description="Detailed description")
    report_type: Optional[str] = Field(None, description="Type of report")
    is_public: Optional[bool] = Field(None, description="Whether the report is publicly viewable")
    data: Optional[Dict[str, Any]] = Field(None, description="Stored report data/results")
    query_definition: Optional[Dict[str, Any]] = Field(None, description="Definition of data query")
    visualization_config: Optional[Dict[str, Any]] = Field(None, description="Visualization settings")


class ReportInDBBase(ReportBase):
    """Base model for reports in the database."""
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Report(ReportInDBBase):
    """Complete report model."""
    pass


class ReportWithOwner(ReportInDBBase):
    """Report model with owner information."""
    owner: UserBase


class ReportListResponse(BaseModel):
    """Response model for paginated report list."""
    items: List[Report]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Monthly Experiment Results",
                        "description": "Analysis of all experiments run in May",
                        "report_type": "experiment_result",
                        "is_public": False,
                        "created_at": "2023-05-01T00:00:00Z",
                        "updated_at": "2023-05-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100
            }
        }
    )
