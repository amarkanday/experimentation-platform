"""
Unit tests for shared utility functions.

Tests logging, validation, AWS helpers, and response formatting.
"""

import json
import logging
import os
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    JsonFormatter,
    get_logger,
    validate_event,
    format_response,
    format_error_response,
    DecimalEncoder,
    get_dynamodb_client,
    get_dynamodb_resource,
    get_kinesis_client,
    put_dynamodb_item,
    get_dynamodb_item,
    put_kinesis_record,
    batch_put_kinesis_records,
    get_env_variable,
)


class TestJsonFormatter:
    """Test suite for JsonFormatter class."""

    def test_json_formatter_basic_message(self):
        """Test that JsonFormatter formats log as JSON."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func"
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test_logger"
        assert data["function"] == "test_func"
        assert data["line"] == 10
        assert "timestamp" in data

    def test_json_formatter_with_exception(self):
        """Test JsonFormatter with exception info."""
        formatter = JsonFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
            func="test_func"
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_json_formatter_with_extra_fields(self):
        """Test JsonFormatter with extra fields."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func"
        )

        # Add extra fields
        record.user_id = "user_123"
        record.experiment_id = "exp_456"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["user_id"] == "user_123"
        assert data["experiment_id"] == "exp_456"


class TestGetLogger:
    """Test suite for get_logger function."""

    def test_get_logger_default_level(self):
        """Test get_logger with default level."""
        logger = get_logger("test_logger")

        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_get_logger_custom_level(self):
        """Test get_logger with custom level."""
        logger = get_logger("test_logger", level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_get_logger_from_env(self, monkeypatch):
        """Test get_logger reads level from environment."""
        monkeypatch.setenv("LOG_LEVEL", "WARNING")

        logger = get_logger("test_logger")

        assert logger.level == logging.WARNING

    def test_get_logger_uses_json_formatter(self):
        """Test that logger uses JsonFormatter."""
        logger = get_logger("test_logger")

        # Check that handler has JsonFormatter
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, JsonFormatter)


class TestValidateEvent:
    """Test suite for validate_event function."""

    def test_validate_event_with_all_fields(self):
        """Test validation passes with all required fields."""
        event = {
            "user_id": "user_123",
            "experiment_key": "exp_001",
            "context": {}
        }
        required = ["user_id", "experiment_key"]

        # Should not raise
        validate_event(event, required)

    def test_validate_event_missing_fields(self):
        """Test validation fails with missing fields."""
        event = {"user_id": "user_123"}
        required = ["user_id", "experiment_key", "context"]

        with pytest.raises(ValueError, match="Missing required fields"):
            validate_event(event, required)

    def test_validate_event_empty_required_list(self):
        """Test validation with empty required list."""
        event = {"foo": "bar"}
        required = []

        # Should not raise
        validate_event(event, required)


class TestFormatResponse:
    """Test suite for format_response function."""

    def test_format_response_basic(self):
        """Test basic response formatting."""
        body = {"variant": "treatment", "experiment_id": "exp_123"}

        response = format_response(200, body)

        assert response["statusCode"] == 200
        assert "headers" in response
        assert response["headers"]["Content-Type"] == "application/json"
        assert "body" in response

        # Body should be JSON string
        parsed_body = json.loads(response["body"])
        assert parsed_body == body

    def test_format_response_with_custom_headers(self):
        """Test response with custom headers."""
        body = {"message": "success"}
        custom_headers = {"X-Custom": "value"}

        response = format_response(200, body, headers=custom_headers)

        assert response["headers"]["X-Custom"] == "value"
        assert response["headers"]["Content-Type"] == "application/json"

    def test_format_response_includes_cors_headers(self):
        """Test that CORS headers are included."""
        response = format_response(200, {})

        assert "Access-Control-Allow-Origin" in response["headers"]
        assert "Access-Control-Allow-Headers" in response["headers"]


class TestFormatErrorResponse:
    """Test suite for format_error_response function."""

    def test_format_error_response_basic(self):
        """Test basic error response."""
        response = format_error_response(400, "Invalid request")

        assert response["statusCode"] == 400

        body = json.loads(response["body"])
        assert "error" in body
        assert body["error"]["message"] == "Invalid request"
        assert body["error"]["type"] == "InternalError"
        assert "timestamp" in body["error"]

    def test_format_error_response_with_type(self):
        """Test error response with custom type."""
        response = format_error_response(
            404,
            "Resource not found",
            error_type="NotFoundError"
        )

        body = json.loads(response["body"])
        assert body["error"]["type"] == "NotFoundError"
        assert body["error"]["message"] == "Resource not found"


