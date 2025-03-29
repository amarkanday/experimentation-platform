"""
Test cases for Experiment CRUD API endpoints.

This module contains test cases for creating, reading, updating, and deleting
experiments, as well as the experiment lifecycle management and enhanced features.
"""

import pytest
import uuid
from unittest import mock
from fastapi.testclient import TestClient


# Add this helper function directly in the test file to avoid import errors
def get_auth_header(token: str = None) -> dict:
    """
    Get authorization header for API requests.

    Args:
        token: Optional token to use, otherwise uses a test token

    Returns:
        Dict containing Authorization header
    """
    if token is None:
        token = "test-token"  # Use a simple test token

    return {"Authorization": f"Bearer {token}"}


# Mock the authentication dependency
@pytest.fixture
def mock_auth():
    """Mock the authentication dependency to bypass authentication."""
    with mock.patch("backend.app.api.deps.get_current_active_user") as mock_auth:
        # Create a mock user
        mock_user = mock.MagicMock()
        mock_user.id = str(uuid.uuid4())
        mock_user.is_superuser = True
        mock_auth.return_value = mock_user
        yield mock_auth


# Mock the DB dependency
@pytest.fixture
def mock_db():
    """Mock the database dependency."""
    with mock.patch("backend.app.api.deps.get_db") as mock_db:
        # Create a mock DB session
        mock_session = mock.MagicMock()
        mock_db.return_value = mock_session
        yield mock_session


# Mock experiment service
@pytest.fixture
def mock_experiment_service():
    """Mock the experiment service."""
    with mock.patch(
        "backend.app.services.experiment_service.ExperimentService"
    ) as mock_service:
        # Create a mock experiment service
        service_instance = mock.MagicMock()
        mock_service.return_value = service_instance

        # Mock the get_experiment_by_id method
        experiment = {
            "id": str(uuid.uuid4()),
            "name": "Test Experiment",
            "description": "Test description",
            "status": "draft",
            "variants": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Control",
                    "is_control": True,
                    "traffic_allocation": 50,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Treatment",
                    "is_control": False,
                    "traffic_allocation": 50,
                },
            ],
            "metrics": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Conversion Rate",
                    "event_name": "conversion",
                    "metric_type": "conversion",
                    "is_primary": True,
                }
            ],
        }
        service_instance.get_experiment_by_id.return_value = experiment
        service_instance.create_experiment.return_value = experiment

        yield service_instance


@pytest.fixture
def client(mock_auth, mock_db, mock_experiment_service):
    """Create a test client with mocked dependencies."""
    from backend.app.main import app

    return TestClient(app)


class TestExperimentCreate:
    """Tests for creating experiments."""

    def test_create_experiment_success(self, client, mock_experiment_service):
        """Test successful experiment creation with valid data."""
        experiment_data = {
            "name": "Test Experiment",
            "description": "Testing experiment creation",
            "hypothesis": "Feature A will increase conversion by 10%",
            "experiment_type": "a_b",
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

        # Mock the create_experiment method
        mock_experiment_service.create_experiment.return_value = {
            "id": str(uuid.uuid4()),
            "name": experiment_data["name"],
            "variants": experiment_data["variants"],
            "metrics": experiment_data["metrics"],
        }

        response = client.post(
            "/api/v1/experiments/", json=experiment_data, headers=get_auth_header()
        )
        assert response.status_code == 201

        # Verify the mock was called
        mock_experiment_service.create_experiment.assert_called_once()

    def test_create_experiment_invalid_data(self, client):
        """Test experiment creation with invalid data."""
        # Missing required fields
        experiment_data = {
            "name": "Test Experiment"
            # Missing variants and metrics
        }

        response = client.post(
            "/api/v1/experiments/", json=experiment_data, headers=get_auth_header()
        )
        assert response.status_code == 422  # Validation error

    def test_create_experiment_invalid_variant_allocation(
        self, client, mock_experiment_service
    ):
        """Test experiment creation with invalid variant traffic allocation."""
        # Mock the service to raise a ValueError
        mock_experiment_service.create_experiment.side_effect = ValueError(
            "Traffic allocations must sum to 100%"
        )

        experiment_data = {
            "name": "Test Experiment",
            "description": "Testing experiment creation",
            "experiment_type": "a_b",
            "variants": [
                {
                    "name": "Control",
                    "is_control": True,
                    "traffic_allocation": 60,  # These don't sum to 100%
                },
                {
                    "name": "Treatment",
                    "is_control": False,
                    "traffic_allocation": 60,  # These don't sum to 100%
                },
            ],
            "metrics": [
                {
                    "name": "Conversion Rate",
                    "event_name": "purchase",
                    "metric_type": "conversion",
                }
            ],
        }

        response = client.post(
            "/api/v1/experiments/", json=experiment_data, headers=get_auth_header()
        )
        assert response.status_code == 400
        assert (
            "traffic allocations must sum to 100%" in response.json()["detail"].lower()
        )

    def test_create_experiment_no_control_variant(
        self, client, mock_experiment_service
    ):
        """Test experiment creation with no control variant."""
        # Mock the service to raise a ValueError
        mock_experiment_service.create_experiment.side_effect = ValueError(
            "At least one variant must be marked as control"
        )

        experiment_data = {
            "name": "Test Experiment",
            "description": "Testing experiment creation",
            "experiment_type": "a_b",
            "variants": [
                {
                    "name": "Variant A",
                    "is_control": False,
                    "traffic_allocation": 50,
                },
                {
                    "name": "Variant B",
                    "is_control": False,  # No control variant
                    "traffic_allocation": 50,
                },
            ],
            "metrics": [
                {
                    "name": "Conversion Rate",
                    "event_name": "purchase",
                    "metric_type": "conversion",
                }
            ],
        }

        response = client.post(
            "/api/v1/experiments/", json=experiment_data, headers=get_auth_header()
        )
        assert response.status_code == 400
        assert "control variant" in response.json()["detail"].lower()


class TestExperimentRead:
    """Tests for reading experiments."""

    def test_get_experiment_by_id(self, client, mock_experiment_service):
        """Test retrieving an experiment by ID."""
        # Create a UUID for the experiment
        experiment_id = str(uuid.uuid4())

        # Mock get_experiment_by_id to return a specific experiment
        experiment = {
            "id": experiment_id,
            "name": "Test Experiment",
            "description": "Test description",
        }
        mock_experiment_service.get_experiment_by_id.return_value = experiment

        response = client.get(
            f"/api/v1/experiments/{experiment_id}", headers=get_auth_header()
        )
        assert response.status_code == 200

        # Verify the mock was called
        mock_experiment_service.get_experiment_by_id.assert_called_once_with(
            experiment_id
        )

    def test_get_experiment_not_found(self, client, mock_experiment_service):
        """Test retrieving a non-existent experiment."""
        # Mock get_experiment_by_id to return None
        mock_experiment_service.get_experiment_by_id.return_value = None

        non_existent_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/experiments/{non_existent_id}", headers=get_auth_header()
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        # Verify the mock was called
        mock_experiment_service.get_experiment_by_id.assert_called_once_with(
            non_existent_id
        )
