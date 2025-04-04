"""
Feature Flag API Tests.

This module contains comprehensive tests for the feature flag API endpoints.
It uses PostgreSQL for testing and covers all CRUD operations and feature flag evaluation.
"""

import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
import os

from backend.app.main import app
from backend.app.api import deps
from backend.app.models.user import User
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.schemas.feature_flag import FeatureFlagCreate, FeatureFlagUpdate
from backend.app.services.feature_flag_service import FeatureFlagService
from backend.app.core.database_config import get_schema_name
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal
from backend.app.models.api_key import APIKey

# Test constants
TEST_USER_ID = "bce3f687-ac5f-4735-9b63-d4f2efcc36e7"  # Match the ID from the mock_auth fixture
TEST_FLAG_ID = str(uuid.uuid4())
TEST_FLAG_KEY = "test-feature-flag"
TEST_FLAG_NAME = "Test Feature Flag"
TEST_FLAG_DESCRIPTION = "A test feature flag for testing purposes"

# Test data
TEST_FLAG_DATA = {
    "key": TEST_FLAG_KEY,
    "name": TEST_FLAG_NAME,
    "description": TEST_FLAG_DESCRIPTION,
    "status": FeatureFlagStatus.INACTIVE.value,
    "rollout_percentage": 50,
    "targeting_rules": {
        "country": ["US", "CA"],
        "user_group": "beta"
    },
    "value": {
        "variants": {
            "control": {"value": False},
            "treatment": {"value": True}
        },
        "default": "control"
    }
}

