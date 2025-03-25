# backend/tests/conftest.py
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the project root to the Python path
# This ensures imports work properly regardless of where tests are run from
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from our modules
from backend.app.core.config import settings
from backend.app.db.session import SessionLocal


@pytest.fixture
def db():
    """Database session fixture for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    # Import here to ensure path is set up
    from backend.app.main import app

    return TestClient(app)
