# backend/tests/unit/models/test_fast_api_setup.py
import pytest
from fastapi.testclient import TestClient

# Import the app from the correct module path
from backend.app.main import (
    app,
)  # Adjust this import path to match your project structure


@pytest.fixture
def client():
    """
    Test client fixture for FastAPI app.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)


def test_health_endpoint(client):
    """Test that the health endpoint returns a 200 status code."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


def test_api_docs_available(client):
    """Test that the API docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# Update the test_openapi_spec function in test_fast_api_setup.py


def test_openapi_spec(client):
    """Test that the OpenAPI spec is available."""
    # In your FastAPI application, the OpenAPI URL might be configured as
    # f"{settings.API_V1_STR}/openapi.json" instead of "/openapi.json"

    # Try with the API_V1_STR prefix
    response = client.get("/api/v1/openapi.json")
    if response.status_code == 404:
        # Fallback to checking the app's openapi_url attribute
        from backend.app.main import app

        if hasattr(app, "openapi_url") and app.openapi_url:
            openapi_url = app.openapi_url
            response = client.get(openapi_url)

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    # Verify some basic OpenAPI structure
    json_data = response.json()
    assert "openapi" in json_data
    assert "paths" in json_data
    assert "info" in json_data
    assert "title" in json_data["info"]