class TestDecimalEncoder:
    """Test suite for DecimalEncoder class."""

    def test_decimal_encoder_with_decimal(self):
        """Test encoding Decimal to float."""
        data = {"value": Decimal("99.99")}

        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)

        assert parsed["value"] == 99.99

    def test_decimal_encoder_with_datetime(self):
        """Test encoding datetime to ISO format."""
        now = datetime.now(timezone.utc)
        data = {"timestamp": now}

        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)

        assert isinstance(parsed["timestamp"], str)
        assert parsed["timestamp"] == now.isoformat()

    def test_decimal_encoder_with_normal_types(self):
        """Test encoder doesn't break normal types."""
        data = {"string": "value", "number": 42, "bool": True}

        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)

        assert parsed == data


class TestAWSClientGetters:
    """Test suite for AWS client getter functions."""

    def setup_method(self):
        """Reset global AWS client caches before each test."""
        import utils
        utils._dynamodb = None
        utils._kinesis = None

    @patch('utils.boto3')
    def test_get_dynamodb_client(self, mock_boto3):
        """Test getting DynamoDB client."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        # First call creates client
        client1 = get_dynamodb_client()
        assert mock_boto3.client.called

        # Second call returns cached client
        mock_boto3.client.reset_mock()
        client2 = get_dynamodb_client()
        assert client1 is client2

    @patch('utils.boto3')
    def test_get_dynamodb_resource(self, mock_boto3):
        """Test getting DynamoDB resource."""
        mock_resource = Mock()
        mock_boto3.resource.return_value = mock_resource

        resource = get_dynamodb_resource()
        assert mock_boto3.resource.called
        assert resource is mock_resource

    @patch('utils.boto3')
    def test_get_kinesis_client(self, mock_boto3):
        """Test getting Kinesis client."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        client = get_kinesis_client()
        assert mock_boto3.client.called


class TestPutDynamoDBItem:
    """Test suite for put_dynamodb_item function."""

    @patch('utils.get_dynamodb_resource')
    def test_put_dynamodb_item_success(self, mock_get_resource):
        """Test successful DynamoDB put operation."""
        mock_table = Mock()
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        item = {"id": "123", "value": "test"}
        result = put_dynamodb_item("test_table", item)

        assert result is True
        mock_table.put_item.assert_called_once()

    @patch('utils.get_dynamodb_resource')
    def test_put_dynamodb_item_with_condition(self, mock_get_resource):
        """Test DynamoDB put with condition expression."""
        mock_table = Mock()
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        item = {"id": "123", "value": "test"}
        condition = "attribute_not_exists(id)"
        result = put_dynamodb_item("test_table", item, condition)

        assert result is True
        call_kwargs = mock_table.put_item.call_args[1]
        assert "ConditionExpression" in call_kwargs

    @patch('utils.get_dynamodb_resource')
    def test_put_dynamodb_item_failure(self, mock_get_resource):
        """Test DynamoDB put handles errors."""
        mock_table = Mock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        item = {"id": "123"}
        result = put_dynamodb_item("test_table", item)

        assert result is False


class TestGetDynamoDBItem:
    """Test suite for get_dynamodb_item function."""

    @patch('utils.get_dynamodb_resource')
    def test_get_dynamodb_item_found(self, mock_get_resource):
        """Test getting item that exists."""
        expected_item = {"id": "123", "value": "test"}
        mock_table = Mock()
        mock_table.get_item.return_value = {"Item": expected_item}
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        result = get_dynamodb_item("test_table", {"id": "123"})

        assert result == expected_item
        mock_table.get_item.assert_called_once_with(Key={"id": "123"})

    @patch('utils.get_dynamodb_resource')
    def test_get_dynamodb_item_not_found(self, mock_get_resource):
        """Test getting item that doesn't exist."""
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        result = get_dynamodb_item("test_table", {"id": "999"})

        assert result is None

    @patch('utils.get_dynamodb_resource')
    def test_get_dynamodb_item_error(self, mock_get_resource):
        """Test get_item handles errors."""
        mock_table = Mock()
        mock_table.get_item.side_effect = Exception("DynamoDB error")
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        result = get_dynamodb_item("test_table", {"id": "123"})

        assert result is None


