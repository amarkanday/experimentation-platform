"""
Batch Processor for Event Processor Lambda.

This module orchestrates the complete event processing pipeline:
- Parse Kinesis events
- Validate events
- Enrich with assignment/experiment data
- Aggregate metrics to DynamoDB
- Archive to S3
- Handle partial batch failures
- Send failed records to DLQ

Follows TDD (Test-Driven Development) - GREEN phase implementation.
"""

import logging
import time
from typing import Dict, Any, List
from event_parser import parse_kinesis_events
from event_validator import validate_events_batch
from event_enricher import enrich_events_batch
from event_aggregator import aggregate_events_batch
from s3_archiver import archive_to_s3_batched

logger = logging.getLogger(__name__)

# Placeholder for SQS client - will be initialized in Lambda handler
sqs_client = None


def send_to_dlq(failed_record: Dict[str, Any], dlq_url: str, error_message: str) -> bool:
    """
    Send a failed record to Dead Letter Queue.

    Args:
        failed_record: The Kinesis record that failed processing
        dlq_url: SQS queue URL for DLQ
        error_message: Error message describing the failure

    Returns:
        True if successfully sent to DLQ, False otherwise
    """
    try:
        message_body = {
            "sequenceNumber": failed_record.get("kinesis", {}).get("sequenceNumber", "unknown"),
            "data": failed_record.get("kinesis", {}).get("data", ""),
            "error": error_message,
            "timestamp": time.time()
        }

        response = sqs_client.send_message(
            QueueUrl=dlq_url,
            MessageBody=str(message_body)
        )

        logger.info(f"Sent failed record to DLQ: {response.get('MessageId')}")
        return True

    except Exception as e:
        logger.error(f"Failed to send record to DLQ: {e}")
        return False


def process_batch(
    kinesis_event: Dict[str, Any],
    dlq_enabled: bool = False,
    dlq_url: str = None,
    s3_bucket: str = "event-archive"
) -> Dict[str, Any]:
    """
    Process a batch of Kinesis records through the complete pipeline.

    Args:
        kinesis_event: Kinesis event from Lambda trigger
        dlq_enabled: Whether to send failed records to DLQ
        dlq_url: SQS queue URL for DLQ
        s3_bucket: S3 bucket for archival

    Returns:
        Processing result with metrics and batch item failures
    """
    start_time = time.time()

    # Initialize tracking
    records = kinesis_event.get("Records", [])
    total_records = len(records)
    success_count = 0
    failure_count = 0
    batch_item_failures = []

    # Initialize metrics
    metrics = {
        "total_processed": total_records,
        "parse_errors": 0,
        "validation_errors": 0,
        "enrichment_errors": 0,
        "aggregation_errors": 0,
        "archive_errors": 0
    }

    # Handle empty batch
    if total_records == 0:
        return {
            "success_count": 0,
            "failure_count": 0,
            "batchItemFailures": [],
            "metrics": metrics,
            "processing_time_ms": 0
        }

    # STAGE 1: Parse Kinesis events
    logger.info(f"Processing batch of {total_records} records")

    try:
        parsed_events, parse_errors = parse_kinesis_events(kinesis_event, skip_errors=True)
        metrics["parse_errors"] = len(parse_errors)

        # Track parse failures
        for error in parse_errors:
            failure_count += 1
            sequence_number = error.get("sequence_number", "unknown")
            batch_item_failures.append({"itemIdentifier": sequence_number})

            # Send to DLQ if enabled
            if dlq_enabled and dlq_url:
                # Find the original record
                for record in records:
                    if record.get("kinesis", {}).get("sequenceNumber") == sequence_number:
                        send_to_dlq(record, dlq_url, error.get("message", "Parse error"))
                        break

    except Exception as e:
        logger.error(f"Parsing stage failed completely: {e}")
        # If parsing fails completely, mark all as failed
        for record in records:
            sequence_number = record.get("kinesis", {}).get("sequenceNumber", "unknown")
            batch_item_failures.append({"itemIdentifier": sequence_number})

        return {
            "success_count": 0,
            "failure_count": total_records,
            "batchItemFailures": batch_item_failures,
            "metrics": metrics,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "error": "Parsing stage failed"
        }

    # If no events were successfully parsed, return early
    if not parsed_events:
        return {
            "success_count": 0,
            "failure_count": total_records,
            "batchItemFailures": batch_item_failures,
            "metrics": metrics,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }

    # STAGE 2: Validate events
    try:
        validated_events, validation_errors = validate_events_batch(
            parsed_events,
            skip_invalid=True
        )
        metrics["validation_errors"] = len(validation_errors)

        # Validation failures don't map back to sequence numbers easily
        # so we just count them
        failure_count += len(validation_errors)

    except Exception as e:
        logger.error(f"Validation stage failed: {e}")
        validated_events = []

    # STAGE 3: Enrich events
    try:
        enriched_events = enrich_events_batch(validated_events)

        # Count enrichment errors
        enrichment_errors = [e for e in enriched_events if e.get("enrichment_error")]
        metrics["enrichment_errors"] = len(enrichment_errors)

    except Exception as e:
        logger.error(f"Enrichment stage failed: {e}")
        enriched_events = []

    # STAGE 4: Aggregate metrics
    try:
        if enriched_events:
            aggregation_result = aggregate_events_batch(
                enriched_events,
                return_summary=True
            )
            metrics["aggregation_errors"] = aggregation_result.get("failure_count", 0)
    except Exception as e:
        logger.error(f"Aggregation stage failed: {e}")
        metrics["aggregation_errors"] += 1

    # STAGE 5: Archive to S3
    try:
        if enriched_events:
            archive_result = archive_to_s3_batched(
                enriched_events,
                bucket=s3_bucket
            )
            if not archive_result.get("success"):
                metrics["archive_errors"] = archive_result.get("failures", 0)
    except Exception as e:
        logger.error(f"Archive stage failed: {e}")
        metrics["archive_errors"] += 1

    # Calculate final counts
    # Success = events that made it through all stages
    success_count = len(enriched_events) - metrics["enrichment_errors"]

    # Processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    logger.info(
        f"Batch processing complete: {success_count} success, {failure_count} failures, "
        f"{processing_time_ms}ms"
    )

    return {
        "success_count": success_count,
        "failure_count": failure_count,
        "batchItemFailures": batch_item_failures,
        "metrics": metrics,
        "processing_time_ms": processing_time_ms
    }
