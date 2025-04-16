"""Unit tests for metrics API endpoints."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.api.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.models.metrics.metric import MetricType, AggregationPeriod
from backend.app.schemas.metrics import (
    MetricsSummary,
    AggregatedMetricResponse,
    ErrorLogResponse,
    MetricsFilterParams,
)
from backend.app.services.metrics_service import MetricsService


@pytest.fixture
def client():
    """Create a test client with mocked dependencies."""
    # Mock the get_db dependency
    def override_get_db():
        try:
            db = MagicMock()
            yield db
        finally:
            pass

    # Mock the authentication dependency
    async def override_get_current_user():
        mock_user = MagicMock(spec=User)
        mock_user.id = UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.is_superuser = True
        return mock_user

    # Override the dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides = {}


def test_get_metrics_summary(client):
    """Test retrieving metrics summary."""
    # Mock the MetricsService.get_metrics_summary method
    with patch.object(MetricsService, "get_metrics_summary") as mock_summary:
        # Configure the mock to return a sample summary
        mock_summary.return_value = MetricsSummary(
            total_evaluations=1000,
            unique_users=250,
            avg_latency=45.5,
            rule_match_rate=75.0,
            error_rate=2.5
        )

        # Make the request
        response = client.get(
            "/api/v1/metrics/summary",
            params={
                "feature_flag_id": "12345678-1234-5678-1234-567812345678",
                "period": "day",
                "start_date": "2023-01-01T00:00:00Z",
                "end_date": "2023-01-31T23:59:59Z"
            }
        )

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["total_evaluations"] == 1000
        assert data["unique_users"] == 250
        assert data["avg_latency"] == 45.5
        assert data["rule_match_rate"] == 75.0
        assert data["error_rate"] == 2.5

        # Verify the service was called with the right parameters
        mock_summary.assert_called_once()
        args, kwargs = mock_summary.call_args
        assert kwargs["feature_flag_id"] == UUID("12345678-1234-5678-1234-567812345678")
        assert kwargs["period"] == AggregationPeriod.DAY
        assert kwargs["start_date"].isoformat() == "2023-01-01T00:00:00+00:00"
        assert kwargs["end_date"].isoformat() == "2023-01-31T23:59:59+00:00"


def test_get_aggregated_metrics(client):
    """Test retrieving aggregated metrics."""
    # Mock the MetricsService.get_aggregated_metrics method
    with patch.object(MetricsService, "get_aggregated_metrics") as mock_get_metrics:
        # Create proper instances of AggregatedMetricResponse
        metric1 = AggregatedMetricResponse(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            metric_type=MetricType.FLAG_EVALUATION,
            period=AggregationPeriod.DAY,
            period_start=datetime(2023, 1, 1, tzinfo=timezone.utc),
            count=500,
            distinct_users=120,
            feature_flag_id=UUID("12345678-1234-5678-1234-567812345678"),
            created_at=datetime(2023, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        )

        metric2 = AggregatedMetricResponse(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            metric_type=MetricType.FLAG_EVALUATION,
            period=AggregationPeriod.DAY,
            period_start=datetime(2023, 1, 2, tzinfo=timezone.utc),
            count=600,
            distinct_users=150,
            feature_flag_id=UUID("12345678-1234-5678-1234-567812345678"),
            created_at=datetime(2023, 1, 2, 1, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 2, 1, 0, 0, tzinfo=timezone.utc)
        )

        # Configure the mock to return the metrics objects
        mock_get_metrics.return_value = [metric1, metric2]

        # Make the request
        response = client.get(
            "/api/v1/metrics/aggregated",
            params={
                "metric_type": "flag_evaluation",
                "feature_flag_id": "12345678-1234-5678-1234-567812345678",
                "period": "day",
                "start_date": "2023-01-01T00:00:00Z",
                "end_date": "2023-01-31T23:59:59Z",
                "skip": 0,
                "limit": 10
            }
        )

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify the service was called with the right parameters
        mock_get_metrics.assert_called_once()
        args, kwargs = mock_get_metrics.call_args

        # Check that the params object was created correctly
        assert isinstance(kwargs["params"], MetricsFilterParams)
        assert kwargs["params"].metric_type == MetricType.FLAG_EVALUATION
        assert kwargs["params"].feature_flag_id == UUID("12345678-1234-5678-1234-567812345678")
        assert kwargs["params"].period == AggregationPeriod.DAY
        assert kwargs["skip"] == 0
        assert kwargs["limit"] == 10


def test_get_error_logs(client):
    """Test retrieving error logs."""
    # Mock the MetricsService.get_error_logs method
    with patch.object(MetricsService, "get_error_logs") as mock_get_errors:
        # Create proper instances of ErrorLogResponse
        error1 = ErrorLogResponse(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            error_type="rule_evaluation_error",
            feature_flag_id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id="user123",
            message="Failed to evaluate targeting rule",
            stack_trace="Error stack trace here",
            request_data={"context": {"country": "US"}},
            metadata={"additional": "debug data"},
            timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        )

        error2 = ErrorLogResponse(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            error_type="flag_evaluation_error",
            feature_flag_id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id="user456",
            message="Invalid feature flag configuration",
            stack_trace="Error stack trace here",
            request_data={"context": {"country": "UK"}},
            metadata={"additional": "debug data"},
            timestamp=datetime(2023, 1, 2, 15, 0, 0, tzinfo=timezone.utc),
            created_at=datetime(2023, 1, 2, 15, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 2, 15, 0, 0, tzinfo=timezone.utc)
        )

        # Configure the mock to return the error objects
        mock_get_errors.return_value = [error1, error2]

        # Make the request
        response = client.get(
            "/api/v1/metrics/errors",
            params={
                "feature_flag_id": "12345678-1234-5678-1234-567812345678",
                "start_date": "2023-01-01T00:00:00Z",
                "end_date": "2023-01-31T23:59:59Z",
                "error_type": "rule_evaluation_error",
                "skip": 0,
                "limit": 10
            }
        )

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify the service was called with the right parameters
        mock_get_errors.assert_called_once()
        args, kwargs = mock_get_errors.call_args
        assert kwargs["feature_flag_id"] == UUID("12345678-1234-5678-1234-567812345678")
        assert kwargs["start_date"].isoformat() == "2023-01-01T00:00:00+00:00"
        assert kwargs["end_date"].isoformat() == "2023-01-31T23:59:59+00:00"
        assert kwargs["error_type"] == "rule_evaluation_error"
        assert kwargs["skip"] == 0
        assert kwargs["limit"] == 10


def test_trigger_aggregation(client):
    """Test triggering metrics aggregation."""
    # Mock the MetricsService.aggregate_metrics method
    with patch.object(MetricsService, "aggregate_metrics") as mock_aggregate:
        # Configure the mock to return a count
        mock_aggregate.return_value = 42

        # Make the request
        response = client.post(
            "/api/v1/metrics/aggregate",
            params={
                "period": "day",
                "feature_flag_id": "12345678-1234-5678-1234-567812345678",
                "metric_type": "flag_evaluation",
                "start_time": "2023-01-01T00:00:00Z",
                "end_time": "2023-01-31T23:59:59Z"
            }
        )

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["aggregated_records"] == 42
        assert data["period"] == "day"

        # Verify the service was called with the right parameters
        mock_aggregate.assert_called_once()
        args, kwargs = mock_aggregate.call_args
        assert kwargs["period"] == AggregationPeriod.DAY
        assert kwargs["feature_flag_id"] == UUID("12345678-1234-5678-1234-567812345678")
        assert kwargs["metric_type"] == MetricType.FLAG_EVALUATION
        assert kwargs["start_time"].isoformat() == "2023-01-01T00:00:00+00:00"
        assert kwargs["end_time"].isoformat() == "2023-01-31T23:59:59+00:00"
