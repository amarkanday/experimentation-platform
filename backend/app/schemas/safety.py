"""
Schemas for safety monitoring and rollback functionality.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from enum import Enum


class HealthStatus(str, Enum):
    """Health status of a safety check."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricThreshold(BaseModel):
    """Threshold configuration for a safety metric."""
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison_type: str = "greater_than"  # "greater_than", "less_than", "equal_to"


class MetricStatus(BaseModel):
    """Status of a metric with its current value and thresholds."""
    name: str
    description: Optional[str] = None
    current_value: float
    threshold: float
    unit: Optional[str] = None
    is_healthy: bool
    details: Optional[Dict[str, Any]] = None


class SafetySettingsBase(BaseModel):
    """Base schema for safety settings."""
    enable_automatic_rollbacks: bool = Field(False, description="Whether to enable automatic rollbacks")
    default_metrics: Optional[Dict[str, MetricThreshold]] = Field(
        None, description="Default metrics to monitor with thresholds"
    )


class SafetySettingsCreate(SafetySettingsBase):
    """Schema for creating safety settings."""
    pass


class SafetySettingsUpdate(SafetySettingsBase):
    """Schema for updating safety settings."""
    pass


class SafetySettingsResponse(SafetySettingsBase):
    """Response schema for safety settings."""
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class FeatureFlagSafetyConfigBase(BaseModel):
    """Base schema for feature flag safety configuration."""
    feature_flag_id: UUID4
    enabled: bool = Field(True, description="Whether safety monitoring is enabled for this feature flag")
    metrics: Dict[str, MetricThreshold] = Field(
        {}, description="Metrics to monitor with thresholds for this feature flag"
    )
    rollback_percentage: int = Field(
        0, description="Percentage to roll back to if automatic rollback is triggered"
    )


class FeatureFlagSafetyConfigCreate(BaseModel):
    """Schema for creating feature flag safety configuration."""
    enabled: bool = Field(True, description="Whether safety monitoring is enabled for this feature flag")
    metrics: Dict[str, MetricThreshold] = Field(
        {}, description="Metrics to monitor with thresholds for this feature flag"
    )
    rollback_percentage: int = Field(
        0, description="Percentage to roll back to if automatic rollback is triggered"
    )


class FeatureFlagSafetyConfigUpdate(BaseModel):
    """Schema for updating feature flag safety configuration."""
    enabled: Optional[bool] = None
    metrics: Optional[Dict[str, MetricThreshold]] = None
    rollback_percentage: Optional[int] = None


class FeatureFlagSafetyConfigResponse(FeatureFlagSafetyConfigBase):
    """Response schema for feature flag safety configuration."""
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class MetricValue(BaseModel):
    """Value of a safety metric."""
    value: float
    status: HealthStatus
    threshold: Optional[MetricThreshold] = None


class SafetyCheckResponse(BaseModel):
    """Response schema for safety check."""
    feature_flag_id: UUID4
    is_healthy: bool
    metrics: List[MetricStatus]
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None


class SafetyRollbackRecordBase(BaseModel):
    """Base schema for safety rollback record."""
    feature_flag_id: UUID4
    trigger_type: str = Field(..., description="Type of trigger: 'automatic', 'manual', 'scheduled'")
    trigger_reason: str = Field(..., description="Reason for the rollback")
    previous_percentage: int
    target_percentage: int


class SafetyRollbackRecordCreate(SafetyRollbackRecordBase):
    """Schema for creating safety rollback record."""
    pass


class SafetyRollbackRecordResponse(SafetyRollbackRecordBase):
    """Response schema for safety rollback record."""
    id: UUID4
    created_at: datetime
    success: bool
    executed_by_user_id: UUID4

    class Config:
        orm_mode = True


class RollbackResponse(BaseModel):
    """Response schema for rollback operation."""
    success: bool
    feature_flag_id: UUID4
    message: str
    trigger_type: Optional[str] = None
    previous_percentage: Optional[int] = None
    new_percentage: Optional[int] = None
    rollback_record_id: Optional[UUID4] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