class TestPutKinesisRecord:
    """Test suite for put_kinesis_record function."""

    @patch('utils.get_kinesis_client')
    def test_put_kinesis_record_success(self, mock_get_client):
        """Test successful Kinesis put operation."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        data = {"event_type": "conversion", "user_id": "user_123"}
        result = put_kinesis_record("test_stream", data, "user_123")

        assert result is True
        mock_client.put_record.assert_called_once()

    @patch('utils.get_kinesis_client')
    def test_put_kinesis_record_error(self, mock_get_client):
        """Test Kinesis put handles errors."""
        mock_client = Mock()
        mock_client.put_record.side_effect = Exception("Kinesis error")
        mock_get_client.return_value = mock_client

        data = {"event": "test"}
        result = put_kinesis_record("test_stream", data, "partition_1")

        assert result is False


class TestBatchPutKinesisRecords:
    """Test suite for batch_put_kinesis_records function."""

    @patch('utils.get_kinesis_client')
    def test_batch_put_kinesis_records_success(self, mock_get_client):
        """Test successful batch put operation."""
        mock_client = Mock()
        mock_client.put_records.return_value = {"FailedRecordCount": 0}
        mock_get_client.return_value = mock_client

        records = [
            {"user_id": f"user_{i}", "event": "test"}
            for i in range(10)
        ]

        successful, failed = batch_put_kinesis_records("test_stream", records)

        assert successful == 10
        assert failed == 0
        mock_client.put_records.assert_called_once()

    @patch('utils.get_kinesis_client')
    def test_batch_put_kinesis_records_partial_failure(self, mock_get_client):
        """Test batch put with partial failures."""
        mock_client = Mock()
        mock_client.put_records.return_value = {"FailedRecordCount": 2}
        mock_get_client.return_value = mock_client

        records = [
            {"user_id": f"user_{i}", "event": "test"}
            for i in range(10)
        ]

        successful, failed = batch_put_kinesis_records("test_stream", records)

        assert successful == 8
        assert failed == 2

    @patch('utils.get_kinesis_client')
    def test_batch_put_kinesis_records_large_batch(self, mock_get_client):
        """Test batch put with > 500 records (multiple batches)."""
        mock_client = Mock()
        mock_client.put_records.return_value = {"FailedRecordCount": 0}
        mock_get_client.return_value = mock_client

        records = [
            {"user_id": f"user_{i}", "event": "test"}
            for i in range(1000)
        ]

        successful, failed = batch_put_kinesis_records("test_stream", records)

        assert successful == 1000
        assert failed == 0
        # Should be called twice (500 + 500)
        assert mock_client.put_records.call_count == 2

    @patch('utils.get_kinesis_client')
    def test_batch_put_kinesis_records_error(self, mock_get_client):
        """Test batch put handles errors."""
        mock_client = Mock()
        mock_client.put_records.side_effect = Exception("Kinesis error")
        mock_get_client.return_value = mock_client

        records = [{"user_id": "user_1", "event": "test"}]

        successful, failed = batch_put_kinesis_records("test_stream", records)

        assert successful == 0
        assert failed == 1


class TestGetEnvVariable:
    """Test suite for get_env_variable function."""

    def test_get_env_variable_exists(self, monkeypatch):
        """Test getting existing environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")

        result = get_env_variable("TEST_VAR")

        assert result == "test_value"

    def test_get_env_variable_with_default(self, monkeypatch):
        """Test getting non-existent variable with default."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)

        result = get_env_variable("NONEXISTENT_VAR", default="default_value")

        assert result == "default_value"

    def test_get_env_variable_required_exists(self, monkeypatch):
        """Test required variable that exists."""
        monkeypatch.setenv("REQUIRED_VAR", "value")

        result = get_env_variable("REQUIRED_VAR", required=True)

        assert result == "value"

    def test_get_env_variable_required_missing(self, monkeypatch):
        """Test required variable that is missing raises error."""
        monkeypatch.delenv("MISSING_REQUIRED", raising=False)

        with pytest.raises(ValueError, match="Required environment variable"):
            get_env_variable("MISSING_REQUIRED", required=True)

    def test_get_env_variable_none_default(self, monkeypatch):
        """Test getting variable with None default."""
        monkeypatch.delenv("NONEXISTENT", raising=False)

        result = get_env_variable("NONEXISTENT")

        assert result is None
