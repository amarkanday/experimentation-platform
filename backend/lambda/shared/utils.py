"""
Shared utility functions for Lambda functions.

Provides common functionality for logging, validation, error handling, and AWS service interactions.
"""

import json
import logging
import os
import boto3
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from decimal import Decimal


# AWS Clients (initialized lazily for better cold start performance)
_dynamodb = None
_kinesis = None


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging in CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'experiment_id'):
            log_data['experiment_id'] = record.experiment_id

        return json.dumps(log_data)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get configured logger for Lambda function.

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR), defaults to env var LOG_LEVEL

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level from parameter or environment variable
    log_level = level or os.environ.get('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, log_level.upper()))

    # Configure handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def validate_event(event: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that event contains required fields.

    Args:
        event: Event dictionary to validate
        required_fields: List of required field names

    Raises:
        ValueError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in event]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def format_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format Lambda response in standard format.

    Args:
        status_code: HTTP status code
        body: Response body dictionary
        headers: Optional response headers

    Returns:
        Formatted response dictionary
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # Configure based on environment
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    }

    if headers:
        default_headers.update(headers)

    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def format_error_response(
    status_code: int,
    error_message: str,
    error_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format error response.

    Args:
        status_code: HTTP status code
        error_message: Error message
        error_type: Optional error type/code

    Returns:
        Formatted error response
    """
    body = {
        'error': {
            'message': error_message,
            'type': error_type or 'InternalError',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    }
    return format_response(status_code, body)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def get_dynamodb_client():
    """
    Get DynamoDB client (cached).

    Returns:
        boto3 DynamoDB client
    """
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.client('dynamodb')
    return _dynamodb


def get_dynamodb_resource():
    """
    Get DynamoDB resource (cached).

    Returns:
        boto3 DynamoDB resource
    """
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource('dynamodb')
    return _dynamodb


def get_kinesis_client():
    """
    Get Kinesis client (cached).

    Returns:
        boto3 Kinesis client
    """
    global _kinesis
    if _kinesis is None:
        _kinesis = boto3.client('kinesis')
    return _kinesis


def put_dynamodb_item(
    table_name: str,
    item: Dict[str, Any],
    condition_expression: Optional[str] = None
) -> bool:
    """
    Put item into DynamoDB table.

    Args:
        table_name: DynamoDB table name
        item: Item to insert
        condition_expression: Optional condition expression

    Returns:
        True if successful, False otherwise
    """
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    try:
        kwargs = {'Item': item}
        if condition_expression:
            kwargs['ConditionExpression'] = condition_expression

        table.put_item(**kwargs)
        return True
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to put item in DynamoDB: {str(e)}", extra={'table': table_name})
        return False


def get_dynamodb_item(
    table_name: str,
    key: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Get item from DynamoDB table.

    Args:
        table_name: DynamoDB table name
        key: Primary key of item to retrieve

    Returns:
        Item if found, None otherwise
    """
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    try:
        response = table.get_item(Key=key)
        return response.get('Item')
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to get item from DynamoDB: {str(e)}", extra={'table': table_name})
        return None


def put_kinesis_record(
    stream_name: str,
    data: Dict[str, Any],
    partition_key: str
) -> bool:
    """
    Put record into Kinesis stream.

    Args:
        stream_name: Kinesis stream name
        data: Data to send (will be JSON encoded)
        partition_key: Partition key for sharding

    Returns:
        True if successful, False otherwise
    """
    kinesis = get_kinesis_client()

    try:
        kinesis.put_record(
            StreamName=stream_name,
            Data=json.dumps(data, cls=DecimalEncoder),
            PartitionKey=partition_key
        )
        return True
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to put record in Kinesis: {str(e)}", extra={'stream': stream_name})
        return False


def batch_put_kinesis_records(
    stream_name: str,
    records: List[Dict[str, Any]],
    partition_key_field: str = 'user_id'
) -> tuple[int, int]:
    """
    Batch put records into Kinesis stream.

    Args:
        stream_name: Kinesis stream name
        records: List of records to send
        partition_key_field: Field to use as partition key

    Returns:
        Tuple of (successful_count, failed_count)
    """
    kinesis = get_kinesis_client()
    logger = get_logger(__name__)

    successful = 0
    failed = 0

    # Kinesis batch limit is 500 records
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        kinesis_records = [
            {
                'Data': json.dumps(record, cls=DecimalEncoder),
                'PartitionKey': str(record.get(partition_key_field, 'default'))
            }
            for record in batch
        ]

        try:
            response = kinesis.put_records(
                StreamName=stream_name,
                Records=kinesis_records
            )

            successful += len(batch) - response.get('FailedRecordCount', 0)
            failed += response.get('FailedRecordCount', 0)

            if response.get('FailedRecordCount', 0) > 0:
                logger.warning(
                    f"Batch put partially failed: {response['FailedRecordCount']} failed",
                    extra={'stream': stream_name}
                )

        except Exception as e:
            logger.error(f"Failed to batch put records in Kinesis: {str(e)}", extra={'stream': stream_name})
            failed += len(batch)

    return successful, failed


def get_env_variable(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable with validation.

    Args:
        name: Environment variable name
        default: Default value if not set
        required: If True, raises ValueError when variable is not set

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If required=True and variable is not set
    """
    value = os.environ.get(name, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value
