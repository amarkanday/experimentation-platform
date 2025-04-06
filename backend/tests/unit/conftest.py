import pytest
from unittest.mock import Mock, patch
import logging

@pytest.fixture(autouse=True)
def mock_logging_handler():
    """Mock logging handler for all tests."""
    handler = Mock(spec=logging.Handler)
    handler.level = logging.INFO
    handler.emit = Mock()

    with patch('logging.getLogger') as mock_get_logger:
        logger = logging.getLogger()
        logger.handlers = [handler]
        logger.level = logging.INFO
        mock_get_logger.return_value = logger
        yield handler
