"""
Test cases for Feature Flag API endpoints.

This module contains test cases for creating, reading, updating, and deleting
feature flags, as well as feature flag status toggling and user evaluation.
"""

import pytest
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.tests.test_helpers import (
    create_test_feature_flag,
    get_auth_header,
)

client = TestClient(app)


class TestFeatureFlagCreate:
    """Tests for creating feature flags."""

    def test_create_feature_flag_success(self):
        """Test successful feature flag creation."""
        feature_flag_data = {
            "key": "new-checkout-flow",
            "name": "New Checkout Flow",
            "description": "Enables the new checkout experience for users",
            "status": "inactive",
            "rollout_percentage": 10,
            "targeting_rules": {"country": ["US", "CA"], "user_group": "beta"},
            "value": {
                "variants": {"control": {"value": False}, "treatment": {"value": True}},
                "default": "control",
            },
        }

        response = client.post(
            "/api/v1/feature-flags/", json=feature_flag_data, headers=get_auth_header()
        )
        assert response.status_code == 201
        assert response.json()["key"] == feature_flag_data["key"]
        assert response.json()["status"] == "inactive"

    def test_create_feature_flag_duplicate_key(self):
        """Test creating a feature flag with an existing key."""
        # Create feature flag
        ff_data = {
            "key": "duplicate-key-test",
            "name": "Test FF",
            "description": "Test description",
        }

        # First one should succeed
        client.post("/api/v1/feature-flags/", json=ff_data, headers=get_auth_header())

        # Second one with same key should fail
        response = client.post(
            "/api/v1/feature-flags/", json=ff_data, headers=get_auth_header()
        )
        assert response.status_code == 409  # Conflict
        assert "already exists" in response.json()["detail"].lower()

    def test_create_feature_flag_invalid_key(self):
        """Test creating a feature flag with an invalid key."""
        ff_data = {
            "key": "Invalid Key With Spaces",  # Invalid key
            "name": "Test FF",
            "description": "Test description",
        }

        response = client.post(
            "/api/v1/feature-flags/", json=ff_data, headers=get_auth_header()
        )
        assert response.status_code == 422  # Validation error
        assert "key" in response.json()["detail"].lower()


class TestFeatureFlagRead:
    """Tests for reading feature flags."""

    def test_get_feature_flag_by_id(self):
        """Test retrieving a feature flag by ID."""
        # First create a feature flag
        flag_id = create_test_feature_flag(client)

        # Now retrieve it
        response = client.get(
            f"/api/v1/feature-flags/{flag_id}", headers=get_auth_header()
        )
        assert response.status_code == 200
        assert response.json()["id"] == flag_id

    def test_get_feature_flag_not_found(self):
        """Test retrieving a non-existent feature flag."""
        non_existent_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/feature-flags/{non_existent_id}", headers=get_auth_header()
        )
        assert response.status_code == 404

    def test_list_feature_flags(self):
        """Test listing feature flags with filtering."""
        # Create test feature flags
        create_test_feature_flag(client, key="test-ff-1", status="active")
        create_test_feature_flag(client, key="test-ff-2", status="inactive")

        # Test basic listing
        response = client.get("/api/v1/feature-flags/", headers=get_auth_header())
        assert response.status_code == 200
        assert len(response.json()) >= 2

        # Test filtering by status
        response = client.get(
            "/api/v1/feature-flags/?status_filter=active", headers=get_auth_header()
        )
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1
        assert all(item["status"] == "active" for item in results)


class TestFeatureFlagUpdate:
    """Tests for updating feature flags."""

    def test_update_feature_flag_success(self):
        """Test successful feature flag update."""
        # First create a feature flag
        flag_id = create_test_feature_flag(client)

        # Update data
        update_data = {
            "name": "Updated Flag Name",
            "description": "Updated description",
            "rollout_percentage": 25,
        }

        response = client.put(
            f"/api/v1/feature-flags/{flag_id}",
            json=update_data,
            headers=get_auth_header(),
        )
        assert response.status_code == 200
        assert response.json()["name"] == update_data["name"]
        assert (
            response.json()["rollout_percentage"] == update_data["rollout_percentage"]
        )

    def test_update_feature_flag_key_conflict(self):
        """Test updating a feature flag with a key that conflicts with another flag."""
        # Create two feature flags
        flag1_id = create_test_feature_flag(client, key="flag-1-key")
        create_test_feature_flag(client, key="flag-2-key")

        # Try to update flag1 to use flag2's key
        update_data = {"key": "flag-2-key"}

        response = client.put(
            f"/api/v1/feature-flags/{flag1_id}",
            json=update_data,
            headers=get_auth_header(),
        )
        assert response.status_code == 409  # Conflict
        assert "already exists" in response.json()["detail"].lower()


