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


def test_api_mount_point():
    """Test different potential API mount points to find the correct one."""
    # Try different potential mount points
    mount_points = [
        "/",
        "/api",
        "/api/v1",
        "/v1",
    ]

    print("\nTesting different mount points:")
    for mount in mount_points:
        response = client.get(f"{mount}")
        print(f"  {mount} - Status: {response.status_code}")
