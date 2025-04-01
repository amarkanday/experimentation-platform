"""
API routing tests.

This module contains unit and integration tests for the API routing system.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app, create_application
from backend.app.api.api import api_router
from backend.app.db.session import Base, get_db

# Create test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup database for testing
Base.metadata.create_all(bind=engine)


# Dependency override
def override_get_db():
    """Override the get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Configure test client
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestAPIRouting:
    """Tests for API routing functionality."""

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"

    def test_api_v1_prefix(self):
        """Test that API v1 prefix is correctly applied."""
        # Try accessing a non-existent endpoint with the API prefix
        response = client.get("/api/v1/nonexistent")
        # Should return 404, but importantly, the router should recognize
        # the prefix and try to route it (not 404 due to prefix not found)
        assert response.status_code == 404
        
        # Try without prefix - should get a different error (not found at root)
        wrong_prefix_response = client.get("/nonexistent")
        assert wrong_prefix_response.status_code == 404

    def test_docs_endpoints(self):
        """Test that documentation endpoints are accessible."""
        # OpenAPI JSON
        openapi_response = client.get("/api/v1/openapi.json")
        assert openapi_response.status_code == 200
        
        # Swagger UI
        swagger_response = client.get("/api/v1/docs")
        assert swagger_response.status_code == 200
        
        # ReDoc
        redoc_response = client.get("/api/v1/redoc")
        assert redoc_response.status_code == 200

    def test_all_routers_included(self):
        """Test that all expected routers are included in the API."""
        openapi_schema = client.get("/api/v1/openapi.json").json()
        
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

    def test_route_tags(self):
        """Test that routes have appropriate tags for documentation."""
        openapi_schema = client.get("/api/v1/openapi.json").json()
        
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
