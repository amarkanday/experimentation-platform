"""
AWS Lambda Handler for Event Processor.

This is the main entry point for the Event Processor Lambda function.
Handles Kinesis stream events and orchestrates the complete processing pipeline:
- Parse Kinesis events
- Validate event schemas
- Enrich with assignment/experiment data
- Aggregate metrics to DynamoDB
- Archive to S3
- Return partial batch failures for retry

Follows TDD (Test-Driven Development) - GREEN phase implementation.
"""

import os
import logging
import boto3
from typing import Dict, Any

# Import processing modules
from batch_processor import process_batch
import event_parser
import event_validator
import event_enricher
import event_aggregator
import s3_archiver

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (will be set on first invocation)
s3_client = None
dynamodb_table = None
sqs_client = None


def initialize_aws_clients():
    """
    Initialize AWS clients for S3, DynamoDB, and SQS.

    This function is called once during cold start to initialize
    all AWS service clients needed by the Lambda function.
    """
    global s3_client, dynamodb_table, sqs_client

    # Initialize S3 client for archival
    s3_client = boto3.client('s3')
    event_parser.s3_client = s3_client
    s3_archiver.s3_client = s3_client

    # Initialize DynamoDB resource and table for aggregation
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE', 'event-aggregations')
    dynamodb_table = dynamodb.Table(table_name)
    event_aggregator.dynamodb_table = dynamodb_table

    # Initialize SQS client for DLQ
    sqs_client = boto3.client('sqs')
    from batch_processor import sqs_client as batch_sqs
    import batch_processor
    batch_processor.sqs_client = sqs_client

    logger.info("AWS clients initialized successfully")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function for Kinesis event processing.

    Args:
        event: Lambda event containing Kinesis records
        context: Lambda context object with runtime information

    Returns:
        Response dict with batchItemFailures for partial batch failure handling
    """
    # Log request information
    request_id = getattr(context, 'aws_request_id', 'unknown')
    logger.info(f"Processing Lambda invocation: {request_id}")

    # Handle None event
    if event is None:
        logger.error("Received None event")
        return {
            "batchItemFailures": [],
            "error": "Invalid event: event is None"
        }

    # Initialize AWS clients on cold start
    global s3_client, dynamodb_table, sqs_client
    if s3_client is None:
        try:
            initialize_aws_clients()
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            # Continue anyway - some functionality may work

    # Get configuration from environment
    s3_bucket = os.environ.get('S3_BUCKET', 'event-archive')
    dlq_url = os.environ.get('DLQ_URL', None)
    dlq_enabled = dlq_url is not None

    # Log configuration
    logger.info(f"Configuration: s3_bucket={s3_bucket}, dlq_enabled={dlq_enabled}")

    # Process the batch
    try:
        result = process_batch(
            event,
            dlq_enabled=dlq_enabled,
            dlq_url=dlq_url,
            s3_bucket=s3_bucket
        )

        # Log results
        logger.info(
            f"Batch processing complete: "
            f"success={result.get('success_count', 0)}, "
            f"failures={result.get('failure_count', 0)}, "
            f"time={result.get('processing_time_ms', 0)}ms"
        )

        # Log metrics
        if 'metrics' in result:
            metrics = result['metrics']
            logger.info(
                f"Processing metrics: "
                f"parse_errors={metrics.get('parse_errors', 0)}, "
                f"validation_errors={metrics.get('validation_errors', 0)}, "
                f"enrichment_errors={metrics.get('enrichment_errors', 0)}, "
                f"aggregation_errors={metrics.get('aggregation_errors', 0)}"
            )

        # Return Lambda response with batch item failures
        return {
            "batchItemFailures": result.get("batchItemFailures", [])
        }

    except Exception as e:
        logger.error(f"Unexpected error in handler: {e}", exc_info=True)

        # Return all records as failures on catastrophic error
        records = event.get("Records", [])
        batch_item_failures = [
            {"itemIdentifier": record.get("kinesis", {}).get("sequenceNumber", "unknown")}
            for record in records
        ]

        return {
            "batchItemFailures": batch_item_failures,
            "error": str(e)
        }
