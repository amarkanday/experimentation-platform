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
from backend.tests.conftest import TestingSessionLocal

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
def test_user(db: Session) -> User:
    """Create a test user."""
    from backend.app.models.user import User

    # Create tables in the test transaction
    print("\nCreating tables in test transaction...")
    for table in Base.metadata.sorted_tables:
        table.schema = "test_experimentation"
        try:
            table.create(bind=db.get_bind(), checkfirst=True)
            print(f"Created table: {table.name}")
        except Exception as e:
            print(f"Error creating table {table.name}: {e}")

    # Set search path
    db.execute(text("SET search_path TO test_experimentation"))
    db.commit()

    user = User(
        id=TEST_USER_ID,  # Use the same ID as the mock_auth fixture
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_feature_flag(db: Session, test_user: User) -> FeatureFlag:
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
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag

@pytest.fixture
def mock_auth(test_user: User, engine):
    """Mock authentication dependencies."""
    def get_mock_user():
        return test_user

    def get_mock_db():
        connection = engine.connect()
        transaction = connection.begin()
        session = TestingSessionLocal(bind=connection)

        try:
            # Set search path to test schema
            session.execute(text("SET search_path TO test_experimentation"))
            session.commit()

            yield session
        finally:
            session.close()
            transaction.rollback()
            connection.close()

    app.dependency_overrides[deps.get_current_user] = get_mock_user
    app.dependency_overrides[deps.get_current_active_user] = get_mock_user
    app.dependency_overrides[deps.get_current_superuser] = get_mock_user
    app.dependency_overrides[deps.get_db] = get_mock_db

    yield

    app.dependency_overrides = {}

class TestFeatureFlagEndpoints:
    """Test suite for feature flag endpoints."""

    def test_create_feature_flag(self, client: TestClient, db: Session, mock_auth, test_user: User):
        """Test creating a new feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_user)
        db.commit()

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

    def test_create_duplicate_feature_flag(self, client: TestClient, db: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test creating a feature flag with duplicate key."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Verify the feature flag exists in the database
        existing_flag = db.query(FeatureFlag).filter(FeatureFlag.key == test_feature_flag.key).first()
        print(f"\nExisting flag in database: {existing_flag.key if existing_flag else 'None'}")

        # Merge the test feature flag to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

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

    def test_get_feature_flag(self, client: TestClient, db: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test retrieving a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

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

    def test_get_nonexistent_feature_flag(self, client: TestClient, db: Session, mock_auth):
        """Test retrieving a nonexistent feature flag."""
        response = client.get(
            f"/api/v1/feature-flags/{uuid.uuid4()}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404

    def test_update_feature_flag(self, client: TestClient, db: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test updating a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

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

    def test_delete_feature_flag(self, client: TestClient, db: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test deleting a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Store the ID before deletion
        flag_id = test_feature_flag.id

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

        response = client.delete(
            f"/api/v1/feature-flags/{flag_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 204

        # Verify flag is deleted using a fresh query
        flag = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
        assert flag is None

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_activate_feature_flag(self, client: TestClient, db: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test activating a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/activate",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FeatureFlagStatus.ACTIVE.value

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_deactivate_feature_flag(self, client: TestClient, db: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test deactivating a feature flag."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

        # First activate the flag using the service
        flag_service = FeatureFlagService(db)
        flag_service.activate_feature_flag(test_feature_flag)

        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/deactivate",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FeatureFlagStatus.INACTIVE.value

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_evaluate_feature_flag(self, client: TestClient, db: Session, test_feature_flag: FeatureFlag):
        """Test evaluating a feature flag for a user."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Create a test API key
        test_api_key = APIKey(
            key="test-api-key",
            name="Test API Key",
            user_id=test_feature_flag.owner_id,
            is_active=True
        )
        db.add(test_api_key)
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

        # First activate the flag using the service
        flag_service = FeatureFlagService(db)
        flag_service.activate_feature_flag(test_feature_flag)

        response = client.get(
            f"/api/v1/feature-flags/evaluate/{test_feature_flag.key}",
            params={"user_id": "test-user-1"},
            headers={"X-API-Key": "test-api-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "config" in data

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_get_user_flags(self, client: TestClient, db: Session, test_feature_flag: FeatureFlag):
        """Test getting all feature flags for a user."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Create a test API key
        test_api_key = APIKey(
            key="test-api-key",
            name="Test API Key",
            user_id=test_feature_flag.owner_id,
            is_active=True
        )
        db.add(test_api_key)
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

        # First activate the flag using the service
        flag_service = FeatureFlagService(db)
        flag_service.activate_feature_flag(test_feature_flag)

        response = client.get(
            f"/api/v1/feature-flags/user/test-user-1",
            headers={"X-API-Key": "test-api-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert test_feature_flag.key in data

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_list_feature_flags(self, client: TestClient, db: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test listing feature flags with filters."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

        response = client.get(
            "/api/v1/feature-flags/",
            params={
                "skip": 0,
                "limit": 10,
                "status_filter": FeatureFlagStatus.INACTIVE.value
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["id"] == str(test_feature_flag.id)

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_list_feature_flags_with_search(self, client: TestClient, db: Session, mock_auth, test_feature_flag: FeatureFlag):
        """Test listing feature flags with search."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Merge the test user to ensure it exists in this session
        db.merge(test_feature_flag)
        db.commit()

        response = client.get(
            "/api/v1/feature-flags/",
            params={"search": "Test Feature"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["id"] == str(test_feature_flag.id)

        # Clean up the dependency override
        app.dependency_overrides.pop(deps.get_db, None)

    def test_feature_flag_validation(self, client: TestClient, db: Session, mock_auth):
        """Test feature flag validation rules."""
        # Override the get_db dependency to use the test session
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[deps.get_db] = override_get_db

        # Ensure the test user exists in the database
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        invalid_data = {
            "key": "INVALID-KEY",  # Should be lowercase
            "name": "",  # Should not be empty
            "rollout_percentage": 150  # Should be between 0 and 100
        }

        response = client.post(
            "/api/v1/feature-flags/",
            json=invalid_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error

        # Clean up the dependency override
    def test_schema_name(self):
        """Test schema name determination."""
        print(f"Current schema name: {get_schema_name()}")

    def test_schema_name_in_test(self, db: Session):
        """Test that schema name is test_experimentation during tests."""
        from backend.app.core.database_config import get_schema_name

        # Verify we're in a test environment
        assert "PYTEST_CURRENT_TEST" in os.environ, "Test environment not detected"

        # Get schema name
        schema_name = get_schema_name()
        print(f"\nCurrent schema name: {schema_name}")

        # Verify schema name
        assert schema_name == "test_experimentation", f"Expected test_experimentation, got {schema_name}"

        # Create tables in the test transaction
        print("\nCreating tables in test transaction...")
        for table in Base.metadata.sorted_tables:
            table.schema = "test_experimentation"
            try:
                table.create(bind=db.get_bind(), checkfirst=True)
                print(f"Created table: {table.name}")
            except Exception as e:
                print(f"Error creating table {table.name}: {e}")

        # Set search path
        db.execute(text("SET search_path TO test_experimentation"))
        db.commit()

        # Verify tables are in the correct schema
        inspector = inspect(db.get_bind())
        tables = inspector.get_table_names(schema="test_experimentation")
        print("\nTables in test_experimentation schema:")
        for table in tables:
            print(f"- {table}")
            # Print columns for each table
            columns = inspector.get_columns(table, schema="test_experimentation")
            print("  Columns:")
            for column in columns:
                print(f"    - {column['name']}: {column['type']}")

        # Verify users table exists in the correct schema
        assert "users" in tables, "Users table not found in test_experimentation schema"

    def test_your_feature(self, client, db, test_user, debug_db):
        from backend.app.core.database_config import get_schema_name
        print(f"Schema name in test: {get_schema_name()}")
        debug_db()  # This will show the current database state
        # ... rest of your test
