"""
Unit tests for the safety API endpoints.

This module contains tests for the API endpoints related to safety monitoring
and rollback functionality for feature flags.
"""

import json
from datetime import datetime
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_user, get_current_superuser
from backend.app.main import app
from backend.app.models.user import User
from backend.app.models.safety import (
    SafetySettings,
    FeatureFlagSafetyConfig,
    RollbackTriggerType
)
from backend.app.services.safety_service import SafetyService
from backend.app.schemas.safety import (
    SafetySettingsResponse,
    FeatureFlagSafetyConfigResponse,
    SafetyCheckResponse,
    RollbackResponse,
    HealthStatus,
    MetricValue,
    MetricThreshold,
    MetricStatus
)


class TestSafetyEndpoints:
    """Tests for safety API endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Get test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self) -> User:
        """Create a mock regular user."""
        return User(
            id=uuid4(),
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            hashed_password="hashed_password"
        )

    @pytest.fixture
    def mock_superuser(self) -> User:
        """Create a mock superuser."""
        return User(
            id=uuid4(),
            username="superuser",
            email="super@example.com",
            is_superuser=True,
            hashed_password="somepassword"
        )

    @pytest.fixture
    def feature_flag_id(self) -> UUID:
        """Provide a feature flag ID for tests."""
        return uuid4()

    @pytest.fixture
    def mock_safety_settings(self) -> Dict[str, Any]:
        """Create mock safety settings data."""
        return {
            "id": str(uuid4()),
            "monitoring_enabled": True,
            "auto_rollback_enabled": False,
            "check_interval_seconds": 60,
            "default_error_threshold": 2.0,
            "default_latency_threshold": 1.5,
            "notification_emails": ["alerts@example.com"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

    @pytest.fixture
    def mock_safety_check(self, feature_flag_id: UUID = uuid4()) -> Dict[str, Any]:
        """Create mock safety check data."""
        return {
            "feature_flag_id": str(feature_flag_id),
            "status": "safe",
            "metrics": {
                "error_rate": 0.5,
                "error_count": 10,
                "total_evaluations": 2000,
                "avg_latency": 150,
                "p95_latency": 200
            },
            "thresholds": {
                "error_threshold": 2.0,
                "error_threshold_value": 0.6,
                "latency_threshold": 1.5,
                "latency_threshold_value": 180
            },
            "details": {
                "error_rate": {
                    "status": "safe",
                    "current": 0.5,
                    "baseline": 0.3,
                    "threshold": 0.6
                },
                "latency": {
                    "status": "safe",
                    "current": 150,
                    "baseline": 120,
                    "threshold": 180
                }
            },
            "checked_at": datetime.utcnow().isoformat()
        }

    @pytest.fixture
    def mock_rollback_response(self, feature_flag_id: UUID = uuid4()) -> Dict[str, Any]:
        """Create mock rollback response data."""
        return {
            "success": True,
            "feature_flag_id": str(feature_flag_id),
            "rollback_record_id": str(uuid4()),
            "previous_percentage": 50,
            "current_percentage": 0,
            "message": "Feature flag rolled back due to manual request",
            "timestamp": datetime.utcnow().isoformat()
        }

    def test_get_safety_settings(self, client: TestClient, mock_superuser: User):
        """Test getting safety settings."""
        # Mock the deps
        app.dependency_overrides[get_current_active_user] = lambda: mock_superuser

        # Mock the response
        mock_settings = SafetySettingsResponse(
            id=uuid4(),
            enable_automatic_rollbacks=False,
            default_metrics={
                "error_rate": MetricThreshold(warning_threshold=0.1, critical_threshold=0.2)
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        with patch("backend.app.services.safety_service.SafetyService.async_get_safety_settings",
                   return_value=mock_settings):
            response = client.get("/api/v1/safety/settings")

        # Reset override
        app.dependency_overrides = {}

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["enable_automatic_rollbacks"] == mock_settings.enable_automatic_rollbacks
        assert "default_metrics" in data

    def test_update_safety_settings(self, client: TestClient, mock_superuser: User):
        """Test updating safety settings."""
        # Mock the deps
        app.dependency_overrides[get_current_superuser] = lambda: mock_superuser

        # Create update data
        update_data = {
            "enable_automatic_rollbacks": True,
            "default_metrics": {
                "error_rate": {
                    "warning_threshold": 0.05,
                    "critical_threshold": 0.1,
                    "comparison_type": "greater_than"
                }
            }
        }

        # Mock the response
        mock_settings = SafetySettingsResponse(
            id=uuid4(),
            enable_automatic_rollbacks=True,
            default_metrics=update_data["default_metrics"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        with patch("backend.app.services.safety_service.SafetyService.create_or_update_safety_settings",
                   return_value=mock_settings):
            response = client.post("/api/v1/safety/settings", json=update_data)

        # Reset override
        app.dependency_overrides = {}

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["enable_automatic_rollbacks"] == update_data["enable_automatic_rollbacks"]
        assert data["default_metrics"]["error_rate"]["warning_threshold"] == update_data["default_metrics"]["error_rate"]["warning_threshold"]

    def test_get_feature_flag_safety_config(self, client: TestClient, mock_user: User, feature_flag_id: UUID):
        """Test getting feature flag safety config."""
        # Mock the deps
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        # Mock the response
        mock_config = FeatureFlagSafetyConfigResponse(
            id=uuid4(),
            feature_flag_id=feature_flag_id,
            enabled=True,
            metrics={
                "error_rate": MetricThreshold(warning_threshold=0.1, critical_threshold=0.2)
            },
            rollback_percentage=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        with patch("backend.app.services.safety_service.SafetyService.async_get_feature_flag_safety_config",
                   return_value=mock_config):
            response = client.get(f"/api/v1/safety/feature-flags/{feature_flag_id}/config")

        # Reset override
        app.dependency_overrides = {}

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["feature_flag_id"] == str(feature_flag_id)
        assert data["enabled"] == mock_config.enabled
        assert "metrics" in data

    def test_check_feature_flag_safety(self, client: TestClient, mock_user: User, mock_safety_check: Dict[str, Any]):
        """Test checking feature flag safety."""
        feature_flag_id = UUID(mock_safety_check["feature_flag_id"])

        # Mock the deps
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        # Mock the response
        mock_check = SafetyCheckResponse(
            feature_flag_id=feature_flag_id,
            is_healthy=True,
            metrics=[
                MetricStatus(
                    name="error_rate",
                    description="Error rate of the feature flag",
                    current_value=0.05,
                    threshold=0.1,
                    unit="%",
                    is_healthy=True,
                    details={"comparison_type": "greater_than"}
                )
            ],
            last_checked=datetime.utcnow()
        )

        with patch("backend.app.services.safety_service.SafetyService.check_feature_flag_safety",
                   return_value=mock_check):
            response = client.get(f"/api/v1/safety/feature-flags/{feature_flag_id}/check")

        # Reset override
        app.dependency_overrides = {}

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["feature_flag_id"] == str(feature_flag_id)
        assert data["is_healthy"] == mock_check.is_healthy
        assert "metrics" in data

    def test_rollback_feature_flag(self, client: TestClient, mock_superuser: User, feature_flag_id: UUID):
        """Test rolling back a feature flag."""
        # Mock the deps
        app.dependency_overrides[get_current_active_user] = lambda: mock_superuser

        # Mock the response
        mock_rollback = RollbackResponse(
            success=True,
            feature_flag_id=feature_flag_id,
            message="Successfully rolled back feature flag",
            previous_percentage=50,
            new_percentage=0,
            trigger_type="manual",
            rollback_record_id=uuid4(),
            timestamp=datetime.utcnow(),
            details={"reason": "Test rollback"}
        )

        with patch("backend.app.services.safety_service.SafetyService.async_rollback_feature_flag",
                   return_value=mock_rollback):
            response = client.post(
                f"/api/v1/safety/feature-flags/{feature_flag_id}/rollback",
                params={"reason": "Test rollback", "percentage": 0}
            )

        # Reset override
        app.dependency_overrides = {}

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] == True
        assert "message" in data

    def test_unauthorized_access(self, client: TestClient, mock_user: User):
        """Test that regular users cannot access superuser endpoints."""
        # Mock the deps - regular user trying to access superuser endpoint
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        # Mock the deps - this will fail for regular users
        def mock_superuser_dependency():
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not a superuser")

        app.dependency_overrides[get_current_superuser] = mock_superuser_dependency

        # Try to update settings (superuser only)
        response = client.post(
            "/api/v1/safety/settings",
            json={"enable_automatic_rollbacks": True}
        )

        # Reset override
        app.dependency_overrides = {}

        # Check response - should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