@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    from backend.app.models.user import User

    # Set search path
    db_session.execute(text("SET search_path TO test_experimentation"))
    db_session.commit()

    user = User(
        id=TEST_USER_ID,  # Use the same ID as the mock_auth fixture
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_feature_flag(db_session: Session, test_user: User) -> FeatureFlag:
    """Create a test feature flag."""
    flag = FeatureFlag(
        id=TEST_FLAG_ID,
        key=TEST_FLAG_KEY,
        name=TEST_FLAG_NAME,
        description=TEST_FLAG_DESCRIPTION,
        status=FeatureFlagStatus.INACTIVE.value,
        owner_id=test_user.id,
        rollout_percentage=50,
        targeting_rules=TEST_FLAG_DATA["targeting_rules"],
        variants=TEST_FLAG_DATA["value"]["variants"]
    )
    db_session.add(flag)
    db_session.commit()
    db_session.refresh(flag)
    return flag

@pytest.fixture
def mock_auth():
    """Mock authentication for testing."""
    class MockAuth:
        def override_get_current_user(self):
            return User(
                id=TEST_USER_ID,
                username="test_user",
                email="test@example.com",
                full_name="Test User",
                is_active=True,
                is_superuser=True,
            )

        def override_get_current_active_user(self):
            return self.override_get_current_user()

        def override_oauth2_scheme(self):
            return "test-token"

    mock_auth = MockAuth()

    # Mock the auth_service.get_user method
    def mock_get_user(access_token: str) -> Dict[str, Any]:
        return {
            "username": "test_user",
            "attributes": {
                "email": "test@example.com",
                "given_name": "Test",
                "family_name": "User"
            }
        }

    # Apply the mock
    from backend.app.services.auth_service import auth_service
    auth_service.get_user = mock_get_user

    # Override dependencies
    app.dependency_overrides[deps.oauth2_scheme] = mock_auth.override_oauth2_scheme
    app.dependency_overrides[deps.get_current_user] = mock_auth.override_get_current_user
    app.dependency_overrides[deps.get_current_active_user] = mock_auth.override_get_current_active_user

    yield mock_auth

    # Clean up
    app.dependency_overrides = {}

class TestFeatureFlagEndpoints:
    """Test suite for feature flag endpoints."""

    def test_create_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_user: User):
        """Test creating a new feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test user to ensure it exists in this session
        db_session.merge(test_user)
        db_session.commit()

        response = client.post(
            "/api/v1/feature-flags/",
            json=TEST_FLAG_DATA,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["key"] == TEST_FLAG_KEY
        assert data["name"] == TEST_FLAG_NAME
        assert data["status"] == FeatureFlagStatus.INACTIVE.value
        assert data["rollout_percentage"] == 50

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_create_duplicate_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test creating a feature flag with duplicate key."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Verify the feature flag exists in the database
        existing_flag = db_session.query(FeatureFlag).filter(FeatureFlag.key == test_feature_flag.key).first()
        print(f"\nExisting flag in database: {existing_flag.key if existing_flag else 'None'}")

        # Merge the test feature flag to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        print("\nMaking POST request to create duplicate feature flag")
        response = client.post(
            "/api/v1/feature-flags/",
            json=TEST_FLAG_DATA,
            headers={"Authorization": "Bearer test-token"}
        )

        print(f"\nResponse status code: {response.status_code}")
        print(f"Response body: {response.json()}")

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_get_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test retrieving a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test user to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        response = client.get(
            f"/api/v1/feature-flags/{test_feature_flag.id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_feature_flag.id)
        assert data["key"] == TEST_FLAG_KEY

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_get_nonexistent_feature_flag(self, client: TestClient, db_session: Session, mock_auth):
        """Test retrieving a nonexistent feature flag."""
        response = client.get(
            f"/api/v1/feature-flags/{uuid.uuid4()}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404

    def test_update_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test updating a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test user to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        update_data = {
            "name": "Updated Feature Flag",
            "description": "Updated description",
            "rollout_percentage": 75
        }

        response = client.put(
            f"/api/v1/feature-flags/{test_feature_flag.id}",
            json=update_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["rollout_percentage"] == update_data["rollout_percentage"]

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_delete_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test deleting a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Store the ID before deletion
        flag_id = test_feature_flag.id

        # Merge the test user to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        response = client.delete(
            f"/api/v1/feature-flags/{flag_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 204

        # Verify flag is deleted using a fresh query
        flag = db_session.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
        assert flag is None

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_activate_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test activating a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test user to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/activate",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FeatureFlagStatus.ACTIVE.value

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_deactivate_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test deactivating a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure we're using the test schema
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test feature flag to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/deactivate",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FeatureFlagStatus.INACTIVE.value

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_evaluate_feature_flag(self, client: TestClient, db_session: Session, test_feature_flag: FeatureFlag, mock_auth):
        """Test evaluating a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db
        app.dependency_overrides[deps.get_api_key] = lambda: {"key": "test-api-key", "type": "test"}

        # Ensure we're using the test schema
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test feature flag to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        # Activate the feature flag
        test_feature_flag.status = FeatureFlagStatus.ACTIVE.value
        db_session.merge(test_feature_flag)
        db_session.commit()

        response = client.get(
            f"/api/v1/feature-flags/evaluate/{test_feature_flag.key}",
            params={"user_id": "test-user-id"},
            headers={"X-API-Key": "test-api-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data

        # Clean up the dependency overrides
        app.dependency_overrides.clear()

    def test_get_user_flags(self, client: TestClient, db_session: Session, test_feature_flag: FeatureFlag, mock_auth):
        """Test getting all feature flags for a user."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db
        app.dependency_overrides[deps.get_api_key] = lambda: {"key": "test-api-key", "type": "test"}

        # Ensure we're using the test schema
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test feature flag to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        response = client.get(
            f"/api/v1/feature-flags/user/{TEST_USER_ID}",
            params={"context": {}},
            headers={"X-API-Key": "test-api-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        # Clean up the dependency overrides
        app.dependency_overrides.clear()

    def test_list_feature_flags(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test listing all feature flags."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure we're using the test schema
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test feature flag to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        response = client.get(
            "/api/v1/feature-flags/",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["key"] == test_feature_flag.key

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_list_feature_flags_with_search(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test listing feature flags with search parameters."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure we're using the test schema
        db_session.execute(text("SET search_path TO test_experimentation"))
        db_session.commit()

        # Merge the test feature flag to ensure it exists in this session
        db_session.merge(test_feature_flag)
        db_session.commit()

        response = client.get(
            "/api/v1/feature-flags/",
            params={"search": test_feature_flag.key[:5]},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["key"] == test_feature_flag.key

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_feature_flag_validation(self, client: TestClient, db_session: Session, mock_auth):
        """Test feature flag validation."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Test invalid key format
        invalid_data = TEST_FLAG_DATA.copy()
        invalid_data["key"] = "Invalid Key!"
        response = client.post(
            "/api/v1/feature-flags/",
            json=invalid_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 422

        # Test invalid rollout percentage
        invalid_data = TEST_FLAG_DATA.copy()
        invalid_data["rollout_percentage"] = 150
        response = client.post(
            "/api/v1/feature-flags/",
            json=invalid_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 422

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_schema_name_in_test(self, db_session: Session):
        """Test that the schema name is correctly set in test environment."""
        schema_name = get_schema_name()
        assert schema_name == "test_experimentation"

        inspector = inspect(db_session.get_bind())
        assert "test_experimentation" in inspector.get_schema_names()
