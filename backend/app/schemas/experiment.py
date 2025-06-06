"""
Experiment schema models for validation and serialization.

This module defines Pydantic models for experiment-related data structures.
These models are used for request/response validation and documentation.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    UUID4,
)


class ExperimentStatus(str, Enum):
    """Experiment status enum."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ExperimentType(str, Enum):
    """Types of experiments."""

    A_B = "a_b"  # Simple A/B test
    MULTIVARIATE = "mv"  # Test with multiple variants
    SPLIT_URL = "split_url"  # Split test with different URLs
    BANDIT = "bandit"  # Multi-armed bandit


class MetricType(str, Enum):
    """Types of metrics."""

    CONVERSION = "conversion"  # Binary conversion event
    REVENUE = "revenue"  # Revenue/monetary value
    COUNT = "count"  # Event count
    DURATION = "duration"  # Time duration
    CUSTOM = "custom"  # Custom metric


class ScheduleConfig(BaseModel):
    """Configuration for experiment scheduling."""

    start_date: Optional[datetime] = Field(
        None,
        description="Date and time when experiment should automatically start"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="Date and time when experiment should automatically complete"
    )
    time_zone: str = Field(
        "UTC",
        description="Time zone for interpreting dates"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2023-12-01T00:00:00Z",
                "end_date": "2023-12-31T23:59:59Z",
                "time_zone": "UTC"
            }
        }
    )

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate that start_date is in the future if provided."""
        if v and v < datetime.now(timezone.utc) - timedelta(minutes=10):  # Allow small buffer
            raise ValueError("Start date must be in the future")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "ScheduleConfig":
        """Validate date relationships."""
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")

        # Minimum duration check
        if self.start_date and self.end_date:
            min_duration = timedelta(hours=1)
            if self.end_date - self.start_date < min_duration:
                raise ValueError(f"Experiment must run for at least {min_duration}")

        return self


class MetricBase(BaseModel):
    """Base model for metric data."""

    name: str = Field(..., min_length=1, max_length=100, description="Metric name")
    description: Optional[str] = Field(None, description="Metric description")
    event_name: str = Field(
        ..., min_length=1, max_length=100, description="Event name to track"
    )
    metric_type: MetricType = Field(MetricType.CONVERSION, description="Type of metric")
    is_primary: bool = Field(False, description="Whether this is the primary metric")
    aggregation_method: str = Field(
        "average", description="How to aggregate the metric"
    )
    minimum_sample_size: int = Field(
        100, ge=10, description="Minimum sample size for statistical significance"
    )
    expected_effect: Optional[float] = Field(
        None, description="Expected effect size for power calculations"
    )
    event_value_path: Optional[str] = Field(
        None, description="JSON path to extract value from event payload"
    )
    lower_is_better: bool = Field(False, description="Whether lower values are better")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Purchase Conversion",
                "description": "Percentage of users who complete a purchase",
                "event_name": "purchase_completed",
                "metric_type": "conversion",
                "is_primary": True,
                "aggregation_method": "average",
                "minimum_sample_size": 200,
                "expected_effect": 0.05,
                "event_value_path": "value",
                "lower_is_better": False,
            }
        }
    )


class VariantBase(BaseModel):
    """Base model for variant data."""

    name: str = Field(..., min_length=1, max_length=100, description="Variant name")
    description: Optional[str] = Field(None, description="Variant description")
    is_control: bool = Field(False, description="Whether this is the control variant")
    traffic_allocation: int = Field(
        50,
        ge=0,
        le=100,
        description="Percentage of traffic to allocate to this variant",
    )
    configuration: Optional[Dict[str, Any]] = Field(
        None, description="Variant-specific configuration"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Treatment A",
                "description": "New button design",
                "is_control": False,
                "traffic_allocation": 50,
                "configuration": {"button_color": "blue", "button_text": "Buy Now"},
            }
        }
    )

    @field_validator("traffic_allocation")
    @classmethod
    def validate_traffic_allocation(cls, v: int) -> int:
        """Validate traffic allocation percentage."""
        if v < 0 or v > 100:
            raise ValueError("Traffic allocation must be between 0 and 100")
        return v


class ExperimentBase(BaseModel):
    """Base model for experiment data."""

    name: str = Field(..., min_length=1, max_length=100, description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    hypothesis: Optional[str] = Field(None, description="Experiment hypothesis")
    experiment_type: ExperimentType = Field(
        ExperimentType.A_B, description="Type of experiment"
    )
    targeting_rules: Optional[Dict[str, Any]] = Field(
        None, description="Rules for targeting users"
    )
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")


class ExperimentCreate(ExperimentBase):
    """Model for creating a new experiment."""

    status: ExperimentStatus = Field(
        ExperimentStatus.DRAFT, description="Initial experiment status"
    )
    variants: List[VariantBase] = Field(
        ..., min_length=1, description="Experiment variants"
    )
    metrics: List[MetricBase] = Field(..., min_length=1, description="Metrics to track")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Button Color Test",
                "description": "Testing different button colors on the checkout page",
                "hypothesis": "Changing the button color to blue will increase conversion rates",
                "experiment_type": "a_b",
                "status": "draft",
                "targeting_rules": {
                    "country": ["US", "CA"],
                    "device": ["desktop", "mobile"],
                },
                "tags": ["checkout", "ui", "conversion"],
                "variants": [
                    {
                        "name": "Control",
                        "description": "Current green button",
                        "is_control": True,
                        "traffic_allocation": 50,
                        "configuration": {"button_color": "green"},
                    },
                    {
                        "name": "Treatment",
                        "description": "New blue button",
                        "is_control": False,
                        "traffic_allocation": 50,
                        "configuration": {"button_color": "blue"},
                    },
                ],
                "metrics": [
                    {
                        "name": "Conversion Rate",
                        "description": "Percentage of users who complete a purchase",
                        "event_name": "purchase",
                        "metric_type": "conversion",
                        "is_primary": True,
                    },
                    {
                        "name": "Average Order Value",
                        "description": "Average value of completed orders",
                        "event_name": "purchase",
                        "metric_type": "revenue",
                        "is_primary": False,
                        "event_value_path": "order_value",
                    },
                ],
            }
        }
    )

    @model_validator(mode="after")
    def validate_variants(self):
        """Validate that there is at least one control variant."""
        if not any(variant.is_control for variant in self.variants):
            raise ValueError("At least one variant must be marked as control")

        # Check that traffic allocations sum to 100
        total_allocation = sum(variant.traffic_allocation for variant in self.variants)
        if total_allocation != 100:
            raise ValueError(
                f"Traffic allocations must sum to 100% (currently {total_allocation}%)"
            )

        return self


class ExperimentUpdate(BaseModel):
    """Model for updating an experiment."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Experiment name"
    )
    description: Optional[str] = Field(None, description="Experiment description")
    hypothesis: Optional[str] = Field(None, description="Experiment hypothesis")
    status: Optional[ExperimentStatus] = Field(None, description="Experiment status")
    experiment_type: Optional[ExperimentType] = Field(
        None, description="Type of experiment"
    )
    targeting_rules: Optional[Dict[str, Any]] = Field(
        None, description="Rules for targeting users"
    )
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    variants: Optional[List[VariantBase]] = Field(
        None, description="Experiment variants"
    )
    metrics: Optional[List[MetricBase]] = Field(None, description="Metrics to track")
    schedule: Optional[ScheduleConfig] = Field(
        None, description="Scheduling configuration for automatic activation/completion"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Button Color Test",
                "description": "Testing different button colors with updated hypothesis",
                "hypothesis": "Changing the button color to dark blue will increase conversion rates",
                "status": "draft",
                "tags": ["checkout", "ui", "conversion", "updated"],
            }
        }
    )

    @model_validator(mode="after")
    def validate_variants(self):
        """Validate variants if provided."""
        if self.variants is not None:
            if not any(variant.is_control for variant in self.variants):
                raise ValueError("At least one variant must be marked as control")

            # Check that traffic allocations sum to 100
            total_allocation = sum(variant.traffic_allocation for variant in self.variants)
            if total_allocation != 100:
                raise ValueError(
                    f"Traffic allocations must sum to 100% (currently {total_allocation}%)"
                )

        return self


