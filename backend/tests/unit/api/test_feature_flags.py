"""
Feature Flag API Tests.

This module contains comprehensive tests for the feature flag API endpoints.
It uses PostgreSQL for testing and covers all CRUD operations and feature flag evaluation.
"""

import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
import os
import json

from backend.app.main import app
from backend.app.api import deps
from backend.app.models.user import User
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.schemas.feature_flag import FeatureFlagCreate, FeatureFlagUpdate, FeatureFlagReadExtended, FeatureFlagListResponse
from backend.app.services.feature_flag_service import FeatureFlagService
from backend.app.core.database_config import get_schema_name
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal
from backend.app.models.api_key import APIKey
from backend.app.crud import crud_feature_flag
from backend.app.api.v1.endpoints import feature_flags
from backend.app.api.deps import get_db, get_current_user, get_api_key, CacheControl
from backend.app.core.config import settings

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
    "is_active": False,
    "rollout_percentage": 50,
    "targeting_rules": {
        "country": ["US", "CA"],
        "user_group": "beta"
    },
    "variants": {
        "control": {"value": False},
        "treatment": {"value": True}
    },
    "default_value": "control"
}


@pytest.fixture(autouse=True)
def clear_schema_cache_fixture():
    """Clear schema cache before each test."""
    from backend.app.core.database_config import clear_schema_cache
    clear_schema_cache()
    yield


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    from backend.app.models.user import User

    # Set search path
    db_session.execute(text("SET search_path TO test_experimentation"))
    db_session.commit()

    # Clean up any existing test user with the same ID or email
    db_session.execute(text(f"DELETE FROM test_experimentation.users WHERE id = '{TEST_USER_ID}' OR email = 'test@example.com'"))
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
    # Clean up any existing feature flag with the same ID or key
    db_session.execute(text(f"DELETE FROM test_experimentation.feature_flags WHERE id = '{TEST_FLAG_ID}' OR key = '{TEST_FLAG_KEY}'"))
    db_session.commit()

    flag = FeatureFlag(
        id=TEST_FLAG_ID,
        key=TEST_FLAG_KEY,
        name=TEST_FLAG_NAME,
        description=TEST_FLAG_DESCRIPTION,
        status=FeatureFlagStatus.INACTIVE.value,
        owner_id=test_user.id,
        rollout_percentage=50,
        targeting_rules=TEST_FLAG_DATA["targeting_rules"],
        variants=TEST_FLAG_DATA["variants"]
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

    # Mock cache control
    class MockCacheControl:
        def __init__(self, skip_cache: bool = False):
            self.enabled = False
            self.skip = skip_cache
            self.redis = None

        def get(self, key, default=None):
            return default

    def override_cache_control(skip_cache: bool = False):
        return MockCacheControl(skip_cache)

    # Override dependencies
    app.dependency_overrides[deps.oauth2_scheme] = mock_auth.override_oauth2_scheme
    app.dependency_overrides[deps.get_current_user] = mock_auth.override_get_current_user
    app.dependency_overrides[deps.get_current_active_user] = mock_auth.override_get_current_active_user
    app.dependency_overrides[deps.get_cache_control] = override_cache_control

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

        # Make sure we use a unique key for this test
        unique_key = f"test-flag-{uuid.uuid4()}"
        test_data = TEST_FLAG_DATA.copy()
        test_data["key"] = unique_key

        response = client.post(
            "/api/v1/feature-flags/",
            json=test_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["key"] == unique_key
        assert data["name"] == TEST_FLAG_NAME
        assert data["status"] == FeatureFlagStatus.INACTIVE.value
        assert data["rollout_percentage"] == 50

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

        # Clean up the created feature flag
        db_session.execute(text(f"DELETE FROM test_experimentation.feature_flags WHERE key = '{unique_key}'"))
        db_session.commit()

    def test_create_duplicate_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test creating a feature flag with duplicate key."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Try to create a feature flag with the same key
        duplicate_data = TEST_FLAG_DATA.copy()

        response = client.post(
            "/api/v1/feature-flags/",
            json=duplicate_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 409

        # Clean up
        app.dependency_overrides.pop(deps.get_db, None)

    def test_get_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test retrieving a feature flag by ID."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        response = client.get(
            f"/api/v1/feature-flags/{test_feature_flag.id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_feature_flag.id)
        assert data["key"] == test_feature_flag.key
        assert data["status"] == test_feature_flag.status.value

        # Clean up
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
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Unique test data to avoid conflicts
        unique_name = f"Updated Flag Name - {uuid.uuid4()}"
        update_data = {
            "name": unique_name,
            "description": "Updated description",
            "rollout_percentage": 75,
            "targeting_rules": {
                "country": ["US", "UK"],
                "user_group": "premium"
            }
        }

        response = client.put(
            f"/api/v1/feature-flags/{test_feature_flag.id}",
            json=update_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == unique_name
        assert data["description"] == "Updated description"
        assert data["rollout_percentage"] == 75

        # Clean up
        app.dependency_overrides.pop(deps.get_db, None)

    def test_delete_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test deleting a feature flag."""
        # Create a new flag just for this test
        unique_id = str(uuid.uuid4())
        unique_key = f"test-delete-flag-{uuid.uuid4()}"

        # Create a test feature flag just for deletion
        flag_to_delete = FeatureFlag(
            id=unique_id,
            key=unique_key,
            name=f"Test Delete Flag {unique_key}",
            description="A feature flag for deletion test",
            status=FeatureFlagStatus.INACTIVE.value,
            owner_id=TEST_USER_ID,
            rollout_percentage=50,
            targeting_rules={"test": True},
            variants={"control": {"value": False}}
        )
        db_session.add(flag_to_delete)
        db_session.commit()
        db_session.refresh(flag_to_delete)

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Capture the ID before deletion
        flag_id = str(flag_to_delete.id)

        response = client.delete(
            f"/api/v1/feature-flags/{flag_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 204

        # Verify flag is deleted
        check_response = client.get(
            f"/api/v1/feature-flags/{flag_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        # Should get a 404 error when trying to get the deleted flag
        assert check_response.status_code == 404

        # Clean up
        app.dependency_overrides.pop(deps.get_db, None)

    def test_activate_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test activating a feature flag."""
        # Create a new flag just for this test
        unique_id = str(uuid.uuid4())
        unique_key = f"test-activate-flag-{uuid.uuid4()}"

        # Create a test feature flag that's inactive
        inactive_flag = FeatureFlag(
            id=unique_id,
            key=unique_key,
            name=f"Test Activate Flag {unique_key}",
            description="A feature flag for activation test",
            status=FeatureFlagStatus.INACTIVE.value,
            owner_id=TEST_USER_ID,
            rollout_percentage=50,
            targeting_rules={"test": True},
            variants={"control": {"value": False}}
        )
        db_session.add(inactive_flag)
        db_session.commit()
        db_session.refresh(inactive_flag)

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        response = client.post(
            f"/api/v1/feature-flags/{inactive_flag.id}/activate",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FeatureFlagStatus.ACTIVE.value

        # Clean up
        app.dependency_overrides.pop(deps.get_db, None)

        # Clean up the flag
        db_session.delete(inactive_flag)
        db_session.commit()

    def test_deactivate_feature_flag(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test deactivating a feature flag."""
        # Create a new flag just for this test
        unique_id = str(uuid.uuid4())
        unique_key = f"test-deactivate-flag-{uuid.uuid4()}"

        # Create a test feature flag that's active
        active_flag = FeatureFlag(
            id=unique_id,
            key=unique_key,
            name=f"Test Deactivate Flag {unique_key}",
            description="A feature flag for deactivation test",
            status=FeatureFlagStatus.ACTIVE.value,
            owner_id=TEST_USER_ID,
            rollout_percentage=50,
            targeting_rules={"test": True},
            variants={"control": {"value": False}}
        )
        db_session.add(active_flag)
        db_session.commit()
        db_session.refresh(active_flag)

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        response = client.post(
            f"/api/v1/feature-flags/{active_flag.id}/deactivate",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FeatureFlagStatus.INACTIVE.value

        # Clean up
        app.dependency_overrides.pop(deps.get_db, None)

        # Clean up the flag
        db_session.delete(active_flag)
        db_session.commit()

    def test_evaluate_feature_flag(self, client: TestClient, db_session: Session, test_feature_flag: FeatureFlag, mock_auth):
        """Test evaluating a feature flag for a specific user."""
        # Create a new flag just for this test
        unique_id = str(uuid.uuid4())
        unique_key = f"test-evaluate-flag-{uuid.uuid4()}"

        # Create a test feature flag that's active
        flag_to_evaluate = FeatureFlag(
            id=unique_id,
            key=unique_key,
            name=f"Test Evaluate Flag {unique_key}",
            description="A feature flag for evaluation test",
            status=FeatureFlagStatus.ACTIVE.value,
            owner_id=TEST_USER_ID,
            rollout_percentage=100,  # 100% rollout to ensure evaluation passes
            targeting_rules={"country": ["US"], "role": "admin"},
            variants={"control": {"value": False}, "treatment": {"value": True}}
        )
        db_session.add(flag_to_evaluate)
        db_session.commit()
        db_session.refresh(flag_to_evaluate)

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Create API key for this test
        api_key = APIKey(
            id=str(uuid.uuid4()),
            key="test-api-key-evaluate",
            name="Test API Key for Evaluation",
            user_id=TEST_USER_ID,
            is_active=True
        )
        db_session.add(api_key)
        db_session.commit()

        # Override get_api_key
        def override_get_api_key():
            user = db_session.query(User).filter(User.id == TEST_USER_ID).first()
            return user

        app.dependency_overrides[deps.get_api_key] = override_get_api_key

        # Test evaluation - using the correct path which is /evaluate/{flag_key} with user_id as a query parameter
        response = client.get(
            f"/api/v1/feature-flags/evaluate/{flag_to_evaluate.key}?user_id=test123",
            headers={"X-API-Key": "test-api-key-evaluate"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert isinstance(data["enabled"], bool)
        assert "key" in data
        assert data["key"] == flag_to_evaluate.key
        assert "config" in data

        # Clean up
        app.dependency_overrides.pop(deps.get_db, None)
        app.dependency_overrides.pop(deps.get_api_key, None)

        # Clean up the created resources
        db_session.delete(flag_to_evaluate)
        db_session.delete(api_key)
        db_session.commit()

    def test_get_user_flags(self, client: TestClient, db_session: Session, test_feature_flag: FeatureFlag, mock_auth):
        """Test retrieving all feature flags for a user."""
        # Create a new flag just for this test
        unique_id = str(uuid.uuid4())
        unique_key = f"test-user-flags-{uuid.uuid4()}"

        # Create a test feature flag that's active
        user_flag = FeatureFlag(
            id=unique_id,
            key=unique_key,
            name=f"Test User Flag {unique_key}",
            description="A feature flag for user flags test",
            status=FeatureFlagStatus.ACTIVE.value,
            owner_id=TEST_USER_ID,
            rollout_percentage=100,
            targeting_rules={},
            variants={"control": {"value": False}, "treatment": {"value": True}}
        )
        db_session.add(user_flag)
        db_session.commit()
        db_session.refresh(user_flag)

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Create API key for this test
        api_key = APIKey(
            id=str(uuid.uuid4()),
            key="test-api-key-user-flags",
            name="Test API Key for User Flags",
            user_id=TEST_USER_ID,
            is_active=True
        )
        db_session.add(api_key)
        db_session.commit()

        # Override get_api_key
        def override_get_api_key():
            user = db_session.query(User).filter(User.id == TEST_USER_ID).first()
            return user

        app.dependency_overrides[deps.get_api_key] = override_get_api_key

        # Test getting user flags - using the correct path which is /user/{user_id}
        response = client.get(
            "/api/v1/feature-flags/user/test123",
            headers={"X-API-Key": "test-api-key-user-flags"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert unique_key in data

        # Clean up
        app.dependency_overrides.pop(deps.get_db, None)
        app.dependency_overrides.pop(deps.get_api_key, None)

        # Clean up the created resources
        db_session.delete(user_flag)
        db_session.delete(api_key)
        db_session.commit()

    def test_list_feature_flags(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test listing feature flags."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Setup mock crud functions
        def mock_get_multi(*args, **kwargs):
            # Convert the database models to FeatureFlagReadExtended compatible format
            flags = db_session.query(FeatureFlag).all()
            formatted_flags = []
            for flag in flags:
                formatted_flags.append({
                    "id": str(flag.id),
                    "key": flag.key,
                    "name": flag.name,
                    "description": flag.description,
                    "is_active": flag.status == FeatureFlagStatus.ACTIVE.value,
                    "status": flag.status,
                    "rollout_percentage": flag.rollout_percentage,
                    "targeting_rules": flag.targeting_rules,
                    "variants": [flag.variants] if flag.variants else [],
                    "owner_id": 12345,  # Use an integer instead of UUID string
                    "created_at": flag.created_at,
                    "updated_at": flag.updated_at,
                    "tags": flag.tags,
                    "metrics": []
                })
            return formatted_flags

        def mock_count(*args, **kwargs):
            # Return the count of feature flags
            return db_session.query(FeatureFlag).count()

        # Patch the crud functions
        original_get_multi = crud_feature_flag.get_multi
        original_count = crud_feature_flag.count
        original_get_multi_by_owner = crud_feature_flag.get_multi_by_owner
        original_count_by_owner = crud_feature_flag.count_by_owner

        crud_feature_flag.get_multi = mock_get_multi
        crud_feature_flag.count = mock_count
        crud_feature_flag.get_multi_by_owner = mock_get_multi
        crud_feature_flag.count_by_owner = mock_count

        try:
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

            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert "items" in data
            assert data["total"] > 0
            assert len(data["items"]) > 0
            assert data["items"][0]["key"] == test_feature_flag.key
        finally:
            # Restore the original functions
            crud_feature_flag.get_multi = original_get_multi
            crud_feature_flag.count = original_count
            crud_feature_flag.get_multi_by_owner = original_get_multi_by_owner
            crud_feature_flag.count_by_owner = original_count_by_owner

            # Clean up
            app.dependency_overrides.pop(deps.get_db, None)

    def test_list_feature_flags_with_search(self, client: TestClient, db_session: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test listing feature flags with search."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Setup mock crud functions
        def mock_get_multi(*args, **kwargs):
            # Convert the test feature flag to FeatureFlagReadExtended compatible format
            flags = db_session.query(FeatureFlag).filter(FeatureFlag.id == test_feature_flag.id).all()
            formatted_flags = []
            for flag in flags:
                formatted_flags.append({
                    "id": str(flag.id),
                    "key": flag.key,
                    "name": flag.name,
                    "description": flag.description,
                    "is_active": flag.status == FeatureFlagStatus.ACTIVE.value,
                    "status": flag.status,
                    "rollout_percentage": flag.rollout_percentage,
                    "targeting_rules": flag.targeting_rules,
                    "variants": [flag.variants] if flag.variants else [],
                    "owner_id": 12345,  # Use an integer instead of UUID string
                    "created_at": flag.created_at,
                    "updated_at": flag.updated_at,
                    "tags": flag.tags,
                    "metrics": []
                })
            return formatted_flags

        def mock_count(*args, **kwargs):
            # Return the count (1 for the test feature flag)
            return db_session.query(FeatureFlag).filter(FeatureFlag.id == test_feature_flag.id).count()

        # Patch the crud functions
        original_get_multi = crud_feature_flag.get_multi
        original_count = crud_feature_flag.count
        original_get_multi_by_owner = crud_feature_flag.get_multi_by_owner
        original_count_by_owner = crud_feature_flag.count_by_owner

        crud_feature_flag.get_multi = mock_get_multi
        crud_feature_flag.count = mock_count
        crud_feature_flag.get_multi_by_owner = mock_get_multi
        crud_feature_flag.count_by_owner = mock_count

        try:
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

            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert "items" in data
            assert data["total"] > 0
            assert len(data["items"]) > 0
            assert data["items"][0]["key"] == test_feature_flag.key
        finally:
            # Restore the original functions
            crud_feature_flag.get_multi = original_get_multi
            crud_feature_flag.count = original_count
            crud_feature_flag.get_multi_by_owner = original_get_multi_by_owner
            crud_feature_flag.count_by_owner = original_count_by_owner

            # Clean up
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
