# backend/tests/unit/models/test_fast_api_setup.py
import os
import sys
import pytest

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now test imports will work correctly
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings


# Simple test function that doesn't require any fixtures
def test_app_exists():
    """Test that the FastAPI app exists and is properly initialized."""
    assert app is not None
    assert app.title == settings.PROJECT_NAME


# Test using the TestClient
def test_health_endpoint():
    """Test the health endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
