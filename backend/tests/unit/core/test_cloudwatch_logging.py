"""Tests for CloudWatch logging integration."""

import logging
import os
import time
from unittest.mock import patch, MagicMock
import uuid

import pytest
import watchtower
import boto3

from backend.app.core.logging import setup_logging, get_logger

class MockCloudWatchHandler(logging.Handler):
    """Mock CloudWatch handler for testing."""
    def __init__(self):
        super().__init__()
        self.emit = MagicMock()
        self.handleError = MagicMock()
        self.level = logging.NOTSET
        self.formatter = None

    def handle(self, record):
        """Override handle to catch exceptions from emit."""
        if self.filter(record) and record.levelno >= self.level:
            try:
                if self.formatter:
                    record.msg = self.formatter.format(record)
                self.emit(record)
            except Exception as e:
                self.handleError(record)

    def setFormatter(self, fmt):
        """Set the formatter for this handler."""
        self.formatter = fmt

@pytest.fixture(autouse=True)
def clear_handlers():
    """Clear all handlers from the root logger before each test."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    yield
    # Clean up after test
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

def test_cloudwatch_handler_added_when_enabled():
    """Test that CloudWatch handler is added when enabled."""
    mock_handler = MockCloudWatchHandler()
    mock_handler.level = logging.NOTSET
    mock_client = MagicMock()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key', 'APP_ENV': 'test', 'AWS_REGION': 'us-east-1'}):
        with patch('watchtower.CloudWatchLogHandler', return_value=mock_handler) as mock_handler_class:
            with patch('boto3.client', return_value=mock_client):
                setup_logging(enable_cloudwatch=True)
                logger = get_logger(__name__)
                logger.info("Test message")

                # Verify handler was added and used
                mock_handler_class.assert_called_once_with(
                    log_group="/experimentation-platform/test",
                    stream_name=mock_handler_class.call_args[1]['stream_name'],  # This will be dynamic
                    boto3_client=mock_client,
                    batch_count=100,
                    batch_timeout=5,
                    create_log_group=True
                )
                assert mock_handler.emit.call_count == 2  # One for setup_logging, one for test message

def test_cloudwatch_handler_not_added_when_disabled():
    """Test that CloudWatch handler is not added when disabled."""
    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key'}):
        with patch('watchtower.CloudWatchLogHandler') as mock_handler:
            setup_logging(enable_cloudwatch=False)
            mock_handler.assert_not_called()

def test_cloudwatch_handler_not_added_without_credentials():
    """Test that CloudWatch handler is not added without AWS credentials."""
    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': ''}):
        with patch('watchtower.CloudWatchLogHandler') as mock_handler:
            setup_logging(enable_cloudwatch=True)
            mock_handler.assert_not_called()

def test_log_formatting_with_cloudwatch():
    """Test that logs are properly formatted for CloudWatch."""
    mock_handler = MockCloudWatchHandler()
    mock_handler.level = logging.NOTSET
    mock_client = MagicMock()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key', 'APP_ENV': 'test', 'AWS_REGION': 'us-east-1'}):
        with patch('watchtower.CloudWatchLogHandler', return_value=mock_handler) as mock_handler_class:
            with patch('boto3.client', return_value=mock_client):
                setup_logging(enable_cloudwatch=True)
                logger = get_logger(__name__)

                # Log a test message
                test_message = "Test log message"
                logger.info(test_message)

                # Verify the log was emitted
                mock_handler_class.assert_called_once()
                assert mock_handler.emit.call_count == 2  # One for setup_logging, one for test message

                # Verify the test message was properly formatted
                last_call = mock_handler.emit.call_args_list[-1]
                record = last_call[0][0]
                assert record.getMessage() == test_message
                assert record.name == __name__
                assert record.levelno == logging.INFO

def test_cloudwatch_batching():
    """Test that logs are properly batched."""
    mock_handler = MockCloudWatchHandler()
    mock_handler.level = logging.NOTSET
    mock_client = MagicMock()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key', 'APP_ENV': 'test', 'AWS_REGION': 'us-east-1'}):
        with patch('watchtower.CloudWatchLogHandler', return_value=mock_handler) as mock_handler_class:
            with patch('boto3.client', return_value=mock_client):
                setup_logging(enable_cloudwatch=True)
                logger = get_logger(__name__)

                # Send multiple log messages
                for i in range(5):
                    logger.info(f"Test message {i}")

                # Verify logs were emitted
                mock_handler_class.assert_called_once()
                assert mock_handler.emit.call_count == 6  # One for setup_logging, five for test messages

def test_cloudwatch_error_handling():
    """Test error handling in CloudWatch logging."""
    mock_handler = MockCloudWatchHandler()
    mock_handler.level = logging.NOTSET
    mock_client = MagicMock()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key', 'APP_ENV': 'test', 'AWS_REGION': 'us-east-1'}):
        with patch('watchtower.CloudWatchLogHandler', return_value=mock_handler) as mock_handler_class:
            with patch('boto3.client', return_value=mock_client):
                setup_logging(enable_cloudwatch=True)
                logger = get_logger(__name__)

                # Set up error simulation after setup_logging
                mock_handler.emit.side_effect = Exception("Test error")

                # Log a message that should trigger the error
                logger.info("Test message")

                # Verify error was handled
                assert mock_handler.handleError.call_count == 1

@pytest.mark.skip(reason="AWS credentials required")
def test_cloudwatch_integration():
    """Integration test for CloudWatch logging (requires valid AWS credentials)."""
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        pytest.skip("AWS credentials not configured")

    setup_logging(enable_cloudwatch=True)
    logger = get_logger(__name__)

    test_id = str(uuid.uuid4())
    test_message = f"Test message {test_id}"

    logger.info(test_message)

    # Note: In a real integration test, you would verify the log in CloudWatch
    # This would require boto3 client to query CloudWatch logs
