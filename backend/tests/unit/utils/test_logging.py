import pytest
from unittest.mock import Mock, patch, MagicMock
import logging
from backend.app.core.logging import setup_logging, get_logger

class TestLogging:
    @pytest.fixture
    def mock_logger(self):
        mock = Mock(spec=logging.Logger)
        mock.handlers = []  # Initialize handlers as a list
        return mock

    @pytest.fixture
    def mock_handler(self):
        return Mock(spec=logging.Handler)

    def test_setup_logging_default(self, mock_handler):
        # Test default logging setup
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_stream_handler, \
             patch('backend.app.core.logging.CustomJsonFormatter') as mock_formatter:

            mock_stream_handler.return_value = mock_handler
            mock_logger = Mock(spec=logging.Logger)
            mock_logger.handlers = []  # Initialize handlers as a list
            mock_get_logger.return_value = mock_logger

            setup_logging()

            # Verify that getLogger() was called with no arguments for root logger
            mock_get_logger.assert_called_with()
            mock_stream_handler.assert_called_once()
            mock_formatter.assert_called_once()
            mock_logger.addHandler.assert_called_once_with(mock_handler)
            mock_logger.setLevel.assert_called_with(logging.INFO)

    def test_setup_logging_custom_level(self, mock_handler):
        # Test logging setup with custom level
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_stream_handler:

            mock_stream_handler.return_value = mock_handler
            mock_logger = Mock(spec=logging.Logger)
            mock_logger.handlers = []  # Initialize handlers as a list
            mock_get_logger.return_value = mock_logger

            setup_logging(level=logging.DEBUG)

            # Verify that the root logger was set to DEBUG level
            mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_setup_logging_custom_format(self, mock_handler):
        # Test logging setup with custom format
        custom_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_stream_handler, \
             patch('logging.Formatter') as mock_formatter:

            mock_stream_handler.return_value = mock_handler
            mock_logger = Mock(spec=logging.Logger)
            mock_logger.handlers = []  # Initialize handlers as a list
            mock_get_logger.return_value = mock_logger

            setup_logging(format=custom_format)

            mock_formatter.assert_called_once_with(custom_format)

    def test_setup_logging_file_handler(self, mock_handler):
        # Test logging setup with file handler
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock(spec=logging.Logger)
            mock_logger.handlers = []  # Initialize handlers as a list
            mock_get_logger.return_value = mock_logger

            # Call setup_logging with a file
            setup_logging(log_file="test.log")

            # Verify a handler was added (don't check which one)
            assert mock_logger.addHandler.called
            # Verify logger level was set
            mock_logger.setLevel.assert_called_with(logging.INFO)

    def test_get_logger(self, mock_logger):
        # Test getting logger
        with patch('logging.getLogger') as mock_get_logger:
            mock_get_logger.return_value = mock_logger

            logger = get_logger("test_logger")

            assert logger == mock_logger
            mock_get_logger.assert_called_once_with("test_logger")

    def test_logger_hierarchy(self, mock_logger):
        # Test logger hierarchy
        with patch('logging.getLogger') as mock_get_logger:
            mock_get_logger.return_value = mock_logger

            parent_logger = get_logger("parent")
            child_logger = get_logger("parent.child")

            assert parent_logger == mock_logger
            assert child_logger == mock_logger
            mock_get_logger.assert_any_call("parent")
            mock_get_logger.assert_any_call("parent.child")

    def test_logger_propagation(self, mock_logger):
        # Test logger propagation
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger.propagate = True
            mock_get_logger.return_value = mock_logger

            logger = get_logger("test_logger")

            assert logger.propagate is True

    def test_logger_level_inheritance(self, mock_logger):
        # Test logger level inheritance
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger.level = logging.INFO
            mock_get_logger.return_value = mock_logger

            logger = get_logger("test_logger")

            assert logger.level == logging.INFO

    def test_logger_exception_handling(self, mock_logger):
        # Test logger exception handling
        with patch('logging.getLogger') as mock_get_logger:
            mock_get_logger.side_effect = Exception("Logger error")

            logger = get_logger("test_logger")

            assert logger is not None
            assert isinstance(logger, logging.Logger)
