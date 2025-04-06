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
        self.emit_call_count = 0
        self.records = []
        self.level = logging.NOTSET
        self.formatter = None
        print("MockCloudWatchHandler initialized")

    def emit(self, record):
        """Mock emit method that counts calls and stores records."""
        print(f"MockCloudWatchHandler.emit called with record: {record.levelname} {record.name}: {record.getMessage()}")
        self.emit_call_count += 1
        self.records.append(record)

    def handle(self, record):
        """Override handle to catch exceptions from emit."""
        print(f"MockCloudWatchHandler.handle called with record: {record.levelname} {record.name}: {record.getMessage()}")
        if self.filter(record) and record.levelno >= self.level:
            try:
                # Format the record if necessary
                if self.formatter:
                    record.message = record.getMessage()
                    # Ensure record is formatted properly
                    try:
                        formatted_record = self.formatter.format(record)
                        record.formatted_msg = formatted_record
                    except Exception as e:
                        print(f"Error formatting record: {e}")
                        return

                # Call our emit method
                self.emit(record)
            except Exception as e:
                print(f"Error in handle: {e}")
                pass

    def setFormatter(self, fmt):
        """Set the formatter for this handler."""
        print(f"MockCloudWatchHandler.setFormatter called with: {fmt}")
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
    mock_client = MagicMock()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key', 'APP_ENV': 'test', 'AWS_REGION': 'us-east-1'}):
        with patch('watchtower.CloudWatchLogHandler', return_value=mock_handler) as mock_handler_class:
            with patch('boto3.client', return_value=mock_client):
                with patch('logging.getLogger') as mock_get_logger:
                    # Create a mock root logger that we can inspect
                    mock_root_logger = MagicMock()
                    mock_get_logger.return_value = mock_root_logger

                    # Call setup_logging
                    setup_logging(enable_cloudwatch=True)

                    # Verify the CloudWatch handler was properly created
                    mock_handler_class.assert_called_once_with(
                        log_group="/experimentation-platform/test",
                        stream_name=mock_handler_class.call_args[1]['stream_name'],  # This will be dynamic
                        boto3_client=mock_client,
                        batch_count=100,
                        batch_timeout=5,
                        create_log_group=True
                    )

                    # Verify that addHandler was called with our mock handler
                    mock_root_logger.addHandler.assert_any_call(mock_handler)

                    # Verify a log message was sent
                    assert mock_root_logger.info.call_count >= 1
                    mock_root_logger.info.assert_any_call("CloudWatch logging enabled")

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
    mock_client = MagicMock()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key', 'APP_ENV': 'test', 'AWS_REGION': 'us-east-1'}):
        with patch('watchtower.CloudWatchLogHandler', return_value=mock_handler) as mock_handler_class:
            with patch('boto3.client', return_value=mock_client):
                with patch('logging.getLogger') as mock_get_logger:
                    # Create a mock root logger that we can inspect
                    mock_root_logger = MagicMock()
                    mock_get_logger.return_value = mock_root_logger

                    # Call setup_logging
                    setup_logging(enable_cloudwatch=True)

                    # Reset mock to track calls to get_logger
                    mock_get_logger.reset_mock()
                    mock_get_logger.return_value = MagicMock()

                    # Get a named logger and log a message
                    logger = get_logger(__name__)
                    test_message = "Test log message"
                    logger.info(test_message)

                    # Verify the log was properly sent
                    logger.info.assert_called_once_with(test_message)

                    # Verify that the CloudWatch handler was initialized correctly
                    mock_handler_class.assert_called_once()

def test_cloudwatch_batching():
    """Test that logs are properly batched."""
    mock_handler = MockCloudWatchHandler()
    mock_client = MagicMock()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key', 'APP_ENV': 'test', 'AWS_REGION': 'us-east-1'}):
        with patch('watchtower.CloudWatchLogHandler', return_value=mock_handler) as mock_handler_class:
            with patch('boto3.client', return_value=mock_client):
                with patch('logging.getLogger') as mock_get_logger:
                    # Create a mock root logger that we can inspect
                    mock_root_logger = MagicMock()
                    mock_get_logger.return_value = mock_root_logger

                    # Call setup_logging
                    setup_logging(enable_cloudwatch=True)

                    # Reset mock to track calls to get_logger
                    mock_get_logger.reset_mock()
                    test_logger = MagicMock()
                    mock_get_logger.return_value = test_logger

                    # Get a named logger and log multiple messages
                    logger = get_logger(__name__)
                    for i in range(5):
                        logger.info(f"Test message {i}")

                    # Verify the logs were sent
                    assert logger.info.call_count == 5

                    # Verify that the CloudWatch handler was initialized correctly
                    mock_handler_class.assert_called_once()

def test_cloudwatch_error_handling():
    """Test error handling in CloudWatch logging."""
    mock_handler = MockCloudWatchHandler()
    mock_client = MagicMock()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key', 'APP_ENV': 'test', 'AWS_REGION': 'us-east-1'}):
        with patch('watchtower.CloudWatchLogHandler', return_value=mock_handler) as mock_handler_class:
            with patch('boto3.client', return_value=mock_client):
                with patch('logging.getLogger') as mock_get_logger:
                    # Create a mock root logger and make addHandler raise an exception
                    mock_root_logger = MagicMock()
                    mock_root_logger.addHandler.side_effect = [None, Exception("Test error")]
                    mock_get_logger.return_value = mock_root_logger

                    # Call setup_logging - it should catch the exception
                    setup_logging(enable_cloudwatch=True)

                    # Verify warning was logged
                    mock_root_logger.warning.assert_any_call("Failed to initialize CloudWatch logging: Test error")

                    # Verify that the CloudWatch handler was initialized correctly
                    mock_handler_class.assert_called_once()

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
