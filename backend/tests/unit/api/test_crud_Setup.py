"""
Test cases for Experiment CRUD API endpoints - Application setup verification.
"""

import pytest
import inspect
from fastapi.testclient import TestClient

# Import the main application
from backend.app.main import app

# Create test client
client = TestClient(app)


def test_application_setup():
    """Verify the FastAPI application setup."""
    # Print application info
    print("\nApplication info:")
    print(f"App title: {app.title}")
    print(f"App version: {app.version}")
    print(f"Debug mode: {app.debug}")

    # Print registered routes
    print("\nRegistered routes:")
    for route in app.routes:
        print(f"  {route.path} [{', '.join(route.methods)}]")

    # Check if the router is properly mounted
    from backend.app.api.api import api_router

    print("\nAPI Router info:")
    print(f"API Router routes count: {len(api_router.routes)}")

    # Print API router routes
    print("\nAPI Router routes:")
    for route in api_router.routes:
        print(f"  {route.path} [{', '.join(route.methods)}]")

    # Verify that the application has more than just the default routes
    assert len(app.routes) > 3, "Application should have more than default routes"


def test_api_endpoints():
    """Test API endpoints are properly mounted."""
    # Test health check endpoint (directly mounted on app)
    health_response = client.get("/health")
    print(f"\nHealth endpoint: {health_response.status_code}")
    assert health_response.status_code == 200, "Health endpoint should be accessible"

    # Test API documentation endpoints
    docs_endpoints = [
        "/api/v1/docs",  # Swagger UI
        "/api/v1/redoc",  # ReDoc
        "/api/v1/openapi.json",  # OpenAPI schema
    ]

    print("\nTesting documentation endpoints:")
    for endpoint in docs_endpoints:
        response = client.get(endpoint)
        print(f"  {endpoint} - Status: {response.status_code}")
        assert (
            response.status_code == 200
        ), f"Documentation endpoint {endpoint} should be accessible"

    # Test API resource endpoints (should return 401 if auth is required)
    api_resource_endpoints = [
        "/api/v1/experiments",
        "/api/v1/feature-flags",
        "/api/v1/users",
    ]

    print("\nTesting API resource endpoints:")
    for endpoint in api_resource_endpoints:
        response = client.get(endpoint)
        print(f"  {endpoint} - Status: {response.status_code}")
        # Most endpoints should require authentication (401) or return 404 if they're POST-only
        assert response.status_code in (
            401,
            404,
            422,
        ), f"API endpoint {endpoint} should require auth or not exist for GET"

    # Test auth token endpoint separately (requires POST with form data)
    print("\nTesting auth token endpoint:")
    auth_token_response = client.post(
        "/api/v1/auth/token", data={}
    )  # Empty form data will fail validation
    print(f"  /api/v1/auth/token - Status: {auth_token_response.status_code}")
    assert auth_token_response.status_code in (
        401,
        422,
    ), "Auth token endpoint should require credentials"


def test_mount_point_discovery():
    """
    Test different potential API mount points to identify how endpoints are mounted.
    This is for diagnostic purposes and not for validation.
    """
    # Try different potential mount points
    mount_points = [
        "/",
        "/api",
        "/api/v1",
        "/v1",
    ]

    print("\nTesting different mount points (for information only):")
    for mount in mount_points:
        response = client.get(f"{mount}")
        print(f"  {mount} - Status: {response.status_code}")
        # We expect these to be 404 except for any specifically implemented endpoints
