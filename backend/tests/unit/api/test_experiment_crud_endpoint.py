# backend/tests/api/v1/endpoints/test_experiment_crud_endpoint.py
"""
Test cases for Experiment CRUD API endpoints.
"""

import os
import pytest
from unittest import mock
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
import boto3
from datetime import datetime
from uuid import uuid4, UUID

from backend.app.main import app
from backend.app.models.user import User
from backend.app.api import deps
from backend.app.utils.aws_client import AWSClient
from backend.app.middleware.logging_middleware import LoggingMiddleware
from backend.app.utils.metrics import MetricsCollector
from backend.app.middleware.error_middleware import ErrorMiddleware


class TestExperimentCreate:
    """Tests for creating experiments."""

    @pytest.fixture(autouse=True)
    def setup_aws_mocks(self, monkeypatch):
        """Set up AWS mocks to prevent any real AWS calls."""
        # Disable AWS service calls
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.setenv("DISABLE_AWS_CALLS", "true")

        # Create mock cloudwatch clients
        mock_logs_client = mock.MagicMock()
        mock_metrics_client = mock.MagicMock()

        # Create a mock AWS client class that handles both static and instance methods
        class MockAWSClient:
            @staticmethod
            def get_cloudwatch_client(*args, **kwargs):
                return mock_logs_client

            @staticmethod
            def get_cloudwatch_metrics_client(*args, **kwargs):
                return mock_metrics_client

            @staticmethod
            def put_metric_data(*args, **kwargs):
                return True

            def __init__(self):
                self.logs_client = mock_logs_client
                self.metrics_client = mock_metrics_client
                self.init_cloudwatch_logs = mock.MagicMock(return_value=True)
                self.init_cloudwatch_metrics = mock.MagicMock(return_value=True)
                self.send_metric = mock.MagicMock(return_value=True)

        # Replace the AWSClient class with our mock
        monkeypatch.setattr("backend.app.utils.aws_client.AWSClient", MockAWSClient)

        # Mock boto3 clients directly
        def mock_boto3_client(service, **kwargs):
            if service == 'logs':
                return mock_logs_client
            elif service == 'cloudwatch':
                return mock_metrics_client
            else:
                mock_client = mock.MagicMock()
                return mock_client

        monkeypatch.setattr(boto3, "client", mock_boto3_client)

        # Patch sessions too
        mock_session = mock.MagicMock()
        mock_session.client.side_effect = mock_boto3_client
        monkeypatch.setattr(boto3, "Session", mock.MagicMock(return_value=mock_session))

    @mock.patch("backend.app.api.v1.endpoints.experiments.ExperimentService")
    @mock.patch("backend.app.middleware.logging_middleware.LoggingMiddleware.dispatch")
    @mock.patch("backend.app.utils.metrics.MetricsCollector")
    @mock.patch("backend.app.middleware.error_middleware.ErrorMiddleware.dispatch")
    @mock.patch("backend.app.middleware.error_middleware.ErrorMiddleware._log_error")
    @mock.patch("backend.app.middleware.error_middleware.ErrorMiddleware._send_error_metrics")
    @mock.patch("backend.app.middleware.metrics_middleware.MetricsMiddleware._send_request_metrics")
    @mock.patch("backend.app.services.auth_service.auth_service.get_user")
    def test_create_experiment_success(
        self,
        mock_get_user,
        mock_metrics_send_metrics,
        mock_error_send_metrics,
        mock_log_error,
        mock_error_dispatch,
        MockMetricsCollector,
        mock_dispatch,
        MockExperimentService,
        client: TestClient,
        db_session: Session,
        mock_auth,
    ):
        """Test successful experiment creation with valid data."""
        # Set test environment
        os.environ["TESTING"] = "true"

        # Setup mock services and dependencies
        mock_service = MockExperimentService.return_value
        experiment_id = uuid4()
        owner_id = uuid4()
        variant1_id = uuid4()
        variant2_id = uuid4()
        metric_id = uuid4()
        mock_service.create_experiment.return_value = {
            "id": experiment_id,
            "name": "Test Experiment",
            "description": "Testing experiment creation",
            "hypothesis": "Feature A will increase conversion by 10%",
            "experiment_type": "a_b",
            "status": "draft",
            "owner_id": owner_id,
            "start_date": None,
            "end_date": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "variants": [
                {
                    "id": variant1_id,
                    "name": "Control",
                    "description": "Original version",
                    "is_control": True,
                    "traffic_allocation": 50,
                    "configuration": {"feature_enabled": False},
                    "experiment_id": experiment_id,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
                {
                    "id": variant2_id,
                    "name": "Treatment",
                    "description": "New version",
                    "is_control": False,
                    "traffic_allocation": 50,
                    "configuration": {"feature_enabled": True},
                    "experiment_id": experiment_id,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            ],
            "metrics": [
                {
                    "id": metric_id,
                    "name": "Conversion Rate",
                    "description": "Percentage of users who complete a purchase",
                    "event_name": "purchase",
                    "metric_type": "conversion",
                    "is_primary": True,
                    "aggregation_method": "average",
                    "minimum_sample_size": 100,
                    "expected_effect": None,
                    "event_value_path": None,
                    "lower_is_better": False,
                    "experiment_id": experiment_id,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
            ],
        }

        # Mock middleware methods that call AWS
        mock_metrics_send_metrics.return_value = None
        mock_error_send_metrics.return_value = None
        mock_log_error.return_value = None

        # Create a simple synchronous wrapper for the async dispatch methods
        def sync_mock_dispatch(request, call_next):
            return call_next(request)

        # Mock middleware dispatch functions to be synchronous
        mock_dispatch.side_effect = sync_mock_dispatch
        mock_error_dispatch.side_effect = sync_mock_dispatch

        # Mock metrics collector
        mock_metrics = MockMetricsCollector.return_value
        mock_metrics.get_metrics.return_value = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "request_count": 0,
            "error_count": 0,
        }

        # Mock auth service
        mock_get_user.return_value = {"username": "testuser", "attributes": {}}

        # Create test data
        test_data = {
            "name": "Test Experiment",
            "description": "Testing experiment creation",
            "hypothesis": "Feature A will increase conversion by 10%",
            "experiment_type": "a_b",
            "status": "draft",
            "variants": [
                {
                    "name": "Control",
                    "description": "Original version",
                    "is_control": True,
                    "traffic_allocation": 50,
                    "configuration": {"feature_enabled": False},
                },
                {
                    "name": "Treatment",
                    "description": "New version",
                    "is_control": False,
                    "traffic_allocation": 50,
                    "configuration": {"feature_enabled": True},
                },
            ],
            "metrics": [
                {
                    "name": "Conversion Rate",
                    "description": "Percentage of users who complete a purchase",
                    "event_name": "purchase",
                    "metric_type": "conversion",
                    "is_primary": True,
                }
            ],
        }

        # Make request
        response = client.post(
            "/api/v1/experiments/",
            json=test_data,
            headers={"Authorization": "Bearer test-token"},
        )

        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        assert UUID(response.json()["id"]) == experiment_id
        assert response.json()["name"] == "Test Experiment"
        assert response.json()["description"] == "Testing experiment creation"
        assert response.json()["hypothesis"] == "Feature A will increase conversion by 10%"
        assert response.json()["experiment_type"] == "a_b"
        assert response.json()["status"] == "draft"
        assert len(response.json()["variants"]) == 2
        assert len(response.json()["metrics"]) == 1

        # Verify service was called
        mock_service.create_experiment.assert_called_once()

        # Clean up
        os.environ.pop("TESTING", None)
