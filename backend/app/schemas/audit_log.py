"""
Pydantic schemas for audit log operations.

This module defines the request and response schemas for audit log APIs,
providing validation and serialization for audit trail operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from enum import Enum

from backend.app.models.audit_log import ActionType, EntityType


class AuditLogBase(BaseModel):
    """Base schema for audit logs."""

    model_config = ConfigDict(from_attributes=True)

    user_email: str
    action_type: str
    entity_type: str
    entity_id: UUID
    entity_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit logs."""

    user_id: Optional[UUID] = None

    @field_validator('action_type')
    @classmethod
    def validate_action_type(cls, v):
        """Validate action type is a valid ActionType enum value."""
        try:
            ActionType(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid action type: {v}")

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type is a valid EntityType enum value."""
        try:
            EntityType(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid entity type: {v}")


class AuditLogResponse(AuditLogBase):
    """Schema for audit log responses."""

    id: UUID
    user_id: Optional[UUID] = None
    timestamp: datetime
    action_description: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log responses."""

    items: List[AuditLogResponse]
    total: int
    page: int
    limit: int
    total_pages: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        """Initialize and calculate total_pages if not provided."""
        if 'total_pages' not in data:
            total = data.get('total', 0)
            limit = data.get('limit', 50)
            if limit <= 0:
                data['total_pages'] = 0
            else:
                data['total_pages'] = (total + limit - 1) // limit
        super().__init__(**data)


class ToggleRequest(BaseModel):
    """Schema for feature flag toggle requests."""

    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        """Validate reason length if provided."""
        if v is not None and len(v.strip()) == 0:
            return None
        if v is not None and len(v) > 1000:
            raise ValueError("Reason must be 1000 characters or less")
        return v


class ToggleResponse(BaseModel):
    """Schema for feature flag toggle responses."""

    id: UUID
    name: str
    key: str
    status: str
    updated_at: datetime
    audit_log_id: Optional[UUID] = None  # Can be None if audit logging fails

    model_config = ConfigDict(from_attributes=True)


class AuditLogFilterParams(BaseModel):
    """Schema for audit log query parameters."""

    user_id: Optional[UUID] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    action_type: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = 1
    limit: int = 50

    model_config = ConfigDict(from_attributes=True)

    @field_validator('page')
    @classmethod
    def validate_page(cls, v):
        """Validate page number is positive."""
        if v < 1:
            raise ValueError("Page number must be 1 or greater")
        return v

    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        """Validate limit is within acceptable range."""
        if v < 1 or v > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        return v

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type if provided."""
        if v is not None:
            try:
                EntityType(v)
                return v
            except ValueError:
                raise ValueError(f"Invalid entity type: {v}")
        return v

    @field_validator('action_type')
    @classmethod
    def validate_action_type(cls, v):
        """Validate action type if provided."""
        if v is not None:
            try:
                ActionType(v)
                return v
            except ValueError:
                raise ValueError(f"Invalid action type: {v}")
        return v

    @model_validator(mode='after')
    def validate_date_range(self):
        """Validate that to_date is after from_date if both are provided."""
        if self.to_date is not None and self.from_date is not None and self.to_date <= self.from_date:
            raise ValueError("to_date must be after from_date")
        return self


class AuditStatsResponse(BaseModel):
    """Schema for audit statistics response."""

    total_logs: int
    action_counts: Dict[str, int]
    entity_counts: Dict[str, int]
    most_active_users: Dict[str, int]
    date_range: Dict[str, Optional[str]]

    model_config = ConfigDict(from_attributes=True)