class VariantResponse(BaseModel):
    """Model for variant response data."""

    id: UUID4
    name: str
    description: Optional[str] = None
    is_control: bool
    traffic_allocation: int
    configuration: Optional[Dict[str, Any]] = None
    experiment_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MetricResponse(BaseModel):
    """Model for metric response data."""

    id: UUID4
    name: str
    description: Optional[str] = None
    event_name: str
    metric_type: str
    is_primary: bool
    aggregation_method: str
    minimum_sample_size: int
    expected_effect: Optional[float] = None
    event_value_path: Optional[str] = None
    lower_is_better: bool
    experiment_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentResponse(BaseModel):
    """Model for experiment response data."""

    id: UUID4
    name: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    experiment_type: str
    status: str
    targeting_rules: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    owner_id: UUID4
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    variants: List[VariantResponse]
    metrics: List[MetricResponse]

    model_config = ConfigDict(from_attributes=True)


class ExperimentListResponse(BaseModel):
    """Model for paginated experiment list response."""

    items: List[ExperimentResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Button Color Test",
                        "description": "Testing different button colors",
                        "status": "active",
                        "total_users": 1000,
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100
            }
        }
    )


class ExperimentResultMetric(BaseModel):
    """Model for experiment result metric data."""

    name: str
    control_value: float
    variant_values: Dict[str, float]
    differences: Dict[str, float]  # Difference from control
    p_values: Dict[str, float]  # Statistical significance
    significant: Dict[str, bool]  # Is the difference statistically significant
    confidence_intervals: Dict[str, List[float]]  # 95% confidence intervals

    model_config = ConfigDict(from_attributes=True)


class ExperimentResults(BaseModel):
    """Model for experiment results."""

    experiment_id: UUID4
    experiment_name: str
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    metrics: List[ExperimentResultMetric]
    sample_sizes: Dict[str, int]
    conclusion: Optional[str] = None
    recommended_variant: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_id": "123e4567-e89b-12d3-a456-426614174000",
                "experiment_name": "Button Color Test",
                "status": "completed",
                "start_date": "2023-01-01T00:00:00Z",
                "end_date": "2023-01-15T00:00:00Z",
                "metrics": [
                    {
                        "name": "Conversion Rate",
                        "control_value": 0.10,
                        "variant_values": {"Treatment": 0.12},
                        "differences": {"Treatment": 0.02},
                        "p_values": {"Treatment": 0.03},
                        "significant": {"Treatment": True},
                        "confidence_intervals": {"Treatment": [0.01, 0.03]}
                    }
                ],
                "sample_sizes": {"Control": 5000, "Treatment": 5000},
                "conclusion": "The blue button significantly improved conversion rates by 20%",
                "recommended_variant": "Treatment"
            }
        }
    )
