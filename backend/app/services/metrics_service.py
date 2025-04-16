"""
Service for collecting and querying metrics.

This module provides functionality for recording metrics during
feature flag evaluation and querying aggregated metrics for analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from uuid import UUID
from sqlalchemy import func, and_, or_, desc, text
from sqlalchemy.orm import Session
from sqlalchemy.sql import extract
from sqlalchemy.dialects.postgresql import insert

from backend.app.models.metrics.metric import (
    RawMetric,
    AggregatedMetric,
    ErrorLog,
    MetricType,
    AggregationPeriod,
)
from backend.app.schemas.metrics import (
    RawMetricCreate,
    ErrorLogCreate,
    MetricsFilterParams,
    MetricsSummary,
)
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsService:
    """
    Service for managing metrics collection and querying.

    This service provides methods for:
    - Recording raw metrics during flag evaluation
    - Logging errors during evaluation
    - Aggregating raw metrics into summary data
    - Querying metrics for dashboards and analysis
    """

    @staticmethod
    def record_metric(db: Session, data: RawMetricCreate) -> RawMetric:
        """
        Record a new raw metric.

        Args:
            db: Database session
            data: Metric data to record

        Returns:
            The created raw metric
        """
        # Set timestamp if not provided
        timestamp = data.timestamp or datetime.utcnow()

        # Create the raw metric
        metric = RawMetric(
            metric_type=data.metric_type,
            timestamp=timestamp,
            feature_flag_id=data.feature_flag_id,
            targeting_rule_id=data.targeting_rule_id,
            user_id=data.user_id,
            segment_id=data.segment_id,
            value=data.value,
            count=data.count,
            meta_data=data.metadata,
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return metric

    @staticmethod
    def record_flag_evaluation(
        db: Session,
        feature_flag_id: UUID,
        user_id: str,
        value: Optional[Any] = None,
        targeting_rule_id: Optional[str] = None,
        segment_id: Optional[UUID] = None,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RawMetric:
        """
        Record a feature flag evaluation.

        Args:
            db: Database session
            feature_flag_id: ID of the evaluated feature flag
            user_id: ID of the user
            value: Result of the evaluation
            targeting_rule_id: ID of the matched targeting rule if any
            segment_id: ID of the matched segment if any
            latency_ms: Time taken to evaluate the flag in milliseconds
            metadata: Additional contextual data

        Returns:
            The created raw metric
        """
        # Record the flag evaluation metric
        metric_data = RawMetricCreate(
            metric_type=MetricType.FLAG_EVALUATION,
            feature_flag_id=feature_flag_id,
            user_id=user_id,
            targeting_rule_id=targeting_rule_id,
            segment_id=segment_id,
            meta_data={
                "result": value,
                **(metadata or {})
            }
        )

        metric = MetricsService.record_metric(db, metric_data)

        # If latency was provided, record it as a separate metric
        if latency_ms is not None:
            latency_data = RawMetricCreate(
                metric_type=MetricType.LATENCY,
                feature_flag_id=feature_flag_id,
                user_id=user_id,
                value=latency_ms
            )
            MetricsService.record_metric(db, latency_data)

        # If a targeting rule was matched, record it
        if targeting_rule_id:
            rule_data = RawMetricCreate(
                metric_type=MetricType.RULE_MATCH,
                feature_flag_id=feature_flag_id,
                user_id=user_id,
                targeting_rule_id=targeting_rule_id
            )
            MetricsService.record_metric(db, rule_data)

        # If a segment was matched, record it
        if segment_id:
            segment_data = RawMetricCreate(
                metric_type=MetricType.SEGMENT_MATCH,
                feature_flag_id=feature_flag_id,
                user_id=user_id,
                segment_id=segment_id
            )
            MetricsService.record_metric(db, segment_data)

        return metric

    @staticmethod
    def log_error(db: Session, data: ErrorLogCreate) -> ErrorLog:
        """
        Log an error that occurred during flag evaluation.

        Args:
            db: Database session
            data: Error data to log

        Returns:
            The created error log
        """
        # Set timestamp if not provided
        timestamp = data.timestamp or datetime.utcnow()

        # Create the error log
        error_log = ErrorLog(
            error_type=data.error_type,
            timestamp=timestamp,
            feature_flag_id=data.feature_flag_id,
            user_id=data.user_id,
            message=data.message,
            stack_trace=data.stack_trace,
            request_data=data.request_data,
            meta_data=data.metadata,
        )

        db.add(error_log)
        db.commit()
        db.refresh(error_log)

        return error_log

    @staticmethod
    def aggregate_metrics(
        db: Session,
        period: AggregationPeriod,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        feature_flag_id: Optional[UUID] = None,
        metric_type: Optional[MetricType] = None,
    ) -> int:
        """
        Aggregate raw metrics into summary data.

        Args:
            db: Database session
            period: Aggregation period (minute, hour, day, etc.)
            start_time: Start of time range to aggregate
            end_time: End of time range to aggregate
            feature_flag_id: Optional filter by feature flag ID
            metric_type: Optional filter by metric type

        Returns:
            Number of aggregation records created
        """
        end_time = end_time or datetime.utcnow()

        # Define the SQL truncation function based on the period
        trunc_func = None
        if period == AggregationPeriod.MINUTE:
            trunc_func = func.date_trunc('minute', RawMetric.timestamp)
        elif period == AggregationPeriod.HOUR:
            trunc_func = func.date_trunc('hour', RawMetric.timestamp)
        elif period == AggregationPeriod.DAY:
            trunc_func = func.date_trunc('day', RawMetric.timestamp)
        elif period == AggregationPeriod.WEEK:
            trunc_func = func.date_trunc('week', RawMetric.timestamp)
        elif period == AggregationPeriod.MONTH:
            trunc_func = func.date_trunc('month', RawMetric.timestamp)
        elif period == AggregationPeriod.TOTAL:
            # For total, we use a fixed date as the period start
            trunc_func = func.to_timestamp(0)

        # Build the base query
        query = db.query(
            RawMetric.metric_type,
            trunc_func.label('period_start'),
            RawMetric.feature_flag_id,
            RawMetric.targeting_rule_id,
            RawMetric.segment_id,
            func.sum(RawMetric.count).label('count'),
            func.sum(RawMetric.value * RawMetric.count).label('sum_value'),
            func.min(RawMetric.value).label('min_value'),
            func.max(RawMetric.value).label('max_value'),
            func.count(func.distinct(RawMetric.user_id)).label('distinct_users')
        ).group_by(
            RawMetric.metric_type,
            'period_start',
            RawMetric.feature_flag_id,
            RawMetric.targeting_rule_id,
            RawMetric.segment_id
        )

        # Apply filters
        if start_time:
            query = query.filter(RawMetric.timestamp >= start_time)

        query = query.filter(RawMetric.timestamp < end_time)

        if feature_flag_id:
            query = query.filter(RawMetric.feature_flag_id == feature_flag_id)

        if metric_type:
            query = query.filter(RawMetric.metric_type == metric_type)

        # Execute query to get aggregation results
        aggregation_results = query.all()

        # Insert aggregated data
        metrics_created = 0

        for result in aggregation_results:
            # Check if an aggregation record already exists
            existing = db.query(AggregatedMetric).filter(
                AggregatedMetric.metric_type == result.metric_type,
                AggregatedMetric.period == period,
                AggregatedMetric.period_start == result.period_start,
                AggregatedMetric.feature_flag_id == result.feature_flag_id,
                AggregatedMetric.targeting_rule_id == result.targeting_rule_id,
                AggregatedMetric.segment_id == result.segment_id
            ).first()

            if existing:
                # Update existing record
                existing.count = result.count
                existing.sum_value = result.sum_value
                existing.min_value = result.min_value
                existing.max_value = result.max_value
                existing.distinct_users = result.distinct_users
                db.add(existing)
            else:
                # Create new aggregation record
                agg_metric = AggregatedMetric(
                    metric_type=result.metric_type,
                    period=period,
                    period_start=result.period_start,
                    feature_flag_id=result.feature_flag_id,
                    targeting_rule_id=result.targeting_rule_id,
                    segment_id=result.segment_id,
                    count=result.count,
                    sum_value=result.sum_value,
                    min_value=result.min_value,
                    max_value=result.max_value,
                    distinct_users=result.distinct_users
                )
                db.add(agg_metric)
                metrics_created += 1

        db.commit()

        return metrics_created

    @staticmethod
    def get_metrics_summary(
        db: Session,
        feature_flag_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: AggregationPeriod = AggregationPeriod.DAY
    ) -> MetricsSummary:
        """
        Get summary statistics for metrics.

        Args:
            db: Database session
            feature_flag_id: Optional filter by feature flag ID
            start_date: Optional filter from this date
            end_date: Optional filter until this date
            period: Aggregation period to use

        Returns:
            Summary statistics
        """
        # Set default dates if not provided
        end_date = end_date or datetime.utcnow()
        start_date = start_date or (end_date - timedelta(days=30))

        # Base query for aggregated metrics
        query = db.query(AggregatedMetric).filter(
            AggregatedMetric.period == period,
            AggregatedMetric.period_start >= start_date,
            AggregatedMetric.period_start <= end_date
        )

        if feature_flag_id:
            query = query.filter(AggregatedMetric.feature_flag_id == feature_flag_id)

        # Get total evaluations
        evaluations_query = query.filter(AggregatedMetric.metric_type == MetricType.FLAG_EVALUATION)
        total_evaluations = sum(m.count for m in evaluations_query.all())

        # Get unique users
        unique_users = db.query(func.count(func.distinct(RawMetric.user_id))).filter(
            RawMetric.timestamp >= start_date,
            RawMetric.timestamp <= end_date,
            RawMetric.metric_type == MetricType.FLAG_EVALUATION
        )

        if feature_flag_id:
            unique_users = unique_users.filter(RawMetric.feature_flag_id == feature_flag_id)

        unique_users = unique_users.scalar() or 0

        # Get average latency
        latency_query = query.filter(AggregatedMetric.metric_type == MetricType.LATENCY)
        latency_metrics = latency_query.all()

        total_latency_count = sum(m.count for m in latency_metrics)
        total_latency_sum = sum(m.sum_value or 0 for m in latency_metrics)

        avg_latency = None
        if total_latency_count > 0:
            avg_latency = total_latency_sum / total_latency_count

        # Get rule match rate
        rule_match_query = query.filter(AggregatedMetric.metric_type == MetricType.RULE_MATCH)
        rule_match_count = sum(m.count for m in rule_match_query.all())

        rule_match_rate = None
        if total_evaluations > 0:
            rule_match_rate = (rule_match_count / total_evaluations) * 100

        # Get error rate
        error_count = db.query(func.count(ErrorLog.id)).filter(
            ErrorLog.timestamp >= start_date,
            ErrorLog.timestamp <= end_date
        )

        if feature_flag_id:
            error_count = error_count.filter(ErrorLog.feature_flag_id == feature_flag_id)

        error_count = error_count.scalar() or 0

        error_rate = None
        if total_evaluations > 0:
            error_rate = (error_count / total_evaluations) * 100

        # Create and return the summary
        return MetricsSummary(
            total_evaluations=total_evaluations,
            unique_users=unique_users,
            avg_latency=avg_latency,
            rule_match_rate=rule_match_rate,
            error_rate=error_rate
        )

    @staticmethod
    def get_aggregated_metrics(
        db: Session,
        params: MetricsFilterParams,
        skip: int = 0,
        limit: int = 100
    ) -> List[AggregatedMetric]:
        """
        Get aggregated metrics based on filter criteria.

        Args:
            db: Database session
            params: Filter parameters
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of aggregated metrics matching the criteria
        """
        query = db.query(AggregatedMetric)

        # Apply filters
        if params.metric_type:
            query = query.filter(AggregatedMetric.metric_type == params.metric_type)

        if params.feature_flag_id:
            query = query.filter(AggregatedMetric.feature_flag_id == params.feature_flag_id)

        if params.segment_id:
            query = query.filter(AggregatedMetric.segment_id == params.segment_id)

        if params.targeting_rule_id:
            query = query.filter(AggregatedMetric.targeting_rule_id == params.targeting_rule_id)

        if params.period:
            query = query.filter(AggregatedMetric.period == params.period)

        if params.start_date:
            query = query.filter(AggregatedMetric.period_start >= params.start_date)

        if params.end_date:
            query = query.filter(AggregatedMetric.period_start <= params.end_date)

        # Order by period start (descending) and metric type
        query = query.order_by(desc(AggregatedMetric.period_start), AggregatedMetric.metric_type)

        # Apply pagination
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_error_logs(
        db: Session,
        feature_flag_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        error_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ErrorLog]:
        """
        Get error logs based on filter criteria.

        Args:
            db: Database session
            feature_flag_id: Optional filter by feature flag ID
            start_date: Optional filter from this date
            end_date: Optional filter until this date
            error_type: Optional filter by error type
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of error logs matching the criteria
        """
        query = db.query(ErrorLog)

        # Apply filters
        if feature_flag_id:
            query = query.filter(ErrorLog.feature_flag_id == feature_flag_id)

        if start_date:
            query = query.filter(ErrorLog.timestamp >= start_date)

        if end_date:
            query = query.filter(ErrorLog.timestamp <= end_date)

        if error_type:
            query = query.filter(ErrorLog.error_type == error_type)

        # Order by timestamp (descending)
        query = query.order_by(desc(ErrorLog.timestamp))

        # Apply pagination
        return query.offset(skip).limit(limit).all()
