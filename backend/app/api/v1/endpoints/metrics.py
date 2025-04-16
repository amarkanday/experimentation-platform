"""
Metrics API endpoints.

This module provides API endpoints for retrieving metrics related to
feature flag evaluations, performance, and errors.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.services.metrics_service import MetricsService
from backend.app.schemas.metrics import (
    MetricsSummary,
    AggregatedMetricResponse,
    ErrorLogResponse,
    MetricsFilterParams,
    AggregationPeriod,
    MetricType,
)

router = APIRouter()


@router.get(
    "/summary",
    response_model=MetricsSummary,
    summary="Get metrics summary",
    description="Get summary statistics for feature flag metrics.",
)
def get_metrics_summary(
    feature_flag_id: Optional[UUID] = Query(None, description="Filter by feature flag ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    period: AggregationPeriod = Query(
        AggregationPeriod.DAY, description="Aggregation period"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricsSummary:
    """
    Get a summary of metrics for analysis and dashboards.

    This endpoint provides aggregated statistics such as total evaluations,
    unique users, average latency, and error rates.
    """
    return MetricsService.get_metrics_summary(
        db=db,
        feature_flag_id=feature_flag_id,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )


@router.get(
    "/aggregated",
    response_model=List[AggregatedMetricResponse],
    summary="Get aggregated metrics",
    description="Get aggregated metrics based on filter criteria.",
)
def get_aggregated_metrics(
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    feature_flag_id: Optional[UUID] = Query(None, description="Filter by feature flag ID"),
    segment_id: Optional[UUID] = Query(None, description="Filter by segment ID"),
    targeting_rule_id: Optional[str] = Query(None, description="Filter by targeting rule ID"),
    period: Optional[AggregationPeriod] = Query(None, description="Aggregation period"),
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AggregatedMetricResponse]:
    """
    Get aggregated metrics for analysis and dashboards.

    This endpoint provides access to pre-aggregated metrics data based on
    different time periods and filter criteria.
    """
    filters = MetricsFilterParams(
        metric_type=metric_type,
        feature_flag_id=feature_flag_id,
        segment_id=segment_id,
        targeting_rule_id=targeting_rule_id,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )

    return MetricsService.get_aggregated_metrics(
        db=db,
        params=filters,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/errors",
    response_model=List[ErrorLogResponse],
    summary="Get error logs",
    description="Get error logs based on filter criteria.",
)
def get_error_logs(
    feature_flag_id: Optional[UUID] = Query(None, description="Filter by feature flag ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for errors"),
    end_date: Optional[datetime] = Query(None, description="End date for errors"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ErrorLogResponse]:
    """
    Get error logs for debugging and monitoring.

    This endpoint provides access to error logs that occurred during
    feature flag evaluation and other system operations.
    """
    return MetricsService.get_error_logs(
        db=db,
        feature_flag_id=feature_flag_id,
        start_date=start_date,
        end_date=end_date,
        error_type=error_type,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/aggregate",
    summary="Trigger metrics aggregation",
    description="Manually trigger the aggregation of raw metrics data.",
)
def trigger_aggregation(
    period: AggregationPeriod = Query(
        AggregationPeriod.DAY, description="Aggregation period"
    ),
    feature_flag_id: Optional[UUID] = Query(None, description="Filter by feature flag ID"),
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    start_time: Optional[datetime] = Query(None, description="Start time for aggregation"),
    end_time: Optional[datetime] = Query(None, description="End time for aggregation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Manually trigger the aggregation of raw metrics data.

    This endpoint is useful for testing or forcing aggregation outside
    of the scheduled aggregation tasks.
    """
    metrics_created = MetricsService.aggregate_metrics(
        db=db,
        period=period,
        start_time=start_time,
        end_time=end_time,
        feature_flag_id=feature_flag_id,
        metric_type=metric_type,
    )

    return {
        "status": "success",
        "aggregated_records": metrics_created,
        "period": period,
    }