class TestFeatureFlagDelete:
    """Tests for deleting feature flags."""

    def test_delete_feature_flag_success(self):
        """Test successful feature flag deletion."""
        # First create a feature flag
        flag_id = create_test_feature_flag(client)

        # Delete it
        response = client.delete(
            f"/api/v1/feature-flags/{flag_id}", headers=get_auth_header()
        )
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/feature-flags/{flag_id}", headers=get_auth_header()
        )
        assert get_response.status_code == 404

    def test_delete_feature_flag_not_found(self):
        """Test deleting a non-existent feature flag."""
        non_existent_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/v1/feature-flags/{non_existent_id}", headers=get_auth_header()
        )
        assert response.status_code == 404


class TestFeatureFlagStatusChange:
    """Tests for changing feature flag status."""

    def test_activate_feature_flag(self):
        """Test activating a feature flag."""
        flag_id = create_test_feature_flag(client, status="inactive")

        response = client.post(
            f"/api/v1/feature-flags/{flag_id}/activate", headers=get_auth_header()
        )
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_deactivate_feature_flag(self):
        """Test deactivating a feature flag."""
        flag_id = create_test_feature_flag(client, status="active")

        response = client.post(
            f"/api/v1/feature-flags/{flag_id}/deactivate", headers=get_auth_header()
        )
        assert response.status_code == 200
        assert response.json()["status"] == "inactive"


class TestFeatureFlagEvaluation:
    """Tests for evaluating feature flags."""

    def test_evaluate_feature_flag(self):
        """Test evaluating a feature flag for a user."""
        # Create an active feature flag with 100% rollout
        flag_key = "test-evaluation"
        create_test_feature_flag(
            client, key=flag_key, status="active", rollout_percentage=100
        )

        # Evaluate for a user
        response = client.get(
            f"/api/v1/feature-flags/evaluate/{flag_key}?user_id=test-user-1",
            headers=get_auth_header(),
        )
        assert response.status_code == 200
        assert "enabled" in response.json()
        assert response.json()["enabled"] is True  # Since rollout is 100%

        # Create another flag with 0% rollout
        zero_flag_key = "zero-rollout"
        create_test_feature_flag(
            client, key=zero_flag_key, status="active", rollout_percentage=0
        )

        # Evaluate for a user
        response = client.get(
            f"/api/v1/feature-flags/evaluate/{zero_flag_key}?user_id=test-user-1",
            headers=get_auth_header(),
        )
        assert response.status_code == 200
        assert "enabled" in response.json()
        assert response.json()["enabled"] is False  # Since rollout is 0%

    def test_get_all_flags_for_user(self):
        """Test getting all feature flags for a user."""
        # Create several active feature flags
        create_test_feature_flag(
            client, key="flag-a", status="active", rollout_percentage=100
        )
        create_test_feature_flag(
            client, key="flag-b", status="active", rollout_percentage=0
        )
        create_test_feature_flag(
            client, key="flag-c", status="inactive", rollout_percentage=100
        )

        # Get all flags for a user
        user_id = "test-user-123"
        response = client.get(
            f"/api/v1/feature-flags/user/{user_id}", headers=get_auth_header()
        )
        assert response.status_code == 200

        # Check results
        flags = response.json()
        assert "flag-a" in flags
        assert flags["flag-a"] is True
        assert "flag-b" in flags
        assert flags["flag-b"] is False
        assert "flag-c" not in flags  # Inactive flags shouldn't be included

    def test_targeting_rules(self):
        """Test feature flag targeting rules."""
        # Create feature flag with targeting rules
        flag_key = "targeted-flag"
        create_test_feature_flag(
            client,
            key=flag_key,
            status="active",
            rollout_percentage=100,
            targeting_rules={
                "type": "context",
                "conditions": [
                    {"attribute": "country", "operator": "eq", "value": "US"}
                ],
            },
        )

        # Evaluate with matching context
        response = client.get(
            f"/api/v1/feature-flags/evaluate/{flag_key}?user_id=user-1",
            headers=get_auth_header(),
            json={"context": {"country": "US"}},
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is True

        # Evaluate with non-matching context
        response = client.get(
            f"/api/v1/feature-flags/evaluate/{flag_key}?user_id=user-2",
            headers=get_auth_header(),
            json={"context": {"country": "UK"}},
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is False
