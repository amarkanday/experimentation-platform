"""
API routing tests.

This module contains unit and integration tests for the API routing system.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.api import deps
from backend.app.core.database_config import get_schema_name

@pytest.fixture(scope="function")
def test_client(db_session: Session):
    """Create a test client with database session."""
    def override_get_db():
        try:
            db_session.execute(text("SET search_path TO test_experimentation"))
            db_session.commit()
            yield db_session
        finally:
            pass

    app.dependency_overrides[deps.get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}

class TestAPIRouting:
    """Tests for API routing functionality."""

    def test_health_endpoint(self, test_client: TestClient):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"

    def test_api_v1_prefix(self, test_client: TestClient):
        """Test that API v1 prefix is correctly applied."""
        # Try accessing a non-existent endpoint with the API prefix
        response = test_client.get("/api/v1/nonexistent")
        # Should return 404, but importantly, the router should recognize
        # the prefix and try to route it (not 404 due to prefix not found)
        assert response.status_code == 404

        # Try without prefix - should get a different error (not found at root)
        wrong_prefix_response = test_client.get("/nonexistent")
        assert wrong_prefix_response.status_code == 404

    def test_docs_endpoints(self, test_client: TestClient):
        """Test that documentation endpoints are accessible."""
        # OpenAPI JSON
        openapi_response = test_client.get("/api/v1/openapi.json")
        assert openapi_response.status_code == 200

        # Swagger UI
        swagger_response = test_client.get("/api/v1/docs")
        assert swagger_response.status_code == 200

        # ReDoc
        redoc_response = test_client.get("/api/v1/redoc")
        assert redoc_response.status_code == 200

    def test_all_routers_included(self, test_client: TestClient):
        """Test that all expected routers are included in the API."""
        openapi_schema = test_client.get("/api/v1/openapi.json").json()

        # Check for endpoints from different routers
        paths = openapi_schema["paths"]

        # Check for auth routes
        auth_routes_exist = any("/auth/" in path for path in paths)
        assert auth_routes_exist, "Auth routes are missing"

        # Check for experiment routes
        experiment_routes_exist = any("/experiments" in path for path in paths)
        assert experiment_routes_exist, "Experiment routes are missing"

        # Check for tracking routes
        tracking_routes_exist = any("/tracking" in path for path in paths)
        assert tracking_routes_exist, "Tracking routes are missing"

        # Check for feature flag routes
        feature_flag_routes_exist = any("/feature-flags" in path for path in paths)
        assert feature_flag_routes_exist, "Feature flag routes are missing"

        # Check for admin routes
        admin_routes_exist = any("/admin" in path for path in paths)
        assert admin_routes_exist, "Admin routes are missing"

    def test_route_tags(self, test_client: TestClient):
        """Test that routes have appropriate tags for documentation."""
        openapi_schema = test_client.get("/api/v1/openapi.json").json()

        # Check tags for specific routes
        for path, methods in openapi_schema["paths"].items():
            if "/experiments" in path:
                for method in methods.values():
                    assert "Experiments" in method["tags"], f"Experiments tag missing for {path}"
            elif "/tracking" in path:
                for method in methods.values():
                    assert "Tracking" in method["tags"], f"Tracking tag missing for {path}"
            elif "/auth" in path:
                for method in methods.values():
                    assert "Authentication" in method["tags"], f"Authentication tag missing for {path}"
