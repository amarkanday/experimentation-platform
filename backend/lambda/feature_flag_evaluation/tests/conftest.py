"""
Pytest configuration and fixtures for feature flag evaluation tests.

Provides common fixtures and test utilities.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))


@pytest.fixture
def mock_dynamodb_resource():
    """Mock DynamoDB resource for testing."""
    with patch('evaluator.get_dynamodb_resource') as mock:
        mock_table = Mock()
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock.return_value = mock_resource
        yield mock_table


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch('evaluator.get_logger') as mock:
        yield mock.return_value


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    import os
    # Store original env vars
    original_env = os.environ.copy()

    # Set required environment variables for tests
    os.environ['FLAGS_TABLE'] = 'experimently-feature-flags'

    yield

    # Restore original env vars
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def reset_handler_evaluator():
    """Reset handler evaluator singleton and client initialization before each test."""
    # Import here to avoid circular imports
    try:
        import handler
        handler.reset_evaluator()
        handler._clients_initialized = False
    except ImportError:
        pass  # Handler not loaded yet

    yield

    try:
        import handler
        handler.reset_evaluator()
        handler._clients_initialized = False
    except ImportError:
        pass
