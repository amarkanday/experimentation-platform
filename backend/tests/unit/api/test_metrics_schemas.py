"""
Metrics Schema Tests.

This module contains tests for the Pydantic v2 metrics schema validation.
"""

import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from pydantic import ValidationError

from backend.app.schemas.metrics import (
    RawMetricCreate,
    RawMetricResponse,
    AggregatedMetricBase,
    AggregatedMetricResponse,
    ErrorLogCreate,
    ErrorLogResponse,
    MetricsFilterParams,
    MetricsSummary
)
from backend.app.models.metrics.metric import MetricType, AggregationPeriod


class TestMetricsSchemaValidation:
    """Tests for metrics schema validation with Pydantic v2."""

    def test_raw_metric_create(self):
        """Test that valid raw metric creation data passes validation."""
        valid_data = {
            "metric_type": MetricType.FLAG_EVALUATION,
            "feature_flag_id": str(uuid.uuid4()),
            "user_id": "test-user-123",
            "value": 1.0,
            "count": 1,
            "metadata": {"browser": "Chrome", "device": "mobile"}
        }

        # This should not raise an exception
        metric = RawMetricCreate(**valid_data)

        # Check that fields were correctly parsed
        assert metric.metric_type == MetricType.FLAG_EVALUATION
        assert metric.user_id == "test-user-123"
        assert metric.value == 1.0
        assert metric.count == 1
        assert metric.metadata["browser"] == "Chrome"
        assert metric.metadata["device"] == "mobile"

    def test_raw_metric_response(self):
        """Test RawMetricResponse schema."""
        current_time = datetime.now(timezone.utc)
        valid_data = {
            "id": str(uuid.uuid4()),
            "metric_type": MetricType.FLAG_EVALUATION,
            "feature_flag_id": str(uuid.uuid4()),
            "user_id": "test-user-123",
            "value": 1.0,
            "count": 1,
            "timestamp": current_time,
            "created_at": current_time,
            "updated_at": current_time,
            "metadata": {"browser": "Chrome", "device": "mobile"}
        }

        # This should not raise an exception
        response = RawMetricResponse(**valid_data)

        # Check that fields were correctly parsed
        assert response.metric_type == MetricType.FLAG_EVALUATION
        assert response.user_id == "test-user-123"
        assert response.count == 1
        assert response.timestamp == current_time
        assert response.metadata["browser"] == "Chrome"

    def test_aggregated_metric_base(self):
        """Test AggregatedMetricBase schema."""
        current_time = datetime.now(timezone.utc)
        valid_data = {
            "metric_type": MetricType.FLAG_EVALUATION,
            "period": AggregationPeriod.DAY,
            "period_start": current_time,
            "feature_flag_id": str(uuid.uuid4()),
            "count": 100,
            "sum_value": 150.5,
            "min_value": 0.5,
            "max_value": 10.0,
            "distinct_users": 50,
            "metadata": {"region": "US", "version": "1.0.0"}
        }

        # This should not raise an exception
        metric = AggregatedMetricBase(**valid_data)

        # Check that fields were correctly parsed
        assert metric.metric_type == MetricType.FLAG_EVALUATION
        assert metric.period == AggregationPeriod.DAY
        assert metric.period_start == current_time
        assert metric.count == 100
        assert metric.sum_value == 150.5
        assert metric.min_value == 0.5
        assert metric.max_value == 10.0
        assert metric.distinct_users == 50
        assert metric.metadata["region"] == "US"

    def test_error_log_create(self):
        """Test ErrorLogCreate schema."""
        valid_data = {
            "error_type": "rule_evaluation_error",
            "feature_flag_id": str(uuid.uuid4()),
            "user_id": "test-user-123",
            "message": "Failed to evaluate targeting rule",
            "stack_trace": "Traceback...",
            "request_data": {"context": {"country": "US"}},
            "metadata": {"severity": "high", "component": "targeting"}
        }

        # This should not raise an exception
        error_log = ErrorLogCreate(**valid_data)

        # Check that fields were correctly parsed
        assert error_log.error_type == "rule_evaluation_error"
        assert error_log.message == "Failed to evaluate targeting rule"
        assert error_log.stack_trace == "Traceback..."
        assert error_log.request_data["context"]["country"] == "US"
        assert error_log.metadata["severity"] == "high"

    def test_metrics_filter_params(self):
        """Test MetricsFilterParams schema."""
        current_time = datetime.now(timezone.utc)
        valid_data = {
            "metric_type": MetricType.FLAG_EVALUATION,
            "feature_flag_id": str(uuid.uuid4()),
            "segment_id": str(uuid.uuid4()),
            "targeting_rule_id": "rule-123",
            "start_date": current_time,
            "end_date": current_time,
            "period": AggregationPeriod.HOUR
        }

        # This should not raise an exception
        filter_params = MetricsFilterParams(**valid_data)

        # Check that fields were correctly parsed
        assert filter_params.metric_type == MetricType.FLAG_EVALUATION
        assert filter_params.targeting_rule_id == "rule-123"
        assert filter_params.start_date == current_time
        assert filter_params.end_date == current_time
        assert filter_params.period == AggregationPeriod.HOUR

    def test_metrics_summary(self):
        """Test MetricsSummary schema."""
        valid_data = {
            "total_evaluations": 1000,
            "unique_users": 500,
            "avg_latency": 125.5,
            "rule_match_rate": 75.0,
            "error_rate": 2.5
        }

        # This should not raise an exception
        summary = MetricsSummary(**valid_data)

        # Check that fields were correctly parsed
        assert summary.total_evaluations == 1000
        assert summary.unique_users == 500
        assert summary.avg_latency == 125.5
        assert summary.rule_match_rate == 75.0
        assert summary.error_rate == 2.5

    def test_model_config_correctly_applied(self):
        """Test that model_config is correctly applied in Pydantic v2 style."""
        # Test enum values are correctly processed
        data_with_enum_string = {
            "metric_type": "flag_evaluation",  # String instead of enum
            "feature_flag_id": str(uuid.uuid4()),
            "user_id": "test-user",
            "value": 1.0
        }

        # This should work because use_enum_values=True in model_config
        metric = RawMetricCreate(**data_with_enum_string)
        assert metric.metric_type == MetricType.FLAG_EVALUATION

        # Test from_attributes option works (replacing orm_mode)
        # This is challenging to test directly, but we can verify the config exists
        assert hasattr(RawMetricResponse, "model_config")
        assert RawMetricResponse.model_config.get("from_attributes") is True
